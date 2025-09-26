

import datetime
import json
from typing import List
from jinja2 import Template, UndefinedError
from pydantic import TypeAdapter
from src.agent.nodes.base_node import BaseNode
from src.agent.model_types import FunctionCallLog, FunctionOption, NextNode, NodeRunResult, NodeType
from src.agent.working.working_graph import WorkingGraph


class ToolNode(BaseNode):
    
    _node_type=NodeType.TOOL

    def __init__(self,role_id:str, role:str,
                 description:str,
                 functions:list[FunctionOption]=[],
                 next_nodes:list[NextNode]=[]):
        super().__init__(role_id,role,description,next_nodes)
        self.functions:list[FunctionOption]=functions #工具

    
    @classmethod
    def from_dict(cls, data: dict):
        role_id=data.get("id","")
        role = data["role"]
        description = data["description"]
        functions=[]
        next_nodes=[]
        functions_dict = data.get("functions", None)
        if functions_dict:
            adapter = TypeAdapter(List[FunctionOption])
            functions = adapter.validate_python(functions_dict)
        next_nodes_dict=data.get("next_nodes",None)
        if next_nodes_dict:
            adapter = TypeAdapter(List[NextNode])
            next_nodes = adapter.validate_python(next_nodes_dict)

        return cls(role_id=str(role_id),
                   role=role,
                   description=description,
                   next_nodes=next_nodes, 
                   functions=functions) 


    def _run(self,trigger:'BaseNode',graph:WorkingGraph)->NodeRunResult:
        """执行 do something"""
        target_roles=[]
        function_calls=[]
        
        temp_data={}
        for f in self.functions:
            start_time = datetime.datetime.now()
            function_name = f.fun_name
            options=f.options
            args={}
            
            try:
                if not graph.working_space.has_function(function_name):
                    raise KeyError(f"function {f} not found")
                if self.loop_context is not None:
                    options["loop_context"]=self.loop_context
                return_value,temp_data= graph.working_space.call_function(name=function_name,options=options,**args)
                graph.working_space.write_role_output(self.role,return_value)

            except Exception as e:
                print(f"Error calling function {function_name}: {e}")
                return_value=f"工具错误：{e}"
                
            end_time = datetime.datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            call_log=FunctionCallLog(function_name=function_name,function_options=options,function_args=args,function_return=return_value,start_time=start_time,end_time=end_time,duration=duration)

            function_calls.append(call_log)

            prompt_str=json.dumps(temp_data,ensure_ascii=False,indent=2) if len(temp_data) else ""


        return NodeRunResult(target_roles=target_roles,prompt_str=prompt_str,response=None,function_calls=function_calls,prompt_temp="")
        