

# 🛤️ VibeRails — Vibe Coding, Without the Chaos

Python
License
Version
Cursor
Status

**A self-hosted team contract engine for vibe coding — define ownership, enforce standards, and sync rules directly into your AI coding tool.**

[Quick Start](#quick-start) • [How It Works](#how-it-works) • [Features](#features) • [Architecture](#architecture) • [Contributing](#contributing)



---

## Why VibeRails?

Vibe coding is fast. Team vibe coding is chaos.

When everyone on your team is using AI to write code simultaneously, you end up with:

- 🔴 **Merge conflicts** — two AIs edited the same file
- 🔴 **Semantic conflicts** — two AIs implemented the same function differently
- 🔴 **Style chaos** — no consistent naming, error handling, or structure
- 🔴 **Duplicate work** — nobody knew the other person already built it
- 🔴 **Boundary violations** — AI rewrote code it had no business touching

The root cause is simple: **your AI doesn't know your team's rules.**

VibeRails fixes that. Define your team contract once, sync it to every developer's AI tool automatically.

---

## Features

- 👤 **Ownership Declaration** — each developer declares which modules they own; AI stays in its lane
- 📋 **Team Standards** — shared coding style, naming conventions, and test requirements injected into every AI session
- 🔍 **Interface Registry** — automatically scans your codebase for public interfaces; AI knows what already exists before it builds anything new
- 🔄 **Dynamic Updates** — standards evolve as the project grows; one sync command keeps everyone current
- 🖥️ **Web UI** — manage your team contract, members, and ownership assignments from a browser
- ⚡ **CLI Sync** — `vibrails sync` writes your personal contract directly into `.cursor/rules/`
- 🐳 **Self-Hosted** — your contract stays on your server; `docker compose up` and you're running
- 👤 **Solo-Friendly** — works just as well for individual developers who want consistent AI behavior

---

## Roadmap

-[x] Project scaffold + architecture design
- [ ] Server: member management + contract storage
- [ ] Server: interface registry auto-scan
- [ ] CLI: `vibrails init` + `vibrails sync`
- [ ] `.mdc` file generation for Cursor
- [ ] Web UI: member dashboard + contract editor
- [ ] Docker Compose deployment
- [ ] Support for additional IDE targets (Claude Code, GitHub Copilot)
- [ ] AI-powered code review *(post-MVP)*
- [ ] AI-powered test generation *(post-MVP)*


---

## License

MIT License — see [LICENSE](LICENSE) for details.

---



Built with 🛤️ VibeRails by [Lin Rui](https://rlin27.github.io)

*Because your AI should know the rules before it writes the code.*

