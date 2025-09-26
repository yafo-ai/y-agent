import ast
import copy
import json
import logging
import math
import os
import re
import traceback
import uuid
from typing import Any, List, Optional, ClassVar

import pandas as pd

from src.api.customer_exception import ValidationException
from src.api.api_params import ProductAttributeParam
from src.database.enums import ProductAttributeDataType, KnowledgeBaseType, TestCaseStateType, TestCaseResultType, TestPlanState, \
    get_enum_name
from src.database.base_model import BaseModel, HistoryBase
from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Boolean, DateTime, Text, Float, cast, func, or_, desc
from sqlalchemy.orm import Mapped, aliased
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from src.agent.model_types import AgentRunLog, NodeType,APITool
from src.mcp.error import MCPAuthError, MCPError
from src.mcp.mcp_client import MCPClient
from src.mcp.types import Tool
from src.utils.config_helper import parse_config
from src.utils.excel_helper import get_excel_data_dict
from src.utils.json_helper import _customer_serializer
from src.utils.testplan_helper import TestPlanTasking, TestPlanContinueTasking


#大模型配置
class ModelConfig(BaseModel):
    base_name = Column(String(255), nullable=False, unique=True)
    type = Column(String(50), nullable=False)
    api_url = Column(String(255), nullable=False)
    api_key = Column(String(255), nullable=False)
    temprature = Column(Float, nullable=False)
    provider = Column(String(50), nullable=False)
    max_token = Column(Integer, nullable=True, comment="最大token数量")
    timeout = Column(Integer, nullable=True, comment="超时时间", default=300)

# # backref 表示，在 Child 类中动态创建 parent 属性，指向当前类
#知识库
class KnowledgeBase(BaseModel):

    # categorys = relationship("Category", back_populates="knowledgebase")
    # documents = relationship("KnowledgeDocument", back_populates="knowledgebase")
    type=Column(Enum(KnowledgeBaseType),nullable=False) #知识库类型
    label = Column(String(50), nullable=True) #标签

    @classmethod
    def get_label_dict(cls, ids: Optional[List[int]]):
        """获取知识库品牌字典"""
        if not ids:
            models = cls.query.all()
        else:
            models = cls.query.filter(cls.id.in_(ids)).all()
        result = {}
        for model in models:
            result[model.id] = model.label
        return result


    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id} deleted={bool(self.deleted_at)}>"


#知识库-类目
class Category(BaseModel):

    # p_id = Column(Integer, ForeignKey('category.id'),nullable=True)
    # knowledgebase_id=Column(Integer, ForeignKey('knowledgebase.id'))
    #
    # documents = relationship("KnowledgeDocument",back_populates="category")
    # knowledgebase = relationship("KnowledgeBase", back_populates="categorys")
    p_id = Column(Integer)
    knowledgebase_id = Column(Integer)

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id} deleted={bool(self.deleted_at)}>"

    @classmethod
    def get_list(cls, knowledgebase_id: Optional[int]):
        categories = cls.query.all()
        if knowledgebase_id is None or knowledgebase_id <= 0:
            return cls.tree(categories, 0)
        filter_categories = [category for category in categories if category.knowledgebase_id == knowledgebase_id]
        if not filter_categories:
            return []
        return cls.tree(filter_categories, 0)


    @classmethod
    def tree(cls, categories_list, pid=None):
        """树形"""
        result = cls.__recursion_category(categories_list, pid)
        return result

    @classmethod
    def __recursion_category(cls, categories_list, pid=None):
        result = []
        for category in categories_list:
            if category.p_id == pid or (category.p_id in (None, 0) and pid in (None, 0)):
                category_dict = {
                    "id": category.id,
                    "name": category.name,
                    "pid": category.p_id,
                    "children": cls.__recursion_category(categories_list, category.id)
                }
                result.append(category_dict)
        return result

    @classmethod
    def add_category_model(cls, name, caption, knowledgebase_id, p_id):
        if knowledgebase_id:
            KnowledgeBase.query.get(knowledgebase_id)
        if p_id:
            Category.query.get(p_id)
        category = cls(name=name, caption=caption, knowledgebase_id=knowledgebase_id, p_id=p_id)
        category.add(True)
        return category

    def edit_category_model(self, name, caption, knowledgebase_id, p_id):
        """编辑类目"""
        if knowledgebase_id:
            KnowledgeBase.query.get(knowledgebase_id)
        if p_id:
            Category.query.get(p_id)
        self.name = name
        self.caption = caption
        self.knowledgebase_id = knowledgebase_id
        self.p_id = p_id
        self.update(True)

    def delete_category_model(self):
        if Category.query.filter_by(p_id=self.id).count() > 0:
            raise ValidationException("类目下存在子类目，无法删除")
        if KnowledgeDocument.query.filter_by(category_id=self.id).count() > 0:
            raise ValidationException("类目下存在知识，无法删除")
        self.delete(True)

    def detail(self):
        detail_dict = {
            "id": self.id,
            "name": self.name,
            "caption": self.caption,
            "p_id": self.p_id,
            "knowledgebase_id": self.knowledgebase_id,
            "knowledgebase_name": None
        }
        if not self.knowledgebase_id:
            return detail_dict
        detail_dict['knowledgebase_name'] = KnowledgeBase.query.get(self.knowledgebase_id).name
        return detail_dict


#知识库-文档
class KnowledgeDocument(BaseModel):

    # category_id=Column(Integer,ForeignKey('category.id'),nullable=True)
    # knowledgebase_id=Column(Integer, ForeignKey('knowledgebase.id'))

    category_id = Column(Integer)
    knowledgebase_id = Column(Integer)

    file_ext: Mapped[str] = mapped_column(String(10), nullable=False, comment="文件扩展类型")
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, comment="文件路径")
    content:Mapped[str] = mapped_column(String(8000), nullable=False, comment="内容")
    is_index:Mapped[bool]=mapped_column(Boolean,default=False,comment="是否创建索引")
    is_markdown:Mapped[bool]=mapped_column(Boolean,default=False,comment="是否markdown格式")
    is_index_refresh:Mapped[bool]=mapped_column(Boolean,default=False,comment="是否需要更新索引")
    markdown_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, comment="markdown创建时间")
    index_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, comment="index创建时间")
    # category= relationship("Category", back_populates="documents")
    # knowledgebase = relationship("KnowledgeBase", back_populates="documents")

    node_qty:Mapped[int]=mapped_column(Integer,default=0, nullable=False, comment="分块数量")


    markdown = relationship("KnowledgeDocumentMarkdown", back_populates="document",uselist=False, cascade='all')


    @classmethod
    def create_document(cls,knowledgebase_id:int,name:str,content:str,category_id:Optional[int]=None,file_path:str="未知",file_ext:str="未知"):
        
        KnowledgeBase.get(knowledgebase_id)
        if category_id and category_id>0:
            category=Category.get(category_id)
            if category.knowledgebase_id!=knowledgebase_id:
                raise ValueError("工具knowledge_add参数category_id错误")
            
        doc=KnowledgeDocument(name=name,content=content,category_id=category_id,knowledgebase_id=knowledgebase_id)
        doc.markdown=KnowledgeDocumentMarkdown(content=content)
        doc.file_path = file_path
        doc.file_ext = file_ext
        doc.markdown_at=func.now()
        doc.is_markdown=True
        doc.add(True)

        return doc
    
    @classmethod
    def edit_content(cls,id:int,name:str,content:str):
        doc = KnowledgeDocument.get(id)
        doc.name=name
        doc.content = content
        doc.update(True)
        return doc

    @classmethod
    def edit_markdown_content(cls,id:int,name:str,markdown_content:str):

        doc = KnowledgeDocument.get(id)
        if doc.markdown:
            doc.markdown.content = str(markdown_content)
        else:
            doc.markdown=KnowledgeDocumentMarkdown(content=str(markdown_content))
        doc.markdown_at=func.now()
        doc.is_markdown=True
        doc.is_index_refresh=True
        doc.name=name
        doc.update(True)

        return doc
    
    @classmethod
    def append_markdown_content(cls,id:int,append_content:str):

        doc = KnowledgeDocument.get(id)
        if doc.markdown:
            doc.markdown.content = doc.markdown.content+"\n\n"+append_content

        else:
            doc.markdown=KnowledgeDocumentMarkdown(content=append_content)
        doc.markdown_at=func.now()
        doc.is_markdown=True
        doc.is_index_refresh=True
        doc.update(True)
        
        return doc
    
    @classmethod
    def document_move_category(cls,id:int,category_id:int):
        Category.get(category_id)
        doc = KnowledgeDocument.get(id)
        doc.category_id = category_id
        doc.update(True)

    @classmethod
    def document_batch_move_category(cls,category_id:int,target_category_id:int):
        Category.get(target_category_id)
        documents = KnowledgeDocument.query.filter(KnowledgeDocument.category_id==category_id).all()
        if documents:
            for doc in documents:
                doc.category_id = target_category_id
                doc.update()
            documents[0].session.commit()
        
    def set_index_ok(self,node_qty:int):
        self.node_qty =node_qty
        self.is_index = True
        self.index_at=func.now()
        self.is_index_refresh=False
        self.update(True)

    def del_index(self):
        self.node_qty=0
        self.is_index = False
        self.update(True)



    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id} deleted={bool(self.deleted_at)}>"

#知识库Markdown文档
class KnowledgeDocumentMarkdown(BaseModel,HistoryBase):
    content:Mapped[str] = mapped_column(String(8000), nullable=True, comment="markdown格式内容")
    knowledge_document_id = Column(Integer, ForeignKey('knowledge_document.id'))

    document = relationship("KnowledgeDocument", back_populates="markdown",uselist=False)

    __versioned__ = {} # 创建历史记录

#产品模型
class ProductModel(BaseModel):
    knowledgebase_id = Column(Integer)
    p_id = Column(Integer)
    attributes = relationship("ProductModelAttribute", back_populates="productmodel", cascade='all', lazy='dynamic')
    is_sku:Mapped[bool]=mapped_column(Boolean,default=False,comment="是否为sku") #sku为最后一个节点
    is_index:Mapped[bool]=mapped_column(Boolean,default=False,comment="是否创建索引")
    barcode: Mapped[str] = mapped_column(String(20), nullable=True, comment="69码")
    nccode:Mapped[str] = mapped_column(String(20), nullable=True, comment="nc编码")
    is_disabled = mapped_column(Boolean, default=False, comment="是否停用【false表示未停用，true表示已停用】")
    is_stop_production = mapped_column(Boolean, default=False, comment="是否停产【false表示未停产，true表示已停产】")

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id} deleted={bool(self.deleted_at)}>"

    def edit_product_model(self, p_id: int, name, caption, note, is_sku, barcode, nccode, attrs: List[ProductAttributeParam], is_disabled, is_stop_production):
        """编辑商品模型"""
        if is_sku:
            if not barcode or not nccode:
                raise ValidationException("商品69码和nc编码不能同时为空")
        self.p_id = p_id
        self.name = name
        self.caption = caption
        self.note = note
        self.is_sku = is_sku
        self.barcode = barcode
        self.nccode = nccode
        if is_disabled is not None:
            self.is_disabled = is_disabled
        if is_stop_production is not None:
            self.is_stop_production = is_stop_production

        # 要删除的属性
        product_remove_attrs = []
        # 要添加的属性
        product_add_attrs = []

        for product_attr in self.attributes:
            match = next((attr for attr in attrs if attr.attr_id == product_attr.id), None)
            if not match:
                product_remove_attrs.append(product_attr.id)
            else:
                product_attr.attr_key = match.attr_key
                product_attr.attr_value = str(match.attr_value)
                product_attr.attr_value_datatype = match.attr_value_datatype
                product_attr.sort = match.sort
        for param_attr in attrs:
            match = next((attr for attr in self.attributes if attr.id == param_attr.attr_id), None)
            if not match:
                product_add_attrs.append(param_attr)
        for rm in product_remove_attrs:
            self.remove_attr(rm)
        for add in product_add_attrs:
            self.append_attr(add.attr_key, str(add.attr_value), add.attr_value_datatype, add.sort)
        self.update(True)

    #修改属性
    def update_attr(self,attr_id,attr_key,attr_value,attr_value_datatype,sort):
        this_attrs= [obj for obj in self.attributes if obj.id == attr_id]
        if this_attrs:
            for item in this_attrs:
                item.attr_key=attr_key
                item.attr_value=attr_value
                item.attr_value_datatype=attr_value_datatype
                item.sort=sort


    #追加新属性
    def append_attr(self,attr_key,attr_value,attr_value_datatype,sort):
        self.attributes.append(ProductModelAttribute(attr_key=attr_key,attr_value_datatype=attr_value_datatype,attr_value=attr_value,sort=sort))

    #移除属性
    def remove_attr(self,attr_id):
        this_attrs= [obj for obj in self.attributes if obj.id == attr_id]
        if this_attrs:
            for item in this_attrs:
                self.attributes.remove(item)

    #递归查询父属性
    def recursion_parent_attrs(self):
        attrs:List[ProductModelAttribute]=[]
        if self.p_id:
            self.__recursion__(self.p_id,attrs)
        return attrs

    def __recursion__(self,p_id,attrs:List):
        model = ProductModel.query.filter(ProductModel.id == p_id).first()
        if not model:
            return
        if model and model.attributes:
            sorted_attr= sorted(model.attributes, key=lambda x: (x.sort,x.id),reverse=True)
            for item in sorted_attr:
                attrs.insert(0,item)
        if model.p_id:
            self.__recursion__(model.p_id,attrs)


    #查询一个同级别的属性
    def get_sameleve_attr(self):
        if self.p_id:
            model = ProductModel.query.filter(ProductModel.p_id==self.p_id).order_by(ProductModel.created_at.desc()).first()
            if not model:
                return None
            return sorted(model.attributes, key=lambda x: (x.sort,x.id),reverse=False)
        else:
            return None

    def get_sub_products(self,count=10):
        models = ProductModel.query.filter(ProductModel.p_id == self.id).limit(count)
        return [item for item in models]

    #查询子商品名称
    def get_sub_products_names(self,count=10):
        models = ProductModel.query.filter(ProductModel.p_id == self.id).limit(count).all()
        if len(models)==0:
            return " "
        text="包含："
        for item in models:
            text+=item.name+","
        return text

    #用于后处理器召回文本
    def get_text(self):
        text=self.name+'\n'
        p_attrs=self.recursion_parent_attrs() or []
        for attr in p_attrs:
            text+=attr.attr_key+":"+attr.attr_value+'\n'
        _attrs=sorted(self.attributes, key=lambda x: (x.sort,x.id),reverse=False) or []
        for attr in _attrs:
            text+=attr.attr_key+":"+attr.attr_value+'\n'
        if self.caption:
            text+=self.caption+'\n'
        if self.note:
            text+=self.note+'\n'
        # text+=self.get_sub_products_names()
        return text

    def move_product_pid(self, target_pid: int):
        """移动商品到目标pid下"""
        if target_pid == self.p_id:
            raise ValidationException("当前已经在目标pid下")
        target_product = self.session.query(ProductModel).filter(ProductModel.id == target_pid).one_or_none()
        if not target_product:
            raise ValidationException("目标pid不存在")
        self.p_id = target_pid
        self.update(True)

    def set_disabled_status(self, is_disabled: bool):
        """停用/启用"""
        self.is_disabled = is_disabled
        self.update(True)

    def set_production_status(self, is_discontinued: bool):
        """停产/启用"""
        self.is_stop_production = is_discontinued
        self.update(True)



#产品模型属性
class ProductModelAttribute(BaseModel):

    product_id=Column(Integer,ForeignKey('product_model.id'),nullable=True)
    productmodel = relationship("ProductModel", back_populates="attributes")

    attr_key:Mapped[str] = mapped_column(String(255), nullable=True, comment="属性键")
    attr_value:Mapped[str] = mapped_column(String(2000), nullable=True, comment="属性值")
    attr_value_datatype=Column(Enum(ProductAttributeDataType),nullable=False) #属性的类型

    sort = Column(Integer)


class PromptModel(BaseModel):
    """
    提示词模型
    """
    content: Mapped[str] = mapped_column(String(8000), comment='提示内容')
    prompt_type = Column(String(200), nullable=False, comment='提示词类型')
    prompt_type_id = Column(Integer, nullable=True, comment='提示词类型id')
    unique_code = Column(String(200), nullable=True, comment='唯一编码', default=None)

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id} deleted={bool(self.deleted_at)}>"

    __versioned__ = {}

    @classmethod
    def get_pagination(cls, page: int, pagesize: int, prompt_type_id: Optional[int], *args, **kwargs):
        """
        分页查询
        @param page:
        @param pagesize:
        @param prompt_type_id: 提示词类型id, 0：未分类， 不传或者None：全部
        @param args: 位置参数 arg1, arg2, arg3
        @param kwargs: 键值对参数  key1=value1, key2=value2
        @return: {"total_records": total_records, "total_pages": total_pages, "rows": []}
        """
        if page <= 0:
            page = 1
        if pagesize <= 0:
            pagesize = 10
        if prompt_type_id is not None and prompt_type_id <= 0:
            query = cls.query.filter(or_(cls.prompt_type_id.is_(None), cls.prompt_type_id == 0))
        elif prompt_type_id is not None and prompt_type_id > 0:
            query = cls.query.filter(cls.prompt_type_id == prompt_type_id)
        else:
            query = cls.query
        if args:
            query = query.filter(*args)
        if kwargs:
            query = query.filter_by(**kwargs)
        total_records = query.count()
        if total_records == 0:
            return {"total_records": 0, "total_pages": 0, "rows": []}
        total_pages = (total_records + pagesize - 1) // pagesize
        query = query.offset((page - 1) * pagesize).limit(pagesize).all()
        return {
            "total_records": total_records,
            "total_pages": total_pages,
            "rows": [
                {
                    "id": item.id,
                    "name": item.name,
                    "prompt_type_name": item.prompt_type if item.prompt_type else None,
                    "prompt_type_id": item.prompt_type_id if item.prompt_type_id else None,
                    "content": item.content,
                    "created_at": item.created_at, "updated_at": item.updated_at
                } for item in query
            ]
        }

    @classmethod
    def get_detail(cls, id: int):
        """
        获取详情
        @param id:
        @return:
        """
        model = cls.get(id)
        return {
            "id": id,
            "name": model.name,
            "content": model.content,
            "prompt_type": model.prompt_type if model.prompt_type else None,
            "prompt_type_name": model.prompt_type if model.prompt_type else None,
            "prompt_type_id": model.prompt_type_id if model.prompt_type_id else None,
            "created_at": model.created_at,
            "updated_at": model.updated_at
        }

    @classmethod
    def add_prompt(cls, name: str, content: str, prompt_type_id: Optional[int]):
        type_id = None
        type_name = None
        if prompt_type_id is not None and prompt_type_id > 0:
            _type_model = PromptType.get(prompt_type_id)
            type_id = _type_model.id
            type_name = _type_model.name
        model = cls(name=name, content=content, prompt_type=type_name, prompt_type_id=type_id, unique_code=str(uuid.uuid4()))
        model.add(True)
        return model

    def update_prompt(self, name: str, content: str, prompt_type_id: Optional[int]):
        type_id = None
        type_name = None
        if prompt_type_id is not None and prompt_type_id > 0:
            _type_model = PromptType.get(prompt_type_id)
            type_id = _type_model.id
            type_name = _type_model.name
        self.update_properties(name=name, content=content, prompt_type=type_name, prompt_type_id=type_id)
        if self.unique_code is None or self.unique_code == "":
            self.unique_code = str(uuid.uuid4())
        self.update(True)
        return self

    def version_history(self, ver: Optional[int] = None):
        if ver is not None and ver <= 0:
            ver = None
        if ver is None:
            versions = sorted(self.versions, key=lambda x: x.ver, reverse=True)
        else:
            versions = self.versions.filter_by(ver=ver).all()
        return [
            {
                "id": v.id,
                "ver": v.ver,
                "name": v.name,
                "content": v.content,
                "prompt_type": v.prompt_type,
                "prompt_type_id": v.prompt_type_id,
                "created_at": v.created_at,
                "updated_at": v.updated_at
            } for v in versions
        ] if versions else [{}]


