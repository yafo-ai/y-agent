from collections import defaultdict
import copy
from typing import Any, Dict, List
from typing_extensions import TypedDict
from pydantic import BaseModel
import datetime
import threading
import uuid
import json


from src.agent.model_types import AgentRunLog, BaseEvent, ChatRoomMessage, FunctionCallLog, NodeSectionRunResult, NodeType, SendHumanMessageEvent, VariablesType
from src.agent.working.working_callback import WorkingCallback
class WorkingSpace():
    """代理运行时的工作空间，包含自定义数据，工具，系统日志等"""

    def __init__(self):
        self.config=defaultdict(dict) #存储各种运行时信息
        self.inputs:dict[str,Any]=defaultdict(dict) #用户输入
        self.memory:str #记忆信息
        self.variables=defaultdict(dict)
        self.documents:list=[] #文档
        self.citations:list=[] #最终引文
        self._agent_logs:list[AgentRunLog] = []
        self.role_output=defaultdict(dict)
        self.room_messages:list[ChatRoomMessage] = []
        from src.agent.tools.function_base import FunctionBase
        self._functions:Dict[str, 'FunctionBase'] = {}
        self.is_terminate=False
        self.callbacks:list[WorkingCallback]=None
        self.temp_catch:dict={}
        self._lock = threading.Lock() 

    def register_flow_function(self,flow_id,flow_name,flow_desc,flow_json,use_log):
        """注册一个函数，用于在代理运行时调用"""
        from src.agent.tools.function_flow import FunctionFlow
        func_instance = FunctionFlow(flow_id=flow_id,flow_name=flow_name,flow_desc=flow_desc,flow_json=flow_json,use_log=use_log)
        if func_instance.name == "":
            raise ValueError(f"自定义函数 {func_instance.__class__.__name__} 的 name 属性未设置")
        
        if func_instance.description == "":
            raise ValueError(f"自定义函数 {func_instance.name} 的 description 属性未设置")
        
        self._functions[func_instance.name] = func_instance 
    
    
    def register_plugin_function(self,tool_id:int,function_name:str,tool_name:str,tool_desc:str,api_url:str,api_method:str,in_params:str,out_params:str):
        """注册一个函数，用于在代理运行时调用"""
        from src.agent.tools.function_plugin import FunctionPluginTool
        func_instance = FunctionPluginTool(tool_id=tool_id,function_name=function_name,tool_name=tool_name,tool_desc=tool_desc,api_url=api_url,api_method=api_method,in_params=in_params,out_params=out_params)
        if func_instance.name == "":
            raise ValueError(f"自定义函数 {func_instance.__class__.__name__} 的 name 属性未设置")
        
        if func_instance.description == "":
            raise ValueError(f"自定义函数 {func_instance.name} 的 description 属性未设置")
        
        self._functions[func_instance.name] = func_instance 

    def register_mcp_function(self,provider_id:int,tool_name:str,tool_desc:str,server_url:str,in_params:str,out_params:str):
        """注册一个函数，用于在代理运行时调用"""
        from src.agent.tools.function_mcp import FunctionMCPTool
        func_instance = FunctionMCPTool(provider_id=provider_id,tool_name=tool_name,tool_desc=tool_desc,in_params=in_params,out_params=out_params)
        if func_instance.name == "":
            raise ValueError(f"MCP函数 {func_instance.__class__.__name__} 的 name 属性未设置")
        
        if func_instance.description == "":
            raise ValueError(f"MCP函数 {func_instance.name} 的 description 属性未设置")
        
        self._functions[func_instance.name] = func_instance 

    def register_function(self,func_class):
        """注册一个函数，用于在代理运行时调用"""
        from src.agent.tools.function_base import FunctionBase
        if issubclass(func_class, FunctionBase):
            func_instance = func_class()
            if func_instance.name == "":
                raise ValueError(f"自定义函数 {func_instance.__class__.__name__} 的 name 属性未设置")
            
            if func_instance.description == "":
                raise ValueError(f"自定义函数 {func_instance.name} 的 description 属性未设置")
            
            self._functions[func_instance.name] = func_instance 
        else:
            raise ValueError("提供的类必须继承自 BaseFunction")
        

    def has_function(self, name):
        """验证函数是否存在"""
        return name in self._functions
    
    def get_function_description(self, name,options):
        """
        通过函数名获取函数的实例。
        """
        return self._functions[name].get_function_description(options)
    
    def get_function_command_prompt(self, name, options):
        """
        通过函数名获取函数的schemas_json
        """
        return self._functions[name].get_function_command_prompt(options)
    
    def call_function(self,name,options, *args, **kwargs):
        """"调用自定义函数，用于在代理运行时调用"""
        func = self._functions[name]
        if func:
            # cloned_func = copy.deepcopy(func)
            return func.run(self,options,*args, **kwargs)
        else:
            raise ValueError(f"没有找到名为'{name}'的函数")
        

    def get_input(self,key:str):
        return self.inputs.get(key,None)
    
    def get_logs(self) -> List[AgentRunLog]:
        """获取所有日志"""
        return self._agent_logs
    
    def get_logs_by_role(self, role: str, cnt: int = None) -> List[AgentRunLog]:
        """获取指定runner的指定cnt条日志"""
        filtered_logs = [log for log in self._agent_logs if log.runner == role]
        if not filtered_logs:
            return None
        
        # 如果cnt是None或者大于日志列表长度，返回所有日志
        if cnt is None or cnt > len(filtered_logs):
            return filtered_logs
        
        # 否则，返回最后cnt条日志
        return filtered_logs[-cnt:]
    
    def _get_log_last(self, role: str) -> AgentRunLog:
        """获取role的最后一条日志"""
        filtered_logs = [log for log in self._agent_logs if log.runner == role]
        if not filtered_logs:
            return None
        return filtered_logs[-1]
    
    
        
    def add_log(self,
                 triggerer:str,
                 runner_type: NodeType,
                 runner:str,
                 runner_id:str,
                 parent_loop_node_id:str,
                 runner_run_times:int,
                 start_time:datetime.datetime,
                 end_time:datetime.datetime,
                 duration:float,
                 model_name:str|None,
                 prompt_temp:str|None,
                 prompt_str:str|None,
                 vision_file_str:str|None,
                 response:Any|None,
                 function_calls:list[FunctionCallLog]|None,
                 section_results:list[NodeSectionRunResult]|None):
        """添加日志"""

        if runner_type==NodeType.LOOP_START: # 如果是循环开始节点，则不添加日志
            return 
        
        role_variables=self.read_role_output(runner)

        with self._lock:
            pid = None
            if triggerer:
                last_log = self._get_log_last(triggerer)
                if last_log:
                    pid=last_log.id
            vars={}
            for key,value in self.variables.items():
                vars[key]=value["content"]
            
            is_section=section_results is not None and len(section_results)>0
            id=str(uuid.uuid4())

            log=AgentRunLog(id=id,
                            pid=pid,
                            triggerer=triggerer,
                            runner=runner,
                            runner_id=runner_id,
                            runner_type=runner_type.value,
                            parent_loop_node_id=parent_loop_node_id,
                            runner_run_times=runner_run_times,
                            start_time=start_time,
                            end_time=end_time,
                            duration=duration,
                            prompt_temp=prompt_temp,
                            prompt_str=prompt_str,
                            vision_file_str=vision_file_str,
                            response_content=response.content if response else None,
                            response_metadata=response.response_metadata if response else None,
                            function_calls=function_calls,
                            room_messages=copy.deepcopy(self.room_messages),
                            variables=copy.deepcopy(vars),
                            inputs=self.inputs,
                            role_variables=role_variables,
                            model_name=model_name,
                            tokens=response.total_tokens if response else None,
                            is_section=is_section,
                            is_section_sub=False
                            )
            
            #以下逻辑是用于处理将循环子节点，分身展示到循环节点         
            if parent_loop_node_id:#表示是循环的子节点
                self._temp_catch_data(parent_loop_node_id,log)
                return
            
            self._agent_logs.append(log)

            if runner_type==NodeType.LOOP:
                catch_data=self._get_temp_catch_data(runner_id)
                for item in catch_data:
                    item.pid=id
                    item.is_section=False
                    item.is_section_sub=True
                    log.is_section=True
                    self._agent_logs.append(item)
                self._temp_catch_clear(runner_id)

            #添加分身日志
            if is_section:
                for section in section_results:
                    self._agent_logs.append(AgentRunLog(id=str(uuid.uuid4()),
                                                pid=id,
                                                triggerer=triggerer,
                                                runner=runner+"-"+section.section_name,
                                                runner_id=runner_id,
                                                runner_type=runner_type.value,
                                                parent_loop_node_id=parent_loop_node_id,
                                                runner_run_times=runner_run_times,
                                                start_time=section.start_time,
                                                end_time=section.end_time,
                                                duration= (section.end_time - section.start_time).total_seconds(),
                                                prompt_temp=section.prompt_temp,
                                                prompt_str=section.prompt_str,
                                                vision_file_str=vision_file_str,
                                                response_content=section.response.content if section.response else section.error,
                                                response_metadata=section.response.response_metadata if section.response else None,
                                                function_calls=function_calls,
                                                room_messages=copy.deepcopy(self.room_messages),
                                                variables=copy.deepcopy(vars),
                                                inputs=self.inputs,
                                                role_variables=role_variables,
                                                model_name=model_name,
                                                tokens=section.response.total_tokens if section.response else None,
                                                is_section=False,
                                                is_section_sub=True
                                                ))

            


    
    def add_talk(self,_from:str,_to:str|None,_message:str):
        """添加聊天室消息"""
        with self._lock:
           id=str(uuid.uuid4())
           self.room_messages.append(ChatRoomMessage(id=id,from_role=_from,to_role=_to,message=_message,send_time=datetime.datetime.now()))
           if _to == "human":
               self.on_event(SendHumanMessageEvent(id=id,user_id=self.config["user_id"],pin_id=self.config["pin_id"],workflow_id=str(self.config["workflow_id"]),question_id=self.config["question_id"],node_role=_from,message=_message))

    def get_talks_to_dict(self,_from:str|None=None,_to:str|None=None,count:int|None=None):
        """获取聊天室消息，返回字典格式"""
        messages=self.get_talks(_from,_to,count)
        return [{"id":message.id,"sender":message.from_role,"receiver":message.to_role,"message":message.message,"time":message.send_time.strftime("%Y-%m-%d %H:%M:%S")} for message in messages]
    
    def get_talks(self,_from:str|None,_to:str|None,count:int|None=None):
        """获取聊天室消息，可选参数count指定获取消息的条数，默认获取最新的消息"""
        messages=[message for message in self.room_messages]
        if _from is not None and _from !="":
            messages=[message for message in messages if message.from_role==_from]
        if _to is not None and _to!="":
            messages=[message for message in messages if message.to_role==_to or message.to_role is None]
        if count is not None:
            messages=messages[-count:]
        return messages
    
    def get_talks_message(self,_from:str|None,_to:str|None,count:int|None=None):
        """获取指定用户的聊天室消息，可选参数count指定获取消息的条数，默认获取最新的消息"""
        messages=[message for message in self.room_messages]
        if _from is not None and _from !="":
            messages=[message for message in messages if message.from_role==_from]
        if _to is not None and _to!="":
            messages=[message for message in messages if message.to_role==_to or message.to_role is None]
        if count is not None:
            messages=messages[-count:]
        return [item.message for item in messages]


    def get_talks_from(self, _from: str, count=None):
        """获取来自指定用户的聊天室消息，可选参数count指定获取消息的条数，默认获取最新的消息"""
        messages = [message for message in self.room_messages if message.from_role == _from]
        return messages[-count:] if count is not None else messages
    
    def get_talks_to(self, _to: str, count=None):
        """获取发送给指定用户的聊天室消息，可选参数count指定获取消息的条数，默认获取最新的消息"""
        messages = [message for message in self.room_messages if message.to_role == _to or message.to_role is None]
        return messages[-count:] if count is not None else messages
        
    def get_talks_from_to(self, _from: str, _to: str, count=None):
        """获取来自指定用户且发送给指定用户的聊天室消息，可选参数count指定获取消息的条数，默认获取最新的消息"""
        messages = [message for message in self.room_messages if message.from_role == _from and (message.to_role == _to or message.to_role is None) ]
        return messages[-count:] if count is not None else messages

    
    def init_var(self,key:str,val_type:VariablesType):
        """向工作空间中初始化变量"""
        with self._lock:
            if key not in self.variables:
                if val_type == VariablesType.OVER_WRITE:
                    self.variables[key] = {'type': val_type.value, 'content': None}
                else:
                    self.variables[key] = {'type': val_type.value, 'content': []}
            else:
                raise ValueError(f"Variable {key} already exists")
        
    def write_var(self,key:str,value):
        """向工作空间变量写入值"""
        if value is None or value == '':
            return
        if isinstance(value,list) and len(value)==0:
            return
        with self._lock:
            if key not in self.variables:
                raise KeyError(f"Key '{key}' not found. Please initialize it first with init_variable method.")
            var_type = VariablesType.value_of(self.variables[key]['type'])
            if var_type == VariablesType.OVER_WRITE:
                self.variables[key]['content'] = value
            elif var_type == VariablesType.APPEND:
                if isinstance(value, list):
                    for item in value:
                        if item =="":
                            continue
                        self.variables[key]['content'].append(item)
                else:
                    if value !="":
                        self.variables[key]['content'].append(value)
            elif var_type == VariablesType.APPEND_UNIQUE:
                if isinstance(value, list):
                    for item in value:
                        if item=="":
                            continue
                        if item not in self.variables[key]['content']:
                            self.variables[key]['content'].append(item)
                else:
                    if value !="" and value not in self.variables[key]['content']:
                        self.variables[key]['content'].append(value)

    def read_var(self,key):
        """从工作空间中读取数据"""
        with self._lock:
            if key in self.variables:
                return self.variables[key]['content']
            else:
                raise KeyError(f"Key '{key}' not found. Please initialize it first with init_variable method.")
        
    def exist_var(self,key):
        """判断工作空间中是否存在key"""
        with self._lock:
            return key in self.variables

    def exist_role(self,role):
        """角色是否存在"""
        with self._lock:
            return role in self.role_output

    def write_role_var(self,role:str,content:any):
        """将角色自身变量写到到工作空间中"""
        with self._lock:
            self.role_output[role]["var"]=content

    def write_role_output(self,role:str,output):
        """将角色数据追加到工作空间中"""
        with self._lock:
            self.role_output[role]["output"]=output

    def write_role_tool_output(self,role:str,toolname,output):
        """将角色数据追加到工作空间中"""
        with self._lock:
            self.role_output[role][toolname]=output

    def write_role_react(self,role:str,react):
        """将角色推理过程追加到工作空间中"""
        with self._lock:
            self.role_output[role]["react"]=react
    
    def read_role_output(self,role:str):
        """获取角色数据"""
        with self._lock:
            return self.role_output.get(role,None)
    def get_roles_output(self,roles:list[str],field_key:str|None=None):
        """获取多个加色输出数据"""
        with self._lock:
            outputs=[]
            for role in roles:
                if role_output:=self.role_output.get(role,None):
                    if output:=role_output.get("output",None):
                        if field_key:
                            field_keys=field_key.split(".")
                            for key in field_keys:
                                if not isinstance(output,dict):
                                    output=None
                                    break;
                                output=output.get(key,None)
                        if output is None:
                            continue
                        if isinstance(output,list):
                            outputs.extend(output)
                        else:
                            outputs.append(output)
            return outputs
        
    def append_doucuments(self, documents:list):
        """向工作空间中添加文档
           documents=[{"id":doc.metadata["id"],"score":doc.metadata["score"],"title":doc.metadata["title"],"content":doc.page_content,"detali_url":doc.metadata["detali_url"],"type":doc.metadata["type"],"filename":doc.metadata["filename"]} for doc in docs]
        """
        with self._lock:
            existing_ids = {item.metadata["id"] for item in self.documents} 
            for document in documents:
                if document.metadata["id"] not in existing_ids:
                    self.documents.append(document)
                    existing_ids.add(document.metadata["id"])

                    
    def append_citations(self, documents:list):
        """向工作空间中添加引文
           documents=[{"id":doc.metadata["id"],"score":doc.metadata["score"],"title":doc.metadata["title"],"content":doc.page_content,"detali_url":doc.metadata["detali_url"],"type":doc.metadata["type"],"filename":doc.metadata["filename"]} for doc in docs]
        """
        with self._lock:
            existing_ids = {item.metadata["id"] for item in self.citations} 
            for document in documents:
                if document.metadata["id"] not in existing_ids:
                    self.citations.append(document)
                    existing_ids.add(document.metadata["id"])


    def get_document(self,ids:list[str]):
        """获取知识库,并存储引用"""
        with self._lock:
            ids_to_keep = set(ids)
            this_citations = [citation for citation in self.documents if citation.metadata["id"] in ids_to_keep]
            existing_ids = {item.metadata["id"] for item in self.citations}
            save_citations = [citation for citation in this_citations if citation.metadata["id"] not in existing_ids]
            if save_citations and len(save_citations) > 0:
                self.citations.extend(save_citations)
            docs = [doc.page_content for doc in this_citations]
            return "\n\n".join(docs)
        
    def get_document_list(self,ids:list[str]):
        """获取知识库,并存储引用"""
        with self._lock:
            ids_to_keep = set(ids)
            this_citations = [citation for citation in self.documents if citation.metadata["id"] in ids_to_keep]
            existing_ids = {item.metadata["id"] for item in self.citations}
            save_citations = [citation for citation in this_citations if citation.metadata["id"] not in existing_ids]
            if save_citations and len(save_citations) > 0:
                self.citations.extend(save_citations)
            docs = [{"id":doc.metadata["id"],"score":doc.metadata["score"],"title":doc.metadata["title"],"content":doc.page_content} for doc in this_citations]
            return docs
    def on_event(self, event:BaseEvent):
        """发生事件"""
        if self.callbacks:
            for callback in self.callbacks:
                callback.on_event(event=event)
        
    def _temp_catch_data(self,id,data):
        """用户缓存临时数据"""
        if self.temp_catch.get(id):
            self.temp_catch[id].append(data)
        else:
            self.temp_catch[id]=[data]
    def _get_temp_catch_data(self,id):
        return self.temp_catch.get(id,[])

    def _temp_catch_clear(self,id):
        if self.temp_catch.get(id):
            del self.temp_catch[id]

    def system_data(self) -> str:
        """获取当前时间 日期 YYYY-MM-DD"""
        return datetime.datetime.now().date().strftime("%Y-%m-%d")

    def system_datetime(self) -> str:
        """获取当前时间 日期时间 YYYY-MM-DD HH:MM:SS"""
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def system_time(self) -> str:
        """获取当前时间"""
        return datetime.datetime.now().time().strftime("%H:%M:%S")
    
    def is_null_or_empty(self,value:any):
        
        from jinja2 import Undefined
        from src.agent.template.undefined import TempUndefined
        """判断是否为空"""
        if value is None:
            return True
        if isinstance(value, Undefined):
            return True
        if isinstance(value,TempUndefined):
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        if isinstance(value, list) and len(value) == 0:
            return True
        if isinstance(value, dict) and len(value) == 0:
            return True
        return False
    
    def custome_contains(self,value:str,target:str):
        """自定义包含判断"""
        if value is None or target is None:
            return False
        if value == '' or target == '':
            return False
        if target in value:
            return True
        return False