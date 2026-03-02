"""CLI output formatters: human-readable, JSON, and table."""

import json
from typing import Any

from rich.console import Console
from rich.table import Table

console = Console()


def print_json(data: Any) -> None:
    """Print data as formatted JSON."""
    console.print_json(json.dumps(data))


def print_table(rows: list[dict[str, Any]], title: str = "") -> None:
    """Print data as a rich table."""
    if not rows:
        console.print("[dim]No results.[/dim]")
        return
    table = Table(title=title, show_header=True, header_style="bold cyan")
    for col in rows[0]:
        table.add_column(col)
    for row in rows:
        table.add_row(*[str(v) for v in row.values()])
    console.print(table)
