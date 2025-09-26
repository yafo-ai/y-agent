import asyncio
import datetime
import json
import os
import shutil
import uuid
from typing import Any, List, Dict

from fastapi import APIRouter, Depends, Body, Path, Query, Request, UploadFile, BackgroundTasks
from sqlalchemy import func, or_

from src.agent.model_types import NodeType
from src.api.customer_exception import ValidationException
from src.database.enums import LogOrigin
from src.database.flow_export.flow_export_in import WorkFlowExportIn
from src.database.flow_export.flow_export_out import WorkFlowExportOut
from src.database.flow_export.flow_models import flow_file_in_path
from src.database.models import WorkFlow, WorkFlowRunLog, WorkFlowRunLogScore, TestCase, TrainCase, WorkFlowRunNodeLog, WorkFlowCategory, ModelConfig

from src.database.db_session import get_scoped_session
from sqlalchemy.orm import Session

from src.agent.working.working_manager import load_graph, run_graph, workflow_node_run_debug, \
    workflow_node_prompt_debug
from src.utils.file_helper import FileHelper
from src.utils.json_helper import parse_nested_json
from src.utils.time_helper import parse_str_to_time
from starlette.responses import FileResponse

router = APIRouter(
    prefix="/api/workflow",
    tags=["流程图"],
)


@router.post("", summary="列表")
def get_workflows(page: int = Body(description="页码", default=1),
                  pagesize: int = Body(description="每页数量", default=10),
                  category_id: int | None = Body(description="分类ID 【0：未分类， 不传或者None：全部】", default=None),
                  session: Session = Depends(get_scoped_session)
                  ):
    flows = session.query(WorkFlow)
    if category_id is not None and category_id == 0:
        flows = flows.filter(or_(WorkFlow.category_id.is_(None), WorkFlow.category_id == 0))
    elif category_id is not None and category_id > 0:
        flows = flows.filter_by(category_id=category_id)
    total_records = flows.count()
    if total_records == 0:
        return {"total_records": 0, "total_pages": 0, "rows": []}
    page_rows = flows.offset((page - 1) * pagesize).limit(pagesize).all()
    total_pages = (total_records + pagesize - 1) // pagesize
    if not flows:
        return {"total_records": 0, "total_pages": 0, "rows": []}
    rows = [
        {
            "id": doc.id,
            "name": doc.name,
            "caption": doc.caption,
            "is_tool": doc.is_tool,
            "use_log": doc.use_log,
            # "view_json": doc.view_json,
            # "data_json": doc.data_json,
            "is_share": doc.is_share,
            "api_key": doc.api_key,
            "category_name": doc.category_name,
            "category_id": doc.category_id,
            "sources": [{"source_id": source.id, "source_name": source.name, "api_key": source.api_key} for source in doc.sources] if doc.sources else []

        } for doc in page_rows
    ]
    return {"total_records": total_records, "total_pages": total_pages, "rows": rows}


@router.post("/tool_flows", summary="工具列表")
def get_tool_flows(session: Session = Depends(get_scoped_session)):
    """获取工具类型工作流列表"""
    flows = WorkFlow.get_tool_flows()
    if not flows or len(flows) == 0:
        return []
    rows = [
        {
            "id": doc.id,
            "name": doc.name,
            "caption": doc.caption,
            "is_tool": doc.is_tool,
            "use_log": doc.use_log,
            "view_json": doc.view_json,
            "data_json": doc.data_json,
            "is_share": doc.is_share,
            "api_key": doc.api_key,
            "category_name": doc.category_name,
            "category_id": doc.category_id

        } for doc in flows
    ]
    return rows


