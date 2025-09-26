from typing import List, Optional
import requests
from src.embedding.embeddings import Embeddings

class VmllEmbeddings(Embeddings):
    """vLLM Embedding 服务客户端实现"""
    server_url: Optional[str]
    model_uid: Optional[str]

    def __init__(
        self,
        server_url: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None
    ):

        self.server_url = server_url
        self.model_name = model_name
        self.api_key = api_key

    def _request_embedding(self, text: str) -> dict:
        """发送单个 embedding 请求"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "vmll-embeddings/1.0"
        }
        if self.api_key is not None and self.api_key != "":
            headers["Authorization"] = f"Bearer {self.api_key}" if not self.api_key.lower().startswith('bearer') else self.api_key
        payload = {
            "input": text,
            "model": self.model_name
        }

        response = requests.post(
            self.server_url,
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()

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
    embeddings = VmllEmbeddings(server_url, model_name)
    query = "这是一个测试" 
    print(embeddings.embed_query(query))