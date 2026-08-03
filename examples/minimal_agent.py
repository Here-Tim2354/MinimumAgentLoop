import json
import os

from openai import OpenAI

from minimal_prompts import SYSTEM_PROMPT  # 主模型的行为规则和权限边界。
from minimal_runtime import (  # 工具描述、srt 沙盒、host_bash 和权限模式。
    MODEL,
    TOOLS,
    permission_mode,
    run_tool,
    set_permission_mode,
)
from minimal_support import (
    read_user_message,  # 读取并显示橙黄色的用户输入。
    render_answer,  # 用蓝色显示最终回答。
    render_reasoning,  # 显示模型已经返回的思考内容。
    render_thinking,  # 在每次模型请求前显示“思考中”。
    render_tool_call,  # 用 LSP 色显示工具名称和命令。
    render_tool_result,  # 显示工具输出并标记工具区域结束。
    render_permission,  # 显示工具权限状态和审核结果。
)


def main() -> None:
    # 启动时告诉用户：工具输出默认折叠，权限可以在会话中切换。
    print(
        "\n命令：/auto 自动审核；/ask-me 每次询问；/deny 拒绝工具；/yolo 跳过审核；"
        "/expand 展开输出；/exit 退出。"
        f"\n沙盒：srt（默认开启）；权限：{permission_mode()}。"
        "\nWindows 首次运行前执行：npm run sandbox:install（需要一次 UAC）。"
    )
    client = OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )
    # messages 是整个会话的上下文，模型每次都会看到之前的 assistant 和 tool 消息。
    # 不同消息（user、assistant、tool）形状不同，交给 SDK 统一接收。
    messages: list[dict] = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
    ]

    # 外层循环处理用户消息，内层循环处理同一条消息可能触发的多次工具调用。
    while prompt := read_user_message():
        if prompt in {"/auto", "/ask-me", "/deny", "/yolo"}:
            mode = {
                "/auto": "autoreview",
                "/ask-me": "manual",
                "/deny": "deny",
                "/yolo": "yolo",
            }[prompt]
            set_permission_mode(mode)
            render_permission(f"权限模式已切换为 {permission_mode()}")
            continue

        messages.append({"role": "user", "content": prompt})

        while True:
            render_thinking()
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                reasoning_effort="max",
                extra_body={"thinking": {"type": "enabled"}},
            )
            message = response.choices[0].message.model_dump(exclude_none=True)
            # assistant 消息必须先写回上下文，下一次请求才能知道刚才做了什么。
            messages.append(message)
            if message.get("reasoning_content"):
                render_reasoning(message["reasoning_content"])
            calls = message.get("tool_calls") or []
            if not calls:
                render_answer(message.get("content") or "")
                break

            # 一次响应可能包含多个 Bash 调用，全部执行后再让模型继续判断。
            for call in calls:
                name = call["function"]["name"]
                command = json.loads(call["function"]["arguments"])["command"]
                render_tool_call(name, command)
                render_permission(f"{permission_mode()} 权限检查中……")
                output, audit = run_tool(name, command, client, prompt)
                if audit:
                    render_permission(audit)
                render_tool_result(output)
                # tool_call_id 把执行结果和对应的 assistant 调用配对起来。
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": output,
                    }
                )


if __name__ == "__main__":
    main()