@router.post('/baseinfo/add', summary='新增流程基本信息')
def baseinfo_add(name: str = Body(description="名称", default=None),
                 is_tool: bool = Body(description="是否为工具", default=False),
                 use_log: bool = Body(description="是否记录日志", default=True),
                 is_share: bool = Body(description="是否允许分享", default=False),
                 category_id: int | None = Body(description="分类ID", default=0),
                 category_name: str | None = Body(description="分类名称", default=None),
                 caption: str | None = Body(description="介绍", default=None),
                 sources: List[Dict[str, Any]] = Body(description="标签", default=None)):
    """
    新增
    - @param id: 工作流ID
    - @param name:工作流名称
    - @param caption:工作流标题
    - @param is_tool:是否为工具
    - @param use_log:是否记录日志
    - @param is_share:是否允许分享
    - @param category_id:分类ID
    - @param category_name:分类名称
    - @param sources:来源 [{'source_id': 1, 'source_name': '来源名称', 'api_key': 'api_key'}]
    - @param session:
    - @return:
    """
    model = WorkFlow.baseinfo_add_update(None, name, caption=caption,
                                         is_tool=is_tool, use_log=use_log, is_share=is_share,
                                         category_id=category_id, category_name=category_name,
                                         sources=sources)
    return {"id": model.id}


@router.post('/baseinfo/update', summary='更新流程基本信息')
def baseinfo_update(id: int = Body(description="ID", default=None),
                    name: str = Body(description="名称", default=None),
                    is_tool: bool = Body(description="是否为工具", default=False),
                    use_log: bool = Body(description="是否记录日志", default=True),
                    is_share: bool = Body(description="是否允许分享", default=False),
                    category_id: int | None = Body(description="分类ID", default=0),
                    category_name: str | None = Body(description="分类名称", default=None),
                    caption: str | None = Body(description="介绍", default=None),
                    sources: List[Dict[str, Any]] = Body(description="标签", default=None)):
    WorkFlow.baseinfo_add_update(id, name, caption=caption,
                                 is_tool=is_tool, use_log=use_log, is_share=is_share,
                                 category_id=category_id, category_name=category_name,
                                 sources=sources)
    return {"result": "success"}


@router.post('/view_edit', summary='编辑流程视图')
def view_edit(id: int = Body(description="ID", default=None),
              view_json: str = Body(description="视图JSON", default=None)):
    WorkFlow.get(id).flow_view_edit(view_json)
    return {"result": "success"}

@router.get("/{id}", summary="详情")
def get_flow(id: int = Path(description="工作流ID"),
             session: Session = Depends(get_scoped_session)
             ):
    model = WorkFlow.get(id)
    return {
        "id": model.id,
        "name": model.name,
        "caption": model.caption,
        "is_tool": model.is_tool,
        "use_log": model.use_log,
        "view_json": model.view_json,
        "is_share": model.is_share,
        "category_name": model.category_name,
        "category_id": model.category_id,
        "sources": [{"source_id": source.id, "source_name": source.name, "api_key": source.api_key} for source in model.sources] if model.sources else []
    }


@router.get("/shareinfo/{id}", summary="详情", tags=["public"])
def get_flow_public(id: int = Path(description="工作流ID"),
                    api_key: str = Query(description="API密钥", default=None)):
    model = WorkFlow.get(id)
    model.validate_api_key(api_key)
    return {"id": model.id, "name": model.name, "caption": model.caption, "is_tool": model.is_tool,"use_log":model.use_log, "view_json": model.view_json, "is_share": model.is_share}


@router.post("/{id}/delete", summary="删除")
def delete_flow(id: int = Path(description="工作流ID"),
                session: Session = Depends(get_scoped_session)
                ):
    WorkFlow.get(id).delete_flow()
    return {"result": "success"}


@router.get("/{id}/input", summary="获取输入参数")
def get_input(id: int = Path(description="工作流ID"),
              session: Session = Depends(get_scoped_session)
              ):
    model = WorkFlow.get(id)
    inputs = model.get_flow_input()
    return inputs


