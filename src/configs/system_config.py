import enum
import json
from abc import ABC, abstractmethod
from typing import Optional

from src.api.customer_exception import ValidationException
from src.database.models import ConfigModel


# 校验配置信息
def validate_config_data(in_config_data: dict):
    """
    校验配置信息
    """
    SystemConfigKnowledge().check_data(in_config_data[SystemConfigKnowledge.config_key][ConfigModel.config_value.key])
    SystemConfigSecurity().check_data(in_config_data[SystemConfigSecurity.config_key][ConfigModel.config_value.key])
    SystemConfigVector().check_data(in_config_data[SystemConfigVector.config_key][ConfigModel.config_value.key])


class DefaultConfig(ABC):
    def __init__(self):
        self.id: Optional[int] = None
        self.config_key = 'sys_config'
        self.config_value: Optional[str | dict] = None

    def check_config_value(self):
        if self.config_value is None or self.config_value == '':
            raise ValidationException(f"系统配置[{self.config_key}]未设置值")

    @abstractmethod
    def init_data(self):
        pass

    # 校验 输入 config_value 是否合法
    def check_data(self, config_value: str):
        self.config_value = config_value
        self.init_data()

    def load_db_config(self):
        self.config_value = ConfigModel.config_dict_json()[self.config_key]["config_value"]
        return self.init_data()


# 基本配置
class SystemConfigBase(DefaultConfig):
    config_key: str = 'sys_config.base'
    config_key_name: str = '系统基本设置：'

    def __init__(self):
        super().__init__()
        self.config_key: str = 'sys_config.base'
        self.fastapi_host: Optional[str] = None
        self.fastapi_port: Optional[int] = None
        self.is_record_operation_log: Optional[bool] = None
        self.db_connect_str: Optional[str] = None
        self.web_name: Optional[str] = None
        self.web_desc: Optional[str] = None
        self.config_value: Optional[str] = ConfigModel.config_base_info().config_value

    def init_data(self) -> 'SystemConfigBase':
        self.check_config_value()
        tmp_config_value = json.loads(self.config_value)
        self.fastapi_host = tmp_config_value.get('fastapi_host', None)
        self.fastapi_port = tmp_config_value.get('fastapi_port', None)
        self.is_record_operation_log = tmp_config_value.get('is_record_operation_log', None)
        self.db_connect_str = tmp_config_value.get('db_connect_str', None)
        self.web_name = tmp_config_value.get('web_name', None)
        self.web_desc = tmp_config_value.get('web_desc', None)
        return self


# 知识库设置
class SystemConfigKnowledge(DefaultConfig):
    config_key: str = 'sys_config.knowledge'
    config_key_name: str = '知识库配置：'

    def __init__(self):
        super().__init__()
        self.config_key: str = 'sys_config.knowledge'
        self._chunk_size: Optional[int] = None
        self._chunk_size_overlap: Optional[int] = None

    @property
    def chunk_size(self):
        return self._chunk_size

    @chunk_size.setter
    def chunk_size(self, value):
        if value is None or not isinstance(value, int):
            raise ValidationException(f"{self.config_key_name}切块大小[chuck_size]必须是整数")
        if value <= 50:
            raise ValidationException(f"{self.config_key_name}切块大小[chuck_size]必须是大于50的整数")
        self._chunk_size = value

    @property
    def chunk_size_overlap(self):
        return self._chunk_size_overlap

    @chunk_size_overlap.setter
    def chunk_size_overlap(self, value):
        if self.chunk_size is None:
            raise ValidationException(f"{self.config_key_name}切块大小[chuck_size]必须先设置")
        if value is None or not isinstance(value, int):
            raise ValidationException(f"{self.config_key_name}重叠大小[chunk_size_overlap]必须是整数")
        # if value <= 50 or value >= self.chunk_size:
        #     raise NoneException(f"{self.config_key_name}重叠大小[chunk_size_overlap]必须大于50并且小于切块大小")
        self._chunk_size_overlap = value

    def init_data(self) -> 'SystemConfigKnowledge':
        self.check_config_value()
        if isinstance(self.config_value, dict):
            tmp_config_value = self.config_value
        else:
            tmp_config_value = json.loads(self.config_value)
        self.chunk_size = tmp_config_value.get('chunk_size', None)
        self.chunk_size_overlap = tmp_config_value.get('chunk_size_overlap', None)
        return self


