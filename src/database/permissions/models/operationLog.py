from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base_model import BaseModel


class OperationLog(BaseModel):
    """
    操作日志
    """
    ip_address: Mapped[str] = mapped_column(String(50), nullable=False, comment="IP地址")
    address: Mapped[str] = mapped_column(String(255), nullable=True, comment="地址")
    api_path: Mapped[str] = mapped_column(String(255), nullable=False, comment="API路径")
    request_params: Mapped[str] = mapped_column(String(1000), nullable=True, comment="请求参数")
    request_body: Mapped[str] = mapped_column(String(1000), nullable=True, comment="请求体")
    user_id: Mapped[int] = mapped_column(Integer, nullable=True, comment="用户ID")
    user_name: Mapped[str] = mapped_column(String(255), nullable=True, comment="用户名")
    method: Mapped[str] = mapped_column(String(20), nullable=True, comment="请求方法")
    duration: Mapped[int] = mapped_column(Integer, nullable=True, comment="请求耗时(ms)")
    status_code: Mapped[int] = mapped_column(Integer, nullable=True, comment="状态码")

    # 分页列表
    @classmethod
    def paged(cls, page_num: int, page_size: int, conditions: dict):
        query = cls.query.filter_by(**conditions)
        total = query.count()
        query = query.limit(page_size).offset((page_num - 1) * page_size)
        items = query.all()
        total_page = (total + page_size - 1) // page_size
        return {"total": total, "total_page": total_page, "rows": items}
