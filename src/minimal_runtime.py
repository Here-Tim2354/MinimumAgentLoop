"""教学版运行时：srt 沙盒、两个 shell 工具和 DeepSeek 权限审核。"""

# pyright: reportImplicitRelativeImport=false

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from minimal_prompts import REVIEWER_PROMPT
from openai import OpenAI

MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
REVIEW_MODEL = os.getenv("DEEPSEEK_REVIEW_MODEL", MODEL)
_permission_mode = os.getenv("PERMISSION_MODE", "autoreview").lower()
_sandbox_enabled = True
_thinking_effort = "max"
CONTEXT_WINDOW = int(os.getenv("DEEPSEEK_CONTEXT_WINDOW", "1000000"))
PERMISSION_COMMANDS = {
    "/permission-auto": "autoreview",
    "/permission-ask": "manual",
    "/permission-deny": "deny",
    "/permission-yolo": "yolo",
}
_LOCAL_SRT = Path(__file__).resolve().parents[1] / "node_modules" / ".bin" / (
    "srt.cmd" if os.name == "nt" else "srt"
)
SRT_COMMAND = os.getenv(
    "SRT_COMMAND", str(_LOCAL_SRT) if _LOCAL_SRT.exists() else "srt"
)


def permission_mode() -> str:
    """返回当前会话的权限模式。"""
    return {"autoreview": "auto", "manual": "ask"}.get(
        _permission_mode, _permission_mode
    )


def set_permission_mode(mode: str) -> None:
    """让 CLI 斜杠命令切换当前会话的权限模式。"""
    global _permission_mode
    _permission_mode = mode


def sandbox_enabled() -> bool:
    """返回当前会话是否启用 srt 沙盒。"""
    return _sandbox_enabled


def set_sandbox_enabled(enabled: bool) -> None:
    """让 CLI 斜杠命令切换当前会话的沙盒。"""
    global _sandbox_enabled
    _sandbox_enabled = enabled


def thinking_effort() -> str:
    """返回当前会话的思考档位。"""
    return _thinking_effort


def set_thinking_effort(effort: str) -> None:
    """让 CLI 斜杠命令切换当前会话的思考档位。"""
    global _thinking_effort
    _thinking_effort = effort


def apply_slash_command(prompt: str) -> tuple[str, str] | None:
    """识别并应用会话控制命令，返回 (渲染类别, 提示文案)。"""
    if prompt in PERMISSION_COMMANDS:
        set_permission_mode(PERMISSION_COMMANDS[prompt])
        return "permission", f"权限模式已切换为 {permission_mode()}"
    if prompt == "/sandbox-on":
        set_sandbox_enabled(True)
        return "permission", "沙盒已开启；bash 将使用 srt"
    if prompt == "/sandbox-off":
        set_sandbox_enabled(False)
        return "permission", "沙盒已关闭；bash 将直接在宿主机执行"
    if prompt in {"/think-off", "/think-high", "/think-max"}:
        set_thinking_effort(prompt.removeprefix("/think-"))
        return "think", f"思考档位已切换为 {thinking_effort()}"
    return None


def thinking_options() -> dict[str, Any]:
    """把思考档位转换成 Responses API 的 reasoning 参数。"""
    effort = "none" if _thinking_effort == "off" else _thinking_effort
    return {"reasoning": {"effort": effort}}


def _command_tool(name: str, description: str) -> dict[str, Any]:
    """生成两个形状相同的命令工具描述，避免重复 JSON。"""
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    }


# web_search 由 DeepSeek 服务端执行；bash 默认先进沙盒，两个 shell 工具都受权限模式控制。
TOOLS: list[Any] = [
    {"type": "web_search"},
    _command_tool(
        "bash",
        "Run a shell command in the default local srt sandbox. "
        "The host may disable the sandbox for this session; use it for normal workspace work.",
    ),
    _command_tool(
        "host_bash",
        "Request one shell command outside the srt sandbox. "
        "It is subject to the current host permission mode; use it for safe work "
        "when the task calls for host access.",
    ),
]


