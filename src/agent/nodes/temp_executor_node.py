import json
from typing import List
from pydantic import TypeAdapter
from src.agent.nodes.base_node import BaseNode
from src.agent.model_types import NextNode, NodeRunResult, NodeType
from src.agent.working.working_graph import WorkingGraph
from json_repair import loads as repair_loads

from src.llm.llm_helper import output_rules_parser_json


class TempExecutorNode(BaseNode):
    
    _node_type=NodeType.TEMP_EXECUTOR

    def __init__(self,role_id:str, role:str,
                 description:str,
                 prompt_template:str,
                 next_nodes:list[NextNode]=[]):
        super().__init__(role_id,role,description,next_nodes)
        self.prompt_template = prompt_template
        self.prompt_str=None
    
    @classmethod
    def from_dict(cls, data: dict):
        role_id=data.get("id","")
        role = data["role"]
        description = data["description"]
        prompt_template = data["prompt_template"]
        next_nodes=[]
        next_nodes_dict=data.get("next_nodes",None)
        if next_nodes_dict:
            adapter = TypeAdapter(List[NextNode])
            next_nodes = adapter.validate_python(next_nodes_dict)

        return cls(role_id=str(role_id),
                   role=role,
                   description=description,
                   prompt_template=prompt_template,
                   next_nodes=next_nodes) 


    def _run(self,trigger:'BaseNode',graph:WorkingGraph)->NodeRunResult:
        """执行 do something"""
        target_roles = []
        self.prompt_str = self._replace_prompt(self.prompt_template, graph)
        tmp_message_json = output_rules_parser_json(self.prompt_str)
        # if tmp_message_json is None or len(tmp_message_json) == 0:
        #     raise ValueError(f'{self.role}-输出规则有错误，只支持工具函数write_var，terminate，notify')
        for data in tmp_message_json:
            self._handling_tools(graph, data,target_roles)

        graph.working_space.write_role_output(self.role,self.prompt_str)
        
        return NodeRunResult(target_roles=target_roles,prompt_str=self.prompt_str,response=None,function_calls=None,prompt_temp=self.prompt_template)

    def _handling_tools(self, graph: WorkingGraph, message_json: dict,target_roles:list[str]):
        """
        处理工具函数
        """
        tool_name = message_json.get('toolname', None)
        variables = message_json.get('args', {})
        if tool_name == 'write_var':
            for key, value in variables.items():
                if key in graph.working_space.variables:
                    graph.working_space.write_var(key,value)
                else:
                    raise ValueError(f'变量 {key} 在工作空间中不存在')
                
        elif tool_name == 'terminate':
            msg = self._output_msg_convert(variables.get('message', ''))
            graph.working_space.add_talk(self.role, "human", msg)
            self.set_termination(graph)
            print(f'{self.role} to terminate: {msg}')

        
        elif tool_name == 'send_message':
            to_role = variables.get('receiver',None)
            if to_role is None or to_role.strip()=='':
                raise ValueError(f"{self.role}-send_message receiver is None")
            msg = self._output_msg_convert(variables.get('message', ''))
            graph.working_space.add_talk(self.role, to_role, msg)
            print(f'{self.role} to {to_role}: {msg}')

        elif tool_name == 'notify':
            to_role = variables.get('receiver', 'human')
            msg = self._output_msg_convert(variables.get('message', ''))
            graph.working_space.add_talk(self.role, to_role, msg)
            print(f'{self.role} to {to_role}: {msg}')

        elif tool_name == 'assignment':
            # 选择节点并跳转
            to_roles = variables['next_roles']
            roles_set=set()
            for to_role in to_roles:
                role=to_role.get("role",None)
                message=self._output_msg_convert(to_role.get("message",""))
                if role is None:
                    raise ValueError(f"{self.role}-assignment role is None")
                roles_set.add(role)
                if message!="":
                    graph.working_space.add_talk(self.role,role,message)
            target_roles.extend(list(roles_set))
        else:
            raise ValueError(f'{self.role}-输出规则有错误，只支持工具函数write_var，terminate，notify')
            # graph.working_space.add_talk(self.role, "human", json.dumps(repair_loads(str(message_json)), ensure_ascii=False))

    def _output_msg_convert(self, message):
        try:
            if isinstance(message, dict) or isinstance(message, list):
                return json.dumps(message, ensure_ascii=False)
            if message.startswith('[{') or message.startswith('{'): 
                tmp_var = json.dumps(repair_loads(message), ensure_ascii=False)
                if tmp_var == '':
                    tmp_var = str(message)
            else:
                tmp_var = str(tmp_var)
        except Exception as e:
            tmp_var = str(message)
        return tmp_var
