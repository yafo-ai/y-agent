import traceback
import pandas as pd
from pandas import DataFrame


def get_excel_data_dict(df: DataFrame, attribute_field="attribute", title_field="标题", unique_code_field="唯一编码"):
    try:
        df[0] = df[0].ffill().mask(df[0].duplicated(keep='first') & df[0].notna(), '')
        df[1] = df[1].fillna('')

        attr_map = {}
        for idx, row in df.iterrows():
            primary = str(row[0]).strip()
            secondary = str(row[1]).strip()

            if secondary and primary:  # 存在二级属性
                attr_map[idx] = (primary, secondary)
            elif primary:  # 仅有一级属性
                attr_map[idx] = (primary, None)
        products = []
        for col in df.columns[2:]:
            product = {f"{attribute_field}": {}, f"{title_field}": "", f"{unique_code_field}": ""}
            current_level = product[f"{attribute_field}"]

            for idx in attr_map:
                primary, secondary = attr_map[idx]
                value = df.iat[idx, col]

                # 特殊字段处理
                if primary == title_field:
                    product[title_field] = str(value)
                elif primary == unique_code_field:
                    product[unique_code_field] = str(value)

                # 存在二级属性
                if secondary:
                    if primary not in current_level:
                        current_level[primary] = {}
                    current_level[primary][secondary] = str(value) if pd.notna(value) else ''
                # 直接一级属性
                else:
                    current_level[primary] = str(value) if pd.notna(value) else ''
            products.append(product)
        return products

    except Exception as e:
        traceback.print_exc()
        from src.utils.log_helper import logger
        logger.error("读取excel数据异常：" + str(e))
