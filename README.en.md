# MinimumAgentLoop

[中文](README.md) | **English**

A minimal Python example I built to understand the AgentLoop. **The core file `minimal_agent.py` is under 100 lines.**

The core is deliberately simple: two nested `while` loops let the model think, call Bash/Web tools, receive tool results, and then produce a final answer.

```text
user input -> LLM -> tool call -> permission check -> shell -> tool result -> LLM
                  \-> no tool call ---------------------------> final answer
```

If you're a beginner, reading `minimal_agent.py` alone is enough — the other supporting files don't matter much.

## Features

The project is built primarily against the release version of `deepseek-v4-flash` and calls the model through the `Responses API`.

It includes several capabilities a modern Agent needs, such as:
1. Automatic command review
2. Adjustable thinking effort
3. Tool-call permission modes
4. Sandbox on/off switch
5. Web search (officially supported by DeepSeek)

It also ships a few UX touches, such as colored terminal output and tool results collapsed by default.

Controlled via the following commands:


| Command | Effect |
| --- | --- |
| `/permission-auto` | Let the model review tool calls automatically |
| `/permission-ask` | Ask the user before every tool call |
| `/permission-deny` | Deny tool calls |
| `/permission-yolo` | Skip permission review |
| `/sandbox-on` / `/sandbox-off` | Enable or disable the sandbox |
| `/think-off` / `/think-high` / `/think-max` | Turn thinking off, or switch the thinking effort |
| `/expand` | Expand this turn's tool output |
| `/exit` or `Ctrl+C` | Quit |

Note: the built-in system prompt and terminal messages are in Chinese.

## Trade-offs

The line count is intentionally capped. This project has absolutely none of the following:
1. Context management
2. Support for `AGENTS.md`/`SKILLS` conventions
3. Advanced features such as subagents or browser use
4. Data validation, defensive/secure programming

Well, the sandbox is the one exception — to keep the big fat fish from accidentally deleting the freshmen's files.

## Requirements

Make sure your machine has:

- Python 3.10+
- Node.js 20.11+ (this project uses `@anthropic-ai/sandbox-runtime` to provide the srt sandbox runtime)

You also need an official DeepSeek API key:
- DeepSeek API Key


## Installation

Clone the repo and install the dependencies:

```bash
git clone https://github.com/Here-Tim2354/MinimumAgentLoop.git
cd MinimumAgentLoop
npm install
pip install -r requirements.txt
```

Here `npm install` installs the srt sandbox runtime. On Windows, before using the sandbox for the first time, you also need to run:

```powershell
npm run sandbox:install
```

## Usage

Copy [.env.example](.env.example) to `.env` and fill in `DEEPSEEK_API_KEY`; it is loaded automatically on startup.

You can also pass the key through an environment variable (current terminal window only). On macOS:
```bash
export DEEPSEEK_API_KEY="sk-..."
```

On Windows:
```powershell
$env:DEEPSEEK_API_KEY="sk-..."
```

Run the program with:
```bash
python src/minimal_agent.py
```


## Project Structure

| File | Responsibility |
| --- | --- |
| `src/minimal_agent.py` | The AgentLoop main loop |
| `src/minimal_runtime.py` | Tools, sandbox, and permission review |
| `src/minimal_render.py` | Terminal input and rendering |
| `src/minimal_prompts.py` | Prompts for the agent and the reviewer model |

## License

This project is released under [The Unlicense](LICENSE) — use, modify, publish, and distribute it without restriction.
