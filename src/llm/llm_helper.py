import re
from typing import Set
from typing import Dict, Any, List
import ast
from json_repair import repair_json
import mimetypes
from src.agent.template.agent_environment import AgentEnvironment
from src.agent.template.undefined import TempUndefined
from src.llm.llm_models import MessageContent,ContentType,HumanMessage


def parse_param_string(param_str: str) -> Dict[str, Any]:
    """
    解析参数字符串为键值对字典
    
    参数:
        param_str: 格式如 'key1=value1, key2=value2, ...' 的字符串
        
    返回:
        包含解析后键值对的字典
    """
    param_str = param_str.strip()
    if not param_str:
        return {}
    
    expressions = split_param_expressions(param_str)
    params = {}
    pattern = re.compile(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*)$', re.DOTALL)
    
    for expr in expressions:
        expr = expr.strip()
        if not expr:
            continue
            
        match = pattern.match(expr)
        if not match:
            continue
            
        key = match.group(1)
        value_str = match.group(2).strip()
        
        # 处理引号包裹的字符串
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            try:
                if value_str.index('[{')<3 or value_str.index('{')<3:
                    repair_value_str=repair_json(value_str,ensure_ascii=False) #修复操作
                    if repair_value_str and repair_value_str!='""':
                        value_str=str(repair_value_str)
                # 使用literal_eval安全解析
                value = ast.literal_eval(value_str)
            except (SyntaxError, ValueError):
                # 解析失败时移除外层引号
                value = value_str[1:-1]
        else:
            # 尝试解析其他类型
            try:
                if value_str.startswith('[') or  value_str.startswith('{'):
                    if value_str.startswith('[{') and not value_str.endswith(']'):
                        value_str += ']'
                    repair_value_str=repair_json(value_str,ensure_ascii=False) #修复操作
                    if repair_value_str and repair_value_str!='""':
                        value_str=str(repair_value_str)
                value = ast.literal_eval(value_str)
            except (SyntaxError, ValueError):
                # 无法解析时保留原始字符串
                value = value_str
                
        params[key] = value
    
    return params

def split_param_expressions(s: str) -> List[str]:
    """
    使用状态机分割参数表达式，处理嵌套结构和转义字符
    
    参数:
        s: 要分割的字符串
        
    返回:
        分割后的参数表达式列表
    """
    stack = []
    current = []
    result = []
    escape = False
    i = 0
    n = len(s)
    
    while i < n:
        char = s[i]
        
        if escape:
            # 处理转义字符
            current.append(char)
            escape = False
            i += 1
            continue
            
        if char == '\\':
            # 设置转义标志
            escape = True
            current.append(char)
            i += 1
            continue
            
        # 处理引号（字符串边界）
        if char in ('"', "'"):
            if stack and stack[-1] == char:
                # 关闭相同类型的引号
                stack.pop()
            else:
                # 开启新引号
                stack.append(char)
            current.append(char)
            i += 1
            continue
            
        # 处理括号嵌套
        if char in ('(', '[', '{'):
            stack.append(char)
            current.append(char)
            i += 1
        elif char in (')', ']', '}'):
            if stack:
                if (char == ')' and stack[-1] == '(') or \
                   (char == ']' and stack[-1] == '[') or \
                   (char == '}' and stack[-1] == '{'):
                    stack.pop()
            current.append(char)
            i += 1
            
        # 处理参数分隔符
        elif char == ',':
            if not stack:  # 不在嵌套结构中
                result.append(''.join(current).strip())
                current = []
            else:
                current.append(char)
            i += 1
        else:
            current.append(char)
            i += 1
    
    # 添加最后一个表达式
    if current:
        result.append(''.join(current).strip())
    
    return result


def output_rules_parser_json(output: str):
    json_data = []
    pattern = r'\<\|\s*(\w+)\((.*?)\)\s*\|>'
    matches = re.findall(pattern, output, re.DOTALL)
    for match in matches:
        func_name = match[0]
        params_str = match[1]
        params = {}
        result = parse_param_string(params_str)
        for key, value in result.items():
            params[key] = value
        json_data.append({"toolname": func_name, "args": params})
    return json_data


def get_jinja2_variables_from_template_rende(template: str) -> Set[str]:
    try:
        from jinja2 import Environment, meta
    except ImportError:
        raise ImportError(
            "jinja2 not installed, which is needed to use the jinja2_formatter. "
            "Please install it with `pip install jinja2`."
        )
    env = Environment()
    ast = env.parse(template)
    variables = meta.find_undeclared_variables(ast)
    return variables


def jinja2_template_render(template: str, context: dict) -> str:
    
    try:
        from jinja2 import Template
    except ImportError:
        raise ImportError(
            "jinja2 not installed, which is needed to use the jinja2_formatter. "
            "Please install it with `pip install jinja2`."
        )
    # j2_template = Template(template,keep_trailing_newline=True)

    env = AgentEnvironment(undefined=TempUndefined)  # 使用自定义的Undefined类

    j2_template = env.from_string(template)

    return j2_template.render(**context)



def judge_file_type(file_path):



    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        if mime_type.startswith('image/'):
            return ContentType.IMAGE,mime_type
        elif mime_type.startswith('video/'):
            return ContentType.VIDEO,mime_type
        elif mime_type.startswith('audio/'):
            return ContentType.AUDIO,mime_type
        elif mime_type.startswith('text/') or \
             mime_type in ['application/pdf', 'application/msword', 
                           'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                           'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
            return ContentType.FILE,mime_type
    
    return ContentType.FILE,mime_type


def llm_vision_message(vision_file_str:str,text:str)->HumanMessage:
    """视觉模型消息"""
    #解析字符串
    file_paths=None
    try:
        file_paths = ast.literal_eval(vision_file_str)
    except (SyntaxError, ValueError):
        file_paths = vision_file_str.strip()

    if isinstance(file_paths,str):
        file_paths=[file_paths]
    if len(file_paths)==0:
        return []
    
    #组织成消息格式
    
    import base64

    messages:list[MessageContent]=[]

    for file_path in file_paths:

        file_type,mime_type=judge_file_type(file_path)
        with open(file_path, "rb") as img_file:
            img_base = base64.b64encode(img_file.read()).decode("utf-8")
        messages.append(MessageContent(type=file_type,value=f"data:{mime_type};base64,{img_base}"))

    messages.append(MessageContent(type=ContentType.TEXT,value=text))

    return HumanMessage(content=messages)
    



def llm_generate_text(llm_id:int,prompt: str,context: dict,vision_file_str:str=None) -> str:
    """使用模型生成文本"""
    from src.llm.llm_adapter import AdapterFactory
    from src.llm.llm_models import HumanMessage

    prompt = jinja2_template_render(prompt,context)

    if vision_file_str and len(vision_file_str.strip())>0:
        message=llm_vision_message(vision_file_str,prompt)
    else:
        message=HumanMessage(content=prompt)

    response= AdapterFactory(llm_id).invoke([message])

    return response.content


def llm_content_markdown_parser(text:str)->str:
    """解析markdowng格式"""
    import re
    match = re.search(r"```markdown(md_text)?(.*)```", text, re.DOTALL)
    if match is None:
        md_text = text
    else:
        md_text = match.group(2)
    return md_text


def llm_content_pydantic_object_parser(model_class,text:str):
    """解析pydantic对象"""
    from pydantic import BaseModel
    if not issubclass(model_class, BaseModel):
        raise ValueError("model_class must be a subclass of BaseModel")
    
    json_data=output_rules_parser_json(text)

    args=json_data[0].get('args', {})

    return model_class(**args)