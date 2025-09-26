import contextlib
from collections.abc import Iterator
from typing import Optional, cast

from src.rag.extractor.base_extractor import BaseExtractor
from src.rag.extractor.blob import Blob
from src.rag.models.documents import Document


class PdfExtractor(BaseExtractor):
    """Load pdf files.


    Args:
        file_path: Path to the file to load.
    """

    def __init__(self, file_path: str):
        """Initialize with file path."""
        self._file_path = file_path


    def extract(self) -> list[Document]:

        documents = list(self.load())

        return documents

    def load(
        self,
    ) -> Iterator[Document]:
        """Lazy load given path as pages."""
        blob = Blob.from_path(self._file_path)
        yield from self.parse(blob)

    def parse(self, blob: Blob) -> Iterator[Document]:
        """Lazily parse the blob."""
        import pypdfium2  # type: ignore

        with blob.as_bytes_io() as file_path:
            pdf_reader = pypdfium2.PdfDocument(file_path, autoclose=True)
            try:
                for page_number, page in enumerate(pdf_reader):
                    text_page = page.get_textpage()
                    content = text_page.get_text_range()
                    text_page.close()
                    page.close()
                    metadata = {"source": blob.source, "page": page_number}
                    yield Document(page_content=content, metadata=metadata)
            finally:
                pdf_reader.close()


if __name__ == "__main__":
    extractor = PdfExtractor("E:\\金兆宇--运营助理.pdf")
    documents = extractor.extract()
    print(documents)