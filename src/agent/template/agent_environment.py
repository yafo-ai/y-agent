from jinja2 import Environment, Undefined


class AgentEnvironment(Environment):
    """
    自定义jinja2环境
    """

    def __init__(self, *args, **kwargs):
        # `keep_trailing_newline`
        #  Preserve the trailing newline when rendering templates.
        #  The default is ``False``, which causes a single newline,
        #  if present, to be stripped from the end of the template.
        kwargs['keep_trailing_newline'] = True
        super().__init__(*args, **kwargs)

    def getattr(self, obj, attribute):
        try:
            # 处理列表的特殊属性
            if isinstance(obj, list):
                if attribute == 'first':
                    return lambda n: obj[:n] if obj else Undefined()
                    # return obj[0] if obj else Undefined()
                elif attribute == 'last':
                    return lambda n: obj[-n:] if obj else Undefined()
                    # return obj[-1] if obj else Undefined()
                elif all(isinstance(x, dict) for x in obj) and obj:
                    # 如果是字典列表且访问的属性是字典键
                    if attribute in obj[0]:
                        return [x.get(attribute) for x in obj]
                    elif attribute == 'field':
                        # 返回一个可调用对象来处理field方法
                        return lambda fields: [
                            {k: v for k, v in item.items() if k in fields}
                            for item in obj
                        ]
            # 默认行为
            return super().getattr(obj, attribute)
        except (KeyError, IndexError, AttributeError):
            return Undefined()


class TestPerson:
    def __init__(self, pname, page):
        self.pname = pname
        self.page = page


def test_customer_attribute_proxy():
    """
    测试方法
    """
    int_list = [1, 2, 3, 4, 5]
    str_list = ['a', 'b', 'c', 'd', 'e']
    dict_list = [{'name': 'John', 'age': '18', 'class': 'A'}, {'name': 'Mary', 'age': '19', 'class': 'B'}, {'name': 'Tom', 'age': '20', 'class': 'C'}]
    obj = TestPerson('p-John', 99)
    obj_list = [TestPerson('p-John-1', 999), TestPerson('p-Mary', 888), TestPerson('p-Tom', 777)]

    evn = AgentEnvironment()

    data = {
        'int_list': int_list, 'str_list': str_list, 'dict_list': dict_list, 'obj': obj, 'obj_list': obj_list,
        'sys': {
            'space': {
                'khs': ['111111111111111111']
            }
        }
    }

    template = """
    {{ int_list.first(2) }}
    {{ int_list.last(3) }}
    {{ str_list.first(2) }}
    {{ str_list.last(3) }}
    {{ dict_list.name }}
    dict_list.field(['name', 'class']): {{ dict_list.field(['age', 'name', 'class', 'a']) }}
    {{ dict_list}}
    {{ obj.pname }}
    {{ obj.page }}
    {{ obj_list[0].pname }}
    {{ obj_list[0].page }}
    {{ sys.space.khs }}
    """
    template = """
  
    {{ sys.space.khs }}
    \n\n
    {{ sys.space.khs }}\n\n"""

    result = evn.from_string(template).render(**data)
    print(result)


if __name__ == '__main__':
    test_customer_attribute_proxy()
