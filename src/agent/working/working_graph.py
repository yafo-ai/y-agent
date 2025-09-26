from typing import Any, Sequence
from src.agent.model_types import NodeType
from src.agent.working.working_callback import WorkingCallback
from src.agent.working.working_space import WorkingSpace

class WorkingGraph:

    def __init__(self, vertices:list['BaseNode']=[],working_space:WorkingSpace=None):
        
        # 初始化图
        self.V = vertices
        self.graph = {i: [] for i in vertices}  # 使用字典存储图的邻接表表示
        self.working_space = working_space
        self.finished=False

    def add_node(self, v):
        # 添加一个新顶点
        if v not in self.V:
            self.V.append(v)
            self.graph[v] = []

    def add_edge(self, u, v):
        # 添加边到图
        self.graph[u].append(v)

    def init_space(self, space:WorkingSpace):
        self.working_space = space
        
    def build_edgs_with_node(self):
        # 根据节点约束关系构建边
        for node in self.V:
            for next_role, _ in node.next_run_constraint.items():
                for next in self.V:
                    if next.role == next_role:
                        self.add_edge(node, next)

    def fill_order(self, v, visited, stack):
        # 递归函数，填充顶点的排序
        visited[v] = True
        for i in self.graph[v]:
            if not visited[i]:
                self.fill_order(i, visited, stack)
        stack = stack.append(v)

    def get_transpose(self):
        # 获取图的转置
        g = WorkingGraph(self.V)
        for i in self.graph:
            for j in self.graph[i]:
                g.add_edge(j, i)
        return g

    def dfs_util(self, v, visited, component):
        # DFS遍历，用于添加顶点到同一个强连通分量
        visited[v] = True
        for i in self.graph[v]:
            if not visited[i]:
                self.dfs_util(i, visited, component)
        component.append(v)

    def get_scc(self):
        # 获取强连通分量
        stack = []
        visited = {v: False for v in self.V}  # 初始化所有顶点为未访问

        # 填充顶点的排序
        for i in self.V:
            if not visited[i]:
                self.fill_order(i, visited, stack)

        # 获取转置图
        gr = self.get_transpose()

        # 初始化所有顶点为未访问，用于第二次DFS遍历
        visited = {v: False for v in self.V}

        # 开始找到强连通分量
        scc_list = []
        while stack:
            i = stack.pop()
            if not visited[i]:
                component = []
                gr.dfs_util(i, visited, component)
                scc_list.append(component)

        return scc_list
    
    
    def is_connected(self, u, v):
        # 判断两个顶点是否在同一个强连通分量中
        scc_list = self.get_scc()
        for component in scc_list:
            if u in component and v in component:
                return True
        return False
    
    def get_downstream_nodes(self, vertex):
        if vertex in self.graph:
            return self.graph[vertex]
        else:
            return []
    
    def get_upstream_nodes(self, vertex):
        upstream_nodes = []
        for v, edges in self.graph.items():
            if vertex in edges:
                upstream_nodes.append(v)
        return upstream_nodes
    
    def dfs_subtree(self, nodes, stop_nodes=None, visited=None, return_list=None):
        # 初始化访问集合和返回列表
        if visited is None:
            visited = set()
        if return_list is None:
            return_list = []

        # 创建一个队列来处理多个起始节点
        queue = nodes[:]

        while queue:
            v = queue.pop(0)  # 取出队列中的第一个节点
            # 如果遇到停止节点，则跳过
            if stop_nodes and v in stop_nodes:
                continue
            # 如果节点未被访问，则进行DFS遍历
            if v not in visited:
                visited.add(v)
                return_list.append(v)
                for neighbour in self.graph[v]:
                    if neighbour not in visited:
                        queue.append(neighbour)

        return return_list


    def run(self,user_input:dict[str,Any]={},memory="",callbacks:list[WorkingCallback]=None):
        
        self.working_space.inputs=user_input
        self.working_space.memory=memory
        self.working_space.callbacks=callbacks
        for node in self.V:
            if node._node_type==NodeType.START:
                node.run(node,self)
                break;
        self.finished=True
    
    def run_sub_loop(self,loop_node_id,loop_context):
        """执行流程中的子循环，因工作空间是共享的，在工作空间内存储角色变量会有冲突，角色名称不可以相同"""
        start=None
        for node in self.V:
            node._set_loop_sub_node(loop_node_id,loop_context)
            if node._node_type==NodeType.LOOP_START:
                start=node
        if start is None:
            raise Exception("No loop start node found")
        start.run(start,self)
    
    def is_end(self):
        return self.finished

    def run_debug(self, node: 'BaseNode'):
        return node.run_debug(node, self)


# 使用示例
if __name__ == "__main__":
    
    
    vertices = ["1", "2", "3", "4"]
    g = WorkingGraph(vertices)
    g.add_edge("1", "2")
    g.add_edge("2", "3")
    g.add_edge("2", "4")
    g.add_edge("3", "2")
    g.add_edge("3", "4")

    print(g.get_scc())
    print(g.dfs_subtree(["3"],["4","2"]))

    # vertices = ["A", "B", "C", "D", "E"]
    # g = AgentGraph(vertices)
    # g.add_edge("A", "B")
    # g.add_edge("A", "C")
    # g.add_edge("A", "D")
    # g.add_edge("B", "E")
    # g.add_edge("C", "E")
    # g.add_edge("D", "E")
    # g.add_edge("E", "A")

    # print(g.get_scc())
    # print(g.dfs_subtree(["C"],["B","D"]))

    # vertices = ["角色1", "角色2", "角色3", "角色4", "角色5","角色6", "角色7", "角色8","角色9"]
    # g = AgentGraph(vertices)
    # g.add_edge("角色1", "角色1")
    # g.add_edge("角色1", "角色2")
    # g.add_edge("角色2", "角色3")
    # g.add_edge("角色2", "角色4")
    # g.add_edge("角色3", "角色5")
    # g.add_edge("角色3", "角色6")
    # g.add_edge("角色4", "角色7")
    # g.add_edge("角色4", "角色8")
    # g.add_edge("角色6", "角色9")
    # g.add_edge("角色8", "角色9")
    # g.add_edge("角色8", "角色2")
    # g.add_edge("角色8", "角色4")


    # print(g.dfs_subtree(["角色4"],"角色3"))

    # # 获取强连通分量
    # print("强连通分量分组排序",g.get_scc())


    # print("角色2的上游",g.get_upstream_nodes("角色2"))

    # print("角色9的上游",g.get_upstream_nodes("角色9"))


    # print("角色2，角色8，是不是在一个环里：",g.are_connected("角色2", "角色8"))


    # 角色1 执行完毕，执行角色2，不验证 角色8 ，因为2和8 是一个分组。

    # 角色8 执行完毕，执行角色2，不验证 角色1，因为2和8 是一个分组

    # 角色6，8 执行完毕，执行9 ，相互验证，因为不属于一个分组   