from collections import defaultdict
import datetime
from enum import Enum
from typing import Any, List, Optional,Literal
from pydantic import BaseModel, Field,validator
import re
class NodeType(Enum):
    """
    节点类型
    """
    WORK_SPACE = 'work_space'
    START = 'start'
    LLM = 'llm'
    TOOL = 'tool'
    TEMP_EXECUTOR="temp_executor"
    # OUTPUT= 'output'
    LOOP_START='loop_start'
    LOOP_END='loop_end'
    LOOP= 'loop'

   
    @classmethod
    def value_of(cls, value: str) -> 'NodeType':

        for node_type in cls:
            if node_type.value == value:
                return node_type
        raise ValueError(f'invalid node type value {value}')


class VariablesType(Enum):
    """
    自定义变量类型
    """  
    OVER_WRITE='over_write'
    APPEND='append'
    APPEND_UNIQUE='append_unique'

    @classmethod
    def value_of(cls, value: str) -> 'VariablesType':

        for _type in cls:
            if _type.value == value:
                return _type
        raise ValueError(f'invalid node type value {value}')
    
class DataType(Enum):
    """数据类型"""
    STRING = 'String'
    INTEGER = 'Integer'
    BOOLEAN = 'Boolean'
    NUMBER = 'Number'
    OBJECT = 'Object'
    FILE='File'
    ARRAY_STRING = 'Array<String>'
    ARRAY_INTEGER = 'Array<Integer>'
    ARRAY_BOOLEAN = 'Array<Boolean>'
    ARRAY_NUMBER = 'Array<Number>'
    ARRAY_OBJECT = 'Array<Object>'
    ARRAY_FILE='Array<File>'


    @classmethod
    def value_of(cls, value: str) -> 'DataType':

        for _type in cls:
            if _type.value == value:
                return _type
        raise ValueError(f'invalid node type value {value}')
    

class FunctionCallLog(BaseModel):
    """函数调用日志"""
    function_name:str
    function_options:Any|None
    function_args:Any|None
    function_return:Any|None
    start_time:datetime.datetime
    end_time:datetime.datetime
    duration:float

class AgentRunLog(BaseModel):
    """代理运行时日志"""
    id:str
    pid:str|None
    triggerer:str
    runner:str
    runner_id:str|None
    runner_type:str|None
    parent_loop_node_id:str|None
    runner_run_times:int
    start_time:datetime.datetime
    end_time:datetime.datetime
    duration:float
    prompt_temp:str|None
    prompt_str:str|None
    vision_file_str:str|None
    response_content:Any|None
    response_metadata:Any|None
    function_calls:list[FunctionCallLog]|None
    room_messages:list['ChatRoomMessage']|None
    inputs:Any|None
    variables:Any|None
    role_variables:Any|None
    model_name:str|None
    tokens:int|None
    is_section:bool|None # 分身True
    is_section_sub:bool|None # 分身后子数据True

class ChatRoomMessage(BaseModel):
    """代理运行时多角色互动聊天"""
    id:Optional[str] = None
    from_role:str
    to_role:str|None
    message:str
    send_time:datetime.datetime


class NodeSectionRunResult(BaseModel):
    """"节点分身执行结果"""
    start_time:Optional[datetime.datetime]=None
    end_time:Optional[datetime.datetime]=None
    prompt_temp:Optional[str] = None  # 提示内容
    prompt_str: Optional[str] = None  # 输入内容
    response: Optional[Any] = None  # 输出内容
    error:Optional[str] = None  # 错误信息
    section_name:Optional[str] = None  # 名称后缀

class NodeRunResult(BaseModel):
    """节点运行结果"""
    target_roles: Optional[List[str]] = None  # 目标角色
    prompt_temp:Optional[str] = None  # 提示内容
    prompt_str: Optional[str] = None  # 输入内容
    vision_file_str:Optional[str] = None  # 视觉模型文件路径
    response: Optional[Any] = None  # 输出内容
    function_calls: Optional[List[FunctionCallLog]] = None
    section_results: Optional[List[NodeSectionRunResult]] = None

    



class NextNode(BaseModel):
    """下一个节点运行约束"""
    role:str
    max_run_times:int

class FunctionOption(BaseModel):
    """函数输入"""
    fun_name:str
    options:Any


class FileConstraint(BaseModel):
    """用于文件类型输入的约束条件"""
    max_file_kb: int = Field(..., description="最大文件大小（KB）")
    allowed_ext_types: List[str] = Field(..., description="允许的文件扩展名列表，如 ['.jpg', '.png']")
    max_qty: Optional[int] = Field(default=None, description="最大文件数量")

