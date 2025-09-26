import ast
from typing import List
from src.agent.tools.function_base import FunctionBase
from src.agent.working.working_space import WorkingSpace
from src.rag.excel_vector_store import ExcelChromaVectorStore
from src.database.models import KnowledgeBase
from src.rag.knowledge_vector_store import KnowledgeChromaVectorStore

class FunctionVectorstoreRetrieve(FunctionBase):

    name="vectorstore_retrieve"
    description="用于查询店铺政策、产品知识、常见参数等的知识库查询工具。适用于一般性问题、多个产品比较类问题等"
    # params_description = {"querys":["提取的查询问题列表"],"brands":["提取的查询问题的品牌"]}
    params_description = 'vectorstore_retrieve(querys=["提取的查询问题列表"],brands=["提取的查询问题的品牌"])'

    def _run(self,space:WorkingSpace,options,*args, **kwargs):
      
        temp_data={}
        
        querys=kwargs.get("querys")
        brands=kwargs.get("brands")
        
        if querys is None: #配置填写的模板或者默认值
            querys=options.get("querys")
            querys=self.template_render(space, querys,options)
            try:
                querys = ast.literal_eval(querys)
            except:
                querys = [querys]
                
        temp_data["querys"]=querys
        
        if brands is None:
            brands=options.get("brands")
            brands=self.template_render(space, brands,options)
            try:
                if brands is None or brands=="":
                    brands=[]
                else:
                    brands = ast.literal_eval(brands)
            except:
                brands = [brands]
        temp_data["brands"]=brands
        
        if querys is None:
            raise ValueError("工具vectorstore_retrieve参数querys错误")
        

        product_knowledge_base_ids=options.get("product_knowledge_base_ids",[])
        product_top_k=options.get("product_top_k",0)

        doc_knowledge_base_ids=options.get("doc_knowledge_base_ids",[])
        doc_top_k=options.get("doc_top_k",0)

        excel_knowledge_base_ids=options.get("excel_knowledge_base_ids",[])
        excel_top_k=options.get("excel_top_k",0)

        filter_value=options.get("filter_value",0)
        output_option=options.get("output_option","json")

        knowledgebase_ids_filter=[]
        product_knowledgebase_ids_filter=[]
        file_knowledgebase_ids_filter=[]

        max_count=product_top_k+doc_top_k+excel_top_k
        #用品牌过滤知识库
        if brands and len(brands)>0:
            lable_maps=KnowledgeBase.get_label_dict(None)

            for id in doc_knowledge_base_ids:
                brand=lable_maps.get(id,"")
                if brand=="" or brand is None or brand in brands:
                    knowledgebase_ids_filter.append(id)
            doc_knowledge_base_ids=knowledgebase_ids_filter

            for id in product_knowledge_base_ids:
                brand=lable_maps.get(id,"")
                if brand=="" or brand is None or brand in brands:
                    product_knowledgebase_ids_filter.append(id)
            product_knowledge_base_ids=product_knowledgebase_ids_filter

            for id in excel_knowledge_base_ids:
                brand=lable_maps.get(id,"")
                if brand=="" or brand is None or brand in brands:
                    file_knowledgebase_ids_filter.append(id)
            excel_knowledge_base_ids=file_knowledgebase_ids_filter

        
        db_excel=ExcelChromaVectorStore()
        db_knowledge=KnowledgeChromaVectorStore()  
        docs=[]

        for query in querys:
            if len(product_knowledge_base_ids)>0 and product_top_k>0:
                doc_score_list=db_knowledge.similarity_search_with_score_titile(knowledgebase_ids=product_knowledge_base_ids,knowledgebase_k=product_top_k,query=query)
                if len(doc_score_list)>0:
                    docs.extend(doc_score_list)
                
            if len(doc_knowledge_base_ids)>0 and doc_top_k>0:
                doc_score_list=db_knowledge.similarity_search_with_score_titile(knowledgebase_ids=doc_knowledge_base_ids,knowledgebase_k=doc_top_k,query=query)
                if len(doc_score_list)>0:
                    docs.extend(doc_score_list)


            if len(excel_knowledge_base_ids)>0 and excel_top_k>0:
                doc_score_list=db_excel.similarity_search_with_score_titile(knowledgebase_ids=excel_knowledge_base_ids,query=query,top_k=excel_top_k)
                if len(doc_score_list)>0:
                    docs.extend(doc_score_list)


        ref_docs_set=[]
        for item in docs:
            f=False
            for _a in ref_docs_set:
                if item.metadata["id"]==_a.metadata["id"]:
                    f=True
                    break
            if not f:
                ref_docs_set.append(item)

        docs=list(filter(lambda x: x.metadata["score"] > filter_value, ref_docs_set))
        # docs=(sorted(docs, key=lambda x: x.metadata["score"])[::-1][0:max_count])
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
        if options.get("brands_desc"): #用户指定了querys描述
            params_commend=params_commend.replace("提取的查询问题的品牌",options.get("brands_desc"))
        else:
            params_commend=params_commend.replace("提取的查询问题的品牌","品牌选择项：华为、惠普、奔图、爱普生、佳能、兄弟、东芝、利盟、京瓷、联想、施乐；根据聊天记录和问题选择品牌，不涉及品牌时留空")
        return params_commend