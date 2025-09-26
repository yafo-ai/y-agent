from fastapi import APIRouter, Body

from src.database.permissions.models.operationLog import OperationLog

router = APIRouter(
    prefix="/api/operator",
    tags=["审计管理"],
)


@router.post("/paged", summary="列表")
def operator_paged_logs(page_index: int = Body(default=1, description="页码"),
                        pagesize: int = Body(default=10, description="每页数量"),
                        user_id: int = Body(default=None, description="用户ID")):
    conditions = {}
    if user_id is not None:
        conditions = {"user_id": user_id}
    return OperationLog.paged(page_index, pagesize, conditions)
