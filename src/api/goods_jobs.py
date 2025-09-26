import re
import traceback
import pandas as pd
from sqlalchemy import update

from src.api.customer_exception import ValidationException
from src.database.models import GoodsCategory, GoodsProfiles, ShopGoods, ShopGoodsProfileMapping
from src.utils.log_helper import logger


# 商品档案导入任务
def import_goods_profile_task(df: pd.DataFrame, session):
    # session = GoodsProfiles().session
    try:
        # 判断除了标题以外是否有数据
        if df.empty:
            raise ValidationException("文件为空，没有数据")

        required_columns = {'商品编码', '商品条码', '商品名称'}

        # 判断excel是否存在指定的列名
        if not required_columns.issubset(df.columns):
            raise ValidationException("商品档案文件格式错误，必须包含'商品编码', '商品条码', '商品名称'列")

        # 商品编码，商品条码  重复验证
        for column in ['商品编码', '商品条码']:
            duplicated_values = df[df[column].duplicated(keep=False)][column].unique()
            # 去除空值
            duplicated_values = duplicated_values[duplicated_values.astype(str) != 'nan']

            if duplicated_values.size > 0:
                raise ValidationException(f"{column}重复：{', '.join(duplicated_values.astype(str))}")

        # 导入商品档案信息
        for row in df.to_dict('records'):
            goods_code = str(row.get('商品编码')) if row.get('商品编码', None) is not None and pd.notna(row.get('商品编码')) else None
            barcode = str(row.get('商品条码')) if row.get('商品条码', None) is not None and pd.notna(row.get('商品条码')) else None
            goods_name = str(row.get('商品名称')) if row.get('商品名称', None) is not None and pd.notna(row.get('商品名称')) else None
            category_name = str(row.get('类目')) if row.get('类目', None) is not None and pd.notna(row.get('类目')) else None
            if goods_code is None and barcode is None:
                continue
            if goods_code.strip() == '' and barcode.strip() == '':
                continue
            current_category = None
            current_category_id = None
            if category_name is not None:
                current_category = GoodsCategory.get_category_by_name(category_name)
            if current_category is not None:
                current_category_id = current_category.id

            current_profile = GoodsProfiles.get_profile_by_code_or_barcode(goods_code, barcode)
            if current_profile is None:
                session.add(GoodsProfiles(goods_code=goods_code, barcode=barcode, name=goods_name, goods_category_id=current_category_id))
            else:
                current_profile.name = goods_name
                current_profile.goods_category_id = current_category_id
            session.commit()
    except ValidationException as e:
        raise ValidationException(f"导入店铺商品信息失败，{e.args[0]}")
    except Exception as e:
        session.rollback()
        traceback.print_exc()
        logger.error(f"导入商品档案信息异常，{e}")
        raise ValidationException(f"导入商品档案信息异常，{e.args[0]}")


