import ast
import copy
import datetime
import json
import traceback
import uuid
from typing import List
from pydantic import TypeAdapter

from src.agent.nodes.loop_node import LoopNode
from src.agent.nodes.loop_start_node import LoopStartNode
from src.agent.tools.function_calculator import FunctionCalculator
from src.agent.tools.function_flow_node_logs import FunctionFlowNodeLogs
from src.agent.tools.function_knowledge_add import FunctionKnowledgeAdd
from src.agent.tools.function_knowledge_append import FunctionKnowledgeAppend
from src.agent.tools.function_knowledge_retrieve import FunctionKnowledgeRetrieve
from src.agent.tools.function_product_retrieve import FunctionProductRetrieve
from src.agent.tools.function_train_case_add import FunctionTrainCaseAdd
from src.agent.tools.function_unit_test_add import FunctionUnitTestAdd
from src.agent.tools.function_vectorstore_retrieve import FunctionVectorstoreRetrieve
from src.agent.nodes.llm_node import LLMNode
from src.agent.model_types import NodeType, VariablesType, ChatRoomMessage
from src.agent.nodes.temp_executor_node import TempExecutorNode
from src.agent.nodes.start_node import StartNode
from src.agent.nodes.tool_node import ToolNode
from src.agent.working.working_callback import WorkingCallback
from src.agent.working.working_graph import WorkingGraph
from src.agent.working.working_space import WorkingSpace
from src.api.customer_exception import ValidationException
from src.database.enums import LogOrigin
from src.database.models import MCPToolProvider, PromptModel, WorkFlow, WorkFlowRunLog,ToolModel
from src.rag.models.documents import Document
from src.utils.json_helper import object_to_json
from src.utils.log_helper import logger

def load_graph(workflow_id:int,json_data:str,user_id:str="",pin_id:str="",question_id:str="",current_token:str="",workflow_source_id:int|None=None,workflow_source_name:str|None=None):
    """加载图"""
    data=json.loads(json_data)
    working_space=WorkingSpace()
    working_space.register_function(FunctionKnowledgeRetrieve)
    working_space.register_function(FunctionVectorstoreRetrieve)
    working_space.register_function(FunctionProductRetrieve)
    working_space.register_function(FunctionCalculator)
    working_space.register_function(FunctionUnitTestAdd)
    working_space.register_function(FunctionTrainCaseAdd)
    working_space.register_function(FunctionKnowledgeAppend)
    working_space.register_function(FunctionFlowNodeLogs)
    working_space.register_function(FunctionKnowledgeAdd)

    flow_tools=WorkFlow.get_tool_flows()
    for tool in flow_tools:
        if tool.data_json is not None and tool.data_json!="": #刚创建还没有完成保存流程内容的不加载
            working_space.register_flow_function(flow_id=tool.id,flow_name=tool.name,flow_desc=tool.caption,flow_json=tool.data_json,use_log=tool.use_log)

    tools=ToolModel.get_tool_list()
    for tool in tools:
        if tool.is_enable:
            working_space.register_plugin_function(tool_id=tool.id,function_name=tool.func_name,tool_name=tool.name,tool_desc=tool.caption,api_url=tool.api_url,api_method=tool.api_method,in_params=tool.in_params,out_params=tool.out_params)

    mcp_tools=MCPToolProvider.get_tool_list()
    for tool in mcp_tools:
        dict_tool=tool.model_dump()
        in_params=json.dumps(dict_tool["in_params"],ensure_ascii=False)
        out_params=json.dumps(dict_tool["out_params"],ensure_ascii=False)
        working_space.register_mcp_function(provider_id=tool.provider_id,tool_name=tool.name,tool_desc=tool.caption,server_url=tool.api_url,in_params=in_params,out_params=out_params)

    working_space.config["workflow_id"]=workflow_id #工作流id
    working_space.config["user_id"]=user_id or uuid.uuid4().hex #用户id 多窗口ID
    working_space.config["pin_id"]=pin_id or uuid.uuid4().hex #客服id socket_id
    working_space.config["question_id"]=question_id or uuid.uuid4().hex #问题id 每次请求的ID
    working_space.config["current_token"]=current_token or "" #当前token
    working_space.config["workflow_source_id"]=workflow_source_id #日志来源
    working_space.config["workflow_source_name"]=workflow_source_name #日志来源

    for item in data["space_vars"]:
        working_space.init_var(item["name"],VariablesType.value_of(item["type"]))
    g=WorkingGraph([],working_space)
    for item in data["nodes"]:
        if item["type"]==NodeType.START.value:
            g.add_node(StartNode.from_dict(item))
        elif item["type"]==NodeType.LLM.value:
            #模板id查询
            id=item["prompt_id"]
            item["prompt_template"]=PromptModel.get(id).content
            g.add_node(LLMNode.from_dict(item))
        elif item["type"]==NodeType.TOOL.value:
            g.add_node(ToolNode.from_dict(item))
        elif item["type"]==NodeType.TEMP_EXECUTOR.value:
            id=item["prompt_id"]
            item["prompt_template"]=PromptModel.get(id).content
            g.add_node(TempExecutorNode.from_dict(item))
        elif item["type"]==NodeType.LOOP.value:
            g.add_node(LoopNode.from_dict(item))
    g.build_edgs_with_node()
    
    return g


