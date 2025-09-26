from pathlib import Path
from typing import Optional

from src.rag.extractor.base_extractor import BaseExtractor
from src.rag.extractor.helpers import detect_file_encodings
from src.rag.models.documents import Document



class TextExtractor(BaseExtractor):
    """Load Text files.

    Args:
        file_path: Path to the file to load.
        encoding: Encoding of the file.
        autodetect_encoding: Whether to automatically detect encoding.

    """

    def __init__(self, file_path: str, encoding: Optional[str] = None, autodetect_encoding: bool = False):
        self._file_path = file_path
        self._encoding = encoding
        self._autodetect_encoding = autodetect_encoding

    def extract(self) -> list[Document]:
        """Load from file path."""
        text = ""
        try:
            text = Path(self._file_path).read_text(encoding=self._encoding)
        except UnicodeDecodeError as e:
            if self._autodetect_encoding:
                detected_encodings = detect_file_encodings(self._file_path)
                for encoding in detected_encodings:
                    try:
                        text = Path(self._file_path).read_text(encoding=encoding.encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise RuntimeError(
                        f"Decode failed: {self._file_path}, all detected encodings failed. Original error: {e}"
                    )
            else:
                raise RuntimeError(f"Decode failed: {self._file_path}, specified encoding failed. Original error: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading {self._file_path}") from e

        metadata = {"source": self._file_path}
        return [Document(page_content=text, metadata=metadata)]
    


if __name__ == "__main__":
    extractor = TextExtractor("E:\\a.txt",encoding="utf-8",autodetect_encoding=True)
    documents = extractor.extract()
    print(documents)