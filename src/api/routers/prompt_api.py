from typing import Optional

from fastapi import APIRouter, Query, Path, Body

from src.database.models import PromptModel, PromptType

router = APIRouter(
    prefix="/api/prompts",
    tags=["提示词"],
)


@router.get("", summary="列表")
def get_prompts(
        page: int = Query(description="页码", default=1),
        pagesize: int = Query(description="每页数量", default=10),
        prompt_type_id: int = Query(description="提示词类型id, 0：未分类， 不传或者None：全部", default=None)
):
    """
    获取分页
    - @param page: 页码 默认1
    - @param pagesize: 每页数量 默认10
    - @param prompt_type_id: 提示词类型id, 0：未分类， 不传或者None：全部
    - @return: {"total_records": total_records, "total_pages": total_pages, "rows": []}
    """
    return PromptModel.get_pagination(page, pagesize, prompt_type_id)


@router.get("/{id}", summary="详情")
def get_prompt(id: int = Path(description="提示词id")):
    return PromptModel.get_detail(id)


@router.post("/add", summary="添加")
def add_prompt(name: str = Body(max_length=50, description="名称"),
               content: str = Body(description="内容"),
               prompt_type_id: Optional[int] = Body(description="提示词类型", default=None)):
    prompt = PromptModel.add_prompt(name, content, prompt_type_id)
    return {"id": prompt.id, "name": prompt.name}


@router.post("/edit/{id}", summary="修改")
def edit_prompt(id: int = Path(description="提示词id"),
                name: str = Body(max_length=50, description="名称"),
                content: str = Body(description="内容"),
                prompt_type_id: Optional[int] = Body(description="提示词类型", default=None)):
    PromptModel.get(id).update_prompt(name, content, prompt_type_id)
    return {"result": "success"}


@router.post("/delete/{id}", summary="删除")
def delete_prompt(id: int = Path(description="提示词id")):
    PromptModel.get(id).delete(True)
    return {"result": "success"}


@router.get("/{id}/versions", summary="历史版本")
def prompt_history(id: int = Path(description="提示词id")):
    """
    历史版本
    """
    return PromptModel.get(id).version_history()


@router.get("/{id}/version/detail/{ver}", summary="版本详情")
def prompt_version_detail(id: int = Path(description="提示词id"), ver: int = Path(description="版本号")):
    return PromptModel.get(id).version_history(ver)[0]


@router.get("/prompts/type/tree", summary="提示词类型树")
def prompt_type_tree():
    return PromptType.tree()


@router.post('/prompts/type/add', summary="添加提示词类型")
def prompt_type_add(name: str = Body(description="名称"),
                    note: str = Body(description="备注", default=None),
                    pid: int = Body(description='父id', default=None)):
    model = PromptType.add_update(None, name, note, pid)
    return {"id": model.id, "name": model.name, "result": "success"}


@router.post('/prompts/type/edit', summary="修改提示词类型")
def prompt_type_edit(id: int = Body(description="类型id"),
                     name: str = Body(description="名称"),
                     note: str = Body(description="备注", default=None),
                     pid: int = Body(description='父id', default=None)):
    model = PromptType.add_update(id, name, note, pid)
    return {"id": model.id, "result": "success"}


@router.post('/prompts/type/{id}/delete', summary="删除提示词类型")
def prompt_type_delete(id: int = Path(description="类型id")):
    PromptType.get(id).prompt_type_delete()
    return {"result": "success"}