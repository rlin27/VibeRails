"""CLI sync commands."""

import click


@click.command()
def sync() -> None:
    """Sync local rules from the server."""
    click.echo("Sync scaffold is ready. Implementation coming next.")