# 商品导入任务
def import_goods_task(df: pd.DataFrame, shop_id, session):
    # session = ShopGoods().session
    error_msg_list = []
    try:
        # 检查文件是否为空
        if df.empty:
            raise ValidationException("文件为空，没有数据")

        # 检查是否包含必需列
        required_columns = {'商品SKU', '商品编码'}
        if not required_columns.issubset(df.columns):
            raise ValidationException("店铺商品文件格式错误，必须包含'商品编码', '商品SKU' 列")

        # 获取所有的商品编码列的数据，提取出来重复的商品编码
        duplicated_values = df[df['商品SKU'].duplicated(keep=False)]['商品SKU'].unique()
        duplicated_values = duplicated_values[duplicated_values.astype(str) != 'nan']
        if duplicated_values.size > 0:
            raise ValidationException(f"商品SKU重复：{', '.join(duplicated_values.astype(str))}")

        # 去重获取商品分类,过滤掉nan
        category_names = df['类目'].dropna().unique().tolist() if '类目' in df.columns else None

        category_list = GoodsCategory.get_category_by_names(category_names)

        category_dict = {c.name: c.id for c in category_list} if category_list is not None else {}

        index = 1
        # 导入商品信息
        for row in df.to_dict('records'):
            index = index + 1
            sku = str(row.get('商品SKU')) if row.get('商品SKU', None) is not None and pd.notna(row.get('商品SKU')) else None
            if sku is None:
                error_msg_list.append(f"第{index}行商品SKU不能为空")
                continue
            # 商品编码
            goods_code = str(row.get('商品编码')) if row.get('商品编码', None) is not None and pd.notna(row.get('商品编码')) else None
            if goods_code is None:
                error_msg_list.append(f"第{index}行商品SKU【SKU：{sku}】对应的【商品编码】不能为空")
                continue

            current_goods_codes = re.split(r'[，,]', goods_code)

            category_name = str(row.get('类目')) if row.get('类目', None) is not None and pd.notna(row.get('类目')) else None
            price = float(row['价格']) if row.get('价格', None) is not None and pd.notna(row.get('价格')) else 0.0

            suite_flag = False if len(current_goods_codes) == 1 else True
            recommend_flag = row.get('是否推荐') == '是' if '是否推荐' in row and pd.notna(row.get('是否推荐')) else False
            sale_point = str(row['卖点']) if '卖点' in row and pd.notna(row['卖点']) else None

            # 类目
            category_id = category_dict.get(category_name, None) if category_name is not None else None

            # 商品数量, 数量为空则默认为1
            quantity_list = []
            quantity_str = str(row.get('商品数量', '1')).replace('.0', '')
            if quantity_str is not None:
                tmp_quantity_list = re.split(r'[，,]', quantity_str)
                if len(tmp_quantity_list) != len(current_goods_codes):
                    # tmp_quantity_list不足的长度，用1补齐
                    for i in range(len(current_goods_codes) - len(tmp_quantity_list)):
                        tmp_quantity_list.append(1)
                quantity_list = [int(str(q)) if isinstance(q, (int, str)) and str(q).isdigit() else 1 for q in tmp_quantity_list]
            else:
                for i in range(len(current_goods_codes)):
                    quantity_list.append(1)

            goods = ShopGoods.query.filter_by(sku=sku.strip()).first()
            if goods is None:
                goods = ShopGoods(sku=sku.strip())
            elif goods.shop_id != shop_id:
                error_msg_list.append(f"第{index}行商品【SKU：{sku}】，在店铺【名称:{goods.shop.name if goods.shop is not None else '未知'}】已经存在")
                continue
            goods.goods_category_id = category_id
            goods.price = price
            goods.suite_flag = suite_flag if suite_flag is not None else False
            goods.recommend_flag = recommend_flag if recommend_flag is not None else False
            goods.on_sale_flag = False
            goods.sale_point = sale_point
            goods.shop_id = shop_id
            session.add(goods)
            session.flush()

            # 获取现有档案映射关系
            mapping = ShopGoodsProfileMapping.query.filter_by(shop_goods_id=goods.id)
            profiles = GoodsProfiles.get_profile_by_goods_codes(current_goods_codes)

            # 要删除的档案映射关系
            delete_mapping = [m for m in mapping if m.goods_profile_id not in [p.id for p in profiles]]

            for delete_mapping_item in delete_mapping:
                session.delete(delete_mapping_item)

            # 要新增的档案映射关系
            add_profile_ids = [p.id for p in profiles if p.id not in [m.goods_profile_id for m in mapping]]

            # 要修改的档案映射关系
            modify_profile_ids = [m.goods_profile_id for m in mapping if m.goods_profile_id in [p.id for p in profiles]]

            goods_error = []
            try:
                for i in range(len(current_goods_codes)):
                    tmp_current_profile = [p for p in profiles if p.goods_code == current_goods_codes[i]]
                    current_profile = tmp_current_profile[0] if len(tmp_current_profile) > 0 else None
                    if current_profile is None:
                        goods_error.append(f"第{index}行商品SKU【SKU：{sku}】对应的【商品编码：{current_goods_codes[i]}】对应的商品档案不存在" + '\r\n')
                        error_msg_list.append(f"第{index}行商品SKU【SKU：{sku}】对应的【商品编码：{current_goods_codes[i]}】对应的商品档案不存在")
                        continue
                    if current_profile.id not in add_profile_ids and current_profile.id not in modify_profile_ids:
                        continue
                    if current_profile.id in add_profile_ids:
                        tmp_add_mapping = ShopGoodsProfileMapping(shop_goods_id=goods.id, goods_profile_id=current_profile.id)
                        tmp_add_mapping.quantity = quantity_list[i] if quantity_list[i] is not None and quantity_list[i] > 0 else 1
                        session.add(tmp_add_mapping)
                        continue
                    if current_profile.id in modify_profile_ids:
                        tmp_modify_mapping = [m for m in mapping if m.goods_profile_id == current_profile.id][0]
                        tmp_modify_mapping.quantity = quantity_list[i] if quantity_list[i] is not None and quantity_list[i] > 0 else 1
            except Exception as e:
                goods_error.append(e.args[0])
            if len(current_goods_codes) == 1:
                if quantity_list[0] > 1:
                    goods.suite_flag = True
            # 避免触发orm的更新时间，导致出现数据库更新时间
            if len(goods_error) > 0:
                session.execute(
                    update(ShopGoods)
                    .where(ShopGoods.id == goods.id)
                    .values(note=','.join(goods_error))
                )
            else:
                session.execute(
                    update(ShopGoods)
                    .where(ShopGoods.id == goods.id)
                    .values(note=None)
                )
            session.commit()
    except ValidationException as e:
        error_msg_list.append(f"导入店铺商品信息失败，{e.args[0]}")
    except Exception as e:
        session.rollback()
        traceback.print_exc()
        error_msg_list.append(f"导入店铺商品信息异常，{e}")
        logger.error(f"导入店铺商品信息异常，{e}")
    finally:
        if len(error_msg_list) > 0:
            logger.error(f"导入店铺商品信息失败，{'; '.join(error_msg_list)}")
            raise ValidationException(f"导入店铺商品信息失败，{'; '.join(error_msg_list)}")
