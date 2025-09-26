from src.database.models import ShopGoods
import re
def replace_jd_order_sku(content):
    pattern = r"查询订单号：(\d+)，商品号：(\d+)(\?[^\s]+)?"
    matches = re.findall(pattern, content)
    for orderNo,jdSku,_ in matches:
        # order_info=get_jd_order_info(orderNo,jdSku)
        order_info=ShopGoods.get_goods_name(jdSku)
        if order_info:
            content = content.replace(f'查询订单号：{orderNo} ，商品号：{jdSku}', f"{order_info}")
    return content

def replace_jd_order_sku_2(content):
    pattern = r"咨询订单号：(\d+) 商品ID：(\d+)(\?[^\s]+)?"
    matches = re.findall(pattern, content)
    for orderNo,jdSku,_ in matches:
        # order_info=get_jd_order_info(orderNo,jdSku)
        order_info=ShopGoods.get_goods_name(jdSku)
        if order_info:
            content = content.replace(f'咨询订单号：{orderNo} 商品ID：{jdSku}', f"{order_info}")
    return content
    
def replace_jd_sku(content):
    pattern = r'https://item.jd.com/(\d+).html(\?[^\s]+)?'
    matches = re.findall(pattern, content)
    for jdSku, _ in matches:
        # sku_info=get_jd_product_name(jdSku)
        sku_info=ShopGoods.get_goods_name(jdSku)
        if sku_info:
            content = content.replace(f'https://item.jd.com/{jdSku}.html{_}', f"{sku_info}")
        else:
            raise Exception(f"商品编码[{jdSku}]缺少配置，我不清楚这个编码是什么商品")
    return content

def replace_jd_image(content):
    pattern = r'https://dd-static.jd.com/[^\s]+'
    return re.sub(pattern, '[图片]', content)

def replace_jd_face(content):
    ##E-s45   #E-s44
    pattern = r"#E-s\d{2}"
    return re.sub(pattern, '[表情]', content)

def replace_jd_coupon(content):
    pattern = r'https://coupon.m.jd.com/[^\s]+'
    return re.sub(pattern, '[优惠券]', content)

def replace_jd_mp4(content):
    pattern = r'https://vod.300hu.com/[^\s]+'
    return re.sub(pattern, '[视频]', content)

def replace_jd_content(content):
    content=replace_jd_order_sku(content)
    content=replace_jd_order_sku_2(content)
    content=replace_jd_sku(content)
    content=replace_jd_image(content)
    content=replace_jd_face(content)
    content=replace_jd_coupon(content)
    content=replace_jd_mp4(content)
    return content

if __name__ == "__main__":

    content="""
jd_dpincjpgphws 2024-02-29 23:50:12	
咨询订单号：290561156779 商品ID：10079200812663
智通仁和彬彬 2024-02-29 23:50:20	
有的亲	
jd_dpincjpgphws 2024-02-29 23:50:31	
发出来看一下吧	
智通仁和彬彬 2024-02-29 23:50:47	
https://item.jd.com/10079200812663.html
智通仁和彬彬 2024-02-29 23:50:51	
这些加一个双肩包	
jd_dpincjpgphws 2024-02-29 23:51:05	
🙄	
智通仁和彬彬 2024-02-29 23:51:15	
https://item.jd.com/10079200812663.html?sdx=ehi-lLxFuZiE6JnIZopejMYosTKXDggrsmxMt6tHZ5H7cJjQIp9e53Xto0HgUg
jd_dpincjpgphws 2024-02-29 23:51:43	
我看到说有8样赠品	
智通仁和彬彬 2024-02-29 23:51:56	
https://coupon.m.jd.com/coupons/show.action?key=2132e6e8074448a4aa51282aeba75e1b&roleId=141456073&to=ztrhbg.jd.com
智通仁和彬彬 2024-02-29 23:52:00	
白条免息等等服务	
智通仁和彬彬 2024-02-29 23:52:02	
不是实物	
jd_dpincjpgphws 2024-02-29 23:52:12	
https://dd-static.jd.com/ddimg/jfs/t1/226139/36/13264/108250/65e03a6cF910143d2/faffdb5831f4b5a0.jpg		
智通仁和彬彬 2024-02-29 23:52:27	
嗯嗯	
智通仁和彬彬 2024-02-29 23:52:33	
https://dd-static.jd.com/ddimg/jfs/t1/226139/36/13264/108250/65e03a6cF910143d2/faffdb5831f4b5a0.jpg	

"""

    print(replace_jd_content(content))
