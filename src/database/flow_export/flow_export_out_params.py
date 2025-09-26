import json

from src.agent.model_types import NodeType
from src.database.flow_export.flow_models import FlowExportBaseParams
from src.database.models import WorkFlow, PromptModel, ToolModel, MCPToolProvider


class WorkFlowOutParams(FlowExportBaseParams):
    """
    流程节点参数
    """

    def __init__(self, flow_id: int):
        super().__init__()
        self.prompts: list[PromptModel] = []
        self.flows: list[WorkFlow] = []
        self.plugin_tools: list[ToolModel] = []
        self.mcp_tools: list[MCPToolProvider] = []
        self.prompt_ids = []
        self.flow_ids = []
        self.plugin_tool_ids = []

        self.mcp_tool_ids = []
        # {"5_webSearchSogou": 5}
        self.mcp_tool_maps = {}
        self.flow_id = flow_id
        self._init_params()

    def _init_params(self):
        flow = WorkFlow.get(self.flow_id)
        get_flow_dependency_params(flow.view_json, self)
        self.flow_ids.insert(0, self.flow_id)
        self.flow_ids.reverse()
        if len(self.prompt_ids) > 0:
            self.prompts = PromptModel.query.filter(PromptModel.id.in_(self.prompt_ids)).all()
        if len(self.plugin_tool_ids) > 0:
            self.plugin_tools = ToolModel.query.filter(ToolModel.id.in_(self.plugin_tool_ids)).all()
        if len(self.mcp_tool_ids) > 0:
            self.mcp_tools = MCPToolProvider.query.filter(MCPToolProvider.id.in_(self.mcp_tool_ids)).all()
        if len(self.flow_ids) > 0:
            self.flows = WorkFlow.query.filter(WorkFlow.id.in_(self.flow_ids)).all()
        return self


# 查找流程和提示id
def get_flow_dependency_params(data: any, params: WorkFlowOutParams) -> None:
    if isinstance(data, str):
        data_dict = json.loads(data)
        if data_dict is not None:
            get_flow_dependency_params(data_dict.get('nodes'), params)
    elif isinstance(data, dict):
        # 内置工具节点
        if data.get('type') == NodeType.TOOL.value and data.get('datatype') == 'tool':
            return
        # 插件工具节点
        if data.get('type') == NodeType.TOOL.value and data.get('datatype') == 'plugin':
            _id = data.get('dataItem', {}).get('id', 0)
            if _id == '' or _id == 0 or _id in params.plugin_tool_ids:
                return
            params.plugin_tool_ids.append(_id)
            return
        if data.get('type') == NodeType.TOOL.value and data.get('datatype') == 'mcp':
            _id = data.get('dataItem', {}).get('id', None)
            if _id is None or _id == '' or _id in params.mcp_tool_maps:
                return
            _provider_id = data.get('dataItem', {}).get('provider_id', 0)

            # {"5_webSearchSogou": 5}
            params.mcp_tool_maps[_id] = _provider_id

            if _provider_id in params.mcp_tool_ids:
                return
            params.mcp_tool_ids.append(_provider_id)
            return
        # 流程工具 节点
        if data.get('type') == NodeType.TOOL.value and data.get('datatype') == 'flow':
            _id = data.get('dataItem', {}).get('id', 0)
            if _id == '' or _id == 0 or _id in params.flow_ids:
                return
            params.flow_ids.append(_id)
            _view_json = WorkFlow.get(_id).view_json
            if _view_json is None:
                return
            get_flow_dependency_params(json.loads(_view_json).get('nodes'), params)
            return
        # 大模型节点
        elif data.get('type') == NodeType.LLM.value and data.get('datatype') == 'llm':
            _id = data.get('prompt_id', 0)
            if _id != '' and _id > 0 and _id not in params.prompt_ids:
                params.prompt_ids.append(_id)
            # 大模型 节点，带有流程工具
            for func_item in data.get('functions', []):
                _tmp_func_name = func_item.get('fun_name', None)
                if _tmp_func_name in params.private_tools_name:
                    # 内置工具，跳过
                    continue
                _db_plugin_tool = ToolModel.query.filter_by(func_name=_tmp_func_name).first()
                if _db_plugin_tool is not None:
                    if _db_plugin_tool.id not in params.plugin_tool_ids:
                        params.plugin_tool_ids.append(_db_plugin_tool.id)
                    continue

                _tmp_flow_id = func_item.get('options', {}).get('workflow_id', 0)
                if _tmp_flow_id == '' or _tmp_flow_id == 0:
                    # 其他工具【工具插件，mcp插件】........跳过。。。。。。。

                    continue
                # 流程工具
                if _tmp_flow_id in params.mcp_tool_maps:
                    continue
                params.flow_ids.append(_tmp_flow_id)
                _view_json = WorkFlow.get(_tmp_flow_id).view_json
                if _view_json is not None:
                    get_flow_dependency_params(json.loads(_view_json).get('nodes'), params)

        # 执行器节点
        elif data.get("type") == NodeType.TEMP_EXECUTOR.value and data.get('datatype') == 'llm':
            _id = data.get('prompt_id', 0)
            if _id == '':
                _id = 0
            if _id > 0 and _id not in params.prompt_ids:
                params.prompt_ids.append(_id)
        else:
            # 老数据可能没有 总结员节点 没有 节点没有 datatype, 目前发现只有 llm 节点有，其他节点没有
            if data.get('type') != NodeType.LLM.value:
                return
            _prompt_id = data.get('prompt_id', 0)
            if _prompt_id != '' and _prompt_id > 0:
                data['datatype'] = 'llm'
                if _prompt_id not in params.prompt_ids:
                    params.prompt_ids.append(_prompt_id)
    elif isinstance(data, list):
        for item in data:
            if (item.get('data', {}).get('type') == NodeType.START.value
                    or item.get('data', {}).get('type') == NodeType.WORK_SPACE.value
                    or item.get('data', {}).get('type') == '-99'
                    or item.get('data', {}).get('type') == NodeType.LOOP.value
                    or item.get('data', {}).get('type') == NodeType.LOOP_START.value):
                continue
            get_flow_dependency_params(item.get("data"), params)
