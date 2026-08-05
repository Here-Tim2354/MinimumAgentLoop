# pyright: reportImplicitRelativeImport=false

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

import minimal_runtime as runtime  # 工具描述、srt 沙盒、host_bash 和权限模式。
import minimal_support as support  # 终端输入和渲染。
from minimal_prompts import SYSTEM_PROMPT  # 主模型的行为规则和权限边界。
from openai import OpenAI


def main() -> None:
    # 启动时展示会话控制命令和当前运行状态。
    support.render_welcome(
        runtime.sandbox_enabled(), runtime.permission_mode(), runtime.thinking_effort()
    )
    client = OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )
    # inputs 是整个会话的上下文：Responses API 无状态，每次请求全量传。
    inputs: list[Any] = []

    # 外层循环处理用户消息，内层循环处理同一条消息可能触发的多次工具调用。
    while True:
        prompt = support.read_user_message()
        if not prompt:
            break
        command = runtime.apply_slash_command(prompt)
        if command:
            kind, message = command
            (support.render_permission if kind == "permission" else support.render_think_level)(message)
            continue

        inputs.append({"role": "user", "content": prompt})

        while True:
            support.render_thinking(runtime.thinking_effort())
            response = client.responses.create(
                model=runtime.MODEL,
                instructions=SYSTEM_PROMPT,
                input=inputs,
                tools=runtime.TOOLS,
                **runtime.thinking_options(),
            )
            # 输出 item 必须先写回上下文，下一轮请求才知道刚才做了什么。
            calls = []
            for item in response.output:
                data = item.model_dump(exclude_none=True)
                inputs.append(data)
                if item.type == "reasoning":
                    text = "".join(p.get("text", "") for p in data.get("content") or [])
                    if text:
                        support.render_reasoning(text)
                elif item.type == "web_search_call":
                    support.render_web_search(data.get("action"))
                elif item.type == "function_call":
                    calls.append(item)
            if not calls:
                support.render_answer(response.output_text)
                support.render_session_status(
                    response.usage.total_tokens, runtime.CONTEXT_WINDOW,
                    runtime.thinking_effort(), runtime.permission_mode(),
                    runtime.sandbox_enabled(),
                )
                break

            # 一次响应可能包含多个 Bash 调用，全部执行后再让模型继续判断。
            for call in calls:
                command = json.loads(call.arguments)["command"]
                support.render_tool_call(call.name, command)
                support.render_permission(f"{runtime.permission_mode()} 权限检查中……")
                output, audit = runtime.run_tool(call.name, command, client, prompt)
                if audit:
                    support.render_permission(audit)
                support.render_tool_result(output)
                # call_id 把执行结果和对应的 function_call 配对起来。
                inputs.append({
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": output,
                })


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        support.render_goodbye()
