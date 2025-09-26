import asyncio
import datetime
import os
import uuid
from io import BytesIO
from typing import Optional
from urllib.parse import quote

import pandas as pd
from fastapi import APIRouter, Depends, Path, Query, Body, BackgroundTasks, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from src.api.customer_exception import ValidationException
from src.api.testcase_task import case_execute_task, testcase_export
from src.database.enums import TestCaseStateType, TestCaseResultType, get_enum_name
from src.database.models import TestCate, TestCase, WorkFlowRunNodeLog, TrainCase
from src.database.db_session import get_scoped_session
from src.llm.llm_helper import llm_generate_text

router = APIRouter(
    prefix="/api/test",
    tags=["分类测试"],
)


# region 测试类别


@router.get("/cate", summary="测试类别")
def get_cate(tag: Optional[str] = Query(description="标签[S:单元测试  W:流程测试]", default=None),
             session: Session = Depends(get_scoped_session)):
    """获取测试类别"""
    if tag is None:
        models = TestCate.query.all()
    else:
        models = TestCate.query.filter(TestCate.tag == tag)
    return TestCate.tree(models)


@router.post("/cate/add", summary="添加测试类别")
def cate_add(pid: int = Body(description="项目id", default=None),
             cate_name: str = Body(description="测试类别名称", default=None),
             color: str = Body(description="测试类别颜色", default=None),
             tag: Optional[str] = Body(description="标签[S:单元测试  W:流程测试]", default='W'),
             session: Session = Depends(get_scoped_session)):
    """添加测试类别"""
    model = TestCate(name=cate_name, color=color, pid=pid, tag=tag)
    model.add(True)
    return {"id": model.id}


@router.post("/cate/edit/{id}", summary="编辑测试类别")
def cate_edit(pid: int = Body(description="项目id", default=None),
              id: int = Path(description="测试类别id"),
              cate_name: str = Body(description="测试类别名称", default=None),
              color: str = Body(description="测试类别颜色", default=None),
              tag: Optional[str] = Body(description="标签[S:单元测试  W:流程测试]", default='W'),
              session: Session = Depends(get_scoped_session)):
    """编辑测试类别"""
    model = TestCate.get(id)
    model.name = cate_name
    model.color = color
    model.pid = pid
    model.tag = tag
    model.update(True)
    return {"result": "success"}


@router.post("/cate/delete/{id}", summary="删除测试类别")
def cate_delete(id: int = Path(description="测试类别id"),
                session: Session = Depends(get_scoped_session)):
    """删除测试类别"""
    model = TestCate.get(id)
    model.recursion_delete()
    return {"result": "success"}


# endregion

# region 测试用例