def _shell_argv(command: str) -> list[str]:
    """把模型命令交给当前平台的 shell，不经过额外的宿主 shell。"""
    if os.name != "nt":
        return ["bash", "-lc", command]

    shell = os.getenv("AGENT_SHELL", "powershell").lower()
    if shell in {"bash", "git-bash"}:
        return [os.getenv("GIT_BASH_PATH", "bash.exe"), "-lc", command]
    return [
        "powershell.exe",
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        command,
    ]


def _decode(data: bytes) -> str:
    """兼容 PowerShell、Git Bash 和普通 UTF-8 输出。"""
    encoding = "utf-16-le" if b"\x00" in data else "utf-8"
    return data.decode(encoding, errors="replace")


def _run(argv: list[str]) -> str:
    """执行一个已经组装好的 argv，并把退出码交给模型。"""
    env = os.environ.copy()
    env.pop("DEEPSEEK_API_KEY", None)
    result = subprocess.run(
        argv, cwd=Path.cwd(), env=env, capture_output=True, check=False
    )
    output = _decode(result.stdout) + _decode(result.stderr)
    return f"{output}\n[exit code: {result.returncode}]"


def _settings_file() -> Path:
    """生成 srt 策略文件：允许写入工作目录，网络和默认写权限保持关闭。"""
    workspace = Path.cwd().resolve()
    settings = {
        "network": {"allowedDomains": [], "deniedDomains": ["*"]},
        "filesystem": {
            # srt 要求这两个字段存在；空数组表示不额外打 ACL 拒绝标记。
            "denyRead": [],
            "denyWrite": [],
            "allowWrite": [str(workspace)],
        },
    }
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".json", delete=False
    ) as file:
        json.dump(settings, file, ensure_ascii=False, indent=2)
        return Path(file.name)


def sandbox_bash(command: str) -> str:
    """默认工具：用 srt 包住 shell，网络默认关闭。"""
    settings = _settings_file()
    try:
        return _run([SRT_COMMAND, "--settings", str(settings), *_shell_argv(command)])
    finally:
        settings.unlink(missing_ok=True)


def host_bash(command: str) -> str:
    """特权工具：在宿主 shell 中执行。"""
    return _run(_shell_argv(command))


def _review(
    client: OpenAI, name: str, command: str, user_request: str
) -> tuple[str, str]:
    """让同一个 DeepSeek API 审核工具请求。"""
    request = json.dumps(
        {
            "user_request": user_request,
            "command": command,
            "working_directory": str(Path.cwd()),
            "requested_tool": name,
        },
        ensure_ascii=False,
    )
    response = client.chat.completions.create(
        model=REVIEW_MODEL,
        messages=[
            {"role": "system", "content": REVIEWER_PROMPT},
            {"role": "user", "content": f"<request>{request}</request>"},
        ],
        reasoning_effort="max",
        extra_body={"thinking": {"type": "enabled"}},
    )
    decision = json.loads(response.choices[0].message.content or "{}")
    return decision.get("decision", "deny"), decision.get("reason", "审核返回格式异常")


def _permission(
    client: OpenAI, name: str, command: str, user_request: str
) -> tuple[str, str]:
    """根据当前权限模式决定允许、拒绝或提交审核。"""
    if _permission_mode == "yolo":
        return "allow", "已跳过权限审核"
    if _permission_mode == "manual":
        decision = "allow" if input("允许这条命令执行吗？[y/N] ").lower() == "y" else "deny"
        return decision, "用户确认" if decision == "allow" else "用户拒绝"
    if _permission_mode == "deny":
        return "deny", "权限模式为 deny"
    return _review(client, name, command, user_request)


def run_tool(
    name: str, command: str, client: OpenAI, user_request: str
) -> tuple[str, str | None]:
    """运行模型请求的工具，并返回工具内容和可显示的权限审计信息。"""
    if name not in {"bash", "host_bash"}:
        return f"Unknown tool: {name}", None

    decision, reason = _permission(client, name, command, user_request)
    audit = f"{permission_mode()}: {decision} — {reason}"

    if decision != "allow":
        return f"[permission denied]\n{reason}", audit
    output = (
        sandbox_bash(command)
        if name == "bash" and _sandbox_enabled
        else host_bash(command)
    )
    return output, audit