# 运行工作流
@router.post("/run", summary="运行")
def run_flow(request: Request, id: int = Body(description="工作流ID"),
             inputs: Any = Body(description="输入参数", default=None),
             use_log: bool = Body(description="是否记录日志", default=False),
             workflow_source_id: int = Body(description="工作流来源id", default=None),
             workflow_source_name: str = Body(description="工作流来源名称", default='流程试运行'),
             session: Session = Depends(get_scoped_session),
             ):
    model = WorkFlow.get(id)
    if model.data_json is None:
        return ValidationException("该工作流没有数据，无法运行")

    # 验证输入inputs
    try:
        json.loads(inputs)
    except Exception as e:
        return ValidationException("输入不是JSON格式")

    # 将嵌套的json字符串转换成字典
    input_dict = parse_nested_json(json.loads(inputs))

    # 验证指定必填key
    user_input = str(input_dict.get("user_input", None))
    if user_input is None or len(user_input) == 0:
        raise ValidationException("user_input输入参数不能为空")

    _flow_check(model.data_json)
  
    current_token=request.headers.get("Authorization")

    # 试运行默认记录日志，False时，需要适用模型配置。
    use_log=model.use_log if not use_log else use_log

    graph = load_graph(id, model.data_json, current_token=current_token, workflow_source_id=workflow_source_id, workflow_source_name=workflow_source_name)
    result = run_graph(model.id,model.name,graph,input_dict,use_log=use_log)
    return result


@router.post('/shareinfo/run', summary='分享运行', tags=["public"])
def run_flow_public(request: Request,
                    id: int = Body(description="工作流ID"),
                    inputs: Any = Body(description="输入参数", default=None),
                    use_log: bool = Body(description="是否记录日志", default=False),
                    api_key: str = Body(description="API密钥", default=None)
                    ):
    flow = WorkFlow.get(id)
    flow.validate_api_key(api_key)
    source_info = flow.get_source_info_by_key(api_key)
    return run_flow(request, id, inputs, use_log, source_info.get("id"), source_info.get("name"))


# 流程节点验证
def _flow_check(flow_data_json_str):
    data_json = json.loads(flow_data_json_str)
    if data_json.get("nodes", None) is None:
        raise ValidationException("该工作流没有节点，无法运行")
    nodes = [node for node in data_json.get("nodes") if node.get("type") != "start"]
    if nodes is None or len(nodes) == 0:
        raise ValidationException("该工作流没有节点，无法运行")
    relationships_roles = []
    role_names = [node.get("role") for node in nodes]
    for node in data_json.get("nodes"):
        if node.get('type') == NodeType.START.value:
            if node.get('next_nodes', None) is None or len(node.get('next_nodes')) == 0:
                raise ValidationException("开始节点没有下一步节点，无法运行")
            relationships_roles = relationships_roles + [next_node.get("role") for next_node in node.get('next_nodes')]
            continue
        if node.get("role") is None or node.get("role") == "":
            raise ValidationException(f"节点角色名称为空，无法运行")
        if node.get("description") is None or node.get("description") == "":
            raise ValidationException(f"角色【{node.get('role')}】没有角色介绍，无法运行")
        if node.get("type") == NodeType.LLM.value:
            if node.get("llm_id") is None or node.get("llm_id") == "":
                raise ValidationException(f"角色【{node.get('role')}】没有选择大模型，无法运行")
            if node.get("prompt_id") is None or node.get("prompt_id") == "":
                raise ValidationException(f"角色【{node.get('role')}】没有选择提示词，无法运行")
        if node.get("type") == NodeType.TEMP_EXECUTOR.value:
            if node.get("prompt_id") is None or node.get("prompt_id") == "":
                raise ValidationException(f"角色【{node.get('role')}】没有选择提示词，无法运行")
        # PromptModel.get(int(node.get("prompt_id")))
        for next_node in node.get("next_nodes", []):
            relationships_roles.append(next_node.get("role"))
    if len(relationships_roles) > 0:
        relationships_roles = list(set(relationships_roles))
        for role in role_names:
            if role not in relationships_roles:
                raise ValidationException(f"角色【{role}】工作流关系不完整，无法运行")