@router.post("/case/pagination", summary="用例列表")
def get_case_page(page: int = Body(default=1, description="页码"),
                  pagesize: int = Body(default=10, description="每页数量"),
                  question: str = Body(default=None, description="搜索问题"),
                  answer: str = Body(default=None, description="搜索答案"),
                  cate_id: int = Body(default=None, description="搜索类别id"),
                  case_state: TestCaseStateType = Body(default=None, description="搜索用例状态"),
                  case_result: TestCaseResultType = Body(default=None, description="搜索用例结果"),
                  tag: Optional[str] = Body(description="标签[S:单元测试  W:流程测试]", default=None),
                  id: Optional[int] = Body(default=None, description="用例id"),
                  session: Session = Depends(get_scoped_session)):
    """获取测试用例列表"""
    condition = {}
    if cate_id is not None:
        if cate_id == 0:
            condition["test_cate_id"] = None
        else:
            condition["test_cate_id"] = cate_id
    if case_state is not None and case_state != TestCaseStateType.默认:
        condition["test_state"] = case_state.value
    if case_result is not None and case_result != TestCaseResultType.默认:
        condition["test_result"] = case_result.value
    if tag is not None:
        condition["tag"] = tag
    if id is not None:
        condition["id"] = id
    cases = session.query(TestCase).filter_by(**condition)

    if question is not None:
        cases = cases.filter(TestCase.question.like(f"%{question}%"))
    if answer is not None:
        cases = cases.filter(TestCase.right_answer.like(f"%{answer}%"))

    total_records = cases.count()
    cases = cases.order_by(TestCase.id.desc()).offset((page - 1) * pagesize).limit(pagesize).all()
    total_pages = (total_records + pagesize - 1) // pagesize
    if not cases:
        return {"total_records": total_records, "total_pages": total_pages, "rows": []}
    rows = []
    for case in cases:
        tmp_test_logs = case.test_case_logs.all() if case.test_case_logs else None
        row = {
            "id": case.id,
            "tag": case.tag,
            "note": case.note,
            "question": case.question,
            "right_answer": case.right_answer,
            "test_standard": case.test_standard,
            "test_result_answer": case.test_result_answer,
            "test_state": case.test_state,
            "test_result": case.test_result,
            "test_cate_id": case.test_cate_id,
            "test_count": case.test_count,
            "test_pass_count": case.test_pass_count,
            "test_fail_count": case.test_fail_count,
            "workflow_id": case.workflow_id,
            "workflow_log_id": case.workflow_log_id,
            "workflow_log_inputs": case.workflow_log_inputs,
            "workflow_node_log_id": case.workflow_node_log_id,
            "vision_file_str": case.vision_file_str,
            "last_test_workflow_log_id": tmp_test_logs[-1].workflow_log_id if tmp_test_logs else None,
            "last_test_time": tmp_test_logs[-1].created_at if tmp_test_logs else None,
            "is_marked": case.is_marked,
            "is_modified": case.is_modified,
            "created_at": case.created_at,
            "updated_at": case.updated_at,
        }
        rows.append(row)
    return {"total_records": total_records, "total_pages": total_pages, "rows": rows}


@router.post("/case/add", summary="添加用例")
def case_add(cate_id: int = Body(description="测试类别id", default=None),
             question: str = Body(description="测试问题", default=None),
             right_answer: str = Body(description="参考答案", default=None),
             note: str = Body(description="备注", default=None),
             workflow_log_id: int = Body(default=None, description="工作流ID"),
             test_standard: Optional[str] = Body(description="测试标准", default=None),
             session: Session = Depends(get_scoped_session)):
    """添加测试用例"""
    if question is None or len(question) == 0:
        raise ValidationException("问题不能为空")
    if workflow_log_id is not None:
        is_exist, cate_name = TestCase.is_exist_workflow_log(cate_id, workflow_log_id)
        if is_exist:
            raise ValidationException(f"工作流日志在类别【{cate_name}】下已存在，不能重复添加")
    model = TestCase.case_add(cate_id, question, right_answer, note, workflow_log_id, test_standard)
    return {"id": model.id}


@router.post("/case/edit/{id}", summary="编辑用例")
def case_edit(cate_id: int = Body(description="测试类别id", default=None),
              id: int = Path(description="测试用例id"),
              question: str = Body(description="测试问题", default=None),
              right_answer: str = Body(description="参考答案", default=None),
              note: str = Body(description="备注", default=None),
              is_marked: bool | None = Body(description="是否标记", default=None),
              is_modified: bool | None = Body(description="是否修改", default=None),
              test_standard: Optional[str] = Body(description="测试标准", default=None),
              session: Session = Depends(get_scoped_session)):
    """编辑测试用例"""
    if question is None or len(question) == 0:
        raise ValidationException("问题不能为空")
    if right_answer is None or len(right_answer) == 0:
        raise ValidationException("参考答案不能为空")
    if cate_id == 0:
        cate_id = None
    model = TestCase.get(id)
    if model.test_cate_id != cate_id:
        if model.workflow_log_id is not None:
            is_exist, cate_name = TestCase.is_exist_workflow_log(cate_id, model.workflow_log_id)
            if is_exist:
                raise ValidationException(f"工作流日志在类别【{cate_name}】下已存在，不能重复添加")
    model.question = question
    model.right_answer = right_answer
    model.note = note
    model.is_marked = is_marked
    model.is_modified = is_modified
    model.test_standard = test_standard
    if cate_id is None:
        model.test_cate_id = None
        model.update_with_foreign_key_none(True)
    else:
        model.test_cate_id = cate_id
        model.update(True)
    return {"result": "success"}


