import json

from src.agent.model_types import NodeType
from src.database.models import WorkFlow, PromptModel, ToolModel, MCPToolProvider


class FlowReplaceHelper:
    """
    替换节点信息的帮助类
    """
    @staticmethod
    def replace_llm_node_prompt(node: dict, model: PromptModel):
        node['prompt_id'] = model.id
        node['prompt_unique_code'] = model.unique_code
        node['prompt_template']['id'] = model.id
        node['prompt_template']['prompt_unique_code'] = model.unique_code
        node['prompt_template']['name'] = model.name
        node['prompt_template']['content'] = model.content
        node['prompt_template']['prompt_type_id'] = model.prompt_type_id
        return node

    # 替换大模型节点中：流程工具信息
    @staticmethod
    def replace_llm_node_function_flow(node: dict, model: WorkFlow):
        """
        替换大模型节点中：流程工具信息
            "functions": [
                {
                    "fun_name": "workflow_58",
                    "options": {
                        "workflow_id": 58,
                        "inputs": "{\"user_input\":\"\"}"
                    },
                    "name": "耗材类多跳检索工具"
                }
            ]
        :param node:
        :param model:
        :return:
        """
        node['fun_name'] = f'workflow_{model.id}'
        node['options']['workflow_id'] = model.id
        node['options']['name'] = model.name

        inputs = {}
        start_node = next((item for item in json.loads(model.data_json).get('nodes', []) if item.get('type') == NodeType.START.value), None)
        for input_item in start_node.get('inputs', []):
            inputs[input_item.get('name')] = ''
        node['options']['inputs'] = json.dumps(inputs)
        return node

    @staticmethod
    def replace_flow_node_info(node: dict, model: WorkFlow):
        FlowReplaceHelper.replace_llm_node_function_flow(node['functions'][0], model)
        node['dataItem']['id'] = model.id
        node['dataItem']['name'] = model.name
        node['dataItem']['caption'] = model.caption
        node['dataItem']['is_tool'] = model.is_tool
        node['dataItem']['use_log'] = model.use_log
        node['dataItem']['is_share'] = model.is_share
        node['dataItem']['api_key'] = model.api_key
        node['dataItem']['view_json'] = model.view_json
        node['dataItem']['data_json'] = model.data_json
        node['dataItem']['fun_name'] = f'workflow_{model.id}'
        node['dataItem']['tool'] = f'workflow_{model.id}'
        node['dataItem']['desc'] = model.caption
        node['dataItem']['options'] = node['functions'][0]['options']
        return node

    @staticmethod
    def replace_plugin_tool_info(node: dict, model: ToolModel):
        node['functions'][0]['fun_name'] = model.func_name
        node['functions'][0]['name'] = model.name
        inputs = {}
        for input_item in json.loads(model.in_params) if model.in_params is not None and model.in_params != '' else []:
            inputs[input_item.get('name')] = ''
        node['functions'][0]['options']['inputs'] = json.dumps(inputs)

        node['dataItem']['id'] = model.id
        node['dataItem']['name'] = model.name
        node['dataItem']['fun_name'] = model.func_name
        node['dataItem']['is_enable'] = model.is_enable
        node['dataItem']['api_url'] = model.api_url
        node['dataItem']['api_method'] = model.api_method
        node['dataItem']['caption'] = model.caption
        node['dataItem']['in_params'] = json.loads(model.in_params) if model.in_params is not None and model.in_params != '' else None
        node['dataItem']['out_params'] = json.loads(model.out_params) if model.out_params is not None and model.out_params != '' else None
        node['dataItem']['tool'] = model.func_name
        node['dataItem']['desc'] = model.caption
        node['dataItem']['options'] = node['functions'][0]['options']
        return node

    @staticmethod
    def replace_mcp_tool_info(node: dict, model: MCPToolProvider):
        mcp_tool_name = node.get('dataItem', {}).get('name', None)
        if mcp_tool_name is None:
            return node
        node['dataItem']['id'] = f'{model.id}_{mcp_tool_name}'
        node['dataItem']['provider_id'] = model.id
        return node

    @staticmethod
    def replace_executor_llm_node_info(node: dict, model: PromptModel):
        node = FlowReplaceHelper.replace_llm_node_prompt(node, model)
        return node
