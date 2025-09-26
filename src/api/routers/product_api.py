import ast
from typing import List
from fastapi import APIRouter, Body, Depends, Query, Path

from src.api.customer_exception import *
from src.api.api_params import ProductAttributeParam
from src.database.db_session import get_scoped_session
from sqlalchemy.orm import Session
from ...database.models import KnowledgeBase, ProductModel
from ...rag.knowledge_vector_store import KnowledgeChromaVectorStore

from pypinyin import lazy_pinyin

router = APIRouter(
    prefix="/api/products",
    tags=["产品知识库"],
)


@router.get("", summary="列表")
def get_products(knowledgebase_id: int = Query(description="知识库id"),
                       p_id: int | None = Query(description="父id", default=None),
                       page: int = Query(description="页码", default=1),
                       pagesize: int = Query(description="每页数量", default=10),
                       keyword: str | None = Query(description="关键词", default=None),
                       session: Session = Depends(get_scoped_session)
                       ):
    """条件分页查询产品知识"""
    """不需要详细属性参数"""

    # print("session:"+str(id(session)))
    conditions = {}
    if knowledgebase_id:
        conditions["knowledgebase_id"] = knowledgebase_id
    if p_id:
        conditions["p_id"] = p_id
    # if keyword:
    #     conditions["name"] = ProductModel.name.ilike(f"%{keyword}%")
    if keyword:
        products = session.query(ProductModel).filter_by(**conditions).filter(
            ProductModel.name.ilike(f"%{keyword}%")).offset(pagesize * (page - 1)).limit(pagesize).all()
    else:
        products = session.query(ProductModel).filter_by(**conditions).offset(pagesize * (page - 1)).limit(
            pagesize).all()
    total_records = session.query(ProductModel).filter_by(**conditions).count()
    total_pages = (total_records + pagesize - 1) // pagesize
    # 连续点击，或者刷新，会提示错误：TypeError: Object is not iterable argument must have __dict__ attribute
    # return {"total_records": total_records, "total_pages": total_pages, "rows": products}
    if not products:
        return {"total_records": total_records, "total_pages": total_pages, "rows": []}
    rows = [{"id": product.id,
             "name": product.name,
             "p_id": product.p_id,
             "is_sku": product.is_sku,
             "is_index": product.is_index,
             "barcode": product.barcode,
             "nccode": product.nccode,
             "note": product.note,
             "is_disabled": product.is_disabled,
             "is_stop_production": product.is_stop_production,
             "knownledgebase_id": product.knowledgebase_id} for product in products]
    return {"total_records": total_records, "total_pages": total_pages, "rows": rows}


@router.get("/get/{id}", summary="详情")
def get_product(id: int = Path(description="产品id")):
    """用于id查询商品详情，商品详情返回具体信息以及继承的属性和自身属性"""
    product = ProductModel.get(id)
    
    parent_attrs = sorted(product.recursion_parent_attrs(), key=lambda x: lazy_pinyin(x.attr_key), reverse=False)
    nodes = KnowledgeChromaVectorStore().get_product_vindex(id)
    product_attrs = sorted(product.attributes, key=lambda x: lazy_pinyin(x.attr_key), reverse=False)

    knowledgebase_name=""
    knowledgebase = KnowledgeBase.get(product.knowledgebase_id)
    if knowledgebase:
        knowledgebase_name=knowledgebase.name


    return {"product": {"id": product.id,
                        "name": product.name,
                        "p_id": product.p_id,
                        "knowledgebase_id":product.knowledgebase_id,
                        "knowledgebase_name":knowledgebase_name,
                        "is_sku": product.is_sku,
                        "is_index": product.is_index,
                        "barcode": product.barcode,
                        "nccode": product.nccode,
                        "note": product.note,
                        "is_disabled": product.is_disabled,
                        "is_stop_production": product.is_stop_production,
                        "created_at": product.created_at,
                        "updated_at": product.updated_at,
                        "attrs": [
                            {"id": item.id,
                             "attr_key": item.attr_key,
                             "attr_value": ast.literal_eval(item.attr_value),
                             "attr_value_datatype": item.attr_value_datatype,
                             "created_at": product.created_at,
                             "updated_at": product.updated_at,
                             "sort": item.sort} for item in product_attrs] if product_attrs else []},
                             
            "parent_attrs": [
                {"id": item.id,
                 "attr_key": item.attr_key,
                 "attr_value": ast.literal_eval(item.attr_value),
                 "product_id": item.product_id,
                 "attr_value_datatype": item.attr_value_datatype,
                 "created_at": product.created_at,
                 "updated_at": product.updated_at,
                 "sort": item.sort} for item in parent_attrs] if parent_attrs else [],
            "nodes": nodes
            }


