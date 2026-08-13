# AI Coding Assistant (Codespaces-ready)

A minimal autonomous coding agent: Claude + tool-use loop that can read/write
files, run shell commands, and iterate until a task is verified.

## Setup

1. Open this repo in GitHub Codespaces (or locally with the `.devcontainer`).
2. Add your key: `cp .env.example .env` and paste your Anthropic API key,
   or set it as a Codespaces secret named `ANTHROPIC_API_KEY`.
3. Install deps (auto-runs in Codespaces via `postCreateCommand`):
   ```
   pip install -r requirements.txt
   ```

## Usage

```bash
python main.py solve "Write a function in utils.py that reverses a string, then add a pytest test for it and run the tests"
```

The agent will:
1. Inspect the repo
2. Write/edit files
3. Run shell commands (e.g. `pytest`) to verify its work
4. Loop and self-correct on failures
5. Report a final summary when done

## Files

| File | Purpose |
|---|---|
| `agent.py` | The core loop: calls Claude, executes tool calls, feeds results back |
| `tools.py` | Tool implementations (`read_file`, `write_file`, `list_dir`, `run_shell`) + safety guardrails |
| `main.py` | CLI entrypoint (`typer`) |
| `.devcontainer/devcontainer.json` | Codespaces container config |

## Safety notes

- All file/shell operations are sandboxed to the project working directory.
- A command blocklist prevents destructive operations (`rm -rf /`, `sudo`, etc).
- `max_turns` caps runaway loops.
- For production use, add: human-in-the-loop approval before writes, Docker-level
  isolation, and an allowlist (not just blocklist) for shell commands.

## Extending it

- Swap the hand-rolled loop for **LangGraph** for branching/multi-agent workflows.
- Add `GitPython`/`gh` calls so the agent opens PRs automatically once tests pass.
- Add `chromadb` + repo embeddings so it can reason over large codebases without
  blowing the context window.
