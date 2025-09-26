import json
from typing import List,Tuple

import chromadb

from src.configs.system_config import system_config, ConnectType
from src.rag.chroma2 import Chroma
from src.rag.chroma_client import get_chroma_client
from src.rag.models.documents import Document
from src.embedding.embeddings_factory import embedding_mode
from src.rag.splitter.markdown import MarkdownHeaderTextSplitter
from src.rag.splitter.character import RecursiveCharacterTextSplitter

from src.configs.server_config import WEB_URL


class ExcelChromaVectorStore():
    """
    把Excel的中的产品数据存储为向量索引
    存储的规则如下：
    1、每个Excel文件都有唯一ID，ID 可以关联索引数据，可以批量删除。
    2、Excel中的每个产品，都有唯一的nc_code,用于限定查询
    3、每个产品 按照 一级标题 拆分多个块存储多分向量
    4、暂定：每个Excel只能整体向量化。（nc_code也有可能被修改）
    注意：存储数据的格式要与其他向量格式一致，避免调用程序端（前端）针对不同业务硬编码
    """
    _PERSIST_DIRECTORY="./src/db/chroma_db"
    _DEFAULT_COLLECTION_NAME="yafo_excel"
    _DOCUMENT_PREFIX="excel_document"

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

    def add_product_index(self,knowledgebase_id:int,excel_id:int,filename:str,relation_code:str,index:int|None,markdown_content:str,filter_data:dict):
        """
        excel产品向量化，markdown内容拆分成多个document向量
        参数：
        knowledgebase_id:知识库id
        excel_id：excel文件id
        filename：excel的文件名称
        relation_code:产品的NC编码，可以用于锁定一个产品
        markdown_content:一个产品的内容，需要按照标题正好markdown结构
        """
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        md_header_splits = markdown_splitter.split_text(markdown_content)
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

            id=f"{excel_id}_{relation_code}_{i}"
            if index is not None:
                id=f"{excel_id}_{index}_{i}"
            ids.append(id)
            metadata={
                "id":id,
                "ref_id":excel_id,
                "ref_real_id":relation_code,
                "filename":filename,
                "knowledgebase_id":knowledgebase_id,
                "type":self._DOCUMENT_PREFIX
                }
            for k,v in filter_data.items():
                metadata[k]=v
            metadatas.append(metadata)
            i+=1

        self.vectorstore.add_texts(texts=texts,metadatas=metadatas,ids=ids)
        return len(ids)

    def get_product_index(self,excel_id:int,relation_code:str):
        """获取文档索引"""
        filter={
            "$and": [
                {
                    "ref_id": {
                    "$eq": excel_id
                    }
                },
                {
                    "ref_real_id": {
                        "$eq": relation_code
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

    def del_products_index(self,excel_id:int):
        """按照excel删除向量库"""
        filter={
                "ref_id": {
                    "$eq": excel_id
                }
         }
        rst_dict=self.vectorstore.get(where=filter)    #返回字典格式为：{'ids': ['1'], 'metadatas': [{'name': '华为笔记本'}], 'documents': ['华为笔记本']}
        _ids=rst_dict["ids"]
        if len(_ids)>0:
            self.vectorstore.delete(ids=_ids)

    def similarity_search_with_score(self,knowledgebase_ids:List[int],query: str,top_k:int)-> List[Document]:
        """
        分库相似查询，2元素
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
        documents=self.vectorstore.similarity_search_with_relevance_scores(query=query,k=top_k,filter=filter)
        for doc in documents:
            doc_process=self._arrange_document(doc)
            results.append(doc_process)
        return results
    
    def similarity_search_with_score_titile(self,knowledgebase_ids:List[int],query: str,top_k:int)-> List[Document]:
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

        documents=self.vectorstore.similarity_search_with_relevance_scores(query=query,k=top_k,filter=filter)
        for doc in documents:
            doc_process=self._arrange_document(doc)
            results.append(doc_process)
        return results
    
    def similarity_search_with_score_titile_by_code(self,knowledgebase_ids:List[int],relation_code:str,query: str,top_k:int)-> List[Document]:
        """
        分库相似查询，3元素
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

        and_filter={"ref_real_id": {"$eq": relation_code}}

        combined_filter = {"$and": [filter, and_filter]}

        documents=self.vectorstore.similarity_search_with_relevance_scores(query=query,k=top_k,filter=combined_filter)
        for doc in documents:
            doc_process=self._arrange_document(doc)
            results.append(doc_process)
        return results
    
    def similarity_search_with_score_titile_by_filter(self,knowledgebase_ids:List[int],query: str,top_k:int,where:list[dict])-> List[Document]:
        """
        分库相似查询，3元素
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

        # and_filter={"ref_real_id": {"$eq": ref_id}}
        and_filter=[filter]+where
        if len(and_filter)>1:
            combined_filter = {"$and": and_filter}
        else:
            combined_filter=filter


        documents=self.vectorstore.similarity_search_with_relevance_scores(query=query,k=top_k,filter=combined_filter)
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
        # return (doc[0],doc[1],page_content)

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

    db=ExcelChromaVectorStore()

    doc=db.similarity_search_with_score_titile(knowledgebase_ids=[16], query="华为PixLab X1（CV81-WDM） 三合一黑白激光机（A4）最大设备连接数量",top_k=5)

    print(doc)



#     markdown_content="""
# # D 14 2023款 
# ## 屏幕
# 屏幕色彩	100% sRGB（典型值）
# 屏幕类型	IPS
# 屏幕尺寸	14英寸
# 屏幕比例	16:10
# 屏占比	90%
# 屏幕分辨率	1920×1200
# 屏幕刷新率	60Hz
# 屏幕可视角度	178度（典型值）
# 屏幕像素密度PPI	161
# 屏幕对比度	1200:1（典型值）
# 整机亮度	300尼特（典型值）
# 屏幕色深	8bit
# 护眼模式	支持（德国莱茵低蓝光护眼认证）
# 窄边框	3.5mm（左右）/6.5mm（上）/10.4mm（下）
# 触摸屏硬件规格	不支持
# 环境光传感器	不支持


# ## 处理器/显卡/内存/硬盘
# 显卡	英特尔® 锐炬® Xe显卡
# CPU类型	第12代智能英特尔® 酷睿™ i5-1240P 处理器
# CPU核数	12核：4性能核+8能效核
# CPU频率	"性能核心：基频1.7GHz，最高频率4.4GHz；
# 效率内核：基频1.2GHz，最高频率3.3GHz；"
# CPU线程数	16线程
# 运行内存容量/频率	16GB / 4266MHz
# 运行内存类型	LPDDR4X
# 运行内存形态（RAM）	板载内存
# 运行内存通道（RAM）	双通道
# 硬盘类型/容量	SSD固态/512GB
# SSD接口理论传输速率	PCIE3.0×4：32Gbps
# SSD协议/形态	NVMe / M.2 2280
# 扩容	内存、硬盘、显卡均不支持扩容


# ## 网络连接
# WIFI	WIFI6
# 有线网口	不支持
# WLAN协议	IEEE 802.11a/b/g/n/ac/ax，160MHz
# WLAN频段	2.4GHz和5GHz
# WLAN理论速率	2.4Gbps（最高速率）
# WLAN加密方式	支持WPA/WPA2/WPA3
# 蓝牙协议	蓝牙5.1

# ## 接口
# USB连接接口	"左侧（第1个）USB-C接口，支持数据（USB3.2 Gen1）、对外供电10W(5V2A)和显示；
# 左侧（第2个）USB-A接口，支持数据（USB3.2 Gen1）和对外供电10W(5V2A)；
# 右侧（第1个）USB-A接口，支持数据（USB2.0）和对外供电7.5W(5V1.5A)；"
# 雷电接口	不支持
# 显示接口(HDMI/DP/VGA)	HDMI1.4b × 1
# 音频接口	3.5mm耳机、麦克风二合一接口×1

# ## 多媒体
# 扬声器数量	2个
# 扬声器音效	HUAWEI Histen
# 扬声器功率	2W × 2（额定功率）
# 麦克风	2个
# 摄像头类型	前置摄像头
# 摄像头像素	100万
# 摄像头开关键	不支持
# 摄像头指示灯	支持
# 摄像头闪光灯	不支持
# 摄像头红外功能	不支持
# 摄像头录像/视频聊天	支持
# 摄像头人脸识别功能	不支持


# ## 传感器
# 霍尔传感器	支持
# 重力传感器	不支持
# 陀螺仪	不支持
# 其他传感器	不支持


# ## 输入设备
# 指纹器件硬件规格	支持
# 触控板硬件规格	支持5点触控（Windows 11 当前仅支持四点手势识别)
# Touchpad触控板盖板材质	麦拉
# 触控板尺寸	119.2mm × 71.4mm（长×宽）
# 电源键	指纹电源键
# 指取设备类型	触摸板
# 键盘类型	全尺寸键盘
# 键盘背光	支持
# 键盘防泼溅	不支持
# 键程	1.5mm
# 数字小键盘	不支持

# ## 系统/软件
# 操作系统	Windows 11 64位 家庭中文版
# 一碰传功能	支持
# 华为电脑管家	支持
# 默认浏览器	微软Edge默认浏览器
# 本地升级	通过U盘升级
# 支持系统恢复	支持
# 在线升级	"支持采用微软Windows Update升级方案进行在线升级；
# 支持HUAWEI MateBook管家驱动升级。"
# 特色应用	华为电脑管家、显示管理（护眼模式）、华为F10一键还原、高能模式（热键Fn+P切换）
# 第三方应用	支持第三方应用程序的安装和卸载，第三方应用遵循地区定制策略；内置Office 家庭和学生版2021版本
# 输入法	微软输入法

# ## 电源适配器

# 适配器规格	"65W USB-C电源适配器（标配）
# 输入：100V～240V AC，50Hz/60Hz
# 输出：5V/2A；9V/2A；12V/2A；15V/3A；20V/3.25A
# 重量：约213克
# (适配器本体含线缆)"
# 电池容量	56Wh（额定容量）（7330mAh@7.64V）
# 电池类型	锂聚合物
# 电池芯数	4芯
# 电池可更换	不支持
# 理论充电时间	"30分钟充电约40%，60分钟充电约80%，100分钟充满，基于65W适配器
# 备注：1）上述数据为使用标配适配器灭屏充电的实验室数据，实际充电时间，视使用情况而有所不同。
# 2）测试条件：使用标配的专用充电器，系统保持关机状态充电。"
# 充电指示灯	支持（白色闪烁代表充电，白色常亮代表充满）
# 电源指示灯	不支持
# 续航时间	"本地1080P视频播放约11小时
# 备注：实验室条件测试，150尼特亮度条件下，本地1080P视频播放，不同配置的播放时间会有差异。"


# ## 机身
# 机身尺寸	314.5mm × 227.79mm × 15.9mm（长×宽×高）
# 机身重量	约1.39kg（含电池）
# 机身材质	铝合金(A/C/D为铝合金,B面为Bezel)
# 翻转角度	约180度
# 单手开合	不支持
# 风扇	风扇×1

# ## 包装
# 包装尺寸	473mm × 280mm × 68mm（长×宽×高）
# 带包装重量	约2.2kg
# 包装清单	"笔记本 X 1
# USB-C电源适配器 X 1（含线缆）
# 快速入门 X 1
# 保修卡 X 1
# （备注：最终以实物为准）"

# ## 认证

# 中国能效等级认证要求	1级能效
# Evo认证	不支持

# ## 工作/存储环境
# 整机充放电温度范围	0°C~ 40°C（32°F～104°F）
# 产品工作环境湿度	5%～95%，非凝结
# 产品存储温度	-10°C ~ 45°C（14℉～113℉）


# ## 售后保修

# 保修期限	"主机 2年
# 电池 1年
# 主要部件：主板、CPU、内存、显示器、硬盘、键盘、电源适配器（含线）2年

# 预置Windows系统（部分机型预置Linux系统）含BIOS、驱动和预置的华为应用软件 1年"
# 服务	"1、快速响应：官方客服热线（950800）7*24小时人工语音，实时服务
# 2、全国联保：1500+华为授权服务中心，遍布全国300+城市（不含港澳台）
# 3、便捷寄修：提供双向免费寄修服务，足不出户完成维修（打950800或者微信小程序，联系在线客服，反馈问题和提供取件信息，客服安排上门取件）"
#     """
#     db.add_product_index(excel_id=1,filename="xxx.xlsx",nc_code="D10001",markdown_content=markdown_content)

#     # products=db.get_product_index(excel_id=1,nc_code="D10001")
#     # print(products)

#     rst=db.similarity_search_with_score_titile(nc_code="D10001",query="屏幕比例",top_k=2)
#     print(rst)

#     db.del_products_index(excel_id=1)

