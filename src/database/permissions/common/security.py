import hashlib
from datetime import timedelta, datetime
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from starlette.requests import Request

from src.api.customer_exception import NoPermissionException
from src.configs.system_config import system_config

SECRET_KEY = "lLNiBWPGiEmCLLR9kRGidgLY7Ac1rpSWwfGzTJpTmCU"

ALGORITHM = "HS256"

bearer = HTTPBearer()


def get_sys_security_info():
    sys_security = system_config.sys_db_security  # SystemConfigSecurity().load_db_config()
    return sys_security.access_token_expire_minutes, sys_security.refresh_token_expire_minutes


def verify_password(plain_password, hashed_password) -> bool:
    return hashed_password == get_password_hash(plain_password)


def get_password_hash(password, salt=SECRET_KEY) -> str:
    return hashlib.md5(f"{password}{salt}".encode()).hexdigest()


def generate_token(username: str, user_id: int, psh: str = '', ip: str = '') -> str:
    now = datetime.now()
    to_encode = {"sub": username, "user_id": user_id, "iat": now, "psh": psh, "ip": ip}
    expire = now + timedelta(minutes=get_sys_security_info()[0])
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def validate_token(token: str) -> Optional['User']:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        from src.database.permissions.models.user import User
        user = User.get(user_id)
        psh: str = payload.get("psh")
        # 更改了密码
        if psh != hashlib.md5(f"{user.password}{SECRET_KEY}".encode()).hexdigest():
            raise HTTPException(status_code=401, detail="更改密码，请重新登录")
        # user.password = "******"
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="token认证失败[1]")


# 获取token
def get_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
    if credentials is None:
        return None

    if credentials.scheme != "Bearer":
        return None

    return credentials.credentials


# 权限校验
def check_permissions(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
    route = request.scope.get("route")
    if route and 'public' in route.tags:
        return
    if request.url.path == "/api/login" or request.url.path == "/api/register":
        return
    if credentials is None:
        raise HTTPException(status_code=401, detail="未提供认证信息")
        # raise NoneException(detail="未提供认证信息")
    user = validate_token(credentials.credentials)

    api = request.url.path
    for k, v in request.path_params.items():
        api = api.replace(v, "{%s}" % k)
    request.state.user_dict = user.obj_to_dict()
    permissions = user.user_authorize_menu()
    if user.is_superuser:
        return
    if not any(api in d.get("api", "") for d in permissions.get("button", [])):
        raise NoPermissionException("无权限访问")


# 刷新token
def refresh_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="token认证失败[2]")
    exp = datetime.fromtimestamp(payload.get("exp"))
    now = datetime.now()

    total_minutes = int((exp - now).total_seconds() // 60)
    if total_minutes < get_sys_security_info()[1]:
        user_id: int = payload.get("user_id")
        user_name: str = payload.get("sub")
        psh: str = payload.get("psh")
        ip: str = payload.get("ip")
        new_token = generate_token(user_name, user_id, psh, ip)
        # new_token = generate_token(user_name, user_id, timedelta(minutes=2), psh, ip)
        return new_token
    else:
        return None