class InputVariable(BaseModel):
    """输入变量"""
    name:str
    data_type:DataType  # 限制为特定的字面量值
    desc:str
    is_required:bool # 是否为必填
    object_fields:Optional[List['InputVariable']] = Field(default=None, description='对象字段（仅当类型为Object时有效）')
    constraint:Optional[FileConstraint]=None

    @validator('name')
    def var_name_must_be_valid(cls, value):
        # 正则表达式匹配系统变量名规则，不允许使用点（.）连接
        pattern = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
        if not pattern.match(value):
            raise ValueError('name must follow system variable naming conventions')
        return value
    
    @validator('constraint')
    def constraint_must_match_type(cls, value, values):
        data_type = values.get('data_type')
        if data_type == DataType.FILE or data_type == DataType.ARRAY_FILE:
            if not isinstance(value, FileConstraint):
                raise ValueError('When data_type is "File", constraint must be a valid FileConstraint object.')
        return value
    
    
class OutputVariable(BaseModel):
    """输出变量"""
    prefix:Optional[Literal['space', 'role']] = None
    name:str
    data_type: DataType  #类型
    desc:str
    object_fields:Optional[List['OutputVariable']] = Field(default=None, description='对象字段（仅当类型为Object时有效）')

    
    @validator('prefix')
    def var_type_must_be_primitive(cls, value):
        if value not in ['space', 'role']:
            raise ValueError('prefix must be one of "space", "role", None')
        return value
    

    @validator('name')
    def var_name_must_be_valid(cls, value):
        # 正则表达式匹配系统变量名规则，不允许使用点（.）连接
        pattern = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
        if not pattern.match(value):
            raise ValueError('name must follow system variable naming conventions')
        return value
    
    
class BaseEvent(BaseModel):
    """事件"""
    pass

class SendHumanMessageEvent(BaseEvent):
    """用户消息发送事件"""
    id:Optional[str] = None #回答id
    user_id:Optional[str] = None #客户id
    pin_id:Optional[str]=None #客服id
    workflow_id:Optional[str]=None #工作流id
    question_id:Optional[str]=None #问题id
    node_role: str #节点角色
    message:str #消息内容
    


class McpTool(BaseModel):
    id:str|None=None
    provider_id: int | None = None
    name: str
    func_name: str
    caption: str
    is_enable: bool
    api_url: str
    api_method: str
    in_params: List['ToolInParam']
    out_params: List['ToolOutParam']

    @validator('func_name')
    def var_fun_nanme_must_be_valid(cls, value):
        # 正则表达式匹配系统变量名规则，不允许使用点（.）连接
        pattern = re.compile(r'^[A-Za-z_][A-Za-z0-9_-]*$')
        if not pattern.match(value):
            raise ValueError('函数名必须符合系统变量名规则，[A-Za-z_][A-Za-z0-9_]')
        return value
class APITool(BaseModel):
    id: int | None = None
    name: str
    func_name: str
    caption: str
    is_enable: bool
    api_url: str
    api_method: str
    in_params: List['ToolInParam']
    out_params: List['ToolOutParam']

    @validator('func_name')
    def var_fun_nanme_must_be_valid(cls, value):
        # 正则表达式匹配系统变量名规则，不允许使用点（.）连接
        pattern = re.compile(r'^[A-Za-z_][A-Za-z0-9_-]*$')
        if not pattern.match(value):
            raise ValueError('函数名必须符合系统变量名规则，[A-Za-z_][A-Za-z0-9_]')
        return value

class ToolInParam(BaseModel):
    id:str|int|None
    name: str
    caption: str
    param_way: str
    data_type: str
    default_value: str
    is_required: bool 
    children: List['ToolInParam'] = []

    @validator('name')
    def var_fnanme_must_be_valid(cls, value):
        # 正则表达式匹配系统变量名规则，不允许使用点（.）连接
        pattern = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
        if not pattern.match(value):
            raise ValueError('字段名必须符合系统变量名规则，[A-Za-z_][A-Za-z0-9_]')
        return value

    @validator('children')
    def check_depth(cls, v):
        def max_depth(nodes, current_depth):
            max_d = current_depth
            for node in nodes:
                if node.children:
                    d = max_depth(node.children, current_depth+1)
                    if d > max_d:
                        max_d = d
            return max_d
            
        if max_depth(v, 1) > 3:
            raise ValueError("参数嵌套不能超过3级")
        return v


class ToolOutParam(BaseModel):
    id:str|int|None
    name: str
    caption: str
    data_type: str
    children: List['ToolOutParam'] = []

    @validator('name')
    def var_fnanme_must_be_valid(cls, value):
        # 正则表达式匹配系统变量名规则，不允许使用点（.）连接
        pattern = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
        if not pattern.match(value):
            raise ValueError('字段名必须符合系统变量名规则，[A-Za-z_][A-Za-z0-9_]')
        return value
    
    @validator('children')
    def check_depth(cls, v):
        def max_depth(nodes, current_depth):
            max_d = current_depth
            for node in nodes:
                if node.children:
                    d = max_depth(node.children, current_depth+1)
                    if d > max_d:
                        max_d = d
            return max_d
            
        if max_depth(v, 1) > 3:
            raise ValueError("参数嵌套不能超过3级")
        return v
class EvaluationResponse(BaseModel):
    """关于文档资料的信息"""
    accuracy: Optional[bool] = Field(description="结果")
    score: Optional[int] = Field(description="评分")