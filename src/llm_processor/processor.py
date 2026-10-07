"""原子处理器：单文件进 → 单文件出。

处理器不知道批量、B站、八字、玉成的存在。
流程：读输入 → 渲染模板 → 调模型（带重试）→ 原子写输出。
"""

from __future__ import annotations

import time
from enum import Enum
from pathlib import Path
from typing import Optional, Union

from . import templates
from .providers import ProviderError

PathLike = Union[str, Path]


class ProcessStatus(str, Enum):
    PROCESSED = "processed"
    SKIPPED = "skipped"


class LLMFileProcessor:
    """原子处理单元。

    retries：ProviderError 时最多重试次数（不含首次调用）。
    backoff_base：指数退避基数秒（实际等待 base * 2**(n-1)）；测试传 0。
    """

    def __init__(self, provider, retries: int = 3, backoff_base: float = 2.0):
        self.provider = provider
        self.retries = retries
        self.backoff_base = backoff_base

    def process(
        self,
        input_path: PathLike,
        output_path: PathLike,
        prompt_path: PathLike,
        variables: Optional[dict] = None,
        force: bool = False,
    ) -> ProcessStatus:
        """处理单个文件。

        内置变量 content/filename/stem/input_path 自动注入；
        调用方 variables 可追加（如 bvid/title），同名时覆盖内置。
        输出已存在且 force=False → 跳过（SKIPPED）。
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        prompt_path = Path(prompt_path)

        if output_path.exists() and not force:
            return ProcessStatus.SKIPPED

        content = input_path.read_text(encoding="utf-8")
        prompt_template = prompt_path.read_text(encoding="utf-8")

        merged = {
            "content": content,
            "filename": input_path.name,
            "stem": input_path.stem,
            "input_path": str(input_path),
            **(variables or {}),
        }
        rendered = templates.render(prompt_template, merged)
        messages = [{"role": "user", "content": rendered}]

        result = self._generate_with_retry(messages)
        self._atomic_write(output_path, result)
        return ProcessStatus.PROCESSED

    def _generate_with_retry(self, messages) -> str:
        attempt = 0
        while True:
            try:
                return self.provider.generate(messages)
            except ProviderError:
                attempt += 1
                if attempt > self.retries:
                    raise
                if self.backoff_base > 0:
                    time.sleep(self.backoff_base * (2 ** (attempt - 1)))

    @staticmethod
    def _atomic_write(path: Path, text: str) -> None:
        """tmp + rename，避免中途失败留下半截输出。"""
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)
