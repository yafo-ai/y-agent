# 获取本地ip
import socket


def get_local_ip():
    ip = socket.gethostbyname(socket.gethostname())
    return ip


# 获取公网ip
def get_network_ip(request):
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]  # 取X-Forwarded-For中的第一个IP
    else:
        ip = request.client.host
    return ip


# pip install XdbSearchIP
from XdbSearchIP.xdbSearcher import XdbSearcher

searcher = XdbSearcher(dbfile='./src/db/ip_db/ip2region.xdb')


def get_ip_address(network_ip_address):
    try:
        region_str = searcher.search(network_ip_address)
        fields = region_str.split('|')
        return (fields[0] if fields[0] != '0' else 'N/A') + '，' + (fields[2] if fields[2] != '0' else 'N/A') + '，' + (
            fields[3] if fields[3] != '0' else 'N/A') + '，' + (fields[4] if fields[4] != '0' else 'N/A')
        # return {
        #     "IP": network_ip_address,
        #     "国家": fields[0] if fields[0] != '0' else 'N/A',
        #     "省份": fields[2] if fields[2] != '0' else 'N/A',
        #     "城市": fields[3] if fields[3] != '0' else 'N/A',
        #     "运营商": fields[4] if fields[4] != '0' else 'N/A'
        # }
    except Exception as e:
        print(e)
        from src.api.customer_exception import ValidationException
        return ValidationException(detail='获取ip地址失败')