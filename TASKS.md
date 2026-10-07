# TASKS — llm-file-processor

## Phase 1: 核心原子
> Phase 验收：`pytest` 全绿 + 一行脚本用 FakeProvider 完成 文件→文件

- [x] T-001 包骨架
  - `pyproject.toml`：src layout；运行时依赖 `openai`、`python-dotenv`；dev 依赖 `pytest`
  - `.gitignore`：`.env`、`logs/`、`__pycache__/`、`.pytest_cache/`、`dist/`、`*.egg-info/`
  - `src/llm_processor/__init__.py`：暴露 `LLMFileProcessor`、`ProviderConfig`
  - Done when: `pip install -e .` 成功且 `import llm_processor` 无报错

- [x] T-002 config.py
  - `load_config(path=None) -> ProviderConfig`：默认读当前目录 `.env`；`path` 指定其他 env 文件（如 `configs/qwen.env`）
  - 字段：`base_url`、`api_key`、`model`（必填）；`temperature`、`max_tokens`、`retries`（可选，有默认值）
  - 缺必填字段 → 抛带清晰信息的错误（指出字段名和配置文件名）
  - Done when: 单测覆盖 默认加载 / 自定义配置文件 / 缺必填字段报错

- [x] T-003 templates.py
  - `render(template: str, variables: dict) -> str`：替换 `{{ name }}`
  - 模板里有变量但 variables 没提供 → 抛 `TemplateError`（防止拼写错误被静默漏掉）
  - Done when: 单测覆盖 单变量 / 多变量 / 无变量 / 未知变量报错

- [x] T-004 providers/openai_compatible.py
  - `OpenAICompatibleProvider(config).generate(messages) -> str`（基于 openai SDK，注入 `http_client` 以便 mock）
  - API 错误 / 超时 → 抛 `ProviderError`（重试不在这里，由 processor 层处理）
  - Done when: 单测用 mock transport 验证请求体（model / messages / temperature）与错误抛出路径

- [x] T-005 processor.py
  - `LLMFileProcessor(provider).process(input_path, output_path, prompt_path, variables=None, force=False)`
  - 流程：读输入 → 渲染（内置变量 `content`/`filename`/`stem`/`input_path` + 调用方注入变量）→ `generate` → 原子写（tmp + rename）
  - 输出已存在且 `force=False` → skip（返回可区分状态，供批量层汇总）
  - `ProviderError` → 指数退避重试，超过 `config.retries` 后抛出
  - Done when: FakeProvider 单测覆盖 成功 / skip / force / 渲染失败 / 重试耗尽失败

- [x] T-006 Phase 验收
  - Done when: `pytest` 全绿 + 一行脚本用 FakeProvider 完成一个 txt → md 处理

## Phase 2: CLI
> Phase 验收：真实 API（Qwen）跑通一个真实 transcript，输出可读

- [x] T-007 cli.py 核心（`main(argv, processor)`，零网络）
  - `build_parser()`：`--input`/`--input-dir` 互斥必填；`--output`/`--output-dir`；`--prompt` 必填；`--config`/`--ext`/`--force`/`--log-dir`
  - `main(argv=None, processor=None) -> int`：processor 可注入（测试用 FakeProvider）；退出码 0=成功 / 1=处理失败 / 2=用法或配置错误
  - 单文件：输入不存在 → 2；TemplateError/ProviderError/OSError → 1
  - 批量：非递归扫描 `.txt`/`.md`（排序）；输出名 = stem + `--ext`（默认 md）；空目录 → 2
  - TemplateError 属系统性错误：立即中止整批（返回 1）；ProviderError/OSError：记日志 + 跳过继续
  - 逐文件日志写 `logs/process-<ts>.log`（INFO）；stdout 汇总 `完成: X processed, Y skipped, Z failed` + 失败清单；有失败 → 退出码 1
  - Done when: tests/test_cli.py 覆盖 单文件成功 / 单文件失败退出 1 / skip / 批量混合（退出 1 + 失败清单 + 输出命名）/ 模板错误中止 / 参数错误（退出 2）
- [x] T-008 入口与配置接线
  - `build_processor(config_path=None)`：load_config → OpenAICompatibleProvider → LLMFileProcessor(retries=config.retries)
  - pyproject `[project.scripts] llm-process = "llm_processor.cli:main"`；`scripts/process.py` 薄封装
  - ConfigError → stderr + 退出 2
  - Done when: `llm-process --help` 可跑 + build_processor 单测（真实配置文件 → provider.config 正确）
- [ ] T-009 Phase 2 验收（真实 API）
  - 填 `.env`（Qwen 端点），单文件命令跑一个 qwen-bv-tts 真实 transcript
  - Done when: 输出 md 可读 + 批量模式冒烟（2 文件，重跑显示 skipped）
