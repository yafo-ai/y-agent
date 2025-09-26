from typing import List, Optional
import requests
from src.embedding.embeddings import Embeddings
from openai import OpenAI

class OpenAIEmbeddings(Embeddings):
    """vLLM Embedding 服务客户端实现"""
    server_url: Optional[str]
    model_uid: Optional[str]

    def __init__(
        self,
        server_url: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None
    ):

        if server_url.endswith("/embeddings"):
            server_url=server_url.replace("/embeddings", "")

        if api_key is None or api_key == "":
            api_key = "Empty"

        self.server_url = server_url
        
        self.model_name = model_name
        self.api_key = api_key
        self.max_retries = 3
        self.timeout = 10
        self.client = OpenAI(api_key=self.api_key,
                        base_url=self.server_url,
                        max_retries=self.max_retries,
                        timeout=self.timeout)
        
    def __del__(self):
        self.client.close()

    def _request_embedding(self, text: str) -> dict:
        """发送单个 embedding 请求"""
    
        response = self.client.embeddings.create(
            input=text,
            model=self.model_name
        )

        if not isinstance(response, dict):
            response = response.model_dump()

        return response


    def _parse_embedding(self, data: dict) -> List[float]:
        """解析响应数据结构"""
        if "data" in data and isinstance(data["data"], list):
            if len(data["data"]) == 0:
                raise ValueError("空数据响应")
            return data["data"][0].get("embedding", [])
        if "embedding" in data:
            return data["embedding"]
        raise ValueError("无法识别的响应格式")

    def embed_query(self, text: str) -> List[float]:
        """获取单个查询的嵌入向量"""
        response_data = self._request_embedding(text)
        return self._parse_embedding(response_data)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量获取文档的嵌入向量"""
        return [self.embed_query(text) for text in texts]
    

if __name__ == "__main__":
    # 测试代码
    server_url = "http://192.168.50.225:8001/v1/embeddings"
    model_name = "bge-m3"
    embeddings = OpenAIEmbeddings(server_url, model_name, api_key="")
    query = "这是一个测试" 
    print(embeddings.embed_query(query))