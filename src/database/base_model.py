from __future__ import annotations

from dataclasses import dataclass
import uuid
import typing as t
import re
# from pymssql._mssql import Iterable
from fastapi import Depends
from sqlalchemy import select, Table, MetaData, insert, func, Column, event
from sqlalchemy import DateTime, String, text, Integer
from sqlalchemy.orm import DeclarativeBase, Session, SessionEvents
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from datetime import datetime
from sqlalchemy.orm import declared_attr

from src.database.db_session import session_scope

from .orm_extensions.soft_delete_ignored_table import IgnoredTable
from .orm_extensions.soft_delete_mixin import generate_soft_delete_mixin_class
from typing import List, Tuple
# 自动添加历史记录相关定义
from sqlalchemy_history import make_versioned


make_versioned(user_cls=None)
# 定义历史记录基类，继承此类，会自动创建历史记录；首次创建数据库表，需要先执行configure_mappers()，会自动创建想历史记录需要的表
class HistoryBase(DeclarativeBase):
    pass

class SoftDeleteMixin(generate_soft_delete_mixin_class(
    # 添加需要排除软删除的类，即使该类拥有soft-delete 属性列
    ignored_tables=[IgnoredTable(table_schema=None, name='sdtablethatshouldnotbesoftdeleted'),
                    IgnoredTable(table_schema=None, name='transaction')] #transaction 是版本历史记录模块自动传教的类
)):
    # type hint for autocomplete IDE support
    deleted_at: datetime

class BaseModel(DeclarativeBase, SoftDeleteMixin):
    query=session_scope.query_property()
    _session = None
    @property
    def session(self):
        if self._session is None:
            self._session = session_scope()
        return self._session
    # 自动根据类名创建表名
    @declared_attr.directive
    def __tablename__(cls) -> str:   
        """驼峰命名转下划线"""
        name = cls.__name__
        if '_' not in name:
            name = re.sub(r'([a-z])([A-Z])', r'\1_\2', name)
        else:
            raise ValueError(f'{name}字符中包含下划线，无法转换')
        return name.lower()
    # 主键：系统标识使用
    # id: Mapped[str] = Column(String, primary_key=True, default=uuid.uuid1().hex, comment="主键：系统标识使用")    
    id: Mapped[int] = mapped_column(primary_key=True, comment="主键：系统标识使用")

    name: Mapped[str] = mapped_column(String(255), nullable=True, comment="名称")
    # 编码：用户使用
    code: Mapped[str] = mapped_column(String(255), nullable=True, comment="编码：用户使用")
    # 备注：选填  
    note: Mapped[str] = mapped_column(String(1000), nullable=True, comment="备注：选填")
    # 介绍：选填
    caption: Mapped[str] = mapped_column(String(512), nullable=True, comment="介绍：选填")

    # 创建时间 sqlite 服务端 默认时间戳函数
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(),
                                                comment="创建时间")
    # 版本控制：系统使用
    ver = mapped_column(Integer, nullable=False)
    __mapper_args__ = {"version_id_col": ver}
    # 最后一次的更新时间戳：系统使用    
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, comment="最后修改时间")
    # 删除的时间戳，删除标志：系统使用
    deleted_at: Mapped[str] = mapped_column(String(50), default=None, nullable=True,
                                            comment="系统软删除的时间，正常查询应过滤")

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id}>"

    def add(self, commit=False):
        self.session.add(self)
              
        self.__is_commit(commit)

    def delete(self, commit=False):
        self.session.delete(self)
              
        self.__is_commit(commit)
    
    def update(self, commit=False):  
        self.__is_commit(commit)

    def update_with_foreign_key_none(self, commit=False):
        """设置当前对象的外键=None的时候，调用此方法"""

        # 不存在属性，在event_before_update事件中监听，防止删除数据
        # list的集合，remove的时候，也是进入event_before_update
        self.with_foreign_key_none = True
        self.__is_commit(commit)

    @classmethod
    def get(cls, id:int):
        model = cls.query.filter_by(id=id).first()
        if not model:
            raise ValueError(f"{cls.__name__}【{id}】：未找到该数据")
        return model

    @classmethod
    def get_list_by_conditions(cls, conditions: dict):
        """
        条件获取列表
        使用方式：
        ClassName.get_list_by_conditions(conditions={"id":1})
        ClassName.get_list_by_conditions({"id":1})
        """
        return cls.query.filter_by(**conditions).all()

    def update_properties(self, **kwargs):
        """可以更新所有属性"""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __is_commit(self, commit=False):
        if commit is True:
            self.session.commit()


