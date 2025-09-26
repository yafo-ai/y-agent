import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from src.agent.model_types import SendHumanMessageEvent
from src.utils.log_helper import logger
import concurrent.futures

class WebSocketManager:
    """
    websocket管理器
    """

    def __init__(self,subscriber_queue):
        self.handlers: dict = {}
        self.subscriber_queue=subscriber_queue
        self.user_sockets: dict = {} #{客服id: websocket}
        self.questions: list = [] # 存储正在运行的问题id
        asyncio.create_task(self.reader_ai_message())

    def handler(self, message_type):
        def decorator(func):
            self.handlers[message_type] = func
            return func

        return decorator
    
    async def connect_socket(self, websocket: WebSocket):
        """接受一个连接"""
        await websocket.accept()

    
    async def add_user_socket_connection(self, pin_id: str, websocket: WebSocket):
        """存储客服的socket连接"""
        self.user_sockets.setdefault(pin_id, set()).add(websocket)


    async def reader_ai_message(self):
        """"接收AI消息,发送给用户"""
        # 获取主事件循环
        loop = asyncio.get_event_loop()
        def get_message():
            while True:
                try:
                    message = self.subscriber_queue.get()
                    self.subscriber_queue.task_done()
                
                    if isinstance(message, SendHumanMessageEvent):
                        for websocket in self.user_sockets.get(message.pin_id, []):
                            try:
                                print(f"send message to {message.pin_id}, user_id={message.user_id}, question_id={message.question_id}, message={message.message}")   
                                # asyncio.run(websocket.send_json({"type":"ai_answer","data":{"question_id":message.question_id,"user_id":message.user_id,"pin_id":message.pin_id,"workflow_id":message.workflow_id,"message":message.message,"role":message.node_role,"id":message.id}}))
                                coro=websocket.send_json({"type":"ai_answer","data":{"question_id":message.question_id,"user_id":message.user_id,"pin_id":message.pin_id,"workflow_id":message.workflow_id,"message":message.message,"role":message.node_role,"id":message.id}})
                                asyncio.run_coroutine_threadsafe(coro, loop)
                            except Exception as ex:
                                print(f"发送失败{ex}")
                                
                except Exception as ex:
                    print(f"发送失败{ex}")

        import threading
        threading.Thread(target=get_message).start()

        

    async def remove_user_socket_connection(self, pin_id: str, websocket: WebSocket):
        """删除客服的socket连接"""
        if pin_id in self.user_sockets:
            self.user_sockets.get(pin_id).remove(websocket)


    async def send_ai_finish(self, data: dict,pin_id: str):
        """发送结束信息"""
        for websocket in self.user_sockets.get(pin_id, []):
            try:
                print(f"send ai_finish to {pin_id}")
                await websocket.send_json({"type": "ai_finish","data":data})
            except Exception as ex:
                print(f"发送失败{ex}")

    async def send_error(self, message: str,pin_id: str):
        """发送错误信息"""
        for websocket in self.user_sockets.get(pin_id, []):
            try:
                print(f"send error to {pin_id}, message={message}")
                await websocket.send_json({"type": "error","data":{"message": message}})
            except Exception as ex:
                print(f"发送失败{ex}")