from src.agent.tools.function_base import FunctionBase
from src.agent.working.working_space import WorkingSpace
from src.database.models import WorkFlowRunNodeLog
from src.utils.time_helper import parse_str_to_time
class FunctionFlowNodeLogs(FunctionBase):

    name="flow_node_logs"
    description="用于使用指定条件查询流程日志"
    params_description = 'flow_node_logs(&_Filter_&)'


    def _run(self,space:WorkingSpace,options,*args, **kwargs):
      
        # 存储被替换的变量内容
        temp_data={}

        flow_id=self.get_required_params_value("flow_id",space,options,*args, **kwargs)
        temp_data["flow_id"]=flow_id

        role_id=self.get_required_params_value("role_id",space,options,*args, **kwargs)
        temp_data["role_id"]=role_id
        
        start_time=self.get_required_params_value("start_time",space,options,*args, **kwargs)
        temp_data["start_time"]=start_time

        end_time=self.get_required_params_value("end_time",space,options,*args, **kwargs)
        temp_data["end_time"]=end_time

        max_top_n=self.get_required_params_value("max_top_n",space,options,*args, **kwargs)
        temp_data["max_top_n"]=max_top_n
   
        flow_id=int(flow_id)
        max_top_n=int(max_top_n)
        start_time = parse_str_to_time(start_time)
        end_time = parse_str_to_time(end_time)

        node_logs = []

        logs = WorkFlowRunNodeLog.query.filter(
                WorkFlowRunNodeLog.run_log.has(flow_id=flow_id),
                WorkFlowRunNodeLog.runner_id == role_id,
                WorkFlowRunNodeLog.start_time.between(start_time, end_time)).limit(max_top_n).all()

        for log in logs:
            if log.prompt_str is None or log.prompt_str == "" or log.response_content is None or log.response_content == "":
                continue
            log_dict = {
                "log_id":log.run_log_id,
                "node_log_id":log.id,
                "role_id": log.runner_id,
                "role": log.runner,            
                "input": log.prompt_str,
                "output": log.response_content,
            }
            node_logs.append(log_dict)
        return {"count": len(node_logs), "rows": node_logs},temp_data
        

    def get_function_description(self,options) -> str:
        """获取工具描述"""
        if options.get("description"): #用户指定了工具描述
            return options["description"]
        return self.description


    def get_function_command_prompt(self,options) -> str:
        """获取工具的schema json"""
        params_commend=self.params_description
        
        filter_prompt=[]

        self.get_params_desc("flow_id","填写流程id",filter_prompt,options)

        self.get_params_desc("role_id","填写节点角色id",filter_prompt,options)
        
        self.get_params_desc("start_time","填写日志起始日期，格式：yyyy-MM-dd hh:mm:ss",filter_prompt,options)

        self.get_params_desc("end_time","填写日志结束日期，格式：yyyy-MM-dd hh:mm:ss",filter_prompt,options)
        
        self.get_params_desc("max_top_n","填写最大返回的日志数量",filter_prompt,options)
        
        filter_prompt_str=",".join(filter_prompt)

        params_commend=params_commend.replace("&_Filter_&",filter_prompt_str)
        return params_commend