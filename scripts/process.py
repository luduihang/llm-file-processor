#!/usr/bin/env python3
"""薄封装：等价于 llm-process 入口。

用法: python scripts/process.py --help
"""
import sys

from llm_processor.cli import main

if __name__ == "__main__":
    sys.exit(main())
