from src.configs.system_config import system_config

from src.embedding.openai_embeddings import OpenAIEmbeddings
from src.embedding.vmll_embeddings import VmllEmbeddings
from src.embedding.xinference import XinferenceEmbeddings


class EmbeddingsFactory:

    @staticmethod
    def get_embeddings():
        sys_embedding = system_config.sys_db_embedding  # SystemConfigEmbedding().load_db_config()
        if sys_embedding.selected_provider_name == 'openai':
            return OpenAIEmbeddings(f"{sys_embedding.selected_url}", sys_embedding.selected_model_name, sys_embedding.selected_api_key)
        if sys_embedding.selected_provider_name == 'vllm':
            return VmllEmbeddings(f"{sys_embedding.selected_url}", sys_embedding.selected_model_name, sys_embedding.selected_api_key)
        if sys_embedding.selected_provider_name == 'xinference':
            return XinferenceEmbeddings(f"{sys_embedding.selected_url}", sys_embedding.selected_model_name, sys_embedding.selected_api_key)


# 使用工厂类获取嵌入模型实例
embedding_mode = EmbeddingsFactory.get_embeddings()