# 流程日志
@router.post("/logs_pagination", summary="日志列表")
def get_logs(flow_log_id: int | None = Body(description="工作流ID", default=None),
             flow_name: str | None = Body(description="工作流名称", default=None),
             page: int = Body(description="页码", default=1),
             pagesize: int = Body(description="每页数量", default=10),
             user_id: str = Body(description="用户ID", default=None),
             conversation_id: str = Body(description="对话ID", default=None),
             created_at_start: str = Body(description="创建时间开始", default=None),
             created_at_end: str = Body(description="创建时间结束", default=None),
             question: str = Body(description="问题", default=None),
             test_cate_id: int = Body(description="测试分类", default=None),
             flow_id: int | None = Body(description="流程ID", default=None),
             source_id: int | None = Body(description="来源ID", default=None),
             source_name: str | None = Body(description="来源名称", default=None)
             ):
    return WorkFlowRunLog.get_pagination(flow_log_id, flow_id, flow_name, source_id, source_name,
                                         user_id, conversation_id, test_cate_id,
                                         created_at_start, created_at_end, question,
                                         page, pagesize)


@router.post("/rating_score", summary="给回答评分", tags=["public"])
def rating_score(log_id:int = Body(description="流程日志id，执行流程时会返回log_id字段"),
                  score: int = Body(description="评分，分数0、10"),
                  amend_answer: str = Body(description="修正后的回答，用于收集正确答案"),
                  answer_id:str = Body(description="回答ID，执行流程时返回的human_messages中的id字段"),
                  api_key: str = Body(description="对应流程的apikey密钥")):
    """
    给回答评分
    """
    if score < 0 or score > 10:
        raise ValidationException("评分必须在0-10之间")
    if answer_id is None or answer_id == "":
        raise ValidationException("回答ID不能为空")
    if api_key is None or api_key == "":
        raise ValidationException("API密钥不能为空")
    
    log = WorkFlowRunLog.get(log_id)
    flow = WorkFlow.get(log.flow_id)
    flow.validate_api_key(api_key)

    human_messages=json.loads(log.human_messages) if log.human_messages else None
    if human_messages is None or len(human_messages) == 0:
        raise ValidationException("日志中没有消息，无法评分")
    
    role = None
    for msg in human_messages:
        if msg.get("id") == answer_id:
            role = msg.get("from_role")
            break
    if role is None:
        raise ValidationException("回答ID不存在")

    WorkFlowRunLogScore.feedback_result(question_id=log.question_id,score=score,amend_answer=amend_answer,role=role,answer_id=answer_id)

    return {"result": "success"}


@router.get("/log/scores", summary="获取日志评分")
def get_log_scores(question_id:str):
    """获取日志评分"""
    return WorkFlowRunLogScore.get_score_by_question_id(question_id)


