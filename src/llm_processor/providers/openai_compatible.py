"""OpenAI 兼容 Provider：覆盖 OpenAI / DeepSeek / Qwen / 硅基流动 / 火山 / vLLM / Ollama。"""

from __future__ import annotations

from typing import List, Optional

from openai import OpenAI

from ..config import ProviderConfig


class ProviderError(RuntimeError):
    """模型调用失败（API 错误 / 超时）。重试由 processor 层负责，这里不重试。"""


class OpenAICompatibleProvider:
    """统一 generate(messages) -> str 接口。

    client 参数用于测试注入（httpx.MockTransport）；生产环境为 None，
    按 config 自建。max_retries=0：重试归 processor 层，避免双重重试。
    """

    def __init__(self, config: ProviderConfig, client: Optional[OpenAI] = None):
        self.config = config
        self._client = client or OpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
            max_retries=0,
            timeout=config.timeout,
        )

    def generate(self, messages: List[dict]) -> str:
        create_kwargs = dict(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        if self.config.extra_body:
            # 直通到请求体（如 vLLM 的 chat_template_kwargs.enable_thinking）
            create_kwargs["extra_body"] = self.config.extra_body
        try:
            resp = self._client.chat.completions.create(**create_kwargs)
        except Exception as exc:  # openai.APIError / 超时 / 连接错误
            raise ProviderError(f"模型调用失败: {exc}") from exc
        return resp.choices[0].message.content or ""