class FileDatabaseModel(BaseModel):
    """文件数据库"""
    knowledgebase_id = Column(Integer)
    file_path = mapped_column(String(255), comment='文件路径')
    file_name = mapped_column(String(255), comment='文件名称')
    file_template_type = mapped_column(Integer, comment='文件模板')
    file_ext = mapped_column(String(10), comment='文件扩展名')
    file_size = mapped_column(Integer, comment='文件大小')
    is_index = mapped_column(Boolean, comment='是否已经添加到向量', default=False)
    index_at = mapped_column(DateTime(timezone=True), nullable=True, comment="index创建时间")
    data_qty = mapped_column(Integer, comment='商品数量')
    file_contents = relationship("FileContentModel", back_populates="file_database", cascade='all', lazy='dynamic', uselist=True)
    is_index_refresh = mapped_column(Boolean, nullable=True, default=False, comment="是否需要更新索引")
    index_refresh_at = mapped_column(DateTime(timezone=True), default=None, comment="刷新时间")

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id} deleted={bool(self.deleted_at)}>"

    # 普通属性，不会在数据库体现，仅用于定义共有字段,，指示orm跳过它
    attribute_field: ClassVar[str] = 'attribute'
    unique_code_field: ClassVar[str] = '唯一编码'
    title_field: ClassVar[str] = '标题'
    not_exist_field: ClassVar[str] = ["id", "ref_id", "ref_real_id", "filename", "knowledgebase_id", "type"]

    # 更新表格数据
    def update_filedata(self, file_path: str):
        excel_model = self.excel_to_model(file_path)
        excel_model_contents = excel_model.file_contents.all()
        excel_content_codes = [content_item.relation_code for content_item in excel_model_contents]
        self_contents_codes = [content_item.relation_code for content_item in self.file_contents.all()]
        del_codes = list(set(self_contents_codes) - set(excel_content_codes))
        del_self_contents = [file_content for file_content in self.file_contents.all() if file_content.relation_code in del_codes]
        for del_code in del_self_contents:
            self.file_contents.remove(del_code)

        self.file_path = excel_model.file_path
        self.file_name = excel_model.file_name
        self.file_ext = excel_model.file_ext
        self.file_size = excel_model.file_size
        self.data_qty = excel_model.data_qty

        for file_content in excel_model.file_contents.all():

            filter_content = filter(lambda x: x.relation_code == file_content.relation_code, self.file_contents)
            match_content = next(filter_content, None)
            if match_content is None:
                file_content.file_database = self
                self.file_contents.append(file_content)
            else:
                match_content.relation_title = file_content.relation_title
                match_content.relation_code = file_content.relation_code
                match_content.relation_index = file_content.relation_index
                match_content.content = file_content.content
                match_content.markdown_content = file_content.markdown_content
        self.is_index_refresh = True
        self.update(True)
        return {"result": "success"}

    # 导入excel，转换成模型数据
    @classmethod
    def excel_to_model(cls, file_path: str):
        sheet_data_list = []
        with pd.ExcelFile(file_path) as xf:
            for sheet_name in xf.sheet_names:
                df_sheet = xf.parse(sheet_name, header=None)
                if len(list(df_sheet.values)) <= 0:
                    continue
                row_list = df_sheet.iloc[:, 0].unique().tolist()
                if len(row_list) <= 0 or not pd.notna(row_list[0]):
                    continue
                exist_field = [tmp_field for tmp_field in row_list if str(tmp_field).lower() in cls.not_exist_field]
                if exist_field is not None and len(exist_field) > 0:
                    raise ValidationException(f"表格sheet【{sheet_name}】，存在非法字段【{exist_field}】")
                if cls.unique_code_field not in row_list:
                    raise ValidationException(f"表格sheet【{sheet_name}】，【{cls.unique_code_field}】行 不存在")
                if cls.title_field not in row_list:
                    raise ValidationException(f"表格sheet【{sheet_name}】，【{cls.title_field}】行 不存在")
                sheet_date = get_excel_data_dict(df_sheet, cls.attribute_field, cls.title_field, cls.unique_code_field)
                sheet_data_list.extend(sheet_date)
        if len(sheet_data_list) == 0:
            raise ValidationException("文件内容为空")
        file_database = FileDatabaseModel()
        file_database.knowledgebase_id = None
        file_database.file_template_type = None
        file_database.file_path = file_path
        file_database.file_name = os.path.basename(file_path)
        file_database.file_ext = file_path.split('.')[-1]
        file_database.file_size = os.path.getsize(file_path)
        file_database.data_qty = 0
        file_content_list = []
        for data_item in sheet_data_list:
            code_list = []
            # region 处理单个单元格，多个唯一编码
            tmp_code = data_item.get(cls.unique_code_field, '').strip()
            if tmp_code.find('\n') != -1:
                tmp_code = tmp_code.replace('\n', ' ')
            tmp_code = re.sub(r'\s+', ' ', tmp_code)
            if tmp_code.find(",") != -1:
                code_list = tmp_code.split(",")
            elif tmp_code.find(" ") != -1:
                code_list = tmp_code.split(" ")
            else:
                code_list.append(tmp_code)
            # endregion

            if len(code_list) > 1 and (len(code_list) != len(data_item.get(cls.title_field, '').strip().split("\n"))):
                raise ValidationException(f"表格sheet【{sheet_name}】，编码【{str(code_list)}】的名称和数量不匹配")

            for code_index, code_item in enumerate(code_list):
                if code_item == '' or code_item is None:
                    continue
                copy_date_item = copy.deepcopy(data_item)

                copy_date_item[cls.unique_code_field] = code_item
                copy_date_item[cls.title_field] = copy_date_item.get(cls.title_field, '').strip().split("\n")[code_index]

                file_content = FileContentModel()
                file_content.relation_title = copy_date_item.get(cls.title_field, '')
                file_content.content = str(copy_date_item)
                file_content.relation_index = file_database.data_qty
                file_content.file_database = file_database

                markdown_content, title, relation_code = FileContentModel.convert_data_to_markdown(
                    data_dic=copy_date_item,
                    title_field=cls.title_field,
                    code_field=cls.unique_code_field,
                    code_field_result=code_item,
                    attribute_field=cls.attribute_field
                )
                file_content.markdown_content = markdown_content
                file_content.relation_title = title
                file_content.relation_code = relation_code
                file_content_list.append(file_content)
                file_database.data_qty += 1
            file_database.file_contents = file_content_list
        return file_database


class FileContentModel(BaseModel):
    """文件数据库详情"""
    file_database_id = Column(Integer, ForeignKey('file_database_model.id'), nullable=False)
    file_database = relationship("FileDatabaseModel", back_populates="file_contents")
    relation_title = mapped_column(String(255), comment='关联标题')
    relation_code = mapped_column(String(255), comment='关联代码')
    relation_index=mapped_column(Integer, comment='数据索引')
    markdown_content = mapped_column(String(8000), comment='markdown内容')
    content = mapped_column(String(), comment='内容')
    

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id} deleted={bool(self.deleted_at)}>"

    # 获取核心主要参数作为元数据
    @property
    def get_metadata(self) -> Optional[dict]:
        if self.content is None or self.content == '':
            return None
        tmp_content = ast.literal_eval(self.content)
        title_dict = {}
        for key, value in tmp_content.get('attribute', {}).items():
            if isinstance(value, dict):
                continue
            title_dict[key] = value
        return title_dict


    # @classmethod
    # def convert_data_to_markdown(cls, data: list[dict], title_field: str = 'Model', attribute_field: str = 'attribute'):
    #     product_markdown_list = []
    #     try:
    #         for item in data:
    #             current_markdown_text = f'# {item.get(title_field)} \n'
    #             for attr_key, attr_value in item.get(attribute_field, {}).items():
    #                 if not isinstance(attr_value, dict):
    #                     current_markdown_text += f'{attr_key} {attr_value} \n'
    #                 else:
    #                     current_markdown_text += f'## {attr_key} \n'
    #                     current_markdown_text += cls._recursion_json(attr_value, depth=3)
    #             product_markdown_list.append(current_markdown_text)
    #     except Exception as e:
    #         traceback.print_exc()
    #         logging.error(f'转换markdown失败，原因：{e}')
    #     return product_markdown_list

    @classmethod
    def convert_data_to_markdown(cls, data_dic: dict, title_field: str = '标题', code_field: str = '唯一编码', code_field_result: str = '', attribute_field: str = 'attribute'):
        current_markdown_text = ''
        try:
            current_markdown_text = f'# {data_dic.get(title_field)}\n'
            for attr_key, attr_value in data_dic.get(attribute_field, {}).items():
                if attr_value == '' or attr_value is None:
                    continue
                if not isinstance(attr_value, dict):
                    current_markdown_text += f'**{attr_key}**：{attr_value}\n'
                else:
                    if isinstance(attr_value, dict):
                        current_markdown_text += f'## {attr_key}\n'
                        for key, value in attr_value.items():
                            current_markdown_text += f'**{key}**：{value}\n'
                    else:

                        recursion_text = cls._recursion_json(attr_value, depth=3)

                        if recursion_text == '' or recursion_text is None:
                            continue
                        current_markdown_text += f'## {attr_key}\n'
                        current_markdown_text += recursion_text

        except Exception as e:
            traceback.print_exc()
            logging.error(f'转换markdown失败，原因：{e}')
        return current_markdown_text, data_dic.get(title_field), code_field_result

    @classmethod
    def _recursion_json(cls, json_obj, depth: int = 1):
        """递归处理属性"""
        markdown_str = ''
        for key, value in json_obj.items():
            if value == '' or value is None:
                continue
            if isinstance(value, dict):
                # 如果值是字典，则递归调用函数
                markdown_str += '#' * depth + ' ' + key + '\n'
                markdown_str += cls._recursion_json(value, depth=depth + 1)
            else:
                # 如果值是字符串，则直接添加到 Markdown 字符串中
                markdown_str += key + ' ' + str(value) + '\n'
        return markdown_str

    @classmethod
    def get_content_attribute_keys(cls, relation_code: list[str]):
        """批量获取内容属性值"""
        result_list = []
        tmp_set_result = set()
        ids = list(set(relation_code))
        if len(ids) <= 0:
            return ""
        datas= cls.query.filter(cls.relation_code.in_(ids)).with_entities(cls.id, cls.file_database_id, cls.content, cls.relation_code).all()
        if datas is None or len(datas) <= 0:
            return ""
        for data in datas:
            tmp_attribute = ast.literal_eval(data.content).get("attribute")
            # tmp_attribute_key = cls._get_dict_keys_str(tmp_attribute)
            tmp_attribute_key = cls._get_dict_keys_list(tmp_attribute)
            if tmp_attribute_key is None:
                continue
            # tmp_result = "\n".join(list(result))
            tmp_set_result_len = len(tmp_set_result)
            tmp_set_result.add(json.dumps(tmp_attribute_key))
            if len(tmp_set_result) > tmp_set_result_len:
                result_list.append({"tags": tmp_attribute_key})
        tmp_result = {"data": result_list}
        return tmp_result

    @classmethod
    def _get_dict_keys_str(cls, data, indent=0):
        key_str = ""
        for k, v in data.items():
            key_str += " " * indent + k + "\n"
            if not isinstance(v, dict):
                continue
            key_str += cls._get_dict_keys_str(v, indent + 1)
        return key_str

    @classmethod
    def _get_dict_keys_list(cls, data):
        key_list = []
        for k, v in data.items():
            if isinstance(v, dict):
                key_list.append({"tag": k, "subtag": list(v.keys())})
            else:
                key_list.append({"tag": k, "subtag": []})
        return key_list


class TestCate(BaseModel):
    """测试分类"""
    color = mapped_column(String(50), comment='颜色')
    pid = mapped_column(Integer, comment='父级id', default=None)
    test_cases = relationship("TestCase", back_populates="test_cate", cascade='all', lazy='dynamic', uselist=True)
    tag = mapped_column(String(2), default='W', comment='标签[S:单元测试  W:流程测试]')

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id} deleted={bool(self.deleted_at)}>"

    @classmethod
    def tree(cls, test_cate_list, pid=None):
        """树形"""
        result = cls.__recursion_category(test_cate_list, pid)
        return result

    @classmethod
    def __recursion_category(cls, test_cate_list, pid=None):
        result = []
        for category in test_cate_list:
            if category.pid == pid or (category.pid in (None, 0) and pid in (None, 0)):
                category_dict = {
                    "id": category.id,
                    "name": category.name,
                    "color": category.color,
                    "pid": category.pid,
                    "tag": category.tag,
                    "children": cls.__recursion_category(test_cate_list, category.id)
                }
                result.append(category_dict)
        return result

    def recursion_delete(self):
        """递归删除"""
        recursive_cate_list = self.get_recursion_children()
        self.delete()
        for cate in recursive_cate_list:
            cate.delete()
        self.session.commit()

    def get_recursion_children(self):
        """递归获取子节点"""
        result = []
        children = TestCate.query.filter_by(pid=self.id).all()
        for child in children:
            result.extend(child.get_recursion_children())
        return result


class TrainCate(BaseModel):
    """训练分类"""
    color = mapped_column(String(50), comment='颜色')
    pid = mapped_column(Integer, comment='父级id', default=None)
    train_cases = relationship("TrainCase", back_populates="train_cate", cascade='all', lazy='dynamic', uselist=True)

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id} deleted={bool(self.deleted_at)}>"

    @classmethod
    def tree(cls, pid=0):
        """树形"""
        categories = cls.query.all()
        if categories is None or len(categories) == 0:
            return []
        result = cls.__recursion_category(categories, pid)
        return result

    @classmethod
    def __recursion_category(cls, categories, pid=None):
        result = []
        for category in categories:
            if category.pid == pid or (category.pid in (None, 0) and pid in (None, 0)):
                category_dict = {
                    "id": category.id,
                    "name": category.name,
                    "color": category.color,
                    "pid": category.pid,
                    "children": cls.__recursion_category(categories, category.id)
                }
                result.append(category_dict)
        return result

    def delete_train_category(self):
        if TrainCate.query.filter(TrainCate.pid == self.id).count() > 0:
            raise ValidationException("该分类下存在子分类，请先删除子分类")
        if TrainCase.query.filter(TrainCase.train_cate_id == self.id).count() > 0:
            raise ValidationException("该分类下存在数据，请先删除数据")
        self.delete(True)


