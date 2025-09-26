from fastapi import APIRouter, Body

from src.configs.system_config import validate_config_data, system_config
from src.database.models import ConfigModel

router = APIRouter(
    prefix="/api/config",
    tags=["配置管理"],
)


@router.get("", summary="配置列表信息")
def configs():
    configs_list = ConfigModel.config_dict_json()
    return configs_list


@router.post('/batch_update', summary="批量更新配置")
def config_batch_update(configs: dict = Body(description="配置项列表", embed=True)):
    validate_config_data(configs)
    ConfigModel.config_all_update(configs)
    system_config.reload_config()
    return {"result": "success"}
