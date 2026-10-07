"""T-004: OpenAICompatibleProvider 单元测试（mock transport，零网络）。"""

import json

import httpx2
import pytest
from openai import OpenAI

from llm_processor.config import ProviderConfig
from llm_processor.providers import OpenAICompatibleProvider, ProviderError

OK_BODY = {
    "id": "chatcmpl-1",
    "object": "chat.completion",
    "created": 1,
    "model": "test-model",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "Hello from model"},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
}


def make_config(**kw) -> ProviderConfig:
    base = dict(
        base_url="https://api.example.com/v1",
        api_key="sk-test",
        model="test-model",
    )
    base.update(kw)
    return ProviderConfig(**base)


def make_provider(handler) -> OpenAICompatibleProvider:
    """注入 httpx2.MockTransport 的 provider（零网络）。"""
    client = OpenAI(
        base_url="https://api.example.com/v1",
        api_key="sk-test",
        max_retries=0,  # 重试归 processor 层，SDK 层不重试
        http_client=httpx2.Client(transport=httpx2.MockTransport(handler)),
    )
    return OpenAICompatibleProvider(make_config(), client=client)


def test_generate_returns_content():
    provider = make_provider(lambda r: httpx2.Response(200, json=OK_BODY))
    assert provider.generate([{"role": "user", "content": "hi"}]) == "Hello from model"


def test_request_body_matches_config():
    captured = []

    def handler(request):
        captured.append(json.loads(request.content))
        return httpx2.Response(200, json=OK_BODY)

    provider = make_provider(handler)
    provider.generate([{"role": "user", "content": "hi"}])

    body = captured[0]
    assert body["model"] == "test-model"
    assert body["messages"] == [{"role": "user", "content": "hi"}]
    assert body["temperature"] == 0.7
    assert body["max_tokens"] == 4096


def test_api_error_raises_provider_error():
    provider = make_provider(
        lambda r: httpx2.Response(
            500, json={"error": {"message": "boom", "type": "server_error"}}
        )
    )
    with pytest.raises(ProviderError):
        provider.generate([{"role": "user", "content": "hi"}])


def test_extra_body_passed_through():
    """config.extra_body 直通到请求体（vLLM chat_template_kwargs 场景）。"""
    captured = []

    def handler(request):
        captured.append(json.loads(request.content))
        return httpx2.Response(200, json=OK_BODY)

    client = OpenAI(
        base_url="https://api.example.com/v1",
        api_key="sk-test",
        max_retries=0,
        http_client=httpx2.Client(transport=httpx2.MockTransport(handler)),
    )
    provider = OpenAICompatibleProvider(
        make_config(extra_body={"chat_template_kwargs": {"enable_thinking": False}}),
        client=client,
    )
    provider.generate([{"role": "user", "content": "hi"}])

    assert captured[0]["chat_template_kwargs"] == {"enable_thinking": False}


def test_no_extra_body_by_default():
    captured = []

    def handler(request):
        captured.append(json.loads(request.content))
        return httpx2.Response(200, json=OK_BODY)

    make_provider(handler).generate([{"role": "user", "content": "hi"}])
    assert "chat_template_kwargs" not in captured[0]
