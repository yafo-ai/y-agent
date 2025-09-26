from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query,Path
from pydantic import Field

from src.api.customer_exception import *
from src.database.enums import KnowledgeBaseType
from src.database.models import KnowledgeBase, Category, KnowledgeDocument, FileDatabaseModel
from src.database.db_session import get_scoped_session
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/api/knowledgebases",
    tags=["知识库"],
)


@router.get("/", summary="列表")
def get_knowledgebases(session:Session=Depends(get_scoped_session)):
    models = KnowledgeBase.query.all()
    result = []
    for model in models:
        result.append({"id": model.id, "name": model.name,"type":model.type, "caption": model.caption, "label": model.label})
    return result



@router.get("/get/{id}", summary="详情")
def get_knowledgebase(id:int=Path(description="知识库主键id"),session:Session=Depends(get_scoped_session)):
    model = KnowledgeBase.get(id)
    return {"id": model.id, "name": model.name,"type":model.type, "caption": model.caption, "label": model.label}




@router.post("/add", summary="新增")
def knowledgebase_add(name:str= Body(max_length=50,description="知识库名称"),
                        caption:str= Body(max_length=200,description="知识库介绍"),
                        type:KnowledgeBaseType=Body(description="知识库类型",default=1),
                        label: str = Body(max_length=50, description="标签", default=""),
                        session:Session=Depends(get_scoped_session)
):
    model = KnowledgeBase(name=name, caption=caption,type=KnowledgeBaseType(type), label=label)
    model.add(True)
    return {"id":model.id,"name":name,"type":model.type,"caption":caption}


@router.post("/edit/{id}", summary="编辑")
def knowledgebase_edit(id:int=Path(description="知识库主键id"),
                         name:str= Body(max_length=50,description="知识库名称"),
                         caption:str= Body(max_length=200,description="知识库介绍"),
                         label: str = Body(max_length=50, description="标签", default=""),
                         session:Session=Depends(get_scoped_session)
):
    model = KnowledgeBase.get(id)
    model.name = name
    model.caption = caption
    model.label = label
    session.commit()
    return {"result":"success"}


@router.post("/delete/{id}", summary="删除")
def knowledgebase_delete(id:int=Path(description="知识库主键id"),session:Session=Depends(get_scoped_session)):
    model = KnowledgeBase.get(id)
    model_category = Category.query.filter(Category.knowledgebase_id == id).first()
    if model_category:
        raise ValidationException(detail="先删除知识库分类")
    model_document = KnowledgeDocument.query.filter(KnowledgeDocument.knowledgebase_id == id).first()
    if model_document:
        raise ValidationException(detail="先删除知识库文档")
    model_file_knowledgebase = FileDatabaseModel.query.filter(FileDatabaseModel.knowledgebase_id == id).first()
    if model_file_knowledgebase:
        raise ValidationException(detail="先删除知识库产品参数")
    model.delete(True)
    return {"result":"success"}


@router.post("/labels/", summary="标签")
def get_label_dict(ids: List[int] = Query(None, description="知识库id列表"),
                   session: Session = Depends(get_scoped_session)):
    """获取知识库品牌字典"""
    return KnowledgeBase.get_label_dict(ids)
