
from abc import ABC, abstractmethod

from src.agent.model_types import BaseEvent,SendHumanMessageEvent
from src.plugins.xbot_utils import send_text_msg
from src.agent.pub_sub_queue import PubSubQueue, Topics


class WorkingCallback(ABC):
    @abstractmethod
    def on_event(self, event: BaseEvent) -> None:
        """
        Published event
        """
        raise NotImplementedError
    


class WorkingLoggingCallback(WorkingCallback):
    """"
    各种事件回调
    """
    def __init__(self,queue:PubSubQueue|None=None):
        self.queue = queue
        pass

    def on_event(self, event: BaseEvent) -> None:
        
        if isinstance(event,SendHumanMessageEvent):
            self.on_human_message_send(event)

    def on_human_message_send(self, event: SendHumanMessageEvent) -> None:
        if self.queue:
            self.queue.publish(Topics.human_message_topic, event)


class XbotWorkingLoggingCallback(WorkingCallback):
    """"
    各种事件回调
    """
    def __init__(self):
        pass

    def on_event(self, event: BaseEvent) -> None:
        
        if isinstance(event,SendHumanMessageEvent):
            self.on_human_message_send(event)

    def on_human_message_send(self, event: SendHumanMessageEvent) -> None:
        send_text_msg(1,event.user_id,event.message)