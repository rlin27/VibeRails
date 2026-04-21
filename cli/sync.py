"""Helpers for syncing VibeRails rules from the server."""

from __future__ import annotations

import json
from pathlib import Path
from urllib import error, request


def _parse_scalar(value: str) -> str:
    value = value.strip()
    if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) >= 2:
        return value[1:-1]
    return value


def load_config(config_path: Path) -> dict[str, object]:
    """Load the small VibeRails YAML config format."""
    config: dict[str, object] = {"api_scan": []}
    current_list_key: str | None = None

    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if line.startswith("  - ") and current_list_key is not None:
            value = _parse_scalar(line.split("- ", 1)[1])
            config.setdefault(current_list_key, [])
            assert isinstance(config[current_list_key], list)
            config[current_list_key].append(value)
            continue

        current_list_key = None
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            config[key] = _parse_scalar(value)
        else:
            config[key] = ""
            if key == "api_scan":
                config[key] = []
                current_list_key = key

    return config


def normalize_member_id(value: object) -> str:
    """Normalize member_id values from config files or YAML parsers."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _render_patterns(patterns: list[str]) -> str:
    if not patterns:
        return "- No module scopes defined yet."
    return "\n".join(f"- {pattern}" for pattern in patterns)


def _render_locked_modules(locked_modules: list[dict[str, str]]) -> str:
    if not locked_modules:
        return "- No locked modules defined."
    return "\n".join(
        f"- {item['pattern']} — {item['reason']}" for item in locked_modules
    )


def _render_standards(standards: list[dict[str, str]]) -> str:
    if not standards:
        return "- No personal standards defined yet."
    return "\n\n".join(item["content"] for item in standards)


def _render_global_standards(standards: list[dict[str, str]]) -> str:
    if not standards:
        return "- No global standards defined yet."
    return "\n\n".join(item["content"] for item in standards)


def render_contract_markdown(payload: dict[str, object]) -> str:
    """Render sync payload JSON into an .mdc rules file."""
    member = payload.get("member", {})
    patterns = payload.get("patterns", [])
    if isinstance(payload.get("scope"), dict):
        patterns = payload["scope"].get("patterns", patterns)  # type: ignore[index]
    locked_modules = payload.get("locked_modules", [])
    global_standards = payload.get("global_standards", [])
    personal_standards = payload.get("personal_standards", [])
    if isinstance(payload.get("standards"), dict):
        standards = payload["standards"]  # type: ignore[assignment]
        global_standards = standards.get("global", global_standards)
        personal_standards = standards.get("personal", personal_standards)

    return f"""---
description: VibeRails team contract
alwaysApply: true
---

# Developer Identity
- Name: {member.get("name", "")}
- Role: {member.get("role", "")}

# Your Modules (You can only modify these)
{_render_patterns(patterns if isinstance(patterns, list) else [])}

# Locked Modules (Do Not Touch)
{_render_locked_modules(locked_modules if isinstance(locked_modules, list) else [])}

# Global Standards
{_render_global_standards(global_standards if isinstance(global_standards, list) else [])}

# Your Personal Standards
{_render_standards(personal_standards if isinstance(personal_standards, list) else [])}
"""


def sync(project_dir: Path | None = None) -> Path:
    """Fetch contract data and write it to the Cursor rules directory."""
    base_dir = project_dir or Path.cwd()
    config = load_config(base_dir / ".vibrails.yml")
    server = str(config.get("server", "")).rstrip("/")
    member_id = normalize_member_id(config.get("member_id"))
    sync_url = f"{server}/sync/{member_id}"

    try:
        with request.urlopen(sync_url) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise RuntimeError(f"sync request failed: HTTP {exc.code}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"failed to reach server: {exc.reason}") from exc

    rules_dir = base_dir / ".cursor" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    output_path = rules_dir / "vibrails.mdc"
    output_path.write_text(render_contract_markdown(payload), encoding="utf-8")
    return output_path
