import asyncio
import shutil
import typing
from typing import List, Optional
from fastapi import APIRouter,File, Path, Query, UploadFile,Body,Depends, BackgroundTasks
from sqlalchemy import func, or_

from src.database.models import KnowledgeDocument, Category, KnowledgeBase, KnowledgeDocumentMarkdown, PromptModel
from src.llm.llm_helper import llm_content_markdown_parser, llm_generate_text
from src.rag.extractor.extract_processor import ExtractProcessor
from src.utils.file_helper import FileHelper
# from src.utils.txt_reader import read_file_with_different_encodings
from ..customer_exception import *
import os
from os.path import join
from src.database.db_session import get_scoped_session
from sqlalchemy.orm import Session

from ..knowledgebase_task import document_convert_index_task
from ...rag.knowledge_vector_store import KnowledgeChromaVectorStore

router = APIRouter(
    prefix="/api/documents",
    tags=["文本知识库"],
)


@router.get("/", summary="分页", tags=['public'])
def get_documents(knowledgebase_id: int = Query(description="知识库id"),
                        category_id: int|None = Query(default=None, description="类目id,不传：查询全部 0：查询未分类文档 大于0：查询指定类目文档"),
                        page: int = Query(description="页码", default=1),
                        pagesize: int = Query(description="每页数量", default=10),
                        keyword: Optional[str] = Query(description="关键字", default=None),
                        session: Session = Depends(get_scoped_session)
                        ):
    
    """
    用于分页查询文档
    参数：知识库id,分类id，页数，页码
    """

    conditions = {}
    if knowledgebase_id:
        conditions['knowledgebase_id'] = knowledgebase_id
    documents = session.query(KnowledgeDocument).filter_by(**conditions)
    if category_id is not None and category_id == 0:
        documents = documents.filter(or_(KnowledgeDocument.category_id == 0, KnowledgeDocument.category_id == None))
    elif category_id is not None and category_id > 0:
        documents = documents.filter_by(category_id=category_id)
    if keyword is not None and keyword.strip():
        documents = documents.join(KnowledgeDocumentMarkdown).filter(KnowledgeDocumentMarkdown.content.ilike(f'%{keyword.strip()}%'))
    total_records = documents.count()
    documents = documents.offset((page-1)*pagesize).limit(pagesize).all()
    total_pages = (total_records+pagesize-1)//pagesize
    if not documents:
        return {"total_records": 0, "total_pages": 0, "rows": []}
    rows = [
        {
            "id": doc.id,
            "name": doc.name,
            "file_path": doc.file_path,
            "file_ext": doc.file_ext,
            "content": None,
            "markdown_content": None,
            "node_qty": doc.node_qty,
            "category_id": doc.category_id,
            "knowledgebase_id": doc.knowledgebase_id,
            "is_index": doc.is_index,
            "is_index_refresh": doc.is_index_refresh,
            "is_markdown": doc.is_markdown,
            "created_at": doc.created_at,
            "markdown_at": doc.markdown_at,
            "updated_at": doc.updated_at,
            "index_at": doc.index_at
        } for doc in documents
    ]
    return {"total_records": total_records, "total_pages": total_pages, "rows": rows}

@router.get("/get/{id}", summary="详情")
def get_document(id:int=Path(description="文档id"),session:Session=Depends(get_scoped_session)):

    """
    用于查询指定的的文档
    参数：文档id
    """
     
    doc = KnowledgeDocument.get(id)
    nodes = KnowledgeChromaVectorStore().get_document_vindex(id)
    category_name = "未分类"
    markdown_content = ""
    if doc.category_id:
        category = Category.query.get(doc.category_id)
        if category:
            category_name = category.name
    if doc.markdown:
        markdown_content = doc.markdown.content
    knowledgebase_name=""
    knowledgebase = KnowledgeBase.get(doc.knowledgebase_id)
    if knowledgebase:
        knowledgebase_name=knowledgebase.name

    
    return {"id":doc.id,
            "name":doc.name,
            "file_path":doc.file_path,
            "file_ext":doc.file_ext,
            "content":doc.content,
            "markdown_content":markdown_content,
            "caption":doc.caption,
            "node_qty":doc.node_qty,
            "category_id":doc.category_id,
            "category_name":category_name,
            "knowledgebase_id":doc.knowledgebase_id,
            "knowledgebase_name":knowledgebase_name,
            "is_index":doc.is_index,
            "is_markdown":doc.is_markdown,
            "nodes":nodes
            }