class TestCase(BaseModel):
    """测试用例"""
    test_cate_id = mapped_column(Integer, ForeignKey('test_cate.id'), comment='测试分类id')
    test_cate=relationship("TestCate", back_populates="test_cases")
    question = mapped_column(String(2000), comment='问题')
    right_answer = mapped_column(String(4000), comment='正确回答')
    test_count = mapped_column(Integer, comment='测试次数', default=0)
    test_pass_count = mapped_column(Integer, comment='测试通过次数', default=0)
    test_fail_count = mapped_column(Integer, comment='测试失败次数', default=0)
    test_result = mapped_column(Integer, default=TestCaseResultType.未测试.value, comment='测试结果')
    test_state = mapped_column(Integer, default=TestCaseStateType.准备就绪.value, nullable=False, comment='测试状态')
    test_case_logs = relationship("TestCaseLog", back_populates="test_case", cascade='all', lazy='dynamic', uselist=True)
    test_case_citations = relationship("TestCaseCitation", back_populates="test_case", cascade='all', lazy='dynamic', uselist=True)
    test_result_answer = mapped_column(String(4000), comment='测试结果回答')
    workflow_log_id = mapped_column(Integer, comment='工作流日志id', nullable=True)
    workflow_log_inputs = mapped_column(Text, comment='工作流输入', nullable=True)
    workflow_id = mapped_column(Integer, comment='工作流id', nullable=True)
    tag = mapped_column(String(2), default='W', comment='标签[S:单元测试  W:流程测试]')
    workflow_node_log_id = mapped_column(Integer, comment='工作流节点日志id', default=None, nullable=True)
    is_marked = mapped_column(Boolean, default=False, comment='是否已经标记')
    is_modified = mapped_column(Boolean, default=False, comment='是否已经修改')
    test_standard = mapped_column(String(1000), comment='测试标准', default=None)
    vision_file_str = mapped_column(Text, comment='视觉模型文件路径', nullable=True)

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id} deleted={bool(self.deleted_at)}>"

    @classmethod
    def case_add(cls, test_cate_id, question, right_answer, note=None, workflow_log_id=None, test_standard=None):
        """新增用例"""
        test_cate_id = test_cate_id if test_cate_id != 0 else None
        workflow_log_id = workflow_log_id if workflow_log_id != 0 else None
        test_case = cls(test_cate_id=test_cate_id, question=question, right_answer=right_answer)
        test_case.note = note
        test_case.workflow_log_id = workflow_log_id
        test_case.test_standard = test_standard

        if workflow_log_id is not None:
            test_case.test_case_citations = cls.get_case_workflow_log_citations(workflow_log_id)
            workflow_log = WorkFlowRunLog.get(workflow_log_id)
            test_case.workflow_log_inputs = workflow_log.inputs
            test_case.workflow_id = workflow_log.flow_id
        test_case.add(True)
        return test_case


    @classmethod
    def get_case_workflow_log_citations(cls, workflow_log_id: int):
        """获取聊天记录引用"""
        test_case_citations = []
        workflow_log = WorkFlowRunLog.get(workflow_log_id)
        for citation in json.loads(workflow_log.citations):
            test_case_citation = TestCaseCitation()
            test_case_citation.type = citation.get("metadata").get("type")
            test_case_citation.title = citation.get("metadata").get("title")
            test_case_citation.ref_id = citation.get("metadata").get("ref_id")
            test_case_citations.append(test_case_citation)
        return test_case_citations

    def execute_completed(self, test_answer, test_result: bool, score: str, citations: str = None, elapsed_time: str = None, test_plan_id: int = None, test_report_id: int = None, evaluation_llm_id:int|None=None,
                          evaluation_prompt_id:int|None=None,
                          current_workflow_log_id:int|None=None,
                          workflow_node_log_id: int | None=None,
                          unit_llm_id: int | None = None,
                          execute_llm_name: str | None = None,
                          execute_workflow_name: str | None = None,
                          error_msg: str | None = None
                          ):
        """添加测试记录"""
        test_report = None
        if test_report_id: 
            test_report = TestReport.get(test_report_id)

        self.test_state = TestCaseStateType.测试完成.value
        if test_result:
            self.test_result = TestCaseResultType.成功.value
            self.test_pass_count += 1
            if test_report: test_report.test_pass_count += 1
        else:
            self.test_result = TestCaseResultType.失败.value
            self.test_fail_count += 1
            if test_report: test_report.test_fail_count += 1

        self.test_count += 1
        case_log = TestCaseLog()
        case_log.test_case_id = self.test_cate_id
        case_log.test_answer = test_answer
        case_log.test_result = self.test_result
        case_log.score = score
        case_log.right_answer = self.right_answer
        case_log.question = self.question
        case_log.citations = citations
        case_log.elapsed_time = elapsed_time
        case_log.test_plan_id = test_plan_id
        case_log.test_report_id = test_report_id
        case_log.evaluation_llm_id = evaluation_llm_id
        case_log.evaluation_prompt_id = evaluation_prompt_id
        case_log.workflow_log_id = current_workflow_log_id
        case_log.workflow_node_log_id = workflow_node_log_id
        case_log.unit_llm_id = unit_llm_id
        case_log.execute_llm_name = execute_llm_name
        case_log.execute_workflow_name = execute_workflow_name
        case_log.error_msg = error_msg
        self.test_case_logs.append(case_log)
        self.test_result_answer = test_answer
        if test_report:
            test_report.update()
            if test_report.case_count == test_report.test_pass_count + test_report.test_fail_count:
                test_plan = TestPlan.get(test_plan_id)
                test_plan.state = TestPlanState.测试完成.value
                test_plan.update()
                TestPlanTasking.remove_plan(test_plan_id)
        self.update(True)
        
    @classmethod
    def check_case_execute(cls, case: 'TestCase', select_workflow_id: int|None, is_forced: bool = False):
        if select_workflow_id is None:
            return
        flow_inputs = WorkFlow.get_workflow_inputs(select_workflow_id)
        flow_inputs_keys = list(flow_inputs.keys())
        if is_forced:
            if len(flow_inputs_keys) > 1:
                raise ValidationException("选择的工作流入参数量大于1，参数不符，请选择单一入参")
            return

        if case is None:
            if len(flow_inputs_keys) > 1:
                raise ValidationException("选择的工作流入参数量大于1，参数不符，请选择单一入参")
            return
        if case.workflow_id is None:
            if len(flow_inputs_keys) > 1:
                raise ValidationException("选择的工作流入参数量大于1，参数不符，请选择单一入参")

    @classmethod
    def get_case_cates_by_workflow_log_ids(cls, log_ids: list[int]):
        testcase= cls.query.filter(cls.workflow_log_id.in_(log_ids)).all()
        test_cates={}
        for item in testcase:
            cate_list = test_cates.setdefault(str(item.workflow_log_id), [])
            if item.test_cate:
                cate_list.append({"cate_id": item.test_cate.id, "color": item.test_cate.color, "name": item.test_cate.name, "tag": item.tag, "node_id": item.workflow_node_log_id})
            else:
                cate_list.append({"cate_id": None, "color": "red", "name": "未分类", "tag": item.tag, "node_id": item.workflow_node_log_id})
        return test_cates

    @classmethod
    def is_exist_workflow_log(cls, test_cate_id: int, workflow_log_id: int):
        """检查用例是否存在"""
        if workflow_log_id is None or workflow_log_id == 0:
            return False, None
        if test_cate_id == 0:
            test_cate_id = None
        if test_cate_id is None:
            test_case = cls.query.filter(cls.workflow_log_id == workflow_log_id, cls.test_cate_id.is_(None)).first()
        else:
            test_case = cls.query.filter(cls.workflow_log_id == workflow_log_id, cls.test_cate_id == test_cate_id).first()
        if test_case is None:
            return False, None
        if test_case.test_cate is None:
            return True, '未分类'
        return True, test_case.test_cate.name

    # 添加流程单元测试用例
    @classmethod
    def case_add_unit(cls, cate_id: int | None, workflow_node_log_id: int | None,note:str|None):
        if cate_id is not None and cate_id <= 0:
            cate_id = None
        is_exist, cate_name = cls.is_exist_workflow_node_log(cate_id, workflow_node_log_id)
        if is_exist:
            raise ValidationException(f"工作流节点日志在类别【{cate_name}】下已存在，不能重复添加")
        model = TestCase(workflow_node_log_id=workflow_node_log_id)
        if cate_id is not None:
            model.test_cate_id = cate_id
        node_log = WorkFlowRunNodeLog.get(workflow_node_log_id)
        model.question = node_log.prompt_str
        model.right_answer = node_log.response_content
        model.workflow_node_log_id = workflow_node_log_id
        model.workflow_log_id = node_log.run_log.id
        model.workflow_id = node_log.run_log.flow_id
        model.vision_file_str = node_log.vision_file_str
        model.note = note
        model.tag = 'S'
        model.add(True)
        return model

    @classmethod
    def is_exist_workflow_node_log(cls, test_cate_id: int | None, workflow_node_log_id: int | None):
        if workflow_node_log_id is None or workflow_node_log_id <= 0:
            raise ValidationException("流程节点日志id不能为空")
        if test_cate_id is None or test_cate_id <= 0:
            test_cate_id = None
        if test_cate_id is None:
            test_case = cls.query.filter(cls.workflow_node_log_id == workflow_node_log_id, cls.test_cate_id.is_(None)).first()
        else:
            test_case = cls.query.filter(cls.workflow_node_log_id == workflow_node_log_id, cls.test_cate_id == test_cate_id).first()
        if test_case is None:
            return False, None
        if test_case.test_cate is None:
            return True, '未分类'
        return True, test_case.test_cate.name

    @classmethod
    def case_move_cate(cls, source_cate_id: Optional[int], target_cate_id: Optional[int], tag='S'):
        """移动用例分类"""
        if source_cate_id is not None and source_cate_id <= 0:
            source_cate_id = None
        if target_cate_id is not None and target_cate_id <= 0:
            target_cate_id = None
        if source_cate_id == target_cate_id:
            raise ValidationException("同分类不可以移动")
        source_cate_name = '未分类' if source_cate_id is None else TestCate.get(source_cate_id).name
        target_cate_name = '未分类' if target_cate_id is None else TestCate.get(target_cate_id).name
        source_case = aliased(cls, name='source_case')
        target_case = aliased(cls, name='target_case')
        this_session = cls().session
        if tag == 'S':
            conflict_query = (this_session.query(*(source_case.id, source_case.workflow_node_log_id,
                                                   target_case.id, target_case.workflow_node_log_id))
                              .select_from(target_case)
                              .join(source_case,
                                    (source_case.workflow_node_log_id == target_case.workflow_node_log_id) &
                                    (source_case.test_cate_id == source_cate_id)
                                    ).filter(target_case.test_cate_id == target_cate_id,
                                             target_case.deleted_at.is_(None),
                                             source_case.deleted_at.is_(None))
                              )
        else:
            conflict_query = (this_session.query(*(source_case.id, source_case.workflow_log_id,
                                                   target_case.id, target_case.workflow_log_id))
                              .select_from(target_case)
                              .join(source_case,
                                    (source_case.workflow_log_id == target_case.workflow_log_id) &
                                    (source_case.test_cate_id == source_cate_id)
                                    ).filter(target_case.test_cate_id == target_cate_id,
                                             target_case.deleted_at.is_(None),
                                             source_case.deleted_at.is_(None))
                              )

        conflict_details = conflict_query.all()
        source_ids = [item[0] for item in conflict_details]
        update_data = this_session.query(cls).filter(cls.test_cate_id == source_cate_id, cls.id.notin_(source_ids))
        update_data.update(
            {cls.test_cate_id: target_cate_id},
            synchronize_session=False
        )
        this_session.commit()

        if conflict_details:
            conflict_message = f"以下用例在目标类目【{target_cate_name}】中已存在，请先删除或者移动：\n"
            for detail in conflict_details:
                conflict_message += f"【源用例ID:{detail[0]}-目标ID:{detail[2]}】\n"
            raise ValidationException(conflict_message)


class TestCaseLog(BaseModel):
    """测试用例日志"""
    test_case_id = mapped_column(Integer, ForeignKey('test_case.id'), nullable=False)
    test_case = relationship("TestCase", back_populates="test_case_logs")
    question = mapped_column(String(2000), comment='问题')
    right_answer = mapped_column(String(4000), comment='正确回答')
    test_answer = mapped_column(String(4000), comment='测试回答')
    test_result = mapped_column(Integer, default=TestCaseResultType.未测试.value, comment='测试结果')
    score = mapped_column(String(20), comment='反馈分数')
    citations = mapped_column(Text, comment='引用')
    elapsed_time = mapped_column(String(50), comment='耗时')
    test_plan_id = mapped_column(Integer, comment='测试计划id')
    test_report_id = mapped_column(Integer, comment='测试报告id')
    evaluation_llm_id = mapped_column(Integer, comment='评估llm id', nullable=True)
    evaluation_prompt_id = mapped_column(Integer, comment='评估提示词 id', nullable=True)
    workflow_log_id = mapped_column(Integer, comment='工作流日志id', nullable=True)
    workflow_node_log_id = mapped_column(Integer, comment='工作流运行节点id', nullable=True)
    unit_llm_id = mapped_column(Integer, comment='执行大模型名称 id', nullable=True)
    execute_llm_name = mapped_column(String(100), comment='执行大模型名称')
    execute_workflow_name = mapped_column(String(100), comment='执行工作流名称')
    error_msg = mapped_column(String(1000), comment='错误信息')

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id} deleted={bool(self.deleted_at)}>"

    @classmethod
    def get_pagination(cls, page: int, pagesize: int, result_type: Optional[TestCaseResultType], *args, **kwargs):
        if page <= 0:
            page = 1
        if pagesize <= 0:
            pagesize = 10
        if result_type is not None and result_type != TestCaseResultType.默认:
            report_logs = cls.query.filter(cls.test_result == result_type.value)
        else:
            report_logs = cls.query
        if args:
            report_logs = report_logs.filter(*args)
        if kwargs:
            report_logs = report_logs.filter_by(**kwargs)
        total_records = report_logs.count()
        if total_records == 0:
            return {"total_records": 0, "total_pages": 0, "rows": []}
        total_pages = (total_records + pagesize - 1) // pagesize
        report_logs = report_logs.order_by(cls.id.desc()).offset((page - 1) * pagesize).limit(pagesize).all()
        evaluation_llm_ids = list(set([report_log.evaluation_llm_id for report_log in report_logs]))
        evaluation_prompt_ids = list(set([report_log.evaluation_prompt_id for report_log in report_logs]))
        evaluation_llms = ModelConfig.query.filter(ModelConfig.id.in_(evaluation_llm_ids)).all()
        evaluation_prompts = PromptModel.query.filter(PromptModel.id.in_(evaluation_prompt_ids)).all()
        rows = []
        for report_log in report_logs:
            current_evaluation_llm = next((llm.name for llm in evaluation_llms if report_log.evaluation_llm_id and llm.id == report_log.evaluation_llm_id), None)
            current_evaluation_prompt = next((prompt.name for prompt in evaluation_prompts if report_log.evaluation_prompt_id and prompt.id == report_log.evaluation_prompt_id), None)
            rows.append(
                {
                    "id": report_log.id,
                    "elapsed_time": report_log.elapsed_time,
                    "question": report_log.question,
                    "right_answer": report_log.right_answer,
                    "score": report_log.score,
                    "test_answer": report_log.test_answer,
                    "test_case_id": report_log.test_case_id,
                    "test_plan_id": report_log.test_plan_id,
                    "test_report_id": report_log.test_report_id,
                    "test_result": report_log.test_result,
                    # "citations": report_log.citations,
                    "citations": None,
                    "workflow_log_id": report_log.workflow_log_id,
                    # "testcase_id": report_log.test_case.id,
                    "testcase_workflow_log_id": report_log.test_case.workflow_log_id,
                    "evaluation_llm_id": report_log.evaluation_llm_id,
                    "evaluation_llm_name": current_evaluation_llm if current_evaluation_llm else None,
                    "evaluation_prompt_id": report_log.evaluation_prompt_id,
                    "evaluation_prompt_name": current_evaluation_prompt if current_evaluation_prompt else None,
                    "unit_llm_id": report_log.unit_llm_id,
                    "execute_llm_name": report_log.execute_llm_name,
                    "execute_workflow_name": report_log.execute_workflow_name,
                    "created_at": report_log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_at": report_log.updated_at.strftime("%Y-%m-%d %H:%M:%S") if report_log.updated_at else None
                }
            )
        return {"total_records": total_records, "total_pages": total_pages, "rows": rows}


class TestCaseCitation(BaseModel):
    """测试用例引用"""
    test_case_id = mapped_column(Integer, ForeignKey('test_case.id'), nullable=False)
    test_case = relationship("TestCase", back_populates="test_case_citations")
    type = mapped_column(String(200), comment='引用类型')
    title = mapped_column(String(200), comment='标题')
    ref_id = mapped_column(String(50), comment='引用id')

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id} deleted={bool(self.deleted_at)}>"


class TrainCase(BaseModel):
    """训练用例"""
    train_cate_id = mapped_column(Integer, ForeignKey('train_cate.id'), comment='训练分类id')
    train_cate=relationship("TrainCate", back_populates="train_cases")
    input_data = mapped_column(Text, comment='输入数据')
    output_data = mapped_column(Text, comment='输出数据')
    workflow_id = mapped_column(Integer, comment='工作流id', nullable=True)
    workflow_log_id = mapped_column(Integer, comment='工作流日志id', nullable=True)
    workflow_node_log_id = mapped_column(Integer, comment='工作流运行节点id', nullable=True)
    is_marked = mapped_column(Boolean, default=False, comment='是否已经标记')
    is_modified = mapped_column(Boolean, default=False, comment='是否已经修改')
    feature = mapped_column(String(2000), default=None, comment='特征概要')
    test_case_id = mapped_column(Integer, default=None, comment='单元测试用例id')
    vision_file_str = mapped_column(Text, comment='视觉模型文件路径', nullable=True)

    @classmethod
    def get_pagination(cls, page: int, pagesize: int, *args, **kwargs):
        if page <= 0:
            page = 1
        if pagesize <= 0:
            pagesize = 10
        cases = cls.query
        if args:
            cases = cases.filter(*args)
        if kwargs:
            cases = cases.filter_by(**kwargs)
        total_records = cases.count()
        if total_records == 0:
            return {"total_records": 0, "total_pages": 0, "rows": []}
        total_pages = (total_records + pagesize - 1) // pagesize
        cases = cases.order_by(cls.id.desc()).offset((page - 1) * pagesize).limit(pagesize).all()
        return {
            "total_records": total_records,
            "total_pages": total_pages,
            "rows": [
                {
                    "id": item.id,
                    "input_data": item.input_data,
                    "output_data": item.output_data,
                    "train_cate_id": item.train_cate_id,
                    "train_cate_name": item.train_cate.name if item.train_cate else "未分类",
                    "train_cate_color": item.train_cate.color if item.train_cate else "red",
                    "is_marked": item.is_marked,
                    "is_modified": item.is_modified,
                    "workflow_id": item.workflow_id,
                    "workflow_log_id": item.workflow_log_id,
                    "workflow_node_log_id": item.workflow_node_log_id,
                    "vision_file_str": item.vision_file_str,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                    "feature": item.feature,
                } for item in cases
            ]
        }

    @classmethod
    def add_train(cls, train_cate_id, node_id, input_data, output_data, is_marked, is_modified, feature, test_case_id):
        train_cate_id = train_cate_id if train_cate_id and train_cate_id > 0 else None
        node_id = node_id if node_id and node_id > 0 else None
        feature = feature.strip() if feature and isinstance(feature, str) else None
        if feature is None:
            raise ValidationException("特征概要不能为空")
        if train_cate_id is not None:
            TrainCate.get(train_cate_id)
        workflow_id = workflow_log_id = vision_file_str = None
        if node_id is not None:
            is_exist, cate_name = cls.is_exist_workflow_node_log(train_cate_id, node_id)
            if is_exist:
                raise ValidationException(f"在类别【{cate_name}】下已存在，不能重复添加")
            current_node = WorkFlowRunNodeLog.get(node_id)
            workflow_id = current_node.run_log.flow_id
            workflow_log_id = current_node.run_log.id
            vision_file_str = current_node.vision_file_str
        train_case = cls(train_cate_id=train_cate_id, input_data=input_data, output_data=output_data)
        train_case.feature = feature
        train_case.test_case_id = test_case_id
        train_case.workflow_node_log_id = node_id
        train_case.workflow_id = workflow_id
        train_case.workflow_log_id = workflow_log_id
        train_case.vision_file_str = vision_file_str
        train_case.is_marked = False if is_marked is None else is_marked
        train_case.is_modified = False if is_modified is None else is_modified
        train_case.add(True)
        return train_case

    def edit_train(self, train_cate_id, input_data, output_data, is_marked, is_modified, feature):
        train_cate_id = train_cate_id if train_cate_id and train_cate_id > 0 else None
        feature = feature.strip() if feature and isinstance(feature, str) else None
        if feature is None:
            raise ValidationException("特征概要不能为空")
        if self.train_cate_id != train_cate_id:
            if train_cate_id is not None:
                TrainCate.get(train_cate_id)
            if self.workflow_node_log_id is not None and self.workflow_node_log_id > 0:
                is_exist, cate_name = self.is_exist_workflow_node_log(train_cate_id, self.workflow_node_log_id)
                if is_exist:
                    raise ValidationException(f"在类别【{cate_name}】下已存在，不能重复添加")
        self.input_data = input_data
        self.output_data = output_data
        self.feature = feature
        self.is_marked = False if is_marked is None else is_marked
        self.is_modified = False if is_modified is None else is_modified

        if self.train_cate_id == train_cate_id:
            self.update(True)
        elif train_cate_id is None:
            self.train_cate_id = None
            self.update_with_foreign_key_none(True)
        else:
            self.train_cate_id = train_cate_id
            self.update(True)

    @classmethod
    def get_cate_by_workflow_log_ids(cls, log_ids: list[int]):
        """获取节点所对应的训练分类"""
        traincases= cls.query.filter(cls.workflow_log_id.in_(log_ids)).all()
        train_cates={}
        for item in traincases:
            cate_list = train_cates.setdefault(str(item.workflow_log_id), [])
            if item.train_cate:
                cate_list.append({"cate_id": item.train_cate.id, "color": item.train_cate.color, "name": item.train_cate.name, "node_id": item.workflow_node_log_id})
            else:
                cate_list.append({"cate_id": None, "color": "red", "name": "未分类", "node_id": item.workflow_node_log_id})
        return train_cates

    @classmethod
    def is_exist_workflow_node_log(cls, train_cate_id: int, node_id: int):
        """检查用例是否存在"""
        if node_id is None or node_id == 0:
            return False, None
        if train_cate_id == 0:
            train_cate_id = None
        if train_cate_id is None:
            train_case = cls.query.filter(cls.workflow_node_log_id == node_id, cls.train_cate_id.is_(None)).first()
        else:
            train_case = cls.query.filter(cls.workflow_node_log_id == node_id, cls.train_cate_id == train_cate_id).first()
        if train_case is None:
            return False, None
        if train_case.train_cate is None:
            return True, '未分类'
        return True, train_case.train_cate.name

    @classmethod
    def marked(cls, ids: list[int], is_marked: bool):
        """标记训练用例"""
        models = cls.query.filter(cls.id.in_(ids)).all()
        for model in models:
            if model.is_marked == is_marked:
                raise ValidationException(f"[{model.id}]已经标记为【{'已标记' if is_marked else '未标记'}】，不能重复操作")
            model.is_marked = is_marked
            model.update(True)

    @classmethod
    def move_cate(cls, source_cate_id: Optional[int], target_cate_id: Optional[int]):
        """移动训练分类"""
        if source_cate_id is not None and source_cate_id <= 0:
            source_cate_id = None
        if target_cate_id is not None and target_cate_id <= 0:
            target_cate_id = None
        if source_cate_id == target_cate_id:
            raise ValidationException("同分类不可以移动")
        source_cate_name = '未分类' if source_cate_id is None else TrainCate.get(source_cate_id).name
        target_cate_name = '未分类' if target_cate_id is None else TrainCate.get(target_cate_id).name
        source_train = aliased(cls, name='source_train')
        target_train = aliased(cls, name='target_train')
        this_session = cls().session
        conflict_query = (this_session.query(*(source_train.id, source_train.workflow_node_log_id,
                                               target_train.id, target_train.workflow_node_log_id))
                          .select_from(target_train)
                          .join(source_train,
                                (source_train.workflow_node_log_id == target_train.workflow_node_log_id) &
                                (source_train.train_cate_id == source_cate_id))
                          .filter(target_train.train_cate_id == target_cate_id,
                                  target_train.deleted_at.is_(None), source_train.deleted_at.is_(None))
                          )
        conflict_details = conflict_query.all()
        source_ids = [item[0] for item in conflict_details]
        update_data = this_session.query(cls).filter(cls.train_cate_id == source_cate_id, cls.id.notin_(source_ids))
        update_data.update(
            {cls.train_cate_id: target_cate_id},
            synchronize_session=False
        )
        this_session.commit()
        if conflict_details:
            conflict_message = f"以下训练用例在目标类目【{target_cate_name}】中已存在，请先删除或者移动：\n"
            for detail in conflict_details:
                conflict_message += f"【源训练ID:{detail[0]}-目标ID:{detail[2]}】\n"
            raise ValidationException(conflict_message)

    @classmethod
    def get_relation_unit_case(cls, ids: list[int]):
        """获取训练数据，关联的单元测试用例,
        1，根据用例的workflow_node_log_id进行关联
        2，根据用户自动写入的test_case_id进行关联---function_train_case.py
        """
        trains = cls.query.filter(cls.id.in_(ids)).all()

        flow_node_log_ids = [train.workflow_node_log_id for train in trains if train.workflow_node_log_id is not None]
        test_case_ids = [train.test_case_id for train in trains if train.test_case_id is not None]

        flow_unit_cases = []
        test_unit_cases = []

        if len(flow_node_log_ids) > 0:
            flow_unit_cases = TestCase.query.filter(TestCase.tag == 'S', TestCase.workflow_node_log_id.in_(flow_node_log_ids)).all()

        if len(test_case_ids) > 0:
            test_unit_cases = TestCase.query.filter(TestCase.id.in_(test_case_ids)).all()

        seen = set()
        rows = []
        for train in trains:
            current_flow_unit_cases = [case for case in flow_unit_cases if case.workflow_node_log_id == train.workflow_node_log_id]
            for case in current_flow_unit_cases:
                key = (train.id, case.id)
                if key in seen:
                    continue
                seen.add(key)
                rows.append({
                    "train_case_id": train.id,
                    "workflow_node_log_id": train.workflow_node_log_id,
                    "case_id": case.id,
                    "case_cate_id": case.test_cate_id,
                    "case_cate_name": case.test_cate.name if case.test_cate else "未分类",
                    "case_cate_color": case.test_cate.color if case.test_cate else "red",
                })
            current_test_unit_cases = [case for case in test_unit_cases if case.id == train.test_case_id]
            for case in current_test_unit_cases:
                key = (train.id, case.id)
                if key in seen:
                    continue
                seen.add(key)
                rows.append({
                    "train_case_id": train.id,
                    "workflow_node_log_id": train.workflow_node_log_id,
                    "case_id": case.id,
                    "case_cate_id": case.test_cate_id,
                    "case_cate_name": case.test_cate.name if case.test_cate else "未分类",
                    "case_cate_color": case.test_cate.color if case.test_cate else "red",
                })
        return {"rows": rows}


