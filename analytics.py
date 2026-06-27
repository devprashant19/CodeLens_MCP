import json
import os
from collections import defaultdict
from rich.console import Console
from rich.table import Table

LOG_FILE = "logs/tool_calls.jsonl"

def analyze_logs():
    console = Console()
    
    if not os.path.exists(LOG_FILE):
        console.print(f"[red]Log file {LOG_FILE} not found.[/red]")
        return
        
    total_calls = 0
    success_calls = 0
    
    # tool_name -> list of latencies
    latencies = defaultdict(list)
    # tool_name -> list of successes
    successes = defaultdict(list)
    
    # Track common queries (specifically for semantic_code_search)
    queries = defaultdict(int)
    
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
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
    console.print(f"\n[bold]Overall Metrics[/bold]")
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

if __name__ == "__main__":
    analyze_logs()
