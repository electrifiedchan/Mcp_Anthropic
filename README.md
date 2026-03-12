# MCP Chat

A terminal-based AI chat application powered by **Groq's Llama 3.3 70B** model, built on the **Model Context Protocol (MCP)** architecture. It gives the LLM live access to your local file system and provides a rich CLI experience with tab-completion, command suggestions, and document referencing — all from your terminal.

---

## Features

- **Conversational AI** — Multi-turn chat with Groq's Llama 3.3 70B Versatile model
- **Local File Access via MCP** — The AI can read files directly from your project directory using the `read_local_file` tool
- **`@document` Referencing** — Mention a file with `@filename` to inject its contents as context into your query
- **`/command` Prompts** — Run server-defined prompt templates with `/command <arg>` syntax
- **Tab Completion** — Auto-complete commands and document IDs as you type
- **Extensible MCP Architecture** — Connect additional MCP servers by passing their script paths as arguments at startup

---

## Requirements

- Python 3.10+
- [Groq API key](https://console.groq.com/)
- [`uv`](https://github.com/astral-sh/uv) *(recommended)* or `pip`

---

## Installation

### Option 1 — Using `uv` (Recommended)

`uv` is a fast Python package manager. Install it once, then:

```bash
# 1. Clone the repository
git clone https://github.com/electrifiedchan/Mcp_Anthropic.git
cd Mcp_Anthropic

# 2. Create and activate a virtual environment
uv venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 3. Install the project and its dependencies
uv pip install -e .
```

### Option 2 — Using `pip`

```bash
git clone https://github.com/electrifiedchan/Mcp_Anthropic.git
cd Mcp_Anthropic

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

pip install anthropic groq python-dotenv prompt-toolkit "mcp[cli]>=1.8.0"
```

---

## Configuration

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
CLAUDE_MODEL=llama-3.3-70b-versatile
```

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your Groq API secret key — get one at [console.groq.com](https://console.groq.com/) |
| `CLAUDE_MODEL` | The model identifier passed at startup (the runtime pins to `llama-3.3-70b-versatile`) |

---

## Running the App

```bash
# Start with the built-in local file system MCP server
python main.py

# Optionally attach additional MCP servers
python main.py extra_server.py another_server.py
```

---

## Usage

### Chat

Type any message and press **Enter** to send it:

```
> Explain how async context managers work in Python
```

### Reference a Local File with `@`

Prefix a filename with `@` to inject its contents into the prompt. Tab-completion is available after `@`.

```
> Summarize the logic in @core/chat.py
```

### Run a Prompt Command with `/`

Use `/` to trigger server-defined prompt templates. Tab-completion shows available commands.

```
> /summarize report.txt
```

### Keyboard Shortcuts

| Key | Action |
|---|---|
| `Tab` | Auto-complete commands or document names |
| `@` | Opens document completion menu |
| `/` | Opens command completion menu |
| `↑` / `↓` | Navigate input history |
| `Ctrl+C` | Exit the application |

---

## Project Structure

```
.
├── main.py              # Entry point — wires MCP clients, Claude service, and CLI together
├── mcp_client.py        # Async MCP client (StdIO transport)
├── mcp_server.py        # Built-in MCP server exposing read_local_file tool
├── core/
│   ├── claude.py        # LLM interface (Groq/Llama backend, Anthropic-compatible API)
│   ├── chat.py          # Core agentic chat loop with tool-use handling
│   ├── cli_chat.py      # CLI-specific chat layer (@mentions, /commands, resource injection)
│   ├── cli.py           # prompt_toolkit UI — completion, key bindings, session
│   └── tools.py         # ToolManager — discovers and executes MCP tools across clients
├── pyproject.toml       # Project metadata and dependencies
└── .env                 # Local secrets (not committed)
```

---

## Architecture Overview

```
User Input (CLI)
      │
      ▼
  CliApp (prompt_toolkit)
      │
      ▼
  CliChat ──── @mentions / /commands
      │
      ▼
   Chat (agentic loop)
      │  ┌──────────────────────┐
      ├──▶  Claude / Groq LLM   │
      │  └──────────────────────┘
      │  ┌──────────────────────┐
      └──▶  MCP Clients         │
           │  mcp_server.py     │
           │  (read_local_file) │
           └──────────────────────┘
```

The `Chat` class runs an autonomous loop: it sends the user's message to the LLM with available tools, and if the model requests a tool call, it routes the request through the appropriate `MCPClient`, feeds the result back, and continues until the model produces a final text response.

---

## Extending the App

### Add a New MCP Server

Write a new MCP server script (see `mcp_server.py` as a reference) and pass it at startup:

```bash
python main.py my_new_server.py
```

### Add New Tools

Define additional tools inside `mcp_server.py` (or a new server) using the `@app.list_tools()` and `@app.call_tool()` decorators. The `ToolManager` will automatically discover and expose them to the LLM.

