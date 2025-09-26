from enum import Enum
from typing import Optional, Union, Any, Sequence

from pydantic.v1 import BaseModel


class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class ContentType(Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    IMAGE_BASE64 = "image_base64"


class MessageContent(BaseModel):
    value: Optional[str] = None
    type: ContentType = ContentType.TEXT


class ChatMessage(BaseModel):
    role: MessageRole.USER.value
    content: Optional[str | Sequence[MessageContent]] = None


class HumanMessage(ChatMessage):
    role: str = MessageRole.USER.value


class SystemMessage(ChatMessage):
    role: str = MessageRole.SYSTEM.value


class AIMessage(ChatMessage):
    role: str = MessageRole.ASSISTANT.value


class LLMResult(BaseModel):
    """
    大模型响应结果
    """
    content: str

    model:str

    total_tokens:int

    response_metadata: Optional[dict] = None