@router.post("/case/delete/{id}", summary="删除用例")
def case_delete(id: int = Path(description="测试用例id"),
                session: Session = Depends(get_scoped_session)):
    """删除测试用例"""
    model = TestCase.get(id)
    if model.test_state == TestCaseStateType.测试中.value:
        raise ValidationException("测试用例正在测试中，请等待测试完成后再删除")
    model.delete(True)
    return {"result": "success"}


@router.post("/case/batch_execute", summary="执行测试用例")
def case_batch_execute(background_tasks: BackgroundTasks,
                       ids: list[int] = Body(description="测试用例id列表", default=None),
                       workflow_id: int = Body(description="工作流日志id", default=None),
                       evaluation_llm_id: int = Body(description="评估大模型id", default=None),
                       evaluation_prompt_id: int = Body(description="评估提示词id", default=None),
                       is_forced: bool = Body(description="是否强制按照选择的流程执行", default=False),
                       session: Session = Depends(get_scoped_session)):
    """批量执行测试用例"""
    if ids is None or len(ids) == 0:
        raise ValidationException("请选择测试用例")
    case_list = TestCase.query.filter(TestCase.id.in_(ids)).all()
    if case_list is None or len(case_list) == 0:
        raise ValidationException("用例不存在")
    if workflow_id is None or workflow_id <= 0:
        raise ValidationException("请选择工作流")
    if evaluation_llm_id is None or evaluation_llm_id <= 0:
        raise ValidationException("请选择评估模型")
    if evaluation_prompt_id is None or evaluation_prompt_id <= 0:
        raise ValidationException("请选择评估提示词")
    for case in case_list:
        TestCase.check_case_execute(case, workflow_id, is_forced)
    background_tasks.add_task(asyncio.to_thread, case_execute_task, ids, workflow_id, None, evaluation_llm_id, evaluation_prompt_id, is_forced)
    return {"result": "success"}


@router.get("/case/result/{id}", summary="测试运行记录")
def case_result(id: int = Path(description="测试用例id"),
                session: Session = Depends(get_scoped_session)):
    """获取测试用例结果"""
    model = TestCase.get(id)
    logs = model.test_case_logs.all()
    if logs is None or len(logs) == 0:
        return []
    logs = sorted(logs, key=lambda x: x.id, reverse=True)
    rows = []
    for log in logs:
        rows.append({
            "testcase_id": id,
            "workflow_log_id": log.test_case.workflow_log_id,
            "id": log.id,
            "test_answer": log.test_answer,
            "right_answer": log.right_answer,
            "test_result_name": get_enum_name(TestCaseResultType, log.test_result),
            "score": log.score,
            # "citations": log.citations,
            "test_workflow_log_id": log.workflow_log_id,
            "citations": None,
            "execute_llm_name": log.execute_llm_name,
            "execute_workflow_name": log.execute_workflow_name,
            "created_at": log.created_at,
            "error_msg": log.error_msg
        })
    return rows


# endregion

# region 单元测试

@router.post('/case/unit/add', summary='新增单元测试用例（使用工作流节点日志id）')
def case_unit_add(cate_id: int = Body(description="测试类别id", default=None),
                  workflow_node_log_id: int = Body(description="工作流节点日志id", default=None),
                  note: Optional[str] = Body(description="备注", default=None),
                  session: Session = Depends(get_scoped_session)):
    """添加单元测试用例"""
    model = TestCase.case_add_unit(cate_id, workflow_node_log_id,note)
    return {"id": model.id}


