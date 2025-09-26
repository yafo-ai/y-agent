import json
from typing import Dict, List
from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.orm import Session
from src.database.db_session import get_scoped_session
from src.database.models import MCPToolProvider


router = APIRouter(
    prefix="/api/mcp_provider",
    tags=["MCP工具提供方管理"],
)

@router.get("", summary="MCP工具提供方列表")
def get_providers(page: int = Query(description="页码", default=1),
                       pagesize: int = Query(description="每页数量", default=10),
                       keyword: str | None = Query(description="关键词", default=None),
                       session: Session = Depends(get_scoped_session)
                       ):
    """条件分页查询"""
    conditions = {}
    if keyword:
        providers = session.query(MCPToolProvider).filter_by(**conditions).filter(MCPToolProvider.name.ilike(f"%{keyword}%")).offset(pagesize * (page - 1)).limit(pagesize).all()
    else:
        providers = session.query(MCPToolProvider).filter_by(**conditions).offset(pagesize * (page - 1)).limit(pagesize).all()

    total_records = session.query(MCPToolProvider).count()
    total_pages = (total_records + pagesize - 1) // pagesize

    if not providers:
        return {"total_records": total_records, "total_pages": total_pages, "rows": []}
    
    rows = [{
            "id": provider_instance.id,
            "name": provider_instance.name,
            "server_identifier": provider_instance.server_identifier,
            "server_url": provider_instance.server_url,
            "authed": provider_instance.authed,
            "tools": provider_instance.mcp_tools,
            "selected_tools": provider_instance.selected_mcp_tools,
            "timeout": provider_instance.timeout,
            "sse_read_timeout": provider_instance.sse_read_timeout,
            "headers": provider_instance.headers,
            "created_at": provider_instance.created_at,
            "updated_at": provider_instance.updated_at,
        } for provider_instance in providers]
    
    return {"total_records": total_records, "total_pages": total_pages, "rows": rows}



@router.get("/{id}", summary="MCP工具提供方详情")
def get_mcp_provider(id: int=Path(description="ID")):
    """
    查询单个MCP工具提供方
    :param provider_id:
    :return:
    """
    provider_instance=MCPToolProvider.get(id)
    return  {
        "id": provider_instance.id,
        "name": provider_instance.name,
        "server_identifier": provider_instance.server_identifier,
        "server_url": provider_instance.server_url,
        "authed": provider_instance.authed,
        "tools": provider_instance.mcp_tools,
        "selected_tools": provider_instance.selected_mcp_tools,
        "timeout": provider_instance.timeout,
        "sse_read_timeout": provider_instance.sse_read_timeout,
        "headers": provider_instance.headers,
        "created_at": provider_instance.created_at,
        "updated_at": provider_instance.updated_at,
        }


@router.post("/create", summary="创建MCP工具提供方")
def create_mcp_provider(name:str = Body(description="名称"),
                        server_url:str = Body(description="服务器地址"),
                        server_identifier:str = Body(description="标识名"),
                        headers:dict[str,str]|None = Body(description="请求头",default=None)):
    """
    创建MCP工具提供方
    :param provider:
    :return:
    """
    provider_instance=MCPToolProvider.create_mcp_provider(name=name,server_url=server_url,server_identifier=server_identifier,headers=headers)
    
    return {
        "id": provider_instance.id,
        "name": provider_instance.name,
        "server_identifier": provider_instance.server_identifier,
        "server_url": provider_instance.server_url,
        "authed": provider_instance.authed,
        "tools": provider_instance.mcp_tools,
        "selected_tools": provider_instance.selected_mcp_tools,
        "timeout": provider_instance.timeout,
        "sse_read_timeout": provider_instance.sse_read_timeout,
        "headers": provider_instance.headers,
        "created_at": provider_instance.created_at,
        "updated_at": provider_instance.updated_at,
    }


@router.post("/update", summary="修改MCP工具提供方")
def update_mcp_provider(id: int = Body(description="ID"),
                        name:str = Body(description="名称"),
                        server_url:str = Body(description="服务器地址"),
                        server_identifier:str = Body(description="标识名"),
                        headers:dict[str,str]|None = Body(description="请求头",default=None)):
    """
    修改MCP工具提供方
    :param provider:
    :return:
    """
    MCPToolProvider.update_mcp_provider(id=id,name=name,server_url=server_url,server_identifier=server_identifier,headers=headers)
    return {"result": "success"}

@router.post("/delete/{id}", summary="删除MCP工具提供方")
def delete_mcp_provider(id: int = Path(description="ID")):
    """
    删除MCP工具提供方
    :param provider:
    :return:
    """
    MCPToolProvider.delete_mcp_provider(id)
    return {"result": "success"}


@router.post("/reconnect/{id}", summary="重新连接MCP工具提供方")
def reconnect_mcp_provider(id: int = Path(description="ID")):
    """
    重新连接MCP工具提供方
    :param provider:
    :return:
    """
    provider_instance=MCPToolProvider.list_mcp_tools_from_server(id)
    return {"result": "success"}


@router.post("/select_tools", summary="选择MCP提供方工具")
def select_mcp_tools(id: int = Body(description="ID"),
                     selected_tools:list[str] = Body(description="选中的工具")):
    """
    选择MCP工具提供方
    :param provider:
    :return:
    """
    MCPToolProvider.select_mcp_tools(id,selected_tools)
    return {"result": "success"}


@router.get("/tools/list", summary="MCP工具列表")
def mcp_tools():
    """
    认证MCP工具提供方
    :param provider:
    :return:
    """
    tools=MCPToolProvider.get_tool_list()

    return {"rows":tools}   