class TestPlan(BaseModel):
    """测试计划"""
    cate_count = mapped_column(Integer, comment='用例库数量')
    case_count = mapped_column(Integer, comment='用例数量')
    run_count = mapped_column(Integer, comment='运行次数')
    state = mapped_column(Integer, default=TestPlanState.准备就绪.value, comment='测试计划状态')
    run_time = mapped_column(DateTime, comment='最后执行时间')
    test_reports = relationship("TestReport", back_populates="test_plan", cascade='all', lazy='dynamic', uselist=True)
    test_plan_cate_maps = relationship("TestPlanCateMap", back_populates="test_plan", cascade='all', lazy='dynamic', uselist=True)
    test_plan_case_maps = relationship("TestPlanCaseMap", back_populates="test_plan", cascade='all', lazy='dynamic', uselist=True)
    workflow_id = mapped_column(Integer, comment='流程id')
    evaluation_llm_id = mapped_column(Integer, comment='评估llm id', nullable=True)
    evaluation_prompt_id = mapped_column(Integer, comment='评估提示词 id', nullable=True)
    is_forced = mapped_column(Boolean, default=False, comment='是否强制按照选择的流程执行', nullable=False)
    tag = mapped_column(String(2), default='W', comment='标签[S:单元测试  W:流程测试]')
    unit_llm_id = mapped_column(Integer, comment='单元测试llm id', nullable=True)
    error_msg = mapped_column(Text, comment='错误信息')

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id} deleted={bool(self.deleted_at)}>"

    @classmethod
    def plan_add(cls, name, caption, note, workflow_id, evaluation_llm_id, evaluation_prompt_id, is_forced, unit_llm_id, tag):
        plan_model = cls(
            name=name,
            caption=caption,
            note=note,
            workflow_id=workflow_id,
            evaluation_llm_id=evaluation_llm_id,
            evaluation_prompt_id=evaluation_prompt_id,
            is_forced=is_forced,
            state=TestPlanState.准备就绪.value,
            cate_count=0,
            case_count=0,
            unit_llm_id=unit_llm_id,
            tag=tag
        )
        plan_model.add(True)
        return plan_model

    def plan_edit(self, name, caption, note, workflow_id, evaluation_llm_id, evaluation_prompt_id, is_forced, unit_llm_id):
        if self.state == TestPlanState.测试中.value:
            raise ValidationException(f"测试计划{self.id}正在执行中，无法编辑")
        self.state = TestPlanState.准备就绪.value
        self.name = name
        self.caption = caption
        self.note = note
        self.workflow_id = workflow_id
        self.evaluation_llm_id = evaluation_llm_id
        self.evaluation_prompt_id = evaluation_prompt_id
        self.is_forced = is_forced
        self.unit_llm_id = unit_llm_id
        self.update(True)

    def plan_relation_cate_maps(self, param_cate_ids: list[int]):
        """添加测试计划分类"""
        if self.state == TestPlanState.测试中.value:
            raise ValidationException("测试计划执行中，不能关联用例库")
        if param_cate_ids is None or len(param_cate_ids) == 0:
            self.test_plan_cate_maps = []
            self.cate_count = 0
            self.update(True)
            return
        cate_models = TestCate.query.filter(TestCate.id.in_(param_cate_ids)).all()
        exist_cate_ids = [cate.id for cate in cate_models]
        if 0 in param_cate_ids:
            exist_cate_ids.append(0)
            none_cate_models = TestCate.query.filter(TestCate.pid.is_(None)).all()
            cate_models.extend(none_cate_models)
        not_exist_cate_ids = list(set(param_cate_ids) - set(exist_cate_ids))
        if not_exist_cate_ids:
            raise ValidationException(f"测试分类id【{not_exist_cate_ids}】不存在")
        cate_maps_remove = []
        cate_maps_add = []

        exist_cate_ids = [cate.test_cate_id for cate in self.test_plan_cate_maps if self.test_plan_cate_maps is not None]
        if not exist_cate_ids:
            exist_cate_ids = []

        for cate_map_id in exist_cate_ids:
            if cate_map_id not in param_cate_ids:
                cate_maps_remove.append(cate_map_id)
        for param_cate_id in param_cate_ids:
            if param_cate_id not in exist_cate_ids:
                cate_maps_add.append(param_cate_id)
        if cate_maps_remove and cate_maps_remove != []:
            self._remove_cate_map(cate_maps_remove)
        if cate_maps_add and cate_maps_add != []:
            self._add_cate_map(cate_maps_add)
        self.cate_count = len(list(set(param_cate_ids)))
        self.update(True)

    def _remove_cate_map(self, param_cate_ids: list[int]):
        """删除测试计划分类映射"""
        tmp_maps = [obj for obj in self.test_plan_cate_maps if obj.test_cate_id in param_cate_ids]
        if tmp_maps:
            for item in tmp_maps:
                self.test_plan_cate_maps.remove(item)

    def _add_cate_map(self, param_cate_ids: list[int]):
        """添加测试计划分类映射"""
        for param_cate_id in param_cate_ids:
            test_plan_cate_map = TestPlanCateMap()
            test_plan_cate_map.test_plan_id = self.id
            test_plan_cate_map.test_cate_id = param_cate_id
            self.test_plan_cate_maps.append(test_plan_cate_map)

    def plan_relation_case_maps(self, param_case_ids: list[int]):
        """添加测试计划用例"""
        if self.state == TestPlanState.测试中.value:
            raise ValidationException("测试计划执行中，不能关联用例")
        if param_case_ids is None or param_case_ids == []:
            self.test_plan_case_maps = []
            self.case_count = 0
            self.update(True)
            return
        case_models = TestCase.query.filter(TestCase.id.in_(param_case_ids)).all()
        exist_case_ids = [case.id for case in case_models]
        not_exist_case_ids = list(set(param_case_ids) - set(exist_case_ids))
        if not_exist_case_ids:
            raise ValidationException(f"测试用例id【{not_exist_case_ids}】不存在")
        case_maps_remove = []
        case_maps_add = []

        exist_case_ids = [case.test_case_id for case in self.test_plan_case_maps if self.test_plan_case_maps is not None]
        if not exist_case_ids:
            exist_case_ids = []

        for case_map_id in exist_case_ids:
            if case_map_id not in param_case_ids:
                case_maps_remove.append(case_map_id)
        for param_case_id in param_case_ids:
            if param_case_id not in exist_case_ids:
                case_maps_add.append(param_case_id)
        if case_maps_remove and case_maps_remove != []:
            self._remove_case_map(case_maps_remove)
        if case_maps_add and case_maps_add != []:
            self._add_case_map(case_maps_add)
        self.case_count = len(param_case_ids)
        self.update(True)

    def _remove_case_map(self, param_case_ids: list[int]):
        """删除测试计划用例映射"""
        tmp_maps = [obj for obj in self.test_plan_case_maps if obj.test_case_id in param_case_ids]
        if tmp_maps:
            for item in tmp_maps:
                self.test_plan_case_maps.remove(item)

    def _add_case_map(self, param_case_ids: list[int]):
        """添加测试计划用例映射"""
        for param_case_id in param_case_ids:
            test_plan_case_map = TestPlanCaseMap()
            test_plan_case_map.test_plan_id = self.id
            test_plan_case_map.test_case_id = param_case_id
            self.test_plan_case_maps.append(test_plan_case_map)

    def plan_add_report(self, plan_name: Optional[str] = None):
        """添加测试报告"""
        self.run_time = datetime.now()
        test_report = TestReport()
        test_report.test_plan_id = self.id
        test_report.case_count = self.plan_cases().__len__()
        if self.tag == 'S':
            test_report.case_count = [case for case in self.plan_cases() if case.tag == 'S'].__len__()
        elif self.tag == 'W':
            test_report.case_count = [case for case in self.plan_cases() if case.tag == 'W'].__len__()
        test_report.test_pass_count = 0
        test_report.test_fail_count = 0
        test_report.evaluation_llm_id = self.evaluation_llm_id
        test_report.evaluation_prompt_id = self.evaluation_prompt_id
        report_time = self.run_time.strftime("%Y-%m-%d %H:%M:%S") if self.run_time else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if plan_name is not None:
            test_report.name = plan_name
        else:
            test_report.name = f'{self.name}({report_time})测试报告'
        self.test_reports.append(test_report)
        if self.run_count is None:
            self.run_count = 0
        self.run_count += 1
        self.session.flush()
        self.update(True)
        return test_report

    def plan_cases(self):
        """获取当前测试计划所有用例 0：代表未分类"""
        cases_dict = {}
        if self.test_plan_case_maps is not None and self.test_plan_case_maps != []:
            case_map_ids = [case_map.test_case_id for case_map in self.test_plan_case_maps]
            tmp_cases = TestCase.query.filter(TestCase.id.in_(case_map_ids)).all()
            for case in tmp_cases:
                if case.id not in cases_dict:
                    cases_dict[case.id] = case
        if self.test_plan_cate_maps is not None and self.test_plan_cate_maps != []:
            cate_map_ids = [cate_map.test_cate_id for cate_map in self.test_plan_cate_maps]
            tmp_cases = TestCase.query.filter(TestCase.test_cate_id.in_(cate_map_ids)).all()
            if 0 in cate_map_ids:
                none_cases = TestCase.query.filter(TestCase.test_cate_id.is_(None)).all()
                tmp_cases.extend(none_cases)
            for case in tmp_cases:
                if case.id not in cases_dict:
                    cases_dict[case.id] = case
        return list(cases_dict.values())

    def get_last_report_case_ids(self):
        """获取上一次测试报告的用例id列表"""
        last_report_id = 0
        if self.test_reports.all() is not None and len(self.test_reports.all()) > 0:
            # 获取最新的第二条测试报告 因为先生成的报告
            last_reports = self.test_reports.order_by(TestReport.id.desc()).all()
            if len(last_reports) >= 2:
                last_report_id = last_reports[1].id

        if last_report_id == 0:
            return []
        last_report_logs = (TestCaseLog().session.query(TestCaseLog.test_case_id, TestCaseLog.test_report_id, TestCaseLog.test_plan_id)
                            .filter_by(test_plan_id=self.id, test_report_id=last_report_id)
                            .all())
        last_report_case_ids = [log.test_case_id for log in last_report_logs]
        return last_report_case_ids

    def plan_reports(self):
        """获取测试计划报告"""
        reports = self.test_reports.order_by(TestReport.id.desc()).all()
        rows = []
        for report in reports:
            rows.append({
                "report_id": report.id,
                "name": report.name,
                "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": report.updated_at.strftime("%Y-%m-%d %H:%M:%S") if report.updated_at else None
            })
        return rows

    @classmethod
    def get_pagination(cls, page: int, pagesize: int,  *args, **kwargs):
        if page <= 0:
            page = 1
        if pagesize <= 0:
            pagesize = 10
        plans = cls.query
        if args:
            plans = plans.filter(*args)
        if kwargs:
            plans = plans.filter_by(**kwargs)
        total_records = plans.count()
        if total_records == 0:
            return {"total_records": 0, "total_pages": 0, "rows": []}
        total_pages = (total_records + pagesize - 1) // pagesize
        plans = plans.order_by(cls.id.desc()).offset((page - 1) * pagesize).limit(pagesize).all()
        evaluation_prompt_ids = list(set([plan.evaluation_prompt_id for plan in plans]))
        evaluation_prompts = PromptModel.query.filter(PromptModel.id.in_(evaluation_prompt_ids)).all()
        continue_plans = TestPlanContinueTasking.load_plan()

        rows = []
        for plan in plans:
            current_prompt_name = next((prompt.name for prompt in evaluation_prompts if plan.evaluation_prompt_id and prompt.id == plan.evaluation_prompt_id), None)
            current_continue_plan = next((plan_id for plan_id in continue_plans if plan_id == plan.id), None)
            rows.append({
                "id": plan.id,
                "name": plan.name,
                "caption": plan.caption,
                "note": plan.note,
                "workflow_id": plan.workflow_id,
                "evaluation_llm_id": plan.evaluation_llm_id,
                "evaluation_prompt_id": plan.evaluation_prompt_id,
                "evaluation_prompt_name": current_prompt_name,
                "is_forced": plan.is_forced,
                "state": get_enum_name(TestPlanState, plan.state),
                "cate_count": plan.cate_count if plan.cate_count else 0,
                "case_count": plan.case_count if plan.case_count else 0,
                "created_at": plan.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": plan.updated_at.strftime("%Y-%m-%d %H:%M:%S") if plan.updated_at else None,
                "run_time": plan.run_time.strftime("%Y-%m-%d %H:%M:%S") if plan.run_time else None,
                "report_id": plan.test_reports.order_by(TestReport.id.desc()).first().id if plan.test_reports is not None and plan.test_reports.count() > 0 else 0,
                "tag": plan.tag,
                "unit_llm_id": plan.unit_llm_id,
                "error_msg": plan.error_msg,
                "is_continue": True if current_continue_plan is not None else False,
            })
        return {"total_records": total_records, "total_pages": total_pages, "rows": rows}

    def get_relation_cate_cases(self):
        """获取关联的用例分类，和用例"""
        cate_ids = [map_cate.test_cate_id for map_cate in self.test_plan_cate_maps]
        case_ids = [case.test_case_id for case in self.test_plan_case_maps]
        case_models = TestCase.query.filter(TestCase.id.in_(case_ids)).all()
        return {"relation_cate_ids": cate_ids, "relation_case_ids": case_ids, "case_models": case_models}



class TestReport(BaseModel):
    """测试报告"""
    test_plan_id = mapped_column(Integer, ForeignKey('test_plan.id'), comment='测试计划id')
    test_plan = relationship("TestPlan", back_populates="test_reports")
    case_count = mapped_column(Integer, comment='用例数量')
    test_pass_count = mapped_column(Integer, comment='计划通过次数', default=0)
    test_fail_count = mapped_column(Integer, comment='计划失败次数', default=0)
    evaluation_llm_id = mapped_column(Integer, comment='评估llm id', nullable=True)
    evaluation_prompt_id = mapped_column(Integer, comment='评估提示词 id', nullable=True)

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id} deleted={bool(self.deleted_at)}>"

    @classmethod
    def get_pagination(cls, page: int, pagesize: int, plan_id: Optional[int], *args, **kwargs):
        """获取分页数据"""
        if page <= 0:
            page = 1
        if pagesize <= 0:
            pagesize = 10
        if plan_id is not None and plan_id > 0:
            query = cls.query.filter(cls.test_plan_id == plan_id)
        else:
            query = cls.query
        if args:
            query = query.filter(*args)
        if kwargs:
            query = query.filter_by(**kwargs)
        total_records = query.count()
        if total_records == 0:
            return {"total_records": 0, "total_pages": 0, "rows": []}
        total_pages = (total_records + pagesize - 1) // pagesize
        query = query.order_by(cls.id.desc()).offset((page - 1) * pagesize).limit(pagesize).all()
        return {
            "total_records": total_records,
            "total_pages": total_pages,
            "rows": [
                {
                    "id": item.id,
                    "name": item.name,
                    "plan_name": item.test_plan.name,
                    "execute_count": item.case_count,
                    "test_pass_count": item.test_pass_count,
                    "test_fail_count": item.test_fail_count,
                    "create_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "update_at": item.updated_at.strftime("%Y-%m-%d %H:%M:%S") if item.updated_at else None
                } for item in query
            ]
        }


class TestPlanCateMap(BaseModel):
    """测试计划分类映射"""
    test_plan_id = mapped_column(Integer, ForeignKey('test_plan.id'), comment='测试计划id')
    test_plan = relationship("TestPlan", back_populates="test_plan_cate_maps")
    test_cate_id = mapped_column(Integer, comment='测试分类id')
    # test_cate = relationship("TestCate", back_populates="test_plan_cate_maps")

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id} deleted={bool(self.deleted_at)}>"


class TestPlanCaseMap(BaseModel):
    """测试计划用例映射"""
    test_plan_id = mapped_column(Integer, ForeignKey('test_plan.id'), comment='测试计划id')
    test_plan = relationship("TestPlan", back_populates="test_plan_case_maps")
    test_case_id = mapped_column(Integer, comment='测试用例id')
    # test_case = relationship("TestCase", back_populates="test_plan_case_maps")

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id} deleted={bool(self.deleted_at)}>"


