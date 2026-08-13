"""
main.py
CLI entrypoint. Usage:
    python main.py solve "Fix the failing test in tests/test_auth.py"
    python main.py solve "Add input validation to app/api.py" --max-turns 25
"""

import typer
from agent import run_agent

app = typer.Typer()


@app.command()
def solve(
    goal: str = typer.Argument(..., help="The coding task for the agent to complete"),
    max_turns: int = typer.Option(20, help="Max agent loop iterations"),
):
    """Run the autonomous coding agent on a given goal."""
    print(f"Goal: {goal}\n{'-'*60}")
    result = run_agent(goal, max_turns=max_turns)
    print(f"\n{'='*60}\nFINAL RESULT:\n{result}")


if __name__ == "__main__":
    app()
