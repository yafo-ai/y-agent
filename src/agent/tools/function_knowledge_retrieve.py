import ast
from typing import List
from src.agent.tools.function_base import FunctionBase
from src.agent.working.working_space import WorkingSpace
from src.rag.excel_vector_store import ExcelChromaVectorStore
from src.database.models import KnowledgeBase
from src.rag.knowledge_vector_store import KnowledgeChromaVectorStore

class FunctionKnowledgeRetrieve(FunctionBase):

    name="knowledge_retrieve"
    description="知识库查询工具，用于查询各种领域知识。"
    params_description = 'knowledge_retrieve(&_Filter_&)'


    def _run(self,space:WorkingSpace,options,*args, **kwargs):

        # 存储被替换的变量内容
        temp_data={}

        queries=self.get_required_array_params_value("queries",space,options,*args, **kwargs)
        temp_data["queries"]=queries

        tags=self.get_nullable_array_params_value("tags",space,options,*args, **kwargs)
        temp_data["tags"]=tags

        ids=self.get_nullable_array_params_value("ids",space,options,*args, **kwargs)
        temp_data["ids"]=ids


        excel_knowledge_base_idsx=options.get("excel_knowledge_base_ids",[])

        doc_knowledge_base_ids=options.get("doc_knowledge_base_ids",[])
        doc_top_k=options.get("doc_top_k",0)

        excel_knowledge_base_ids=options.get("excel_knowledge_base_ids",[])
        excel_top_k=options.get("excel_top_k",0)

        filter_value=options.get("filter_value",0)
        output_option=options.get("output_option","json")

        knowledgebase_ids_filter=[]
        file_knowledgebase_ids_filter=[]

        #用标签过滤知识库
        if tags and len(tags)>0:
            lable_maps=KnowledgeBase.get_label_dict(None)

            for id in doc_knowledge_base_ids:
                lable=lable_maps.get(id,"")
                if lable=="" or lable is None or lable in tags:
                    knowledgebase_ids_filter.append(id)
            doc_knowledge_base_ids=knowledgebase_ids_filter

            for id in excel_knowledge_base_ids:
                lable=lable_maps.get(id,"")
                if lable=="" or lable is None or lable in tags:
                    file_knowledgebase_ids_filter.append(id)
            excel_knowledge_base_ids=file_knowledgebase_ids_filter


        db_excel=ExcelChromaVectorStore()
        db_knowledge=KnowledgeChromaVectorStore()  
        docs=[]

        for query in queries:

            #先用query查excel库
            if len(excel_knowledge_base_ids)>0 and excel_top_k>0:
                doc_score_list=db_excel.similarity_search_with_score_titile(knowledgebase_ids=excel_knowledge_base_ids,query=query,top_k=excel_top_k)
                if len(doc_score_list)>0:
                    docs.extend(doc_score_list)
                
            if len(doc_knowledge_base_ids)>0 and doc_top_k>0:
                doc_score_list=db_knowledge.similarity_search_with_score_titile(knowledgebase_ids=doc_knowledge_base_ids,knowledgebase_k=doc_top_k,query=query)
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
        
        where=[]
        if len(ids)>0:
            ref_id=[str(id) for id in ids]
            where.append({"ref_real_id": {"$in": ref_id}})

        # 元数据过滤字段
        metadata_filters=options.get("metadata_filter",[])
        if len(metadata_filters)>0:
            for _filter in metadata_filters:
                if _filter.get("value")=="" or _filter.get("value") is None:
                    if kwargs.get(_filter["key"]) is None or kwargs.get(_filter["key"])=="":
                        continue
                    where.append({_filter["key"]: {"$eq": str(kwargs.get(_filter["key"]))}})
                else:
                    _filter["value"]=self.template_render(space, _filter["value"],options)
                    where.append({_filter["key"]: {"$eq": _filter["value"]}})

        sift_docs=[]
        #在按照精确条件筛选Excel库
        if len(excel_knowledge_base_idsx)>0 and excel_top_k>0 and len(where)>0:
            doc_score_list=db_excel.similarity_search_with_score_titile_by_filter(knowledgebase_ids=excel_knowledge_base_idsx,query=str(queries),top_k=excel_top_k,where=where)
            if len(doc_score_list)>0:
                sift_docs.extend(doc_score_list)

        for item in sift_docs:
            f=False
            for _a in docs:
                if item.metadata["id"]==_a.metadata["id"]:
                    f=True
                    break
            if not f:
                docs.append(item)
                    

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
        # queries=["提取要查询的问题列表"],tags=["提取要查询的问题标签列表"],ids=["提取要查询的问题id列表"]
        filter_prompt=[]

        self.get_array_params_desc("queries","提取要查询的问题列表",filter_prompt,options)
        
        self.get_array_params_desc("tags","提取要查询的问题标签列表",filter_prompt,options)
        
        self.get_array_params_desc("ids","提取要查询的问题id列表",filter_prompt,options)
        
        
        #元数据过滤提示词组装 
        metadata_filters=options.get("metadata_filter",[])
        if len(metadata_filters)>0:
            for _filter in metadata_filters:
                if _filter["value"]=="":
                    filter_prompt.append(f'{_filter["key"]}="{_filter["desc"]}"')
        filter_prompt_str=",".join(filter_prompt)            
        params_commend=params_commend.replace("&_Filter_&",filter_prompt_str)
        return params_commend