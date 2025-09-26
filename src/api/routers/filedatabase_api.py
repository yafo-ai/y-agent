import asyncio
import os.path
import traceback
from datetime import datetime

from os.path import join

from fastapi import APIRouter, Path, Depends, Query, UploadFile, Body, BackgroundTasks
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

from src.api.customer_exception import ValidationException, BusinessException
from src.api.knowledgebase_task import filedata_convert_index_task
from src.rag.excel_vector_store import ExcelChromaVectorStore
from src.database.enums import get_enum_name, FileTemplateType
from src.database.db_session import get_scoped_session
from src.database.models import FileDatabaseModel, FileContentModel
from src.utils.file_helper import FileHelper
from src.utils.log_helper import logger

router = APIRouter(
    prefix="/api/filedatabase",
    tags=["参数库"],
)


@router.get("", summary="分页")
def get_file_database(page: int = Query(description="页码", default=1),
                      pagesize: int = Query(description="每页数量", default=10),
                      knowledgebase_id: int = Query(description="知识库主键id"),
                      session: Session = Depends(get_scoped_session)):
    """分页获取文件数据库列表"""
    conditions = {}
    if knowledgebase_id:
        conditions['knowledgebase_id'] = knowledgebase_id
    file_database = session.query(FileDatabaseModel).filter_by(**conditions).offset(pagesize * (page - 1)).limit(pagesize).all()
    total_records = session.query(FileDatabaseModel).filter_by(**conditions).count()
    total_pages = (total_records + pagesize - 1) // pagesize
    if not file_database:
        return {"total_records": total_records, "total_pages": total_pages, "rows": []}
    rows = [
        {
            "id": database.id,
            "template_name": get_enum_name(FileTemplateType, database.file_template_type),
            "file_name": database.file_name,
            "file_size": str(round(database.file_size / (1024 * 1024), 2) if database.file_size else 0) + "MB",
            "path": database.file_path,
            "created_at": database.created_at,
            "index_at": database.index_at,
            "is_index_refresh": database.is_index_refresh,
            "index_refresh_at": database.index_refresh_at.strftime("%Y-%m-%d %H:%M:%S") if database.index_refresh_at else None,
            "updated_at": database.updated_at,
        } for database in file_database
    ]
    return {"total_records": total_records, "total_pages": total_pages, "rows": rows}


@router.post("/add", summary="添加")
def add_file_database(file: UploadFile,
                      template_type: FileTemplateType = Query(description="文件模板类型"),
                      knowledgebase_id: int = Query(description="知识库主键id"),
                      session: Session = Depends(get_scoped_session)):
    """
    新增文件数据库
    file: 文件
    template_type: 文件模板类型
    """

    if template_type != FileTemplateType.产品参数模板:
        raise ValidationException('暂不支持该文件模板类型')

    folder_path = f'./src/upload_field/file_database/{template_type.value}_{knowledgebase_id}/'
    os.makedirs(folder_path, exist_ok=True)
    file_ext = os.path.splitext(file.filename)[1]
    if file_ext.lower() not in ['.xlsx']:
        raise ValidationException("文件格式错误，必须为excel文件xlsx")
    full_file_path = join(folder_path, file.filename)
    if os.path.exists(full_file_path):
        raise ValidationException(f"{full_file_path} 已经存在！")
    with open(full_file_path, 'wb') as buffer:
        buffer.write(file.file.read())

    try:
        file_database = FileDatabaseModel.excel_to_model(full_file_path)
        file_database.knowledgebase_id = knowledgebase_id
        file_database.file_template_type = template_type.value
        file_database.add(True)
        return {"id": file_database.id, "file_name": file_database.file_name}
    except ValidationException as ne:
        FileHelper.delete_file(full_file_path)
        raise ValidationException(str(ne))
    except Exception as e:
        logger.error(f"文件【{full_file_path}】导入异常：" + str(e))
        traceback.print_exc()
        FileHelper.delete_file(full_file_path)
        raise BusinessException(detail=f"文件处理失败：{e}")


@router.post("/delete/{id}", summary="删除")
def delete_file_database(id: int = Path(description="文件数据库id"), session: Session = Depends(get_scoped_session)):
    """删除"""
    file_database = FileDatabaseModel.get(id)
    if file_database.is_index:
        ExcelChromaVectorStore().del_products_index(file_database.id)
    try:
        if os.path.exists(file_database.file_path):
            os.remove(os.path.abspath(file_database.file_path))
    except Exception as e:
        traceback.print_exc(e.args[0])
        import logging
        logging.error(f"删除文件【{file_database.file_path}】失败：" + str(e.args[0]))
    file_database.delete(True)
    return {'result': 'success'}


@router.post("/converter_index/{id}", summary="向量化")
def converter_index(id: int = Path(description="文件数据库id"), session: Session = Depends(get_scoped_session)):
    """转换为索引"""
    file_database = FileDatabaseModel.get(id)
    # 这里写转换为索引......
    vector_store = ExcelChromaVectorStore()
    vector_store.del_products_index(file_database.id)
    for file_content in file_database.file_contents:
        vector_store.add_product_index(file_database.knowledgebase_id, file_database.id, file_database.file_name, file_content.relation_code,
                                       file_content.relation_index, file_content.markdown_content,file_content.get_metadata)

    file_database.is_index = True
    import datetime
    file_database.index_at = datetime.datetime.now()
    file_database.is_index_refresh = False
    file_database.index_refresh_at = datetime.datetime.now()
    file_database.update(True)
    return {'result': 'success'}


