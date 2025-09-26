from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base_model import BaseModel


class Role(BaseModel):

    def obj_to_dict(self):
        role_menu_maps = RoleMenu.query.filter_by(role_id=self.id).all()
        if len(role_menu_maps) <= 0:
            return {"id": self.id, "name": self.name, "note": self.note, "menus": []}
        role_menu_ids = [menu_map.menu_id for menu_map in role_menu_maps]
        from src.database.permissions.models.menu import Menu
        menus = Menu.query.filter(Menu.id.in_(role_menu_ids)).all()
        menus_dict_list = [menu.obj_to_dict() for menu in menus]
        return {"id": self.id, "name": self.name, "note": self.note, "menus": menus_dict_list}

    @classmethod
    def role_page(cls, page: int, page_size: int, name: str = None, note: str = None):
        query = cls.query
        if name:
            query = query.filter(cls.name.like(f'%{name}%'))
        if note:
            query = query.filter(cls.note.like(f'%{note}%'))
        total = query.count()
        query = query.limit(page_size).offset((page - 1) * page_size)
        roles = query.all()
        total_page = (total + page_size - 1) // page_size
        return {"total": total, "total_page": total_page, "rows": [role.obj_to_dict() for role in roles]}

    # 添加/更新用户
    @classmethod
    def role_update(cls, id: int, name: str, note: str = None):
        model = None
        from src.api.customer_exception import ValidationException
        try:
            if name is None or name.strip() == "":
                raise ValidationException("角色名称不能为空")
            if id is not None and id > 0:
                model = cls.get(id)
                if cls.query.filter(cls.id != id, cls.name == name).first():
                    raise ValidationException("角色名称已存在")
                model.name = name
                model.note = note
                model.update(True)
            else:
                if cls.query.filter_by(name=name).first():
                    raise ValidationException("角色名称已存在")
                model = cls(name=name, note=note)
                model.add(True)
            return {"result": "success", "id": model.id}
        except ValidationException as e:
            from src.utils.log_helper import logger
            logger.error(f"NoneException: {e}")
            raise e
        except Exception as e:
            if model is not None:
                model.session.rollback()

    # 删除角色
    def role_delete(self):
        role_menus = RoleMenu.query.filter_by(role_id=self.id)
        for role_menu in role_menus:
            role_menu.delete()
        from src.database.permissions.models.user import UserRole
        user_roles = UserRole.query.filter_by(role_id=self.id)
        for user_role in user_roles if user_roles else []:
            user_role.delete()
        self.delete(True)

    # 授权角色菜单
    def authorize_role_menu(self, menu_ids: list[int]):
        role_menus = RoleMenu.query.filter_by(role_id=self.id).all()
        for role_menu in role_menus if role_menus else []:
            role_menu.delete()
        if len(menu_ids) > 0:
            for menu_id in menu_ids:
                RoleMenu(role_id=self.id, menu_id=menu_id).add()
        self.session.commit()


class RoleMenu(BaseModel):
    role_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="角色ID")
    menu_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="菜单ID")
