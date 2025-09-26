from typing import List
from pydantic import TypeAdapter
from src.agent.nodes.base_node import BaseNode
from src.agent.model_types import NextNode, NodeRunResult, NodeType
from src.agent.working.working_graph import WorkingGraph


class LoopStartNode(BaseNode):
    
    _node_type= NodeType.LOOP_START

    def __init__(self,role_id:str, role:str,description:str,next_nodes:list[NextNode]=[]):
        super().__init__(role_id,role,description,next_nodes)

    @classmethod
    def from_dict(cls, data: dict):
        role_id=data.get("id","")
        role = data["role"]
        description = data["description"]
        next_nodes = []
        next_nodes_dict=data.get("next_nodes",None)
        if next_nodes_dict:
            adapter = TypeAdapter(List[NextNode])
            next_nodes = adapter.validate_python(next_nodes_dict)

        return cls(role_id=str(role_id),role=role,description=description, next_nodes=next_nodes)

    def _run(self, trigger: BaseNode, graph: WorkingGraph) -> NodeRunResult:
        
        return NodeRunResult()
    


    