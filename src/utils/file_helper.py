import json
import os
import shutil
import zipfile
from datetime import datetime
from os.path import join
from pathlib import Path

import pyzipper

from src.api.customer_exception import ValidationException
from src.utils.log_helper import logger


class FileHelper:
    """
    文件处理工具类
    move_file：将文件重命名（加上时间戳）并移动到指定目录, 返回日志文件名和目标文件路径
    """

    @classmethod
    def move_file(cls, file_path: str, file_name: str, save_path: str = None):
        """
        将文件重命名（加上时间戳）并移动到指定目录, 返回日志文件名和目标文件路径；
        save_path如果不指定，则默认保存到源文件所在目录的同级目录下，并以源文件名_log作为日志文件目录名；
        """
        error_msg = None
        is_success = False
        log_file_name = None
        target_file_path = None
        try:
            source_file_path = join(file_path, file_name)
            if os.path.exists(source_file_path) is False:
                raise ValidationException("源文件不存在")
            file_ext = Path(file_name).suffix
            file_name_without_ext = Path(file_name).stem
            if save_path is not None and len(save_path) > 0:
                file_path_log = save_path if save_path.endswith('/') else save_path + '/'
            else:
                file_path_log = join(file_path, f"{file_name_without_ext}_log/")
            if not os.path.exists(file_path_log):
                os.makedirs(file_path_log)
            log_file_name = f'{file_name_without_ext}[{datetime.now().strftime("%Y%m%d_%H%M%S%f")}]{file_ext}'
            target_file_path = join(file_path_log, log_file_name)
            shutil.move(join(file_path, file_name), target_file_path)
            is_success = True
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"移动文件【{file_name}】出错，原因：{str(e)},{traceback.format_exc()}")
            error_msg = f"移动文件失败：{e}"
        return is_success, error_msg, log_file_name, target_file_path

    @classmethod
    def delete_file(cls, file_path: str):
        print(f"删除文件【{file_path}】")
        if os.path.exists(file_path) is False:
            return
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"删除文件【{file_path}】出错，原因：{str(e)}")

    @classmethod
    def save_file(cls, save_path: str, file_name: str, file_content_dict: any):
        if save_path is None or len(save_path) == 0:
            save_path = f'./src/export/workflow/'
        os.makedirs(save_path, exist_ok=True)
        file_path = os.path.join(save_path, file_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(file_content_dict, f, ensure_ascii=False, indent=4)
        return file_path

    @classmethod
    def create_encrypted_zip(cls, file_paths: list[str], zip_path: str, password: str = '123456', delete_files=False):
        """
        创建加密压缩包
        :param file_paths:
        :param zip_path:
        :param password:
        :param delete_files:
        :return:
        """
        if password is not None and len(password) > 0:
            with pyzipper.AESZipFile(zip_path, 'w', compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES) as zf:
                zf.setpassword(password.encode())
                for file in file_paths.copy():
                    if file is None:
                        continue
                    file_name = os.path.basename(file)
                    zf.write(file, arcname=file_name)
        else:
            with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_LZMA) as zf:
                for file in file_paths.copy():
                    if file is None:
                        continue
                    file_name = os.path.basename(file)
                    zf.write(file, arcname=file_name)
        if delete_files:
            shutil.rmtree(zip_path.replace('.zip', ''))

    @classmethod
    def extract_encrypted_zip(cls, zip_path: str, password: str = '123456', extract_path: str = None, delete_zip=False):
        """
        解压加密压缩包
        :param zip_path:
        :param password:
        :param extract_path:
        :param delete_zip:
        :return:
        """
        if extract_path is None:
            extract_path = os.path.dirname(zip_path)
        if password is not None and len(password) > 0:
            with pyzipper.AESZipFile(zip_path, 'r', encryption=pyzipper.WZ_AES) as zf:
                zf.setpassword(password.encode())
                zf.testzip()
                zf.extractall(path=extract_path)
                print(f'解压成功: {extract_path}')
        else:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.testzip()
                zf.extractall(path=extract_path)
                print(f'解压成功: {extract_path}')
        file_paths = [os.path.join(extract_path, file) for file in os.listdir(extract_path)]
        if delete_zip:
            cls.delete_file(zip_path)
        return file_paths


"""以下是测试代码"""


def file_helper_test():
    file_helper = FileHelper.move_file(
        file_path=f'./src/upload_field/file_database/1001_16/',
        file_name='华为台式机一体机8.6修改一体机上市时间.xlsx'
    )
    print(file_helper)


def file_helper_test2():
    path = f'./src/upload_field/file_database/1001_16/华为台式机一体机8.6修改一体机上市时间.xlsx'
    # 获取path中的除了文件名的目录
    parent_path = os.path.dirname(path)
    # 将tuple转换为地址字符串
    parent_path1 = './{0}'.format('/'.join(Path(path).parent.parts))

    # 获取文件名
    file_name = os.path.basename(path)
    file_name1 = Path(path).name
    # 获取文件名的后缀名
    file_ext = os.path.splitext(file_name)[1]
    file_ext1 = Path(file_name).suffix
    file_ext2 = Path(path).suffix
    # 获取文件名的不带后缀名
    file_name_without_ext = os.path.splitext(file_name)[0]
    file_name_without_ext1 = Path(file_name).stem
    print('\n----------')
    print(parent_path, file_name, file_ext, file_name_without_ext)
    print('-----------------------------')
    print(parent_path1, file_name1, file_ext1, file_ext2, file_name_without_ext1)


if __name__ == '__main__':
    # file_helper_test()
    file_helper_test2()
