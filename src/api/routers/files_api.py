import mimetypes
from pathlib import Path
from typing import List, Optional
from fastapi.responses import FileResponse, StreamingResponse
from fastapi import APIRouter, Body, Query, Request, UploadFile
import os.path
from src.api.customer_exception import ValidationException
import shutil
import uuid
import base64

from src.database.models import WorkFlow
from src.database.permissions.common.security import validate_token
from src.exts.file_manager import FileManager


router = APIRouter(
    prefix="/api/files",
    tags=["文件上传"],
)


@router.get("/view/{file_name}",summary="获取文件", tags=["public"])
def get_file(file_name: str):
    
    file_manager = FileManager("./src/upload_field/")

    #base64 解密
    file_name = base64.b64decode(file_name).decode('utf-8')
    
    file_path = file_manager.exists(file_name)

    if not file_path:
        raise ValidationException(f"文件 {file_name} 不存在")
    
    full_path = file_manager._get_full_path(file_name)
    mime_type, _ = mimetypes.guess_type(str(full_path))
    if mime_type is None:
        mime_type = "application/octet-stream"

    # 使用 file_manager 的生成器函数
    file_stream = file_manager.load_stream(file_name)
        
    # StreamingResponse 会将生成器产生的数据块逐个发送给客户端
    return StreamingResponse(
        content=file_stream,
        media_type=mime_type,
    )



@router.post("/upload",summary="单文件上传",tags=["public"])
def upload_file(request: Request,file: UploadFile,flow_id: int = Query(description="节点日志ID"),api_key: str = Query(description="API密钥", default=None)):
    """
    上传一个或多个文件
    
    - **max_file_kb**: 最大文件大小(KB)
    - **allowed_ext_types**: 允许的文件类型(MIME类型),逗号分隔
    - **file**: 要上传的文件列表
    """

    if api_key:
        flow = WorkFlow.get(flow_id)
        flow.validate_api_key(api_key)
    else:
        token = request.headers.get("Authorization")
        if not token:
            raise ValidationException("未提供认证信息")
        token = token.split(" ")[-1]
        validate_token(token)

    filename = Path(file.filename).name
    
    if not filename:
        raise ValidationException("文件名不能为空")
    
    file_ext = Path(file.filename).suffix.lower()

    if not file_ext:
        raise ValidationException(f"文件 '{filename}' 没有扩展名")

    new_file_name = f'{uuid.uuid4().hex}{file_ext}'

    import datetime
    now = datetime.datetime.now()
    formatted_date = now.strftime("%Y-%m-%d")

    folder_path = f'./src/upload_field/workflow/{formatted_date}'

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_path = f"{folder_path}/{new_file_name}"

    with open(file_path, 'wb') as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file_path
    #return {'file_name': file.filename, 'file_size': file.size/1024, 'file_ext': file_ext, 'file_path': f'{file_path}'}

