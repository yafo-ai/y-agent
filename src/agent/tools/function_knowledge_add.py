from sqlalchemy import func
from src.agent.tools.function_base import FunctionBase
from src.agent.working.working_space import WorkingSpace
from src.database.models import Category, KnowledgeBase, KnowledgeDocument, KnowledgeDocumentMarkdown

class FunctionKnowledgeAdd(FunctionBase):

    name="knowledge_add"
    description="用于向指定的知识库指定的分类中添加一份独立的知识文档。"
    params_description = 'knowledge_add(&_Filter_&)'


    def _run(self,space:WorkingSpace,options,*args, **kwargs):
      
        # 存储被替换的变量内容
        temp_data={}

        knowledgebase_id=self.get_required_params_value("knowledgebase_id",space,options,*args, **kwargs)
        temp_data["knowledgebase_id"]=knowledgebase_id

        category_id=self.get_nullable_params_value("category_id",space,options,*args, **kwargs)
        temp_data["category_id"]=category_id
        
        title=self.get_required_params_value("title",space,options,*args, **kwargs)
        temp_data["title"]=title

        content=self.get_required_params_value("content",space,options,*args, **kwargs)
        temp_data["content"]=content


        if category_id and category_id!="":
            category_id=int(category_id)
        else:
            category_id=None

        KnowledgeDocument.create_document(knowledgebase_id=int(knowledgebase_id),name=title,content=content,category_id=category_id)

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

        self.get_params_desc("knowledgebase_id","填写文档所属知识库id",filter_prompt,options)

        self.get_params_desc("category_id","填写文档所属分类id",filter_prompt,options)

        self.get_params_desc("title","填写文档的标题",filter_prompt,options)

        self.get_params_desc("content","填写文档的内容",filter_prompt,options)

    
        filter_prompt_str=",".join(filter_prompt)

        params_commend=params_commend.replace("&_Filter_&",filter_prompt_str)
        return params_commend