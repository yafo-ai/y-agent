from typing import List
from src.agent.tools.function_base import FunctionBase
from src.agent.working.working_space import WorkingSpace
from src.rag.excel_vector_store import ExcelChromaVectorStore
import ast

class FunctionProductRetrieve(FunctionBase):

    name="product_retrieve"
    description="仅当问题中明确包含产品[id]并且是询问该商品的规格时，才使用此工具查询特定[id]商品的规格信息"
    # params_description = {"query":"提取的查询问题","nc_ids":["提取产品id列表"]}
    params_description = 'product_retrieve(querys=["提取的查询问题列表"],nc_ids=["提取产品id列表"])'


    def _run(self,space:WorkingSpace,options,*args, **kwargs):
        """
        工具执行函数，用于查询特定[id]商品的规格信息
        工具两用，一种是通过模型构造参数，参数在kwargs，另一种是作为工具节点用户配置options参数
        """
        
        temp_data={}

        querys=kwargs.get("querys")
        nc_ids=kwargs.get("nc_ids")
        
        if querys is None: #配置填写的模板或者默认值
            querys=options.get("querys")
            querys=self.template_render(space, querys,options)
            try:
                querys = ast.literal_eval(querys)
            except:
                querys = [querys]
        
        temp_data["querys"]=querys

        if nc_ids is None:
            nc_ids=options.get("nc_ids")
            nc_ids=self.template_render(space, nc_ids,options)
            try:
                nc_ids = ast.literal_eval(nc_ids)
            except:
                nc_ids = [nc_ids]

        temp_data["nc_ids"]=nc_ids
            
        if querys is None or nc_ids is None:
            raise ValueError("工具product_retrieve参数querys，nc_ids错误")

        excel_knowledge_base_ids=options.get("excel_knowledge_base_ids",[])
        excel_top_k=options.get("excel_top_k",0)

        # filter_value=self.options["filter_value"]
        output_option=options.get("output_option","json")

        db_excel=ExcelChromaVectorStore()
        docs=[]
        query=",".join(querys)
        if excel_knowledge_base_ids and len(excel_knowledge_base_ids)>0:
            for nc_id in nc_ids:
                nc_code=nc_id if isinstance(nc_id, str) else str(nc_id) #兼提取的参数类型错误
                doc_score_list=db_excel.similarity_search_with_score_titile_by_code(knowledgebase_ids=excel_knowledge_base_ids,relation_code=nc_code,query=query,top_k=excel_top_k)
                if len(doc_score_list)>0:
                    docs.extend(doc_score_list)

        
        # docs=list(filter(lambda x: x.metadata["score"] > filter_value, docs))
        # docs=(sorted(docs, key=lambda x: x.metadata["score"])[::-1][0:excel_top_k])
        docs=sorted(docs, key=lambda x: x.metadata["score"])[::-1]
   
        #引用存储
        space.append_doucuments(docs)
            

        if output_option=="json":
            jsons=[]
            for doc in docs:
                jsons.append({"id":doc.metadata["id"],"score":doc.metadata["score"],"title":doc.metadata["title"],"content":doc.page_content})
            return jsons,temp_data
        else:
            return "\n\n".join([item.page_content for item in docs]),temp_data

    def get_function_description(self,options) -> str:
        """获取工具描述"""

        if options.get("description"): #用户指定了工具描述
            return options["description"]
        return self.description

    def get_function_command_prompt(self,options) -> str:
        """获取工具的schema json"""
        params_commend=self.params_description
        if options.get("querys_desc"): #用户指定了querys描述
            params_commend=params_commend.replace("提取的查询问题列表",options.get("querys_desc"))
        if options.get("nc_ids_desc"): #用户指定了nc_ids_desc描述
            params_commend=params_commend.replace("提取产品id列表",options.get("nc_ids_desc"))
        return params_commend