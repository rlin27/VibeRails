"""CLI scanner commands."""

import click


@click.command()
def scanner() -> None:
    """Scan the codebase for shared interfaces."""
    click.echo("Scanner scaffold is ready. Implementation coming next.")
