
from enum import Enum

#知识库类型
class KnowledgeBaseType(int,Enum):
    文档库 = 1
    产品库 = 2
    参数库 = 3


class ProductAttributeDataType(int,Enum):
    字符串=1
    数值=2
    日期=3
    列表=4


class PromptDataType(int, Enum):
    """
    提示词类型
    """
    接待客服 = 1001


    知识筛选员 = 2001


    知识回答员 = 3001


    Markdown编辑员 = 4001


    聊天记录总结员 = 5001


    测试结果测评员 = 6001




class FileTemplateType(int, Enum):
    """产品上传文件类型  1001：纵向商品Excel文件"""
    产品参数模板 = 1001
    # 其他商品文件 = 9999


def get_enum_name(enum_class, value):
    """根据数字获取枚举文本名称"""
    for enum_member in enum_class:
        if enum_member.value == value:
            return enum_member.name
    return None


class TestCaseStateType(int, Enum):
    """测试用例状态"""
    默认 = 0
    准备就绪 = 1001
    测试中 = 2001
    测试完成 = 3001


class TestCaseResultType(int, Enum):
    """测试用例结果"""
    默认 = 0
    未测试 = 1001
    成功 = 2001
    失败 = 3001


class TestPlanState(int, Enum):
    """测试计划状态"""
    默认 = 0
    准备就绪 = 1001
    测试中 = 2001
    测试完成 = 3001


class ModelType(Enum):
    """模型类型"""

    LLM = 'LLM'
    VLM  = 'VLM'
    
    @classmethod
    def value_of(cls, value: str) -> 'ModelType':

        for _type in cls:
            if _type.value == value:
                return _type
        raise ValueError(f'invalid node type value {value}')

class LogOrigin(Enum):
    """日志来源"""
    未知=None
    京东咚咚=1
    流程试运行=2
    流程分享=3
    流程测试=4
    企业微信=5
    其他平台=99

    @classmethod
    def value_of(cls, value: int | None) -> 'LogOrigin':

        for _type in cls:
            if _type.value == value:
                return _type
        raise ValueError(f'invalid log origin value {value}')

class ModelProvider(Enum):
    """模型提供者"""

    OpenAI = 'OpenAI'
    ZhipuAI = 'ZhipuAI'
    Ollama = 'Ollama'
    Tongyi = 'Tongyi'
    
    @classmethod
    def value_of(cls, value: str) -> 'ModelProvider':

        for _type in cls:
            if _type.value == value:
                return _type
        raise ValueError(f'invalid node type value {value}')