class WorkFlowCategory(BaseModel):
    """流程分类"""
    pid: Mapped[Optional[int]] = mapped_column(Integer, default=None, comment="流程分类父id")

    @classmethod
    def tree(cls):
        """获取分类树"""
        categories = cls.query.all()
        tree_data = []
        parent_categories = [item for item in categories if item.pid is None]
        for parent_category in parent_categories:
            tree_data.append({
                "id": parent_category.id,
                "name": parent_category.name,
                "pid": parent_category.pid,
                "children": cls._recursion(categories, parent_category.id)
            })
        return tree_data

    @classmethod
    def _recursion(cls, categories, pid=None):
        """递归获取分类"""
        category_list = []
        for category in categories:
            if category.pid == pid:
                category_list.append({
                    "id": category.id,
                    "name": category.name,
                    "pid": category.pid,
                    "children": cls._recursion(categories, category.id)
                })
        return category_list

    @classmethod
    def add_category(cls, name, note, pid=None):
        """添加分类"""
        model = cls()
        if pid is not None and pid <= 0:
            pid = None
        model.name = name
        model.note = note
        model.pid = pid
        model.add(True)
        return {"id": model.id, "name": model.name, "result": "success"}

    def edit_category(self, name, note, pid=None):
        if name == self.name and note == self.note and pid == self.pid:
            return {"id": self.id, "result": "success"}
        if name != self.name:
            flows = WorkFlow.query.filter_by(category_id=self.id)
            for flow in flows:
                flow.category_name = name
                flow.update()
        self.name = name
        self.note = note
        if pid is not None and pid <= 0:
            pid = None
        self.pid = pid
        self.update(True)
        return {"id": self.id, "result": "success"}

    def delete_category(self):
        flows = WorkFlow.query.filter_by(category_id=self.id)
        if flows.count() > 0:
            raise ValidationException("该分类下存在流程，不能删除")
        if WorkFlowCategory.query.filter_by(pid=self.id).count() > 0:
            raise ValidationException("该分类下存在子分类，先删除子分类后再删除该分类")
        self.delete(True)
        return {'result': 'success'}


class WorkFlow(BaseModel):
    """Agent流程"""
    view_json = mapped_column(Text, comment='前端流程json')
    data_json = mapped_column(Text, comment='后端数据json')
    is_tool = mapped_column(Boolean, comment='是否可以作为工具', default=False)
    use_log = mapped_column(Boolean, comment='是否启用日志', default=True)
    # 允许分享
    is_share = mapped_column(Boolean, comment='是否允许分享', default=False)
    api_key = mapped_column(String(50), comment='api_key', default=None, nullable=True)

    category_name = Column(String(200), nullable=True, comment='分类名称')
    category_id = Column(Integer, nullable=True, comment='分类id')
    unique_code = Column(String(200), nullable=True, comment='唯一编码', default=None)
    sources = relationship("WorkFlowSourceKey", back_populates="flow", cascade='all', lazy='dynamic')

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id} deleted={bool(self.deleted_at)}>"

    def validate_api_key(self, api_key: str):
        if not self.is_share:
            raise ValidationException("该流程已停止访问")
        sources = self.sources.all()
        if len(sources) == 0:
            raise ValidationException("该流程设置无效，请联系管理员")
        if api_key in [source.api_key for source in sources]:
            return True
        raise ValidationException("无权访问该流程")

    @classmethod
    def get_source_info_by_api_key(cls, flow_id: int, api_key: str):
        return next(({"id": source.id, "name": source.name} for source in cls.get(flow_id).sources if source.api_key == api_key), {})

    def get_source_info_by_key(self, api_key: str):
        return next(({"id": source.id, "name": source.name} for source in self.sources if source.api_key == api_key), {})

    def add_update_flow(self, name, caption, view_json, data_json, is_tool=False, use_log=True,
                        is_share: Optional[bool] = False,
                        category_id: Optional[int] = None, category_name: Optional[str] = None,
                        sources: Optional[list[dict]] = None) -> 'WorkFlow':

        """
        全量 新增/添加 流程
        @param name: 流程名称
        @param caption: 流程标题
        @param view_json: 前端流程json
        @param data_json: 后端数据json
        @param is_tool: 是否可以作为工具
        @param use_log: 是否启用日志
        @param is_share: 是否允许分享
        @param category_id: 分类id
        @param category_name: 分类名称
        @param sources: 来源 [{'source_id': 1, 'source_name': '来源名称', 'api_key': 'api_key'}]
        """
        self.name = name
        self.caption = caption
        self.view_json = view_json
        self.data_json = data_json
        self.is_tool = is_tool
        self.use_log = use_log
        self.is_share = is_share
        self.category_name = category_name
        self.category_id = category_id
        if sources is None:
            sources = []
        else:
            source_names = [source.get('source_name') for source in sources]
            if len(set(source_names)) != len(source_names):
                raise ValidationException(f"来源名称重复：{[name for name in source_names if source_names.count(name) > 1]}")
            source_keys = [source.get('api_key') for source in sources]
            if len(set(source_keys)) != len(source_keys):
                raise ValidationException(f"来源 api_key 重复：{[key for key in source_keys if source_keys.count(key) > 1]}")
            none_sources = [source for source in sources
                            if source.get('api_key') is None or source.get('source_name') is None
                            or source.get('api_key') == '' or source.get('source_name') == '']
            if len(none_sources) > 0:
                raise ValidationException(f"来源名称或 api_key 为空")
        if is_share and len(sources) == 0:
            raise ValidationException("分享流程必须设置来源")
        if self.id is None or self.id == 0:
            for source_item in sources:
                self.sources.append(WorkFlowSourceKey(name=source_item.get('source_name'), api_key=source_item.get('api_key')))
            self.unique_code = str(uuid.uuid4())
            self.add(True)
        else:
            db_sources = self.sources.all()

            arg_update_source_ids = [source.get('source_id') for source in sources if source.get('source_id') > 0]

            db_source_ids = [source.id for source in db_sources]

            # 删除
            remove_source_ids = list(set(db_source_ids) - set(arg_update_source_ids))

            # 修改
            update_source_ids = list(set(db_source_ids) & set(arg_update_source_ids))

            # 新增
            add_sources = [source for source in sources if source.get('source_id') == 0]
            if add_sources:
                for source in add_sources:
                    self.sources.append(WorkFlowSourceKey(flow_id=self.id, name=source.get('source_name'), api_key=source.get('api_key')))

            # 移除tag
            if remove_source_ids:
                remove_tags = list(filter(lambda x: x.id in remove_source_ids, db_sources))
                for remove_tag_item in remove_tags:
                    self.sources.remove(remove_tag_item)

            # 修改tag
            if update_source_ids:
                update_sources = list(filter(lambda x: x.id in update_source_ids, db_sources))
                for update_source_item in update_sources:
                    tmp_db_source = next((source for source in sources if source.get('source_id') == update_source_item.id), None)
                    if tmp_db_source is None:
                        continue
                    update_source_item.name = tmp_db_source.get('source_name')
                    update_source_item.api_key = tmp_db_source.get('api_key')

            self.update(True)
        return self

    @classmethod
    def baseinfo_add_update(cls, flow_id, name, caption,
                            is_tool=False, use_log=True, is_share: Optional[bool] = False,
                            category_id: Optional[int] = None, category_name: Optional[str] = None,
                            sources: Optional[list[dict]] = None):
        """
        流程基本信息
        @param flow_id:
        @param name:
        @param caption:
        @param is_tool:
        @param use_log:
        @param is_share:
        @param category_id:
        @param category_name:
        @param sources:
        @return:
        """
        if flow_id is not None and flow_id > 0:
            model = cls.get(flow_id)
            model.add_update_flow(name, caption, model.view_json, model.data_json, is_tool, use_log, is_share, category_id, category_name, sources)
        else:
            model = cls().add_update_flow(name, caption, '', '', is_tool, use_log, is_share, category_id, category_name, sources)
        return model

    def flow_view_edit(self, view_json: str | None = None):
        """编辑流程视图"""
        if view_json is not None and view_json.strip() == '':
            view_json = None
        if view_json is not None:
            data_json = self.get_date_json(view_json)
        else:
            data_json = None
        self.view_json = view_json
        self.data_json = data_json
        self.update(True)

    def delete_flow(self):
        """删除流程"""
        self.delete(True)

    def get_flow_input(self):
        """获取输入"""
        import json
        if self.data_json is None or self.data_json == '':
            return []
        tmp_nodes = json.loads(self.data_json).get('nodes')
        if tmp_nodes is None or len(tmp_nodes) == 0:
            return []
        start_node = [item for item in tmp_nodes if item.get('type') == 'start'][0]
        return start_node.get('inputs', [])

    @classmethod
    def get_date_json(cls, json_str):
        import json
        tmp_json = json.loads(json_str)
        json_nodes = [nodes.get('data') for nodes in tmp_json.get('nodes')]

        all_nodes=[]
        node_dict = {}
        space_vars=[]
        for node in json_nodes:
            node_type = node.get('type').lower()
            new_node = None
            if node_type == NodeType.START.value:
                new_node={
                    "id": node.get('id'),
                    "type": node.get('type'),
                    "role": node.get('role'),
                    "description": node.get('description'),
                    "inputs": [cls._extract_fields(output_item) for output_item in node.get('inputs', [])],
                    "next_nodes": [{"max_run_times": input_item.get('max_run_times'), "role": input_item.get('role')} for input_item in node.get('next_nodes')] if node.get('next_nodes') else []
                }
            elif node_type==NodeType.LOOP.value:
                new_node={
                    "id": node.get('id'),
                    "type": node.get('type'),
                    "role": node.get('role'),
                    "description": node.get('description'),
                    "pid": node.get('pid'),
                    "loop_traget": node.get('loop_traget'),
                    "loop_size": node.get('loop_size'),
                    "sub_nodes":[],
                    "next_nodes": [{"max_run_times": input_item.get('max_run_times'), "role": input_item.get('role')} for input_item in node.get('next_nodes')] if node.get('next_nodes') else []
                }
            elif node_type==NodeType.LOOP_START.value:
                new_node={
                    "id": node.get('id'),
                    "type": node.get('type'),
                    "role": node.get('role',"循环开始"),
                    "description": node.get('description',""),
                    "pid": node.get('pid'),
                    "next_nodes": [{"max_run_times": input_item.get('max_run_times'), "role": input_item.get('role')} for input_item in node.get('next_nodes')] if node.get('next_nodes') else []
                }
            elif node_type==NodeType.LLM.value:
                new_node={
                    "id": node.get('id'),
                    "type": node.get('type'),
                    "role": node.get('role'),
                    "description": node.get('description'),
                    "pid": node.get('pid'),
                    "llm_id": node.get('llm_id'),
                    "prompt_id": node.get('prompt_id'),
                    "auto_choice_node": node.get('auto_choice_node'),
                    "choice_role_prompt": node.get('choice_role_prompt',''),
                    "output_var_prompt": node.get('output_var_prompt',''),
                    "react_part_prompt":node.get("react_part_prompt",''),
                    "react": node.get('react', False),
                    "auto_section_run": node.get('auto_section_run', False),
                    "react_max_times": node.get('react_max_times', 10),
                    "functions": node.get('functions', []),
                    "use_vt": node.get('use_vt', False),
                    "vt_file": node.get('vt_file', ''),
                    "outputs": [cls._extract_fields(output_item, False) for output_item in node.get('outputs', [])],
                    "next_nodes": [{"max_run_times": input_item.get('max_run_times'), "role": input_item.get('role')} for input_item in node.get('next_nodes')] if node.get('next_nodes') else []
                }
            elif node_type==NodeType.TOOL.value:
                new_node={
                    "id": node.get('id'),
                    "type": node.get('type'),
                    "role": node.get('role'),
                    "description": node.get('description'),
                    "pid": node.get('pid'),
                    "functions": node.get('functions', []),
                    "next_nodes": [{"max_run_times": input_item.get('max_run_times'), "role": input_item.get('role')} for input_item in node.get('next_nodes')] if node.get('next_nodes') else []
                }
            elif node_type==NodeType.TEMP_EXECUTOR.value:
                new_node={
                    "id": node.get('id'),
                    "type": node.get('type'),
                    "role": node.get('role'),
                    "description": node.get('description'),
                    "pid": node.get('pid'),
                    "prompt_id": node.get('prompt_id'),
                    "next_nodes": [{"max_run_times": input_item.get('max_run_times'), "role": input_item.get('role')} for input_item in node.get('next_nodes')] if node.get('next_nodes') else []
                }
            elif node_type==NodeType.WORK_SPACE.value:
                space_vars = [{"name": var.get('name'), "type": var.get('type').lower()} for var in node.get('space_vars')] if node.get('space_vars') else []
                
            if new_node:
                all_nodes.append(new_node)
                node_dict[new_node['id']] = new_node  # 建立ID到节点的映射

        role_set = set()  # 用于存储已经出现过的role值
        # 构建父子关系
        for node in all_nodes:
            if node.get("role") in role_set and node.get('type').lower()!=NodeType.LOOP_START.value:
                raise ValueError(f"角色名称重复: {node.get('role')}")
            else:
                role_set.add(node.get("role"))

            if pid := node.get('pid'):
                if parent := node_dict.get(pid):
                    if parent['type'].lower() == 'loop' and 'sub_nodes' in parent:
                        parent['sub_nodes'].append(node)

        nodelist = [node for node in all_nodes if not node.get('pid')]


        data_dict_json = {
            "space_vars": space_vars,
            "nodes": nodelist
        }
        return json.dumps(data_dict_json, ensure_ascii=False)

    @classmethod
    def _extract_fields(cls, node, is_input=True):
        if is_input:
            extracted_node = {
                "name": node.get("name"),
                "data_type": node.get("data_type"),
                "desc": node.get("desc"),
                "is_required": node.get("is_required", False),
                "object_fields": []
            }
        else:
            extracted_node = {
                "name": node.get("name"),
                "data_type": node.get("data_type"),
                "desc": node.get("desc"),
                "prefix": node.get("prefix", "role"),
                "object_fields": []
            }
        if "object_fields" in node:
            for child in node["object_fields"]:
                extracted_node["object_fields"].append(cls._extract_fields(child))
        return extracted_node

    @classmethod
    def get_tool_flows(cls):
        """获取工具流程"""
        return cls.query.filter(cls.is_tool == True).all()

    @classmethod
    def get_workflow_inputs(cls, flow_id):
        """获取流程输入"""
        model_data_json_str = cls.get(flow_id).data_json
        data_json = json.loads(model_data_json_str)
        start_node = [node for node in data_json.get('nodes') if node.get('role') == '开始'][0]
        inputs = start_node.get('inputs', [])

        flow_inputs = {}
        for input_item in inputs:
            if input_item.get('data_type') == 'String':
                flow_inputs[input_item.get('name')] = ""
            if input_item.get('data_type') == 'Object':
                flow_inputs[input_item.get('name')] = {}
            if input_item.get('data_type').startswith('Array'):
                flow_inputs[input_item.get('name')] = []
        return flow_inputs


