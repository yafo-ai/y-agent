from typing import Optional

from sqlalchemy import String, Integer
from sqlalchemy.orm import mapped_column

from src.database.base_model import BaseModel


class Menu(BaseModel):
    icon = mapped_column(String(255), nullable=False, comment="菜单图标")
    pid = mapped_column(Integer, nullable=True, comment="父菜单ID")
    type = mapped_column(Integer, nullable=True, comment="菜单类型 0目录 1菜单 2按钮 3数据")
    sort = mapped_column(Integer, nullable=True, comment="菜单排序")
    api = mapped_column(String(255), nullable=True, comment="菜单api")
    method = mapped_column(String(255), nullable=True, comment="菜单请求方法")

    def __repr__(self):
        return f"<Menu(id={self.id}, name={self.name}, code={self.code}, caption={self.caption}, type={self.type}, sort={self.sort}, note={self.note}, icon={self.icon}, pid={self.pid}, created_at={self.created_at}, updated_at={self.updated_at}, deleted_at={self.deleted_at}, api={self.api})>"

    def obj_to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "caption": self.caption,
            "type": self.type,
            "type_name": "未知" if self.type is None else "目录" if self.type == 0 else "菜单" if self.type == 1 else "按钮" if self.type == 2 else "数据",
            "sort": self.sort,
            "note": self.note,
            "icon": self.icon,
            "pid": self.pid,
            "api": self.api,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at is not None else None,
            "deleted_at": self.deleted_at.strftime("%Y-%m-%d %H:%M:%S") if self.deleted_at is not None else None
        }

    @classmethod
    def menu_update(cls, id: Optional[int], name, type, sort, note, icon, pid, api, method):
        if pid is None or pid <= 0:
            pid = None
        if type not in [0, 1, 2, 3]:
            type = 1
        from src.api.customer_exception import ValidationException
        model = None
        try:
            model = cls.get(id) if id and id > 0 else cls()
            attrs = {
                'name': name, 'type': type,
                'sort': sort, 'note': note, 'icon': icon,
                'pid': pid, 'api': api, 'method': method
            }
            for key, value in attrs.items():
                setattr(model, key, value)
            model.update(True) if id and id > 0 else model.add(True)
            return {"result": "success", "id": model.id}
        except ValidationException as e:
            if model is not None:
                model.session.rollback()
            raise ValidationException(e.args[0])
        except Exception as e:
            from src.utils.log_helper import logger
            logger.error(f"菜单更新失败：{e}")
            raise ValidationException("菜单更新失败")

    @classmethod
    def menu_tree(cls, arr: list['Menu'], c_name: str = 'children'):
        tree = []
        first_level = [arr[i] for i in range(len(arr)) if arr[i].pid is None]
        for item in first_level:
            item_dict = item.obj_to_dict()
            item_dict[c_name] = [arr[i].obj_to_dict() for i in range(len(arr)) if arr[i].pid == item.id]
            tree.append(item_dict)
        return tree

    # 删除菜单
    def menu_delete(self):
        from src.database.permissions.models.user import UserMenu
        from src.database.permissions.models.role import RoleMenu
        user_menus = UserMenu.query.filter_by(menu_id=self.id).all()
        role_menus = RoleMenu.query.filter_by(menu_id=self.id).all()
        for user_menu in user_menus:
            user_menu.delete()
        for role_menu in role_menus:
            role_menu.delete()
        self.delete(True)
