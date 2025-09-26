from fastapi import Depends
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from src.api.middleware import AuditMiddleware, RequestIDMiddleware
from src.api.routers import mcp_provider, modelconfig_api, tool_api, workflow_socket, wxbot, goods_api, user_api, authorize_api, menu_api, operator_api, \
    sysconfig_api
from src.database.db_session import set_current_request_id

from .customer_exception import *
from .routers import document_api, category_api, chat_api, knowledgebase_api, product_api, prompt_api, filedatabase_api, files_api, testcase_api, traincase_api, testplan_api, workflow_api


#fastapi：https://fastapi.tiangolo.com/zh/learn/
#fastapi 仓储 https://github.com/BiteStreams/fastapi-template/blob/main/api/main.py
#             https://dev.to/tobias-piotr/patterns-and-practices-for-using-sqlalchemy-20-with-fastapi-49n8
#             https://github.com/tobias-piotr/alchemist/blob/main/alchemist/api/v1/routes.py
#https://github.com/fastapi-practices/fastapi_sqlalchemy_mysql/blob/master/app/admin/api/v1/user.py

# uvicorn main:app --reload
# app = FastAPI()
from fastapi_offline import FastAPIOffline

from ..utils.testplan_helper import TestPlanContinueTasking

app = FastAPIOffline()

from src.database.permissions.common.security import check_permissions


app.include_router(chat_api.router, dependencies=[Depends(check_permissions)])
app.include_router(knowledgebase_api.router, dependencies=[Depends(check_permissions)])
app.include_router(document_api.router, dependencies=[Depends(check_permissions)])
app.include_router(category_api.router, dependencies=[Depends(check_permissions)])
app.include_router(product_api.router, dependencies=[Depends(check_permissions)])
app.include_router(prompt_api.router, dependencies=[Depends(check_permissions)])
app.include_router(filedatabase_api.router, dependencies=[Depends(check_permissions)])
app.include_router(files_api.router, dependencies=[Depends(check_permissions)])
app.include_router(traincase_api.router, dependencies=[Depends(check_permissions)])
app.include_router(testcase_api.router, dependencies=[Depends(check_permissions)])
app.include_router(testplan_api.router, dependencies=[Depends(check_permissions)])
app.include_router(workflow_api.router, dependencies=[Depends(check_permissions)])
app.include_router(modelconfig_api.router, dependencies=[Depends(check_permissions)])
app.include_router(tool_api.router, dependencies=[Depends(check_permissions)])
app.include_router(workflow_socket.router)
app.include_router(wxbot.router)
app.include_router(goods_api.router, dependencies=[Depends(check_permissions)])
app.include_router(authorize_api.router)
app.include_router(mcp_provider.router, dependencies=[Depends(check_permissions)])
app.include_router(user_api.router, dependencies=[Depends(check_permissions)])
app.include_router(operator_api.router, dependencies=[Depends(check_permissions)])
app.include_router(menu_api.router, dependencies=[Depends(check_permissions)])
app.include_router(sysconfig_api.router, dependencies=[Depends(check_permissions)])
app.add_middleware(AuditMiddleware)
app.add_middleware(RequestIDMiddleware)


register_exception(app)


@app.on_event("startup")
def startup_event():
    set_current_request_id()
    from src.database.permissions.models.user import User
    users = User.query.first()
    if users is None:
        User.user_update(None, 'admin', '000000', 'admin', None, None, True, True, None)
    on_request_end()
    
    import asyncio
    from src.api.middleware import audit_log_worker
    asyncio.create_task(audit_log_worker())


@app.on_event("shutdown")
def shutdown_event():
    print(">>>shutdown_event。。。。。。")
    TestPlanContinueTasking.append_restart_plan()


@app.get("/error")
def error(id:int):
    if id==1:
        raise BusinessException("这是个SimpleException错误！")
    elif id==2:
        raise ValidationException("这是个NoneException错误！")
    elif id==3:
        raise NoPermissionException("这是个NoPermissionException错误！")
    else:
        raise Exception("这是个Exception错误！")



# @app.get("/")
# def root():
#     import os
#     pid = os.getpid()
#     return {"message": "Hello World!", "pid": pid}


@app.get('/{path:path}', summary='vue路由 history 模式', tags=['public'])
async def catch_all(path: str):
    file_path = f'./web'
    if path.startswith('static/'):
        if path.endswith('.js'):
            return FileResponse(f"{file_path}/{path}", media_type='application/javascript')
        if path.endswith('.css'):
            return FileResponse(f"{file_path}/{path}", media_type='text/css')
    if path.endswith('.svg'):
        return FileResponse(f"{file_path}/{path}", media_type='image/svg+xml')
    if path.endswith('.js'):
        return FileResponse(f"{file_path}/{path}", media_type='application/javascript')
        # 处理字体文件
    if path.endswith('.woff'):
        return FileResponse(f"{file_path}/{path}", media_type='font/woff')
    if path.endswith('.woff2'):
        return FileResponse(f"{file_path}/{path}", media_type='font/woff2')
    if path.endswith('.ttf'):
        return FileResponse(f"{file_path}/{path}", media_type='font/ttf')
    if path.endswith('.eot'):
        return FileResponse(f"{file_path}/{path}", media_type='application/vnd.ms-fontobject')
    return FileResponse(f"{file_path}/index.html")


