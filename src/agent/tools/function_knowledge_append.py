from sqlalchemy import func
from src.agent.tools.function_base import FunctionBase
from src.agent.working.working_space import WorkingSpace
from src.database.models import KnowledgeDocument, KnowledgeDocumentMarkdown

class FunctionKnowledgeAppend(FunctionBase):

    name="knowledge_append"
    description="用于向知识库指定的文档中追加内容。"
    params_description = 'knowledge_append(&_Filter_&)'


    def _run(self,space:WorkingSpace,options,*args, **kwargs):
      
        # 存储被替换的变量内容
        temp_data={}

        doucument_id=self.get_required_params_value("doucument_id",space,options,*args, **kwargs)
        temp_data["doucument_id"]=doucument_id

        content=self.get_required_params_value("content",space,options,*args, **kwargs)
        temp_data["content"]=content
        
        KnowledgeDocument.append_markdown_content(id=int(doucument_id),append_content=content)

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
        
        self.get_params_desc("doucument_id","填写文档的id",filter_prompt,options)

        self.get_params_desc("content","填写要追加的知识内容",filter_prompt,options)

        filter_prompt_str=",".join(filter_prompt)

        params_commend=params_commend.replace("&_Filter_&",filter_prompt_str)
        return params_commend