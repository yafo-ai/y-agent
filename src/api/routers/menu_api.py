from fastapi import APIRouter, Body, Path, Query, Security

from src.database.permissions.common.security import check_permissions
from src.database.permissions.models.menu import Menu
from src.database.permissions.models.user import User

router = APIRouter(
    prefix="/api/menu",
    tags=["菜单管理"],
)


@router.get("/refresh", summary="刷新")
def refresh_menu():
    from fastapi.routing import APIRoute
    from src.api.app import app
    menu_api_json = {}

    tmp_menu_api_list = []
    for router in app.routes:
        if not isinstance(router, APIRoute):
            continue
        if (router.path.lower().startswith('/docs')
                or router.path.lower() == '/redoc'
                or router.path.lower().startswith('/api/messagehistory')
                or router.path.lower().startswith('/api/chatappmodes')
                or router.path.lower().startswith('/api/wxbot')
                or router.path.lower().startswith('/api/authorize')):
            continue
        if router.summary is None:
            continue
        if 'public' in router.tags:
            continue
        if router.tags and len(router.tags) > 0:
            menu_api_json[router.tags[0]] = menu_api_json.get(router.tags[0], [])

            menu_api_json.get(router.tags[0]).append({
                "api": router.path.lower(),
                "method": list(router.methods)[0],
                "name": router.summary
            })

            tmp_menu_api_list.append(router.path.lower())

    delete_menus = Menu.query.filter(Menu.api.notin_(tmp_menu_api_list))
    for delete_menu in delete_menus:
        delete_menu.delete()
    del tmp_menu_api_list

    session = Menu().session

    all_menus = Menu.query.all()

    tmp_parent_menus = list(filter(lambda x: x.name in menu_api_json.keys(), all_menus))
    existing_parents = {parent.name: parent for parent in tmp_parent_menus}

    from src.database.permissions.models.user import UserMenu
    from src.database.permissions.models.role import RoleMenu

    for key, value in menu_api_json.items():
        tmp_parent = existing_parents.get(key)
        if not tmp_parent:
            tmp_parent = Menu(type=0, sort=0, name=key)
            tmp_parent.add()
            tmp_parent.session.flush()
            existing_parents[key] = tmp_parent

        children = list(filter(lambda x: x.pid == tmp_parent.id, all_menus))
        # children = Menu.query.filter_by(pid=tmp_parent.id).all()
        if children is None or len(children) == 0:
            # 全部添加
            for item in value:
                Menu(api=item.get("api"), name=item.get("name"), type=2, pid=tmp_parent.id, method=item.get("method")).add()
        else:
            # 部分添加
            for child in children:
                if child.api not in [item.get("api") for item in value]:
                    child.delete()

                    user_menus = UserMenu.query.filter_by(menu_id=child.id).all()
                    for user_menu in user_menus:
                        user_menu.delete()

                    role_menus = RoleMenu.query.filter_by(menu_id=child.id).all()
                    for role_menu in role_menus:
                        role_menu.delete()
                for item in value:
                    tmp_child = Menu.query.filter_by(api=item.get("api"), pid=tmp_parent.id).first()
                    # tmp_childrens = list(filter(lambda x: x.pid == tmp_parent.id and x.api != item.get("api"), all_menus))
                    if not tmp_child:
                        Menu(api=item.get("api"), name=item.get("name"), type=2, pid=tmp_parent.id, method=item.get("method")).add()
                    else:
                        tmp_child.name = item.get("name")
    session.commit()
    return {"result": "success"}


@router.post("", summary="用户菜单")
def get_menu_paged(user_id: int = Query(default=None, description="用户ID")):
    return User.get(user_id).user_all_menus()


@router.post("/tree", summary="菜单树")
def get_menu_tree():
    return Menu.menu_tree(Menu.query.all())


@router.post("/add", summary="新增", dependencies=[Security(check_permissions)])
def add_menu(pid: int | None = Body(default=None, description="父菜单ID"),
             name: str = Body(default=..., description="菜单名称"),
             type: int = Body(default=1, description="菜单类型 0目录 1菜单 2按钮 3数据"),
             icon: str = Body(default=None, description="菜单图标"),
             sort: int = Body(default=0, description="菜单排序"),
             api: str = Body(default=None, description="菜单api"),
             method: str = Body(default=None, description="菜单请求方法"),
             ):
    return Menu.menu_update(None, name, type, sort, None, icon, pid, api, method)


@router.post("/{id}/update", summary="更新")
def update_menu(id: int = Path(default=..., description="菜单ID"),
                pid: int = Body(default=None, description="父菜单ID"),
                name: str = Body(default=..., description="菜单名称"),
                type: int = Body(default=1, description="菜单类型 0目录 1菜单 2按钮 3数据"),
                icon: str = Body(default=None, description="菜单图标"),
                sort: int = Body(default=0, description="菜单排序"),
                api: str = Body(default=None, description="菜单api")
                ):
    return Menu.menu_update(id, name, type, sort, None, icon, pid, api)


@router.post("/{id}/delete", summary="删除")
def delete_menu(id: int = Path(default=..., description="菜单ID")):
    Menu.get(id).menu_delete()
    return {"result": "success"}
