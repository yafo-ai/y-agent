import threading
from typing import Any
from fastapi import APIRouter, Body, Path
from src.agent.working.working_manager import load_graph, run_graph
from src.agent.working.working_callback import XbotWorkingLoggingCallback
from src.database.db_session import on_request_end, set_current_request_id
from src.database.enums import LogOrigin
from src.database.models import WorkFlow, WxBotMessage
from src.plugins.jd_utils import replace_jd_content
from src.plugins.xbot_utils import xbot_client_user_id
from src.utils.log_helper import logger

router = APIRouter(
    prefix="/api/wxbot",
    tags=["微信机器人"],
)

def process_ai_logic(workflow_id: int, data: Any):
    try:
        set_current_request_id()
        type=data.get("type")
        client_id=data.get("client_id")
        if type=="WW_RECV_TEXT_MSG" or type=="WW_RECV_TEXT_IMG_MSG":
            WxBotMessage.add_message(data)

            xdata=data.get("data")
            receiver=xdata.get("receiver")
            sender_name=xdata.get("sender_name")
            sender=xdata.get("sender")
            conversation_id=xdata.get("conversation_id")
            content=xdata.get("content") or xdata.get("text_content")
            at_list=xdata.get("at_list")
            
            ai_run=False
            if conversation_id.startswith("R:"):
                #群聊
                if "@洋帆AI" in content or any(user['user_id'] == xbot_client_user_id for user in at_list):
                    ai_run=True
                
            elif conversation_id.startswith("S:"):
                #私聊
                if sender!=xbot_client_user_id:
                    ai_run=True


            if ai_run:
                
                history_msgs=WxBotMessage.get_messages_paged(page_num=1,page_size=5,conversation_id=conversation_id,user_id=None,client_id=None,receiver=None,sender=None).get("rows",[])

                user_input=""
                for message in history_msgs:
                    if message.get("sender")==xbot_client_user_id:
                        tm="客服："+replace_jd_content(message.get("content"))+"\n"
                        user_input+=tm
                    else:
                        tm="用户："+replace_jd_content(message.get("content"))+"\n"
                        user_input+=tm

                question=sender_name+":"+replace_jd_content(content)

                workflow_model = WorkFlow.get(workflow_id)
                graph = load_graph(workflow_id=workflow_id,
                                json_data=workflow_model.data_json,
                                user_id=conversation_id,
                                pin_id=sender_name,
                                workflow_source_name="企业微信"
                                )
                #TODO 加载压缩聊天记录
                result=run_graph(workflow_id=workflow_id,
                    workflow_name=workflow_model.name,
                    graph=graph,
                    input_dict={"user_input":user_input,"question":question},
                    callbacks=[XbotWorkingLoggingCallback()]
                )
    except Exception as e:
        print(e,data)
        logger.error(f"Error: {e}, data: {data}")
    finally:
        on_request_end()

# 声明回调地址接口
@router.post("/{workflow_id}/callback", summary="回调地址接口")
def callback(workflow_id:int=Path(...), data:Any = Body(...)):
    thread = threading.Thread(target=process_ai_logic, args=(workflow_id, data))
    thread.start()
    return {"result": "ok"}