@router.get("/detail/{id}", summary="详情")
def detail_by_id(id: int = Path(description="文件数据库id"),
                 code: str = Query(description="编码", default=None),
                 session: Session = Depends(get_scoped_session)):
    """获取文件数据库详情"""
    # from sqlalchemy.orm import selectinload
    # session.query(FileDatabaseModel).options(selectinload(FileDatabaseModel.file_contents)).all()
    file_database = FileDatabaseModel.get(id)
    contents = list(filter(lambda x: x.relation_code == code, file_database.file_contents.all()))
    content = contents[0].markdown_content if len(contents) > 0 else None
    if content is not None:
        return {'file_name': file_database.file_name, 'title': contents[0].relation_title, 'code': contents[0].relation_code, 'content': content}
    else:
        return {'file_name': file_database.file_name, 'title': None, 'code': None, 'content': content}


@router.get("/download/{id}", summary="下载")
def download_file_database(id: int = Path(description="文件数据库id"), session: Session = Depends(get_scoped_session)):
    """下载文件"""
    file_database = FileDatabaseModel.get(id)
    if not os.path.exists(file_database.file_path):
        raise ValidationException("文件不存在")
    from starlette.responses import FileResponse
    return FileResponse(file_database.file_path, filename=file_database.file_name)


@router.post("/detail/{id}/contents", summary="内容列表")
def get_file_database_contents(id: int = Path(description="文件数据库id"),
                               page: int = Body(description="页码", default=1),
                               pagesize: int = Body(description="每页数量", default=10),
                               code: str = Body(description="编码", default=None),
                               title: str = Body(description="标题", default=None),
                               relation_index: int | None = Body(description="关联索引", default=None),
                               session: Session = Depends(get_scoped_session)):
    """分页获取文件数据库内容列表"""
    file_database = FileDatabaseModel.get(id)
    if not file_database.file_contents:
        return {"total_records": 0, "total_pages": 0, "rows": []}
    contents = file_database.file_contents.all()
    if code:
        contents = list(filter(lambda x: code in x.relation_code, contents))
    if title:
        contents = list(filter(lambda x: title in x.relation_title, contents))
    if relation_index is not None:
        contents = list(filter(lambda x: x.relation_index == relation_index, contents))

    total_records = len(contents)
    total_pages = (total_records + pagesize - 1) // pagesize

    contents = contents[(page - 1) * pagesize:page * pagesize]
    rows = [
        {
            "id": content.id,
            "code": content.relation_code,
            "title": content.relation_title,
            "relation_index": content.relation_index,
            "created_at": content.created_at,
            "updated_at": content.updated_at,
        } for content in contents
    ]
    return {"total_records": total_records, "total_pages": total_pages, "rows": rows}


@router.get("/content/attributes/", summary="内容详情", tags=['public'])
def get_file_database_content_attributes(relation_code: list[str] = Query(description="文件的唯一编码"),
                                         session: Session = Depends(get_scoped_session)):
    return FileContentModel.get_content_attribute_keys(relation_code)


@router.post("/batch_convert_index/{knowledgebase_id}", summary="批量更新向量库")
def batch_convert_index(background_tasks: BackgroundTasks, knowledgebase_id: int = Path(description="知识库id")):
    """批量转换为索引"""
    background_tasks.add_task(asyncio.to_thread, filedata_convert_index_task, knowledgebase_id)
    return {'result': 'success'}


@router.post("/update", summary='更新')
def update_file_database(file: UploadFile, id: int = Query(description="文件数据库id")):
    """
    更新
    :param file:
    :param id:
    :return:
    """
    file_database = FileDatabaseModel.get(id)
    old_file_path = file_database.file_path

    root_path = f'./src/upload_field/file_database/{file_database.file_template_type}_{file_database.knowledgebase_id}/'
    os.makedirs(root_path, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    if ext.lower() not in ['.xlsx']:
        raise ValidationException("文件格式错误，必须为excel文件xlsx")
    file_path = os.path.join(root_path, file.filename)
    if os.path.exists(file_path):
        raise ValidationException(f"{file_path} 已经存在！")
    with open(file_path, 'wb') as f:
        f.write(file.file.read())
    try:
        result = file_database.update_filedata(file_path)
        vector = ExcelChromaVectorStore()
        vector.del_products_index(file_database.id)
        for content in file_database.file_contents:
            vector.add_product_index(file_database.knowledgebase_id, file_database.id, file_database.file_name, content.relation_code, content.relation_index, content.markdown_content, content.get_metadata)
        file_database.is_index = True
        file_database.index_at = datetime.now()
        file_database.is_index_refresh = False
        file_database.index_refresh_at = datetime.now()
        file_database.update(True)
        return result
    except ValidationException as e:
        FileHelper.delete_file(file_path)
        raise e
    except Exception as ex:
        traceback.print_exc()
        FileHelper.delete_file(file_path)
        raise BusinessException(detail=f"文件处理失败：{ex}")


@router.get('/template', summary='导出参数库模板')
def export_file_template():
    file_path = f'./src/upload_field/template/参数库模板.xlsx'
    if not os.path.exists(file_path):
        raise ValidationException("模板文件不存在")
    return FileResponse(file_path, filename=os.path.basename(file_path), media_type='application/octet-stream')
