<h1 align="center">tAI, a terminal AI assistant</h1>

<div align="center">
tAI is a CLI that helps you with Linux and macOS terminal commands. Just ask it a question, and it will use AI to suggest a command and explain what it does. If you like the suggestion, the script can automatically run the command for you in your terminal.
</div>
<br />

![Demo](example.png)

## Why & What?

- Github Copilot CLI syntax feels clunky to me
- Faster than using Gemini, ChatGPT or similar in a browser
- Simpler to find answers without checking man pages
- Support for multiple AI providers (OpenAI, Google, Anthropic, OpenRouter, Ollama, OpenCode)
- Interactive TUI setup using `inquirer` for provider and model selection
- **fzf** integration for fuzzy model selection (type to filter, arrows to navigate)
- Live model fetching from Ollama and OpenCode servers
- Enhanced terminal UI with `rich` for better readability and prompts
- Run commands right from this command-line interface

However, never trust the output entirely.

## Providers

| Provider | Type | API Key | Models |
|----------|------|---------|--------|
| `openai` | Cloud | Required | GPT-4.1-mini, o4-mini, GPT-4o, GPT-4-turbo, GPT-3.5-turbo |
| `google` | Cloud | Required | Gemini 2.5 Flash, Gemini 2.5 Pro |
| `anthropic` | Cloud | Required | Claude Sonnet 4, Claude 3.5 Haiku |
| `openrouter` | Cloud | Required | GPT-4o-mini, Claude 3.5 Sonnet, Gemini 2.5 Flash |
| `ollama` | Local | None | Fetches from local Ollama instance |
| `opencode` | Local | None | Fetches free models from OpenCode server |

### Ollama (Local)

Runs against your local [Ollama](https://ollama.com) instance. No API key needed.

```bash
# Make sure Ollama is running
ollama serve

# Install a model
ollama pull llama3.1

# Configure tAI
tai
# Select: ollama -> llama3.1
```

### OpenCode (Local)

Runs against your local [OpenCode](https://opencode.ai) server. No API key needed. Free models are listed first during setup.

```bash
# Make sure OpenCode server is running
opencode serve --port 4096

# Configure tAI
tai
# Select: opencode -> choose a free model
```

#### Systemd Service (recommended)

```ini
# ~/.config/systemd/user/opencode-server.service
[Unit]
Description=OpenCode Server (port 4096)
After=network.target

[Service]
Type=simple
EnvironmentFile=/etc/opencode/env
ExecStart=/home/<username>/.opencode/bin/opencode serve --hostname 0.0.0.0 --port 4096
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now opencode-server
```

## Installation

```bash
# install pipx (if you don't have it)
brew install pipx
pipx ensurepath

# install TAI from PyPI
pipx install terminal-ai-assistant

# or install from local repo (for development)
pipx install --force /path/to/tAI
```

## Usage

On your first run, `tai` will guide you through a quick, interactive setup process to choose your AI provider, select a model from a curated list, and enter your API key. This information will be securely stored in `~/.config/tai/config.json`.

Once configured, you can use `tai` with your queries:

```bash
$ tai kill port 3000

# Example output (formatted with rich):
╭────────────────────────────────────────────────── Command ───────────────────────────────────────────────────╮
│ kill $(lsof -t -i :3000)                                                                                     │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

Execute the command: kill $(lsof -t -i :3000)? [y/n]:
```

## Development

```bash
pip install --user pipenv
pipenv --python 3.11
pipenv install

pipenv run tai kill port 3000
```
