from enum import Enum
import queue
import threading

class Topics:
    # 定义消息主题
    human_message_topic = "human_message"




class PubSubQueue:
    def __init__(self):
        # 创建一个字典来存储订阅者队列
        self.subscribers = {}

    def publish(self, topic, message):
        # 如果没有订阅者，则直接返回
        if topic not in self.subscribers:
            return
        
        # 将消息发送给所有订阅者
        for subscriber_queue in self.subscribers[topic]:
            subscriber_queue.put(message)

    def subscribe(self, topic):
        # 创建一个队列用于该订阅者接收消息
        subscriber_queue = queue.Queue()
        
        # 如果是新的主题，则初始化订阅者列表
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        
        # 将订阅者队列添加到订阅者列表中
        self.subscribers[topic].append(subscriber_queue)
        
        return subscriber_queue

    def unsubscribe(self, topic, subscriber_queue):
        # 从订阅者列表中移除指定的订阅者队列
        if topic in self.subscribers:
            if subscriber_queue in self.subscribers[topic]:
                self.subscribers[topic].remove(subscriber_queue)
            # 如果主题下没有订阅者了，则删除该主题
            if not self.subscribers[topic]:
                del self.subscribers[topic]

