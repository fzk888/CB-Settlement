# -*- coding: utf-8 -*-
"""
Phase 1 集成测试脚本
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.main import main

if __name__ == '__main__':
    print("启动 Phase 1 集成测试...")
    main()
