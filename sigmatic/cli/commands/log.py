"""sigmatic log — signal activity log viewer.

Shows ingested signals as a timestamped log stream.  With --follow,
polls for new signals every few seconds like `tail -f`.

Examples
--------
    sigmatic log                   # last 20 signals
    sigmatic log -n 50             # last 50 signals
    sigmatic log --symbol AAPL     # filter to one symbol
    sigmatic log --follow          # live tail (Ctrl-C to stop)
    sigmatic log --follow --symbol BTCUSDT
"""

import asyncio
import time
from typing import Any

import click
from rich.console import Console

console = Console()

_STATUS_ICONS = {
    "INGESTED": "[green]●[/green]",
    "ADAPTER_ERROR": "[red]✗[/red]",
    "VALIDATION_ERROR": "[red]✗[/red]",
    "SCORED": "[cyan]◆[/cyan]",
    "ROUTED": "[blue]→[/blue]",
}

_DIR_STYLES = {
    "long": "[green]↑ long[/green]",
    "short": "[red]↓ short[/red]",
    "flat": "[yellow]— flat[/yellow]",
}


def _icon(status: str) -> str:
    return _STATUS_ICONS.get(status, "[dim]?[/dim]")


def _dir_label(direction: str) -> str:
    return _DIR_STYLES.get(direction, direction)


def _fmt_signal(s: Any, show_id: bool = True) -> str:
    ts = str(s.ingested_at)[:19] if s.ingested_at else "          "
    symbol = f"[bold]{s.symbol:<10}[/bold]"
    direction = _dir_label(str(s.direction))
    icon = _icon(str(s.status))
    entry = f" @ {s.entry_zone:.2f}" if s.entry_zone is not None else ""
    conf = f" [{s.confidence:.0%}]" if s.confidence is not None else ""
    sid = f"  [dim]{str(s.signal_id)[:8]}…[/dim]" if show_id else ""
    source = f"  [dim]src:{str(s.source_id)[:8]}…[/dim]" if s.source_id else ""
    return f"{icon} {ts}  {symbol}  {direction}{entry}{conf}{sid}{source}"


async def _fetch_signals(
    symbol: str | None,
    source_id: str | None,
    limit: int,
    after_signal_id: str | None = None,
) -> list[Any]:
    from sqlalchemy import select

    from sigmatic.server.database import AsyncSessionLocal
    from sigmatic.server.models.signal import Signal

    async with AsyncSessionLocal() as session:
        query = select(Signal)
        if symbol:
            query = query.where(Signal.symbol == symbol.strip().upper())
        if source_id:
            query = query.where(Signal.source_id == source_id)
        query = query.order_by(Signal.ingested_at.desc()).limit(limit)
        result = await session.execute(query)
        signals = list(result.scalars().all())
        # Reverse so oldest is first (log-style chronological display)
        signals.reverse()
        return signals


@click.command(name="log")
@click.option("--symbol", "-s", default=None, help="Filter by symbol")
@click.option("--source", default=None, help="Filter by source ID")
@click.option("--limit", "-n", default=20, show_default=True, help="Number of entries to show")
@click.option(
    "--follow",
    "-f",
    is_flag=True,
    default=False,
    help="Poll for new signals (Ctrl-C to stop)",
)
@click.option(
    "--interval",
    default=2.0,
    show_default=True,
    help="Poll interval in seconds (with --follow)",
)
def log_cmd(
    symbol: str | None,
    source: str | None,
    limit: int,
    follow: bool,
    interval: float,
) -> None:
    """Show the signal activity log."""

    async def _initial() -> list[Any]:
        return await _fetch_signals(symbol, source, limit)

    try:
        signals = asyncio.run(_initial())
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1) from exc

    if not signals:
        console.print("[dim]No signals found.[/dim]")
        if not follow:
            return

    header = "[bold cyan]sigmatic log[/bold cyan]"
    if symbol:
        header += f"  symbol=[bold]{symbol.upper()}[/bold]"
    if source:
        header += f"  source=[dim]{source[:12]}…[/dim]"
    console.print(header)
    console.print("[dim]" + "─" * 72 + "[/dim]")

    # Print initial batch
    seen_ids: set[str] = set()
    for s in signals:
        console.print(_fmt_signal(s))
        seen_ids.add(s.signal_id)

    if not follow:
        console.print(f"\n[dim]{len(signals)} signal(s). Run with --follow to tail.[/dim]")
        return

    # Live tail — poll for new signals
    console.print("\n[dim]Watching for new signals (Ctrl-C to stop)…[/dim]")
    try:
        while True:
            time.sleep(interval)

            async def _poll() -> list[Any]:
                # Fetch recent signals with a slightly larger window to catch all new ones
                return await _fetch_signals(symbol, source, limit=50)

            try:
                fresh = asyncio.run(_poll())
            except Exception:
                continue

            for s in fresh:
                if s.signal_id not in seen_ids:
                    console.print(_fmt_signal(s))
                    seen_ids.add(s.signal_id)

    except (KeyboardInterrupt, SystemExit):
        console.print("\n[dim]Stopped.[/dim]")
