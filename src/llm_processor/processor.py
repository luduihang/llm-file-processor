"""原子处理器：单文件进 → 单文件出。"""


class LLMFileProcessor:
    """process(input_path, output_path, prompt_path, variables=None, force=False)

    TODO(T-005): 实现（读 → 渲染 → 调用 → 原子写 + 重试）。
    """
