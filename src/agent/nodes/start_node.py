from typing import List
from pydantic import TypeAdapter
from src.agent.nodes.base_node import BaseNode
from src.agent.model_types import DataType, InputVariable, NextNode, NodeRunResult, NodeType
from src.agent.working.working_graph import WorkingGraph


class StartNode(BaseNode):
    
    _node_type= NodeType.START

    def __init__(self,role_id:str, role:str,description:str,next_nodes:list[NextNode]=[],inputs:list[InputVariable]=[]):
        super().__init__(role_id,role,description,next_nodes)
        self.inputs = inputs
        self.inputs_variables_json={}
        self._convert_input_variables_json()

    @classmethod
    def from_dict(cls, data: dict):
        role_id=data.get("id","")
        role = data["role"]
        description = data["description"]
        inputs= []
        inputs_dict=data.get("inputs",None)
        if inputs_dict:
            adapter = TypeAdapter(List[InputVariable])
            inputs = adapter.validate_python(inputs_dict)

        next_nodes = []
        next_nodes_dict=data.get("next_nodes",None)
        if next_nodes_dict:
            adapter = TypeAdapter(List[NextNode])
            next_nodes = adapter.validate_python(next_nodes_dict)


        return cls(role_id=str(role_id),role=role,description=description, next_nodes=next_nodes, inputs=inputs)

    def _run(self, trigger: BaseNode, graph: WorkingGraph) -> NodeRunResult:
        
        #验证输入是否合法
        for input in self.inputs:

            if input.name not in graph.working_space.inputs:
                raise ValueError(f"space user_input中没有变量{input.name}")
            
            if input.is_required:
                var_value=graph.working_space.inputs.get(input.name,None)
                if var_value is None:
                    raise ValueError(f"输入变量{input.name}为空")
                
                
        return NodeRunResult()
    

    def _convert_object_fields(self, object_fields: List[InputVariable]) -> dict:
        """递归处理对象字段"""
        object_dict = {}
        for field in object_fields:
            name = field.name
            if field.data_type == DataType.OBJECT:
                if field.object_fields is None or len(field.object_fields) == 0:
                    raise ValueError(f"object variable {name} must have object_fields")
                object_dict[name] = self._convert_object_fields(field.object_fields)
            elif field.data_type == DataType.ARRAY_OBJECT:
                if field.object_fields is None or len(field.object_fields) == 0:
                    raise ValueError(f"array object variable {name} must have object_fields")
                object_dict[name] = [self._convert_object_fields(field.object_fields)]
            elif field.data_type==DataType.STRING or field.data_type==DataType.NUMBER or field.data_type==DataType.BOOLEAN or field.data_type==DataType.INTEGER:
                object_dict[name]=field.desc
            elif field.data_type==DataType.ARRAY_STRING or field.data_type==DataType.ARRAY_NUMBER or field.data_type==DataType.ARRAY_BOOLEAN or field.data_type==DataType.ARRAY_INTEGER:
                object_dict[name]=[field.desc]

        return object_dict
    
    def _convert_input_variables_json(self):
        """把输出变量转换为描述的字典"""
        for v in self.inputs:
            name=v.name
            #变量名去重
            if name in self.inputs_variables_json:
                raise KeyError(f"variable {name} already exist")
            if v.data_type==DataType.STRING or v.data_type==DataType.NUMBER or v.data_type==DataType.BOOLEAN or v.data_type==DataType.INTEGER:
                self.inputs_variables_json[name]=v.desc
            elif v.data_type==DataType.ARRAY_STRING or v.data_type==DataType.ARRAY_NUMBER or v.data_type==DataType.ARRAY_BOOLEAN or v.data_type==DataType.ARRAY_INTEGER:
                self.inputs_variables_json[name]=[v.desc]
            elif v.data_type==DataType.OBJECT:
                if v.object_fields is None or len(v.object_fields)==0:
                    raise ValueError(f"object variable {name} must have object_fields")
                self.inputs_variables_json[name] = self._convert_object_fields(v.object_fields)
            elif v.data_type==DataType.ARRAY_OBJECT:
                if v.object_fields is None or len(v.object_fields)==0:
                    raise ValueError(f"object variable {name} must have object_fields")
                self.inputs_variables_json[name] = [self._convert_object_fields(v.object_fields)]
            elif v.data_type==DataType.FILE:
                self.inputs_variables_json[name]=v.desc
            elif v.data_type==DataType.ARRAY_FILE:
                self.inputs_variables_json[name]=[v.desc]
            else:
                raise ValueError(f"variable {name} data_type {v.data_type} not support")