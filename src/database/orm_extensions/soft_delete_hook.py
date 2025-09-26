"""This module is responsible for activating the query rewriter."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.event import listens_for
from sqlalchemy.orm import ORMExecuteState, Session
from sqlalchemy.orm import attributes


from .soft_delete_ignored_table import IgnoredTable
from .soft_delete_rewriter import SoftDeleteRewriter





global_rewriter: Optional[SoftDeleteRewriter] = None


def activate_soft_delete_hook(
    deleted_field_name: str, disable_soft_delete_option_name: str, ignored_tables: List[IgnoredTable]
):
    """Activate an event hook to rewrite the queries."""

    global global_rewriter
    global_rewriter = SoftDeleteRewriter(
        deleted_field_name=deleted_field_name,
        disable_soft_delete_option_name=disable_soft_delete_option_name,
        ignored_tables=ignored_tables,
    )

# https://www.osgeo.cn/sqlalchemy/orm/session_events.html
# session.delete() 是一个工作单元方法，被 before_delete 和 after_delete 截获。
# do_orm_execute钩子仅适用于传递给 session.execute() 的对象：
# https://docs.sqlalchemy.org/en/20/orm/session_events.html#basic-query-interception 
# 会话 Events.do_orm_execute() 首先用于拦截任何类型的查询，包括由 Query 发出的 1.x 样式的查询，
# 以及当启用 ORM 的 2.0 样式 select()、update() 或 delete() 构造交付给 Session.execute() 时也就是说，删除构造记录在：
# https://docs.sqlalchemy.org/en/20/core/dml.html#sqlalchemy.sql.expression.delete https://docs.sqlalchemy.org/en/20/tutorial/orm_data_manipulation.html#bulk-multi-row-insert-upsert-update-and-delete 
# 的教程试图将 Session 用于工作单元模式（即 Session.delete()）
# 与“批量”INSERT/UPDATE/DELETE 的概念（即 session.execute（delete()））进行对比。
    @listens_for(Session, "do_orm_execute")
    def _do_orm_execute(orm_execute_state):
        if (
            orm_execute_state.is_select or orm_execute_state.is_delete and
            not orm_execute_state.is_column_load and
            not orm_execute_state.is_relationship_load
        ):
            
            # Rewrite the statement
            adapted = global_rewriter.rewrite_statement(orm_execute_state.statement)

            # Replace the statement
            orm_execute_state.statement = adapted
            # 可以尝试一下写法 是否可以省略 rewriter.py中的 写法
            # orm_execute_state.statement = orm_execute_state.statement.options(with_loader_criteria(SoftDeleteMixin,
            # lambda cls: cls.deleted_at.is_(None),include_aliases=True,))
# def versioned_session(session):
    # 拦截由session.add update delete 发起的数据库操作
    @listens_for(Session, "before_flush")
    def before_flush(session, flush_context, instances):

        # 拦截session.add
        for instance in session.new:
            # if isinstance(instance, BaseModel): # 这里可以判断是否是继承自BaseModel的类
            from sqlalchemy import inspect
            for rel_name, rel in inspect(instance.__class__).relationships.items():
                if rel.cascade.delete_orphan:
                    raise Exception(instance.__class__.__name__ + '类的relationship配置有误，暂不支持delete_orphan')
            instance.created_at = datetime.now()        
        # 拦截session. 更新 对象
        for instance in session.dirty:
            from sqlalchemy import inspect
            for rel_name, rel in inspect(instance.__class__).relationships.items():
                if rel.cascade.delete_orphan:
                    raise Exception(instance.__class__.__name__ + '类的relationship配置有误，暂不支持delete_orphan')
            instance.updated_at = datetime.now()
        # 拦截session.delete
        for instance in session.deleted:
            from sqlalchemy import inspect
            for rel_name, rel in inspect(instance.__class__).relationships.items():
                if rel.cascade.delete_orphan:
                    raise Exception(instance.__class__.__name__ + '类的relationship配置有误，暂不支持delete_orphan')
            instance.deleted_at = datetime.now()
            session.add(instance)