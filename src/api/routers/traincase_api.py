import datetime
import os
import uuid
from io import BytesIO
from typing import Optional
from urllib.parse import quote

import pandas as pd
from fastapi import APIRouter, Body, Path, Depends, Query, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse, FileResponse

from ..customer_exception import ValidationException
from ...database.db_session import get_scoped_session
from ...database.models import TrainCase, TrainCate, WorkFlowRunNodeLog, TestCase

router = APIRouter(
    prefix="/api/train",
    tags=["训练"],
)
# region 训练类目


@router.get("/get_cates", summary="类目列表")
def get_category_tree():
    """加载训练类目"""
    return TrainCate.tree()


@router.get("/cates/{id}", summary="类目详情")
def get_category(id: int = Path(description="类目id")):
    """加载训练类目详情"""
    model = TrainCate.get(id)
    return {"id": model.id, "name": model.name, "color": model.color, "pid": model.pid}


@router.post("/cate_add", summary="添加类目")
def category_add(pid: int | None = Body(description="所属类目id", default=None), name: str = Body(max_length=50, description="名称"), color: str = Body(description="颜色")):
    """添加类目"""
    if pid is not None and pid > 0:
        TrainCate.get(pid)
    category = TrainCate(name=name, color=color, pid=pid)
    category.add(True)
    return {"id": category.id}


@router.post("/cate_edit/{id}", summary="编辑类目")
def category_edit(id: int = Path(description="类目id"), name: str = Body(max_length=50, description="名称"), color: str = Body(description="颜色")):
    """编辑类目"""
    model = TrainCate.get(id)
    model.name = name
    model.color = color
    model.update(True)
    return {"result": "success"}


@router.post("/cate_delete/{id}", summary="删除类目")
def category_delete(id: int = Path(description="类目id")):
    TrainCate.get(id).delete_train_category()
    return {"result": "success"}

# endregion

# region 训练用例


@router.post("/get_train_cases", summary="训练列表")
def get_trains(cate_id: int | None = Body(default=None, description="类目id,不传：查询全部 0：查询未分类 大于0：查询指定类目"),
               page: int = Body(description="页码", default=1),
               pagesize: int = Body(description="每页数量", default=10),
               is_marked: bool | None = Body(description="是否标记", default=None),
               is_modified: bool | None = Body(description="是否修改", default=None),
               id: Optional[int] = Body(default=None, description="用例id"),
               input_data: Optional[str] = Body(default=None, description="输入"),
               output_data: Optional[str] = Body(default=None, description="输出"),
               feature: Optional[str] = Body(default=None, description="特征概要")):

    """
    用于分页查询训练用例
    参数：分类id，页数，页码
    """
    filters = []
    if cate_id is not None and cate_id > 0:
        filters.append(TrainCase.train_cate_id == cate_id)
    if cate_id is not None and cate_id == 0:
        filters.append(or_(TrainCase.train_cate_id == 0, TrainCase.train_cate_id.is_(None)))
    if is_marked is not None:
        filters.append(TrainCase.is_marked == is_marked)
    if is_modified is not None:
        filters.append(TrainCase.is_modified == is_modified)
    if input_data is not None and input_data != "":
        filters.append(TrainCase.input_data.like(f"%{input_data}%"))
    if output_data is not None and output_data != "":
        filters.append(TrainCase.output_data.like(f"%{output_data}%"))
    if feature is not None and feature != "":
        filters.append(TrainCase.feature.like(f"%{feature}%"))
    if id is not None and id != "":
        filters.append(TrainCase.id == id)
    return TrainCase.get_pagination(page, pagesize, *filters)


