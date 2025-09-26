import json
import os
import shutil

from src.api.customer_exception import ValidationException
from src.database.flow_export.flow_models import flow_zip_password
from src.database.models import WorkFlow, PromptModel, ToolModel, MCPToolProvider
from src.utils.file_helper import FileHelper
from src.database.flow_export.flow_export_in_params import WorkFlowImportInParams, replace_json_data


class WorkFlowExportIn:
    """
    导入工作流
    params 导入参数

    依次导入：解开压缩包，入库 提示词，插件，mcp信息，然后开始按顺序导入流程

    eg:
        export_out_path = f'./src/upload_field/flow_in/12_be40936c32904b3d8ad5da62d02d7b15.zip'
        export_in = WorkFlowExportIn(export_out_path)
        export_in.export_in()
        # 导入后，是否删除，可以调用
        export_in.delete_files()
    """

    def __init__(self, zip_file_path: str, default_llm_id: int = 0):
        """
        导入工作流
        :param zip_file_path: zip文件路径
        :param default_llm_id: 默认大模型id, 默认取数据库第一个
        """
        self.params = WorkFlowImportInParams(default_llm_id)
        if not os.path.exists(zip_file_path):
            raise ValidationException(f'{zip_file_path}文件不存在')
        self.zip_file_path = zip_file_path
        self.file_paths = self._extract_zip_file()

        # [{"target_id": None, "source_id": item.get('id')}]
        # target_id: 数据库中存在的id  source_id: 导入文件中的id
        self.flows_relations: list[dict[str, int]] = []
        self.plugin_tools_relations: list[dict[str, int]] = []
        self.mcp_tools_relations: list[dict[str, int]] = []
        self._init_db_data()

    def _init_db_data(self):
        """
        导入提示词，插件，mcp信息
        :return:
        """
        self._in_prompt()
        self._in_plugin_tools()
        self._in_mcp_tools()

    # 解压 zip 文件
    def _extract_zip_file(self):
        """
        解压 zip 文件
        :return:
        """
        extract_dir = os.path.basename(self.zip_file_path)
        extract_path = self.zip_file_path.replace('.zip', '')
        return FileHelper.extract_encrypted_zip(self.zip_file_path, password=flow_zip_password, extract_path=extract_path, delete_zip=True)

    # region 导入 in 相关
    def _in_prompt(self):
        """
        存储提示词对应关系
        :return:
        """
        file = next((file for file in self.file_paths if file.endswith('prompt.json')), None)
        if file is None:
            return
        with open(file, 'r', encoding='utf-8') as f:
            prompt_datas = json.load(f)
        db_datas = PromptModel.query.all()
        target_ids = []
        for item in prompt_datas:
            tmp_relation = {"target_id": None, "source_id": item.get('id')}
            current_data = next((pd for pd in db_datas if pd.unique_code == item.get('unique_code')), None)
            if current_data is None:
                model = PromptModel(unique_code=item.get('unique_code'), name=item.get('name'), content=item.get('content'))
                model.prompt_type_id = None
                model.add(True)
                tmp_relation['target_id'] = model.id
            else:
                tmp_relation['target_id'] = current_data.id
            if tmp_relation['target_id'] not in target_ids:
                target_ids.append(tmp_relation['target_id'])
                self.params.prompt_relations.append(tmp_relation)

    def _in_plugin_tools(self):
        """
        导入插件，存储插件对应关系，和，插件名称对应文件
        :return:
        """
        file = next((file for file in self.file_paths if file.endswith('plugin_tools.json')), None)
        if file is None:
            return
        with open(file, 'r', encoding='utf-8') as f:
            plugin_tools_datas = json.load(f)
        db_datas = ToolModel.query.all()
        target_ids = []
        for item in plugin_tools_datas:
            func_name = item.get('func_name')
            tmp_relation = {"target_id": None, "source_id": item.get('id')}
            current_data = next((pd for pd in db_datas if pd.unique_code == item.get('unique_code')), None)
            if current_data is None:
                model = ToolModel(unique_code=item.get('unique_code'), name=item.get('name'), caption=item.get('caption'), func_name=func_name)
                model.in_params = json.dumps(item.get('in_params'))
                model.out_params = json.dumps(item.get('out_params'))
                model.api_url = item.get('api_url')
                model.is_enable = item.get('is_enable')
                model.add(True)
                tmp_relation['target_id'] = model.id
            else:
                tmp_relation['target_id'] = current_data.id
                func_name = current_data.func_name
            if tmp_relation['target_id'] not in target_ids:
                target_ids.append(tmp_relation['target_id'])
                self.params.plugin_tools_relations.append(tmp_relation)
                if func_name not in self.params.plugin_tools_name:
                    self.params.plugin_tools_name.append({func_name: tmp_relation['target_id']})

    def _in_mcp_tools(self):
        file = next((file for file in self.file_paths if file.endswith('mcp_tools.json')), None)
        if file is None:
            return
        with open(file, 'r', encoding='utf-8') as f:
            mcp_tools_datas = json.load(f)
        db_datas = MCPToolProvider.query.all()
        target_ids = []
        for item in mcp_tools_datas:
            tmp_relation = {"target_id": None, "source_id": item.get('id')}
            current_data = next((pd for pd in db_datas if pd.unique_code == item.get('unique_code')), None)
            if current_data is None:
                model = MCPToolProvider(name=item.get('name'),
                                        unique_code=item.get('unique_code'),
                                        server_identifier=item.get('server_identifier'),
                                        server_url=item.get('server_url'),
                                        server_url_hash=item.get('server_url_hash'),
                                        caption=item.get('caption'),
                                        authed=item.get('authed'),
                                        tools=item.get('tools'),
                                        selected_tools=item.get('selected_tools'),
                                        timeout=item.get('timeout'),
                                        sse_read_timeout=item.get('sse_read_timeout'))
                model.add(True)
                tmp_relation['target_id'] = model.id
            else:
                tmp_relation['target_id'] = current_data.id
            if tmp_relation['target_id'] not in target_ids:
                target_ids.append(tmp_relation['target_id'])
                self.params.mcp_tools_relations.append(tmp_relation)

    # 导入
    def export_in(self):
        """
        导入
        :return:
        """
        file = next((file for file in self.file_paths if file.endswith('flow.json')), None)
        if file is None:
            return
        file_sequence = next((file for file in self.file_paths if file.endswith('flow_sequence.json')), None)
        if file_sequence is None:
            return
        with open(file, 'r', encoding='utf-8') as f:
            flow_datas = json.load(f)
        with open(file_sequence, 'r', encoding='utf-8') as f:
            flow_sequence_datas = json.load(f)
        db_datas = WorkFlow.query.all()

        target_ids = flow_sequence_datas.copy()

        for item in flow_sequence_datas:
            current_flow = next((fd for fd in flow_datas if fd.get('id') == item), None)
            if current_flow is None:
                continue
            if item not in target_ids:
                target_ids.append(item)
                self.params.flow_relations.append({"target_id": current_flow.id, "source_id": item})

        for item in flow_sequence_datas:
            current_flow = next((fd for fd in flow_datas if fd.get('id') == item), None)
            if current_flow is None:
                continue
            tmp_relation = {"target_id": None, "source_id": current_flow.get('id')}
            current_data = next((fd for fd in db_datas if fd.unique_code == current_flow.get('unique_code')), None)
            if current_data is None:
                # 需要执行替换 view_json 和 data_json 中的 数据 @@@@@@
                new_flow = WorkFlow()
                new_flow.unique_code = current_flow.get('unique_code')
                new_flow.name = current_flow.get('name')
                new_flow.caption = current_flow.get('caption')

                view_json_dict = json.loads(current_flow.get('view_json'))

                view_json_nodes_dict = view_json_dict.get('nodes')
                replace_json_data(view_json_nodes_dict, self.params)
                view_json_dict['nodes'] = view_json_nodes_dict

                view_json = json.dumps(view_json_dict)

                data_json = WorkFlow.get_date_json(view_json)

                new_flow.view_json = view_json
                new_flow.data_json = data_json
                new_flow.is_share = current_flow.get('is_share')
                new_flow.is_tool = current_flow.get('is_tool')
                new_flow.use_log = current_flow.get('use_log')
                new_flow.add(True)
                tmp_relation['target_id'] = new_flow.id
            else:
                tmp_relation['target_id'] = current_data.id
            if tmp_relation.get('target_id') not in target_ids:
                self.params.flow_relations.append(tmp_relation)

    # endregion

    def delete_files(self):
        """
        删除压缩文件和解压后的文件以及文件夹
        :return:
        """
        if os.path.exists(self.zip_file_path):
            FileHelper.delete_file(self.zip_file_path)
        if os.path.exists(self.zip_file_path.replace('.zip', '')):
            shutil.rmtree(self.zip_file_path.replace('.zip', ''))