@router.post('/case/unit/add/new', summary='新增单元测试用例')
def case_unit_add_new(cate_id: int = Body(description="测试类别id", default=None),
                      question: Optional[str] = Body(description="测试问题", default=None),
                      right_answer: Optional[str] = Body(description="参考答案", default=None),
                      note: Optional[str] = Body(description="备注", default=None),
                      workflow_node_log_id: int = Body(description="工作流节点日志id", default=None),
                      is_marked: bool | None = Body(description="是否标记", default=None),
                      is_modified: bool | None = Body(description="是否修改", default=None),
                      test_standard: Optional[str] = Body(description="测试标准", default=None),
                      session: Session = Depends(get_scoped_session)
                      ):
    """添加单元测试用例"""
    if cate_id is not None and cate_id <= 0:
        cate_id = None
    if workflow_node_log_id is not None and workflow_node_log_id <= 0:
        workflow_node_log_id = None
    if workflow_node_log_id is not None:
        is_exist, cate_name = TestCase.is_exist_workflow_node_log(cate_id, workflow_node_log_id)
        if is_exist:
            raise ValidationException(f"工作流节点日志在类别【{cate_name}】下已存在，不能重复添加")
    model = TestCase(test_cate_id=cate_id, question=question, right_answer=right_answer, note=note, tag='S')
    model.is_marked = is_marked
    model.is_modified = is_modified
    model.test_standard = test_standard
    if workflow_node_log_id is not None:
        model.workflow_node_log_id = workflow_node_log_id
        node_log = WorkFlowRunNodeLog.get(workflow_node_log_id)
        model.workflow_log_id = node_log.run_log.id
        model.workflow_id = node_log.run_log.flow_id
    model.add(True)
    return {"id": model.id}


@router.post('/case/unit/edit/{id}', summary='编辑单元测试用例')
def case_unit_edit(id: int = Path(description="测试用例id"),
                   cate_id: Optional[int] = Body(description="测试类别id", default=None),
                   question: Optional[str] = Body(description="测试问题", default=None),
                   right_answer: Optional[str] = Body(description="参考答案", default=None),
                   note: Optional[str] = Body(description="备注", default=None),
                   is_marked: bool | None = Body(description="是否标记", default=None),
                   is_modified: bool | None = Body(description="是否修改", default=None),
                   test_standard: Optional[str] = Body(description="测试标准", default=None),
                   ):
    """编辑单元测试用例"""
    if question is None or len(question) == 0:
        raise ValidationException("问题不能为空")
    if right_answer is None or len(right_answer) == 0:
        raise ValidationException("参考答案不能为空")
    if cate_id == 0:
        cate_id = None
    model = TestCase.get(id)
    if model.test_cate_id != cate_id:
        if model.workflow_node_log_id is not None:
            is_exist, cate_name = TestCase.is_exist_workflow_node_log(cate_id, model.workflow_node_log_id)
            if is_exist:
                raise ValidationException(f"工作流节点日志在类别【{cate_name}】下已存在，不能重复添加")
    model.question = question
    model.right_answer = right_answer
    model.note = note
    model.is_marked = is_marked
    model.is_modified = is_modified
    model.test_standard = test_standard
    if cate_id is None:
        model.test_cate_id = None
        model.update_with_foreign_key_none(True)
    else:
        model.test_cate_id = cate_id
        model.update(True)
    return {"result": "success"}


@router.post('/case/unit/batch_execute')
def case_unit_batch_execute(background_tasks: BackgroundTasks,
                            ids: list[int] = Body(description="测试用例id列表", default=None),
                            unit_llm_id: int | None = Body(description="单元测试大模型Id", default=None),
                            evaluation_llm_id: int | None = Body(description="评估大模型id", default=None),
                            evaluation_prompt_id: int | None = Body(description="评估提示词id", default=None)):
    if ids is None or len(ids) == 0:
        raise ValidationException("请选择单元测试用例")
    case_list = TestCase.query.filter(TestCase.id.in_(ids)).all()
    if case_list is None or len(case_list) == 0:
        raise ValidationException("单元测试用例不存在")
    if unit_llm_id is None or unit_llm_id <= 0:
        raise ValidationException("必须选择执行的大模型")
    if evaluation_llm_id is None or evaluation_llm_id <= 0:
        raise ValidationException("必须选择评估的大模型")
    if evaluation_prompt_id is None or evaluation_prompt_id <= 0:
        raise ValidationException("必须选择评估的提示词")
    background_tasks.add_task(asyncio.to_thread, case_execute_task, ids, None, unit_llm_id, evaluation_llm_id, evaluation_prompt_id, False, 'S')
    return {"result": "success"}