@router.get("/train_cases/{id}", summary="训练详情")
def get_train_detail(id:int=Path(description="数据id")):

    """
    用于查询指定的的训练数据
    参数：文档id
    """
    train_case = TrainCase.get(id)
    return {
        "id": train_case.id,
        "input_data": train_case.input_data,
        "output_data": train_case.output_data,
        "train_cate_id": train_case.train_cate_id,
        "train_cate_name": train_case.train_cate.name if train_case.train_cate else "未分类",
        "train_cate_color": train_case.train_cate.color if train_case.train_cate else "red",
        "is_marked": train_case.is_marked,
        "is_modified": train_case.is_modified,
        "workflow_id": train_case.workflow_id,
        "workflow_log_id": train_case.workflow_log_id,
        "workflow_node_log_id": train_case.workflow_node_log_id,
        "vision_file_str": train_case.vision_file_str,
        "created_at": train_case.created_at,
        "updated_at": train_case.updated_at,
        "feature": train_case.feature,
    }


@router.post("/train_case_add", summary="添加训练数据")
def add_train(train_cate_id: int | None = Body(description="所属类目id", default=None),
              node_id: int | None = Body(description="流程日志节点id", default=None),
              input_data: str | None = Body(description="输入数据", default=None),
              output_data: str | None = Body(description="输出数据", default=None),
              is_marked: bool | None = Body(description="是否标记", default=None),
              is_modified: bool | None = Body(description="是否修改", default=None),
              feature: str | None = Body(description="特征概要", default=None),
              test_case_id: int | None = Body(description="单元测试用例id", default=None)):
    
    """
    用于添加训练数据
    参数：所属类目id，聊天id，输入数据，输出数据
    """
    TrainCase.add_train(train_cate_id, node_id, input_data, output_data, is_marked, is_modified, feature, test_case_id)
    return {"result": "success"}


@router.post("/train_case_update", summary="更新训练数据")
def edit_train(id: int = Body(description="数据id", default=0),
               train_cate_id: int | None = Body(description="所属类目id", default=None),
               input_data: str|None = Body(description="输入数据", default=None),
               output_data: str|None = Body(description="输出数据", default=None),
               is_marked: bool | None = Body(description="是否标记",default=None),
               is_modified: bool | None = Body(description="是否修改",default=None),
               feature: str | None = Body(description="特征概要", default=None)):
    """
    用于更新训练数据
    参数：数据id，所属类目id，输入数据，输出数据
    """
    TrainCase.get(id).edit_train(train_cate_id, input_data, output_data, is_marked, is_modified, feature)
    return {"result": "success"}


@router.post("/train_case_delete/{id}", summary="删除训练数据")
def train_case_delete(id: int = Path(description="id")):
    """用于删除指定的训练数据"""
    TrainCase.get(id).delete(True)
    return {"result": "success"}


@router.post("/train_case_move/{id}", summary="移动训练数据")
def train_case_move(id: int = Path(description="id"), train_cate_id: int | None = Query(description="目标类目id")):
    """移动训练数据到目标类目"""   
    if train_cate_id:
        target_category = TrainCate.get(train_cate_id)
        if not target_category:
            raise ValidationException(detail="目标类目不存在")
    doc = TrainCase.get(id)
    doc.train_cate_id = train_cate_id
    doc.update(True)
    return {"result": "success"}


@router.post("/train_case_marked", summary="标记训练数据")
def train_case_marked(ids: list[int] | None = Body(description="数据id列表", default=None),
                      is_marked: bool | None = Body(description="是否标记", default=None)):
    """标记训练数据"""
    if ids is None or len(ids) == 0:
        raise ValidationException(detail="请选择数据")
    if is_marked is None:
        raise ValidationException(detail="请选择标记状态")
    TrainCase.marked(ids, is_marked)
    return {"result": "success"}


