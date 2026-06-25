"""Click entrypoint for the VibeRails CLI."""

from __future__ import annotations

import json
from pathlib import Path
from urllib import error, request
import uuid

import click

from cli.scanner import scan_interfaces
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


@cli.command("scan")
@click.option("--upload", is_flag=True, help="Upload scanned interfaces to the server.")
def scan_command(upload: bool) -> None:
    """Scan project interfaces from the configured api_scan patterns."""
    config_path = Path.cwd() / ".vibrails.yml"
    if not config_path.exists():
        click.echo("Missing .vibrails.yml. Please run viberails init first.")
        raise SystemExit(1)

    config = load_config(config_path)
    server = str(config.get("server", "")).rstrip("/")
    member_id = normalize_member_id(config.get("member_id"))
    raw_patterns = config.get("api_scan", [])
    if isinstance(raw_patterns, list):
        api_scan_patterns = [str(pattern) for pattern in raw_patterns]
    elif isinstance(raw_patterns, str) and raw_patterns.strip():
        api_scan_patterns = [raw_patterns.strip()]
    else:
        api_scan_patterns = []

    if not member_id:
        click.echo("Please edit .vibrails.yml and set your member_id first.")
        raise SystemExit(1)

    scanned = scan_interfaces(str(Path.cwd()), api_scan_patterns)
    interfaces = [
        {"file_path": file_path, "signature": signature}
        for file_path, signatures in scanned.items()
        for signature in signatures
    ]

    if not upload:
        click.echo(json.dumps({"interfaces": interfaces}, indent=2))
        return

    body = json.dumps({"interfaces": interfaces}).encode("utf-8")
    upload_request = request.Request(
        f"{server}/contracts/interfaces/upload",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(upload_request) as response:
            result = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise click.ClickException(f"upload failed: HTTP {exc.code}") from exc
    except error.URLError as exc:
        raise click.ClickException(f"failed to reach server: {exc.reason}") from exc

    click.echo(
        "Scan complete. "
        f"{result['inserted']} interfaces inserted, "
        f"{result['deprecated']} deprecated, "
        f"{result['skipped']} skipped."
    )


if __name__ == "__main__":
    cli()