def load_sub_loop_graph(graph:WorkingGraph,sub_nodes:list[dict],index):
    """
    加载子循环图，子图与主流程图，工作空间共享
    sub_nodes:子循环节点
    index:循环索引，用于区分循环节点,工作空间内角色需要用索引避免重复
    """
    
    #共享工作空间
    g=WorkingGraph([],graph.working_space)
    #在多线程下，字典属于共享数据，需要深拷贝避免共享修改
    copied_nodes = [copy.deepcopy(item) for item in sub_nodes]
    for item in copied_nodes:
        #处理节点名称冲突，循环节点名称后面添加索引
        item["role"]=item["role"]+f"_batch_{index}"
        if item.get("next_nodes",None) is not None:
            for next in item["next_nodes"]:
                next["role"]=next["role"]+f"_batch_{index}"
        if item["type"]==NodeType.LOOP_START.value:
            g.add_node(LoopStartNode.from_dict(item))
        elif item["type"]==NodeType.LLM.value:
            #模板id查询
            id=item["prompt_id"]
            item["prompt_template"]=PromptModel.get(id).content
            g.add_node(LLMNode.from_dict(item))
        elif item["type"]==NodeType.TOOL.value:
            g.add_node(ToolNode.from_dict(item))
        elif item["type"]==NodeType.TEMP_EXECUTOR.value:
            id=item["prompt_id"]
            item["prompt_template"]=PromptModel.get(id).content
            g.add_node(TempExecutorNode.from_dict(item))
        elif item["type"]==NodeType.LOOP.value:
            g.add_node(LoopNode.from_dict(item))
    g.build_edgs_with_node()
    
    return g
    


def run_graph(workflow_id:int,workflow_name:str,graph:WorkingGraph,input_dict:dict,callbacks:list[WorkingCallback]=None,use_log:bool=True):

    """运行图"""

    start_time = datetime.datetime.now()
    user_input = str(input_dict.get("user_input", None))
    error_msg = None
    try:
        graph.run(user_input=input_dict,callbacks=callbacks)
    except Exception as e:
        error_msg = str(e)

    pin_id= graph.working_space.config.get("pin_id")
    user_id= graph.working_space.config.get("user_id")
    question_id= graph.working_space.config.get("question_id")
    workflow_source_id= graph.working_space.config.get("workflow_source_id")
    workflow_source_name= graph.working_space.config.get("workflow_source_name")
    end_time = datetime.datetime.now()

    elapsed_time = f'{(end_time - start_time).total_seconds()}'

    human_message = [{
        "id":message.id,
        "message": message.message,
        "from_role": message.from_role,
        "to_role": message.to_role,
        "send_time": message.send_time.strftime("%Y-%m-%d %H:%M:%S.%f")
    } for message in graph.working_space.get_talks_to('human')] if graph.working_space.get_talks_to('human') else []

    result = {
        "inputs": input_dict,
        "output": [message["message"] for message in human_message] if human_message is not None and len(human_message) > 0 else [],
        "human_messages": human_message,
        "node_log": graph.working_space.get_logs(),
        "error_msg": error_msg,
        "question_id":question_id,
        "citations": graph.working_space.citations,
        "elapsed_time":elapsed_time
    }

    if use_log:
        log_id=WorkFlowRunLog.add_log(user_id, pin_id,
                            workflow_id, workflow_name, start_time, end_time, user_input,
                            json.dumps(input_dict, ensure_ascii=False),
                            json.dumps(result["output"], ensure_ascii=False),
                            json.dumps(result["human_messages"], ensure_ascii=False),
                            None,
                            result["node_log"],
                            json.dumps(result["citations"], ensure_ascii=False, default=lambda o: o.__dict__),
                            question_id,
                            result["error_msg"],
                            workflow_source_id=workflow_source_id,workflow_source_name=workflow_source_name)
        result["log_id"]=log_id

    return result


