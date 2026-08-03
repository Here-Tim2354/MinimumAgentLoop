# pyright: reportImplicitRelativeImport=false

import json
import os
from collections.abc import Iterable
from typing import Any, cast

import minimal_runtime as runtime  # 工具描述、srt 沙盒、host_bash 和权限模式。
import minimal_support as support  # 终端输入和渲染。
from minimal_prompts import SYSTEM_PROMPT  # 主模型的行为规则和权限边界。
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam


def main() -> None:
    # 启动时展示会话控制命令和当前运行状态。
    support.render_welcome(runtime.sandbox_enabled(), runtime.permission_mode())
    client = OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )
    # messages 是整个会话的上下文，模型每次都会看到之前的 assistant 和 tool 消息。
    # 不同消息（user、assistant、tool）形状不同，交给 SDK 统一接收。
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
    ]
    previous_context_tokens: int | None = None

    # 外层循环处理用户消息，内层循环处理同一条消息可能触发的多次工具调用。
    while prompt := support.read_user_message():
        if prompt in {"/auto", "/ask-me", "/deny", "/yolo"}:
            mode = {
                "/auto": "autoreview",
                "/ask-me": "manual",
                "/deny": "deny",
                "/yolo": "yolo",
            }[prompt]
            runtime.set_permission_mode(mode)
            support.render_permission(f"权限模式已切换为 {runtime.permission_mode()}")
            continue
        if prompt in {"/on", "/off"}:
            runtime.set_sandbox_enabled(prompt == "/on")
            state = "开启" if runtime.sandbox_enabled() else "关闭"
            destination = "使用 srt" if runtime.sandbox_enabled() else "直接在宿主机执行"
            support.render_permission(f"沙盒已{state}；bash 将{destination}")
            continue

        messages.append({"role": "user", "content": prompt})

        while True:
            support.render_thinking()
            response = client.chat.completions.create(
                model=runtime.MODEL,
                messages=cast(Iterable[ChatCompletionMessageParam], messages),
                tools=runtime.TOOLS,
                reasoning_effort="max",
                extra_body={"thinking": {"type": "enabled"}},
            )
            message: dict[str, Any] = response.choices[0].message.model_dump(exclude_none=True)
            # assistant 消息必须先写回上下文，下一次请求才能知道刚才做了什么。
            messages.append(message)
            if message.get("reasoning_content"):
                support.render_reasoning(message["reasoning_content"])
            calls = message.get("tool_calls") or []
            if not calls:
                support.render_answer(message.get("content") or "")
                usage = runtime.context_usage(response, previous_context_tokens)
                support.render_context_usage(usage)
                previous_context_tokens = usage[1]
                break

            # 一次响应可能包含多个 Bash 调用，全部执行后再让模型继续判断。
            for call in calls:
                name = call["function"]["name"]
                command = json.loads(call["function"]["arguments"])["command"]
                support.render_tool_call(name, command)
                support.render_permission(f"{runtime.permission_mode()} 权限检查中……")
                output, audit = runtime.run_tool(name, command, client, prompt)
                if audit:
                    support.render_permission(audit)
                support.render_tool_result(output)
                # tool_call_id 把执行结果和对应的 assistant 调用配对起来。
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": output,
                    }
                )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        support.render_goodbye()
