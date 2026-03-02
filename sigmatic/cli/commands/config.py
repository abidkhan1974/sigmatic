"""sigmatic config command group."""

import asyncio

import click
from rich.console import Console
from rich.panel import Panel

console = Console()


@click.group(name="config")
def config_cmd() -> None:
    """View and manage Sigmatic configuration."""
    pass


@config_cmd.command("create-key")
@click.option("--name", prompt="Key name", help="Label for this API key (e.g. 'dev', 'ci')")
def create_key(name: str) -> None:
    """Generate a new API key and store it in the database.

    The raw key is displayed once — save it immediately.
    """

    async def _run() -> tuple[str, str]:
        from sigmatic.server.database import AsyncSessionLocal
        from sigmatic.server.services.api_key_service import create_api_key

        async with AsyncSessionLocal() as session:
            raw_key, record = await create_api_key(session, name)
            return raw_key, record.id

    try:
        raw_key, key_id = asyncio.run(_run())
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        console.print("[dim]Is the database running? Check DATABASE_URL in your .env[/dim]")
        raise SystemExit(1) from exc

    console.print(Panel.fit(
        f"[bold green]API key created[/bold green]\n\n"
        f"Name : [cyan]{name}[/cyan]\n"
        f"ID   : [dim]{key_id}[/dim]\n\n"
        f"[bold yellow]Key (shown once — save it now):[/bold yellow]\n"
        f"[white]{raw_key}[/white]",
        title="sigmatic config create-key",
        border_style="green",
    ))
    console.print("\nUse it in requests:")
    console.print(f"  [dim]curl -H 'X-API-Key: {raw_key}' http://localhost:8000/v1/signals[/dim]")


@config_cmd.command("list-keys")
def list_keys() -> None:
    """List all API keys (names and IDs, not the raw keys)."""

    async def _run() -> list[dict]:  # type: ignore[type-arg]
        from sqlalchemy import select

        from sigmatic.server.database import AsyncSessionLocal
        from sigmatic.server.models.api_key import APIKey

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(APIKey).order_by(APIKey.created_at.desc())
            )
            keys = result.scalars().all()
            return [
                {
                    "id": k.id,
                    "name": k.name,
                    "status": k.status,
                    "created_at": str(k.created_at)[:19],
                    "last_used_at": str(k.last_used_at)[:19] if k.last_used_at else "never",
                }
                for k in keys
            ]

    try:
        rows = asyncio.run(_run())
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1) from exc

    if not rows:
        console.print("[dim]No API keys found. Run: sigmatic config create-key[/dim]")
        return

    from rich.table import Table

    table = Table(title="API Keys", show_header=True, header_style="bold cyan")
    for col in ("name", "status", "created_at", "last_used_at", "id"):
        table.add_column(col)
    for row in rows:
        status_style = "green" if row["status"] == "active" else "red"
        table.add_row(
            row["name"],
            f"[{status_style}]{row['status']}[/{status_style}]",
            row["created_at"],
            row["last_used_at"],
            f"[dim]{row['id']}[/dim]",
        )
    console.print(table)
