
import ast
import json
from typing import Any, List
import requests
from src.agent.tools.function_base import FunctionBase
from src.agent.model_types import DataType
from src.agent.working.working_space import WorkingSpace



def dict_to_formatted_string(d):
   # 将字典转换为键值对字符串
   pairs = []
   for key, value in d.items():
       if isinstance(value, str):
           # 字符串值
           pair = f"{key}='{value}'"
       else:
           # 其他类型（如字典、列表等）
           pair = f"{key}={value}"
       pairs.append(pair)
   
   # 将所有键值对用逗号连接成一个字符串
   formatted_string = ','.join(pairs)
   return formatted_string


        
class FunctionPluginTool(FunctionBase):
    """
    插件工具类
    """
    def __init__(self,tool_id:int,function_name:str,tool_name:str,tool_desc:str,api_url:str,api_method:str,in_params:str,out_params:str):
        """注册插件工具"""
        super().__init__()
        self.tool_id=tool_id
        self.name=function_name
        self.tool_name=tool_name    
        self.description=tool_desc
        self.api_url=api_url
        self.api_method=api_method
        self.in_params=in_params
        self.out_params=out_params

    
    def _run(self,space:WorkingSpace,options, *args, **kwargs):

        """
        从kwargs提取大模型参数
        从options提取用户指定的参数，并替换变量
        组装流程的是输入inputs
        funname(a="",b="",c={'a': '123123', 'b': '123'})
        """

        # 存储被替换的变量内容
        temp_data={}

        inputs_str=options.get("inputs") 
        inputs_dict =json.loads(inputs_str)
        for key, value in inputs_dict.items():
            #如用户配置的输出参数是空的，说明需要大模型填写
            if value is None or value == "":
                inputs_dict[key]= kwargs.get(key,None) #直接从大模型中获取
            elif '{{' in value or '{%' in value: #如果用户配置的输出参数是变量，需要替换变量
                inputs_dict[key]=self.template_render(space,value,options)
                temp_data[key]=inputs_dict[key]
        # options["inputs"]=json.dumps(inputs_dict)
        output_option=options.get("output_option","json")
        in_params=json.loads(self.in_params) if self.in_params else []
        response=self.do_http_request(in_params,inputs_dict)

        try:
            response_data=response.json()
            out_params=json.loads(self.out_params) if self.out_params else []
            if len(out_params)==0:
                return response_data,temp_data
            parsed_data = self.parse_response(response_data, out_params)
            if output_option=="json":
                return parsed_data,temp_data
            return self.format_output(parsed_data, out_params),temp_data
        
        except Exception as e:
            return response.text,temp_data

        

    def get_function_description(self,options) -> str:
        """获取工具描述"""
        return self.description

    def get_function_command_prompt(self,options) -> str:
        """
        基于工具输入参数和工具配置，生成工具指令提示词
        工具配置如果是空这，需要大模型填写，注意提示词的生成。
        
        返回：
        funname(a="",b="",c={'a': '123123', 'b': '123'})
        """
        schemas_json={}
        input_dict =self.convert_input_variables_json()
        #用户配置的输出项目
        options_inputs=options.get("inputs") 
        options_inputs_dict =json.loads(options_inputs)
        for key, value in options_inputs_dict.items():
            #如用户配置的输出参数是空的，说明需要大模型填写
            if value is None or value == "":
                schemas_json[key]= input_dict[key] #直接替换用户输入的描述值
        if schemas_json is {}:
            return  f'{self.name}()'
        return  f'{self.name}({dict_to_formatted_string(schemas_json)})'
        
    
    def _convert_field(self, field: dict):
        """处理单个字段，根据数据类型返回对应的结构"""
        name = field["name"]
        data_type = DataType.value_of(field["data_type"])
        
        # 基本类型处理
        if data_type in (DataType.STRING, DataType.NUMBER, DataType.BOOLEAN, DataType.INTEGER):
            return field["caption"] if field["default_value"]=="" else field["default_value"]
        
        # 数组基本类型处理
        if data_type in (DataType.ARRAY_STRING, DataType.ARRAY_NUMBER, 
                        DataType.ARRAY_BOOLEAN, DataType.ARRAY_INTEGER):
            return [field["caption"]]
        
        # 对象类型处理
        if data_type == DataType.OBJECT:
            if not field.get("children"):
                raise ValueError(f"object variable {name} must have object_fields")
            return self._convert_object_fields(field["children"])
        
        # 数组对象类型处理
        if data_type == DataType.ARRAY_OBJECT:
            if not field.get("children"):
                raise ValueError(f"array object variable {name} must have object_fields")
            return [self._convert_object_fields(field["children"])]
        
        raise ValueError(f"Unsupported data type: {data_type}")

    def _convert_object_fields(self, object_fields: List[dict]) -> dict:
        """递归处理对象字段"""
        return {field["name"]: self._convert_field(field) for field in object_fields}

    def convert_input_variables_json(self):
        """把输入变量转换为描述的字典"""
        inputs_variables_json = {}
        inputs = json.loads(self.in_params) if self.in_params else []
        
        for v in inputs:
            name = v["name"]
            if name in inputs_variables_json:
                raise KeyError(f"variable {name} already exist")
            inputs_variables_json[name] = self._convert_field(v)
        
        return inputs_variables_json
    

    def parse_response(self, data: dict, out_params: List[dict]) -> dict:
        result = {}
        
        def process_output(param: dict, source: dict, target: dict):
            if param["name"] not in source:
                return
            value = source[param["name"]]

            if DataType.value_of(param["data_type"]) == DataType.ARRAY_OBJECT:
                if not isinstance(value, list):
                    return
                processed_elements = []
                for element in value:
                    element_result = {}
                    for child in param["children"]:
                        process_output(child, element, element_result)
                    processed_elements.append(element_result)
                target[param["name"]] = processed_elements
            elif param["children"]:
                nested = {}
                for child in param["children"]:
                    process_output(child, value, nested)
                target[param["name"]] = nested
            else:
                target[param["name"]] = value

        for param in out_params:
            process_output(param, data, result)
        
        return result

    def format_output(self, data: dict, out_params: List[dict]) -> str:
        output = []
        
        def format_recursive(params: List[dict], values: dict, indent: int):
            for param in params:
                if param["name"] not in values:
                    continue
                value = values[param["name"]]
                line = '  ' * indent + f'{param["caption"]}:'
                
                if DataType.value_of(param["data_type"]) == DataType.ARRAY_OBJECT:
                    output.append(line)
                    for idx, item in enumerate(value, 1):
                        output.append('')
                        if param["children"]:
                            format_recursive(param["children"], item, indent + 2)
                elif param["children"]:
                    output.append(line)
                    format_recursive(param["children"], value, indent + 1)
                else:
                    output.append(f'{line} {value}')

        format_recursive(out_params, data, 0)
        return '\n'.join(output)
    

    def do_http_request(self, in_params: list[dict], inputs_dict: dict):
        headers = {}
        data = {}
        params = {}

        def process_param(param: dict, context: dict) -> Any:
            """递归处理参数及其子参数"""
            # 获取参数值（优先从输入中获取，否则用默认值）
            param_value = context.get(param["name"])

            if param["default_value"]!="":
                param_value = param["default_value"]

            if param_value is None or param_value == "":
                if param["is_required"]:
                    raise ValueError(f"参数必须提供")
                else:
                    return None

            # 转换数据类型
            try:
                data_type = DataType.value_of(param["data_type"])
            except ValueError as e:
                raise ValueError(f"参数数据类型错误: {e}")

            # 类型转换逻辑
            try:
                if data_type == DataType.STRING:
                    return str(param_value) if param_value is not None else None
                elif data_type == DataType.INTEGER:
                    return int(param_value)
                elif data_type == DataType.NUMBER:
                    return float(param_value)
                elif data_type == DataType.BOOLEAN:
                    if isinstance(param_value, str):
                        return param_value.lower() in ["true", "1", "yes"]
                    return bool(param_value)
                elif data_type == DataType.OBJECT:
                    if not isinstance(param_value, dict):
                        raise ValueError("OBJECT类型需要字典格式")
                    obj = {}
                    for child in param["children"]:
                        obj[child["name"]] = process_param(child, param_value)
                    return obj
                elif data_type in (DataType.ARRAY_STRING, DataType.ARRAY_INTEGER,
                                DataType.ARRAY_NUMBER, DataType.ARRAY_BOOLEAN):
                    
                    if not isinstance(param_value, list):
                        param_value=ast.literal_eval(param_value)
                        param_value=[param_value] if not isinstance(param_value,list) else param_value
                    if not isinstance(param_value, list):
                        raise ValueError("ARRAY类型需要列表格式")
                    
                    # 获取数组元素类型
                    element_type = data_type.value.split("<")[1][:-1]
                    converted = []
                    for item in param_value:
                        if element_type == "String":
                            converted.append(str(item))
                        elif element_type == "Integer":
                            converted.append(int(item))
                        elif element_type == "Number":
                            converted.append(float(item))
                        elif element_type == "Boolean":
                            if isinstance(item, str):
                                converted.append(item.lower() in ["true", "1", "yes"])
                            else:
                                converted.append(bool(item))
                    return converted
                elif data_type == DataType.ARRAY_OBJECT:
                    if not isinstance(param_value, list):
                        raise ValueError("ARRAY_OBJECT需要列表格式")
                    arr = []
                    for item in param_value:
                        if not isinstance(item, dict):
                            raise ValueError("ARRAY_OBJECT元素需要字典格式")
                        obj = {}
                        for child in param["children"]:
                            obj[child["name"]] = process_param(child, item)
                        arr.append(obj)
                    return arr
                else:
                    return param_value
            except Exception as e:
                raise ValueError(f"参数值转换失败: {e}")

        # 遍历所有参数
        for param in in_params:
            try:
                value = process_param(param, inputs_dict)
            except ValueError as e:
                raise Exception(f"参数处理错误: {str(e)}")

            # 根据参数位置分配
            if param["param_way"] == "Header":
                headers[param["name"]] = value
            elif param["param_way"] == "Body":
                data[param["name"]] = value
            elif param["param_way"] == "Query":
                params[param["name"]] = value
            elif param["param_way"]=="Path":
                self.api_url=self.api_url.replace("{"+param["name"]+"}",value)
            else:
                raise ValueError(f"参数方式错误")

        # 发送请求
        try:
            response = requests.request(
                method=self.api_method.upper(),
                url=self.api_url,
                params=params,
                json=data if self.api_method.upper() != "GET" else None,
                headers=headers
            )
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP错误: {e.response.text}")
        except Exception as e:
            raise Exception(f"请求失败: {str(e)}")
        