"""sigmatic signals command group."""

import asyncio
from typing import Any

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group(name="signals")
def signals_cmd() -> None:
    """Query and inspect ingested signals."""
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fmt(val: object) -> str:
    if val is None:
        return "[dim]-[/dim]"
    return str(val)


def _direction_style(direction: str) -> str:
    styles = {"long": "green", "short": "red", "flat": "yellow"}
    style = styles.get(direction, "white")
    return f"[{style}]{direction}[/{style}]"


def _status_style(status: str) -> str:
    if status == "INGESTED":
        return f"[green]{status}[/green]"
    if status in ("ADAPTER_ERROR", "VALIDATION_ERROR"):
        return f"[red]{status}[/red]"
    return status


# ---------------------------------------------------------------------------
# sigmatic signals list
# ---------------------------------------------------------------------------


@signals_cmd.command("list")
@click.option("--symbol", "-s", default=None, help="Filter by symbol (e.g. AAPL)")
@click.option("--source", default=None, help="Filter by source ID")
@click.option("--status", default=None, help="Filter by status (INGESTED, ADAPTER_ERROR, …)")
@click.option("--direction", "-d", default=None, help="Filter by direction (long/short/flat)")
@click.option("--limit", "-n", default=20, show_default=True, help="Number of results")
@click.option("--offset", default=0, show_default=True, help="Page offset")
def list_signals(
    symbol: str | None,
    source: str | None,
    status: str | None,
    direction: str | None,
    limit: int,
    offset: int,
) -> None:
    """List recent signals, newest first."""

    async def _run() -> list[Any]:
        from sigmatic.server.database import AsyncSessionLocal
        from sigmatic.server.services.signal_service import list_signals as svc_list

        async with AsyncSessionLocal() as session:
            return await svc_list(
                session,
                symbol=symbol,
                source_id=source,
                status=status,
                direction=direction,
                limit=limit,
                offset=offset,
            )

    try:
        signals = asyncio.run(_run())
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1) from exc

    if not signals:
        console.print("[dim]No signals found.[/dim]")
        return

    table = Table(title=f"Signals (showing {len(signals)})", show_header=True, header_style="bold cyan")
    table.add_column("signal_id", style="dim", max_width=12)
    table.add_column("symbol")
    table.add_column("direction")
    table.add_column("status")
    table.add_column("entry_zone")
    table.add_column("confidence")
    table.add_column("timeframe")
    table.add_column("ingested_at")

    for s in signals:
        sid = str(s.signal_id)[:8] + "…"  # type: ignore[attr-defined]
        ingested = str(s.ingested_at)[:19] if s.ingested_at else "-"  # type: ignore[attr-defined]
        table.add_row(
            sid,
            str(s.symbol),  # type: ignore[attr-defined]
            _direction_style(str(s.direction)),  # type: ignore[attr-defined]
            _status_style(str(s.status)),  # type: ignore[attr-defined]
            _fmt(s.entry_zone),  # type: ignore[attr-defined]
            _fmt(s.confidence),  # type: ignore[attr-defined]
            _fmt(s.timeframe),  # type: ignore[attr-defined]
            ingested,
        )

    console.print(table)


# ---------------------------------------------------------------------------
# sigmatic signals get
# ---------------------------------------------------------------------------


@signals_cmd.command("get")
@click.argument("signal_id")
def get_signal(signal_id: str) -> None:
    """Show full detail for a single signal."""

    async def _run() -> object:
        from sigmatic.server.database import AsyncSessionLocal
        from sigmatic.server.services.signal_service import get_signal as svc_get

        async with AsyncSessionLocal() as session:
            return await svc_get(session, signal_id)

    try:
        signal = asyncio.run(_run())
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1) from exc

    if signal is None:
        console.print(f"[red]Signal '{signal_id}' not found.[/red]")
        raise SystemExit(1)

    from rich.panel import Panel

    lines = [
        f"signal_id  : [cyan]{signal.signal_id}[/cyan]",  # type: ignore[attr-defined]
        f"source_id  : {_fmt(signal.source_id)}",  # type: ignore[attr-defined]
        f"symbol     : [bold]{signal.symbol}[/bold]",  # type: ignore[attr-defined]
        f"direction  : {_direction_style(str(signal.direction))}",  # type: ignore[attr-defined]
        f"status     : {_status_style(str(signal.status))}",  # type: ignore[attr-defined]
        f"entry_zone : {_fmt(signal.entry_zone)}",  # type: ignore[attr-defined]
        f"stop_dist  : {_fmt(signal.stop_distance)}",  # type: ignore[attr-defined]
        f"target     : {_fmt(signal.target)}",  # type: ignore[attr-defined]
        f"confidence : {_fmt(signal.confidence)}",  # type: ignore[attr-defined]
        f"timeframe  : {_fmt(signal.timeframe)}",  # type: ignore[attr-defined]
        f"strategy   : {_fmt(signal.strategy_id)}",  # type: ignore[attr-defined]
        f"ingested   : {_fmt(signal.ingested_at)}",  # type: ignore[attr-defined]
    ]
    if signal.metadata_:  # type: ignore[attr-defined]
        import json
        lines.append(f"metadata   : {json.dumps(signal.metadata_, indent=2)}")  # type: ignore[attr-defined]

    console.print(Panel.fit("\n".join(lines), title="Signal Detail", border_style="cyan"))
