from fastapi import APIRouter, Body, Path
from ...database.models import Category

router = APIRouter(
    prefix="/api/categories",
    tags=["知识库类目"],
)


@router.get("/", summary="列表")
def get_categories(knowledgebase_id: int | None = None):
    """知识库类目列表"""
    return Category.get_list(knowledgebase_id)


# 类目详情
@router.get("/get/{id}", summary="详情")
def get_category(id: int = Path(description="类目id")):
    return Category.get(id).detail()


# 添加类目
@router.post("/add", summary="添加类目")
def category_add(name: str = Body(max_length=50, description="名称"),
                 caption: str = Body(max_length=200, description="介绍"),
                 knowledgebase_id: int = Body(description="知识库id"),
                 p_id: int | None = Body(description="所属类目id", default=None)):
    return {"id": Category.add_category_model(name, caption, knowledgebase_id, p_id).id}


@router.post("/edit/{id}", summary="编辑")
def category_edit(id: int = Path(description="类目id"),
                  name: str = Body(max_length=50, description="名称"),
                  caption: str = Body(max_length=200, description="介绍"),
                  knowledgebase_id: int = Body(description="知识库id"),
                  p_id: int | None = Body(description="所属类目id", default=None)):
    """编辑类目"""
    model = Category.get(id)
    model.edit_category_model(name, caption, knowledgebase_id, p_id)
    return {"result": "success"}


@router.post("/delete/{id}", summary="删除")
def category_delete(id: int = Path(description="类目id")):
    Category.get(id).delete_category_model()
    return {"result": "success"}
