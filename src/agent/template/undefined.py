from jinja2 import Environment, Template, Undefined, UndefinedError

from src.agent.working.working_graph import WorkingGraph

class TempUndefined(Undefined):
    """安全处理未定义变量，避免渲染报错"""
    # def __getattr__(self, _):
    #     # return TempUndefined()
    def __bool__(self):
        return False  # 未定义变量视为False
    
    def __len__(self):
        return 0  # 未定义变量长度视为0

def is_empty(value) -> bool:
    """判断变量是否为空"""
    if isinstance(value, TempUndefined) or value is None:
        return True
    if isinstance(value, (list, dict, str)):
        return len(value) == 0
    return False

def is_not_empty(value) -> bool:
    """判断变量是否已定义且非空"""
    return not is_empty(value)



if __name__ == "__main__":
    env = Environment(undefined=TempUndefined)  # 使用自定义的Undefined类
    env.tests["empty"] = is_empty      # 注册empty测试器
    env.tests["not_empty"] = is_not_empty
    j2_template = env.from_string("{% if 店铺政策客服.output is empty %}1{% else %}0{% endif %}")
    context = {}
    context["店铺政策客服"]={}
    
    rst=j2_template.render(context)
    print(rst)