from fastapi import APIRouter, Body, Request
from src.database.permissions.models.user import User

router = APIRouter(
    prefix="/api/authorize",
    tags=["系统设置"],
)


@router.post("/login", summary="用户登录")
def login(request: Request, username: str = Body(default=None, description="用户名"),
          password: str = Body(default=None, description="密码")):
    return User.login(username, password, request.client.host)


@router.post("/register", summary="用户注册")
def register(username: str = Body(default=None, description="用户名"),
             password: str = Body(default=None, description="密码"),
             nickname: str = Body(default=None, description="昵称"),
             email: str = Body(default=None, description="邮箱"),
             phone: str = Body(default=None, description="手机号")
             ):
    return User.user_update(None, username, password, nickname, email, phone, False, False, [])
