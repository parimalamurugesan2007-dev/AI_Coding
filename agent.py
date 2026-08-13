"""
agent.py
The autonomous agent loop: sends the goal + conversation history to Claude,
executes whatever tools Claude requests, feeds results back, and repeats
until Claude finishes (no more tool calls) or max_turns is hit.
"""

import os
from dotenv import load_dotenv
import anthropic
from tools import TOOL_SCHEMAS, execute_tool

load_dotenv()

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are an autonomous coding assistant working inside a
GitHub Codespace. You have tools to read/write files, list directories,
and run shell commands (tests, linters, git, pip/npm installs, etc).

Rules:
1. Always inspect the repo (list_dir / read_file) before making changes,
   unless the task is trivially self-contained.
2. Make small, verifiable changes. After writing code, run tests or the
   relevant command to confirm it works before declaring success.
3. If a command fails, read the error carefully and fix the root cause —
   don't guess repeatedly.
4. When the task is complete and verified, summarize what you changed and
   stop calling tools.
5. Never run destructive commands (rm -rf, force-push, etc).
"""


def run_agent(user_goal: str, max_turns: int = 20, verbose: bool = True) -> str:
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    messages = [{"role": "user", "content": user_goal}]

    for turn in range(1, max_turns + 1):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        # Print any reasoning/text the model produced this turn
        if verbose:
            for block in response.content:
                if block.type == "text" and block.text.strip():
                    print(f"\n[turn {turn}] Claude: {block.text.strip()}")

        if response.stop_reason != "tool_use":
            final_text = "\n".join(
                b.text for b in response.content if b.type == "text"
            )
            return final_text

        # Execute every tool call this turn and collect results
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                if verbose:
                    print(f"[turn {turn}] -> {block.name}({block.input})")
                result = execute_tool(block.name, block.input)
                if verbose:
                    preview = result if len(result) < 300 else result[:300] + "...(truncated)"
                    print(f"[turn {turn}] <- {preview}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "user", "content": tool_results})

    return "Stopped: reached max_turns without finishing. Consider raising max_turns."
