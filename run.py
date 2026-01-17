#!/usr/bin/env python3
"""
运行脚本 - 解决导入路径问题
"""
import os
import sys

# 设置环境变量
os.environ.setdefault('PYTHONPATH', os.path.dirname(os.path.abspath(__file__)))

# 添加src目录到路径
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_dir)

# 现在运行主程序
if __name__ == '__main__':
    from main import main
    main()
