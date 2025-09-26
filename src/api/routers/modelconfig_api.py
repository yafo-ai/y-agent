from src.database.enums import ModelType
from src.database.models import ModelConfig
from sqlalchemy.orm import Session
from ...database.db_session import get_scoped_session
from fastapi import APIRouter, Depends, Path, Body

router = APIRouter(
    prefix="/api/model_config",
    tags=["模型配置"],
)


@router.get("/all", summary="列表")
def all(session: Session = Depends(get_scoped_session)):
    models = ModelConfig.query.all()
    result = []
    for model in models:
        result.append(
            {"id": model.id, "name": model.name, "type": model.type, "base_name": model.base_name, "api_url": model.api_url, "api_key": model.api_key,
             "temprature": model.temprature, "provider": model.provider, "max_token": model.max_token, "timeout": model.timeout, "note": model.note})
    return result


@router.get("/get/{id}", summary="详情")
def get_model_config(id: int = Path(description="模型id"), session: Session = Depends(get_scoped_session)):
    model = ModelConfig.get(id)
    return {"id": model.id, "name": model.name, "type": model.type, "base_name": model.base_name, "api_url": model.api_url, "api_key": model.api_key,
            "temprature": model.temprature, "provider": model.provider, "max_token": model.max_token, "timeout": model.timeout, "note": model.note}


@router.post("/add", summary="新增")
def model_config_add(name: str = Body(max_length=50, description="名称"),
                     type: str = Body(description="类型"),
                     base_name: str = Body(max_length=50, description="基础模型", default=""),
                     api_url: str = Body(max_length=200, description="api地址", default=""),
                     api_key: str = Body(max_length=200, description="apikey", default=""),
                     temprature: float = Body(description="温度", default=0.1),
                     provider: str = Body(description="提供者", default=""),
                     max_token: int = Body(description="最大token数量", default=None),
                     note: str | None = Body(description="备注", default=None),
                     timeout: int = Body(description="超时时间", default=300),
                     session: Session = Depends(get_scoped_session)
                     ):
    model = ModelConfig(name=name, base_name=base_name, type=ModelType.value_of(type).value, api_url=api_url, api_key=api_key, temprature=temprature,
                        provider=provider)
    model.max_token = max_token
    model.note = note
    model.timeout = timeout if timeout is not None and timeout > 0 else 300
    model.add(True)
    return {"id": model.id}


@router.post("/edit/{id}", summary="编辑")
def model_config_edit(id: int = Path(description="id"),
                      name: str = Body(max_length=50, description="名称"),
                      type: str = Body(description="类型"),
                      base_name: str = Body(max_length=200, description="基础模型"),
                      api_url: str = Body(max_length=200, description="api地址", default=""),
                      api_key: str = Body(max_length=200, description="apikey", default=""),
                      temprature: float = Body(description="温度", default=0.1),
                      provider: str = Body(description="提供者", default=""),
                      max_token: int = Body(description="最大token数量", default=None),
                      note: str | None = Body(description="备注", default=None),
                      timeout: int = Body(description="超时时间", default=300),
                      session: Session = Depends(get_scoped_session)
                      ):
    model = ModelConfig.get(id)
    model.type=ModelType.value_of(type).value
    model.name = name
    model.base_name = base_name
    model.api_url = api_url
    model.api_key = api_key
    model.temprature = temprature
    model.provider = provider
    model.max_token = max_token
    model.note = note
    model.timeout = timeout if timeout is not None and timeout > 0 else 300
    session.commit()
    return {"result": "success"}


@router.post("/delete/{id}", summary="删除")
def model_config_delete(id: int = Path(description="id"), session: Session = Depends(get_scoped_session)):
    model = ModelConfig.get(id)
    model.delete(True)
    return {"result": "success"}
