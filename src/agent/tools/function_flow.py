
import datetime
import json
from typing import List
import uuid

from src.agent.tools.function_base import FunctionBase
from src.agent.working.working_space import WorkingSpace
from src.database.db_session import get_current_request
from src.database.enums import LogOrigin
from src.utils.json_helper import parse_nested_json


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

class FunctionFlow(FunctionBase):
    """
    流程工具类
    初始化需要：流程id，流程名称，流程描述，流程json    
    """
    def __init__(self,flow_id:int,flow_name:str,flow_desc:str,flow_json:str,use_log:bool):
        super().__init__()
        self.flow_id=flow_id
        self.flow_name=flow_name
        self.flow_desc=flow_desc
        self.flow_json=flow_json
        self.flow_dict=json.loads(flow_json)
        self.name=f"workflow_{flow_id}"
        self.description=flow_desc
        self.use_log=use_log



    def _run(self,space:WorkingSpace,options, *args, **kwargs):

        """
        从kwargs提取大模型参数
        从options提取用户指定的参数，并替换变量
        组装流程的是输入inputs
        """
        if space.config["workflow_id"]==self.flow_id:
            raise Exception("工具配置错误，不能调用自己")
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
        user_input = str(inputs_dict.get("user_input", None))
        if user_input is None or len(user_input) == 0:
            raise Exception("user_input输入参数不能为空")

        # 将嵌套的json字符串转换成字典
        inputs_dict = parse_nested_json(inputs_dict)

        from src.agent.working.working_manager import load_graph,run_graph
        print("FunctionFlow:",get_current_request())
        #来源继承父流程的来源
        workflow_source_id=space.config.get("workflow_source_id")
        workflow_source_name=space.config.get("workflow_source_name")
        graph = load_graph(self.flow_id,self.flow_json,workflow_source_id=workflow_source_id,workflow_source_name=workflow_source_name)
        result=run_graph(self.flow_id,self.flow_name,graph,inputs_dict,use_log=self.use_log)

        human_message=result.get("human_messages",None)
        mes=[message["message"] for message in human_message] if human_message is not None and len(human_message) > 0 else []

        #引用文章
        sub_citations=graph.working_space.citations
        space.append_doucuments(sub_citations) #添加引用文章
        space.append_citations(sub_citations) #添加引用文章
        
        res='/n'.join(mes) if len(mes) > 0 else "没有查询到相关内容！"
        
        return res,temp_data


    def get_function_description(self,options) -> str:
        """获取工具描述"""
        return self.description

    def get_function_command_prompt(self,options) -> str:
        """
        {"user_input": "","user_id": "123456","user_map":"{'user_id': '123456', 'user_name': '张三'}"}
        如果value是空着的，说明需要配置成大模型的输入
        flow_tool_(user_input="",user_id="",user_map={'user_id': '123123', 'user_name': '123'})
        """
        schemas_json={}
        input_dict =self._get_flow_inputs()
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
        
    
    def _get_flow_inputs(self)-> dict:
        """获取流程输入参数的介绍格式"""
        start_node_dict = [node for node in self.flow_dict.get('nodes') if node.get('type') == 'start'][0]
        from src.agent.nodes.start_node import StartNode
        start_node = StartNode.from_dict(start_node_dict)
        inputs_dict=start_node.inputs_variables_json
        return inputs_dict

    

