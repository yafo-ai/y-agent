from typing import Optional
from uuid import uuid4


from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from contextvars import ContextVar
from src.configs.server_config import DB_CONNECT_STR

current_request_id: ContextVar[Optional[str]] = ContextVar(
    'current_request_id', default=None)

def set_current_request_id():
    current_request_id.set(uuid4().hex)

def get_current_request():
    return current_request_id.get()

def on_request_end():
    session_scope.remove()
    current_request_id.set('uuid4().hex')

engine = create_engine(DB_CONNECT_STR, echo=False,pool_pre_ping=True, pool_size=50, max_overflow=100, pool_timeout=30, pool_recycle=3600)
# 仅适用于SQLite。其他数据库不需要。 链接参数：检查同一条线？ 即需要可多线程

# 通过sessionmaker得到一个类，一个能产生session的工厂。
SessionMaker = sessionmaker(autocommit=False, autoflush=True, bind=engine) 
# 会话生成器   自动提交 自动刷新,这个很重要，对于自增主键，在add后还没commit，只有将这个设置为True，才会拿到主键
session_scope = scoped_session(SessionMaker,scopefunc=get_current_request)  # 作用域会话，可以跨请求使用同一个session

def get_engine():
    return engine

def get_scoped_session():
    db =session_scope()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    # finally:
    #     db.close()

