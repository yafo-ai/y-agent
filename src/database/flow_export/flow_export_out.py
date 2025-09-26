import json
import os
import uuid

from src.database.flow_export.flow_models import flow_file_out_path, flow_zip_password
from src.database.models import WorkFlow
from src.utils.file_helper import FileHelper
from src.database.flow_export.flow_export_out_params import WorkFlowOutParams


class WorkFlowExportOut:
    """
    流程导出
    params: 导出参数
    dir_name: 导出目录名称
    file_path: 导出目录路径
    zip_path: 导出zip文件路径

    依次导出：提示词、插件工具、mcp工具、流程、流程顺序，然后打包成zip文件，并返回zip文件路径。

    ge: WorkFlowExportOut(12).export_out()

    """

    def __init__(self, flow_id: int):
        """
        流程id
        :param flow_id:
        """
        self.flow_id = flow_id
        self.params = WorkFlowOutParams(self.flow_id)
        self.dir_name = f'{WorkFlow.get(flow_id).name}_{uuid.uuid4().hex}'
        self.file_path = os.path.join(flow_file_out_path, self.dir_name)
        self.zip_path = os.path.join(flow_file_out_path, f'{self.dir_name}.zip')

    def export_out(self):
        """
        导出最终zip文件
        :return: zip路径
        """
        prompt_path = self._out_prompt()
        plugin_tools_path = self._out_plugin_tools()
        mcp_tools_path = self._out_mcp_tools()
        flow_path = self._out_flow()
        flow_sequence_path = self._out_flow_sequence()
        file_paths = [prompt_path, plugin_tools_path, mcp_tools_path, flow_path, flow_sequence_path]
        FileHelper.create_encrypted_zip(file_paths, self.zip_path, password=flow_zip_password, delete_files=True)
        return self.zip_path

    # region 导出 out 相关

    def _out_prompt(self):
        """
        导出提示词
        :return: 提示词文件路径
        """
        if len(self.params.prompts) == 0:
            return None
        file_name = 'prompt.json'
        result = []
        for prompt in self.params.prompts:
            result.append({
                'id': prompt.id,
                'unique_code': prompt.unique_code,
                'name': prompt.name,
                'content': prompt.content,
                'prompt_type_id': prompt.prompt_type_id,
            })
        return FileHelper.save_file(self.file_path, file_name, result)

    def _out_plugin_tools(self):
        """
        导出插件工具
        :return: 插件工具文件路径
        """
        if len(self.params.plugin_tools) == 0:
            return None
        file_name = 'plugin_tools.json'
        result = []
        for tool in self.params.plugin_tools:
            in_params_dict = json.loads(tool.in_params) if tool.in_params is not None and tool.in_params != '' else []
            self._in_params_clear_value(in_params_dict)
            result.append({
                'id': tool.id,
                'name': tool.name,
                'caption': tool.caption,
                'description': tool.caption,
                'unique_code': tool.unique_code,
                'func_name': tool.func_name,
                'in_params': in_params_dict,
                'out_params': json.loads(tool.out_params) if tool.out_params is not None and tool.out_params != '' else [],
                'api_url': None,
                'is_enable': tool.is_enable,
            })
        return FileHelper.save_file(self.file_path, file_name, result)

    @classmethod
    def _in_params_clear_value(cls, in_params_list: list[dict]):
        """
        移除插件默认值
        :param in_params_list:
        :return:
        """
        for item in in_params_list:
            item['default_value'] = ''
            if item['children'] is None or len(item['children']) == 0:
                continue
            cls._in_params_clear_value(item['children'])

    def _out_mcp_tools(self):
        """
        导出mcp工具
        :return: mcp 文件路径
        """
        if len(self.params.mcp_tools) == 0:
            return None
        file_name = 'mcp_tools.json'
        result = []
        for tool in self.params.mcp_tools:
            tmp_mcp_tool = {
                'id': tool.id,
                'name': tool.name,
                'caption': tool.caption,
                'description': tool.caption,
                'unique_code': tool.unique_code,
                'server_identifier': tool.server_identifier,
                'server_url': tool.server_url,
                'server_url_hash': tool.server_url_hash,
                'encrypted_credentials': tool.encrypted_credentials,
                'authed': None,
                'tools': tool.tools,
                'selected_tools': tool.selected_tools,
                'timeout': tool.timeout,
                'sse_read_timeout': tool.sse_read_timeout,
                'encrypted_headers': None,
                'tools_map': {},
                'tools_nams': []
            }
            for tool_name_item in json.loads(tool.tools) if tool.tools is not None and tool.tools != '' else []:
                tmp_mcp_tool['tools_map'].update({f'{tool.id}_{tool_name_item.get("name", "")}': tool.id})
                if tool_name_item.get("name", "") not in tmp_mcp_tool['tools_nams']:
                    tmp_mcp_tool['tools_nams'].append(tool_name_item.get("name", ""))

            result.append(tmp_mcp_tool)
        return FileHelper.save_file(self.file_path, file_name, result)

    def _out_flow(self):
        """
        导出流程
        :return: 流程文件路径
        """
        if len(self.params.flows) == 0:
            return None
        file_name = 'flow.json'
        result = []
        for flow in self.params.flows:
            result.append({
                'id': flow.id,
                'name': flow.name,
                'caption': flow.caption,
                'view_json': flow.view_json,
                'data_json': flow.data_json,
                'is_share': flow.is_share,
                'is_tool': flow.is_tool,
                'use_log': flow.use_log,
                'unique_code': flow.unique_code,
            })
        return FileHelper.save_file(self.file_path, file_name, result)

    def _out_flow_sequence(self):
        """
        导出流程顺序，用于导入时候，确定流程的导入顺序
        :return:
        """
        file_name = 'flow_sequence.json'
        return FileHelper.save_file(self.file_path, file_name, self.params.flow_ids)
    # endregion


if __name__ == '__main__':
    print(WorkFlowExportOut(12).export_out())
    # WorkFlowImportIn('./src/export/workflow/51_596cd0201e174486b92d82004e13f8c5 - 副本.zip')
