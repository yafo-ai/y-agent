import asyncio
import json
from datetime import datetime

from fastapi import Request

from src.configs.server_config import IS_RECORD_OPERATION_LOG
from src.database.permissions.common.security import validate_token, refresh_token
from src.database.permissions.models.operationLog import OperationLog
from src.utils.log_helper import logger
from src.database.db_session import set_current_request_id, on_request_end
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.network_helper import get_network_ip, get_ip_address


class RequestIDMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        # 请求开始前，生成请求ID
        set_current_request_id()
        try:
            # 调用实际的API处理函数
            response = await call_next(request)
        finally:
            on_request_end()
        # 请求结束后，可以从响应中移除请求ID，这里只是示例，实际上你可能不需要删除它
        # 因为请求已经结束了，除非你在其他地方（如数据库或日志）存储了这个ID

        return response


AUDIT_BATCH_SIZE = 5  # 每批插入数量
AUDIT_BUFFER_TIME = 1  # 缓冲时间（秒）
audit_log_queue = asyncio.Queue()


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.now().timestamp()
        request_body = None
        print(f'当前路由:{request.url.path}')
        if (not request.url.path.lower().startswith('/api/filedatabase/add')
                and not request.url.path.lower().startswith('/api/filedatabase/update')
                and request.url.path.lower() != '/api/files/upload'
                and request.url.path.lower() != '/api/documents/add'
                and request.url.path.lower() != '/api/goods/import'
                and request.url.path.lower() != '/api/goods/profile/import'
                and request.url.path.lower() != '/api/test/case/unit/import'
                and request.url.path.lower() != '/api/train/case/import'
                and request.url.path.lower() != '/api/test/case/unit/import_update'
                and request.url.path.lower() != '/api/train/case/import_update'
                and request.url.path.lower() != '/api/workflow/import'):
            
            if request.method in ["POST", "PUT", "PATCH"]:
                request_body = await request.json() if await request.body() else None
        # 调用实际的API处理函数
        response = await call_next(request)
        duration = datetime.now().timestamp() - start_time
        try:
            response.headers["x-new-token"] = ''
            if request.url.path.lower() != '/api/authorize/login' and response.headers.get(
                    "Authorization") is not None and response.headers.get("Authorization") != '':
                new_token = refresh_token(request.headers.get("Authorization").split(" ")[1])
                if hasattr(response, 'headers') and new_token is not None and new_token != '':
                    response.headers["x-new-token"] = new_token

            user_id = None
            user_name = None
            if hasattr(request.state, 'user_dict'):
                user_id = request.state.user_dict.get("id")
                user_name = request.state.user_dict.get("username")
            else:
                if request.headers.get("Authorization"):
                    token = request.headers.get("Authorization").split(" ")[1]
                    user = validate_token(token)
                    if user:
                        user_id = user.id
                        user_name = user.username
            query_params = None
            if len(dict(request.query_params).keys()) > 0:
                query_params = json.dumps(dict(request.query_params), ensure_ascii=False)
            if request.url.path.lower() == '/api/authorize/login':
                request_body['password'] = '******'
            if request.url.path.endswith('/reset_password'):
                request_body['old_password'] = '******'
                request_body['new_password'] = '******'
            if request.url.path.lower() == '/api/user/add':
                request_body['password'] = '******'
            if IS_RECORD_OPERATION_LOG:
                log_dict = {
                    "api_path": request.url.path,
                    "user_id": user_id,
                    "user_name": user_name,
                    "request_params": query_params,
                    "request_body": json.dumps(request_body, ensure_ascii=False) if request_body is not None else None,
                    "ip_address": get_network_ip(request),
                    "address": get_ip_address(get_network_ip(request)),
                    "method": request.method,
                    "status_code": response.status_code,
                    "duration": duration
                }
                await audit_log_queue.put(log_dict)
        except Exception as e:
            logger.error(f"日志记录失败：{e}")
        return response


async def audit_log_worker():
    while True:
        list_logs_dict = []
        while len(list_logs_dict) < AUDIT_BATCH_SIZE and not audit_log_queue.empty():
            list_logs_dict.append(await audit_log_queue.get())

        if len(list_logs_dict) > 0:
            try:
                set_current_request_id()
                session = OperationLog().session
                for log_dict in list_logs_dict:
                    log = OperationLog(api_path=log_dict.get('api_path'),
                                       user_id=log_dict.get('user_id'),
                                       user_name=log_dict.get('user_name'))
                    log.request_params = log_dict.get('request_params')
                    log.request_body = log_dict.get('request_body')
                    log.ip_address = log_dict.get('ip_address')
                    log.address = log_dict.get('address')
                    log.method = log_dict.get('method')
                    log.status_code = log_dict.get('status_code')
                    log.duration = log_dict.get('duration')
                    log.add()
                session.commit()
            except Exception as e:
                logger.error(f"批量日志记录失败：{e}")
            finally:
                on_request_end()

        await asyncio.sleep(AUDIT_BUFFER_TIME)
