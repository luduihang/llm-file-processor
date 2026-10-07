"""T-007/T-008: CLI 单元测试（真 Processor + FakeProvider，零网络）。"""

import pytest

from llm_processor import LLMFileProcessor
from llm_processor.cli import build_processor, main
from llm_processor.providers import ProviderError


class FakeProvider:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def generate(self, messages):
        self.calls.append(messages)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def make_processor(outcomes):
    # retries=0：CLI 测试不关心重试（T-005 已覆盖），失败文件只消耗 1 次调用
    return LLMFileProcessor(FakeProvider(outcomes), retries=0, backoff_base=0)


def setup_case(tmp_path, files=("a.txt", "b.txt"), prompt_text="处理: {{ content }}"):
    for name in files:
        (tmp_path / name).write_text(f"内容{name}", encoding="utf-8")
    prompt = tmp_path / "prompts" / "p.md"
    prompt.parent.mkdir(exist_ok=True)
    prompt.write_text(prompt_text, encoding="utf-8")
    return prompt


def test_single_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    prompt = setup_case(tmp_path)
    rc = main(
        ["--input", str(tmp_path / "a.txt"), "--output", str(tmp_path / "o.md"),
         "--prompt", str(prompt)],
        processor=make_processor(["ok"]),
    )
    assert rc == 0
    assert (tmp_path / "o.md").read_text(encoding="utf-8") == "ok"


def test_single_provider_error_exit1(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    prompt = setup_case(tmp_path)
    rc = main(
        ["--input", str(tmp_path / "a.txt"), "--output", str(tmp_path / "o.md"),
         "--prompt", str(prompt)],
        processor=make_processor([ProviderError("boom")]),
    )
    assert rc == 1
    assert not (tmp_path / "o.md").exists()


def test_single_missing_input_exit2(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    prompt = setup_case(tmp_path)
    rc = main(
        ["--input", str(tmp_path / "nope.txt"), "--output", str(tmp_path / "o.md"),
         "--prompt", str(prompt)],
        processor=make_processor(["ok"]),
    )
    assert rc == 2


def test_input_without_output_exit2(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    prompt = setup_case(tmp_path)
    rc = main(["--input", str(tmp_path / "a.txt"), "--prompt", str(prompt)],
              processor=make_processor(["ok"]))
    assert rc == 2


def test_requires_input_or_input_dir():
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


def test_batch_mixed_failure_and_naming(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    prompt = setup_case(tmp_path, files=("BV1aaa-甲.txt", "BV1bbb-乙.txt"))
    out_dir = tmp_path / "out"
    # 排序后 BV1aaa 先失败，BV1bbb 成功
    p = make_processor([ProviderError("boom"), "ok-b"])
    rc = main(
        ["--input-dir", str(tmp_path), "--output-dir", str(out_dir),
         "--prompt", str(prompt)],
        processor=p,
    )
    assert rc == 1
    assert (out_dir / "BV1bbb-乙.md").read_text(encoding="utf-8") == "ok-b"
    assert not (out_dir / "BV1aaa-甲.md").exists()
    out = capsys.readouterr().out
    assert "1 processed" in out
    assert "0 skipped" in out
    assert "1 failed" in out
    assert "BV1aaa-甲.txt" in out  # 失败清单


def test_batch_ext_option(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    prompt = setup_case(tmp_path, files=("a.txt",))
    out_dir = tmp_path / "out"
    rc = main(
        ["--input-dir", str(tmp_path), "--output-dir", str(out_dir),
         "--prompt", str(prompt), "--ext", "txt"],
        processor=make_processor(["ok"]),
    )
    assert rc == 0
    assert (out_dir / "a.txt").read_text(encoding="utf-8") == "ok"


def test_batch_skips_existing_on_rerun(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    prompt = setup_case(tmp_path, files=("a.txt",))
    out_dir = tmp_path / "out"
    args = ["--input-dir", str(tmp_path), "--output-dir", str(out_dir),
            "--prompt", str(prompt)]
    assert main(args, processor=make_processor(["ok-1"])) == 0
    # 重跑：输出已存在 → skip，不再调用模型
    p = make_processor([])
    assert main(args, processor=p) == 0
    assert p.provider.calls == []
    assert (out_dir / "a.md").read_text(encoding="utf-8") == "ok-1"


def test_batch_template_error_aborts(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    prompt = setup_case(tmp_path, files=("a.txt", "b.txt"), prompt_text="{{ missing }}")
    out_dir = tmp_path / "out"
    p = make_processor(["never"])
    rc = main(
        ["--input-dir", str(tmp_path), "--output-dir", str(out_dir),
         "--prompt", str(prompt)],
        processor=p,
    )
    assert rc == 1
    assert list(out_dir.iterdir()) == []  # 一个都没写
    assert "中止" in capsys.readouterr().err


def test_batch_empty_dir_exit2(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    prompt = setup_case(tmp_path, files=())
    empty = tmp_path / "empty"
    empty.mkdir()
    rc = main(
        ["--input-dir", str(empty), "--output-dir", str(tmp_path / "out"),
         "--prompt", str(prompt)],
        processor=make_processor(["ok"]),
    )
    assert rc == 2


def test_build_processor_from_config_file(tmp_path):
    env = tmp_path / "qwen.env"
    env.write_text(
        "LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1\n"
        "LLM_API_KEY=sk-test\n"
        "LLM_MODEL=qwen-max\n"
        "LLM_RETRIES=5\n",
        encoding="utf-8",
    )
    p = build_processor(env)
    assert isinstance(p, LLMFileProcessor)
    assert p.provider.config.model == "qwen-max"
    assert p.provider.config.api_key == "sk-test"
    assert p.retries == 5
