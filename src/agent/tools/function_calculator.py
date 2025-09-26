import json
from src.agent.tools.function_base import FunctionBase
from src.agent.working.working_space import WorkingSpace
import numexpr as ne

class FunctionCalculator(FunctionBase):

    name="calculator"
    description="计算器工具，用于执行数学表达式。"
    params_description = 'calculator(expression="填写要计算的数学表达式")'


    def _run(self,space:WorkingSpace,options,*args, **kwargs):
        
        # 存储被替换的变量内容
        temp_data={}

        expression=self.get_required_params_value("expression",space,options,*args, **kwargs)
        temp_data["expression"]=expression

        result=ne.evaluate(expression).item()
        return result,temp_data
      

    def get_function_description(self,options) -> str:
        """获取工具描述"""

        if options.get("description"): #用户指定了工具描述
            return options["description"]
        return self.description

    def get_function_command_prompt(self,options) -> str:
        """获取工具的schema json"""
        params_commend=self.params_description
        if options.get("expression_desc"): 
            params_commend=params_commend.replace("填写要计算的数学表达式",options.get("expression_desc"))
        return params_commend
    

if __name__ == "__main__":
    python_ast_repl=FunctionCalculator()

    a2=python_ast_repl._run(None,{"expression":"1+2*3+5"})
    print(a2)