@router.get("/get_template", summary="模板")
def get_product_template(p_id: int | None = None):
    """
    用于新增修改前获取参数模板，返回继承属性信息，和同类属性的键值、类型
    继承属性，用于展示给客户
    同类属性，作为属性的参考，不需要值。
    """
    product = ProductModel(p_id=p_id) #创建虚拟节点
    parent_attrs = product.recursion_parent_attrs()
    same_attrs = product.get_sameleve_attr()

    return {"parent_attrs": [{"attr_key": item.attr_key,
                              "attr_value": ast.literal_eval(item.attr_value),
                              "attr_value_datatype": item.attr_value_datatype} for item in
                             parent_attrs] if parent_attrs else [],
            "same_attrs": [{"attr_key": item.attr_key, "attr_value_datatype": item.attr_value_datatype} for item in
                           same_attrs] if same_attrs else []}


@router.post("/add", summary="新增")
def add_product(knowledgebase_id: int = Body(description="知识库主键id"),
                      p_id: int | None = Body(description='父类id', default=None),
                      name: str = Body(max_length=256, description="商品名称"),
                      caption: str | None = Body(max_length=500, description="商品介绍", default=None),
                      note: str | None = Body(max_length=500, description="备注", default=None),
                      is_sku: bool = Body(description="是否为商品", default=False),
                      barcode: str | None = Body(description="69码", default=None),
                      nccode: str | None = Body(description="nc编码", default=None),
                      attrs: List[ProductAttributeParam] = Body(description="属性列表"),
                      is_disabled: bool = Body(description="是否停用", default=False),
                      is_stop_production: bool = Body(description="是否停产", default=False)):
    """
    用于添加商品：
    商品时需要：69码，nc编码
    商品属性：包含属性键值，类型，排序。只保留自身属性，不需要存储父类属性
    """
    if is_sku:
        if not barcode or not nccode:
            raise ValidationException(detail="商品69码和nc编码不能为空")
    if is_disabled is None:
        is_disabled = False
    if is_stop_production is None:
        is_stop_production = False
    product = ProductModel(knowledgebase_id=knowledgebase_id, p_id=p_id, name=name, caption=caption, note=note, is_sku=is_sku, barcode=barcode, nccode=nccode, is_disabled=is_disabled, is_stop_production=is_stop_production)
    for attr in attrs:
        product.append_attr(attr.attr_key, str(attr.attr_value), attr.attr_value_datatype, attr.sort)
    product.add(True)
    KnowledgeChromaVectorStore().add_product_vindex(product)
    product.is_index = True
    product.update(True)
    return {"id": product.id, "name": product.name}


@router.post("/edit/{id}", summary="修改")
def edit_product(id: int = Path(description="产品id"),
                         p_id: int | None = Body(description='父类id', default=None),
                         name: str = Body(max_length=256, description="商品名称"),
                         caption: str | None = Body(max_length=500, description="商品介绍", default=None),
                         note: str | None = Body(max_length=500, description="备注", default=None),
                         is_sku: bool = Body(description="是否为商品", default=False),
                         barcode: str | None = Body(description="69码", default=None),
                         nccode: str | None = Body(description="nc编码", default=None),
                         attrs: List[ProductAttributeParam] = Body(description="属性列表"),
                         is_disabled: bool | None = Body(description="是否停用", default=None),
                         is_stop_production: bool | None = Body(description="是否停产", default=None)):
    """
    用于修改商品，知识库不允许修改
    商品时需要：69码，nc编码
    商品属性：包含属性键值，类型，排序。只保留自身属性，不需要存储父类属性
    """
    product = ProductModel.get(id)
    KnowledgeChromaVectorStore().add_product_vindex(product)
    product.edit_product_model(p_id, name, caption, note, is_sku, barcode, nccode, attrs, is_disabled, is_stop_production)
    return {"result": "success"}


@router.post("/delete/{id}", summary="删除")
def delete_product(id: int = Path(description="产品id")):
    """
    用于删除商品
    商品存在子类时不允许删除。
    """
    product = ProductModel.get(id)
    if ProductModel.query.filter_by(p_id=id).first():
        raise ValidationException(detail="存在子类，不允许删除")
    KnowledgeChromaVectorStore().del_product_vindex(id)
    product.is_index = False
    product.delete(True)
    return {"result": "success"}


@router.post("/converter_index/{id}", summary="向量化")
def converter_product_index(id: int = Path(description="商品id")):
    """
    用于构建商品索引
    """
    product = ProductModel.get(id)
    KnowledgeChromaVectorStore().add_product_vindex(product)
    product.is_index = True
    product.update(True)
    return {"result": "success"}


@router.post('/move/{id}', summary="移动pid")
def move_product_pid(id: int = Path(description="商品id"), target_pid: int = Query(description="目标pid")):
    """
    用于移动商品pid
    """
    product = ProductModel.get(id)
    product.move_product_pid(target_pid)
    return {"result": "success"}


@router.post('/set_disabled/{id}', summary="设置停用")
def set_product_disabled(id: int = Path(description="商品id"), is_disabled: bool = Query(description="是否停用")):
    """
    用于设置商品停用状态
    """
    ProductModel.get(id).set_disabled_status(is_disabled)
    return {"result": "success"}


@router.post('/set_discontinued/{id}', summary="设置停产")
def set_product_discontinued(id: int = Path(description="商品id"), is_discontinued: bool = Query(description="是否停产")):
    """
    用于设置商品停产状态
    """
    ProductModel.get(id).set_production_status(is_discontinued)
    return {"result": "success"}