# 节点调试
def workflow_node_run_debug(flow_id: int, runner_node_id: str):
    """
    调试节点
    :param flow_id:
    :param runner_node_id:
    :return:
    """
    graph, current_node = _get_graph_runner_node(flow_id, runner_node_id)
    try:
        start_time = datetime.datetime.now()
        error_msg = None
        response = None
        try:
            response = current_node.run_debug(current_node, graph)
        except Exception as e:
            traceback.print_exc()
            logger.error(f"流程【{flow_id}】节点【{runner_node_id}】调试异常：{str(e)}")
            error_msg = str(e)
        end_time = datetime.datetime.now()
        elapsed_time = (end_time - start_time).total_seconds()
        variables = {}
        for key, value in graph.working_space.variables.copy().items():
            variables[key] = value['content']
        talk_messages = []
        if graph.working_space.room_messages is not None:
            talk_messages = graph.working_space.get_talks(None, None) if graph.working_space.get_talks(None, None) else []

        # 在开始时间和结束时间之间的数据，就是当前节点输出的数据
        if len(talk_messages) > 0:
            talk_messages = [message for message in talk_messages if start_time <= message.send_time <= end_time]
        filter_room_messages = [message for message in talk_messages if message.from_role == current_node.role]
        filter_human_messages = [message for message in talk_messages if message.to_role == 'human' or message.to_role is None]
        room_messages = [{
            'id': message.id,
            'message': message.message,
            'from_role': message.from_role,
            'to_role': message.to_role,
            'send_time': message.send_time.strftime("%Y-%m-%d %H:%M:%S")
        } for message in filter_room_messages]

        human_messages = [{
            "id": message.id,
            "message": message.message,
            "from_role": message.from_role,
            "to_role": message.to_role,
            "send_time": message.send_time.strftime("%Y-%m-%d %H:%M:%S.%f")
        } for message in filter_human_messages]

        result = {
            'error_msg': error_msg,
            'create_at': start_time.strftime("%Y-%m-%d %H:%M:%S"),
            'elapsed_time': elapsed_time,
            'flow_id': flow_id,
            'flow_name': graph.workflow_name,
            'human_messages': human_messages,
            'inputs': graph.working_space.inputs,
            'node_log': [],
            'output': [message["message"] for message in human_messages] if human_messages is not None and len(human_messages) > 0 else [],
        }
        if response is None:
            return result
        result['node_log'] = [
            {
                'inputs': graph.working_space.inputs,
                'output': [message["message"] for message in human_messages] if human_messages is not None and len(
                    human_messages) > 0 else [],
                'variables': variables,
                'id': uuid.uuid4().hex,
                'triggerer': current_node.role,
                'runner_id': runner_node_id,
                'runner': current_node.role,
                'runner_run_times': current_node.run_times + 1,
                'start_time': start_time.strftime("%Y-%m-%d %H:%M:%S"),
                'end_time': end_time.strftime("%Y-%m-%d %H:%M:%S"),
                'duration': elapsed_time,
                'prompt_str': response.prompt_str, 'prompt_temp': response.prompt_temp,
                'response_content': response.response.content if response.response is not None else None,
                'response_metadata': response.response.response_metadata if response.response is not None else None,
                'function_calls': object_to_json(response.function_calls),
                'room_messages': room_messages,
                'human_messages': human_messages,
                'role_variables': graph.working_space.role_output[current_node.role],
                'model_name': response.response.model if response.response is not None else None,
                'tokens': response.response.total_tokens if response.response is not None else None,
                'is_section': (response.section_results is not None and len(response.section_results) > 0),
                'is_section_sub': False,
                'runner_type': current_node._node_type.value
            }
        ]
        return result
    except ValidationException as e:
        raise ValidationException(str(e))
    except Exception as e:
        traceback.print_exc()
        logger.error(f"流程【{flow_id}】节点【{runner_node_id}】调试异常：{str(e)}")
        raise ValueError(str(e))


