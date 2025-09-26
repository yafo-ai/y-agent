
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from src.agent.template.undefined import TempUndefined, is_empty, is_not_empty
from src.agent.working.working_graph import WorkingGraph
from src.agent.model_types import NextNode, NodeRunResult, NodeType
import threading
from src.database.db_session import  on_request_end,set_current_request_id
from jinja2 import UndefinedError
from src.agent.template.agent_environment import AgentEnvironment


class BaseNode(ABC):

    _node_type: NodeType

    def __init__(self,role_id:str, role:str,description:str,next_nodes:list[NextNode]):
        self.role_id=role_id
        self.role = role
        self.description = description
        self.run_times=0
        self.virtual_run_times=0
        self.next_nodes=next_nodes
        self.next_run_constraint=defaultdict(dict) #下游运行次数约束
        for node in next_nodes:
            self.next_run_constraint[node.role]={"max_run_times":node.max_run_times,"run_times":0}
        self.lock = threading.Lock()
        self.is_running = False

        #以下两个属性用于循环节点，id和循环数据注入
        self.parent_loop_node_id=None
        self.loop_context=None

        #运行时错误信息
        self.runned_error=None

    def _set_loop_sub_node(self,parent_loop_node_id:str,loop_context:dict):
        """设置循环节点数据"""
        self.parent_loop_node_id=parent_loop_node_id
        self.loop_context=loop_context

    def add_next_node(self,node:'BaseNode',max_run_times:int):
        """添加下游节点"""
        self.next_run_constraint[node.role]={"max_run_times":max_run_times,"run_times":0}

    def get_next_run_times(self,role:str):
        """获取下游节点运行次数"""
        if role in self.next_run_constraint:
            return self.next_run_constraint[role]["run_times"]
        else:
            raise ValueError(f"没有初始化{role}的运行次数限制")
        
    def get_next_run_max_times(self,role:str):
        """获取下游节点运行次数限制"""
        if role in self.next_run_constraint:
            return self.next_run_constraint[role]["max_run_times"]
        else:
            raise ValueError(f"没有初始化{role}的运行次数限制")
            
    def _record_next_run_times(self,role:str):
        """记录下游运行次数限制"""
        with self.lock:
            if role in self.next_run_constraint:
                self.next_run_constraint[role]["run_times"]+=1
            else:
                raise ValueError(f"没有初始化{role}的运行次数限制")

    def _run_verify(self,trigger:'BaseNode',graph:WorkingGraph):
        """执行前验证"""
        if graph.working_space.is_terminate:
            #工作空间已经终止
            return False

        if trigger.role==self.role:
            return True
        
        #触发者和执行者不在一个强连通分量中
        if not graph.is_connected(trigger,self):

            if self.run_times+self.virtual_run_times>=trigger.run_times+trigger.virtual_run_times:
                #当前节点已经执行过,新增验证逻辑，防止A——>C   B——>C   AB同时执行完触发C，导致C执行两次
                return False
        
            up_nodes=graph.get_upstream_nodes(self)
            for up_node in up_nodes:
                #执行者和上游依赖在一个强连通分量中
                if graph.is_connected(up_node,self):
                    continue
                #判断依赖：上游依赖执行次数不应该小于触发者的执行次数
                if up_node.run_times+up_node.virtual_run_times<trigger.run_times+trigger.virtual_run_times:
                    return False
        #触发者和执行者是同一个环
        else:
            if self.run_times+self.virtual_run_times>trigger.run_times+trigger.virtual_run_times:
                #当前节点已经执行过,新增验证逻辑，防止A——>C   B——>C   AB同时执行完触发C，导致C执行两次
                return False
            
            up_nodes=graph.get_upstream_nodes(self)
            for up_node in up_nodes:
                #执行者和上游依赖在一个强连通分量中
                if graph.is_connected(up_node,self):
                    #判断依赖：上游依赖执行次数不应该小于触发者的执行次数
                    if up_node.run_times+up_node.virtual_run_times<trigger.run_times+trigger.virtual_run_times:
                        return False
                
        return True
    
    @abstractmethod
    def _run(self,trigger:'BaseNode',graph:WorkingGraph)->NodeRunResult:
        """执行 do something"""

        raise NotImplementedError

    def run(self,trigger:'BaseNode',graph:WorkingGraph):
        """执行"""
        if self._node_type!=NodeType.START and self._node_type!=NodeType.LOOP_START:
            set_current_request_id()
        self.is_running=True
        target_roles=[]
        try:
            
            with self.lock:
                if not self._run_verify(trigger,graph):
                    self.is_running=False
                    return
                print(f"----------------------{trigger.role} 触发了 {self.role} , 第 {self.run_times+1} 次执行,当前线程：{threading.current_thread().ident} ---------------------------\n")
                start_time =  datetime.now()
                result=self._run(trigger,graph)
                if result.target_roles:
                    target_roles=result.target_roles
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                self.run_times+=1
                
                model_name=self.llm_name if hasattr(self, 'llm_name') else None 

                graph.working_space.add_log(triggerer=trigger.role,
                                            runner_type=self._node_type,
                                            runner=self.role,
                                            runner_id=self.role_id,
                                            parent_loop_node_id=self.parent_loop_node_id,
                                            runner_run_times=self.run_times,
                                            start_time=start_time,
                                            end_time=end_time,
                                            duration=duration,
                                            model_name=model_name,
                                            prompt_temp=result.prompt_temp,
                                            prompt_str=result.prompt_str,
                                            vision_file_str=result.vision_file_str,
                                            response=result.response,
                                            function_calls=result.function_calls,
                                            section_results=result.section_results)
                
                if self.runned_error is not None:
                    raise Exception(self.runned_error)
            
            
            self._trigger_down_nodes(target_roles,graph)
        except Exception as e: 
            raise e 
        finally:
            #特殊管理多线程session
            self.is_running=False
            if self._node_type!=NodeType.START and self._node_type!=NodeType.LOOP_START:
                on_request_end()
       
    def set_termination(self,graph:WorkingGraph):
        """终止流程"""
        graph.working_space.is_terminate=True

    def _run_virtual(self,trigger:'BaseNode',graph:WorkingGraph):
        """跳过执行，目的是解决依赖计算为问题"""
        with self.lock:
            if trigger.run_times+trigger.virtual_run_times>self.run_times+self.virtual_run_times:
                #虚拟执行增加验证逻辑，防止A——>C   B——>C   AB执行完触发C，导致C执行两次
                if self._run_verify(trigger,graph):
                    self.virtual_run_times+=1
                    print(f"{trigger.role} 触发了 {self.role} , 第 {self.virtual_run_times} 次【虚拟】执行,当前线程：{threading.current_thread().ident} \n")

    def _trigger_down_nodes(self,target_roles:list[str],graph:WorkingGraph):
        """
        触发下游节点
        target_roles : 需要执行的下游目标节点，没有目标时，下游均执行。有目标时，目标执行，其他虚拟执行
        """
        downnodes=graph.get_downstream_nodes(self)

        target_nodes=[]
        jump_nodes=[]
        if len(target_roles)>0:
            for node in downnodes:
                if node.role in target_roles:
                    target_nodes.append(node)
                else:
                    jump_nodes.append(node)
            if len(target_nodes)!=len(target_roles):
                raise ValueError(f"{self.role}-目标错误，请检查，{target_roles}中存在不存在的节点")
        else:
            target_nodes=downnodes
        
        #处理执行次数
        remaining_nodes = []
        for target_node in target_nodes:
            if self.get_next_run_max_times(target_node.role)>self.get_next_run_times(target_node.role):
                self._record_next_run_times(target_node.role)
                remaining_nodes.append(target_node)
            else:
                jump_nodes.append(target_node)
                
        target_nodes[:] = remaining_nodes

        if len(jump_nodes)>0:
            stop_nodes=[node for node in target_nodes]
            stop_nodes.append(self)
            junmp_trees=graph.dfs_subtree(nodes=jump_nodes,stop_nodes=stop_nodes)
            for junmp_node in junmp_trees:
                junmp_node._run_virtual(self,graph)

        from concurrent.futures import ThreadPoolExecutor,as_completed
        with ThreadPoolExecutor(max_workers=16) as executor:
            futures = {executor.submit(node.run,self,graph) for node in target_nodes}
            # 异常处理
            for future in as_completed(futures):
                try:
                    future.result()  # 获取结果，如果任务抛出异常，这里会抛出
                except Exception as e:
                    raise e

    def _replace_prompt(self, temp: str, graph: WorkingGraph):
        """处理prompt,替换模板"""
        try:
            env = AgentEnvironment(undefined=TempUndefined)  # 使用自定义的Undefined类
            env.tests["empty"] = is_empty  # 注册empty测试器
            env.tests["not_empty"] = is_not_empty
            j2_template = env.from_string(temp)
            context = {"sys": {}}
            context["sys"]["time"] = graph.working_space.system_time
            context["sys"]["date"] = graph.working_space.system_data
            context["sys"]["datetime"] = graph.working_space.system_datetime
            context["sys"]["contains"]=graph.working_space.custome_contains
            context['sys']["space"] = {}
            variables_snapshot = graph.working_space.variables.copy()
            for key, value in variables_snapshot.items():
                context['sys']["space"][key] = value["content"]
            context["sys"]["get_documents_text"] = graph.working_space.get_document
            context["sys"]["get_documents_json"] = graph.working_space.get_document_list

            context["sys"]['chat_room'] = {}
            context["sys"]['chat_room']['get_talks'] = graph.working_space.get_talks_to_dict
            context["sys"]["current_token"] = graph.working_space.config.get("current_token")
            context["sys"]["is_null_or_empty"]=graph.working_space.is_null_or_empty

            context["role"] = {}
            context['role']["开始"] = graph.working_space.inputs
            context['role']["input"] = graph.working_space.inputs
            context["role"]["get_roles_outputs"] = graph.working_space.get_roles_output
            context["role"]["exist"] = graph.working_space.exist_role

            role_output_snapshot = graph.working_space.role_output.copy()
            for key, value in role_output_snapshot.items():
                context["role"][key] = value
                # 检查循环节点
                if self.parent_loop_node_id is not None:
                    # 还原循环变量中的节点变量名称。在循环内部，去掉后缀表示当前一次循环的节点
                    suffix = f"_batch_{self.loop_context.get('index')}"
                    if key.endswith(suffix):
                        context["role"][key.replace(suffix, "")] = value
            if self.parent_loop_node_id is not None:
                context["loop"] = self.loop_context #已过期
                context["batch"] = self.loop_context
            return j2_template.render(**context)

        except UndefinedError as e:
            raise ValueError(f"{self.role}-Prompt模板渲染失败,变量未定义：{e}")
        except Exception as e:
            raise ValueError(f"{self.role}-Prompt模板渲染失败，未知错误：{e}")

    def run_debug(self, trigger: 'BaseNode', graph: WorkingGraph):
        """
        运行调试
        :param trigger:
        :param graph:
        :return:
        """
        return self._run(trigger, graph)


