# MinimumAgentLoop

**中文** | [English](README.en.md)

这是我开发的一个用于理解 AgentLoop 的极简 Python 示例。**核心文件 `minimal_agent.py` 不到 100 行**

核心文件非常简单，两层 While 循环就可以让模型思考、调用 Bash/Web 工具、接收工具结果，再继续生成最终回答。

```text
用户输入 -> LLM -> 工具调用 -> 权限检查 -> Shell -> 工具结果 -> LLM
                \-> 无工具调用 -----------------------> 最终回答
```

作为初学者，只需要阅读`minimal_agent.py`足矣。其他支持文件并不重要。

## 功能

本项目高度基于 `deepseek-v4-flash` 正式版开发，并且采用 `Responses API` 进行模型调用。

我加入了不少现代 Agent 所必备的功能，比如：
1. 自动审核命令
2. 思考档位调整
3. 工具调用权限设置
4. 沙箱开关
5. 联网搜索（Deepseek 官方支持）

也加入了一些用户体验的优化，比如文字颜色渲染，默认折叠工具调用结果。

通过以下命令开关：


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

## 取舍

代码量是有意控制的。本项目完全没有任何的：
1. 上下文管理机制
2. `AGENTS.md/SKILLS` 规范支持
3. subagents/browser use 等高级功能
4. 数据校验，防御性/安全性编程

好吧，沙箱是个例外。为了避免大肥鱼意外地删掉了新生们的文件。

## 运行要求

确保电脑有以下环境：

- Python 3.10+
- Node.js 20.11+（本项目采用了`@anthropic-ai/sandbox-runtime`用于安装 srt 沙盒运行时）

需要有 DeepSeek 官方 API 的密钥：
- DeepSeek API Key


## 安装

通过以下命令将文件安装到本地：

```bash
git clone https://github.com/Here-Tim2354/MinimumAgentLoop.git
cd MinimumAgentLoop
npm install
pip install -r requirements.txt
```

其中 `npm install` 安装的是 srt 沙盒运行时。Windows 首次使用沙盒前还需要执行：

```powershell
npm run sandbox:install
```

## 运行

复制 [.env.example](.env.example) 为 `.env` 并填入 `DEEPSEEK_API_KEY`，程序启动时会自动加载你的密钥。

也可以直接通过环境变量来存放你的密钥（仅限该终端窗口）。如果是 Mac：
```bash
export DEEPSEEK_API_KEY="sk-..."
```

如果是 Windows：
```powershell
$env:DEEPSEEK_API_KEY="sk-..."
```

通过以下命令执行本程序：
```bash
python src/minimal_agent.py
```


## 项目结构

| 文件 | 职责 |
| --- | --- |
| `src/minimal_agent.py` | AgentLoop 主循环 |
| `src/minimal_runtime.py` | 工具、沙盒和权限审核 |
| `src/minimal_render.py` | 终端输入与渲染 |
| `src/minimal_prompts.py` | Agent 与审核模型提示词 |

## License

本项目使用 [The Unlicense](LICENSE)，可以不受限制地使用、修改、发布和分发。
