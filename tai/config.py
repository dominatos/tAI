import os
import json
import subprocess
import inquirer
import requests
from rich.console import Console
from rich.panel import Panel

CONFIG_DIR = os.path.expanduser("~/.config/tai")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
CONSOLE = Console()

MODELS = {
    "openai": ["gpt-4.1-mini", "o4-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
    "google": ["gemini-2.5-flash", "gemini-2.5-pro"],
    "anthropic": ["claude-sonnet-4-20250514", "claude-3-5-haiku-20241022"],
    "openrouter": ["openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet", "google/gemini-2.5-flash"],
    "ollama": [],
    "opencode": [],
}


def has_fzf():
    """Check if fzf is available."""
    try:
        subprocess.run(["fzf", "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def fzf_select(items, prompt="Select"):
    """Use fzf to select an item from a list. Returns selected item or None."""
    try:
        proc = subprocess.Popen(
            ["fzf", "--prompt", f"{prompt}> ", "--height", "40%", "--reverse"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        stdout, _ = proc.communicate(input="\n".join(items))
        if proc.returncode == 0 and stdout.strip():
            return stdout.strip()
        return None
    except (FileNotFoundError, OSError):
        return None


def fetch_ollama_models():
    """Fetch available models from local Ollama instance."""
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        return models if models else MODELS.get("ollama", [])
    except Exception:
        return MODELS.get("ollama", [])


def fetch_opencode_models():
    """Fetch available free models from OpenCode server, free first."""
    try:
        resp = requests.get("http://localhost:4096/provider", timeout=5)
        resp.raise_for_status()
        free_models = []
        for provider in resp.json().get("all", []):
            provider_id = provider.get("id", "")
            for model_id, model_info in provider.get("models", {}).items():
                cost = model_info.get("cost", {})
                if cost.get("input", 0) == 0 and cost.get("output", 0) == 0:
                    name = model_info.get("name", model_id)
                    full_id = f"{provider_id}/{model_id}"
                    free_models.append((full_id, name))
        free_models.sort(key=lambda x: x[1].lower())
        return free_models
    except Exception:
        return []


def load_config():
    """
    Loads the configuration from the config file.
    Returns the config dictionary or None if it doesn't exist or is invalid.
    """
    if not os.path.exists(CONFIG_PATH):
        return None
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        CONSOLE.print(
            Panel(
                f"[bold red]Error reading config file at {CONFIG_PATH}: {e}. Please fix or delete it.[/bold red]",
                title="Configuration Error",
                border_style="red",
            )
        )
        return None


def create_config():
    """
    Prompts the user to create a new configuration file and saves it.
    """
    CONSOLE.print(
        Panel(
            "[bold yellow]Welcome to tAI! Let's set up your configuration.[/bold yellow]",
            title="tAI Setup",
            border_style="yellow",
        )
    )

    questions = [
        inquirer.List(
            "provider",
            message="Choose your AI provider",
            choices=list(MODELS.keys()),
        ),
    ]
    answers = inquirer.prompt(questions)
    provider = answers["provider"]
    use_fzf = has_fzf()

    if provider == "ollama":
        with CONSOLE.status("[bold green]Fetching Ollama models...[/bold green]"):
            ollama_models = fetch_ollama_models()
        if ollama_models:
            model_choices = ollama_models
        else:
            CONSOLE.print("[yellow]No Ollama models found. Make sure Ollama is running.[/yellow]")
            model_choices = MODELS.get("ollama", [])
    elif provider == "opencode":
        with CONSOLE.status("[bold green]Fetching free OpenCode models...[/bold green]"):
            opencode_models = fetch_opencode_models()
        if opencode_models:
            model_choices = [f"{mid}  ({name})" for mid, name in opencode_models]
        else:
            CONSOLE.print("[yellow]No OpenCode models found. Make sure OpenCode server is running.[/yellow]")
            model_choices = MODELS.get("opencode", [])
    else:
        model_choices = MODELS.get(provider, [])

    if model_choices:
        if use_fzf:
            all_choices = model_choices + ["custom (enter manually)"]
            selected = fzf_select(all_choices, prompt="Choose a model")
            if selected is None:
                CONSOLE.print("[red]No selection made. Exiting.[/red]")
                return
            if selected == "custom (enter manually)":
                custom_answer = inquirer.prompt(
                    [inquirer.Text("model", message="Enter custom model name")]
                )
                answers["model"] = custom_answer["model"].strip()
            elif provider == "opencode" and "  (" in selected:
                answers["model"] = selected.split("  (")[0]
            else:
                answers["model"] = selected
        else:
            model_questions = [
                inquirer.List(
                    "model_choice",
                    message="Choose a model (or enter a custom model name)",
                    choices=model_choices + ["custom"],
                ),
            ]
            answers.update(inquirer.prompt(model_questions))
            if answers["model_choice"] == "custom":
                custom_answer = inquirer.prompt(
                    [inquirer.Text("model", message="Enter custom model name")]
                )
                answers["model"] = custom_answer["model"].strip()
            elif provider == "opencode" and "  (" in answers["model_choice"]:
                answers["model"] = answers["model_choice"].split("  (")[0]
            else:
                answers["model"] = answers["model_choice"]
    else:
        answers.update(
            inquirer.prompt([inquirer.Text("model", message="Enter model name")])
        )

    if provider in ["ollama", "opencode"]:
        config = {
            "provider": answers["provider"],
            "api_key": "local",
            "model": answers["model"],
        }
    else:
        answers.update(
            inquirer.prompt(
                [inquirer.Password("api_key", message=f"Enter your {provider.capitalize()} API key")]
            )
        )
        config = {
            "provider": answers["provider"],
            "api_key": answers["api_key"],
            "model": answers["model"],
        }

    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

    CONSOLE.print(
        Panel(
            f"[bold green]Configuration saved successfully to {CONFIG_PATH}.\nYou can now run 'tai <your-query>'.[/bold green]",
            title="Setup Complete",
            border_style="green",
        )
    )