@router.post("/add", summary="添加文件")
def document_add(file: UploadFile,
                       knowledgebase_id:int,
                       category_id:int|None=Query(default=None),session:Session=Depends(get_scoped_session)
                       ):
    """
    用于添加文档，需要上传指定的文件
    参数：知识库id，类目id，文件
    """
    filename = file.filename
    folder_path=f"./src/upload_field/knowledge_{knowledgebase_id}"
    full_file_path = join(folder_path, filename)
    file_ext=os.path.splitext(filename)[1]

    if file_ext not in [".txt",".md",".docx",".xlsx",".pdf",".csv"]:
        raise ValidationException(detail="文件格式不支持")

    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
    if os.path.exists(full_file_path):
        raise ValidationException(detail="文件已存在不可以重复上传")
    
    try:
        with open(full_file_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)

        docs=ExtractProcessor.extract(full_file_path,file_ext,True);
        content=""
        for doc in docs:
            content+=doc.page_content


        doc=KnowledgeDocument.create_document(knowledgebase_id=knowledgebase_id,name=filename,content=content,category_id=category_id,file_path=full_file_path,file_ext=file_ext)

        return {"id":doc.id,"name":doc.name,"file_path":doc.file_path,"file_ext":doc.file_ext}
    
    except Exception as e:
        FileHelper.delete_file(full_file_path)
        raise BusinessException(detail=f"文件处理失败：{e}")

@router.post("/add_content", summary="添加内容")
def document_add_markdown_content(knowledgebase_id: int = Body(description="知识库主键id"),
                                        category_id: int | None = Body(description='类目id', default=None),
                                        name: str = Body(description="文档名称"),
                                        content:str= Body(description="内容"),
                                        session: Session = Depends(get_scoped_session)):
    """
    用于手动添加内容
    参数：类目id，知识库id，名称，内容，提示词id
    """
    if not content:
        raise ValidationException(detail="文档内容不能为空")
    if not knowledgebase_id:
        raise ValidationException(detail="知识库id不能为空")

    document=KnowledgeDocument.create_document(knowledgebase_id=knowledgebase_id,name=name,content=content,category_id=category_id)

    return {"id": document.id, "name": document.name}

@router.post("/edit/{id}/content", summary="编辑内容")
def document_edit_content(id:int=Path(description="文档主键id"),
                         name:str =Body(description="名称，标题"),
                         content: typing.Any = Body(description="文档内容"),
                         session:Session=Depends(get_scoped_session)
):
    """
    用于编辑文档内容
    参数：文档id，内容
    """

    KnowledgeDocument.edit_content(id=id,name=name,content=content)

    return {"result":"success"}

@router.post("/edit/{id}/markdown_content", summary="编辑markdown")
def document_edit_markdown_content(id:int=Path(description="文档主键id"),
                         name:str =Body(description="名称，标题"),
                         markdown_content:typing.Any = Body(description="文档内容"),
                         session:Session=Depends(get_scoped_session)
):
    """
    用于编辑文档markdown内容
    参数：文档id，markdown内容
    """
    KnowledgeDocument.edit_markdown_content(id=id,name=name,markdown_content=markdown_content)
    
    return {"result":"success"}


@router.post("/append_content", summary="追加markdown内容")
def document_edit_markdown_content(id:int=Body(description="文档主键id"),
                         append_content:str = Body(description="追加的内容",default=...),
                         session:Session=Depends(get_scoped_session)
):
    """
    用于编辑文档markdown内容
    参数：文档id，markdown内容
    """

    KnowledgeDocument.append_markdown_content(id=id,append_content=append_content)

    return {"result":"success"}


@router.post("/delete/{id}", summary="删除")
def document_delete(id:int=Path(description="文档主键id"),session:Session=Depends(get_scoped_session)):

    """
    用于删除文档
    参数：文档id
    """

    doc = KnowledgeDocument.get(id)
    KnowledgeChromaVectorStore().del_document_vindex(id)
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    doc.delete(True)
    return {"result":"success"}
    
@router.post("/converter_markdown/{id}", summary="转换为markdown")
def document_converter_markdown(id:int=Path(description="文档主键id"),
                                prompt_id:int|None=Body(description="提示词id",default=None),
                                llm_id:int=Body(description="大模型类型"),
                                content:str=Body(description="文档内容"),
                                session:Session=Depends(get_scoped_session)):

    """
    用于将文档内容整理成markdown格式
    参数：文档id
    """

    prompt_temp_str=""
    if prompt_id:
        prompt = PromptModel.get(prompt_id)
        prompt_temp_str=prompt.content
    else:
        raise ValidationException("请选择markdown提示词")
    
    content=llm_generate_text(llm_id=llm_id,prompt=prompt_temp_str,context={"context_str":content})
    content=llm_content_markdown_parser(content)

    return {"result":"success","content":content}

