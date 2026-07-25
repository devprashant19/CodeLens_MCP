import json
import os
from collections import defaultdict
from datetime import UTC, datetime, timedelta

import click
from rich.console import Console
from rich.table import Table

from codelens.config import config


def analyze_logs(days: int | None = None):
    console = Console()

    if not os.path.exists(config.log_file):
        console.print(f"[red]Log file not found at {config.log_file}[/red]")
        return

    cutoff_date = None
    if days is not None:
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        console.print(f"[cyan]Filtering logs to the last {days} days (since {cutoff_date.date()})[/cyan]")

    total_calls = 0
    success_calls = 0

    # tool_name -> list of latencies
    latencies = defaultdict(list)
    # tool_name -> list of successes
    successes = defaultdict(list)

    # Track common queries (specifically for semantic_code_search)
    queries = defaultdict(int)

    with open(config.log_file, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)

                if cutoff_date:
                    ts_str = entry.get("timestamp", "")
                    if ts_str:
                        try:
                            # Parse aware datetime
                            entry_date = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                            if entry_date < cutoff_date:
                                continue
                        except ValueError:
                            pass

                total_calls += 1

                tool_name = entry.get("tool_name", "unknown")
                latency = entry.get("latency_ms", 0)
                success = entry.get("success", False)

                latencies[tool_name].append(latency)
                successes[tool_name].append(success)

                if success:
                    success_calls += 1

                if tool_name == "semantic_code_search":
                    query = entry.get("input_args", {}).get("query")
                    if query:
                        queries[query] += 1
            except json.JSONDecodeError:
                pass

    if total_calls == 0:
        console.print("[yellow]No valid log entries found.[/yellow]")
        return

    # Overall summary
    overall_success_rate = (success_calls / total_calls) * 100
    console.print("\n[bold]Overall Metrics[/bold]")
    console.print(f"Total Calls: {total_calls}")
    console.print(f"Overall Success Rate: {overall_success_rate:.1f}%")

    # Tool breakdown table
    table = Table(title="Tool Metrics")
    table.add_column("Tool Name", style="cyan")
    table.add_column("Calls", justify="right")
    table.add_column("Avg Latency (ms)", justify="right")
    table.add_column("Success Rate", justify="right")

    for tool_name, lats in latencies.items():
        calls = len(lats)
        avg_lat = sum(lats) / calls if calls > 0 else 0
        succ_rate = (sum(successes[tool_name]) / calls) * 100 if calls > 0 else 0
        table.add_row(
            tool_name,
            str(calls),
            f"{avg_lat:.1f}",
            f"{succ_rate:.1f}%"
        )

    console.print("\n")
    console.print(table)

    # Most common queries
    if queries:
        console.print("\n[bold]Top 5 Semantic Queries[/bold]")
        sorted_queries = sorted(queries.items(), key=lambda x: x[1], reverse=True)[:5]
        for q, count in sorted_queries:
            console.print(f"- '{q}' ({count} times)")

@click.command()
@click.option("--days", type=int, default=None, help="Filter to the last N days")
def cli(days):
    """Analyze CodeLens MCP logs."""
    analyze_logs(days=days)

if __name__ == "__main__":
    cli()
