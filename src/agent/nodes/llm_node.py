import copy
from datetime import datetime
from typing import List
from concurrent.futures import ThreadPoolExecutor,as_completed
from src.agent.working.working_graph import WorkingGraph
from src.agent.working.working_space import FunctionCallLog
from src.agent.nodes.base_node import BaseNode
from src.agent.model_types import DataType, FunctionOption, NextNode, NodeRunResult, NodeSectionRunResult, NodeType, OutputVariable
import json
from pydantic import TypeAdapter
from src.database.db_session import on_request_end,set_current_request_id
from src.llm.llm_adapter import AdapterFactory
from src.llm.llm_helper import llm_vision_message, output_rules_parser_json
from src.llm.llm_models import HumanMessage

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

class LLMNode(BaseNode):
    
    _node_type=NodeType.LLM

    def __init__(self,role_id:str, role:str,
                 description:str,
                 llm_id:int,
                 prompt_template:str,
                 auto_compose_prompt:bool=True,
                 react:bool=False,
                 react_max_times:int=10,
                 auto_choice_node:bool=False,
                 choice_role_prompt:str='',
                 output_var_prompt:str='',
                 react_prompt_part_dict:dict={},
                 functions:list[FunctionOption]=[],
                 outputs:list[OutputVariable]=[],
                 next_nodes:list[NextNode]=[],
                 auto_section_run:bool=False,
                 use_vt:bool=False,
                 vt_file:str=''):
        
        super().__init__(role_id,role,description,next_nodes)
        self.llm_id=llm_id
        self.llm=AdapterFactory(llm_id).instance()
        self.llm_name=self.llm.name
        self.prompt_template=prompt_template
        self.prompt_str=None
        self.auto_compose_prompt=auto_compose_prompt #自动合成提示词
        self.auto_choice_node=auto_choice_node #是否自动选择节点
        self.choice_role_prompt=choice_role_prompt #自动选择节点的备注
        self.output_var_prompt=output_var_prompt #输出变量的备注
        self.react_prompt_part_dict=react_prompt_part_dict #推理提示词
        self.react=react #是否为反应节点  raAct推理，特别处理
        self.react_step="" #反应步骤
        # self.react_step_list=[] #反应步骤字典列表
        self.react_completion=False #是否完成反应
        self.react_max_times=react_max_times #反应次数
        self.react_times=0 #反应次数
        self.functions:list[FunctionOption]=functions #工具
        self.outputs:list[OutputVariable]=outputs #输出变量
        self._output_variables_json={}
        self._convert_output_variables_json()
        self.auto_section_run=auto_section_run #是否分身执行，会把prompt_template拆分成多个部分，每个部分并行执行
        self.use_vt=use_vt #是否开启视觉
        self.vt_file=vt_file #视觉文件，用于视觉模型的输入
        self.vision_file_str=None #视觉文件内容被替换后的内容
    
    @classmethod
    def from_dict(cls, data: dict):

        role_id=data.get("id","")
        role = data["role"]
        description = data["description"]
        llm_id =data["llm_id"]
        prompt_template = data["prompt_template"]
        auto_compose_prompt =True
        auto_choice_node = data["auto_choice_node"]
        react = data["react"]
        react_max_times = data["react_max_times"]
        choice_role_prompt=data.get("choice_role_prompt", '')
        output_var_prompt=data.get("output_var_prompt", '')
        use_vt=data.get("use_vt", False)
        vt_file=data.get("vt_file", '')
        react_prompt_part_dict={}
        try:
            react_part_prompt=data.get("react_part_prompt","")
            react_prompt_part_dict=json.loads(react_part_prompt if react_part_prompt!='' else '{}')
        except Exception as ex:
            raise ValueError(f"{role}参数react_part_prompt格式错误{ex}")
        functions=[]
        outputs=[]
        next_nodes=[]
        functions_dict = data.get("functions", None)
        if functions_dict:
            adapter = TypeAdapter(List[FunctionOption])
            functions = adapter.validate_python(functions_dict)
        outputs_dict = data.get("outputs", None)
        if outputs_dict:
            adapter = TypeAdapter(List[OutputVariable])
            outputs = adapter.validate_python(outputs_dict)
        next_nodes_dict=data.get("next_nodes",None)
        if next_nodes_dict:
            adapter = TypeAdapter(List[NextNode])
            next_nodes = adapter.validate_python(next_nodes_dict)

        auto_section_run = data.get("auto_section_run", False)

        return cls(role_id=str(role_id),
                   role=role,
                   description=description,
                   next_nodes=next_nodes, 
                   llm_id=llm_id, 
                   prompt_template=prompt_template, 
                   auto_compose_prompt=auto_compose_prompt, 
                   auto_choice_node=auto_choice_node,
                   choice_role_prompt=choice_role_prompt,
                   output_var_prompt=output_var_prompt,
                   react_prompt_part_dict=react_prompt_part_dict,
                   react=react, 
                   react_max_times=react_max_times, 
                   functions=functions, 
                   outputs=outputs,
                   auto_section_run=auto_section_run,
                   use_vt=use_vt,
                   vt_file=vt_file)

    def _check_functions(self,graph:WorkingGraph):
        """给节点绑定函数"""
        for f in self.functions:
            if not graph.working_space.has_function(f.fun_name):
                raise KeyError(f"{self.role}-function {f} not found")
    
    def _get_function_option(self,fun_name):
        """获取函数,配置项"""
        for f in self.functions:
            if f.fun_name==fun_name:
                return f.options

        raise KeyError(f"{self.role}-function {fun_name} not found")

    def _convert_object_fields(self, object_fields: List[OutputVariable]) -> dict:
        """递归处理对象字段"""
        object_dict = {}
        for field in object_fields:
            name = field.name
            if field.data_type == DataType.OBJECT:
                if field.object_fields is None or len(field.object_fields) == 0:
                    raise ValueError(f"{self.role}-object variable {name} must have object_fields")
                object_dict[name] = self._convert_object_fields(field.object_fields)
            elif field.data_type == DataType.ARRAY_OBJECT:
                if field.object_fields is None or len(field.object_fields) == 0:
                    raise ValueError(f"{self.role}-array object variable {name} must have object_fields")
                object_dict[name] = [self._convert_object_fields(field.object_fields)]
            elif field.data_type==DataType.STRING or field.data_type==DataType.NUMBER or field.data_type==DataType.BOOLEAN or field.data_type==DataType.INTEGER:
                object_dict[name]=field.desc
            elif field.data_type==DataType.ARRAY_STRING or field.data_type==DataType.ARRAY_NUMBER or field.data_type==DataType.ARRAY_BOOLEAN or field.data_type==DataType.ARRAY_INTEGER:
                object_dict[name]=[field.desc]

        return object_dict
    
    def _convert_output_variables_json(self):
        """给节点绑定输出变量"""
        for v in self.outputs:
            name=v.name
            #变量名去重
            if name in self._output_variables_json:
                raise KeyError(f"variable {name} already exist")
            if v.data_type==DataType.STRING or v.data_type==DataType.NUMBER or v.data_type==DataType.BOOLEAN or v.data_type==DataType.INTEGER:
                self._output_variables_json[name]=v.desc
            elif v.data_type==DataType.ARRAY_STRING or v.data_type==DataType.ARRAY_NUMBER or v.data_type==DataType.ARRAY_BOOLEAN or v.data_type==DataType.ARRAY_INTEGER:
                self._output_variables_json[name]=[v.desc]
            elif v.data_type==DataType.OBJECT:
                if v.object_fields is None or len(v.object_fields)==0:
                    raise ValueError(f"{self.role}-object variable {name} must have object_fields")
                self._output_variables_json[name] = self._convert_object_fields(v.object_fields)
            elif v.data_type==DataType.ARRAY_OBJECT:
                if v.object_fields is None or len(v.object_fields)==0:
                    raise ValueError(f"{self.role}-object variable {name} must have object_fields")
                self._output_variables_json[name] = [self._convert_object_fields(v.object_fields)]

    def _run(self,trigger:'BaseNode',graph:WorkingGraph)->NodeRunResult:
        """执行 do something"""
        target_roles=[]
        function_calls=[]
        tmep=self._compose_prompt(graph)
        self.prompt_str=self._replace_prompt(tmep,graph)
        section_results=[]
        #分身执行,React推理不可以分身
        if self.auto_section_run and not self.react and len(self._section_compose_prompt(graph))>1: 

            section_results=self._run_section(trigger,graph)
            response=None
            content=""
            for section_result in section_results:
                if section_result.response is not None:
                    content+=section_result.response.content+"\n\n"
                    if response is None:
                        response=copy.deepcopy(section_result.response)

            if response is not None:
                response.content=content
            self._handle_response(content,graph,target_roles,function_calls)
            return NodeRunResult(target_roles=target_roles,prompt_str=self.prompt_str,vision_file_str=self.vision_file_str,response=response,function_calls=function_calls,prompt_temp=tmep,section_results=section_results)
        
        else:
            start_time = datetime.now()
            response= self._ai_run(self.prompt_str,graph)
            self._handle_response(response.content,graph,target_roles,function_calls)
            end_time = datetime.now()
            if self.react and not self.react_completion:
                self.react_times+=1
                result = NodeSectionRunResult()
                result.start_time = start_time
                result.prompt_str =self.prompt_str
                result.prompt_temp=tmep
                result.section_name="第"+str(self.react_times)+"轮"
                result.end_time = end_time
                result.response=response
                section_results.append(result)
                response=self._run_react_setp(trigger=trigger,graph=graph,target_roles=target_roles,function_calls=function_calls,section_results=section_results)
                
            #表示已经完成推理react
            if self.react:
                self._clear_react_step()

            return NodeRunResult(target_roles=target_roles,prompt_str=self.prompt_str,vision_file_str=self.vision_file_str,response=response,function_calls=function_calls,prompt_temp=tmep,section_results=section_results)
        
    def _run_section(self,trigger:'BaseNode',graph:WorkingGraph):
        """并发执行多个分身内容"""
        section_results=[]
        prompts=self._section_compose_prompt(graph=graph)
        re_prompts=[(name,temp,self._replace_prompt(temp,graph)) for name,temp in prompts]

        def execute_ai_run(section_name:str,prompt_temp:str,prompt_str: str) -> NodeSectionRunResult:
            """执行 _ai_run 并捕获结果"""
            set_current_request_id()
            result = NodeSectionRunResult()
            result.start_time = datetime.now()
            result.prompt_str = prompt_str
            result.prompt_temp=prompt_temp
            result.section_name=section_name
            try:
                result.response = self._ai_run(prompt_str,graph)
            except Exception as e:
                # result.error = f"{self.role}-分身执行失败: {e}"
                self.runned_error=f"{self.role}-分身执行失败: {e}"
                # raise Exception(f"{self.role}-分身执行失败: {e}")
            finally:
                on_request_end()
            result.end_time = datetime.now()
            return result
        

        
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(execute_ai_run,section_name,prompt_temp,prompt_str) for section_name,prompt_temp,prompt_str in re_prompts}
            # 异常处理
            for future in as_completed(futures):
                result = future.result()  # 获取结果，如果任务抛出异常，这里会抛出
                section_results.append(result)
        return section_results
    
    def _run_react_setp(self,trigger:'BaseNode',graph:WorkingGraph,target_roles,function_calls,section_results):
        """执行react"""
        start_time = datetime.now()
        tmep=self._compose_prompt(graph)
        self.prompt_str=self._replace_prompt(tmep,graph)
        response= self._ai_run(self.prompt_str,graph)
        self._handle_response(response.content,graph,target_roles,function_calls)
        self.react_times+=1
        end_time = datetime.now()
        result = NodeSectionRunResult()
        result.start_time = start_time
        result.prompt_str =self.prompt_str
        result.prompt_temp=tmep
        result.section_name="第"+str(self.react_times)+"轮"
        result.end_time = end_time
        result.response=response
        if self.react_completion or self.react_times>self.react_max_times:
            return response
        section_results.append(result)
        return self._run_react_setp(trigger,graph,target_roles,function_calls,section_results)
        
    def _section_compose_prompt(self,graph:WorkingGraph)->str:
        """
        分身组装提示词
        由于大模型处理同时处理多项任务不可靠，因此把函数调用，选择角色，最终输出，分开处理，保证每一步的输出都是可靠的
        注意，先不考虑react的情况，react不做分身处理。react关闭自动选择下游。
        """
        temps=[]
        if self.auto_compose_prompt:
            if len(self.functions)>0:
                fun_temp=self.prompt_template
                fun_temp+="\n\n"
                fun_temp+=self.functions_prompt_template_options(graph)
                temps.append(("工具",fun_temp))
            if self.auto_choice_node and len(self.next_nodes)>1:
                choice_temp=self.prompt_template
                choice_temp+="\n\n"
                choice_temp+=self.roles_prompt_template_options(graph)
                temps.append(("角色",choice_temp))
            if len(self.outputs)>0:
                output_temp=self.prompt_template
                output_temp+="\n\n"
                output_temp+=self.output_prompt_template_options(graph)
                temps.append(("变量",output_temp))
        else:
            temps.append(self.prompt_template)
        return temps

    def _compose_prompt(self,graph:WorkingGraph)->str:
        """组装提示词"""
        temp=''
        if self.auto_compose_prompt:
            temp=self.prompt_template
            temp+="\n\n"
            temp+=self.functions_prompt_template_options(graph)
            temp+=self.output_prompt_template_options(graph)
            temp+=self.roles_prompt_template_options(graph)
            temp+=self.react_prompt_template_options(graph)
        else:
            temp=self.prompt_template
        return temp

    def _ai_run(self,prompt_str:str,graph:WorkingGraph):
        """调用大模型"""
        try:
            #视觉模型业务处理
            if self.use_vt and self.vt_file!='':
                self.vision_file_str=self._replace_prompt(self.vt_file,graph)
                human_message=llm_vision_message(self.vision_file_str,prompt_str)
                response=self.llm.generate([human_message])
                return response

            response=self.llm.generate([HumanMessage(content=prompt_str)])
            return response
        except Exception as e:
            raise Exception(f"{self.role}，大模型API失败:{e}")


    def functions_prompt_template_options(self,graph:WorkingGraph):
        """
        获取工具提示词选项
        可选工具列表：
        -----------------------
        vectorstore_retrieve | 用于查询店铺政策、产品知识、常见参数等的知识库查询工具。适用于一般性问题、多个产品比较类问题等。
        工具vectorstore_retrieve的使用方法：
        |<| vectorstore_retrieve(querys=["提取的查询问题列表"], brands="提取的查询问题的品牌") |>|
        替代```json
        {"type":"function_call","name":"vectorstore_retrieve","args":{"query":"填写行动输入"}}
        ```
        -----------------------
        """
        if len(self.functions)==0:
            return ''
        
        self._check_functions(graph)

        prompt=""
        for func in self.functions:
            func_name=func.fun_name
            prompt += f"{func_name} 工具介绍： {graph.working_space.get_function_description(func_name,func.options)}。\n"
            prompt += f"{func_name} 工具指令：command=|<|{graph.working_space.get_function_command_prompt(func_name, func.options)}|>|\n\n"
        prompt+='\n'
        return prompt
    
    def output_prompt_template_options(self,graph:WorkingGraph):
        """获取输出提示词选项"""
        prompt=''
        if len(self.outputs)==0:
            return prompt
        

        #验证输出变量是否在空间中存在
        for v in self.outputs:
            name=v.name
            if v.prefix=='space':
                if not graph.working_space.exist_var(name):
                    raise KeyError(f"{self.role}-variable {name} in space not found")
        variables_json= dict_to_formatted_string(self._output_variables_json)       
        if self.output_var_prompt!='':
            prompt+=self.output_var_prompt.format(variables_json=variables_json)+"\n\n"
        else:
            prompt="write_var 工具介绍：用于将答案/结果/输出内容存储到特殊的位置。\n "
            prompt+= f"write_var 工具指令：command=|<|write_var({variables_json})|>|\n\n"
            prompt+='\n'
        return prompt
    
    def roles_prompt_template_options(self,graph:WorkingGraph):
        """
        获取角色提示词选项
         
        可选角色列表：
        -----------------------
        role1:role1的介绍
        role2:role2的介绍
        
        这里写个备注，用于指导llm选择指引

        选择角色,必须规范输出以下格式```json：
        |<| assignment(next_role=["xxxx"],message="消息内容) |>| 
        替换掉```json
        {"toolname":"assignment","args":{"next_role":["xxxx"],"message":"xxxx"}}
        
        ```
        -----------------------
        """
        target_roles:list[BaseNode]=graph.get_downstream_nodes(self)
        if len(target_roles)>0:
            target_roles=[r for r in target_roles if self.get_next_run_max_times(r.role)>self.get_next_run_times(r.role)]
        
        prompt=''
        if len(target_roles)>1 and self.auto_choice_node:
            prompt+="可选角色列表：\n"
            prompt+="| 角色 | 角色职责 |\n"
            prompt+="|-|-|\n"
            role_names=[]
            for role in target_roles:
                prompt += f"| {role.role} | {role.description} |\n"
                role_names.append(role.role)
            prompt+="\n\n"
            if self.choice_role_prompt!='':
                prompt+=self.choice_role_prompt+"\n\n"
            else:
                prompt += f"assignment 工具介绍：用于从“可选角色列表”中筛选出适宜的角色，进行处理下一步任务。\n"
                prompt +=  'assignment 工具指令：command=|<|assignment(next_roles=[{"role":"填写选择的角色","message":"填写角色的任务内容"},\n{"role":"填写选择的角色","message":"填写角色的任务内容"}])|>|\n\n'
                # prompt += f'assignment 工具指令：command=|<|assignment(next_role=["填写筛查后的角色列表"],message="填写下一步任务")|>|\n\n'
                prompt+='\n'
        return prompt
                      
    def react_prompt_template_options(self,graph:WorkingGraph):
        """
        获取推理react提示词选项
        """
        if not self.react:
            return ""
        
        if prompt_step_part:=self.react_prompt_part_dict.get("prompt_step_part"):
            prompt=prompt_step_part.format(step=self.react_step)

        else:
            prompt="以下是推理过程：\n\n"
            prompt +=f"{self.react_step}\n\n"

        #表示最后一次执行推理，需要强制修改提示词结束推理
        if self.react_max_times-self.react_times<=1:
            if prompt_end_guide_part:=self.react_prompt_part_dict.get("prompt_end_guide_part"):
                prompt+=prompt_end_guide_part
            else:
                prompt +=f"请停止推理查询，使用以上信息回答问题，按照以下格式输出：\n"
                prompt +=f"【思考】：填写你分析的问题答案\n"
                prompt +=f'【工具指令】：填写最终回答工具指令，工具指令必须以"command=|<|"开始，以"|>|"结束\n'
        else:  
            if prompt_guide_part:=self.react_prompt_part_dict.get("prompt_guide_part"):
                prompt+=prompt_guide_part
            else:
                prompt +=f"分析以上信息并进行思考，按照以下格式输出：\n"
                prompt +=f"【思考】：填写你的分析过程\n"
                prompt +=f'【工具指令】：填写你使用的工具指令，工具指令必须以"command=|<|"开始，以"|>|"结束\n'
        return prompt

    def _set_react_setp(self,content:str,return_value:str):
        """设置react步骤"""
        #开启了reAct推理，需要拼接推理过程，并且循环自身
        prompt_think_part=self.react_prompt_part_dict.get("prompt_think_part")
        if prompt_think_part:
            self.react_step+=prompt_think_part.format(react_times=self.react_times+1,think=content,return_value=return_value)
        else:
            self.react_step+=f"第{self.react_times+1}轮推理过程：\n\n"
            self.react_step+=f"{content} \n"
            self.react_step+=f"【工具执行结果】：{return_value}\n\n"

        # result =f"【工具执行结果】：{return_value}" if return_value and return_value.strip()!='' else ""
        # self.react_step_list.append({"content":content,"result":result})

    def _set_react_compatible(self):
        """设置agent推理完成，不在执行react"""
        if self.react:
            self.react_completion=True
    
    def _clear_react_step(self):
        """清除react步骤"""
        self.react_step=''
        # self.react_step_list=[]
        self.react_completion=False
        self.react_times=0

    def _response_handling(self,content:str,graph:WorkingGraph,target_roles:list[str],function_calls:list[FunctionCallLog],instruction:dict,react_setp_return_values:list[str]):
        """并发出来响应指令"""
        set_current_request_id()
        data=instruction
        try:
            # 根据类型执行不同的操作
            toolname = data.get('toolname','')
            if toolname == 'write_var':
                # self._set_react_compatible()
                role_dict = {}
                # 变量赋值
                variables=data.get('args', {})
                for key,value in variables.items():
                    for v in self.outputs:
                        if v.name == key:
                            if v.prefix=='space':
                                graph.working_space.write_var(key,value)
                            else:
                                role_dict[key]=value
                            break
                if len(role_dict)>0:
                    graph.working_space.write_role_var(self.role,role_dict)
                
                # if self.react:
                #     react_setp_return_values.append("变量存储成功！")
                    
                print(f"变量赋值: {variables}")

            elif toolname == 'assignment':

                self._set_react_compatible()
                args = data.get('args', {})
                # 选择节点并跳转
                to_roles = args['next_roles']

                roles_set=set()
                for to_role in to_roles:
                    role=to_role.get("role",None)
                    message=to_role.get("message","")
                    if role is None:
                        raise ValueError(f"{self.role}-assignment role is None")
                    roles_set.add(role)
                    graph.working_space.add_talk(self.role,role,message)
                    # print(f"{self.role} to {role} assignment {message}")
                
                target_roles.extend(list(roles_set))  

                # message = args.get('message',None)
                # if message:
                #     for to_role in to_roles:
                #         graph.working_space.add_talk(self.role,to_role,message)

                # print(f"{self.role} to assignment :{to_roles},{message}")

            
            elif toolname == 'send_message':

                # self._set_react_compatible()
                args = data.get('args', {})
                # 选择节点并发送消息
                to_role = args.get('receiver',None)
                message = args.get('message',None)
                if to_role is None or to_role.strip()=='':
                    raise ValueError(f"{self.role}-send_message receiver is None")
                if message is None or message.strip()=='':
                    raise ValueError(f"{self.role}-send_message message is None")
                
                graph.working_space.add_talk(self.role,to_role,message)
                print(f"{self.role} to {to_role} :{message}")
            
            elif toolname == 'notify':

                # self._set_react_compatible()

                args = data.get('args', {})
                # 选择节点并发送消息
                to_role = args.get('receiver',"human")
                message = args.get('message',None)
                if message is None or message.strip()=='':
                    raise ValueError(f"{self.role}-notify message is None")
                graph.working_space.add_talk(self.role,to_role,message)
                print(f"{self.role} to {to_role} :{message}")

                #开启了reAct推理，需要拼接推理过程，并且循环自身
                # if self.react:
                #     react_setp_return_values.append("消息发送成功！")

            elif toolname == 'terminate':
                self._set_react_compatible()
                args=data.get('args', {})
                # 发送终止消息
                message = args['message']
                if isinstance(message,dict):
                    message = str(message)
                graph.working_space.add_talk(self.role,"human",message)
                
                self.set_termination(graph)

                print(f"{self.role} to terminate :{message}")


            elif toolname!='':
                # 执行函数调用
                function_name = toolname
                args = data.get('args', {})
                start_time =  datetime.now()
                #用户的选择的配置项
                options = None
                return_value = None
                try:
                    options=self._get_function_option(function_name)
                    if self.loop_context is not None:
                        options["loop_context"]=self.loop_context
                    return_value,temp_data= graph.working_space.call_function(name=function_name,options=options,**args)
                    graph.working_space.write_role_tool_output(self.role,function_name,return_value)

                except Exception as e:
                    print(f"Error calling function {function_name}: {e}")
                    return_value=f"工具错误：{e}"
                    graph.working_space.write_role_tool_output(self.role,function_name,None)
                    
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                    
                call_log=FunctionCallLog(function_name=function_name,function_options=options,function_args=args,function_return=return_value,start_time=start_time,end_time=end_time,duration=duration)

                function_calls.append(call_log)

                #开启了reAct推理，需要拼接推理过程，并且循环自身
                if self.react:
                    if isinstance(return_value,str):
                        react_setp_return_values.append(return_value)
                    else:
                        react_setp_return_values.append(str(return_value))
                    #下面这行代码当多个工具时会出现多个第n轮推理，需要挪到循环外部
                    # self._set_react_setp(content, return_value)
                print(f"调用函数: {function_name}，参数为: {args} ,返回内容: {return_value}")
            else:
                self._set_react_compatible()

                # graph.working_space.write_role_output(self.role,data)

                print(f"{self.role} output :{data}")
        except Exception as e:
            # raise ValueError(f"{self.role}:{content}[error:_handle_response {e}]")
            self.runned_error=f"{self.role}:{content}[error:_handle_response {e}]"
        finally:
            on_request_end()

    def _handle_response(self,content:str,graph:WorkingGraph,target_roles:list[str],function_calls:list[FunctionCallLog]):
        """
        处理大模型返回的response
        函数调用：|<| vectorstore_retrieve(querys=["提取的查询问题列表"], brands="提取的查询问题的品牌") |>|
        发送消息：|<| notify(receiver="human",message="xxxx") |>|
        选择下游处理人: |<| assignment(next_role=["下一步任务处理角色"],message="填写下一步做什么") |>|
        结束消息：|<| terminate(message="xxxx") |>|
        变量赋值：|<| write_var(key1="填写的问题",key2={"key":"填写标题","key":"填写内容"}) |>|
        """

        json_data = output_rules_parser_json(content)
        
        # 存储react步骤的返回值,一轮推理有可能调用多个/多次工具，每个工具的返回值按顺序存储
        react_setp_return_values=[]

        #并发的执行各种工具，加速处理速度
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(self._response_handling,content,graph,target_roles,function_calls,data,react_setp_return_values) for data in json_data}
            # 异常处理
            for future in as_completed(futures):
                try:
                    future.result()  # 获取结果，如果任务抛出异常，这里会抛出
                except Exception as e:
                    raise e

        # react 如果调用没有返回值的函数，则直接结束       
        if self.react and len(react_setp_return_values)==0:
            self._set_react_compatible()

        if self.react: #and len(react_setp_return_values)>0:
            self._set_react_setp(content, "\n\n".join(react_setp_return_values))
            #向工作空间写入react步骤
            # graph.working_space.write_role_react(self.role,self.react_step_list)

        if len(json_data)==0:
            self._set_react_compatible()
            print(f"{self.role} output :{content}")

        graph.working_space.write_role_output(self.role,content)
