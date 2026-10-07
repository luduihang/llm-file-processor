"""T-005: LLMFileProcessor.process 单元测试（FakeProvider，零网络）。"""

import pytest

from llm_processor import LLMFileProcessor
from llm_processor.processor import ProcessStatus
from llm_processor.providers import ProviderError
from llm_processor.templates import TemplateError


class FakeProvider:
    """测试替身：按序弹出 outcomes（str=返回，Exception=抛出）。"""

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def generate(self, messages):
        self.calls.append(messages)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


PROMPT = (
    "任务：整理下面的文本\n\n"
    "文件名：{{ filename }}\n"
    "stem：{{ stem }}\n"
    "路径：{{ input_path }}\n\n"
    "内容：\n{{ content }}"
)


def make_case(tmp_path, input_text="hello world"):
    inp = tmp_path / "BV1xx-title.txt"
    inp.write_text(input_text, encoding="utf-8")
    prompt = tmp_path / "study_note.md"
    prompt.write_text(PROMPT, encoding="utf-8")
    out = tmp_path / "out" / "BV1xx-title.md"
    return inp, prompt, out


def test_process_success(tmp_path):
    inp, prompt, out = make_case(tmp_path)
    provider = FakeProvider(["# 笔记\n\nhello world"])
    processor = LLMFileProcessor(provider, backoff_base=0)
    status = processor.process(inp, out, prompt)
    assert status == ProcessStatus.PROCESSED
    assert out.read_text(encoding="utf-8") == "# 笔记\n\nhello world"
    # 内置变量已渲染进发给模型的文本
    sent = provider.calls[0][0]["content"]
    assert "BV1xx-title.txt" in sent
    assert "BV1xx-title\n" in sent
    assert str(inp) in sent
    assert "hello world" in sent


def test_process_injects_caller_variables(tmp_path):
    inp, prompt, out = make_case(tmp_path)
    prompt.write_text("{{ bvid }}: {{ content }}", encoding="utf-8")
    provider = FakeProvider(["ok"])
    processor = LLMFileProcessor(provider, backoff_base=0)
    processor.process(inp, out, prompt, variables={"bvid": "BV1xx"})
    assert provider.calls[0][0]["content"] == "BV1xx: hello world"


def test_process_skips_existing(tmp_path):
    inp, prompt, out = make_case(tmp_path)
    out.parent.mkdir(parents=True)
    out.write_text("old", encoding="utf-8")
    provider = FakeProvider(["new"])
    processor = LLMFileProcessor(provider, backoff_base=0)
    assert processor.process(inp, out, prompt) == ProcessStatus.SKIPPED
    assert provider.calls == []
    assert out.read_text(encoding="utf-8") == "old"


def test_process_force_overwrites(tmp_path):
    inp, prompt, out = make_case(tmp_path)
    out.parent.mkdir(parents=True)
    out.write_text("old", encoding="utf-8")
    provider = FakeProvider(["new"])
    processor = LLMFileProcessor(provider, backoff_base=0)
    assert processor.process(inp, out, prompt, force=True) == ProcessStatus.PROCESSED
    assert len(provider.calls) == 1
    assert out.read_text(encoding="utf-8") == "new"


def test_process_template_error_raises_no_output(tmp_path):
    inp, prompt, out = make_case(tmp_path)
    prompt.write_text("{{ missing_var }}", encoding="utf-8")
    provider = FakeProvider(["ok"])
    processor = LLMFileProcessor(provider, backoff_base=0)
    with pytest.raises(TemplateError):
        processor.process(inp, out, prompt)
    assert not out.exists()


def test_process_retries_then_succeeds(tmp_path):
    inp, prompt, out = make_case(tmp_path)
    provider = FakeProvider([ProviderError("e1"), ProviderError("e2"), "ok"])
    processor = LLMFileProcessor(provider, retries=3, backoff_base=0)
    assert processor.process(inp, out, prompt) == ProcessStatus.PROCESSED
    assert len(provider.calls) == 3
    assert out.read_text(encoding="utf-8") == "ok"


def test_process_retries_exhausted_raises_no_output(tmp_path):
    inp, prompt, out = make_case(tmp_path)
    provider = FakeProvider([ProviderError(f"e{i}") for i in range(4)])
    processor = LLMFileProcessor(provider, retries=3, backoff_base=0)
    with pytest.raises(ProviderError):
        processor.process(inp, out, prompt)
    assert len(provider.calls) == 4  # 1 次初始 + 3 次重试
    assert not out.exists()