@router.get("/train_case_export", summary="导出训练数据")
def train_case_export(cate_id: int | None = Query(description="类目id", default=None)):
    """导出训练数据"""
    if cate_id is not None and cate_id == 0:
        train_cases = TrainCase.query.filter(or_(TrainCase.train_cate_id == 0, TrainCase.train_cate_id == None)).all()
    elif cate_id is not None and cate_id > 0:
        train_cases = TrainCase.query.filter_by(train_cate_id=cate_id).all()
    else:
        raise ValidationException(detail="请选择类目")
    if not train_cases or len(train_cases) == 0:
        raise ValidationException(detail="没有数据")
    rows = [
        {
            "ID": train_case.id,
            "输入": train_case.input_data,
            "输出": train_case.output_data,
            "特征概要": train_case.feature,
            "分类名称": train_case.train_cate.name if train_case.train_cate else "未分类",
            "分类ID": train_case.train_cate_id,
            "是否审核": '是' if train_case.is_marked is True else '否',
            "是否更正": '是' if train_case.is_modified is True else '否',
            "创建时间": train_case.created_at.strftime("%Y-%m-%d %H:%M:%S")
        } for train_case in train_cases
    ]
    cate_name = '未分类' if cate_id == 0 else rows[0].get('分类名称')
    filename = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{cate_name}.xlsx"
    encoded_filename = quote(filename, encoding='utf-8')
    content_disposition = f"attachment; filename={encoded_filename}"
    df = pd.DataFrame(rows)
    output = BytesIO()
    df.to_excel(output, index=False, sheet_name='训练数据', engine='openpyxl')
    output.seek(0)
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": content_disposition})


@router.post("/unit_cases", summary="获取关联单元测试用例列表")
def get_unit_cases(ids: list[int] | None = Body(..., embed=True, description="训练id列表")):
    """
    获取单元测试用例列表
    """
    return TrainCase.get_relation_unit_case(ids)

# endregion


@router.post("/move_cate", summary="移动训练分类")
def train_move_cate(source_cate_id: Optional[int] = Body(description="来源类别id", default=None),
                    target_cate_id: Optional[int] = Body(description="目标类别id", default=None)):
    """
    Args:
        source_cate_id: 来源类别id
        target_cate_id: 目标类别id
    Returns:
        None
    """
    TrainCase.move_cate(source_cate_id, target_cate_id)
    return {"result": "success"}


@router.get("/download/case_template", summary="下载---训练导入模板")
def download_case_template():
    file_path = f'./src/upload_field/template/训练导入模板.xlsx'
    if not os.path.exists(file_path):
        raise ValidationException("模板文件不存在")
    return FileResponse(file_path, filename=os.path.basename(file_path), media_type='application/octet-stream')


@router.post('/case/import', summary='导入训练数据')
def case_import(file: UploadFile, session: Session = Depends(get_scoped_session)):
    folder_path = f'./src/upload_field/file_case_unit/'
    file_ext = os.path.splitext(file.filename)[1]
    if file_ext.lower() not in ['.xlsx']:
        raise ValidationException("请上传xlsx格式文件")
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, f'{uuid.uuid4().hex}_{file_ext}')
    with open(file_path, 'wb') as f:
        f.write(file.file.read())
    df = pd.read_excel(file_path)
    try:
        os.remove(file_path)
    finally:
        pass
    try:
        if df.empty:
            raise ValidationException("导入文件为空")
        required_columns = {'输入', '输出', '分类名称'}
        if not required_columns.issubset(df.columns):
            raise ValidationException("导入文件缺少必填字段，必须包含'输入', '输出', '分类名称'字段")
        cate_names = df['分类名称'].dropna().unique()
        cates = TrainCate.query.filter(TrainCate.name.in_(cate_names)).all()
        index = 1
        is_commit = False
        for row in df.to_dict(orient='records'):
            index += 1
            cate_id = None
            cate_name = str(row.get('分类名称')) if pd.notna(row.get('分类名称')) else None
            if cate_name is not None:
                current_cate = filter(lambda x: x.name == cate_name, cates)
                tmp_cates = list(current_cate)
                if len(tmp_cates) > 0:
                    cate_id = tmp_cates[0].id
                else:
                    raise ValidationException(f"第{index}行，分类名称【{cate_name}】不存在")
            input_date = str(row.get('输入')) if pd.notna(row.get('输入')) else None
            output_date = str(row.get('输出')) if pd.notna(row.get('输出')) else None
            feature = str(row.get('特征概要')) if pd.notna(row.get('特征概要')) else None
            if (input_date is None or len(input_date) == 0) or (output_date is None or len(output_date) == 0) or (feature is None or len(feature) == 0):
                raise ValidationException(f"第{index}行，输入、输出、特征概要不能为空")
            is_modified = True if pd.notna(row.get('是否更正')) and str(row.get('是否更正')).lower() == '是' else False
            is_marked = True if pd.notna(row.get('是否审核')) and str(row.get('是否审核')).lower() == '是' else False
            TrainCase(train_cate_id=cate_id, input_data=input_date, output_data=output_date, is_modified=is_modified, is_marked=is_marked, feature=feature).add()
            is_commit = True
        if is_commit:
            session.commit()
    except Exception as e:
        raise ValidationException(f"导入训练数据异常，原因：{str(e)}")
    return {"result": "success"}


