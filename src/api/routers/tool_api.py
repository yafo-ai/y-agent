import ast
import json
from typing import List
import uuid
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Path
from pydantic import Field

from src.api.customer_exception import *
from src.agent.model_types import APITool
from src.database.db_session import get_scoped_session
from sqlalchemy.orm import Session

from src.database.models import ToolModel


router = APIRouter(
    prefix="/api/tools",
    tags=["工具插件"],
)


@router.get("", summary="列表")
def get_tools(page: int = Query(description="页码", default=1),
                       pagesize: int = Query(description="每页数量", default=10),
                       keyword: str | None = Query(description="关键词", default=None),
                       is_enable: bool | None = Query(description="是否启用", default=None),
                       session: Session = Depends(get_scoped_session)
                       ):
    """条件分页查询"""
    conditions = {}
    if is_enable:
        conditions["is_enable"] = is_enable

    tools=None
    if keyword:
        tools = session.query(ToolModel).filter_by(**conditions).filter(ToolModel.name.ilike(f"%{keyword}%")).offset(pagesize * (page - 1)).limit(pagesize).all()
    else:
        tools = session.query(ToolModel).filter_by(**conditions).offset(pagesize * (page - 1)).limit(pagesize).all()

    total_records = session.query(ToolModel).count()
    total_pages = (total_records + pagesize - 1) // pagesize

    if not tools:
        return {"total_records": total_records, "total_pages": total_pages, "rows": []}
    
    rows = [{"id": tool.id,
             "name": tool.name,
             "func_name": tool.func_name,
             "is_enable": tool.is_enable,
             "api_url": tool.api_url,
             "api_method": tool.api_method,
             "caption": tool.caption,
             "in_params": json.loads(tool.in_params) if tool.in_params else [],
             "out_params": json.loads(tool.out_params) if tool.out_params else []
            } for tool in tools]
    return {"total_records": total_records, "total_pages": total_pages, "rows": rows}


@router.get("/get/{id}", summary="详情")
def get_tool(id: int = Path(description="工具id"),
                      session: Session = Depends(get_scoped_session)):
    """用于id查询工具详情"""

    tool = ToolModel.get(id)


    in_params=json.loads(tool.in_params) if tool.in_params else []

    out_params=json.loads(tool.out_params) if tool.out_params else []


    return {
        "id": tool.id,
        "name": tool.name,
        "func_name": tool.func_name,
        "is_enable": tool.is_enable,
        "api_url": tool.api_url,
        "api_method": tool.api_method,
        "caption": tool.caption,
        "in_params": in_params,
        "out_params": out_params
    }

@router.post("/add", summary="添加")
def add_tool(tool:APITool=Body(description="工具参数"), session: Session = Depends(get_scoped_session)):
    """添加工具"""

    ex=ToolModel.query.filter_by(func_name=tool.func_name).first()
    if ex:
        raise ValidationException(detail="工具名称已经存在")

    model = ToolModel()
    model.unique_code = str(uuid.uuid4())
    model.edit(tool)

    model.add(True) 
    return {"result": "success"}


@router.post("/edit/{id}", summary="编辑")
def edit_tool(id: int = Path(description="产品id"),tool:APITool=Body(description="工具参数"),session: Session = Depends(get_scoped_session)):
    """
    编辑工具
    """
    model = ToolModel.get(id)

    ex=ToolModel.query.filter_by(func_name=tool.func_name).filter(ToolModel.id!=tool.id).first()
    if ex:
        raise ValidationException(detail="工具名称已经存在")

    model.edit(tool)
    model.update(True)
    return {"result": "success"}


@router.post("/delete/{id}", summary="删除")
def delete_tool(id: int = Path(description="工具id"), session: Session = Depends(get_scoped_session)):
    """
    删除工具
    """
    tool = ToolModel.get(id)
    tool.delete(True)
    return {"result": "success"}



@router.post('/set_disabled/{id}', summary="停用工具")
def set_tool_disabled(id: int = Path(description="工具id"),session: Session = Depends(get_scoped_session)):
    """
    用于设置工具停用状态
    """
    tool=ToolModel.get(id)
    tool.toggle_enable()
    tool.update(True)
    return {"result": "success"}