class WorkFlowRunLog(BaseModel):
    """Agent流程运行日志"""
    conversation_id = mapped_column(String(50), comment='窗口id', nullable=True)
    ai_run_id = mapped_column(String(50), comment='用户id', nullable=True)
    flow_id = mapped_column(Integer, comment='流程id')
    flow_name = mapped_column(String(200), comment='流程名称')
    run_start_time = mapped_column(DateTime, comment='运行开始时间')
    run_end_time = mapped_column(DateTime, comment='运行结束时间')
    elapsed_time = mapped_column(String(50), comment='耗时', nullable=True)
    score = mapped_column(String(20), comment='反馈分数', nullable=True)
    origin=mapped_column(Integer, comment='日志来源',nullable=True)

    user_input = mapped_column(Text, comment='用户输入', nullable=True)
    inputs = mapped_column(Text, comment='流程输入 {}', nullable=True)
    outputs = mapped_column(Text, comment='流程输出 []', nullable=True)
    citations=mapped_column(Text, comment='引用 []', nullable=True)
    use_tools = mapped_column(Text, comment='使用工具 []', nullable=True)
    memory = mapped_column(Text, comment='记忆 []', nullable=True)
    human_messages = mapped_column(Text, comment='人工消息 []', nullable=True)
    variables = mapped_column(Text, comment='变量值 {}', nullable=True)
    error_msg = mapped_column(Text, comment='错误信息', nullable=True)
    question_id = mapped_column(String(50), comment='问题id', nullable=True)
    node_logs = relationship("WorkFlowRunNodeLog", back_populates="run_log", cascade='all', lazy='dynamic')
    workflow_source_id=mapped_column(Integer, comment='工作流来源id', nullable=True)
    workflow_source_name=mapped_column(String(200), comment='工作流来源名称', nullable=True)

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id} deleted={bool(self.deleted_at)}>"

    @classmethod
    def add_log(cls, conversation_id, ai_run_id, flow_id, flow_name, run_start_time, run_end_time, user_input, inputs, outputs, human_messages, memory, agent_logs: List[AgentRunLog],citations, question_id=None, error_msg=None,
                workflow_source_id:int|None=None,workflow_source_name:str|None=None) -> int:
        try:
            model = cls(conversation_id=conversation_id, ai_run_id=ai_run_id, flow_id=flow_id, flow_name=flow_name)
            model.question_id = question_id
            model.user_input = user_input
            model.run_start_time = run_start_time
            model.run_end_time = run_end_time
            model.elapsed_time = f'{(run_end_time - run_start_time).total_seconds()}'
            model.inputs = inputs
            model.outputs = outputs
            model.citations = citations
            model.human_messages = human_messages
            model.memory = memory
            model.error_msg = error_msg
            model.workflow_source_id=workflow_source_id
            model.workflow_source_name=workflow_source_name
            model.origin=None
            if agent_logs is None or len(agent_logs) == 0:
                model.add(True)
                return model.id
            use_tools = []
            node_logs = []
            for agent_log in agent_logs:
                node_log = WorkFlowRunNodeLog()
                node_log.agent_run_log_id = agent_log.id
                node_log.pid = agent_log.pid
                node_log.triggerer = agent_log.triggerer
                node_log.runner_id=agent_log.runner_id
                node_log.runner = agent_log.runner
                node_log.runner_run_times = agent_log.runner_run_times
                node_log.start_time = agent_log.start_time
                node_log.end_time = agent_log.end_time
                node_log.duration = agent_log.duration
                node_log.score = None
                node_log.prompt_temp = agent_log.prompt_temp
                node_log.prompt_str = agent_log.prompt_str
                node_log.vision_file_str=agent_log.vision_file_str
                node_log.response_content = agent_log.response_content
                node_log.response_metadata = json.dumps(agent_log.response_metadata, ensure_ascii=False, default=_customer_serializer) if agent_log.response_metadata else None

                if agent_log.function_calls is not None and len(agent_log.function_calls) > 0:

                    tmp_func_calls = [{
                       "function_name": func_call.function_name,
                       "function_options": func_call.function_options,
                       "function_args": func_call.function_args,
                       "function_return": func_call.function_return,
                       "start_time": func_call.start_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
                       "end_time": func_call.end_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
                       "duration": f'{func_call.duration}',
                    } for func_call in agent_log.function_calls]
                    node_log.function_calls = json.dumps(tmp_func_calls, ensure_ascii=False) if tmp_func_calls else None
                    use_tools.extend([func_call.get('function_name') for func_call in tmp_func_calls])

                if agent_log.room_messages is not None and len(agent_log.room_messages) > 0:
                    tmp_room_messages = [{
                        "id": room_message.id,
                        "from_role": room_message.from_role,
                        "to_role": room_message.to_role,
                        "message": room_message.message,
                        "send_time": room_message.send_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
                    } for room_message in agent_log.room_messages]
                    node_log.room_messages = json.dumps(tmp_room_messages, ensure_ascii=False) if tmp_room_messages else None

                node_log.inputs = json.dumps(agent_log.inputs, ensure_ascii=False) if agent_log.inputs else None
                node_log.variables = json.dumps(agent_log.variables, ensure_ascii=False) if agent_log.variables else None
                node_log.role_variables = json.dumps(agent_log.role_variables, ensure_ascii=False) if agent_log.role_variables else None
                node_log.model_name = agent_log.model_name
                node_log.tokens = agent_log.tokens
                node_log.is_section=agent_log.is_section
                node_log.is_section_sub=agent_log.is_section_sub
                node_log.run_log_id = model.id
                node_log.runner_type = agent_log.runner_type
                node_logs.append(node_log)
            model.node_logs = node_logs
            model.use_tools = json.dumps(list(set(use_tools)), ensure_ascii=False)
            model.variables = json.dumps(agent_logs[-1].variables, ensure_ascii=False) if agent_logs[-1].variables else None
            model.add(True)

            return model.id
        except Exception as e:
            print(f"WorkFlowRunLog 添加日志失败: {e}")
            traceback.print_exc()
            return 0

    @classmethod
    def get_run_logs_pages(cls, flow_id: int, page_num: int = 1, page_size: int = 10, conditions: Optional[dict] = None):
        if flow_id is None or flow_id == 0:
            run_logs = cls.query
        else:
            run_logs = cls.query.filter_by(id=flow_id)
        if conditions:
            filter_conditions = [getattr(cls, key) == value for key, value in conditions.items() if hasattr(cls, key)]
            run_logs = run_logs.filter(*filter_conditions)
        total_records = run_logs.count()
        if total_records == 0:
            return {"total_records": total_records, "total_pages": 0, "rows": []}
        run_logs = run_logs.order_by(cls.id.desc()).offset((page_num - 1) * page_size).limit(page_size).all()
        total_pages = (total_records + page_size - 1) // page_size
        logs = []
        question_ids = [run_log.question_id for run_log in run_logs if run_log.question_id]
        agv_scores_dict = WorkFlowRunLogScore.get_avg_score(question_ids)
        for log in run_logs:
            tmp_log = {
                "id": log.id,
                "ai_run_id": log.ai_run_id,
                "conversation_id": log.conversation_id,
                "user_input": log.user_input,
                "inputs": json.loads(log.inputs) if log.inputs else None,
                "output": json.loads(log.outputs) if log.outputs else None,
                "citations":json.loads(log.citations) if log.citations else None,
                "human_messages": json.loads(log.human_messages) if log.human_messages else None,
                "memory": log.memory,
                "flow_id": log.flow_id,
                "flow_name": log.flow_name,
                "use_tools": log.use_tools,
                "elapsed_time": log.elapsed_time,
                "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else None,
                "score": agv_scores_dict.get(log.question_id, None) if log.question_id else None,
                "error_msg": log.error_msg,
                "question_id":log.question_id,
                "workflow_source_id":log.workflow_source_id,
                "workflow_source_name":log.workflow_source_name,
                "node_log": []
            }
            for node_log in log.node_logs if log.node_logs else []:
                tmp_log["node_log"].append({
                    "detail_id": node_log.id,
                    "id": node_log.agent_run_log_id,
                    "pid": node_log.pid,
                    "triggerer": node_log.triggerer,
                    "runner": node_log.runner,
                    "runner_run_times": node_log.runner_run_times,
                    "start_time": node_log.start_time.strftime("%Y-%m-%d %H:%M:%S.%f") if node_log.start_time else None,
                    "end_time": node_log.end_time.strftime("%Y-%m-%d %H:%M:%S.%f") if node_log.end_time else None,
                    "duration": node_log.duration,
                    "prompt_temp": node_log.prompt_temp,
                    "prompt_str": node_log.prompt_str,
                    "vision_file_str": node_log.vision_file_str,
                    "response_content": node_log.response_content,
                    "response_metadata": json.loads(node_log.response_metadata) if node_log.response_metadata else None,
                    "function_calls": json.loads(node_log.function_calls) if node_log.function_calls else None,
                    "room_messages": json.loads(node_log.room_messages) if node_log.room_messages else None,
                    "inputs": json.loads(node_log.inputs) if node_log.inputs else None,
                    "variables": json.loads(node_log.variables) if node_log.variables else None,
                    "role_variables": json.loads(node_log.role_variables) if node_log.role_variables else None,
                    "model_name": node_log.model_name,
                    "tokens": node_log.tokens,
                    "is_section":node_log.is_section if node_log.is_section else False,
                    "is_section_sub":node_log.is_section_sub if node_log.is_section_sub else False,
                    "runner_type": node_log.runner_type
                })
            logs.append(tmp_log)
        return {"total_records": total_records, "total_pages": total_pages, "rows": logs}

    def feedback_score(self, feedback_score: Optional[str] = None) -> None:
        """
        反馈分数
        :param feedback_score: 反馈分数
        """
        self.score = feedback_score
        self.update(True)

    @classmethod
    def get_pagination(cls, flow_log_id, flow_id, flow_name, source_id, source_name,
                       user_id, conversation_id, test_cate_id,
                       created_at_start, created_at_end, question,
                       page: int = 1, pagesize: int = 10):
        session = cls().session
        conditions = {}
        if flow_id is not None and flow_id <= 0:
            flow_id = None
        if flow_name is not None and len(flow_name.strip()) == 0:
            flow_name = None
        if source_id is not None and source_id <= 0:
            source_id = None
        if source_name is not None and len(source_name.strip()) == 0:
            source_name = None
        if flow_log_id is not None and flow_log_id <= 0:
            flow_log_id = None
        if user_id is not None and len(user_id.strip()) == 0:
            user_id = None
        if conversation_id is not None and len(conversation_id.strip()) == 0:
            conversation_id = None
        if test_cate_id is not None and test_cate_id <= 0:
            test_cate_id = None
        if question is not None and len(question.strip()) == 0:
            question = None


        if flow_id is not None:
            conditions['flow_id'] = flow_id
        if source_id is not None:
            conditions['workflow_source_id'] = source_id
        if flow_log_id is not None:
            conditions['id'] = flow_log_id
        if user_id is not None:
            conditions['ai_run_id'] = user_id
        if conversation_id is not None:
            conditions['conversation_id'] = conversation_id

        flow_log_ids = []
        if test_cate_id is not None:
            cases = session.query(TestCase).filter_by(test_cate_id=test_cate_id)
            if cases:
                flow_log_ids = [case.workflow_log_id for case in cases]

        selected_fields = (WorkFlowRunLog.id,
                           WorkFlowRunLog.ai_run_id, WorkFlowRunLog.conversation_id,
                           WorkFlowRunLog.user_input, WorkFlowRunLog.inputs, WorkFlowRunLog.outputs, WorkFlowRunLog.citations,
                           WorkFlowRunLog.human_messages, WorkFlowRunLog.memory, WorkFlowRunLog.flow_id, WorkFlowRunLog.flow_name,
                           WorkFlowRunLog.use_tools, WorkFlowRunLog.elapsed_time, WorkFlowRunLog.created_at, WorkFlowRunLog.error_msg,
                           WorkFlowRunLog.question_id, WorkFlowRunLog.workflow_source_id, WorkFlowRunLog.workflow_source_name)
        run_logs = session.query(*selected_fields).filter_by(**conditions)
        total_records_count = session.query(func.count(WorkFlowRunLog.id)).filter_by(**conditions)
        if len(flow_log_ids) > 0:
            run_logs = run_logs.filter(WorkFlowRunLog.id.in_(flow_log_ids))
            total_records_count = total_records_count.filter(WorkFlowRunLog.id.in_(flow_log_ids))
        if question is not None:
            run_logs = run_logs.filter(WorkFlowRunLog.user_input.like(f'%{question}%'))
            total_records_count = total_records_count.filter(WorkFlowRunLog.user_input.like(f'%{question}%'))
        if flow_id is None and flow_name is not None:
            run_logs = run_logs.filter(WorkFlowRunLog.flow_name.like(f'%{flow_name}%'))
            total_records_count = total_records_count.filter(WorkFlowRunLog.flow_name.like(f'%{flow_name}%'))
        if source_id is None and source_name is not None:
            run_logs = run_logs.filter(WorkFlowRunLog.workflow_source_name.like(f'%{source_name}%'))
            total_records_count = total_records_count.filter(WorkFlowRunLog.workflow_source_name.like(f'%{source_name}%'))
        if created_at_start and created_at_end:
            created_at_start = datetime.strptime(created_at_start, '%Y-%m-%d %H:%M:%S')
            created_at_end = datetime.strptime(created_at_end, '%Y-%m-%d %H:%M:%S')
            if created_at_end.hour == 0 and created_at_end.minute == 0 and created_at_end.second == 0:
                created_at_end = created_at_end.replace(hour=23, minute=59, second=59)
            run_logs = run_logs.filter(WorkFlowRunLog.created_at.between(created_at_start, created_at_end))
            total_records_count = total_records_count.filter(WorkFlowRunLog.created_at.between(created_at_start, created_at_end))
        total_records = total_records_count.scalar()
        run_logs = run_logs.order_by(WorkFlowRunLog.id.desc()).offset((page - 1) * pagesize).limit(pagesize).all()
        total_pages = (total_records + pagesize - 1) // pagesize
        if not run_logs:
            return {"total_records": 0, "total_pages": 0, "rows": []}
        logs = []
        question_ids = [run_log.question_id for run_log in run_logs if run_log.question_id]
        agv_scores_dict = WorkFlowRunLogScore.get_avg_score(question_ids)
        ids = [log.id for log in run_logs]
        test_cates = TestCase.get_case_cates_by_workflow_log_ids(ids)
        train_cates = TrainCase.get_cate_by_workflow_log_ids(ids)
        for log in run_logs:
            tmp_log = {
                "id": log.id,
                "ai_run_id": log.ai_run_id,
                "conversation_id": log.conversation_id,
                "user_input": log.user_input,
                "inputs": json.loads(log.inputs) if log.inputs else None,
                "output": json.loads(log.outputs) if log.outputs else [],
                "citations": json.loads(log.citations) if log.citations else None,
                "human_messages": json.loads(log.human_messages) if log.human_messages else None,
                "memory": log.memory,
                "flow_id": log.flow_id,
                "flow_name": log.flow_name,
                "use_tools": log.use_tools,
                "elapsed_time": log.elapsed_time,
                "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else None,
                "score": agv_scores_dict.get(log.question_id, None) if log.question_id else None,
                "error_msg": log.error_msg,
                "question_id": log.question_id,
                "source_id": log.workflow_source_id if log.workflow_source_id else None,
                "source_name": log.workflow_source_name if log.workflow_source_name else None,
            }
            tmp_log["test_cates"] = test_cates.get(str(log.id), [])
            tmp_log["train_cates"] = train_cates.get(str(log.id), [])
            logs.append(tmp_log)
        return {"total_records": total_records, "total_pages": total_pages, "rows": logs}

class WorkFlowRunNodeLog(BaseModel):
    """Agent流程运行节点日志"""
    run_log_id = mapped_column(Integer, ForeignKey('work_flow_run_log.id'), comment='节点日志id')
    run_log = relationship("WorkFlowRunLog", back_populates="node_logs")
    """以下是流程节点原本的属性【agent_run_log_id， id】"""
    agent_run_log_id = mapped_column(String(100), comment='节点id')
    pid = mapped_column(String(100), comment='父节点id')
    triggerer = mapped_column(String(100), comment='触发者', nullable=True)
    runner = mapped_column(String(100), comment='执行者', nullable=True)
    runner_id= mapped_column(String(100), comment='执行者id', nullable=True)
    runner_run_times = mapped_column(Integer, comment='执行次数', default=0)
    start_time = mapped_column(DateTime, comment='开始时间')
    end_time = mapped_column(DateTime, comment='结束时间')
    duration = mapped_column(String(50), comment='耗时', nullable=True)
    prompt_temp = mapped_column(Text, comment='提示模板', nullable=True)
    prompt_str = mapped_column(Text, comment='提示信息', nullable=True)
    vision_file_str = mapped_column(Text, comment='视觉模型文件路径', nullable=True)
    response_content = mapped_column(Text, comment='响应内容', nullable=True)
    response_metadata = mapped_column(Text, comment='响应元数据 {}', nullable=True)
    function_calls = mapped_column(Text, comment='函数调用 []', nullable=True)
    room_messages = mapped_column(Text, comment='聊天室消息 []', nullable=True)
    inputs = mapped_column(Text, comment='流程输入 {}', nullable=True)
    variables = mapped_column(Text, comment='流程变量 {}', nullable=True)
    role_variables= mapped_column(Text, comment='角色变量 {}', nullable=True)
    model_name = mapped_column(String(200), comment='模型名称', nullable=True)
    tokens = mapped_column(Integer, comment='token数量', nullable=True)
    is_section=mapped_column(Boolean, comment='是否分身了', default=False) # 分身True
    is_section_sub=mapped_column(Boolean, comment='分身后的子数据', default=False) # 分身后子数据True
    runner_type = mapped_column(String(50), comment='节点类型', nullable=True)


class WorkFlowRunLogScore(BaseModel):
    """评分表"""
    question_id = mapped_column(String(50), comment='问题id')
    score = mapped_column(Integer, comment='反馈分数', nullable=True)
    amend_answer = mapped_column(Text, comment='采用的回答', nullable=True)
    role = mapped_column(String(200), comment='角色', nullable=True)
    answer_id= mapped_column(String(50), comment='回答id', nullable=True)

    @classmethod
    def feedback_result(cls, question_id: str, score: int, amend_answer: str,role:str,answer_id:str) -> 'WorkFlowRunLogScore':
        """
        评分反馈
        :param question_id: 问题id
        :param score: 评分
        :param amend_answer: 采用的回答
        :param role : 角色
        """
        model = cls(question_id=question_id, score=score, amend_answer=amend_answer,role=role,answer_id=answer_id)
        model.add(True)
        return model

    @classmethod
    def get_score_by_question_id(cls, question_id: str):
        scores_dict=[]
        if not question_id:
            return scores_dict
        scores= cls.query.filter(cls.question_id==question_id).all()
        for item in scores:
            scores_dict.append({"question_id":item.question_id,"score":item.score,"amend_answer":item.amend_answer,"role":item.role,"answer_id":item.answer_id})
        return scores_dict
    
    @classmethod
    def get_avg_score(cls, question_ids: List[str]) -> dict[str, float]:
        """
        获取多个问题的平均评分,保存对应小数点位数
        :param question_ids: 问题id列表
        :return: 问题id-平均分字典
        评分向下取整 eg: 如果是1.9，取值为1
        若没有评分，则返回{}
        若有未评分的，则不计算

        """
        if not question_ids:
            return {}
        scores = (cls.query
                  .filter(cls.question_id.in_(question_ids)).with_entities(cls.question_id, func.avg(cls.score).label('score'))
                  .group_by(cls.question_id).all()
                  )
        return {score[0]: int(score[1]) for score in scores} if scores else {}


class WorkFlowSourceKey(BaseModel):
    """流程标签"""
    flow_id = mapped_column(Integer, ForeignKey('work_flow.id'), comment='流程id')
    flow = relationship("WorkFlow", back_populates="sources")
    api_key = mapped_column(String(50), comment='api_key')


class WxBotMessage(BaseModel):
    """聊天机器人消息"""
    conversation_id = mapped_column(String(50), comment='对话id R: 3277079711')
    conversation_type = mapped_column(String(50), comment='对话类型')
    message_type = mapped_column(String(50), comment='消息类型')
    user_id = mapped_column(String(50), comment='监控的企业微信用户id')
    client_id = mapped_column(String(50), comment='客户端id')

    receiver = mapped_column(String(50), comment='接收者id 1688857198674249')
    sender = mapped_column(String(50), comment='发送者id 1688851745691648')
    sender_name = mapped_column(String(100), comment='发送者名称')
    send_timespan = mapped_column(String(50), comment='发送时间 时间戳 1735555736')
    send_time = mapped_column(DateTime, comment='发送时间')
    server_id = mapped_column(String(50), comment='服务id 1000307')

    # [
    #    {
    #       'nickname': '洋帆AI',
    #       'user_id': '1688857198674249'
    #    }
    # ]
    at_list = mapped_column(String(500), comment='@了哪些人 at_list []')

    appinfo = mapped_column(String(500), comment='消息appinfo CIGABBCZ9cm7BhiAsIWDh4CAAyA0')
    cdn_data = mapped_column(Text, comment='消息cdn数据 ChcIBRITCMmCnaubgIADEgjmtIvluIZBSQoOCAASCgoIIOa1i')
    content = mapped_column(Text, comment='消息内容')
    content_type = mapped_column(String(50), comment='消息内容类型')
    is_pc = mapped_column(String(50), comment='is_pc 0')
    local_id = mapped_column(String(50), comment='local_id 49')
    quote_content = mapped_column(Text, comment='quote_content')

    # message_type = WW_RECV_IMG_MSG，WW_RECV_FILE_MSG 图片消息，文件消息
    cdn = mapped_column(Text, comment='图片信息，文件信息 json格式')
    cdn_type = mapped_column(String(50), comment='cdn_type  2')

    # message_type = WW_RECV_TEXT_IMG_MSG 图片+文本消息  此时，不返回content， 需要将text_content赋值给content
    image_list = mapped_column(Text, comment='图片列表 json格式')

    @classmethod
    def add_message(cls, message: dict):
        model = cls(conversation_id=message.get('data', {}).get('conversation_id', None), client_id=message.get('client_id'))
        model.message_type = message.get('type')
        model.user_id = message.get('user_id')
        model.receiver = message.get('data', {}).get('receiver')
        model.sender = message.get('data', {}).get('sender')
        model.sender_name = message.get('data', {}).get('sender_name')
        model.send_timespan = message.get('data', {}).get('send_time')
        model.send_time = datetime.fromtimestamp(int(model.send_timespan), timezone.utc).astimezone()
        model.server_id = message.get('data', {}).get('server_id')
        model.appinfo = message.get('data', {}).get('appinfo')
        model.cdn_data = message.get('data', {}).get('cdn_data')
        model.content = message.get('data', {}).get('content', None)
        model.content_type = message.get('data', {}).get('content_type')
        model.is_pc = message.get('data', {}).get('is_pc')
        model.local_id = message.get('data', {}).get('local_id')
        model.quote_content = message.get('data', {}).get('quote_content')
        model.at_list = json.dumps(message.get('data').get('at_list'), ensure_ascii=False) if message.get('data', {}).get('at_list', None) else None
        if model.message_type == 'WW_RECV_IMG_MSG' or model.message_type == 'WW_RECV_FILE_MSG':
            model.cdn = json.dumps(message.get('data').get('cdn'), ensure_ascii=False) if message.get('data', {}).get('cdn', None) else None
            model.cdn_type = message.get('data', {}).get('cdn_type')
        if model.message_type == 'WW_RECV_TEXT_IMG_MSG':
            model.image_list = json.dumps(message.get('data').get('image_list'), ensure_ascii=False) if message.get('data', {}).get('image_list', None) else None
            model.content = message.get('data', {}).get('text_content')
        if model.conversation_id.startswith('R:'):
            model.conversation_type = "GROUP"
        elif model.conversation_id.startswith('S:'):
            model.conversation_type = "PERSONAL"

        model.add(True)
        return model

    # 分页查询
    @classmethod
    def get_messages_paged(cls, page_num: int, page_size: int,
                           conversation_id: str, user_id: str, client_id: str, receiver: str, sender: str
                           ) -> dict:
        """
        分页查询聊天机器人消息
        :param page_num: 页码
        :param page_size: 页大小
        :param conversation_id: 对话id
        :param user_id: 监控的企业微信用户id
        :param receiver: 接收者id
        :param sender: 发送者id
        :param client_id: 客户端id
        :return: 聊天机器人消息列表
        """
        conditions = {}
        if conversation_id:
            conditions['conversation_id'] = conversation_id
        if user_id:
            conditions['user_id'] = user_id
        if client_id:
            conditions['client_id'] = client_id
        if receiver:
            conditions['receiver'] = receiver
        if sender:
            conditions['sender'] = sender
        total_records = cls.query.filter_by(**conditions).count()
        total_pages = math.ceil(total_records / page_size)
        logs = cls.query.filter_by(**conditions).order_by(cls.id.desc()).offset((page_num - 1) * page_size).limit(page_size).all()
        logs = sorted(logs, key=lambda x: x.id, reverse=False)
        rows = []
        for log in logs:
            rows.append({
                "id": log.id,
                "conversation_id": log.conversation_id,
                "message_type": log.message_type,
                "user_id": log.user_id,
                "client_id": log.client_id,
                "receiver": log.receiver,
                "sender": log.sender,
                "sender_name": log.sender_name,
                "send_time": log.send_time,
                "server_id": log.server_id,
                "at_list": json.loads(log.at_list) if log.at_list else None,
                "appinfo": log.appinfo,
                "cdn_data": log.cdn_data,
                "content": log.content,
                "content_type": log.content_type,
                "is_pc": log.is_pc,
                "local_id": log.local_id,
                "quote_content": log.quote_content,
                "cdn": log.cdn,
                "cdn_type": log.cdn_type,
                "image_list": json.loads(log.image_list) if log.image_list else None
            })
        return {"total_records": total_records, "total_pages": total_pages, "rows": rows}


