from src.agent.tools.function_base import FunctionBase
from src.agent.working.working_space import WorkingSpace
from src.database.models import TestCase

class FunctionUnitTestAdd(FunctionBase):

    name="unit_test_add"
    description="用于把指定的流程运行日志添加到单元测试中。"
    params_description = 'unit_test_add(&_Filter_&)'


    def _run(self,space:WorkingSpace,options,*args, **kwargs):
      
        # 存储被替换的变量内容
        temp_data={}

        unit_cate_id=self.get_required_params_value("unit_cate_id",space,options,*args, **kwargs)
        temp_data["unit_cate_id"]=unit_cate_id

        node_log_id=self.get_required_params_value("node_log_id",space,options,*args, **kwargs)
        temp_data["node_log_id"]=node_log_id

        test_note=self.get_nullable_params_value("test_note",space,options,*args, **kwargs)
        temp_data["test_note"]=test_note
        
        model = TestCase.case_add_unit(int(unit_cate_id), int(node_log_id),test_note)

        return {"result":"success"},temp_data

    def get_function_description(self,options) -> str:
        """获取工具描述"""
        if options.get("description"): #用户指定了工具描述
            return options["description"]
        return self.description


    def get_function_command_prompt(self,options) -> str:
        """获取工具的schema json"""
        params_commend=self.params_description
        # queries=["提取要查询的问题列表"],tags=["提取要查询的问题标签列表"],ids=["提取要查询的问题id列表"]
        filter_prompt=[]
        
        self.get_params_desc("unit_cate_id","填写要添加单元测试的指定分类id",filter_prompt,options)

        self.get_params_desc("node_log_id","填写要添加单元测试的节点日志id",filter_prompt,options)

        self.get_params_desc("test_note","填写测试备注信息",filter_prompt,options)

        filter_prompt_str=",".join(filter_prompt)

        params_commend=params_commend.replace("&_Filter_&",filter_prompt_str)
        return params_commend