@router.get("/log/detail/{id}", summary="日志详情")
def get_log_detail(id: int = Path(description="日志ID"),
                   session: Session = Depends(get_scoped_session)
                   ):
    log = WorkFlowRunLog.get(id)
    if not log:
        return ValidationException("日志不存在")
    agv_scores_dict = WorkFlowRunLogScore.get_avg_score([str(log.question_id)])

    log_dict = {
        "id": log.id,
        "ai_run_id": log.ai_run_id,
        "conversation_id": log.conversation_id,
        "user_input": log.user_input,
        "inputs": json.loads(log.inputs) if log.inputs else None,
        "output": json.loads(log.outputs) if log.outputs else [],
        "citations": json.loads(log.citations) if log.citations else None,
        "human_messages": json.loads(log.human_messages) if log.human_messages else None,
        "memory": log.memory,
        "flow_id": log.flow_id,
        "flow_name": log.flow_name,
        "use_tools": log.use_tools,
        "elapsed_time": log.elapsed_time,
        "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else None,
        "score": agv_scores_dict.get(log.question_id, None) if log.question_id else None,
        "error_msg": log.error_msg,
        "question_id":log.question_id,
        "node_log": []
    }

    test_cates = TestCase.get_case_cates_by_workflow_log_ids([log.id])
    log_dict["test_cates"] = test_cates.get(str(log.id), [])

    train_cates = TrainCase.get_cate_by_workflow_log_ids([log.id])
    log_dict["train_cates"] = train_cates.get(str(log.id), [])

    for node_log in log.node_logs if log.node_logs else []:
        log_dict["node_log"].append({
            "detail_id": node_log.id,
            "id": node_log.agent_run_log_id,
            "pid": node_log.pid,
            "triggerer": node_log.triggerer,
            "runner_id":node_log.runner_id,
            "runner": node_log.runner,
            "runner_run_times": node_log.runner_run_times,
            "start_time": node_log.start_time.strftime("%Y-%m-%d %H:%M:%S.%f") if node_log.start_time else None,
            "end_time": node_log.end_time.strftime("%Y-%m-%d %H:%M:%S.%f") if node_log.end_time else None,
            "duration": node_log.duration,
            "prompt_temp": node_log.prompt_temp,
            "prompt_str": node_log.prompt_str,
            "vision_file_str": node_log.vision_file_str,
            "response_content": node_log.response_content,
            "response_metadata": json.loads(node_log.response_metadata) if node_log.response_metadata else None,
            "function_calls": json.loads(node_log.function_calls) if node_log.function_calls else None,
            "room_messages": json.loads(node_log.room_messages) if node_log.room_messages else None,
            "inputs": json.loads(node_log.inputs) if node_log.inputs else None,
            "variables": json.loads(node_log.variables) if node_log.variables else None,
            "role_variables": json.loads(node_log.role_variables) if node_log.role_variables else None,
            "model_name": node_log.model_name,
            "tokens": node_log.tokens,
            "is_section": node_log.is_section if node_log.is_section else False,
            "is_section_sub": node_log.is_section_sub if node_log.is_section_sub else False,
            "runner_type": node_log.runner_type,
            "cate": [{"cate_id": cate.get("cate_id"), "name": cate.get("name"), "color": cate.get("color")} for cate in log_dict["train_cates"] if
                     cate.get("node_id") == node_log.id],
            "unit_cate": [{"cate_id": cate.get("cate_id"), "name": cate.get("name"), "color": cate.get("color"), "tag": cate.get("tag")} for cate in log_dict["test_cates"] if
                     cate.get("node_id") == node_log.id and cate.get("tag") == "S"]
        })
    return log_dict


@router.post('/node_logs', summary="获取节点信息", tags=["public"])
def get_node_logs(flow_id: int = Body(description="节点日志ID"),
                            role_id: str = Body(description="节点ID", default=None),
                            start_time: str = Body(description="开始时间", default=None),
                            end_time: str = Body(description="结束时间", default=None),
                            session: Session = Depends(get_scoped_session)
                            ):
    """获取节点日志的输入输出信息"""
    if flow_id is None or flow_id <= 0:
        raise ValidationException("流程ID不能为空")
    if start_time is None or end_time is None:
        raise ValidationException("开始时间和结束时间不能为空")
    start_time = parse_str_to_time(start_time)
    end_time = parse_str_to_time(end_time)
    node_logs = []
    if role_id is not None and role_id !="":
        logs = WorkFlowRunNodeLog.query.filter(
                WorkFlowRunNodeLog.run_log.has(flow_id=flow_id,origin=LogOrigin.京东咚咚.value),
                WorkFlowRunNodeLog.runner_id == role_id,
                WorkFlowRunNodeLog.start_time.between(start_time, end_time)).all()
    else:
        logs = WorkFlowRunNodeLog.query.filter(
                WorkFlowRunNodeLog.run_log.has(flow_id=flow_id,origin=LogOrigin.京东咚咚.value),
                WorkFlowRunNodeLog.start_time.between(start_time, end_time)).all()

    for log in logs:
        if log.prompt_str is None or log.prompt_str == "" or log.response_content is None or log.response_content == "":
            continue
        log_dict = {
            "log_id":log.run_log_id,
            "node_log_id":log.id,
            "role_id": log.runner_id,
            "role": log.runner,            
            "input": log.prompt_str,
            "output": log.response_content,
        }
        node_logs.append(log_dict)
    return {"count": len(node_logs), "rows": node_logs}