@router.post("/converter_index/{id}", summary="向量化")
def document_converter_index(id:int=Path(description="文档主键id"),session:Session=Depends(get_scoped_session)):

    """
    用于将文档向量化
    参数：文档id
    """
    doc = KnowledgeDocument.get(id)
    if not doc.is_markdown:
        raise ValidationException(detail="没有转换为markdown,格式")
    if doc.is_index:
        KnowledgeChromaVectorStore().del_document_vindex(id)
    cnt = KnowledgeChromaVectorStore().add_document_vindex(doc)

    doc.set_index_ok(cnt)

    return {"result": "success"}

@router.post("/delete/{id}/index", summary="删除向量")
def document_delete_index(id:int=Path(description="文档主键id"),session:Session=Depends(get_scoped_session)):

    """
    用于删除文档【向量】
    参数：文档id
    """
    doc = KnowledgeDocument.get(id)
    KnowledgeChromaVectorStore().del_document_vindex(id)
    doc.del_index()

    return {"result":"success"}

@router.post("/move", summary="批量移动文档类目")
def document_batch_move_category(category_id: int = Query(description="原始类目id"),
                                 target_category_id: int | None = Query(description="目标类目id"),
                                 session: Session = Depends(get_scoped_session)
):
    
    KnowledgeDocument.document_batch_move_category(category_id=category_id,target_category_id=target_category_id)
    return {"result": "success"}

@router.post("/move/{id}", summary="移动文档类目")
def document_move_category(id: int = Path(description="文档主键id"),
                                       target_category_id: int | None = Query(description="目标类目id"),
                                       session: Session = Depends(get_scoped_session)
):
    KnowledgeDocument.document_move_category(id=id,category_id=target_category_id)
    
    return {"result": "success"}

@router.get("/{id}/versions", summary="文档历史版本")
def document_history(id: int = Path(description="文档主键id"),
                           session: Session = Depends(get_scoped_session)):
    """
    文档分页历史版本
    """
    document = KnowledgeDocument.get(id)
    if not document.markdown:
        return []
    versions = document.markdown.versions.all()
    versions = sorted(versions, key=lambda x: x.ver, reverse=True)
    return [{
             "id": version.id,
             "ver": version.ver,
             "name": document.name,
             "created_at": version.created_at,
             "updated_at": version.updated_at
             } for version in versions]


@router.get("/{id}/version/detail/{ver}", summary="文档历史版本详情")
def document_history_detail(id: int = Path(description="文档主键id"),
                           ver: int = Path(description="历史版本"),
                           session: Session = Depends(get_scoped_session)):

    """
    历史版本详情
    """
    if not ver:
        raise ValidationException(detail="历史版本不能为空")
    document = KnowledgeDocument.get(id)
    if not document.markdown:
        return {}
    versions = document.markdown.versions
    current_version = versions.filter_by(ver=ver).first()
    if not current_version:
        return {}
    return {
             "ver": current_version.ver,
             "name": document.name,
             "content": current_version.content,
             "caption": document.caption,
             "category_id": document.category_id,
             "is_markdown": document.is_markdown,
             "is_index": document.is_index,
             "node_qty": document.node_qty,
             "created_at": current_version.created_at,
             "updated_at": current_version.updated_at
             }


@router.post("/edit/{id}/markdown_content_to_index", summary="编辑markdown并同步向量库")
def document_edit_markdown_content_to_index(id:int=Path(description="文档主键id"),
                                            name:str =Body(description="名称，标题"),
                                            markdown_content:typing.Any = Body(description="文档内容"),
                                            session:Session=Depends(get_scoped_session)
):
    """
    用于编辑文档markdown内容
    参数：文档id，markdown内容
    """

    doc=KnowledgeDocument.edit_markdown_content(id=id,name=name,markdown_content=markdown_content)
    if doc.is_index:
        KnowledgeChromaVectorStore().del_document_vindex(id)
    node_qty = KnowledgeChromaVectorStore().add_document_vindex(doc)
    
    doc.set_index_ok(node_qty)

    return {"result":"success"}

@router.post("/batch_convert_index/{knowledgebase_id}", summary="批量更新向量库")
def document_batch_converter_index(background_tasks: BackgroundTasks, knowledgebase_id:int = Path(description="知识库id")):
    background_tasks.add_task(asyncio.to_thread, document_convert_index_task, knowledgebase_id)
    return {"result": "success"}
