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


def render_welcome(
    sandbox_enabled: bool, permission_mode: str, thinking_effort: str
) -> None:
    """打印欢迎信息和当前会话状态。"""
    sandbox_state = "开启" if sandbox_enabled else "关闭"
    print(
        "\n权限：/permission-auto | /permission-ask | /permission-deny | /permission-yolo"
        "\n沙盒：/sandbox-on | /sandbox-off"
        "\n思考：/think-off | /think-high | /think-max"
        "\n其他：/expand 展开本轮工具输出 | /exit 或 Ctrl+C 退出"
        f"\n当前：沙盒{sandbox_state}；权限：{permission_mode}；思考：{thinking_effort}。"
        "\nWindows 首次运行前执行：npm run sandbox:install（需要一次 UAC）。"
    )


def render_thinking(effort: str) -> None:
    """显示模型请求状态和思考档位。"""
    print(f"\n{THINKING}[thinking/{effort}] 请求中...{RESET}", flush=True)


def render_session_status(
    context_tokens: int,
    capacity: int,
    thinking_effort: str,
    permission_mode: str,
    sandbox_enabled: bool,
) -> None:
    """打印本轮请求的上下文用量和运行状态。"""
    capacity_label = (
        f"{capacity // 1_000_000}M"
        if capacity % 1_000_000 == 0
        else f"{capacity:,}"
    )
    sandbox = "on" if sandbox_enabled else "off"
    print(
        f"{ANSWER}thinking:{thinking_effort} 丨 permission:{permission_mode} 丨 "
        f"sandbox:{sandbox} 丨 context:{context_tokens:,}/{capacity_label}{RESET}",
        flush=True,
    )


def render_reasoning(content: str) -> None:
    """显示模型返回的 reasoning 思考文本。"""
    print(f"{THINKING}[thinking] 思考内容{RESET}\n{THINKING}{content}{RESET}")


def render_tool_call(name: str, command: str) -> None:
    """显示模型发起的本地工具调用。"""
    print(f"\n{LSP}[tool/{name}] {command}{RESET}")


def render_web_search(action: dict | None) -> None:
    """显示 DeepSeek 服务端联网搜索提示。"""
    # 服务端会在 queries 末尾塞一个 ws_call_id=... 的追踪项，展示时过滤掉。
    queries = [q for q in (action or {}).get("queries") or [] if not q.startswith("ws_call_id=")]
    detail = f"，查询：{'、'.join(queries)}" if queries else ""
    print(f"\n{LSP}[web_search] DeepSeek 正在联网搜索{detail}……{RESET}")


def render_permission(content: str) -> None:
    """显示权限状态或审核结果。"""
    print(f"\n{PERMISSION}[permission] {content}{RESET}")


def render_think_level(content: str) -> None:
    """显示思考档位切换提示。"""
    print(f"\n{PERMISSION}[think_level] {content}{RESET}")


def render_notice(kind: str, message: str) -> None:
    """根据通知类别分发到对应的渲染函数。"""
    (render_permission if kind == "permission" else render_think_level)(message)


def render_tool_result(output: str) -> None:
    """折叠保存本轮工具输出，避免长日志淹没模型回答。"""
    _tool_outputs.append(output)
    print(f"{TOOL_OUTPUT}[tool output folded — type /expand to show]{RESET}")


def expand_tool_output() -> None:
    """展开显示本轮所有工具输出。"""
    for number, output in enumerate(_tool_outputs, 1):
        print(
            f"\n{TOOL_OUTPUT}--- tool output {number} ---\n"
            f"{output}\n--- end tool {number} ---{RESET}"
        )


def read_user_message() -> str | None:
    """读取用户输入，处理 /expand 和退出命令。"""
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
    """显示本轮最终回答。"""
    print(f"\n{ANSWER}Agent> {content}{RESET}")


def render_goodbye() -> None:
    """显示退出告别语。"""
    print(f"\n{ANSWER}Agent> 好的，先告辞啦！👋{RESET}", flush=True)
