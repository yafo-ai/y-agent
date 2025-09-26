from typing import Optional

from fastapi import APIRouter, Body, Path, Query

from src.database.permissions.models.role import Role
from src.database.permissions.models.user import User

router = APIRouter(
    prefix="/api/user",
    tags=["用户管理"],
)


@router.post("/paged", summary="用户列表")
def get_user_paged(page_index: int = Body(default=1, description="页码"),
                   pagesize: int = Body(default=10, description="每页数量"),
                   username: str | None = Body(default=None, description="用户名"),
                   nickname: str | None = Body(default=None, description="昵称"),
                   email: str | None = Body(default=None, description="邮箱"),
                   phone: str | None = Body(default=None, description="手机号"),
                   is_active: bool | None = Body(default=None, description="是否激活"),
                   is_superuser: bool | None = Body(default=None, description="是否超级管理员")):
    return User.user_page(page_index, pagesize, username, nickname, email, phone, is_active, is_superuser)


@router.post("/add", summary="用户添加")
def add_user(username: str = Body(default=None, description="用户名"),
             password: str = Body(default=None, description="密码"),
             nickname: str | None = Body(default=None, description="昵称"),
             email: str | None = Body(default=None, description="邮箱"),
             phone: str | None = Body(default=None, description="手机号"),
             is_active: bool | None = Body(default=None, description="是否激活"),
             is_superuser: bool | None = Body(default=None, description="是否超级管理员"),
             role_ids: Optional[list[int]] = Body(default=None, description="角色id列表")):
    return User.user_update(None, username, password, nickname, email, phone, is_active, is_superuser, role_ids)


@router.post("/{id}/update", summary="用户更新")
def update_user(id: int = Path(default=..., description="用户id"),
                username: str = Body(default=None, description="用户名"),
                nickname: str | None = Body(default=None, description="昵称"),
                email: str | None = Body(default=None, description="邮箱"),
                phone: str | None = Body(default=None, description="手机号"),
                is_active: bool | None = Body(default=None, description="是否激活"),
                is_superuser: bool | None = Body(default=None, description="是否超级管理员"),
                role_ids: Optional[list[int]] = Body(default=None, description="角色id列表")):
    return User.user_update(id, username, None, nickname, email, phone, is_active, is_superuser, role_ids)


@router.get("/{id}", summary="用户详情")
def get_user_detail(id: int = Path(default=..., description="用户id")):
    return User.get(id).user_detail()


@router.post("/{id}/delete", summary="用户删除")
def delete_user(id: int = Path(default=..., description="用户id")):
    User.get(id).delete_user()
    return {"result": "success"}


@router.post("/{id}/reset_password", summary="用户密码重置")
def reset_password(id: int = Path(default=..., description="用户id"),
                   old_password: str = Body(default=None, description="旧密码"),
                   new_password: str = Body(default=None, description="新密码")):
    User.get(id).reset_password(old_password, new_password)
    return {"result": "success"}


@router.post("/{id}/activate", summary="用户激活")
def activate_user(id: int = Path(default=..., description="用户id"),
                  is_active: bool = Query(default=None, description="是否激活")):
    User.get(id).activate_user(is_active)
    return {"result": "success"}


@router.get("/{id}/add_role", summary="用户增加角色")
def assign_user_role(id: int = Path(default=..., description="用户id"),
                     role_ids: Optional[list[int]] = Query(default=None, description="角色id")):
    User.get(id).assign_user_role(role_ids)
    return {"result": "success"}


@router.post("/authorize_menu", summary="用户授权菜单")
def user_authorize_menu(id: int = Body(default=..., description="用户id"),
                        menu_ids: Optional[list[int]] = Body(default=None, description="菜单id列表")
                        ):
    User.get(id).authorize_user_menu(menu_ids)
    return {"result": "success"}


"""
--------------------------------------------角色-------------------------------
"""


@router.post("/role/paged", summary="角色列表")
def get_role_paged(page_index: int = Body(default=1, description="页码"),
                   pagesize: int = Body(default=10, description="每页数量"),
                   name: str | None = Body(default=None, description="角色名称")):
    return Role.role_page(page_index, pagesize, name)


@router.post("/role/add", summary="角色新增")
def add_role(name: str = Body(default=None, description="角色名称"),
             note: str | None = Body(default=None, description="角色描述")):
    return Role.role_update(None, name, note)


@router.post("/role/{id}/update", summary="角色更新")
def update_role(id: int = Path(default=..., description="角色id"),
                name: str = Body(default=None, description="角色名称"),
                note: str | None = Body(default=None, description="角色描述")):
    return Role.role_update(id, name, note)


@router.get("/role/{id}", summary="角色详情")
def get_role_detail(id: int = Path(default=..., description="角色id")):
    return Role.get(id).obj_to_dict()


@router.post("/role/{id}/delete", summary="角色删除")
def delete_role(id: int = Path(default=..., description="角色id")):
    Role.get(id).role_delete()
    return {"result": "success"}


@router.post("/role/authorize_menu", summary="角色授权菜单")
def role_authorize_menu(id: int = Body(default=..., description="角色id"),
                        menu_ids: Optional[list[int]] = Body(default=None, description="菜单id列表")):
    Role.get(id).authorize_role_menu(menu_ids)
    return {"result": "success"}
