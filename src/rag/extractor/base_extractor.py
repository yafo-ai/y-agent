
from abc import ABC, abstractmethod

class BaseExtractor(ABC):
    """文件提取器接口"""

    @abstractmethod
    def extract(self):
        raise NotImplementedError