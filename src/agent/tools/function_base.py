from abc import ABC, abstractmethod
from typing import Any, Dict
from jinja2 import UndefinedError
from src.agent.template.undefined import TempUndefined, is_empty, is_not_empty
from src.agent.working.working_space import WorkingSpace
from src.agent.template.agent_environment import AgentEnvironment
import ast

class FunctionBase(ABC):

    name=""  # 类属性，用于存储函数的名称
    description = ""  # 类属性，用于存储函数的描述
    params_description = ''  # 类属性，用于存储参数的说明


    @abstractmethod
    def _run(self,space,options, *args, **kwargs):
        raise NotImplementedError("子类必须实现 execute 方法")
    
    def run(self,space:WorkingSpace,options:Dict[str, Any], *args, **kwargs):

        try:
            return self._run(space,options,*args, **kwargs)
        except Exception as e:
            raise Exception(f"函数{self.name}执行失败,请检查函数配置,{e}")
        
    @abstractmethod
    def get_function_description(self,options) -> str:
        raise NotImplementedError("子类必须实现 get_function_description 方法")

    @abstractmethod
    def get_function_command_prompt(self,options) -> str:
        """
        返回LLM调用函数时输出的自定义json格式字符串
        如：{"toolname":"toolname","args":{"query":"填写行动输入"}}
        """
        raise NotImplementedError("子类必须实现 get_function_command_prompt 方法")

    def get_required_array_params_value(self,key:str,space:WorkingSpace,options:Dict[str, Any],*args, **kwargs)->list:
        """
        获取必填参数的数组值
        """
        value=options.get(key)
        if value is None or value=="":
            value=kwargs.get(key)

        if value is None or value=="":
            raise ValueError(f"工具{self.name}参数{key}错误")
        
        if isinstance(value,list):
            return value

        if "{{" in value or '{%' in value:
            value=self.template_render(space, value,options)

        try:
            value = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            value = [value]

        return value
    
    def get_nullable_array_params_value(self,key:str,space:WorkingSpace,options:Dict[str, Any],*args, **kwargs)->list:
        """
        获取必填参数的数组值
        """
        value=options.get(key)
        if value is None or value=="":
            value=kwargs.get(key)

        if isinstance(value,list):
            return value

        if value is not None and value!="":
            if "{{" in value or '{%' in value:
                value=self.template_render(space, value,options)

        if value is None or value=="":
            return []
        
        try:
            value = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            value = [value]

        return value

    def get_required_params_value(self,key:str,space:WorkingSpace,options:Dict[str, Any],*args, **kwargs)->str:
        """
        获取必填参数的值
        """
        value=options.get(key)
        if value is None or value=="":
            value=kwargs.get(key)

        if value is None or value=="":
            raise ValueError(f"工具{self.name}参数{key}错误")

        if "{{" in value or '{%' in value:
            value=self.template_render(space, value,options)

        return value
    
    def get_nullable_params_value(self,key:str,space:WorkingSpace,options:Dict[str, Any],*args, **kwargs):
        """
        获取必填参数的值
        """
        value=options.get(key)
        if value is None or value=="":
            value=kwargs.get(key)

        if value is not None and value!="":
            if "{{" in value or '{%' in value:
                value=self.template_render(space, value,options)

        return value
    
    def get_params_desc(self,key:str,default:str,res:list[str],options:Dict[str, Any]):
        """获取工具参数的说明"""
        if options.get(key) is None or options.get(key)=="":
            if options.get(f"{key}_desc") and options.get(f"{key}_desc")!="": 
                res.append(f'{key}="{options.get(f"{key}_desc")}"')
            else:
                res.append('{key}="{default}"')
    def get_array_params_desc(self,key:str,default:str,res:list[str],options:Dict[str, Any]):
        """获取工具参数的说明"""
        if options.get(key) is None or options.get(key)=="":
            if options.get(f"{key}_desc") and options.get(f"{key}_desc")!="": 
                res.append(f'{key}=["{options.get(f"{key}_desc")}"]')
            else:
                res.append('{key}=["{default}"]')
                

    def template_render(self, space: WorkingSpace, template_str: str, options):
        """配置输入变量替换"""

        try:
            env = AgentEnvironment(undefined=TempUndefined)  # 使用自定义的Undefined类
            env.tests["empty"] = is_empty  # 注册empty测试器
            env.tests["not_empty"] = is_not_empty
            j2_template = env.from_string(template_str)

            context = {"sys": {}}
            context["sys"]["time"] = space.system_time
            context["sys"]["date"] = space.system_data
            context["sys"]["datetime"] = space.system_datetime
            context["sys"]["contains"]=space.custome_contains
            context['sys']["space"] = {}
            variables_snapshot = space.variables.copy()
            for key, value in variables_snapshot.items():
                context['sys']["space"][key] = value["content"]

            context["sys"]["get_documents_text"] = space.get_document
            context["sys"]["get_documents_json"] = space.get_document_list

            context["sys"]['chat_room'] = {}
            context["sys"]['chat_room']['get_talks'] = space.get_talks_to_dict
            context["sys"]["current_token"] = space.config.get("current_token")
            context["sys"]["is_null_or_empty"]=space.is_null_or_empty

            context["role"] = {}
            context['role']["开始"] = space.inputs
            context['role']["input"] = space.inputs

            context["role"]["get_roles_outputs"] = space.get_roles_output
            context["role"]["exist"] = space.exist_role

            role_output_snapshot = space.role_output.copy()
            for key, value in role_output_snapshot.items():
                context["role"][key] = value

                if loop_context := options.get("loop_context", None):
                    # 还原循环变量中的节点变量名称。在循环内部，去掉后缀表示当前一次循环的节点
                    suffix = f"_batch_{loop_context.get('index')}"
                    if key.endswith(suffix):
                        context["role"][key.replace(suffix, "")] = value

            if loop_context := options.get("loop_context", None):
                context["loop"] = loop_context 
                context["batch"] = loop_context

            return j2_template.render(**context)

        except UndefinedError as e:
            raise ValueError(f"Prompt模板渲染失败,变量未定义：{e}")
        except Exception as e:
            raise ValueError(f"Prompt模板渲染失败，未知错误：{e}")
    
    