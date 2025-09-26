import datetime
import json
from decimal import Decimal
from enum import Enum
from typing import Mapping


def convert_to_dict(value):
    """将json字符串转换为字典, 如果转换失败则返回原值"""
    try:
        return json.loads(value)
    except:
        return value


def parse_nested_json(data):
    """转换嵌套的json字符串为字典"""
    if isinstance(data, dict):
        return {k: parse_nested_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [parse_nested_json(v) for v in data]
    elif isinstance(data, str):
        return convert_to_dict(data)
    else:
        return data


def _customer_serializer(obj):
    """自定义序列化"""
    if isinstance(obj, datetime.datetime):
        return datetime.datetime.strftime(obj, '%Y-%m-%d %H:%M:%S.%f')
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    return str(obj)


def object_to_json(obj, *, fallback=None):
    """将对象转换为json字符串"""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, datetime.datetime):
        return obj.isoformat(sep=" ", timespec="seconds")
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    if isinstance(obj, datetime.time):
        return obj.isoformat(timespec="seconds")
    if isinstance(obj, datetime.timedelta):
        return obj.total_seconds()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, Mapping):
        return {k: object_to_json(v, fallback=fallback) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set, frozenset)):
        return [object_to_json(item, fallback=fallback) for item in obj]
    if hasattr(obj, '__dict__'):
        return {k: object_to_json(v, fallback=fallback) for k, v in obj.__dict__.items() if not k.startswith('_')}
    if fallback is not None:
        return fallback(obj)
    if type(obj).__name__ == 'lock':
        return None
    raise Exception(f"无法序列化对象{obj}")