@router.post('/case/unit/import', summary='导入单元测试用例')
def case_unit_import(file: UploadFile, session: Session = Depends(get_scoped_session)):
    """导入单元测试用例"""
    folder_path = f'./src/upload_field/file_case_unit/'
    file_ext = os.path.splitext(file.filename)[1]
    if file_ext.lower() not in ['.xlsx']:
        raise ValidationException("文件格式错误，必须为excel文件xlsx")
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, f'{uuid.uuid4().hex}_{file.filename}')
    with open(file_path, 'wb') as f:
        f.write(file.file.read())
    df = pd.read_excel(file_path)
    try:
        os.remove(file_path)
    finally:
        pass
    try:
        if df.empty:
            raise ValidationException("文件为空，没有数据")
        required_columns = {'分类名称', '问题', '参考答案'}
        if not required_columns.issubset(df.columns):
            raise ValidationException("单元测试文件格式错误，必须包含'分类名称', '问题', '参考答案'列")
        # 获取所有非空，非null的分类名称
        cate_names = df['分类名称'].dropna().unique()
        cates = TestCate.query.filter(TestCate.tag == "S", TestCate.name.in_(cate_names)).all()
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
            question = str(row.get('问题')) if pd.notna(row.get('问题')) else None
            right_answer = str(row.get('参考答案')) if pd.notna(row.get('参考答案')) else None
            if (question is None or len(question) == 0) or (right_answer is None or len(right_answer) == 0):
                raise ValidationException(f"第{index}行，问题【{question}】和参考答案【{right_answer}】不能为空")
            is_modified = True if pd.notna(row.get('是否更正')) and str(row.get('是否更正')).lower() == '是' else False
            is_marked = True if pd.notna(row.get('是否审核')) and str(row.get('是否审核')).lower() == '是' else False
            test_standard = str(row.get('测试标准')) if pd.notna(row.get('测试标准')) else None
            TestCase(tag='S', test_cate_id=cate_id,
                     question=question, right_answer=right_answer,
                     is_marked=is_marked, is_modified=is_modified,
                     test_standard=test_standard).add()
            is_commit = True
        if is_commit:
            session.commit()
    except Exception as e:
        raise ValidationException(f"导入单元测试用例异常，原因：{str(e)}")
    return {"result": "success"}


@router.get('/download/case_unit_template', summary="下载---单元测试用例导入模板")
def download_case_unit_template():
    """下载商品导入模板"""
    file_path = f'./src/upload_field/template/单元测试用例模板.xlsx'
    if not os.path.exists(file_path):
        raise ValidationException("模板文件不存在")
    from starlette.responses import FileResponse
    return FileResponse(file_path, filename=os.path.basename(file_path), media_type='application/octet-stream')


@router.post('/case/unit/generate_answer', summary='LLM生成答案')
def case_unit_generate_answer(llm_id: int = Body(description="llm_id", default=None), 
                              input: str = Body(description="input", default=None),
                              vision_file_str:str|None=Body(description="视觉文件字符串",default=None)):
    """生成单元测试的答案"""
    return {"answer": llm_generate_text(llm_id, input, {},vision_file_str)}


