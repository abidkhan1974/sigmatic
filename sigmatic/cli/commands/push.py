"""sigmatic push — manually inject a signal from the CLI.

Useful for testing routing rules and delivery pipelines without
needing a live webhook source.  The signal bypasses all adapters
and goes straight into the DB as status=INGESTED.

Examples
--------
    sigmatic push --symbol AAPL --direction long
    sigmatic push --symbol BTCUSDT --direction short --entry-zone 65000 --confidence 0.9
    sigmatic push --symbol SPY --direction flat --timeframe 1h --strategy manual
"""

import asyncio
from datetime import datetime, timezone

import click
from rich.console import Console
from rich.panel import Panel

console = Console()

_UTC = timezone.utc


@click.command(name="push")
@click.option("--symbol", "-s", required=True, help="Ticker symbol (e.g. AAPL, BTCUSDT)")
@click.option(
    "--direction",
    "-d",
    required=True,
    type=click.Choice(["long", "short", "flat"], case_sensitive=False),
    help="Signal direction",
)
@click.option("--entry-zone", type=float, default=None, help="Entry price / zone midpoint")
@click.option("--stop-distance", type=float, default=None, help="Stop distance in price units")
@click.option("--target", type=float, default=None, help="Target price")
@click.option(
    "--confidence",
    type=click.FloatRange(0.0, 1.0),
    default=None,
    help="Signal confidence 0.0–1.0",
)
@click.option("--timeframe", default=None, help="Timeframe (e.g. 1h, 4h, 1d)")
@click.option("--strategy", "strategy_id", default=None, help="Strategy identifier")
def push_cmd(
    symbol: str,
    direction: str,
    entry_zone: float | None,
    stop_distance: float | None,
    target: float | None,
    confidence: float | None,
    timeframe: str | None,
    strategy_id: str | None,
) -> None:
    """Manually push a pre-normalized signal into the pipeline."""

    async def _run() -> object:
        from sigmatic.server.database import AsyncSessionLocal
        from sigmatic.server.models.base import generate_uuid
        from sigmatic.server.models.signal import Signal
        from sigmatic.server.schemas.signal import NormalizedSignal

        validated = NormalizedSignal(
            symbol=symbol,
            direction=direction.lower(),
            confidence=confidence,
            entry_zone=entry_zone,
            stop_distance=stop_distance,
            target=target,
            strategy_id=strategy_id,
            timeframe=timeframe,
        )
        raw = validated.model_dump_json()

        signal = Signal(
            signal_id=generate_uuid(),
            source_id=None,
            symbol=validated.symbol,
            direction=validated.direction,
            confidence=validated.confidence,
            entry_zone=validated.entry_zone,
            stop_distance=validated.stop_distance,
            target=validated.target,
            strategy_id=validated.strategy_id,
            timeframe=validated.timeframe,
            status="INGESTED",
            raw_payload=raw,
            ingested_at=datetime.now(_UTC),
        )
        async with AsyncSessionLocal() as session:
            session.add(signal)
            await session.commit()
            await session.refresh(signal)
        return signal

    try:
        sig = asyncio.run(_run())
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1) from exc

    fields = {  # type: ignore[attr-defined]
        "signal_id": sig.signal_id,  # type: ignore[attr-defined]
        "symbol": sig.symbol,  # type: ignore[attr-defined]
        "direction": sig.direction,  # type: ignore[attr-defined]
        "entry_zone": sig.entry_zone,  # type: ignore[attr-defined]
        "stop_distance": sig.stop_distance,  # type: ignore[attr-defined]
        "target": sig.target,  # type: ignore[attr-defined]
        "confidence": sig.confidence,  # type: ignore[attr-defined]
        "timeframe": sig.timeframe,  # type: ignore[attr-defined]
        "strategy_id": sig.strategy_id,  # type: ignore[attr-defined]
        "ingested_at": str(sig.ingested_at)[:19],  # type: ignore[attr-defined]
    }

    dir_colours = {"long": "green", "short": "red", "flat": "yellow"}
    dir_style = dir_colours.get(str(sig.direction), "white")  # type: ignore[attr-defined]

    lines = [
        f"[bold green]✓ Signal pushed[/bold green]  "
        f"[bold]{sig.symbol}[/bold] [{dir_style}]{sig.direction}[/{dir_style}]",  # type: ignore[attr-defined]
        "",
        f"  ID        : [dim]{sig.signal_id}[/dim]",  # type: ignore[attr-defined]
    ]
    for k, v in fields.items():
        if k in ("signal_id", "symbol", "direction"):
            continue
        if v is not None:
            lines.append(f"  {k:<12}: {v}")

    console.print(Panel.fit("\n".join(lines), title="sigmatic push", border_style="green"))
    console.print(
        f"\n[dim]sigmatic signals get {sig.signal_id}[/dim]"  # type: ignore[attr-defined]
    )
