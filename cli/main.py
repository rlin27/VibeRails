"""Click entrypoint for the VibeRails CLI."""

from __future__ import annotations

from pathlib import Path
import uuid

import click

from cli.sync import load_config, normalize_member_id, sync as run_sync


@click.group()
def cli() -> None:
    """VibeRails command line tools."""


@cli.command("init")
def init_command() -> None:
    """Initialize VibeRails config in the current directory."""
    config_path = Path.cwd() / ".vibrails.yml"
    if config_path.exists() and not click.confirm(
        ".vibrails.yml already exists. Overwrite it?",
        default=False,
    ):
        return

    config_path.write_text(
        "\n".join(
            [
                f"project_id: {uuid.uuid4()}",
                "server: http://localhost:8000",
                "member_id:",
                "api_scan:",
                '  - "src/**/api.py"',
                '  - "src/**/__init__.py"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    click.echo(
        "VibeRails initialized. Please edit .vibrails.yml to set your member_id."
    )


@cli.command("sync")
def sync_command() -> None:
    """Sync local rules from the VibeRails server."""
    config_path = Path.cwd() / ".vibrails.yml"
    if not config_path.exists():
        click.echo("Missing .vibrails.yml. Please run viberails init first.")
        raise SystemExit(1)

    config = load_config(config_path)
    member_id = normalize_member_id(config.get("member_id"))
    if not member_id:
        click.echo("Please edit .vibrails.yml and set your member_id first.")
        raise SystemExit(1)

    try:
        run_sync(Path.cwd())
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo("Synced. Your contract is ready at .cursor/rules/vibrails.mdc")


if __name__ == "__main__":
    cli()
