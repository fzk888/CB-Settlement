# -*- coding: utf-8 -*-
"""
CSV解析器基类
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models import ParseResult


class BaseParser(ABC):
    """CSV解析器基类"""
    
    def __init__(self):
        self.encoding = 'utf-8-sig'
    
    @abstractmethod
    def parse(self, file_path: str) -> ParseResult:
        """解析CSV文件"""
        pass
    
    @abstractmethod
    def detect_header_row(self, content: str) -> Optional[int]:
        """检测表头行位置"""
        pass
    
    def get_platform(self) -> str:
        """获取平台标识"""
        return "unknown"