@router.post('/copy', summary='复制工作流')
def copy_workflow(flow_id: int | None = Query(description="流程ID", default=None)):
    """复制工作流"""
    if flow_id is None or flow_id <= 0:
        raise ValidationException("流程ID不能为空")
    flow = WorkFlow.get(flow_id)
    sources = flow.sources.all()
    flow_sources = [{"source_id": source.id, "source_name": source.name, "api_key": source.api_key} for source in sources]
    model = WorkFlow().add_update_flow(flow.name+'_副本', flow.caption,
                                       flow.view_json, flow.data_json,
                                       flow.is_tool, flow.use_log,
                                       False,
                                       flow.category_id, flow.category_name, flow_sources)
    return {"id": model.id}


@router.get('/export/{flow_id}', summary='导出工作流')
def export_workflow(background_tasks: BackgroundTasks, flow_id: int | None = Path(description="流程ID", default=...)):
    """导出工作流"""
    if flow_id is None or flow_id <= 0:
        raise ValidationException("流程ID不能为空")
    file_path = WorkFlowExportOut(flow_id).export_out()
    return FileResponse(
        file_path,
        filename=os.path.basename(file_path),
        media_type='application/octet-stream',
        background=background_tasks.add_task(asyncio.to_thread, FileHelper.delete_file, file_path)
    )


@router.post('/import', summary='导入工作流')
def import_workflow(file: UploadFile):
    """导入工作流"""
    os.makedirs(flow_file_in_path, exist_ok=True)
    file_path = os.path.join(flow_file_in_path, file.filename)
    with open(file_path, 'wb') as buffer:
        shutil.copyfileobj(file.file, buffer)
    llm_id = 0
    model = ModelConfig.query.first()
    if model is not None:
        llm_id = model.id
    export_in = WorkFlowExportIn(file_path, llm_id)
    export_in.export_in()
    export_in.delete_files()
    return {"result": "success"}


@router.post('/node_run_debug', summary='调试节点')
def node_run_debug(flow_id: int = Body(description="流程ID"),
                   runner_id: str = Body(description="节点ID")):
    """调试节点"""
    if runner_id is None or runner_id == "":
        raise ValidationException("节点ID不能为空")
    if flow_id is None or flow_id <= 0:
        raise ValidationException("流程ID不能为空")
    return workflow_node_run_debug(flow_id, runner_id)


@router.post('/node_prompt_debug', summary='调试节点提示词')
def node_prompt_debug(flow_id: int = Body(description="流程ID"),
                      runner_id: str = Body(description="节点ID"),
                      prompt_temp: str = Body(description="提示词模板")
                      ):
    """调试节点"""
    if runner_id is None or runner_id == "":
        raise ValidationException("节点ID不能为空")
    if prompt_temp is None or prompt_temp == "":
        raise ValidationException("提示词模板不能为空")
    if flow_id is None or flow_id <= 0:
        raise ValidationException("流程ID不能为空")
    return workflow_node_prompt_debug(flow_id, runner_id, prompt_temp)


# region 流程分类相关
@router.get('/category/tree', summary='获取分类树')
def get_category_tree():
    return WorkFlowCategory.tree()


@router.post('/category/add', summary="添加分类")
def add_category(name: str = Body(description="名称"),
                 note: str = Body(description="备注", default=None),
                 pid: int | None = Body(description='父id', default=None)):
    return WorkFlowCategory.add_category(name=name, note=note, pid=pid)


@router.post('/category/edit', summary="修改分类")
def edit_category(id: int = Body(description="类型id"),
                  name: str = Body(description="名称"),
                  note: str = Body(description="备注", default=None),
                  pid: int = Body(description='父id', default=None)):
    return WorkFlowCategory.get(id).edit_category(name=name, note=note, pid=pid)


@router.post('/category/{id}/delete', summary="删除分类")
def delete_category(id: int = Path(description="分类id", default=...)):
    return WorkFlowCategory.get(id).delete_category()

# endregion


@router.get('/list/all', summary='获取所有工作流')
def get_flows():
    flows = WorkFlow.query.all()
    rows = [
        {
            "flow_id": flow.id,
            "flow_name": flow.name,
            "sources": [{"source_id": source.id, "source_name": source.name, "flow_id": flow.id} for source in flow.sources.all()],
        }for flow in flows
    ]
    return {"result": "success", "rows": rows}
