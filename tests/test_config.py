"""T-002: config.load_config 单元测试（TDD：先于实现）。"""

from pathlib import Path

import pytest

from llm_processor.config import ConfigError, load_config


def test_load_config_defaults(tmp_path, monkeypatch):
    """默认读当前目录 .env；可选字段缺省时用默认值。"""
    (tmp_path / ".env").write_text(
        "LLM_BASE_URL=https://api.example.com/v1\n"
        "LLM_API_KEY=sk-test\n"
        "LLM_MODEL=test-model\n"
    )
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert cfg.base_url == "https://api.example.com/v1"
    assert cfg.api_key == "sk-test"
    assert cfg.model == "test-model"
    assert cfg.temperature == 0.7
    assert cfg.max_tokens == 4096
    assert cfg.retries == 3


def test_load_config_custom_path(tmp_path):
    """path 指定具体 env 文件（如 configs/qwen.env），可选字段可覆盖默认值。"""
    cfg_file = tmp_path / "configs" / "qwen.env"
    cfg_file.parent.mkdir()
    cfg_file.write_text(
        "LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1\n"
        "LLM_API_KEY=sk-qwen\n"
        "LLM_MODEL=qwen-max\n"
        "LLM_TEMPERATURE=0.2\n"
        "LLM_MAX_TOKENS=8192\n"
        "LLM_RETRIES=5\n"
    )
    cfg = load_config(cfg_file)
    assert cfg.model == "qwen-max"
    assert cfg.temperature == 0.2
    assert cfg.max_tokens == 8192
    assert cfg.retries == 5


def test_missing_required_field_raises(tmp_path, monkeypatch):
    """缺必填字段 → ConfigError，错误信息含字段名和配置文件名。"""
    (tmp_path / ".env").write_text("LLM_BASE_URL=https://api.example.com/v1\n")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ConfigError) as exc:
        load_config()
    msg = str(exc.value)
    assert "LLM_API_KEY" in msg
    assert ".env" in msg


def test_env_file_not_found_raises(tmp_path, monkeypatch):
    """配置文件不存在 → ConfigError。"""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ConfigError) as exc:
        load_config()
    assert ".env" in str(exc.value)
