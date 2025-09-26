from typing import Dict, List
from src.agent.model_types import McpTool, ToolInParam
from src.database.models import MCPToolProvider


def adapt_mcp_tool(provider:MCPToolProvider,mcp_tool: Dict) -> McpTool:
    
    # 提取输入参数
    in_params = []
    if  "properties" in mcp_tool.inputSchema:
        in_params = convert_json_schema_to_in_params(
            mcp_tool.inputSchema["properties"],
            mcp_tool.inputSchema.get("required", [])
        )
    
    # 创建ToolDto实例
    tool_dto = McpTool(
        provider_id=provider.id,
        id=str(provider.id)+"_"+mcp_tool.name,
        name=mcp_tool.name,
        func_name=mcp_tool.name,
        caption=mcp_tool.description,
        is_enable=True,  # 默认启用
        api_url=provider.server_url,  
        api_method="POST", 
        in_params=in_params,
        out_params=[]
    )

    return tool_dto

def convert_json_schema_to_in_params(properties: Dict, required_fields: List[str] = []) -> List[ToolInParam]:
    """将JSON Schema属性转换为输入参数DTO列表"""
    params = []
    
    for param_name, param_schema in properties.items():
        param_dto = ToolInParam(
            id=param_name,  # 或使用其他ID生成方式
            name=param_name,
            caption=param_schema.get("description", param_name),
            param_way="Body",
            data_type=convert_json_schema_type(param_schema.get("type", "string")),
            default_value=str(param_schema.get("default", "")),
            is_required=param_name in required_fields,
            children=convert_json_schema_to_in_params(
                param_schema.get("properties", {}),
                param_schema.get("required", [])
            ) if param_schema.get("type") == "object" else []
        )
        params.append(param_dto)
    
    return params

def convert_json_schema_type(json_schema_type: str) -> str:
    """将JSON Schema类型转换为系统类型"""
    type_mapping = {
        "string": "String",
        "number": "Number",
        "integer": "Integer",
        "boolean": "Boolean",
        "object": "Object",
        "array": "Array<String>",
    }
    return type_mapping.get(json_schema_type, "str")  # 默认返回str