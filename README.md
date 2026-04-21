<div align="center">

<img src="assets/viberails_logo.png" alt="VibeRails" width="480"/>

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-0.1.0-orange)
![Cursor](https://img.shields.io/badge/Cursor-Native_Support-purple)
![Status](https://img.shields.io/badge/Status-Active_Development-yellow)

**A self-hosted team contract engine for vibe coding — define ownership, enforce standards, and sync rules directly into your AI coding tool.**

</div>

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
- 🖥️ **Web UI** — manage your team contract, members, and ownership from a browser
- ⚡ **CLI Sync** — `viberails sync` writes your personal contract directly into `.cursor/rules/`
- 🐳 **Self-Hosted** — your contract stays on your server; `docker compose up` and you're running
- 👤 **Solo-Friendly** — works just as well for individual developers who want consistent AI behavior

---

## Roadmap

- [x] Project scaffold + architecture design
- [x] Server: member management + contract storage
- [x] Server: sync API
- [x] CLI: `viberails init` + `viberails sync`
- [x] `.mdc` file generation for Cursor
- [ ] Server: interface registry auto-scan
- [ ] Web UI: member dashboard + contract editor
- [ ] Docker Compose deployment
- [ ] Support for additional IDE targets (Claude Code, GitHub Copilot)
- [ ] AI-powered code review *(post-MVP)*
- [ ] AI-powered test generation *(post-MVP)*

---

<div align="center">

Built with by [Lin Rui](https://rlin27.github.io)

*Because your AI should know the rules before it writes the code.*

</div>