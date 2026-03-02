"""sigmatic sources command group."""

import asyncio
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.group(name="sources")
def sources_cmd() -> None:
    """Manage signal sources (webhook / API / internal)."""
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fmt(val: object) -> str:
    if val is None:
        return "[dim]-[/dim]"
    return str(val)


def _status_style(status: str) -> str:
    return f"[green]{status}[/green]" if status == "active" else f"[yellow]{status}[/yellow]"


# ---------------------------------------------------------------------------
# sigmatic sources list
# ---------------------------------------------------------------------------


@sources_cmd.command("list")
def list_sources() -> None:
    """List all registered sources."""

    async def _run() -> list[Any]:
        from sigmatic.server.database import AsyncSessionLocal
        from sigmatic.server.services.source_manager import list_sources as svc_list

        async with AsyncSessionLocal() as session:
            return await svc_list(session)

    try:
        sources = asyncio.run(_run())
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1) from exc

    if not sources:
        console.print("[dim]No sources found. Run: sigmatic sources create[/dim]")
        return

    table = Table(title=f"Sources ({len(sources)})", show_header=True, header_style="bold cyan")
    table.add_column("name")
    table.add_column("type")
    table.add_column("adapter")
    table.add_column("status")
    table.add_column("trust")
    table.add_column("source_id", style="dim")

    for s in sources:
        table.add_row(
            str(s.name),  # type: ignore[attr-defined]
            str(s.type),  # type: ignore[attr-defined]
            str(s.schema_adapter),  # type: ignore[attr-defined]
            _status_style(str(s.status)),  # type: ignore[attr-defined]
            f"{s.trust_score:.2f}" if s.trust_score is not None else "-",  # type: ignore[attr-defined]
            str(s.source_id),  # type: ignore[attr-defined]
        )

    console.print(table)


# ---------------------------------------------------------------------------
# sigmatic sources get
# ---------------------------------------------------------------------------


@sources_cmd.command("get")
@click.argument("source_id")
def get_source(source_id: str) -> None:
    """Show full detail for a single source."""

    async def _run() -> object:
        from sigmatic.server.database import AsyncSessionLocal
        from sigmatic.server.services.source_manager import get_source as svc_get

        async with AsyncSessionLocal() as session:
            return await svc_get(session, source_id)

    try:
        source = asyncio.run(_run())
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1) from exc

    if source is None:
        console.print(f"[red]Source '{source_id}' not found.[/red]")
        raise SystemExit(1)

    lines = [
        f"source_id     : [cyan]{source.source_id}[/cyan]",  # type: ignore[attr-defined]
        f"name          : [bold]{source.name}[/bold]",  # type: ignore[attr-defined]
        f"type          : {source.type}",  # type: ignore[attr-defined]
        f"adapter       : {source.schema_adapter}",  # type: ignore[attr-defined]
        f"status        : {_status_style(str(source.status))}",  # type: ignore[attr-defined]
        f"trust_score   : {_fmt(source.trust_score)}",  # type: ignore[attr-defined]
        f"webhook_token : [dim]{_fmt(source.webhook_token)}[/dim]",  # type: ignore[attr-defined]
    ]
    console.print(Panel.fit("\n".join(lines), title="Source Detail", border_style="cyan"))


# ---------------------------------------------------------------------------
# sigmatic sources create
# ---------------------------------------------------------------------------


@sources_cmd.command("create")
@click.option("--name", prompt="Source name", help="Unique name for the source")
@click.option(
    "--type",
    "source_type",
    type=click.Choice(["webhook", "api", "internal"]),
    prompt="Type",
    help="Source type",
)
@click.option(
    "--adapter",
    default="generic",
    show_default=True,
    help="Schema adapter (generic, tradingview, …)",
)
def create_source(name: str, source_type: str, adapter: str) -> None:
    """Register a new signal source."""

    async def _run() -> object:
        from sigmatic.server.database import AsyncSessionLocal
        from sigmatic.server.schemas.source import SourceCreate
        from sigmatic.server.services.source_manager import create_source as svc_create

        body = SourceCreate(name=name, type=source_type, schema_adapter=adapter)
        async with AsyncSessionLocal() as session:
            return await svc_create(session, body)

    try:
        source = asyncio.run(_run())
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1) from exc

    console.print(Panel.fit(
        f"[bold green]Source created[/bold green]\n\n"
        f"Name          : [cyan]{source.name}[/cyan]\n"  # type: ignore[attr-defined]
        f"ID            : [dim]{source.source_id}[/dim]\n"  # type: ignore[attr-defined]
        f"Type          : {source.type}\n"  # type: ignore[attr-defined]
        f"Adapter       : {source.schema_adapter}\n"  # type: ignore[attr-defined]
        f"\n[bold yellow]Webhook token (use in X-Webhook-Token header):[/bold yellow]\n"
        f"[white]{source.webhook_token}[/white]",  # type: ignore[attr-defined]
        title="sigmatic sources create",
        border_style="green",
    ))


# ---------------------------------------------------------------------------
# sigmatic sources pause / resume
# ---------------------------------------------------------------------------


@sources_cmd.command("pause")
@click.argument("source_id")
def pause_source(source_id: str) -> None:
    """Pause a source (stop accepting new signals)."""
    _set_status(source_id, "paused")


@sources_cmd.command("resume")
@click.argument("source_id")
def resume_source(source_id: str) -> None:
    """Resume a paused source."""
    _set_status(source_id, "active")


def _set_status(source_id: str, status: str) -> None:
    async def _run() -> object:
        from sigmatic.server.database import AsyncSessionLocal
        from sigmatic.server.services.source_manager import set_source_status

        async with AsyncSessionLocal() as session:
            return await set_source_status(session, source_id, status)

    try:
        source = asyncio.run(_run())
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1) from exc

    if source is None:
        console.print(f"[red]Source '{source_id}' not found.[/red]")
        raise SystemExit(1)

    verb = "paused" if status == "paused" else "resumed"
    console.print(f"[green]✓[/green] Source [cyan]{source.name}[/cyan] {verb}.")  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# sigmatic sources delete
# ---------------------------------------------------------------------------


@sources_cmd.command("delete")
@click.argument("source_id")
@click.confirmation_option(prompt="Delete this source and all its signals? This cannot be undone")
def delete_source(source_id: str) -> None:
    """Delete a source (and cascade-deletes its signals)."""

    async def _run() -> bool:
        from sigmatic.server.database import AsyncSessionLocal
        from sigmatic.server.services.source_manager import delete_source as svc_delete

        async with AsyncSessionLocal() as session:
            return await svc_delete(session, source_id)

    try:
        deleted = asyncio.run(_run())
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1) from exc

    if not deleted:
        console.print(f"[red]Source '{source_id}' not found.[/red]")
        raise SystemExit(1)

    console.print(f"[green]✓[/green] Source [dim]{source_id}[/dim] deleted.")
