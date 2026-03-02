"""Sigmatic CLI entry point."""

import click

from sigmatic.cli.commands.config import config_cmd
from sigmatic.cli.commands.log import log_cmd
from sigmatic.cli.commands.push import push_cmd
from sigmatic.cli.commands.routes import routes_cmd
from sigmatic.cli.commands.serve import serve
from sigmatic.cli.commands.signals import signals_cmd
from sigmatic.cli.commands.sources import sources_cmd
from sigmatic.cli.commands.stats import stats_cmd
from sigmatic.cli.commands.watch import watch_cmd


@click.group()
@click.version_option(version="0.1.0", prog_name="sigmatic")
def cli() -> None:
    """Sigmatic: Signal aggregation & routing infrastructure."""
    pass


cli.add_command(serve)
cli.add_command(signals_cmd, name="signals")
cli.add_command(sources_cmd, name="sources")
cli.add_command(routes_cmd, name="routes")
cli.add_command(push_cmd, name="push")
cli.add_command(watch_cmd, name="watch")
cli.add_command(log_cmd, name="log")
cli.add_command(stats_cmd, name="stats")
cli.add_command(config_cmd, name="config")