# TODO: session.commit() 后对象无法访问，因为session已经关闭了，需要解决重复访问问题
# TODO: 方法执行后返回受影响行数，或者是否成功

from sqlalchemy import inspect


# session.delete 会在src/utils/db_infra/orm/soft_delete_hook.py 文件的before_flush里面拦截，而不走这里
# 这里只有字类remove,用主表更新子表的操作，才会进这里 (relationship 配置了cascade='all, delete-orphan')
#  user.address.remove(user.address[0])
#  user.update()
@event.listens_for(BaseModel, 'before_delete', propagate=True)
def event_before_delete(mapper, connection, target):
    target.deleted_at = datetime.now()

    for rel_name, rel in inspect(target.__class__).relationships.items():
        if rel.cascade.delete_orphan:
            raise Exception(target.__class__.__name__ + '类的relationship配置有误，暂不支持delete_orphan')

    # 即使将对象从当前回话移除，或者return False 或者两者一起，也无法删除
    # from sqlalchemy.orm import object_session
    # cur_session = object_session(target)
    # cur_session.expunge(target)
    # cur_session.add(target)
    # cur_session.execute()
    # return False


# event_before_update
# 修改字表数据，关联id与删除时间，是以下情况，会将子表的外键id清空，此事件用于回写关联外键id
# (relationship 配置了cascade='all')
#  user.address.remove(user.address[0])
#  user.update()
@event.listens_for(BaseModel, 'before_update', propagate=True)
def event_before_update(mapper, connection, target):
    # 此事件，针对的是数据表的外键，如果外键为None，或者为0，执行更新 deleted_at时间

    # 获取主键名称    ['id']
    primary_key_names = [column.name for column in mapper.primary_key]
    if len(primary_key_names) <= 0:
        return

    # 外键名称  ['user_id']
    foreign_key_names = [foreign_key.name for relationship in mapper.relationships for foreign_key in relationship._calculated_foreign_keys ]
    if not foreign_key_names:
        return

    # 当前对象列名['user_id', 'email_address', 'id', 'name',  'created_at', 'ver', 'updated_at', 'deleted_at']
    target_columns = [column.name for column in inspect(target).mapper.columns]
    foreign_key_names_new1 = []
    foreign_key_names_new = []
    for target_columns_item in target_columns:
        if target_columns_item in foreign_key_names:
            foreign_key_names_new1.append(target_columns_item)
            try:
                getattr(target, target_columns_item)
            except Exception as e:
                continue
            if getattr(target, target_columns_item) is None:
                foreign_key_names_new.append(target_columns_item)

    if not foreign_key_names_new:
        return

    if len(foreign_key_names_new1) != len(foreign_key_names_new):
        return

    # 当前提交修改数据  {'user_id': 1}
    committed_state = inspect(target).committed_state

    committed_state_new = {}

    for key in foreign_key_names_new:
        if key not in committed_state:
            continue
        else:
            if committed_state[key] is None:
                continue
            else:
                committed_state_new[key] = committed_state[key]
    if not committed_state_new:
        return
    if hasattr(target, 'with_foreign_key_none') and target.with_foreign_key_none == True:
        return
    for key, value in committed_state_new.items():
        setattr(target, key, value)
    setattr(target, 'deleted_at', datetime.now())

    # 当前session方式，会导致remove字表数据的时候，报警告，先注释，不影响
    # Usage of the 'Session.merge()' operation is not currently supported within the execution stage of the flush process.
    # Results may not be consistent.  Consider using alternative event listeners or connection-level operations instead
    # from sqlalchemy.orm import object_session
    # object_session(target).merge(target)