# 安全设置
class SystemConfigSecurity(DefaultConfig):
    config_key: str = 'sys_config.security'
    config_key_name: str = '安全配置：'

    def __init__(self):
        super().__init__()
        self.config_key: str = 'sys_config.security'
        self._access_token_expire_minutes: Optional[int] = None
        self._refresh_token_expire_minutes: Optional[int] = None

    @property
    def access_token_expire_minutes(self):
        return self._access_token_expire_minutes

    @access_token_expire_minutes.setter
    def access_token_expire_minutes(self, value):
        if value is None or not isinstance(value, int):
            raise ValidationException(f"{self.config_key_name}令牌过期时间[access_token_expire_minutes]必须是整数")
        if value <= 120:
            raise ValidationException(f"{self.config_key_name}令牌过期时间[access_token_expire_minutes]必须大于120的整数")
        self._access_token_expire_minutes = value

    @property
    def refresh_token_expire_minutes(self):
        return self._refresh_token_expire_minutes

    @refresh_token_expire_minutes.setter
    def refresh_token_expire_minutes(self, value):
        if self.access_token_expire_minutes is None:
            raise ValidationException(f"{self.config_key_name}令牌过期时间[access_token_expire_minutes]必须先设置")
        if value is None or not isinstance(value, int):
            raise ValidationException(f"{self.config_key_name}令牌刷新时间[refresh_token_expire_minutes]必须是整数")
        if value <= 60 or value >= self.access_token_expire_minutes:
            raise ValidationException(f"{self.config_key_name}令牌刷新时间[refresh_token_expire_minutes]必须大于60并且小于访问令牌过期时间")
        self._refresh_token_expire_minutes = value

    def init_data(self) -> 'SystemConfigSecurity':
        self.check_config_value()
        tmp_config_value = json.loads(self.config_value)
        self.access_token_expire_minutes = tmp_config_value.get('access_token_expire_minutes', None)
        self.refresh_token_expire_minutes = tmp_config_value.get('refresh_token_expire_minutes', None)
        return self


class ProvidersData:
    def __init__(self, provider_name: Optional[str], connect_type: Optional[list[str]]):
        self.provider_name: Optional[str] = provider_name
        self.connect_type: Optional[list[str]] = connect_type


class ConnectType(enum.Enum):
    local = "local(本地)"
    remote = "remote(远程)"


# 向量数据库配置
class SystemConfigVector(DefaultConfig):
    config_key: str = 'sys_config.vector_provider'
    config_key_name: str = '向量数据库配置：'

    def __init__(self):
        super().__init__()
        self.config_key: str = 'sys_config.vector_provider'
        self.providers: list[ProvidersData] = [ProvidersData("chromadb", ["local", "remote"])]

        self.selected_provider_name: Optional[str] = None
        self.selected_connect_type: Optional[ConnectType] = None
        self.connect_str: Optional[str] = None
        self.param_config: Optional[dict] = None

    def init_data(self):
        self.check_config_value()
        tmp_config_value = json.loads(self.config_value)
        self.selected_provider_name = tmp_config_value.get('selected', {}).get('provider_name', None)
        tmp_connect_type = tmp_config_value.get('selected', {}).get('connect_type', None)
        if tmp_connect_type is not None:
            self.selected_connect_type = ConnectType(tmp_connect_type)
        self.connect_str = tmp_config_value.get('selected', {}).get('connect_str', None)
        self.param_config = tmp_config_value.get('selected', {}).get('connect_str', {}).get('param_config', None)
        if self.param_config == '':
            self.param_config = None
        if self.param_config is not None and isinstance(self.param_config, str) and self.param_config != "":
            try:
                self.param_config = json.loads(self.param_config)
            except Exception as e:
                raise ValidationException(f"{self.config_key_name}连接参数配置[param_config]格式错误，请检查json格式")
            if self.param_config.get('collection_metadata', None) is not None:
                try:
                    self.param_config['collection_metadata'] = json.loads(self.param_config['collection_metadata'])
                except Exception as e:
                    raise ValidationException(f"{self.config_key_name}连接参数配置[param_config]collection_metadata格式错误，请检查json格式")

        return self


# 向量模型配置
class SystemConfigEmbedding(DefaultConfig):
    config_key: str = 'sys_config.embedding_provider'
    config_key_name: str = '向量模型配置：'

    def __init__(self):
        super().__init__()
        self.config_key: str = 'sys_config.embedding_provider'
        self.providers: list[str] = ['openai', 'vllm', 'xinference']
        self.selected_provider_name: Optional[str] = None
        self.selected_model_name: Optional[str] = None
        self.selected_url: Optional[str] = None
        self.selected_api_key: Optional[str] = None

    def init_data(self) -> 'SystemConfigEmbedding':
        self.check_config_value()
        tmp_config_value = json.loads(self.config_value)
        self.selected_provider_name = tmp_config_value.get('selected', {}).get('provider_name', None)
        self.selected_model_name = tmp_config_value.get('selected', {}).get('model_name', None)
        self.selected_url = tmp_config_value.get('selected', {}).get('connect_url', None)
        self.selected_api_key = tmp_config_value.get('selected', {}).get('api_key', None)
        return self


class SystemConfig:

    def __init__(self):
        self.seed_config()
        self.__load_db_config()

    def reload_config(self):
        self.__load_db_config()

    # 数据库配置初始化
    @classmethod
    def seed_config(cls):
        first_data = ConfigModel.query.first()
        if first_data is not None:
            return
        with open('./src/configs/system_config_seed.json', 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        session = ConfigModel().session
        for config_key, config_value in config_data.items():
            ConfigModel(config_key=config_key, config_value=json.dumps(config_value, ensure_ascii=False)).add()
        session.commit()

    def __load_db_config(self):
        self.sys_db_base: SystemConfigBase = SystemConfigBase().load_db_config()
        self.sys_db_knowledge: SystemConfigKnowledge = SystemConfigKnowledge().load_db_config()
        self.sys_db_security: SystemConfigSecurity = SystemConfigSecurity().load_db_config()
        self.sys_db_vector: SystemConfigVector = SystemConfigVector().load_db_config()
        self.sys_db_embedding: SystemConfigEmbedding = SystemConfigEmbedding().load_db_config()


system_config = SystemConfig()
