import os
import uuid

import pandas as pd
from fastapi import APIRouter, Depends, Body, Path, Query, UploadFile
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

from src.api.customer_exception import ValidationException
from src.api.goods_jobs import import_goods_profile_task, import_goods_task
from src.database.db_session import get_scoped_session
from src.database.models import Shop, Platforms, GoodsCategory, GoodsProfiles, ShopGoods

router = APIRouter(
    prefix="/api/goods",
    tags=["商品管理"],
)


# region 平台
@router.post("/platform/add", summary="编辑/新增---平台")
def add_platform(id: int | None = Body(default=None, description="平台ID"),
                 platform_name: str | None = Body(default=None, description="平台名称")):
    """编辑/新增---平台信息"""
    model = Platforms.edit_platform(id, platform_name)
    return {"result": "success", "id": model.id}


@router.post("/platform/delete/{id}", summary="删除---平台")
def delete_platform(id: int = Path(..., description="平台ID")):
    """删除平台信息"""
    Platforms.get(id).delete_platform()
    return {"result": "success"}


@router.get("/platform/list", summary="列表---平台")
def get_platform_list(session: Session = Depends(get_scoped_session)):
    """获取平台列表"""
    models = session.query(Platforms.id, Platforms.name).all()
    return [{"id": model.id, "name": model.name} for model in models]


# endregion

# region 店铺
@router.post("/shop/add", summary="编辑/新增---店铺")
def add_shop(id: int = Body(default=..., description="平台ID"),
             platform_id: int | None = Body(default=None, description="平台ID"),
             shop_name: str | None = Body(default=None, description="店铺名称")):
    """编辑/新增---店铺信息"""
    model = Shop.edit_shop(id, platform_id, shop_name)
    return {"result": "success", "id": model.id}


@router.post("/shop/list", summary="列表---店铺")
def get_shop_list(platform_id: int | None = Query(default=None, description="平台ID")):
    return Shop.list_shop(platform_id)


@router.post("/shop/delete/{id}", summary="删除---店铺")
def delete_shop(id: int = Path(..., description="店铺ID")):
    """删除店铺信息"""
    Shop.get(id).delete_shop()
    return {"result": "success"}


# endregion

# region 商品分类
@router.post("/categories/list", summary="列表---商品分类")
def get_goods_categories():
    return GoodsCategory.get_recursive_categories()


@router.get("/category/{id}/list", summary="分类及其子分类---商品分类")
def get_current_categories(id: int = Path(default=..., description="分类ID")):
    """获取当前分类及其子分类"""
    return GoodsCategory.get(id).get_recursive_current_categories()


@router.post("/category/add", summary="编辑/新增---商品分类")
def add_goods_category(id: int = Body(default=..., description="分类ID"),
                       name: str = Body(default=..., description="分类名称"),
                       parent_id: int | None = Body(default=None, description="父分类ID")):
    """编辑/新增---商品分类"""
    model = GoodsCategory.edit_category(name, parent_id, id)
    return {"result": "success", "id": model.id}


@router.post("/category/delete/{id}", summary="删除---商品分类")
def delete_goods_category(id: int = Path(default=..., description="分类ID")):
    """删除商品分类"""
    GoodsCategory.get(id).delete_category()
    return {"result": "success"}


# endregion

# region 商品档案
@router.post("/profile/add", summary="编辑/新增---商品档案")
def add_goods_profile(id: int = Body(default=..., description="商品ID"),
                      goods_name: str = Body(default=..., description="商品名称"),
                      goods_code: str = Body(default=None, description="商品编码"),
                      barcode: str = Body(default=None, description="条形码"),
                      category_id: int = Body(default=None, description="商品分类ID"),
                      is_forced_commit: bool = Body(default=False, description="是否强制提交"),
                      session: Session = Depends(get_scoped_session)):
    """编辑/新增---商品档案信息"""
    if id is not None and id > 0 and not is_forced_commit:
        if GoodsProfiles.has_config_shop_goods_by_id(id):
            return {"result": "fail", "is_forced_commit": True, "message": "该商品已经配置到店铺商品，是否要强制修改"}
    model = GoodsProfiles.edit_goods_profile(id, goods_code.strip(), barcode, category_id, goods_name)
    return {"result": "success", "id": model.id}


