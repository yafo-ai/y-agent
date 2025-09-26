import json
from typing import List,Tuple

import chromadb

from src.configs.system_config import system_config, ConnectType
from src.rag.chroma2 import Chroma
from src.rag.chroma_client import get_chroma_client
from src.rag.models.documents import Document
from src.embedding.embeddings_factory import embedding_mode
from src.configs.server_config import WEB_URL
from src.database.models import ProductModel,KnowledgeDocument
from src.rag.splitter.markdown import MarkdownHeaderTextSplitter
from src.rag.splitter.character import RecursiveCharacterTextSplitter


class KnowledgeChromaVectorStore():

    _PERSIST_DIRECTORY="./src/db/chroma_db"
    _DEFAULT_COLLECTION_NAME="yafo_document"
    _DOCUMENT_PREFIX="knowledge_document"
    _PRODUCT_PREFIX="product_model"

    def __init__(self,persist_directory=_PERSIST_DIRECTORY,collection_name=_DEFAULT_COLLECTION_NAME):
        self.sys_knowledge = system_config.sys_db_knowledge
        chroma_client = None
        sys_vector = system_config.sys_db_vector
        if sys_vector.selected_connect_type == ConnectType.remote:
            chroma_client = get_chroma_client(sys_vector)

        self.vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=embedding_mode,
            collection_name=collection_name,
            client=chroma_client,
            collection_metadata={
                "hnsw:space": "cosine",
                "hnsw:search_ef": 200
            }
        )

    def add_document_vindex(self,knowledge_doucment:KnowledgeDocument):

        """文档知识向量化，markdown内容拆分成多个document向量"""
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            # ("###", "Header 3"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        md_header_splits = markdown_splitter.split_text(knowledge_doucment.markdown.content)
        chunk_size = self.sys_knowledge.chunk_size
        chunk_overlap = self.sys_knowledge.chunk_size_overlap
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        splits_texts = text_splitter.split_documents(md_header_splits)

        texts=[]
        ids=[]
        metadatas=[]
        h1_text=''
        h1_title=''
        cnt=len(splits_texts)
        for i in range(cnt):
            header_group=splits_texts[i]
            h1=header_group.metadata.get("Header 1","")
            h2=header_group.metadata.get("Header 2","")
            
            if h1!=h1_title:
                h1_text=''

            #当前是h1 判断下一个是不是h2
            if  h1!="" and h2=="":
                h1_text="# "+h1+"\n"+header_group.page_content+"\n"
                h1_title=h1
                if i+1<=cnt-1 :
                    next_header_gorup=splits_texts[i+1]
                    next_h1=next_header_gorup.metadata.get("Header 1","")
                    next_h2=next_header_gorup.metadata.get("Header 2","")
                    if next_h2 and h1==next_h1:
                        continue

            text="> "+h1+" "+h2+"\n"
            if h1!="" and h2=="":
                text=text+"# "+h1+"\n"+header_group.page_content
            elif h2!="":
                #之前出现了是h1
                if h1_text!="":
                    text=text+h1_text+"## "+h2+"\n"+header_group.page_content
                else:
                    text=text+"# "+h1+"\n## "+h2+"\n"+header_group.page_content
            else:
                text=header_group.page_content

            texts.append(text)

            id=f"{self._DOCUMENT_PREFIX}_{knowledge_doucment.id}_{i}"
            ids.append(id)
            metadata={
                "id":id,
                "ref_id":f"{self._DOCUMENT_PREFIX}_{knowledge_doucment.id}",
                "ref_real_id":knowledge_doucment.id,
                "filename":knowledge_doucment.name,
                "knowledgebase_id":knowledge_doucment.knowledgebase_id,
                "type":self._DOCUMENT_PREFIX
                }
            metadatas.append(metadata)

        self.vectorstore.add_texts(texts=texts,metadatas=metadatas,ids=ids)
        return len(ids)

    def get_document_vindex(self,document_id:int):
        """获取文档索引"""
        filter={
            "$and": [
                {
                    "ref_id": {
                    "$eq": f"{self._DOCUMENT_PREFIX}_{document_id}"
                    }
                },
                {
                    "ref_real_id": {
                        "$eq": document_id
                    }
                }
            ]
        }
        rst_dict=self.vectorstore.get(where=filter)    #返回字典格式为：{'ids': ['1'], 'metadatas': [{'name': '华为笔记本'}], 'documents': ['华为笔记本']}
        _ids=rst_dict["ids"]
        _metadatas=rst_dict["metadatas"]
        _documents=rst_dict["documents"]
        documents=[]
        for i in range(len(_ids)):
            documents.append({"node_id":_ids[i],"text":_documents[i]})
        return documents

    def del_document_vindex(self,document_id:int):
        """删除文档知识索引"""
        filter={
            "$and": [
                {
                    "ref_id": {
                    "$eq": f"{self._DOCUMENT_PREFIX}_{document_id}"
                    }
                },
                {
                    "ref_real_id": {
                        "$eq": document_id
                    }
                }
            ]
        }
        rst_dict=self.vectorstore.get(where=filter) 
        ids=rst_dict["ids"]
        if len(ids)>0:
            self.vectorstore.delete(ids=ids)

    def add_product_vindex(self,product:ProductModel):
        """产品向量存存储,每个商品存一个向量，一对一的关系，直接用格式化后的id查询即可"""
        texts=[product.name]
        ids=[f"{self._PRODUCT_PREFIX}_{product.id}"]
        metadatas=[{"id":f"{self._PRODUCT_PREFIX}_{product.id}",
                    "ref_id":f"{self._PRODUCT_PREFIX}_{product.id}",
                    "ref_real_id":product.id,
                    "filename":product.name,
                    "knowledgebase_id":product.knowledgebase_id,
                    "type":self._PRODUCT_PREFIX
                   }]
        self.vectorstore.add_texts(texts=texts,metadatas=metadatas,ids=ids)

    def get_product_vindex(self,product_id:int)->List[Document]:
        """产品向量查询,每个商品存一个向量，一对一的关系，直接用格式化后的id查询即可"""
        ids=[f"{self._PRODUCT_PREFIX}_{product_id}"]
        rst_dict=self.vectorstore.get(ids=ids)    #返回字典格式为：{'ids': ['1'], 'metadatas': [{'name': '华为笔记本'}], 'documents': ['华为笔记本']}
        _ids=rst_dict["ids"]
        _metadatas=rst_dict["metadatas"]
        _documents=rst_dict["documents"]
        documents=[]
        for i in range(len(_ids)):
            documents.append(Document(page_content=_documents[i],metadata=_metadatas[i]))
        return documents
    
    def get_any_document_vindex(self,id:str)->List[Document]:
        """根据id查询"""
        filter={
                    "id": {
                    "$eq": f"{id}"
                    }
                }


        rst_dict=self.vectorstore.get(where=filter) 
        _ids=rst_dict["ids"]
        _metadatas=rst_dict["metadatas"]
        _documents=rst_dict["documents"]
        documents=[]
        for i in range(len(_ids)):
            doc=Document(page_content=_documents[i],metadata=_metadatas[i])
            doc_process=self._product_process((doc,0))
            documents.append(doc_process)
        return documents

    def del_product_vindex(self,product_id:int):
        """产品向量删除,直接用格式化id删除"""
        ids=[f"{self._PRODUCT_PREFIX}_{product_id}"]
        self.vectorstore.delete(ids=ids)

    def similarity_search_with_score(self,knowledgebase_ids:List[int],knowledgebase_k:int,query: str)-> List[Document]:
        """
        分库相似查询
        knowledgebase_ids：需要指定知识库id，支持多个 [知识库id1，知识库id2]
        knowledgebase_k：需要指定对应知识库检索的数量[1，2]
        """
        results=[]
        filter={"knowledgebase_id": {"$eq": knowledgebase_ids[0]}}
        if len(knowledgebase_ids)>1:
            filter={
                "$or": [
                    {
                        "knowledgebase_id": {
                        "$eq": item
                        }
                    } for item in knowledgebase_ids
                ]
            }
        documents=self.vectorstore.similarity_search_with_relevance_scores(query=query,k=knowledgebase_k,filter=filter)
        for doc in documents:
            doc_process=self._product_process(doc)
            results.append(doc_process)

        return results
    
    def similarity_search_with_score_titile(self,knowledgebase_ids:List[int],knowledgebase_k:int,query: str)-> List[Document]:
        """
        分库相似查询
        knowledgebase_ids：需要指定知识库id，支持多个 [知识库id1，知识库id2]
        knowledgebase_k：需要指定对应知识库检索的数量[1，2]
        """
        # 这个策略是，所有库一起一次查询，共同召回topk
        results=[]
        filter={"knowledgebase_id": {"$eq": knowledgebase_ids[0]}}
        if len(knowledgebase_ids)>1:
            filter={
                "$or": [
                    {
                        "knowledgebase_id": {
                        "$eq": item
                        }
                    } for item in knowledgebase_ids
                ]
            }
        documents=self.vectorstore.similarity_search_with_relevance_scores(query=query,k=knowledgebase_k,filter=filter)
        for doc in documents:
            doc_process=self._arrange_document(doc)
            results.append(doc_process)
        return results

    
    def _arrange_document(self,doc:Tuple[Document, float])->Document:
        """
        整理document
        把向量查询的2元组整理成3元数
        第3项存放实际原文。document里只包含简要信息
        """
        id=doc[0].metadata["ref_real_id"]
        if doc[0].metadata["type"]==self._DOCUMENT_PREFIX:
            # 标题 模式
            page_content=doc[0].page_content
            title=""
            lines=page_content.splitlines()
            line=lines[0]
            if line.startswith("> "):
                page_content=page_content.removeprefix(line)
                title=line.removeprefix("> ")
            if title=="":
                title=page_content
            doc[0].page_content=page_content
            doc[0].metadata["title"]=title
            doc[0].metadata["score"]=doc[1]
            doc[0].metadata["detali_url"]=f"{WEB_URL}/chat/detail?id={doc[0].metadata['knowledgebase_id']}&type={doc[0].metadata['type']}&did={doc[0].metadata['ref_real_id']}&rid={doc[0].metadata['ref_id']}"
            return doc[0]   

        else:
            product=ProductModel.get(id=id)
            if product:
                doc[0].page_content=product.get_text()
            doc[0].metadata["title"]=doc[0].metadata["filename"]
            doc[0].metadata["score"]=doc[1]
            doc[0].metadata["detali_url"]=f"{WEB_URL}/chat/detail?id={doc[0].metadata['knowledgebase_id']}&type={doc[0].metadata['type']}&did={doc[0].metadata['ref_real_id']}&rid={doc[0].metadata['ref_id']}"
            return doc[0]
        

    def _product_process(self,doc:Tuple[Document, float])->Document:
        doc[0].metadata["score"]=doc[1]
        doc[0].metadata["detali_url"]=f"{WEB_URL}/chat/detail?id={doc[0].metadata['knowledgebase_id']}&type={doc[0].metadata['type']}&did={doc[0].metadata['ref_real_id']}&rid={doc[0].metadata['ref_id']}"
        if doc[0].metadata["type"]!=self._PRODUCT_PREFIX:
            return doc[0]
        else:
            id=doc[0].metadata["ref_real_id"]
            product=ProductModel.get(id=id)
            if product:
                doc[0].page_content=product.get_text()
            return doc[0]
        
    def get(self,id:str)->Document:
        """指定向量id查询数据"""
        rst_dict=self.vectorstore.get(ids=[id])
        _ids=rst_dict["ids"]
        _metadatas=rst_dict["metadatas"]
        _documents=rst_dict["documents"]

        if len(_ids)>0:
            return self._arrange_document((Document(page_content=_documents[0],metadata=_metadatas[0]),1.0))
        return None



if __name__ == "__main__":
    db=KnowledgeChromaVectorStore()
    doc=db.similarity_search_with_score_titile(knowledgebase_ids=[5],knowledgebase_k=4,query="打开手机超级终端")
    print(doc)