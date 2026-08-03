# 这个文件只负责教学版的终端输入和颜色渲染。
# 沙盒、工具执行和权限审核都在 minimal_runtime.py，避免主循环和 UI 互相缠绕。
RESET = "\033[0m"
USER = "\033[38;5;220m"  # 偏黄的橙黄色
LSP = "\033[36m"  # 工具调用使用青色作为 LSP 色
THINKING = "\033[90m"  # 灰色
TOOL_OUTPUT = "\033[90m"  # 工具输出也用灰色，和思考内容区分开边界。
ANSWER = "\033[94m"  # 蓝色
PERMISSION = "\033[38;5;214m"  # 权限请求使用醒目的橙色。

_tool_outputs: list[str] = []  # 保存当前用户请求产生的全部工具输出。


def render_thinking() -> None:
    # 先显示状态，用户能看到模型请求正在进行，即使本次没有 reasoning_content。
    print(f"\n{THINKING}[thinking] 思考中...{RESET}", flush=True)


def render_context_usage(usage: tuple[int, int, int, int]) -> None:
    capacity, prompt_tokens, _, total_tokens = usage
    capacity_label = (
        f"{capacity // 1_000_000}M"
        if capacity >= 1_000_000 and capacity % 1_000_000 == 0
        else f"{capacity:,}"
    )
    print(
        f"{THINKING}[context] 当前上下文长度：{prompt_tokens:,}/{capacity_label}；"
        f"本轮对话：{total_tokens:,}Tokens{RESET}",
        flush=True,
    )


def render_reasoning(content: str) -> None:
    # reasoning_content 是模型已经返回的思考文本，用灰色和最终回答区分开。
    print(f"{THINKING}[thinking] 思考内容{RESET}\n{THINKING}{content}{RESET}")


def render_tool_call(name: str, command: str) -> None:
    # 普通和特权工具都用 LSP 色，但保留工具名让越权请求可见。
    print(f"\n{LSP}[tool/{name}] {command}{RESET}")


def render_permission(content: str) -> None:
    # 权限状态和审核结果单独占一行，用户能看见当前模式是否改变。
    print(f"\n{PERMISSION}[permission] {content}{RESET}")


def render_tool_result(output: str) -> None:
    # 先保存并折叠输出，避免长日志淹没模型回答；/expand 会显示本轮全部输出。
    _tool_outputs.append(output)
    print(f"{TOOL_OUTPUT}[tool output folded — type /expand to show]{RESET}")


def expand_tool_output() -> None:
    # 展开时整块使用灰色，让用户一眼看出这不是 Agent 的回答。
    for number, output in enumerate(_tool_outputs, 1):
        print(
            f"\n{TOOL_OUTPUT}--- tool output {number} ---\n"
            f"{output}\n--- end tool {number} ---{RESET}"
        )


def read_user_message() -> str | None:
    # 支持层处理展开和退出；权限斜杠命令返回主循环来修改运行时状态。
    while True:
        print(f"\n{USER}You> ", end="", flush=True)
        message = input()
        print(RESET, end="\n", flush=True)
        if message == "/expand":
            expand_tool_output()
            continue
        if message in {"/exit", "/quit"}:
            return None
        _tool_outputs.clear()
        return message


def render_answer(content: str) -> None:
    # 这是一次模型循环的最终回答，用蓝色结束当前用户请求。
    print(f"\n{ANSWER}Agent> {content}{RESET}")