# 节点提示词模板调试
def workflow_node_prompt_debug(flow_id: int, runner_node_id: str, prompt_temp: str):
    graph, current_node = _get_graph_runner_node(flow_id, runner_node_id)
    try:
        return {"prompt_str": current_node._replace_prompt(prompt_temp, graph)}
    except Exception as e:
        traceback.print_exc()
        logger.error(f"流程【{flow_id}】节点【{runner_node_id}】调试异常：{str(e)}")
        raise ValueError(str(e))


# 获取节点调试graph和节点
def _get_graph_runner_node(flow_id: int, runner_node_id: str):
    graph = _load_node_debug_graph(flow_id)
    is_loop_node, loop_node_id, loop_sub_nodes = _is_loop_node(flow_id, runner_node_id)
    if not is_loop_node:
        current_node = next((x for x in graph.V if x.role_id == runner_node_id), None)
    else:
        loop_node = next((x for x in graph.V if x.role_id == loop_node_id), None)
        runner_graph = load_sub_loop_graph(graph, loop_sub_nodes, 0)
        loop_data = ast.literal_eval(loop_node._replace_prompt(loop_node.loop_traget, runner_graph))
        if len(loop_data) > 0:
            loop_data = [loop_data[0]]
        loop_context = {"index": 0, "item": loop_data}
        runner_graph.workflow_name = graph.workflow_name
        for node_item in runner_graph.V:
            node_item._set_loop_sub_node(loop_node.role_id, loop_context)
        current_node = next((x for x in runner_graph.V if x.role_id == runner_node_id), None)
        graph = runner_graph
    return graph, current_node


# 判断是否是循环节点的数据
def _is_loop_node(flow_id: int, runner_node_id: str):
    """
    判断节点是否是循环节点
    循环节点，返回parent_id，否则返回None
    :param flow_id:
    :param runner_node_id:
    :return:
    """
    flow = WorkFlow.get(flow_id)
    if flow.data_json is None:
        raise ValidationException("流程数据为空，请先保存流程")
    nodes = json.loads(flow.data_json).get("nodes", [])
    if len(nodes) == 0:
        raise ValidationException("流程节点为空，请先添加节点")
    if not any(str(d.get("id", -1)) == runner_node_id for d in nodes):
        # 主节点中不存在, 查找循环节点
        loop_nodes = [x for x in nodes if x.get("type", "") == NodeType.LOOP.value]
        if len(loop_nodes) == 0:
            raise ValidationException(f"未找到主节点{runner_node_id}")
        for step, tmp_node in enumerate(loop_nodes):
            if tmp_node.get("sub_nodes", None) is None or len(tmp_node.get("sub_nodes", [])) == 0:
                continue
            if any(str(d.get("id", -1)) == runner_node_id for d in tmp_node.get("sub_nodes", [])):
                return True, str(tmp_node.get("id", '')), tmp_node.get("sub_nodes", [])
                # return True, tmp_node.get("id")
        raise ValidationException(f"未找到循环节点{runner_node_id}")
    else:
        return False, None, None


# 加载拼装节点graph
def _load_node_debug_graph(flow_id: int):
    current_workflow = WorkFlow.get(flow_id)
    graph = load_graph(flow_id, current_workflow.data_json)
    graph.workflow_name = current_workflow.name

    last_run_log = WorkFlowRunLog.query.filter_by(flow_id=flow_id).order_by(WorkFlowRunLog.id.desc()).first()
    # last_run_log = WorkFlowRunLog.get(108783)
    if last_run_log is None:
        raise Exception("没有找到上次运行日志，无法调试节点")
    inputs = json.loads(last_run_log.inputs) if last_run_log else {}
    # user_input = inputs.get("user_input", {})

    docs = TypeAdapter(List[Document]).validate_json(last_run_log.citations)

    node_logs = last_run_log.node_logs.all()

    # region 加载当前节点 - roo_messages
    room_messages = None

    last_node_log = node_logs[-1] if node_logs else None
    if last_node_log is not None and last_node_log.room_messages is not None and len(last_node_log.room_messages) > 0:
        room_messages = TypeAdapter(List[ChatRoomMessage]).validate_json(last_node_log.room_messages)
    # endregion

    for node_log in node_logs:
        if node_log.role_variables is None:
            continue
        role_variables = node_log.role_variables
        if role_variables is None:
            continue
        graph.working_space.role_output[node_log.runner] = json.loads(role_variables)

    graph.working_space.inputs = inputs
    graph.working_space.append_doucuments(docs)
    graph.working_space.append_citations(docs)
    graph.working_space.room_messages = room_messages
    return graph


