"""
tools.py
Implements the actual actions the agent can take: read/write files,
run shell commands, and list directories — all sandboxed to the
project's working directory.
"""

import subprocess
import pathlib

# Restrict all file/shell operations to this root (safety guardrail)
WORKDIR = pathlib.Path.cwd().resolve()

# Commands the agent is never allowed to run
BLOCKED_COMMANDS = ["rm -rf /", "sudo", "mkfs", ":(){", "shutdown", "reboot"]


def _safe_path(path: str) -> pathlib.Path:
    """Resolve a path and make sure it stays inside WORKDIR."""
    p = (WORKDIR / path).resolve()
    if WORKDIR not in p.parents and p != WORKDIR:
        raise PermissionError(f"Access outside working directory denied: {path}")
    return p


def read_file(path: str) -> str:
    p = _safe_path(path)
    if not p.exists():
        return f"ERROR: file not found: {path}"
    return p.read_text(errors="replace")


def write_file(path: str, content: str) -> str:
    p = _safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"OK: wrote {len(content)} characters to {path}"


def list_dir(path: str = ".") -> str:
    p = _safe_path(path)
    if not p.exists():
        return f"ERROR: path not found: {path}"
    entries = sorted(str(x.relative_to(WORKDIR)) for x in p.rglob("*")
                      if ".git" not in x.parts)
    return "\n".join(entries) if entries else "(empty)"


def run_shell(command: str, timeout: int = 60) -> str:
    for blocked in BLOCKED_COMMANDS:
        if blocked in command:
            return f"ERROR: command blocked by safety policy: {command}"
    try:
        result = subprocess.run(
            command, shell=True, cwd=WORKDIR,
            capture_output=True, text=True, timeout=timeout
        )
        output = result.stdout + result.stderr
        return output.strip() or "(no output, exit code 0)"
    except subprocess.TimeoutExpired:
        return f"ERROR: command timed out after {timeout}s"


# Tool schemas for Claude's tool-use API
TOOL_SCHEMAS = [
    {
        "name": "read_file",
        "description": "Read and return the full contents of a file.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Relative file path"}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Create or overwrite a file with the given content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative file path"},
                "content": {"type": "string", "description": "Full file content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "list_dir",
        "description": "List all files recursively under a directory (default: project root).",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Relative dir path, default '.'"}},
        },
    },
    {
        "name": "run_shell",
        "description": "Run a shell command (e.g. pytest, pip install, git) in the project directory and return stdout/stderr.",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string", "description": "Shell command to execute"}},
            "required": ["command"],
        },
    },
]


def execute_tool(name: str, tool_input: dict) -> str:
    """Dispatch a tool call by name to its implementation."""
    try:
        if name == "read_file":
            return read_file(**tool_input)
        if name == "write_file":
            return write_file(**tool_input)
        if name == "list_dir":
            return list_dir(**tool_input)
        if name == "run_shell":
            return run_shell(**tool_input)
        return f"ERROR: unknown tool '{name}'"
    except Exception as e:
        return f"ERROR: {e}"
