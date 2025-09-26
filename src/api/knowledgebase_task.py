from datetime import datetime

from src.api.customer_exception import ValidationException
from src.database.db_session import set_current_request_id, on_request_end
from src.database.models import KnowledgeDocument, FileDatabaseModel
from src.rag.excel_vector_store import ExcelChromaVectorStore
from src.rag.knowledge_vector_store import KnowledgeChromaVectorStore
from src.utils.log_helper import logger


def document_convert_index_task(knowledgebase_id):
    set_current_request_id()
    try:
        documents = KnowledgeDocument.query.filter_by(knowledgebase_id=knowledgebase_id, is_index=True).all()
        if not documents:
            raise ValidationException(f"没有找到要更新的文档知识库[{knowledgebase_id}]")
        vector = KnowledgeChromaVectorStore()
        for doc in documents:
            vector.del_document_vindex(doc.id)
            node_qty = vector.add_document_vindex(doc)
            doc.set_index_ok(node_qty)
    except Exception as e:
        logger.error(f"更新文档知识库[{knowledgebase_id}]索引失败：{e}")
    finally:
        print(f"更新文档知识库[{knowledgebase_id}]索引完成")
        on_request_end()


def filedata_convert_index_task(knowledgebase_id):
    set_current_request_id()
    try:
        documents = FileDatabaseModel.query.filter_by(knowledgebase_id=knowledgebase_id, is_index=True).all()
        if not documents:
            raise ValidationException(f"没有找到要更新的参数知识库[{knowledgebase_id}]")
        vector = ExcelChromaVectorStore()
        for document in documents:
            vector.del_products_index(document.id)
            for file_content in document.file_contents:
                vector.add_product_index(knowledgebase_id, document.id, document.file_name, file_content.relation_code,
                                         file_content.relation_index, file_content.markdown_content,
                                         file_content.get_metadata)
            document.index_at = datetime.now()
            document.is_index_refresh = False
            document.index_refresh_at = datetime.now()
            document.update(True)
    except Exception as e:
        logger.error(f"更新参数知识库[{knowledgebase_id}]索引失败：{e}")
    finally:
        print(f"更新参数知识库[{knowledgebase_id}]索引完成")
        on_request_end()
