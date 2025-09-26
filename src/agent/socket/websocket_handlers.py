import asyncio
import json
from fastapi import WebSocket
from src.agent.socket.websocket_manager import WebSocketManager
from src.agent.working.working_manager import load_graph,run_graph
from src.agent.working.working_callback import WorkingLoggingCallback
from src.database.models import WorkFlow, WorkFlowRunLogScore
from src.plugins.jd_utils import replace_jd_content
from src.agent.pub_sub_queue import PubSubQueue, Topics
from src.database.db_session import set_current_request_id,session_scope,on_request_end
from src.database.enums import LogOrigin

pubsub = PubSubQueue()
subscriber_queue = pubsub.subscribe(Topics.human_message_topic)
socket_manager = WebSocketManager(subscriber_queue=subscriber_queue)


@socket_manager.handler("feedback_score")
# 定义一个异步函数，用于处理反馈评分
async def feedback_score_handler(websocket: WebSocket, pin_id: str, json_data: dict, **kwargs):
    # 从json数据中获取问题id、评分、修改答案、角色和id
    question_id = json_data.get("question_id")
    score = json_data.get("score")
    amend_answer = json_data.get("amend_answer")
    role= json_data.get("role")
    id=json_data.get("id")
    # 定义一个线程运行函数
    def thread_run():
        # 设置当前请求id
        set_current_request_id()
        try:
            # 调用反馈结果函数
            WorkFlowRunLogScore.feedback_result(question_id, score, amend_answer,role,id)
        except Exception as e:
            # 抛出异常
            raise ValueError(str(e))
        finally:
            # 请求结束
            on_request_end()
    # await sync_to_async(func=thread_run)()
    # 使用asyncio.to_thread运行线程
    await asyncio.to_thread(thread_run)



@socket_manager.handler("run_workflow")
async def run_workflow_handler(websocket: WebSocket,pin_id: str,json_data:dict,**kwargs):
    """
    通用执行流程接口
    input:参数为对应流程的输入参数
    {"input":{"user_input":"xxx"}}
    """
    workflow_id=json_data.get("workflow_id")
    user_id=json_data.get("user_id")
    input_dict=json_data.get("input")
    origin=json_data.get("origin") # 来源
    api_key=json_data.get("api_key") #分享的api_key
    loop = asyncio.get_event_loop()
    def thread_run():
        set_current_request_id()
        try:
            
            workflow_model = WorkFlow.get(workflow_id)

            workflow_model.validate_api_key(api_key)
            source_info = workflow_model.get_source_info_by_key(api_key)
            workflow_source_id=source_info.get("id")
            workflow_source_name=source_info.get("name")    
            
            if LogOrigin.value_of(origin)==LogOrigin.京东咚咚:

                for key, val in input_dict.items():
                    if not isinstance(val, str):
                        continue
                    input_dict[key] = replace_jd_content(val)

            graph = load_graph(workflow_id=workflow_id,
                            json_data=workflow_model.data_json,
                            user_id=user_id,
                            pin_id=pin_id,
                            workflow_source_id=workflow_source_id,
                            workflow_source_name=workflow_source_name
                            )
            
            result=run_graph(workflow_id=workflow_id,
                    workflow_name=workflow_model.name,
                    graph=graph,
                    input_dict=input_dict,
                    callbacks=[WorkingLoggingCallback(queue=pubsub)],
                    use_log=workflow_model.use_log
                    )
            
            #执行完毕
            citations=json.dumps(result["citations"], ensure_ascii=False, default=lambda o: o.__dict__)
            citations_disc=json.loads(citations) if citations else None
            data={"workflow_id":workflow_id,"question_id":result["question_id"],"user_id":user_id,"pin_id":pin_id,"elapsed_time":result["elapsed_time"],"answer_num":len(result["output"]),"citations":citations_disc}
            # asyncio.run(socket_manager.send_ai_finish(data,pin_id))
            asyncio.run_coroutine_threadsafe(socket_manager.send_ai_finish(data,pin_id), loop)
            
        except Exception as e:
            # asyncio.run(socket_manager.send_error(message=str(e), pin_id=pin_id))
            # asyncio.run(socket_manager.send_ai_finish({"workflow_id":workflow_id,"question_id":"","user_id":user_id,"pin_id":pin_id,"elapsed_time":'0',"answer_num":0,"citations":[]},pin_id))
            asyncio.run_coroutine_threadsafe(socket_manager.send_ai_finish({"workflow_id":workflow_id,"question_id":"","user_id":user_id,"pin_id":pin_id,"elapsed_time":'0',"answer_num":0,"citations":[]},pin_id), loop)
            print("run_workflow_handler 错误"+str(e))
            raise ValueError(str(e))
        
        finally:
            on_request_end()
    
    await asyncio.to_thread(thread_run)
    # await sync_to_async(func=thread_run)()