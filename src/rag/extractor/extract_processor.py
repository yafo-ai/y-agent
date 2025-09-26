
from typing import Optional

from src.rag.extractor.csv_extractor import CSVExtractor
from src.rag.extractor.excel_extractor import ExcelExtractor
from src.rag.extractor.html_extractor import HtmlExtractor
from src.rag.extractor.markdown_extractor import MarkdownExtractor
from src.rag.extractor.pdf_extractor import PdfExtractor
from src.rag.extractor.text_extactor import TextExtractor
from src.rag.extractor.word_extractor import WordExtractor
from src.rag.models.documents import Document


class ExtractProcessor:
    def __init__(self):
        self.file_extension  = {}

    @classmethod
    def extract(
        cls, file_path: str,file_extension:str,is_automatic: bool = False,
    ) -> list[Document]:

        if file_extension in {".xlsx", ".xls"}:
            extractor = ExcelExtractor(file_path)
        elif file_extension == ".pdf":
            extractor = PdfExtractor(file_path)
        elif file_extension==".md":
            extractor = MarkdownExtractor(file_path, autodetect_encoding=is_automatic)
        elif file_extension in {".htm", ".html"}:
            extractor = HtmlExtractor(file_path)
        elif file_extension == ".docx":
            extractor = WordExtractor(file_path)
        elif file_extension == ".csv":
            extractor = CSVExtractor(file_path, autodetect_encoding=is_automatic)
        elif file_extension==".txt":
            extractor = TextExtractor(file_path,encoding="utf-8",autodetect_encoding=is_automatic)
        else:
            raise ValueError(f"文档格式不支持: {file_extension}")
    
        return extractor.extract()
        
        