flow_file_out_path = './src/upload_field/flow_out/'
flow_file_in_path = './src/upload_field/flow_in/'
flow_zip_password = None


class FlowExportBaseParams:
    def __init__(self):
        """
        导出参数基类
        private_tools_name: 私有工具名称列表
        """
        self.private_tools_name = [
            'calculator',
            'flow_node_logs',
            'knowledge_append',
            'knowledge_add',
            'knowledge_retrieve',
            'product_retrieve',
            'train_case_add',
            'unit_test_add',
            'vectorstore_retrieve'
        ]
