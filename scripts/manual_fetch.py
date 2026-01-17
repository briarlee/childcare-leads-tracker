#!/usr/bin/env python3
"""
手动运行脚本
用于手动触发商机追踪系统
"""

import os
import sys
from pathlib import Path

# 切换到src目录
src_path = Path(__file__).parent.parent / 'src'
os.chdir(src_path)
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv(Path(__file__).parent.parent / '.env')

# 运行主程序
from main import main

if __name__ == '__main__':
    main()
