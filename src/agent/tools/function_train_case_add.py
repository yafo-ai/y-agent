from src.agent.tools.function_base import FunctionBase
from src.agent.working.working_space import WorkingSpace
from src.database.models import TrainCase, TrainCate, WorkFlowRunNodeLog

class FunctionTrainCaseAdd(FunctionBase):

    name="train_case_add"
    description="用于向指定训练分类中添加训练语料。"
    params_description = 'train_case_add(&_Filter_&)'


    def _run(self,space:WorkingSpace,options,*args, **kwargs):
      
        # 存储被替换的变量内容
        temp_data={}

        train_cate_id=self.get_required_params_value("train_cate_id",space,options,*args, **kwargs)
        temp_data["train_cate_id"]=train_cate_id

        input_content=self.get_required_params_value("input_content",space,options,*args, **kwargs)
        temp_data["input_content"]=input_content

        output_contet=self.get_required_params_value("output_contet",space,options,*args, **kwargs)
        temp_data["output_contet"]=output_contet
        
        feature=self.get_required_params_value("feature",space,options,*args, **kwargs)
        temp_data["feature"]=feature
        
        node_log_id=self.get_nullable_params_value("node_log_id",space,options,*args, **kwargs)
        temp_data["node_log_id"]=node_log_id
    
        test_case_id=self.get_nullable_params_value("test_case_id",space,options,*args, **kwargs)
        temp_data["test_case_id"]=test_case_id
    

        train_cate_id=int(train_cate_id)
        if train_cate_id==0:
            train_cate_id=None
        if train_cate_id:
            TrainCate.get(train_cate_id)
        if feature is None or feature.strip() == '':
            raise Exception('特征概要不能为空')
        workflow_id = None
        workflow_log_id = None

        if node_log_id is not None:
            is_exist, cate_name = TrainCase.is_exist_workflow_node_log(train_cate_id, int(node_log_id))
            if is_exist:
                raise Exception(f"在类别【{cate_name}】下已存在，不能重复添加")
            current_node = WorkFlowRunNodeLog.get(int(node_log_id))
            workflow_id = current_node.run_log.flow_id
            workflow_log_id = current_node.run_log.id
        train_case = TrainCase(train_cate_id=train_cate_id, input_data=input_content,output_data=output_contet)

        train_case.feature = feature
        train_case.test_case_id = int(test_case_id) if test_case_id else None
        train_case.workflow_node_log_id = int(node_log_id) if node_log_id else None
        train_case.workflow_id = workflow_id
        train_case.workflow_log_id = workflow_log_id
        train_case.is_marked = False
        train_case.is_modified = False
        train_case.add(True)
        
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

        self.get_params_desc("train_cate_id","填写要添加到训练的指定分类id",filter_prompt,options)
        
        self.get_params_desc("input_content","填写训练语料输入文本",filter_prompt,options)
        
        self.get_params_desc("output_contet","填写训练语料输出文本",filter_prompt,options)

        self.get_params_desc("feature","填写语料特征文本",filter_prompt,options)

        self.get_params_desc("node_log_id","填写要添加训练的关联节点日志id，非必填",filter_prompt,options)
        
        self.get_params_desc("test_case_id","填写要添加训练的关联的单元测试的Id，非必填",filter_prompt,options)


        filter_prompt_str=",".join(filter_prompt)

        params_commend=params_commend.replace("&_Filter_&",filter_prompt_str)
        return params_commend