class ToolModel(BaseModel):
    """工具实体类"""

    func_name: Mapped[str] = mapped_column(String(64), comment="工具函数名")
    is_enable: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否启用")
    api_url:Mapped[str]=mapped_column(String(512),comment="api地址")
    api_method:Mapped[str]=mapped_column(String(10),comment="api请求方法")
    in_params:Mapped[str]=mapped_column(Text,comment="输入参数")
    out_params:Mapped[str]=mapped_column(Text,comment="输出参数")
    unique_code = Column(String(200), nullable=True, comment='唯一编码', default=None)


    def toggle_enable(self):
        """切换插件启用状态"""
        self.is_enable = not self.is_enable


    def edit(self, tool_data: APITool):
        self.name = tool_data.name
        self.func_name = tool_data.func_name
        self.caption = tool_data.caption
        self.is_enable = tool_data.is_enable
        self.api_url = tool_data.api_url
        self.api_method = tool_data.api_method
        self.in_params = json.dumps(tool_data.in_params, default=lambda o: o.dict(), ensure_ascii=False)
        self.out_params = json.dumps(tool_data.out_params,default=lambda o: o.dict(), ensure_ascii=False)


    @classmethod
    def get_tool_list(cls):
        """获取工具流程"""
        return cls.query.filter(cls.is_enable == True).all()


class Platforms(BaseModel):
    """平台"""
    shops = relationship("Shop", back_populates="platform")

    """编辑/新增---平台"""
    @classmethod
    def edit_platform(cls, platform_id, platform_name):
        """编辑/新增---平台"""
        if platform_id is None or platform_id <= 0:
            model = Platforms(name=platform_name)
            model.add(True)
        else:
            model = Platforms.get(platform_id)
            model.name = platform_name
            model.update(True)
        return model

    """删除平台"""
    def delete_platform(self):
        """删除平台"""
        if len(self.shops) > 0:
            raise ValidationException("平台下存在店铺，不能删除")
        self.delete(True)


class Shop(BaseModel):
    """店铺"""

    platform_id: Mapped[int] = mapped_column(Integer, ForeignKey("platforms.id"), comment="平台id")
    platform = relationship("Platforms", back_populates="shops")

    """编辑/新增---店铺"""
    @classmethod
    def edit_shop(cls, shop_id, platform_id, shop_name):
        """编辑/新增---店铺"""
        if platform_id is None or platform_id <= 0:
            raise ValidationException("平台ID不能为空")
        if shop_id is None or shop_id <= 0:
            model = Shop(platform_id=platform_id, name=shop_name)
            model.add(True)
        else:
            model = Shop.get(shop_id)
            model.name = shop_name
            model.platform_id = platform_id
            model.update(True)
        return model

    """删除店铺"""
    def delete_shop(self):
        """删除店铺"""
        has_goods = ShopGoods.has_goods(self.id)
        if has_goods:
            raise ValidationException("店铺下存在商品，不能删除")
        self.delete(True)

    @classmethod
    def list_shop(cls, platform_id: Optional[int], *args, **kwargs):
        """获取平台下的店铺列表"""
        platform_id = platform_id if platform_id and platform_id > 0 else None
        query = cls.query.filter_by(platform_id=platform_id) if platform_id else cls.query
        if args:
            query = query.filter(*args)
        if kwargs:
            query = query.filter_by(**kwargs)
        rows = query.all()
        if len(rows) == 0:
            return []
        return [
            {
                'id': model.id,
                'name': model.name,
                'platform_id': model.platform_id,
                "platform_name": model.platform.name if model.platform else None,
            } for model in rows
        ]




class GoodsCategory(BaseModel):
    """商品分类"""
    parent_id: Mapped[int] = mapped_column(Integer, default=0, comment="父级分类id")
    level: Mapped[int] = mapped_column(Integer, default=1, comment="分类层级")

    """递归获取所有分类及其子分类"""
    @classmethod
    def get_recursive_categories(cls):
        """递归获取所有分类及其子分类"""
        root_categories = cls.query.filter_by(parent_id=0).all()
        categories = []
        for root_category in root_categories:
            category_dict = {"id": root_category.id, "name": root_category.name, "level": root_category.level, "pid": root_category.parent_id,
                             "children": []}
            children = cls.query.filter_by(parent_id=root_category.id).all()
            for child in children:
                child_dict = child.get_recursive_current_categories()
                category_dict["children"].append(child_dict)
            categories.append(category_dict)
        return categories

    """递归获取当前分类及其子分类"""
    def get_recursive_current_categories(self):
        """递归获取当前分类及其子分类"""
        current_dict = {"id": self.id, "name": self.name, "level": self.level, "pid": self.parent_id, "children": []}
        children = GoodsCategory.query.filter_by(parent_id=self.id).all()
        for child in children:
            child_dict = child.get_recursive_current_categories()
            current_dict["children"].append(child_dict)
        return current_dict

    """编辑/新增---分类"""
    @classmethod
    def edit_category(cls, name, parent_id=0, category_id: int = 0):
        """编辑/新增---分类"""
        if name is None or name == "" or name.strip() == "":
            raise ValidationException("分类名称不能为空")
        if parent_id is None or parent_id <= 0:
            level = 1
        else:
            parent_category = cls.get(parent_id)
            if parent_category is None:
                level = 1
            else:
                level = parent_category.level + 1
        if category_id is None or category_id <= 0:
            model = GoodsCategory(name=name, level=level, parent_id=parent_id)
            model.add(True)
        else:
            model = GoodsCategory.get(category_id)
            if model is None:
                raise ValidationException("分类不存在")
            model.name = name
            model.parent_id = parent_id
            model.update(True)
        return model

    """删除分类"""
    def delete_category(self):
        """删除分类"""
        has_child = GoodsCategory.query.filter_by(parent_id=self.id).count()
        if has_child:
            raise ValidationException("分类下存在子分类，不能删除")
        has_profile = GoodsProfiles.query.filter_by(goods_category_id=self.id).count()
        if has_profile:
            raise ValidationException("分类下存在商品档案，不能删除")
        has_goods = ShopGoods.query.filter_by(goods_category_id=self.id).count()
        if has_goods:
            raise ValidationException("分类下存在商品，不能删除")
        self.delete(True)

    @classmethod
    def get_category_by_name(cls, category_name):
        """根据分类名称获取分类"""
        if category_name is None or category_name.strip() == "":
            return None
        return cls.query.filter_by(name=category_name).first()

    @classmethod
    def get_category_by_names(cls, category_names) -> Optional[List['GoodsCategory']]:
        """根据分类名称列表获取分类"""
        if category_names is None or len(category_names) == 0:
            return None
        return cls.query.filter(cls.name.in_(category_names)).all()


class GoodsProfiles(BaseModel):
    """商品档案"""
    goods_code: Mapped[str] = mapped_column(String(64), comment="商品编码")
    barcode: Mapped[str] = mapped_column(String(64), comment="条形码")

    goods_category_id: Mapped[int] = mapped_column(Integer, ForeignKey("goods_category.id"), comment="分类id")
    category = relationship("GoodsCategory", backref="goods_category")

    @classmethod
    def has_config_shop_goods_by_id(cls, id):
        """根据商品档案id获取商品档案"""
        return ShopGoodsProfileMapping.query.filter_by(goods_profile_id=id).count() > 0

    def has_config_shop_goods(self):
        """判断商品档案是否有配置店铺商品"""
        return ShopGoodsProfileMapping.query.filter_by(goods_profile_id=self.id).count() > 0

    """编辑/新增---商品档案"""
    @classmethod
    def edit_goods_profile(cls, goods_profile_id, goods_code, barcode, goods_category_id, goods_name):
        """编辑/新增---商品档案"""
        if (goods_code is None or goods_code.strip() == "") and (barcode is None or barcode.strip() == ""):
            raise ValidationException("商品编码和条形码不能为空")
        if goods_name is None or goods_name.strip() == "":
            raise ValidationException("商品名称不能为空")
        cls._check_profile_exist(goods_code, barcode, goods_profile_id)
        if goods_profile_id is None or goods_profile_id <= 0:
            model = GoodsProfiles(goods_code=goods_code, barcode=barcode, goods_category_id=goods_category_id, name=goods_name)
            model.add(True)
        else:
            model = GoodsProfiles.get(goods_profile_id)
            if model is None:
                raise ValidationException("商品档案不存在")
            model.goods_code = goods_code
            model.barcode = barcode
            model.goods_category_id = goods_category_id
            model.name = goods_name
            model.update(True)
        return model

    """检查商品档案是否存在"""
    @classmethod
    def _check_profile_exist(cls, goods_code, barcode, goods_profile_id):
        """检查商品档案是否存在"""
        if (goods_code is None or goods_code.strip() == "") and (barcode is None or barcode.strip() == ""):
            raise ValidationException("商品编码、条码不可以同时为空")
        has_goods_code_data = False
        if goods_code is not None and goods_code.strip() != "":
            if goods_profile_id is None or goods_profile_id <= 0:
                has_goods_code_data = cls.query.filter_by(goods_code=goods_code).count() > 0
            else:
                has_goods_code_data = cls.query.filter_by(goods_code=goods_code).filter(cls.id != goods_profile_id).count() > 0
        if has_goods_code_data:
            raise ValidationException("商品编码重复，无法保存")
        has_barcode_data = False
        # if barcode is not None and barcode.strip() != "":
        #     if goods_profile_id is None or goods_profile_id <= 0:
        #         has_barcode_data = cls.query.filter_by(barcode=barcode).count() > 0
        #     else:
        #         has_barcode_data = cls.query.filter_by(barcode=barcode).filter(cls.id != goods_profile_id).count() > 0
        if has_barcode_data:
            raise ValidationException("商品条码重复，无法保存")

    """删除商品档案"""
    def delete_goods_profile(self):
        """删除商品档案"""
        has_goods = self.has_config_shop_goods()
        if has_goods:
            raise ValidationException("商品档案有关联店铺商品，请先修改店铺商品后再删除")
        self.delete(True)

    @classmethod
    def paged(cls, page_num, page_size, **kwargs):
        """分页获取商品档案"""
        query_data = cls.query
        if "name" in kwargs and kwargs["name"] is not None and kwargs["name"].strip() != "":
            query_data = query_data.filter(GoodsProfiles.name.like("%" + kwargs["name"] + "%"))
        if "goods_code" in kwargs and kwargs["goods_code"] is not None and kwargs["goods_code"].strip() != "":
            query_data = query_data.filter(cls.goods_code == kwargs.get("goods_code").strip())
        if "barcode" in kwargs and kwargs["barcode"] is not None and kwargs["barcode"].strip() != "":
            query_data = query_data.filter(cls.barcode == kwargs.get("barcode").strip())
        if "category_id" in kwargs and kwargs["category_id"] is not None and kwargs["category_id"] > 0:
            query_data = query_data.filter(cls.goods_category_id == kwargs.get("category_id"))
        if "profile_code" in kwargs and kwargs["profile_code"] is not None and kwargs["profile_code"].strip() != "":
            query_data = query_data.filter(or_(cls.goods_code == kwargs.get("profile_code").strip(), cls.barcode == kwargs.get("profile_code").strip()))
        total = query_data.count()
        query_data = query_data.order_by(desc(func.coalesce(cls.updated_at, cls.created_at)), cls.id.desc())
        total_page = (total + page_size - 1) // page_size
        query_data = query_data.offset((page_num - 1) * page_size).limit(page_size).all()
        rows = []
        for item in query_data:
            row = {
                "id": item.id, "name": item.name,
                "goods_code": item.goods_code, "barcode": item.barcode,
                "category_id": item.goods_category_id if item.goods_category_id is not None else None,
                "category_name": item.category.name if item.category is not None else None,
                "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": item.updated_at.strftime("%Y-%m-%d %H:%M:%S") if item.updated_at is not None else None
            }
            rows.append(row)
        return {"total": total, "total_page": total_page, "rows": rows}

    @classmethod
    def get_profile_by_code_or_barcode(cls, goods_code, barcode):
        """根据商品编码或者商品条码获取商品档案"""
        if goods_code is not None and goods_code.strip() != "":
            models = cls.query.filter_by(goods_code=goods_code.strip())
            if models.count() > 0:
                return models.first()
            return None
        if barcode is not None and barcode.strip() != "":
            models = cls.query.filter_by(barcode=barcode.strip())
            if models.count() > 0:
                return models.first()
            return None
        return None

    @classmethod
    def get_profile_by_goods_codes(cls, goods_codes):
        """根据商品编码列表获取商品档案"""
        if goods_codes is None or len(goods_codes) == 0:
            return None
        return cls.query.filter(cls.goods_code.in_(goods_codes)).all()