@router.post("/profile/paged", summary="列表---商品档案")
def get_goods_profile_paged(page_index: int = Body(default=1, description="页码"),
                            pagesize: int = Body(default=10, description="每页数量"),
                            name: str | None = Body(default=None, description="商品名称"),
                            goods_code: str | None = Body(default=None, description="商品编码"),
                            barcode: str | None = Body(default=None, description="条形码"),
                            category_id: int | None = Body(default=None, description="商品分类ID"),
                            profile_code: str | None = Body(default=None, description="商品档案编码或者条形码"),
                            session: Session = Depends(get_scoped_session)):
    return GoodsProfiles.paged(page_index, pagesize, name=name, goods_code=goods_code, barcode=barcode, category_id=category_id,
                               profile_code=profile_code)


@router.post("/profile/delete/{id}", summary="删除---商品档案")
def delete_goods_profile(id: int = Path(default=..., description="商品ID"),
                         session: Session = Depends(get_scoped_session)):
    """删除商品信息"""
    if id is None or id <= 0:
        raise ValidationException("商品ID不能为空")
    GoodsProfiles.get(id).delete_goods_profile()
    return {"result": "success"}


@router.post("/profile/import", summary="导入---商品档案")
def import_goods_profile(file: UploadFile,
                         session: Session = Depends(get_scoped_session)):
    """导入商品档案信息"""
    folder_path = f'./src/upload_field/goods_profile/'
    file_ext = os.path.splitext(file.filename)[1]
    if file_ext.lower() not in ['.xlsx']:
        raise ValidationException("文件格式错误，必须为excel文件xlsx")
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, f"{uuid.uuid4().hex}_{file.filename}")

    with open(file_path, 'wb') as f:
        f.write(file.file.read())

    df = pd.read_excel(file_path)
    try:
        os.remove(file_path)
    finally:
        pass
    import_goods_profile_task(df, session)
    # background_tasks.add_task(import_goods_profile_task, df)
    return {"result": "success"}


@router.get('/download/profile_template', summary="下载---商品档案导入模板")
def download_profile_template():
    """下载商品档案导入模板"""
    file_path = f'./src/upload_field/template/商品档案导入模板.xlsx'
    if not os.path.exists(file_path):
        raise ValidationException("模板文件不存在")
    from starlette.responses import FileResponse
    return FileResponse(file_path, filename=os.path.basename(file_path), media_type='application/octet-stream')

# endregion

# region 商品

@router.post("/add", summary="编辑/新增---商品")
def add_goods(id: int = Body(default=None, description="商品ID"),
              shop_id: int = Body(default=None, description="店铺ID"),
              category_id: int = Body(default=None, description="商品分类ID"),
              sku: str = Body(default=None, description="商品SKU"),
              suite_flag: bool = Body(default=False, description="是否套装商品"),
              recommend_flag: bool = Body(default=False, description="是否推荐商品"),
              price: float | None | str = Body(default=0.0, description="商品价格"),
              on_sale_flag: bool = Body(default=True, description="是否上架"),
              sale_point: str = Body(default=None, description="商品卖点"),
              profile_tuple: list[tuple[int, int, int]] = Body(default=None, description="关联档案信息，元组形式，如[(profile_id, quantity, price)]"),
              session: Session = Depends(get_scoped_session)):
    """
    :param id: 商品ID\n
    :param shop_id: 所属店铺\n
    :param category_id: 所属类目\n
    :param sku: 商品sku\n
    :param suite_flag: 是否套装商品\n
    :param recommend_flag: 是否推荐商品\n
    :param price: 零售价\n
    :param on_sale_flag: 上下架标记\n
    :param sale_point: 商品卖点\n
    :param profile_tuple: 关联的商品档案列表[(商品档案id, 配置数量, 商品mapping表id)]
    """
    if price is None:
        price = 0.0
    if id is None or id <= 0:
        model = ShopGoods.add_goods(shop_id, category_id, sku.strip(), suite_flag, recommend_flag, price, on_sale_flag, sale_point, profile_tuple)
        return {"result": "success", "id": model.id}
    else:
        ShopGoods.get(id).update_goods(shop_id, category_id, sku.strip(), suite_flag, recommend_flag, price, on_sale_flag, sale_point, profile_tuple)
        return {"result": "success", "id": id}


