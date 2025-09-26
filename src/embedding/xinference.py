from typing import Any, List, Optional
from src.embedding.embeddings import Embeddings

class XinferenceEmbeddings(Embeddings):

    client: Any
    server_url: Optional[str]
    model_uid: Optional[str]

    def __init__(
        self, server_url: Optional[str] = None, model_uid: Optional[str] = None, api_key: Optional[str] = None
    ):
        try:
            from xinference.client import RESTfulClient
        except ImportError as e:
            raise ImportError(
                "Could not import RESTfulClient from xinference. Please install it"
                " with `pip install xinference`."
            ) from e

        super().__init__()

        if server_url is None:
            raise ValueError("Please provide server URL")

        if model_uid is None:
            raise ValueError("Please provide the model UID")

        self.server_url = server_url

        self.model_uid = model_uid

        self.client = RESTfulClient(server_url)
        self.client._set_token(api_key)


    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents using Xinference.
        Args:
            texts: The list of texts to embed.
        Returns:
            List of embeddings, one for each text.
        """

        model = self.client.get_model(self.model_uid)

        embeddings = [
            model.create_embedding(text)["data"][0]["embedding"] for text in texts
        ]
        return [list(map(float, e)) for e in embeddings]

    def embed_query(self, text: str) -> List[float]:
        """Embed a query of documents using Xinference.
        Args:
            text: The text to embed.
        Returns:
            Embeddings for the text.
        """

        model = self.client.get_model(self.model_uid)

        embedding_res = model.create_embedding(text)

        embedding = embedding_res["data"][0]["embedding"]

        return list(map(float, embedding))

if __name__ == "__main__":
    embeddings = XinferenceEmbeddings(
        server_url="http://192.168.50.131:9997", model_uid="bge-m3",
    )
    query = "这是一个测试" 
    print(embeddings.embed_query(query))