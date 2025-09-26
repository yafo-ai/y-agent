import base64
import mimetypes
import os
from pathlib import Path
from typing import Generator, Union


class FileManager:
    """本地文件存储实现，将文件保存到项目指定目录"""
    
    def __init__(self, base_path: Union[str, Path]):
        """
        初始化本地存储
        
        Args:
            base_path: 存储文件的基础目录路径
        """
        self.base_path = Path(base_path).resolve()
        # 确保基础目录存在
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_full_path(self, filename: str) -> Path:
        """获取文件的完整路径，并进行安全校验"""
        # 规范化路径，防止目录遍历攻击
        full_path = (self.base_path / filename).resolve()
        
        # 确保路径在基础目录内
        if not str(full_path).startswith(str(self.base_path)):
            raise ValueError(f"文件路径 {filename} 试图访问基础目录外的位置")
            
        return full_path
    
    def save(self, filename: str, data: Union[bytes, str]) -> None:
        """保存数据到文件"""
        full_path = self._get_full_path(filename)
        
        # 确保目录存在
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入数据
        if isinstance(data, str):
            full_path.write_text(data, encoding='utf-8')
        else:
            full_path.write_bytes(data)

    
    def load_once(self, filename: str) -> bytes:
        """一次性加载整个文件内容"""
        full_path = self._get_full_path(filename)
        return full_path.read_bytes()
    
    def load_stream(self, filename: str, chunk_size: int = 8192) -> Generator[bytes, None, None]:
        """流式加载文件内容"""
        full_path = self._get_full_path(filename)
        
        with open(full_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
       
    def exists(self, filename: str) -> bool:
        """检查文件是否存在"""
        full_path = self._get_full_path(filename)
        return full_path.exists()
    
    def delete(self, filename: str) -> None:
        """删除文件"""
        full_path = self._get_full_path(filename)
        if full_path.exists():
            full_path.unlink()
    
    def scan(self, path: str = "", files: bool = True, directories: bool = False) -> list[str]:
        """扫描目录中的文件和文件夹"""
        scan_path = self._get_full_path(path)
        
        if not scan_path.exists():
            return []
        
        result = []
        for item in scan_path.iterdir():
            # 根据参数决定是否包含文件或目录
            if item.is_file() and files:
                # 返回相对于基础路径的相对路径
                rel_path = item.relative_to(self.base_path)
                result.append(str(rel_path))
            elif item.is_dir() and directories:
                rel_path = item.relative_to(self.base_path)
                result.append(str(rel_path))
        
        return result
