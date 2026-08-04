# MinimumAgentLoop

一个用于理解 AgentLoop 的极简 Python 示例：模型可以思考、调用 Bash 工具、接收工具结果，再继续生成最终回答。

```text
用户输入 -> LLM -> 工具调用 -> 权限检查 -> Shell -> 工具结果 -> LLM
                \-> 无工具调用 -----------------------> 最终回答
```

## 运行要求

- Python 3.10+
- Node.js 20.11+
- DeepSeek API Key

## 安装

```bash
npm install
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell 激活虚拟环境：

```powershell
.venv\Scripts\Activate.ps1
```

Windows 首次使用沙盒前还需要执行：

```powershell
npm run sandbox:install
```

## 运行

项目不会自动读取 `.env`，请先设置环境变量。

macOS / Linux：

```bash
export DEEPSEEK_API_KEY="sk-..."
python examples/minimal_agent.py
```

Windows PowerShell：

```powershell
$env:DEEPSEEK_API_KEY="sk-..."
python examples/minimal_agent.py
```

其他配置可以参考 [.env.example](.env.example)。

## 会话命令

| 命令 | 作用 |
| --- | --- |
| `/permission-auto` | 由模型自动审核工具调用 |
| `/permission-ask` | 每次工具调用都询问用户 |
| `/permission-deny` | 拒绝工具调用 |
| `/permission-yolo` | 跳过权限审核 |
| `/sandbox-on` / `/sandbox-off` | 开启或关闭沙盒 |
| `/think-off` / `/think-high` / `/think-max` | 关闭思考，或切换思考档位 |
| `/expand` | 展开本轮工具输出 |
| `/exit` 或 `Ctrl+C` | 退出 |

## 文件结构

| 文件 | 职责 |
| --- | --- |
| `examples/minimal_agent.py` | AgentLoop 主循环 |
| `examples/minimal_runtime.py` | 工具、沙盒和权限审核 |
| `examples/minimal_support.py` | 终端输入与渲染 |
| `examples/minimal_prompts.py` | Agent 与审核模型提示词 |

## 教学范围

这个项目用于展示多轮工具调用的基本过程，刻意不实现上下文压缩、会话持久化、自动重试和生产级框架能力。

## License

本项目使用 [The Unlicense](LICENSE)，可以不受限制地使用、修改、发布和分发。
