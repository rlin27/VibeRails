"""Click entrypoint for the VibeRails CLI."""

import click

from cli.scanner import scanner
from cli.sync import sync


@click.group()
def cli() -> None:
    """VibeRails command line tools."""


cli.add_command(sync)
cli.add_command(scanner)


if __name__ == "__main__":
    cli()
