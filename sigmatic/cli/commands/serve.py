"""sigmatic serve command."""

import click
import uvicorn


@click.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, help="Port to listen on")
@click.option("--reload", is_flag=True, default=False, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool) -> None:
    """Start the Sigmatic server."""
    click.echo(f"Starting Sigmatic server on {host}:{port}")
    uvicorn.run(
        "sigmatic.server.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
