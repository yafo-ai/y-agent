

import ast
from typing import List
from jinja2 import Template
from pydantic import TypeAdapter
from src.agent.model_types import NextNode, NodeRunResult, NodeType
from src.agent.nodes.base_node import BaseNode
from src.agent.working.working_graph import WorkingGraph
from src.database.db_session import on_request_end, set_current_request_id



class LoopNode(BaseNode):
    """这是一个循环节点，用于循环执行子节点"""

    _node_type= NodeType.LOOP

    def __init__(self,role_id:str, role:str,description:str,loop_traget:str,loop_size:int,max_workers:int,sub_nodes:list[dict],next_nodes:list[NextNode]=[]):
        super().__init__(role_id,role,description,next_nodes)
        #循环数据目标
        self.loop_traget=loop_traget
        #每几个循环一次
        self.loop_size=loop_size
        #循环子节点
        self.sub_nodes=sub_nodes
        #最大并发线程数
        self.max_workers=max_workers

    @classmethod
    def from_dict(cls, data: dict):

        role_id=data.get("id","")
        role = data["role"]
        description = data["description"]
        loop_traget=data["loop_traget"]
        loop_size=data["loop_size"]
        sub_nodes=data["sub_nodes"]
        max_workers=data.get("max_workers",64)
        next_nodes=[]
        next_nodes_dict=data.get("next_nodes",None)
        if next_nodes_dict:
            adapter = TypeAdapter(List[NextNode])
            next_nodes = adapter.validate_python(next_nodes_dict)

        return cls(role_id=str(role_id),
                   role=role,
                   description=description,
                   loop_traget=loop_traget,
                   loop_size=loop_size,
                   max_workers=max_workers,
                   sub_nodes=sub_nodes,
                   next_nodes=next_nodes) 


    def _run(self,trigger:'BaseNode',graph:WorkingGraph)->NodeRunResult:
        """执行节点，处理分批循环"""
        loop_data=ast.literal_eval(self._replace_prompt(self.loop_traget,graph))
        if loop_data is None:
            return NodeRunResult()
        
        if not isinstance(loop_data,list):
            raise ValueError(f"{self.role}拆分循环目标数据错误")
    
        if not self.loop_size>0:
            raise ValueError(f"{self.role}拆分循环批次大小错误")
        
        if not self.max_workers>0:
            raise ValueError(f"{self.role}并发数必须大于0")
        
        if len(loop_data)==0:
            return NodeRunResult()
       

        #注意分批后，每给批次还是一个列表
        batches: List[List] = [loop_data[i:i + self.loop_size] for i in range(0, len(loop_data), self.loop_size)]

        import concurrent.futures
        from concurrent.futures import ThreadPoolExecutor
        def run_loop_graph(index, batch):
            """执行循环"""
            set_current_request_id()
            try:
                loop_context = {"index": index, "item": batch}
                from src.agent.working.working_manager import load_sub_loop_graph
                loop_graph = load_sub_loop_graph(graph, self.sub_nodes,index)
                try:
                    loop_graph.run_sub_loop(self.role_id, loop_context)
                except Exception as e:
                    self.runned_error=f"{self.role}[第{index}批]错误:{e}"
                #取一次循环所有节点的ouput
                outputs={"index":index}
                for node in loop_graph.V:
                    if node._node_type==NodeType.LOOP_START:
                        continue
                    role_output=loop_graph.working_space.read_role_output(node.role)
                    if role_output is None:
                        continue
                    output=role_output.get("output","")
                    key=node.role.replace(f"_batch_{index}","")
                    outputs[key]=output
                return outputs
            except Exception as e:
                raise Exception(f"{e}")
            finally:
                on_request_end()
            

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(run_loop_graph, index, batch) for index, batch in enumerate(batches)]
            all_results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()  # 获取结果
                    all_results.append(result)  # 收集结果
                except Exception as e:
                    raise Exception(f"{self.role}循环执行错误:{e}")
                
        graph.working_space.write_role_output(self.role,all_results)
        
        return NodeRunResult()

        


