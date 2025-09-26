import datetime
import hashlib
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, Integer
from sqlalchemy.orm import mapped_column, Mapped

from src.database.base_model import BaseModel
from src.api.customer_exception import ValidationException
from src.database.permissions.common.security import verify_password, generate_token, SECRET_KEY
from src.database.permissions.models.role import Role


class User(BaseModel):
    username: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, comment="登录名")
    password: Mapped[str] = mapped_column(String(255), nullable=True, comment="密码")
    nickname: Mapped[str] = mapped_column(String(255), nullable=True, comment="昵称")
    email: Mapped[str] = mapped_column(String(255), nullable=True, comment="邮箱")
    phone: Mapped[str] = mapped_column(String(255), nullable=True, comment="手机号")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否激活")
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否超级管理员")
    last_login: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=True, comment="最后登录时间")

    def obj_to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "nickname": self.nickname,
            "email": self.email,
            "phone": self.phone,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "last_login": self.last_login.strftime("%Y-%m-%d %H:%M:%S") if self.last_login else None,
        }

    @classmethod
    def login(cls, username: Optional[str], password: Optional[str], ip: Optional[str] = None):
        user = cls.query.filter_by(username=username).first()
        if user is None:
            raise ValidationException('用户不存在')
        if not verify_password(password, user.password):
            raise ValidationException("密码错误")
        if not user.is_active:
            raise ValidationException("用户未激活")
        token = generate_token(user.username, user.id, psh=hashlib.md5(f"{user.password}{SECRET_KEY}".encode()).hexdigest(), ip=ip)
        user.last_login = datetime.datetime.now()
        user.update(True)
        return {"result": "success", "id": user.id, "username": user.name, "token": token}

    # 用户分页
    @classmethod
    def user_page(cls, page_num: int, page_size: int,
                  username: str = None, nickname: str = None,
                  email: str = None, phone: str = None,
                  is_active: bool = None, is_superuser: bool = None):
        query = cls.query
        if username:
            query = query.filter(cls.username.like(f"%{username}%"))
        if nickname:
            query = query.filter(cls.nickname.like(f"%{nickname}%"))
        if email:
            query = query.filter(cls.email.like(f"%{email}%"))
        if phone:
            query = query.filter(cls.phone.like(f"%{phone}%"))
        if is_active is not None:
            query = query.filter(cls.is_active == is_active)
        if is_superuser is not None:
            query = query.filter(cls.is_superuser == is_superuser)
        total = query.count()
        query = query.limit(page_size).offset((page_num - 1) * page_size)
        users = query.all()
        total_page = (total + page_size - 1) // page_size
        uid = [user.id for user in users]
        user_roles = UserRole.query.filter(UserRole.user_id.in_(uid)).all()
        rids = [user_role.role_id for user_role in user_roles]
        roles = Role.query.filter(Role.id.in_(rids)).all()
        rows = []
        for user in users:
            user_dict = user.obj_to_dict()
            user_dict["roles"] = [role.obj_to_dict() for role in roles if role.id in [user_role.role_id for user_role in user_roles if user_role.user_id == user.id]]
            rows.append(user_dict)

        return {"total": total, "total_page": total_page, "rows": rows}

    # 添加/更新用户
    @classmethod
    def user_update(cls, id: Optional[int], username, password, nickname, email, phone, is_active, is_superuser,
                    role_ids: Optional[list[int]] = None):
        model = None
        try:
            from src.database.permissions.common.security import get_password_hash, verify_password
            if id is not None and id > 0:
                model = cls.get(id)
                model.nickname = nickname
                model.email = email
                model.phone = phone
                model.is_active = False if is_active is None else is_active
                model.is_superuser = False if is_superuser is None else is_superuser
                user_roles = UserRole.query.filter_by(user_id=id).all()
                for user_role in user_roles:
                    user_role.delete()
                for role_id in role_ids if role_ids else []:
                    UserRole(user_id=id, role_id=role_id).add()
                model.update(True)
            else:
                ext_user = cls.query.filter_by(username=username).first()
                if ext_user:
                    raise ValidationException("用户名已存在")
                model = cls(username=username, password=get_password_hash(password), nickname=nickname, email=email, phone=phone, is_active=is_active,
                            is_superuser=is_superuser)
                model.add()
                model.session.flush()
                for role_id in role_ids if role_ids else []:
                    UserRole(user_id=model.id, role_id=role_id).add()
                model.session.commit()
            return {"result": "success", "id": model.id}
        except ValidationException as e:
            if model is not None:
                model.session.rollback()
            raise ValidationException(str(e))
        except Exception as e:
            if model is not None:
                model.session.rollback()

    # 用户详情
    def user_detail(self):
        user_dict = self.obj_to_dict()
        user_dict["roles"] = [role.obj_to_dict() for role in self.user_roles()]
        user_dict["menus"] = [menu.obj_to_dict() for menu in self.user_menus()]
        return user_dict

    # 用户授权的角色
    def user_roles(self) -> list['Role']:
        user_roles = UserRole.query.filter_by(user_id=self.id).all()
        if len(user_roles) <= 0:
            return []
        roles_ids = [user_role.role_id for user_role in user_roles]
        from src.database.permissions.models.role import Role
        roles = Role.query.filter(Role.id.in_(roles_ids)).all()
        return roles

    # 用户的授权菜单
    def user_menus(self):
        user_menus = UserMenu.query.filter(UserMenu.user_id == self.id).all()
        if len(user_menus) <= 0:
            return []
        from src.database.permissions.models.menu import Menu
        menu_ids = [user_menu.menu_id for user_menu in user_menus]
        menus = Menu.query.filter(Menu.id.in_(menu_ids)).all()
        return menus

    # 用户授权菜单
    def user_authorize_menu(self):
        permissions = {"folder": [], "menu": [], "button": [], "data": []}
        for menu in self.user_all_menus():
            # menu = menu.obj_to_dict()
            if menu.get("type", None) is None:
                continue
            if menu.get("type") == 0:
                if not any(d.get("id") == menu.get("id") for d in permissions["folder"]):
                    permissions["folder"].append({"id": menu.get("id"), "name": menu.get("name")})
            elif menu.get("type") == 1:
                if not any(d.get("id") == menu.get("id") for d in permissions["menu"]):
                    permissions["menu"].append({"id": menu.get("id"), "name": menu.get("name")})
            elif menu.get("type") == 2:
                if not any(d.get("id") == menu.get("id") for d in permissions["button"]):
                    permissions["button"].append({"id": menu.get("id"), "name": menu.get("name"), "api": menu.get("api"), "sort": menu.get("sort")})
            elif menu.get("type") == 3:
                if not any(d.get("id") == menu.get("id") for d in permissions["data"]):
                    permissions["data"].append({"id": menu.get("id"), "name": menu.get("name"), "api": menu.get("api"), "sort": menu.get("sort")})
        return permissions

    # 获取用户所有菜单
    def user_all_menus(self):
        menus = []
        if self.is_superuser:
            from src.database.permissions.models.menu import Menu
            menus = [menu.obj_to_dict() for menu in Menu.query.all()]
            return menus
        for role in self.user_roles():
            for menu in role.obj_to_dict().get("menus", []):
                if any(menu.get("id") == m.get("id") for m in menus):
                    continue
                menus.append(menu)
        for menu in self.user_menus():
            if any(menu.id == m.get("id") for m in menus):
                continue
            menus.append(menu.obj_to_dict())
        return menus

    # 授权用户菜单
    def authorize_user_menu(self, menu_ids: Optional[list[int]]):
        user_menus = UserMenu.query.filter(UserMenu.user_id == self.id).all()
        for user_menu in user_menus if user_menus else []:
            user_menu.delete()
        if menu_ids is not None and len(menu_ids) > 0:
            for menu_id in menu_ids:
                UserMenu(user_id=self.id, menu_id=menu_id).add()
        self.session.commit()

    # 给用户分配角色
    def assign_user_role(self, role_ids: list[int]):
        user_roles = UserRole.query.filter(UserRole.user_id == self.id).all()
        for user_role in user_roles if user_roles else []:
            user_role.delete()
        user_menus = UserMenu.query.filter(UserMenu.user_id == self.id).all()
        for user_menu in user_menus if user_menus else []:
            user_menu.delete()
        for role_id in role_ids:
            UserRole(user_id=self.id, role_id=role_id).add()
        self.session.commit()

    # 删除用户
    def delete_user(self):
        user_roles = UserRole.query.filter(UserRole.user_id == self.id).all()
        for user_role in user_roles if user_roles else []:
            user_role.delete()
        user_menus = UserMenu.query.filter(UserMenu.user_id == self.id).all()
        for user_menu in user_menus if user_menus else []:
            user_menu.delete()
        self.delete(True)

    # 重置密码
    def reset_password(self, old_password, new_password):
        from src.database.permissions.common.security import get_password_hash, verify_password
        if old_password == new_password:
            raise ValidationException("新密码不能与旧密码相同")
        if not verify_password(old_password, self.password):
            raise ValidationException("旧密码错误")
        self.password = get_password_hash(new_password)
        self.update(True)

    # 激活/禁用 用户
    def activate_user(self, is_active: bool):
        self.is_active = is_active
        self.update(True)


class UserRole(BaseModel):
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="用户ID")
    role_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="角色ID")


class UserMenu(BaseModel):
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="用户ID")
    menu_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="菜单ID")