@router.get("/detail/{id}", summary="详情---商品")
def get_goods_detail(id: int = Path(default=..., description="商品ID"),
                     session: Session = Depends(get_scoped_session)):
    """获取商品详情"""
    return ShopGoods.get(id).detail_info()


@router.post("/delete/{id}", summary="删除---商品")
def delete_goods(id: int = Path(default=..., description="商品ID"),
                 session: Session = Depends(get_scoped_session)):
    """删除商品"""
    if id is None:
        raise ValidationException("商品ID不能为空")
    ShopGoods.get(id).delete_shop_goods()
    return {"result": "success"}


@router.post("/paged", summary="列表---商品")
def get_goods_paged(page_index: int = Body(default=1, description="页码"),
                    pagesize: int = Body(default=10, description="每页数量"),
                    category_id: int | None = Body(default=None, description="商品分类ID"),
                    sku: str | None = Body(default=None, description="商品SKU"),
                    shop_id: int | None = Body(default=None, description="店铺ID"),
                    suite_flag: bool | None = Body(default=None, description="是否套装商品"),
                    recommend_flag: bool | None = Body(default=None, description="是否推荐商品"),
                    on_sale_flag: bool | None = Body(default=None, description="是否上架"),
                    is_empty_profile: bool | None = Body(default=None, description="是否无档案商品"),
                    goods_code: str | None = Body(default=None, description="商品编码")):
    """获取商品列表"""
    return ShopGoods.paged(page_index, pagesize, category_id=category_id, sku=sku, shop_id=shop_id,
                           suite_flag=suite_flag, recommend_flag=recommend_flag, on_sale_flag=on_sale_flag, is_empty_profile=is_empty_profile,
                           goods_code=goods_code)


@router.post("/import", summary="导入---商品")
def import_shop_goods(file: UploadFile,
                      shop_id: int = Body(default=..., description="店铺ID"),
                      session: Session = Depends(get_scoped_session)):
    """导入店铺商品信息"""
    folder_path = f'./src/upload_field/shop_goods/'
    os.makedirs(folder_path, exist_ok=True)
    file_ext = os.path.splitext(file.filename)[1]
    if file_ext.lower() not in ['.xlsx']:
        raise ValidationException("文件格式错误，必须为excel文件xlsx")

    file_path = os.path.join(folder_path, f"{uuid.uuid4().hex}_{file.filename}")

    # 保存上传文件
    with open(file_path, 'wb') as f:
        f.write(file.file.read())

    # 读取Excel文件
    df = pd.read_excel(file_path)
    try:
        os.remove(file_path)
    finally:
        pass
    import_goods_task(df, shop_id, session)
    # background_tasks.add_task(import_goods_task, df, shop_id)
    return {"result": "success"}


@router.get('/download/goods_template', summary="下载---商品导入模板")
def download_goods_template():
    """下载商品导入模板"""
    file_path = f'./src/upload_field/template/店铺商品导入模板.xlsx'
    if not os.path.exists(file_path):
        raise ValidationException("模板文件不存在")
    return FileResponse(file_path, filename=os.path.basename(file_path), media_type='application/octet-stream')

# endregion


# @router.get('/test',summary='测试接口', tags=['public'])
# def download_goods_sample(sku: str = Query(default=..., description="商品SKU")):
#     """测试接口"""
#     return ShopGoods.get_goods_name(sku)