@router.post('/case/import_update', summary='导入训练数据-更新')
def case_import_update(file: UploadFile, session: Session = Depends(get_scoped_session)):
    folder_path = f'./src/upload_field/file_case_unit/'
    file_ext = os.path.splitext(file.filename)[1]
    if file_ext.lower() not in ['.xlsx']:
        raise ValidationException("请上传xlsx格式文件")
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, f'{uuid.uuid4().hex}_{file.filename}')
    with open(file_path, 'wb') as f:
        f.write(file.file.read())
    df = pd.read_excel(file_path)
    try:
        os.remove(file_path)
    finally:
        pass
    index = 1
    is_commit = False
    try:
        if df.empty:
            raise ValidationException("文件为空，没有数据")
        required_columns = {'ID', '创建时间', '分类名称', '分类ID', '输入', '输出'}
        if not required_columns.issubset(df.columns):
            raise ValidationException("单元测试文件格式错误，必须包含'ID', '创建时间','分类名称', '分类ID', '输入', '输出'列")
        ids = df['ID'].dropna().unique()
        if len(ids) == 0:
            raise ValidationException("文件中没有ID列，请检查文件格式")
        cases = TrainCase.query.filter(TrainCase.id.in_(ids)).all()
        for row in df.to_dict(orient='records'):
            index += 1
            row_id = str(row.get('ID')) if pd.notna(row.get('ID')) else None
            cate_id = str(row.get('分类ID')) if pd.notna(row.get('分类ID')) else None
            create_time = str(row.get('创建时间')) if pd.notna(row.get('创建时间')) else None
            input_data = str(row.get('输入')) if pd.notna(row.get('输入')) else None
            output_data = str(row.get('输出')) if pd.notna(row.get('输出')) else None

            if row_id is None:
                raise ValidationException(f"第{index}行，ID不能为空")
            tmp_cases = list(filter(lambda x: str(x.id) == row_id, cases))
            if len(tmp_cases) == 0:
                raise ValidationException(f"第{index}行，ID【{row_id}】的数据不存在")

            current_case = tmp_cases[0]

            if str(current_case.train_cate_id) != str(cate_id):
                raise ValidationException(f"第{index}行，分类ID【{cate_id}】与原分类ID【{current_case.train_cate_id}】不一致")
            if current_case.created_at.strftime('%Y-%m-%d %H:%M:%S') != create_time:
                raise ValidationException(f"第{index}行，创建时间【{create_time}】与原创建时间【{current_case.created_at.strftime('%Y-%m-%d %H:%M:%S')}】不一致")

            is_modified = True if pd.notna(row.get('是否更正')) and str(row.get('是否更正')).lower() == '是' else False
            is_marked = True if pd.notna(row.get('是否审核')) and str(row.get('是否审核')).lower() == '是' else False
            feature = str(row.get('特征概要')) if pd.notna(row.get('特征概要')) else None
            if (input_data is None or len(input_data) == 0) or (output_data is None or len(output_data) == 0) or (feature is None or len(feature) == 0):
                raise ValidationException(f"第{index}行，输入、输出、特征概要不能为空")
            current_case.input_data = input_data
            current_case.output_data = output_data
            current_case.is_marked = is_marked
            current_case.is_modified = is_modified
            current_case.feature = feature
            current_case.update()
            is_commit = True
        if is_commit:
            session.commit()
    except ValidationException as e:
        if is_commit:
            session.commit()
        raise ValidationException(f"导入单元测试用例错误，原因：{str(e)}")
    except Exception as e:
        raise ValidationException(f"导入单元测试用例异常，原因：{str(e)}")
    return {"result": "success"}