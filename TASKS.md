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

- [ ] T-005 processor.py
  - `LLMFileProcessor(provider).process(input_path, output_path, prompt_path, variables=None, force=False)`
  - 流程：读输入 → 渲染（内置变量 `content`/`filename`/`stem`/`input_path` + 调用方注入变量）→ `generate` → 原子写（tmp + rename）
  - 输出已存在且 `force=False` → skip（返回可区分状态，供批量层汇总）
  - `ProviderError` → 指数退避重试，超过 `config.retries` 后抛出
  - Done when: FakeProvider 单测覆盖 成功 / skip / force / 渲染失败 / 重试耗尽失败

- [ ] T-006 Phase 验收
  - Done when: `pytest` 全绿 + 一行脚本用 FakeProvider 完成一个 txt → md 处理
