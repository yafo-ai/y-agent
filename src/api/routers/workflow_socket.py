import asyncio
from json import JSONDecodeError
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.utils.log_helper import logger
from src.agent.socket.websocket_handlers import socket_manager,subscriber_queue

router = APIRouter()


@router.websocket("/ws/{pin_id}/workflow")
async def websocket_endpoint(websocket: WebSocket,pin_id:str):
    """
    type:业务接口
    workflow_id：流程id
    pin_id：客服账号id
    user_id：用户id
    question_id：问题id，每个问题独立一个id
    chat_history：聊天记录

    socket接口：
    1、ai问题：{"type":"ai_run","data":{"question_id":"","user_id":"","workflow_id":"","pin_id":"","chat_history":[]}}
    2、评分：{"type":"feedback_score","data":{"question_id":"","user_id":"","pin_id":"","score":"","amend_answer":""}}
    3、type:根据业务发展，可以扩展

    后端发送的消息：
    1、ai回答：{"type":"ai_answer","data":{"question_id":"","user_id":"","pin_id":"","answer":""}}
    2、问题完成{"type":"ai_finish","data":{"question_id":"","user_id":"","pin_id":""}}
    3、错误信息{"type":"error","data":{"message":""}}


    """
    await socket_manager.connect_socket(websocket=websocket)

    print(f"接受一个socket链接......{socket_manager}")

    await socket_manager.add_user_socket_connection(pin_id, websocket)

    try:
        while True:
            try:
                _json = await websocket.receive_json()
                print(_json)

                data_type = _json.get("type")

                if not data_type:
                    await socket_manager.send_error("数据错误，缺少type字段", pin_id)
                    continue

                handler = socket_manager.handlers.get(data_type)

                if not handler:
                    logger.error(f"No handler [{data_type}] exists")
                    await socket_manager.send_error(f"Type: {data_type} was not found", pin_id)
                    continue

                json_data=_json.get("data")

                if not json_data:
                    await socket_manager.send_error("数据错误，缺少data字段", pin_id)
                    continue
                    

                await handler(
                    websocket=websocket,
                    pin_id=pin_id,
                    json_data=json_data
                )
                

            except (JSONDecodeError, AttributeError) as ex:
                print("JSONDecodeError"+str(ex))
                await socket_manager.send_error("数据json格式化错误", pin_id)

            except ValueError as ex:
                print("ValueError"+str(ex))
                await socket_manager.send_error(str(ex), pin_id)

            
    except WebSocketDisconnect:
        print("socket链接断开......")
        await socket_manager.remove_user_socket_connection(pin_id, websocket)

