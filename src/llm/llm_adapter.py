from abc import ABC, abstractmethod

import requests

from openai import OpenAI, APIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from zhipuai import ZhipuAI

from src.api.customer_exception import ValidationException
from src.llm.llm_models import LLMResult, ChatMessage, ContentType
from src.database.models import ModelConfig


class BaseAdapter(ABC):
    def __init__(self, **kwargs):
        self.api_key = kwargs.get('api_key')
        if self.api_key is None or self.api_key.strip() == "":
            self.api_key="EMPTY"
        self.base_url = kwargs.get('base_url', 'https://api.openai.com/v1')
        self.model = kwargs.get('model', 'gpt-3.5-turbo')
        self.max_retries = kwargs.get('max_retries', 3)
        self.streaming = kwargs.get('streaming', False)
        self.timeout = kwargs.get('timeout', 300)
        self.temperature = kwargs.get('temperature', 0.1)
        self.max_tokens = kwargs.get('max_tokens', None)
        self.name=kwargs.get('name',self.model)


    def convert_text_message(self, message: ChatMessage) -> dict[str, any]:
        return {
            "role": message.role,
            "content": message.content or ""
        }

    def convert_vision_message(self, message: ChatMessage) -> dict[str, any]:
        content = []
        for c in message.content:
            if c.type == ContentType.TEXT:
                content.append({
                    "type": "text",
                    "text": c.value
                })
            elif c.type == ContentType.IMAGE:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": c.value
                    }
                })
            elif c.type == ContentType.VIDEO.value:
                content.append({
                    "type": "video_url",
                    "video_url": {
                        "url": c.value
                    }
                })
            elif c.type == ContentType.AUDIO.value:
                content.append({
                    "type": "audio_url",
                    "audio_url": {
                        "url": c.value
                    }
                })
            elif c.type == ContentType.FILE.value:
                content.append({
                    "type": "file_url",
                    "file_url": {
                        "url": c.value
                    }
                })
        return {"role": message.role, "content": content}


    def convert_messages(self, messages: list[ChatMessage]) -> list[dict[str, any]]:
        data= []
        for message in messages:
            if isinstance(message.content,str):
                data.append(self.convert_text_message(message))
            else:
                data.append(self.convert_vision_message(message))
        return data


    @abstractmethod
    def generate(self, messages: list[ChatMessage], **kwargs) -> LLMResult:
        raise NotImplementedError("子类必须实现 execute 方法")
    


class OpenAIAdapter(BaseAdapter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = OpenAI(api_key=self.api_key,
                        base_url=self.base_url,
                        max_retries=self.max_retries,
                        timeout=self.timeout)
        
    def __del__(self):
        self.client.close()


    def generate(self, messages: list[ChatMessage], **kwargs) -> LLMResult:

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.convert_messages(messages),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **kwargs
        )

        total_tokens = getattr(response.usage, 'total_tokens', 0) if hasattr(response, 'usage') else 0
        finish_reason = getattr(response.choices[0], 'finish_reason', None)

        return LLMResult(
            content=response.choices[0].message.content,
            model=self.model,
            total_tokens=total_tokens,
            response_metadata={"token_usage": dict(getattr(response.usage, '__dict__', {})) if hasattr(response, 'usage') else {}, 
                               "model_name": self.model, 
                               "finish_reason": finish_reason}
        )


class ZhipuAdapter(BaseAdapter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = kwargs.get('base_url', 'https://open.bigmodel.cn/api/paas/v3/chat/completions')
        self.model = kwargs.get('model', 'zhimabot-v1')
        self.client=ZhipuAI(api_key=self.api_key,
                         base_url=self.base_url,
                         max_retries=self.max_retries,
                         timeout=self.timeout)
    def __del__(self):
        self.client.close()
        
    def generate(self, messages: list[ChatMessage], **kwargs) -> LLMResult:

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.convert_messages(messages),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **kwargs
        )

        return LLMResult(
            content=response.choices[0].message.content,
            model=self.model,
            total_tokens=response.usage.total_tokens if response.usage is not None else 0,
            response_metadata={"token_usage": dict(response.usage) if response.usage is not None else {}, "model_name": self.model, "finish_reason": response.choices[0].finish_reason}
        )


class OllamaAdapter(BaseAdapter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = kwargs.get('base_url', 'http://192.168.50.131:11434/api/chat')
        self.model = kwargs.get('model', 'Qwen2.5-7b-v2.3-2-18-Q6_K')

    def convert_vision_message(self, message: ChatMessage) -> dict[str, any]:
        texts = [m.value for m in message.content if m.type == ContentType.TEXT]
        images = [m.value for m in message.content if m.type == ContentType.IMAGE]
        return {"role": message.role, "content": texts[0] if len(texts) > 0 else "", "images": images}
    
    def generate(self, messages: list[ChatMessage], **kwargs) -> LLMResult:

        data = {
            "model": self.model,
            "messages": self.convert_messages(messages),
            "stream": self.streaming,
            "options": {
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
        }
        
        response = requests.post(self.base_url, json=data, timeout=self.timeout)

        response=response.json()

        return LLMResult(
            content=response.get('message', {}).get('content', ''),
            model=self.model,
            total_tokens=response.get("prompt_eval_count",0)+response.get("eval_count",0),
            response_metadata={"token_usage":{"completion_tokens": response.get("eval_count",0), "prompt_tokens": response.get("prompt_eval_count",0), "total_tokens": response.get("prompt_eval_count",0)+response.get("eval_count",0)}, "model_name": self.model, "finish_reason": response.get("done_reason","")}
        )




class AdapterFactory:
    def __init__(self, id: int):
        self.id = id
        self.model = ModelConfig.get(id)

    def instance(self) -> BaseAdapter:
        model = self.model
        if model.provider.lower() == 'zhipuai':
            return ZhipuAdapter(api_key=model.api_key, base_url=model.api_url, model=model.base_name, temperature=model.temprature, timeout=model.timeout,name=model.name)

        elif model.provider.lower() == 'ollama':
            return OllamaAdapter(api_key=model.api_key, model=model.base_name, temperature=model.temprature, timeout=model.timeout,name=model.name)
        return OpenAIAdapter(api_key=model.api_key, base_url=model.api_url, model=model.base_name, temperature=model.temprature, timeout=model.timeout,name=model.name)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10),
           retry=retry_if_exception_type((APIError, requests.RequestException)))
    def invoke(self, inputs: list[ChatMessage] = None, **kwargs) ->LLMResult:
        adapter = self.instance()
        try:
            response = adapter.generate(inputs, **kwargs)
            return response
        except Exception as a:
            raise ValidationException(f"调用{adapter.__class__.__name__}失败,原因:{str(a)}")

