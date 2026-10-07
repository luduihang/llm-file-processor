"""模型配置（谁来做）。

Prompt 管"做什么"，配置管"谁来做"。
配置文件是 env 格式文件：默认当前目录 `.env`，可用 path 指定其他文件
（如 `configs/qwen.env`）。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Union

from dotenv import dotenv_values


class ConfigError(ValueError):
    """配置缺失或无效。"""


@dataclass(frozen=True)
class ProviderConfig:
    base_url: str
    api_key: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    retries: int = 3


REQUIRED_VARS = ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL")


def _opt(
    values: dict, name: str, cast: Callable[[str], object], default: object
) -> object:
    raw = values.get(name)
    return cast(raw) if raw not in (None, "") else default


def load_config(path: Union[str, Path, None] = None) -> ProviderConfig:
    """加载 ProviderConfig。

    path 为 None 时读当前目录 `.env`，否则读指定文件。
    缺必填字段或文件不存在 → ConfigError。
    """
    env_path = Path(path) if path is not None else Path.cwd() / ".env"
    if not env_path.is_file():
        raise ConfigError(f"配置文件不存在: {env_path}")

    values = dotenv_values(env_path)

    missing = [k for k in REQUIRED_VARS if not values.get(k)]
    if missing:
        raise ConfigError(f"缺少必填配置 {', '.join(missing)} (文件: {env_path})")

    return ProviderConfig(
        base_url=values["LLM_BASE_URL"],
        api_key=values["LLM_API_KEY"],
        model=values["LLM_MODEL"],
        temperature=_opt(values, "LLM_TEMPERATURE", float, 0.7),
        max_tokens=_opt(values, "LLM_MAX_TOKENS", int, 4096),
        retries=_opt(values, "LLM_RETRIES", int, 3),
    )
