from abc import ABC, abstractmethod
import asyncio
from typing import Any, Literal, Optional, Sequence
from pydantic import BaseModel

class Document(BaseModel):

    page_content: str

    metadata: dict = {}

    type: Literal["Document"] = "Document"



class BaseDocumentTransformer(ABC):
    

    @abstractmethod
    def transform_documents(self, documents: Sequence[Document], **kwargs: Any) -> Sequence[Document]:
        """Transform a list of documents.

        Args:
            documents: A sequence of Documents to be transformed.

        Returns:
            A list of transformed Documents.
        """

    
    async def atransform_documents(self, documents: Sequence[Document], **kwargs: Any) -> Sequence[Document]:
        """Asynchronously transform a list of documents.

        Args:
            documents: A sequence of Documents to be transformed.

        Returns:
            A list of transformed Documents.
        """
        result = await asyncio.to_thread(self.transformdocuments, documents, kwargs)
        return result