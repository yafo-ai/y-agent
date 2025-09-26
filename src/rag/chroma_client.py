import json
import threading
import chromadb

from src.configs.system_config import SystemConfigVector


_cached_client = None
# 用于存储创建当前客户端时所依据的连接信息（host, port, ssl）
# 我们使用一个元组 (host, port, ssl) 作为“键”来进行比较
_cached_connection_key = None

# 创建一个模块级别的锁对象
_client_lock = threading.Lock()


def get_chroma_client(sys_vector:SystemConfigVector) -> chromadb.ClientAPI:
    """
    获取一个 ChromaDB 的 HttpClient 实例。

    该方法实现了客户端的缓存机制。只有当连接的 host 或 port 发生变化时，
    才会创建一个新的 HttpClient 实例。否则，将返回已缓存的实例。

    Args:
        sys_vector: 一个包含 connect_str 属性的对象。
                    connect_str 可以是一个字典或一个JSON格式的字符串。

    Returns:
        chromadb.HttpClient: 一个已配置好的 ChromaDB HTTP 客户端实例。
    """
    # 使用 global 关键字声明我们要修改模块级别的全局变量
    global _cached_client, _cached_connection_key

    connect_dict = sys_vector.connect_str if isinstance(sys_vector.connect_str, dict) else json.loads(sys_vector.connect_str)
    host = connect_dict.get("host", '')
    ssl = True if host.startswith("https") else False
    if host.startswith("https"):
        host = host[8:]
    if host.startswith("http"):
        host = host[7:]
    port = connect_dict.get("port", 8000)

    current_connection_key = (host, port, ssl)

    with _client_lock:
        if _cached_client is None or current_connection_key != _cached_connection_key:

            # 创建新的客户端实例
            _cached_client = chromadb.HttpClient(host=host, port=port, ssl=ssl)
            
            # 更新缓存“键”，以便下次进行比较
            _cached_connection_key = current_connection_key

    return _cached_client