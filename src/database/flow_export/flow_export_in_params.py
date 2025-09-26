import json

from src.database.flow_export.flow_models import FlowExportBaseParams
from src.database.flow_export.flow_replace import FlowReplaceHelper
from src.agent.model_types import NodeType
from src.database.models import WorkFlow, PromptModel, ToolModel, MCPToolProvider


class WorkFlowImportInParams(FlowExportBaseParams):
    """
    导入流程时，需要替换的节点信息
    """

    def __init__(self, default_llm_id=0):
        super().__init__()
        self.default_llm_id = default_llm_id
        # [{"target_id": None, "source_id": item.get('id')}]
        # target_id: 数据库中存在的id  source_id: 导入文件中的id
        self.prompt_relations: list[dict[str, int]] = []
        self.plugin_tools_relations: list[dict[str, int]] = []
        self.mcp_tools_relations: list[dict[str, int]] = []
        self.flow_relations: list[dict[str, int]] = []


        # 插件工具映射 [{'product_topic', 6}]
        self.plugin_tools_name = []


def replace_json_data(data, in_params: WorkFlowImportInParams):
    if isinstance(data, list):
        for item in data:
            if (item.get('data', {}).get('type') == NodeType.START.value
                    or item.get('data', {}).get('type') == NodeType.WORK_SPACE.value
                    or item.get('data', {}).get('type') == '-99'
                    or item.get('data', {}).get('type') == NodeType.LOOP.value
                    or item.get('data', {}).get('type') == NodeType.LOOP_START.value):
                continue
            replace_json_data(item.get('data', {}), in_params)
        return
    if isinstance(data, dict):
        # 内置工具，跳过
        if data.get('type') == NodeType.TOOL.value and data.get('datatype') == 'tool':
            return
        # 插件工具，替换
        if data.get('type') == NodeType.TOOL.value and data.get('datatype') == 'plugin':
            _tool_id = data.get('dataItem', {}).get('id', 0)
            if _tool_id == '' or _tool_id == 0:
                return
            tmp_tool = next((tool for tool in in_params.plugin_tools_relations if tool.get('source_id') == _tool_id), None)
            if tmp_tool is None:
                return
            db_tool = ToolModel.get(tmp_tool.get('target_id'))
            FlowReplaceHelper.replace_plugin_tool_info(data, db_tool)
        # mcp工具
        elif data.get('type') == NodeType.TOOL.value and data.get('datatype') == 'mcp':
            _mcptool_id = data.get('dataItem', {}).get('provider_id', 0)
            if _mcptool_id == '' or _mcptool_id == 0:
                return
            tmp_mcptool = next((mcptool for mcptool in in_params.mcp_tools_relations if mcptool.get('source_id') == _mcptool_id), None)
            if tmp_mcptool is None:
                return
            db_mcptool = MCPToolProvider.get(tmp_mcptool.get('target_id'))
            FlowReplaceHelper.replace_mcp_tool_info(data, db_mcptool)
        # 流程工具 节点
        elif data.get('type') == NodeType.TOOL.value and data.get('datatype') == 'flow':
            _flow_id = data.get('dataItem', {}).get('id', 0)
            if _flow_id == '' or _flow_id == 0:
                return
            tmp_flow = next((flow for flow in in_params.flow_relations if flow.get('source_id') == _flow_id), None)
            if tmp_flow is None:
                return
            db_flow = WorkFlow.get(tmp_flow.get('target_id'))
            FlowReplaceHelper.replace_flow_node_info(data, db_flow)
        # 大模型节点
        elif data.get('type') == NodeType.LLM.value and data.get('datatype') == 'llm':
            """
            需要替换 1：提示词 2：工具【内置工具，插件工具，mcp工具】
            """
            data['llm_id'] = in_params.default_llm_id
            # 1：提示词
            _prompt_id = data.get('prompt_id', 0)
            if _prompt_id != '' and _prompt_id > 0:
                tmp_prompt = next((prompt for prompt in in_params.prompt_relations if prompt.get('source_id') == _prompt_id), None)
                if tmp_prompt is not None:
                    db_prompt = PromptModel.get(tmp_prompt.get('target_id'))
                    FlowReplaceHelper.replace_llm_node_prompt(data, db_prompt)

            # 2：工具
            for func_item in data.get('functions', []):
                _func_name = func_item.get('fun_name', None)
                if _func_name == '' or _func_name is None:
                    continue
                # 内置工具
                if _func_name in in_params.private_tools_name:
                    continue
                # 插件工具
                _plugin_tool_dict = next((d for d in in_params.plugin_tools_name if _func_name in d), None)
                if _plugin_tool_dict is not None:
                    continue
                # 流程工具
                _tmp_workflow_id = func_item.get('options', {}).get('workflow_id', 0)
                if _tmp_workflow_id != '' and _tmp_workflow_id > 0:

                    tmp_flow = next((flow for flow in in_params.flow_relations if flow.get('source_id') == _tmp_workflow_id), None)
                    if tmp_flow is None:
                        continue
                    db_flow = WorkFlow.get(tmp_flow.get('target_id'))
                    FlowReplaceHelper.replace_llm_node_function_flow(func_item, db_flow)
                    continue
                # mcp工具
                pass
        # 执行器节点
        elif data.get("type") == NodeType.TEMP_EXECUTOR.value and data.get('datatype') == 'llm':
            data['llm_id'] = in_params.default_llm_id
            _prompt_id = data.get('prompt_id', 0)
            if _prompt_id == '' or _prompt_id == 0:
                return
            tmp_prompt = next((prompt for prompt in in_params.prompt_relations if prompt.get('source_id') == _prompt_id), None)
            if tmp_prompt is None:
                return
            db_prompt = PromptModel.get(tmp_prompt.get('target_id'))
            FlowReplaceHelper.replace_executor_llm_node_info(data, db_prompt)
        else:
            # 其他节点， 老数据可能没有datatype字段
            pass
        return

    # 其他数据类型
    pass


def test_replace():
    in_params = WorkFlowImportInParams()

    flow_json_dict = json.loads(WorkFlow.get(92).view_json).get('nodes')
    replace_json_data(flow_json_dict, in_params=in_params)


if __name__ == '__main__':
    test_replace()
    pass
