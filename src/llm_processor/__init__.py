"""llm-file-processor: 文件 → LLM → 文件。

文件是输入输出边界，Prompt 是业务逻辑，Provider 是模型能力，
Processor 只负责把三者连接起来。
"""

from .config import ProviderConfig
from .processor import LLMFileProcessor, ProcessStatus
from .providers import OpenAICompatibleProvider, ProviderError

__all__ = [
    "LLMFileProcessor",
    "ProcessStatus",
    "ProviderConfig",
    "OpenAICompatibleProvider",
    "ProviderError",
]