@router.get('/case/unit/export', summary='导出单元测试用例')
def case_export(cate_id: int = Query(description="测试类别id", default=None)):
    if cate_id is None or cate_id < 0:
        raise ValidationException("请选择测试类别")
    rows = testcase_export(cate_id, 'S')
    output = BytesIO()
    pd.DataFrame(rows).to_excel(output, index=False, sheet_name=f'单元测试用例数据', engine='openpyxl')
    output.seek(0)
    cate_name = '未分类' if cate_id == 0 else rows[0].get('分类名称')
    filename = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{cate_name }.xlsx"
    encoded_filename = quote(filename, encoding='utf-8')
    content_disposition = f"attachment; filename={encoded_filename}"
    return StreamingResponse(output,
                             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": content_disposition})


@router.post('/case/unit/import_update', summary='导入单元测试用例-更新')
def case_unit_import_update(file: UploadFile, session: Session = Depends(get_scoped_session)):
    folder_path = f'./src/upload_field/file_case_unit/'
    file_ext = os.path.splitext(file.filename)[1]
    if file_ext.lower() not in ['.xlsx']:
        raise ValidationException("文件格式错误，必须为excel文件xlsx")
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
        required_columns = {'ID', '创建时间', '分类名称', '分类ID', '问题', '参考答案'}
        if not required_columns.issubset(df.columns):
            raise ValidationException("单元测试文件格式错误，必须包含'ID', '创建时间','分类名称', '分类ID', '问题', '参考答案'列")

        ids = df['ID'].dropna().unique()
        if len(ids) == 0:
            raise ValidationException("文件中没有ID列，请检查文件格式")
        cases = TestCase.query.filter(TestCase.tag == 'S', TestCase.id.in_(ids)).all()

        for row in df.to_dict(orient='records'):
            index += 1
            row_id = str(row.get('ID')) if pd.notna(row.get('ID')) else None
            cate_id = str(row.get('分类ID')) if pd.notna(row.get('分类ID')) else None
            create_time = str(row.get('创建时间')) if pd.notna(row.get('创建时间')) else None
            question = str(row.get('问题')) if pd.notna(row.get('问题')) else None
            right_answer = str(row.get('参考答案')) if pd.notna(row.get('参考答案')) else None
            note = str(row.get('备注')) if pd.notna(row.get('备注')) else None

            if row_id is None:
                raise ValidationException(f"第{index}行，ID不能为空")
            tmp_cases = list(filter(lambda x: str(x.id) == row_id, cases))
            if len(tmp_cases) == 0:
                raise ValidationException(f"第{index}行，ID【{row_id}】的数据不存在")

            current_case = tmp_cases[0]

            if str(current_case.test_cate_id) != str(cate_id):
                raise ValidationException(f"第{index}行，分类ID【{cate_id}】与原分类ID【{current_case.test_cate_id}】不一致")
            if current_case.created_at.strftime('%Y-%m-%d %H:%M:%S') != create_time:
                raise ValidationException(f"第{index}行，创建时间【{create_time}】与原创建时间【{current_case.created_at.strftime('%Y-%m-%d %H:%M:%S')}】不一致")

            is_modified = True if pd.notna(row.get('是否更正')) and str(row.get('是否更正')).lower() == '是' else False
            is_marked = True if pd.notna(row.get('是否审核')) and str(row.get('是否审核')).lower() == '是' else False
            test_standard = str(row.get('测试标准')) if pd.notna(row.get('测试标准')) else None

            current_case.question = question
            current_case.right_answer = right_answer
            current_case.is_marked = is_marked
            current_case.is_modified = is_modified
            current_case.test_standard = test_standard
            current_case.note = note
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


@router.post('/case/unit/train_cases', summary='获取单元测试关联训练用例列表', tags=['public'])
def get_train_cases(ids: list[int] | None = Body(..., embed=True, description="单元测试id列表")):
    """获取关联训练用例列表"""
    unit_cases = TestCase.query.filter(TestCase.id.in_(ids)).all()
    workflow_node_log_ids = [case.workflow_node_log_id for case in unit_cases if case.workflow_node_log_id is not None]
    train_cases = TrainCase.query.filter(or_(TrainCase.workflow_node_log_id.in_(workflow_node_log_ids), TrainCase.test_case_id.in_(ids))).all()
    seen = set()
    rows = []
    for case in unit_cases:
        if case.workflow_node_log_id is None:
            continue
        current_train_cases = list(filter(lambda x: x.test_case_id == case.id or x.workflow_node_log_id == case.workflow_node_log_id, train_cases))
        for train_case in current_train_cases:
            key = (case.id, case.workflow_node_log_id, train_case.id)
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "unit_case_id": case.id,
                "workflow_node_log_id": case.workflow_node_log_id,
                "case_id": train_case.id,
                "case_cate_id": train_case.train_cate_id,
                "case_cate_name": train_case.train_cate.name if train_case.train_cate else '未分类',
                "case_cate_color": train_case.train_cate.color if train_case.train_cate else 'red'
            })
    return {"rows": rows}

# endregion


@router.post('/case/move_cate', summary='移动用例分类')
def case_move_cate(source_cate_id: Optional[int] = Body(description="来源类别id", default=None),
                   target_cate_id: Optional[int] = Body(description="目标类别id", default=None),
                   tag: Optional[str] = Body(description="用例类型", default='S')):
    """移动用例分类"""
    TestCase.case_move_cate(source_cate_id, target_cate_id, tag)
    return {"result": "success"}