class ShopGoods(BaseModel):
    """店铺商品"""
    # 所属店铺
    shop_id: Mapped[int] = mapped_column(Integer, ForeignKey("shop.id"), comment="店铺id")
    shop = relationship("Shop", backref="shop_goods")
    # 所属类目
    goods_category_id: Mapped[int] = mapped_column(Integer, ForeignKey("goods_category.id"), comment="商品分类id")
    goods_category = relationship("GoodsCategory", backref="shop_goods_category")

    sku: Mapped[str] = mapped_column(String(64), comment="商品sku")
    suite_flag: Mapped[bool]=mapped_column(Boolean, default=False, comment="是否套装商品")
    # 推荐标记
    recommend_flag: Mapped[bool]=mapped_column(Boolean, default=False, comment="是否推荐商品")
    # 零售价
    price: Mapped[float]=mapped_column(Float, comment="零售价")
    # 上下架标记
    on_sale_flag: Mapped[bool]=mapped_column(Boolean, default=False, comment="是否上架")
    # 商品卖点
    sale_point: Mapped[str]=mapped_column(String(256), comment="商品卖点")

    @classmethod
    def get_goods_name(cls,sku:str):
        """根据商品sku获取商品名称"""
        shop_goods = cls.query.filter_by(sku=sku).all()
        if not shop_goods or len(shop_goods)==0:
            raise Exception(f"商品sku:{sku}不存在，请联系管理员配置！")
        if len(shop_goods) > 1 :
            raise Exception(f"商品sku:{sku}存在重复，请联系管理员检查！")
        goods_ids=[item.id for item in shop_goods]
        mapping = ShopGoodsProfileMapping.query.filter(ShopGoodsProfileMapping.shop_goods_id.in_(goods_ids)).all()
        mapping_profile_ids = [item.goods_profile_id for item in mapping]
        profiles = GoodsProfiles.query.filter(GoodsProfiles.id.in_(mapping_profile_ids)).all()
        if profiles is None or len(profiles)==0:
            raise Exception(f"商品sku:{sku}缺少映射配置，请联系管理员配置！")
        
        if shop_goods[0].suite_flag:
            profile_list=[]
            for mapping_item in mapping:
                profile = [item for item in profiles if item.id == mapping_item.goods_profile_id]
                if len(profile) == 0:
                    continue
                profile = profile[0]
                profile_list.append(profile.name+'[产品id:'+profile.goods_code+']*'+str(mapping_item.quantity))
            return "套装商品【"+'；'.join(profile_list)+"】"
        else:
            return profiles[0].name+'[产品id:'+profiles[0].goods_code+']'

    @classmethod
    def has_goods(cls, shop_id):
        """判断店铺是否有商品"""
        return cls.query.filter_by(shop_id=shop_id).count() > 0

    """新增店铺商品"""
    @classmethod
    def add_goods(cls, shop_id, category_id, sku, suite_flag, recommend_flag, price, sale_flag, sale_point, profile_tuple: list[tuple[int, int, int]]):
        """
        新增店铺商品
        :param shop_id: 所属店铺
        :param category_id: 所属类目
        :param sku: 商品sku
        :param suite_flag: 是否套装商品
        :param recommend_flag: 是否推荐商品
        :param price: 零售价
        :param sale_flag: 上下架标记
        :param sale_point: 商品卖点
        :param profile_tuple: 关联的商品档案列表[(商品档案id, 配置数量, 商品mapping表id)]
        """
        cls.check_sku_exist(sku)
        cls._check_profile_repeat(profile_tuple)
        if profile_tuple is None or len(profile_tuple) == 0:
            raise ValidationException("关联的商品档案不能为空")
        goods = ShopGoods(
            shop_id=shop_id, goods_category_id=category_id, sku=sku,
            suite_flag=suite_flag, recommend_flag=recommend_flag, price=price, on_sale_flag=sale_flag, sale_point=sale_point
        )
        if len(profile_tuple) > 1:
            goods.suite_flag = True
        elif len(profile_tuple) == 1:
            profile_id, quantity, current_id = profile_tuple[0]
            if quantity > 1:
                goods.suite_flag = True
        goods.session.add(goods)
        goods.session.flush()

        for tuple_item in profile_tuple:
            goods_profile_id, quantity, current_id = tuple_item
            if quantity is None or quantity <= 0:
                raise ValidationException("关联商品档案数量不能为空")
            mapping = ShopGoodsProfileMapping(goods_profile_id=goods_profile_id, shop_goods_id=goods.id, quantity=quantity)
            goods.session.add(mapping)
        goods.session.commit()
        return goods

    """编辑店铺商品"""
    def update_goods(self, shop_id, category_id, sku, suite_flag, recommend_flag, price, sale_flag, sale_point, profile_tuple: list[tuple[int, int, int]]):
        """
        编辑店铺商品
        :param shop_id: 所属店铺
        :param category_id: 所属类目
        :param sku: 商品sku
        :param suite_flag: 是否套装商品
        :param recommend_flag: 是否推荐商品
        :param price: 零售价
        :param sale_flag: 上下架标记
        :param sale_point: 商品卖点
        :param profile_tuple: 关联的商品档案列表[(商品档案id, 配置数量, 商品mapping表id)]
        """
        ShopGoods.check_sku_exist(sku, self.id)
        ShopGoods._check_profile_repeat(profile_tuple)
        self.shop_id = shop_id
        self.goods_category_id = category_id
        self.sku = sku
        self.suite_flag = suite_flag
        self.recommend_flag = recommend_flag
        self.price = price
        self.on_sale_flag = sale_flag
        self.sale_point = sale_point
        self.note = None
        if len(profile_tuple) > 1:
            self.suite_flag = True
        elif len(profile_tuple) == 1:
            profile_id, quantity, current_id = profile_tuple[0]
            if quantity > 1:
                self.suite_flag = True
        args_mapping_ids = [item[2] for item in profile_tuple if item[2] is not None and item[2] > 0]

        mapping = ShopGoodsProfileMapping.query.filter_by(shop_goods_id=self.id)
        mapping_ids = [item.id for item in mapping]

        # 要删除的mapping_id
        del_mapping_ids = [item for item in mapping_ids if item not in args_mapping_ids]
        for del_mapping_id in del_mapping_ids:
            del_mapping = ShopGoodsProfileMapping.query.filter_by(id=del_mapping_id).first()
            self.session.delete(del_mapping)

        # 要编辑的mapping_id
        edit_mapping_ids = [item for item in args_mapping_ids if item in mapping_ids]
        for edit_mapping_id in edit_mapping_ids:
            edit_mapping = ShopGoodsProfileMapping.query.filter_by(id=edit_mapping_id).first()
            edit_mapping.quantity = [item[1] for item in profile_tuple if item[2] == edit_mapping_id][0]

        # 新增的，mapping_id为空
        args_add_profile_ids = [item[0] for item in profile_tuple if item[2] is None or item[2] <= 0]
        for add_profile_id in args_add_profile_ids:
            add_mapping = ShopGoodsProfileMapping(goods_profile_id=add_profile_id, shop_goods_id=self.id)
            add_mapping.quantity = [item[1] for item in profile_tuple if item[0] == add_profile_id][0]
            self.session.add(add_mapping)

        self.session.commit()

    @classmethod
    def check_sku_exist(cls, sku, goods_id=None):
        """检查商品sku是否存在"""
        if sku is None or sku.strip() == "":
            raise ValidationException("商品sku不能为空")
        if goods_id is None or goods_id <= 0:
            has_sku_data = cls.query.filter_by(sku=sku).count() > 0
        else:
            has_sku_data = cls.query.filter_by(sku=sku).filter(cls.id != goods_id).count() > 0
        if has_sku_data:
            raise ValidationException("商品sku重复，已经存在对应的商品，无法保存")

    # 校验参数文档是否重复
    @classmethod
    def _check_profile_repeat(cls, profile_tuple: list[tuple[int, int, int]]):
        """校验参数文档是否重复"""
        if profile_tuple is None or len(profile_tuple) == 0:
            raise ValidationException("关联的商品档案不能为空")
        profile_ids = [item[0] for item in profile_tuple]
        if len(profile_ids) != len(set(profile_ids)):
            raise ValidationException("商品档案信息配置不能重复")

    """获取店铺商品详情"""
    def detail_info(self):
        """获取店铺商品详情"""
        detail = {
            "id": self.id, "sku": self.sku,
            "shop_id": self.shop_id, "shop_name": self.shop.name if self.shop is not None else None,
            "goods_category_id": self.goods_category_id if self.goods_category_id is not None else None,
            "goods_category_name": self.goods_category.name if self.goods_category is not None else None,
            "suite_flag": self.suite_flag, "recommend_flag": self.recommend_flag, "on_sale_flag": self.on_sale_flag,
            "price": self.price, "sale_point": self.sale_point
        }
        mapping = ShopGoodsProfileMapping.query.filter_by(shop_goods_id=self.id).all()
        mapping_profile_ids = [item.goods_profile_id for item in mapping]
        profiles = GoodsProfiles.query.filter(GoodsProfiles.id.in_(mapping_profile_ids)).all()

        profile_list = []
        for mapping_item in mapping:
            profile = [item for item in profiles if item.id == mapping_item.goods_profile_id]
            if len(profile) == 0:
                continue
            profile = profile[0]
            profile_list.append({
                "profile_id": profile.id, "name": profile.name,
                "goods_code": profile.goods_code, "barcode": profile.barcode,
                "quantity": mapping_item.quantity,
                "mapping_id": mapping_item.id
            })
        detail["profiles"] = profile_list
        return detail

    def delete_shop_goods(self):
        """删除店铺商品"""
        mapping = ShopGoodsProfileMapping.query.filter_by(shop_goods_id=self.id).all()
        for item in mapping:
            self.session.delete(item)
        self.session.delete(self)
        self.session.commit()

    @classmethod
    def paged(cls, page_num, page_size, **kwargs):
        """分页获取店铺商品"""
        query_data = cls.query
        if "category_id" in kwargs and kwargs["category_id"] is not None and kwargs["category_id"] > 0:
            query_data = query_data.filter(cls.goods_category_id == kwargs.get("category_id"))
        if "sku" in kwargs and kwargs["sku"] is not None and kwargs["sku"].strip() != "":
            query_data = query_data.filter(cls.sku == kwargs.get("sku"))
        if "shop_id" in kwargs and kwargs["shop_id"] is not None and kwargs["shop_id"] > 0:
            query_data = query_data.filter(cls.shop_id == kwargs.get("shop_id"))
        if 'suite_flag' in kwargs and kwargs['suite_flag'] is not None:
            query_data = query_data.filter(cls.suite_flag == kwargs.get('suite_flag'))
        if 'recommend_flag' in kwargs and kwargs['recommend_flag'] is not None:
            query_data = query_data.filter(cls.recommend_flag == kwargs.get('recommend_flag'))
        if 'on_sale_flag' in kwargs and kwargs['on_sale_flag'] is not None:
            query_data = query_data.filter(cls.on_sale_flag == kwargs.get('on_sale_flag'))
        if 'is_empty_profile' in kwargs and kwargs['is_empty_profile'] is not None:
            if kwargs['is_empty_profile']:
                query_data = query_data.filter(cls.note.isnot(None))
            else:
                query_data = query_data.filter(cls.note.is_(None))
        if 'goods_code' in kwargs and kwargs['goods_code'] is not None and kwargs['goods_code'].strip() != "":
            query_data = query_data.join(ShopGoodsProfileMapping, ShopGoodsProfileMapping.shop_goods_id == cls.id).join(GoodsProfiles, GoodsProfiles.id == ShopGoodsProfileMapping.goods_profile_id).filter(GoodsProfiles.goods_code == kwargs.get('goods_code'))
        total_count = query_data.count()
        if total_count == 0:
            return {"total": 0, "total_page": 0, "rows": []}
        total_page = (total_count + page_size - 1) // page_size
        query_data = query_data.order_by(desc(func.coalesce(cls.updated_at, cls.created_at)), cls.id.desc()).offset((page_num - 1) * page_size).limit(page_size).all()
        rows = []
        goods_ids = [item.id for item in query_data]
        mapping = ShopGoodsProfileMapping.query.filter(ShopGoodsProfileMapping.shop_goods_id.in_(goods_ids)).all()
        mapping_profile_ids = [item.goods_profile_id for item in mapping]
        profiles = GoodsProfiles.query.filter(GoodsProfiles.id.in_(mapping_profile_ids)).all()
        for item in query_data:
            row = {
                "id": item.id, "sku": item.sku,
                "shop_id": item.shop_id, "shop_name": item.shop.name if item.shop is not None else None,
                "goods_category_id": item.goods_category_id if item.goods_category_id is not None else None,
                "goods_category_name": item.goods_category.name if item.goods_category is not None else None,
                "suite_flag": item.suite_flag, "recommend_flag": item.recommend_flag, "on_sale_flag": item.on_sale_flag,
                "price": item.price, "sale_point": item.sale_point,
                "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": item.updated_at.strftime("%Y-%m-%d %H:%M:%S") if item.updated_at is not None else None,
                "note": item.note,
                "profiles": []
            }
            for mapping_item in mapping:
                if mapping_item.shop_goods_id == item.id:
                    profile = [item for item in profiles if item.id == mapping_item.goods_profile_id]
                    if len(profile) == 0:
                        continue
                    profile = profile[0]
                    row["profiles"].append({
                        "profile_id": profile.id, "name": profile.name,
                        "goods_code": profile.goods_code, "barcode": profile.barcode,
                        "quantity": mapping_item.quantity,
                        "mapping_id": mapping_item.id
                    })
            row["profiles_name"] = "<br/>".join([item.get("name", "") for item in row.get("profiles", [])]) if len(row.get("profiles", [])) > 0 else None
            rows.append(row)
        return {"total": total_count, "total_page": total_page, "rows": rows}


class ShopGoodsProfileMapping(BaseModel):
    """店铺商品档案映射"""
    # 所属商品档案
    goods_profile_id: Mapped[int] = mapped_column(Integer, comment="商品档案id")
    # 所属店铺商品
    shop_goods_id: Mapped[int] = mapped_column(Integer, comment="店铺商品id")
    # 商品档案数量
    quantity: Mapped[int] = mapped_column(Integer, comment="配置数量")


class PromptType(BaseModel):
    """提示类型"""
    pid: Mapped[Optional[int]] = mapped_column(Integer, default=None, comment="提示类型id")

    @classmethod
    def tree(cls):
        """获取提示类型树"""
        prompt_types = cls.query.all()
        tree_data = []
        parent_prompt_types = [item for item in prompt_types if item.pid is None]
        for parent_prompt_type in parent_prompt_types:
            tree_data.append({
                "id": parent_prompt_type.id,
                "name": parent_prompt_type.name,
                "pid": parent_prompt_type.pid,
                "children": cls._recursion(prompt_types, parent_prompt_type.id)
            })
        return tree_data

    @classmethod
    def _recursion(cls, prompt_types, pid=None):
        """递归获取提示类型"""
        prompt_type_list = []
        for prompt_type in prompt_types:
            if prompt_type.pid == pid:
                prompt_type_list.append({
                    "id": prompt_type.id,
                    "name": prompt_type.name,
                    "pid": prompt_type.pid,
                    "children": cls._recursion(prompt_types, prompt_type.id)
                })
        return prompt_type_list

    @classmethod
    def add_update(cls, id: Optional[int], name: Optional[str], note: Optional[str], pid: Optional[int]):
        if pid is not None and pid <= 0:
            pid = None
        if id is not None and id <= 0:
            id = None
        # 新增
        if id is None:
            model = cls(name=name, note=note, pid=pid)
            model.add(True)
            return model
        # 更新
        model = cls.get(id)
        if name == model.name and note == model.note and pid == model.pid:
            return model
        if name != model.name:
            prompts = PromptModel.query.filter_by(prompt_type_id=model.id).all()
            for prompt in prompts:
                prompt.prompt_type = name
                prompt.update()
        model.name = name
        model.note = note
        model.pid = pid
        model.update(True)
        return model

    def prompt_type_delete(self):
        if PromptModel.query.filter_by(prompt_type_id=self.id).count() > 0:
            raise ValidationException("该提示类型下存提示词，无法删除")
        self.delete(True)



# 系统配置
class ConfigModel(BaseModel):
    config_key = Column(String(50), nullable=False, comment="配置项", unique=True)
    config_value = Column(String(2000), comment="配置值")

    def __repr__(self):
        attrs = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
        return f"{self.__class__.__name__}({', '.join([f'{attr}={getattr(self, attr)}' for attr in attrs])})"

    def obj_to_dict(self):
        """
        将对象转为字典
        """
        return {
            "id": self.id,
            "note": self.note,
            "caption": self.caption,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at is not None else None,
            "config_key": self.config_key,
            "config_value": self.config_value
        }

    @classmethod
    def config_page(cls, **kwargs):
        """
        获取配置列表
        :param kwargs: page=1, pagesize=10
        :return:
        """
        page = int(kwargs.get("page", 1))
        pagesize = int(kwargs.get("pagesize", 10))
        configs = cls.query
        if 'module' in kwargs:
            configs = configs.filter(cls.config_module == kwargs['module'])
        if 'config_key' in kwargs:
            configs = configs.filter(cls.config_key == kwargs['config_key'])
        total = configs.count()
        data = [config.obj_to_dict() for config in configs.offset((page - 1) * pagesize).limit(pagesize).all()]
        if total == 0:
            return {"total_records": 0, "total_pages": 0, "data": []}
        return {"total_records": total, "total_pages": (total + pagesize - 1) // pagesize, "data": data}

    @classmethod
    def config_all_update(cls, config_all: dict):

        this_session = cls().session

        db_config = cls.query.filter(cls.config_key.in_(config_all.keys())).all()
        for config in db_config:
            config.config_value = config_all[config.config_key]['config_value']
            config.update()

        this_session.commit()

    @classmethod
    def config_base_info(cls) -> 'ConfigModel':
        """
        获取配置列表
        :return:
        """
        file_configs = parse_config('./src/configs/server_config.py')
        if len(file_configs.keys()) > 0:
            return cls(config_key="sys_config.base", config_value=json.dumps(file_configs, ensure_ascii=False))
        return cls(config_key="sys_config.base")

    @classmethod
    def config_list(cls) -> list['ConfigModel']:
        """
        获取配置列表
        :return:
        """
        configs = cls.query.all()
        configs.append(cls.config_base_info())
        return configs

    @classmethod
    def config_dict_json(cls) -> dict:
        """
        获取配置列表
        :return:
        """
        configs = cls.config_list()
        config_dict = {}
        for config in configs:
            tmp_config = {"id": config.id, "config_key": config.config_key, "config_value": config.config_value}
            tmp_value = config.config_value
            try:
                if not isinstance(json.loads(tmp_value), dict):
                    tmp_config["config_value"] = json.dumps({"dynamic_data": tmp_value}, ensure_ascii=False)
            except:
                tmp_config["config_value"] = json.dumps({"dynamic_data": config.config_value}, ensure_ascii=False)
            config_dict[config.config_key] = tmp_config
        return config_dict


class MCPToolProvider(BaseModel):

    server_identifier: Mapped[str] = mapped_column(String(64), nullable=False,comment="唯一标识")
    
    server_url: Mapped[str] = mapped_column(Text, nullable=False,comment="服务器地址")

    server_url_hash: Mapped[str] = mapped_column(String(64), nullable=False, comment="服务器地址哈希")

    encrypted_credentials: Mapped[str] = mapped_column(Text, nullable=True, comment="加密凭据")

    authed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False,comment="是否认证")

    tools: Mapped[str] = mapped_column(Text, nullable=False, default="[]",comment="工具列表")

    selected_tools: Mapped[str] = mapped_column(Text, nullable=False, default="[]",comment="选中的工具列表")

    timeout: Mapped[float] = mapped_column(Float, nullable=False, server_default="30",comment="超时时间")

    sse_read_timeout: Mapped[float] = mapped_column(Float, nullable=False, server_default="300",comment="SSE读取超时时间")

    encrypted_headers: Mapped[str | None] = mapped_column(Text, nullable=True,comment="请求头")

    unique_code = Column(String(200), nullable=True, comment='唯一编码', default=None)

    
    @classmethod
    def create_mcp_provider(cls,name:str,server_identifier: str, server_url: str,headers: dict[str, str] | None = None,timeout: float = 30, sse_read_timeout: float = 300) -> 'MCPToolProvider':
        """
        创建MCP工具提供方
        :param name: 名称
        :param server_identifier: 唯一标识
        :param server_url: 服务器地址
        :return:
        """
        existing_provider =cls.query.filter(
            or_(
                cls.name==name,
                cls.server_identifier==server_identifier,
                cls.server_url==server_url
            )
        ).first()

        if existing_provider:
            if existing_provider.server_identifier == server_identifier:
                raise ValueError("server_identifier already exists")
            if existing_provider.server_url == server_url:
                raise ValueError("server_url already exists")
            if existing_provider.name == name:
                raise ValueError("name already exists")
        
        encrypted_headers = None
        if headers:
            encrypted_headers=json.dumps(headers, ensure_ascii=False)

        new_provider = cls(
            name=name,
            server_identifier=server_identifier,
            server_url=server_url,
            tools="[]",
            authed=False,
            encrypted_credentials="{}",
            encrypted_headers=encrypted_headers,
            timeout=timeout,
            sse_read_timeout=sse_read_timeout
        )
        
        reconnect_result = cls.connect_mcp_provider(0,server_url,headers=headers)
        if reconnect_result:
            new_provider.authed = reconnect_result["authed"]
            new_provider.tools = reconnect_result["tools"]
            new_provider.encrypted_credentials = reconnect_result["encrypted_credentials"]
        new_provider.unique_code = str(uuid.uuid4())
        new_provider.add(commit=True)

        return new_provider
    
    @classmethod
    def update_mcp_provider(cls,id:int,name:str,server_identifier: str, server_url: str,headers: dict[str, str] | None = None,timeout: float = 30, sse_read_timeout: float = 300)-> 'MCPToolProvider':
        """
        更新MCP工具提供方
        :return:
        """
        provider_instance=cls.get(id)

        #检查名称是否重复
        existing_provider =cls.query.filter(
            or_(
                cls.name==name,
                cls.server_identifier==server_identifier,
                cls.server_url==server_url
            )
        ).first()
        if existing_provider:
            if existing_provider.id != id:
                if existing_provider.server_identifier == server_identifier:
                    raise ValueError("server_identifier already exists")
                if existing_provider.server_url == server_url:
                    raise ValueError("server_url already exists")
                if existing_provider.name == name:
                    raise ValueError("name already exists")

        provider_instance.name=name
        provider_instance.server_identifier=server_identifier
        provider_instance.server_url=server_url

        encrypted_headers = None
        if headers:
            encrypted_headers=json.dumps(headers, ensure_ascii=False)
        provider_instance.encrypted_headers=encrypted_headers
        provider_instance.timeout=timeout
        provider_instance.sse_read_timeout=sse_read_timeout

        reconnect_result = cls.connect_mcp_provider(id,server_url,headers=headers)
        if reconnect_result:
            provider_instance.authed = reconnect_result["authed"]
            provider_instance.tools = reconnect_result["tools"]
            provider_instance.encrypted_credentials = reconnect_result["encrypted_credentials"]


        provider_instance.update(commit=True)
        
        return provider_instance

    @classmethod
    def select_mcp_tools(cls,id:int,selected_tools:list[str]):
        """
        选择MCP工具
        :return:
        """
        provider_instance=cls.get(id)

        provider_instance.selected_tools=json.dumps(selected_tools,ensure_ascii=False)

        provider_instance.update(commit=True)

    @classmethod
    def list_mcp_tools_from_server(cls,id:int):
        """
        从服务器获取MCP工具列表
        :return:
        """
        provider_instance=cls.get(id)

        connect_result=cls.connect_mcp_provider(id,provider_instance.server_url,headers=provider_instance.headers)

        if connect_result:
            provider_instance.authed = connect_result["authed"]
            provider_instance.tools = connect_result["tools"]
            provider_instance.encrypted_credentials = connect_result["encrypted_credentials"]

        provider_instance.update(commit=True)

        return provider_instance
    
    @classmethod
    def connect_mcp_provider(cls,id: int,server_url:str,headers: dict[str, str] | None = None):
        """
        连接MCP工具提供方
        :return:
        """
        try:
            with MCPClient(
                server_url=server_url,
                provider_id=id,
                headers=headers
            ) as mcp_client:
                tools = mcp_client.list_tools()
                return {
                    "authed": True,
                    "tools": json.dumps([tool.model_dump() for tool in tools],ensure_ascii=False),
                    "encrypted_credentials": "{}",
                }
        except MCPAuthError as e:
            raise ValueError(f"Auth Failed to re-connect MCP server: {e}") from e
            # return {"authed": False, "tools": "[]", "encrypted_credentials": "{}"}
        except MCPError as e:
            raise ValueError(f"Failed to re-connect MCP server: {e}") from e

    @classmethod
    def delete_mcp_provider(cls,id: int):
        """
        删除MCP工具提供方
        :return:
        """
        provider_instance=cls.get(id)
        provider_instance.delete(commit=True)

    
    @classmethod
    def get_tool_list(cls):
        """
        获取MCP工具列表
        :return:
        """
        providers=cls.query.all()
        tools=[]
        from src.database.helper import adapt_mcp_tool
        for provider in providers:
            for tool in provider.mcp_tools:
                if tool.name in provider.selected_mcp_tools:
                    tools.append(adapt_mcp_tool(provider,tool))
        return tools
    
    @property
    def credentials(self) -> dict[str, Any]:
        try:
            return cast(dict[str, Any], json.loads(self.encrypted_credentials)) or {}
        except Exception:
            return {}

    @property
    def mcp_tools(self) -> list[Tool]:
        return [Tool(**tool) for tool in json.loads(self.tools)]
    @property
    def selected_mcp_tools(self) -> list[str]:
        return ast.literal_eval(self.selected_tools)

    @property
    def decrypted_credentials(self) -> dict[str, Any]:
        return self.credentials
    
    @property
    def headers(self) -> dict[str, str]|None:
        return json.loads(self.encrypted_headers) if self.encrypted_headers else None

    def update_mcp_provider_credentials(self,credentials: dict[str, Any], authed: bool = False):
        self.encrypted_credentials = json.dumps({**self.credentials, **credentials},ensure_ascii=False)
        self.authed = authed
        if not authed:
            self.tools = "[]"
        self.update(True)
