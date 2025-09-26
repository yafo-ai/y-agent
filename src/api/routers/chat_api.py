from typing import Any,List
from src.database.models import KnowledgeBase
from src.rag.knowledge_vector_store import KnowledgeChromaVectorStore
from src.rag.excel_vector_store import ExcelChromaVectorStore
from src.api.customer_exception import ValidationException
from sqlalchemy.orm import Session
from ...database.db_session import get_scoped_session
from fastapi import APIRouter, Depends, Query, Path, Body

router = APIRouter(
    prefix="/api/chats",
    tags=["知识检索"],
)

@router.post("/similarity_search", summary="相似查询")
def similarity_search(question:str = Body(description="问题",max_length=500),
                      knowledgebase_ids:List[int]=Body(description="知识库id"),
                      knowledgebase_k:int=Body(description="知识库召回个数"),
                      file_knowledgebase_ids: List[int] = Body(description="文件参数知识库id",default=[]),
                      file_knowledgebase_k: int = Body(description="文件参数知识库召回个数",default=0),
                      product_model_ids: List[int] = Body(description="产品知识库id",default=[]),
                      product_model_top_k: int = Body(description="产品知识库召回个数",default=0),
                      session: Session = Depends(get_scoped_session)):
    
    if not question:
        raise ValidationException(detail="问题不能为空")
    if len(file_knowledgebase_ids) == 0 and len(knowledgebase_ids) == 0 and len(product_model_ids) == 0:
        raise ValidationException(detail="知识库id不能全部为空")
    
    # 知识库id
    knowledgebase_ids=list(set(knowledgebase_ids))

    store=KnowledgeChromaVectorStore()

    if len(knowledgebase_ids) > 0 and knowledgebase_k > 0:
        targets = store.similarity_search_with_score_titile(knowledgebase_ids=knowledgebase_ids,knowledgebase_k=knowledgebase_k,query=question)
    else:
        targets = []
    if len(product_model_ids) > 0 and product_model_top_k > 0:
        product_targets = store.similarity_search_with_score_titile(knowledgebase_ids=product_model_ids,knowledgebase_k=product_model_top_k,query=question)
        targets.extend(product_targets)

    if len(file_knowledgebase_ids) > 0 and file_knowledgebase_k > 0:
        file_targets = ExcelChromaVectorStore().similarity_search_with_score_titile(knowledgebase_ids=file_knowledgebase_ids,top_k=file_knowledgebase_k,query=question)
        targets.extend(file_targets)

    # 按照分数，从高到低排序
    targets = sorted(targets, key=lambda x: x.metadata.get("score", 0), reverse=True)

    return targets

@router.post("/similarity_search_test", summary="相似查询",tags=['public'])
def similarity_search_test(brands:str=Body(description="品牌"),
                           nc_ids:List[str]=Body(description="产品id"),
                           querys:List[str]=Body(description="问题"),
                           knowledgebase_ids:List[int]=Body(description="知识库id"),
                           file_knowledgebase_ids: List[int] = Body(description="文件参数知识库id",default=[]),
                           product_model_ids: List[int] = Body(description="产品知识库id",default=[]),
                           top_k:int=Body(description="top_k"),
                           min_score:float=Body(description="最小分数")):

    
    db_excel=ExcelChromaVectorStore()
    db_knowledge=KnowledgeChromaVectorStore()  
    docs=[]
    query=",".join(querys)
    filter_value=min_score
    knowledgebase_ids_filter=[]
    product_knowledgebase_ids_filter=[]
    file_knowledgebase_ids_filter=[]
    file_knowledgebase_ids_temp=file_knowledgebase_ids
    if brands and len(brands)>0:
        brand_maps=KnowledgeBase.get_label_dict(None)

        for id in knowledgebase_ids:
            brand=brand_maps.get(id,"")
            if brand=="" or brand is None or brand in brands:
                knowledgebase_ids_filter.append(id)
        knowledgebase_ids=knowledgebase_ids_filter

        for id in product_model_ids:
            brand=brand_maps.get(id,"")
            if brand=="" or brand is None or brand in brands:
                product_knowledgebase_ids_filter.append(id)
        product_model_ids=product_knowledgebase_ids_filter

        for id in file_knowledgebase_ids:
            brand=brand_maps.get(id,"")
            if brand=="" or brand is None or brand in brands:
                file_knowledgebase_ids_filter.append(id)
        file_knowledgebase_ids=file_knowledgebase_ids_filter

    for nc_id in nc_ids:
        if len(file_knowledgebase_ids_temp)>0:
            doc_score_list=db_excel.similarity_search_with_score_titile_by_code(knowledgebase_ids=file_knowledgebase_ids_temp,relation_code=nc_id,query=query,top_k=top_k)
            if len(doc_score_list)>0:
                docs.extend(doc_score_list)
    

    for query in querys:
        if len(product_model_ids)>0:
            doc_score_list=db_knowledge.similarity_search_with_score_titile(knowledgebase_ids=product_model_ids,knowledgebase_k=top_k,query=query)
            if len(doc_score_list)>0:
                docs.extend(doc_score_list)
        
        if len(knowledgebase_ids)>0:
            doc_score_list=db_knowledge.similarity_search_with_score_titile(knowledgebase_ids=knowledgebase_ids,knowledgebase_k=top_k,query=query)
            if len(doc_score_list)>0:
                docs.extend(doc_score_list)

        if len(file_knowledgebase_ids)>0:
            doc_score_list=db_excel.similarity_search_with_score_titile(knowledgebase_ids=file_knowledgebase_ids,query=query,top_k=top_k)
            if len(doc_score_list)>0:
                docs.extend(doc_score_list)
    

    docs=sorted(docs, key=lambda x: x.metadata["score"])[::-1]

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

    jsons=[]

    for doc in docs:
        jsons.append({"id":doc.metadata["id"],"score":doc.metadata["score"],"title":doc.metadata["title"],"content":doc.page_content})

    return jsons
