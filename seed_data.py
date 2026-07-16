"""Seed realistic sample data for VibeRails (English)."""
import urllib.request, json

API = "http://localhost:8000"


def _request(path, data, method="POST"):
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(data).encode() if data else None,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    return json.loads(urllib.request.urlopen(req).read())


def post(path, data):
    return _request(path, data, "POST")


def put(path, data):
    return _request(path, data, "PUT")


# ===== Team Members =====
m1 = post("/members/", {"name": "Zhang Ming", "role": "owner"})["member_id"]
m2 = post("/members/", {"name": "Li Ting", "role": "member"})["member_id"]
m3 = post("/members/", {"name": "Wang Hao", "role": "member"})["member_id"]
m4 = post("/members/", {"name": "Chen Xue", "role": "member"})["member_id"]
print(f"Members: Zhang Ming({m1}), Li Ting({m2}), Wang Hao({m3}), Chen Xue({m4})")

# ===== Scope Patterns =====
put(f"/contracts/scopes/{m1}", {"patterns": ["src/server/**", "cli/**", "docker/**"]})
put(f"/contracts/scopes/{m2}", {"patterns": ["web/**", "assets/**"]})
put(f"/contracts/scopes/{m3}", {"patterns": ["src/scanner/**", "src/sync/**", "tests/**"]})
put(f"/contracts/scopes/{m4}", {"patterns": ["docs/**", "*.md", ".github/**"]})

# ===== Locked Modules =====
post("/contracts/locked", {"pattern": "src/core/**", "reason": "Core library — requires team review for any change"})
post("/contracts/locked", {"pattern": "server/database.py", "reason": "Database schema changes require a migration script"})
post("/contracts/locked", {"pattern": "pyproject.toml", "reason": "Dependency versions managed by the owner only"})

# ===== Global Standards =====
post("/contracts/standards", {
    "scope": "global", "category": "naming",
    "content": "## Naming Conventions\n\n- **Functions**: `snake_case`\n- **Classes**: `PascalCase`\n- **Constants**: `UPPER_SNAKE_CASE`\n- **Files**: `snake_case.py`\n- **API routes**: lowercase with hyphens `/api/v1/user-profiles`"
})
post("/contracts/standards", {
    "scope": "global", "category": "error-handling",
    "content": "## Error Handling\n\n1. All public functions MUST document raised exceptions or return a `Result` type\n2. API errors follow `{\"detail\": \"human-readable message\"}`\n3. Never swallow exceptions — always `logging.error()` at minimum\n4. External service calls must have a timeout (default 30s)"
})
post("/contracts/standards", {
    "scope": "global", "category": "testing",
    "content": "## Testing Requirements\n\n- Every new feature must include unit tests\n- Coverage targets: core ≥ 90%, UI layer ≥ 70%\n- Naming: `test_{function}_{scenario}`\n- Every PR must pass CI tests before merging"
})
post("/contracts/standards", {
    "scope": "global", "category": "commit",
    "content": "## Git Commit Convention\n\nFollow Conventional Commits:\n\n| Type     | Usage           |\n|----------|----------------|\n| `feat:`  | New feature    |\n| `fix:`   | Bug fix        |\n| `docs:`  | Documentation  |\n| `refactor:` | Code refactor |\n| `test:`  | Tests          |\n| `chore:` | Build/tooling  |\n\nExamples:\n```\nfeat(auth): implement JWT refresh token flow\nfix(api): handle null pointer in user serializer\n```"
})

# ===== Personal Standards (Weekly Goals) =====
post("/contracts/standards", {
    "scope": str(m2), "category": "goal",
    "content": "## This Week\n\nComplete dark mode toggle for the Web UI\n- [x] CSS variable architecture\n- [ ] Dark mode toggle button\n- [ ] localStorage persistence\n- [ ] Component compatibility testing"
})
post("/contracts/standards", {
    "scope": str(m3), "category": "goal",
    "content": "## This Week\n\nOptimize interface scanner performance\n- [ ] Incremental parsing for large files (>5000 lines)\n- [ ] Add async scanning support\n- [ ] Fix method signature extraction for nested classes"
})
post("/contracts/standards", {
    "scope": str(m4), "category": "goal",
    "content": "## This Week\n\nDraft developer documentation site\n- [ ] Installation & deployment guide\n- [ ] API reference documentation\n- [ ] CLI usage tutorial\n- [ ] Contributor guidelines"
})

# ===== Features =====
f1 = post("/features/", {"id": None, "name": "User Authentication", "description": "JWT-based registration, login, token refresh, and role-based access control (owner/member). Includes session management and secure password handling.", "status": "stable", "owner_id": m1})["id"]
f2 = post("/features/", {"id": None, "name": "Contract Sync Engine", "description": "Sync team contracts (ownership scopes, coding standards, locked modules) from server to local .cursor/rules/ directory. Supports incremental updates and conflict detection.", "status": "stable", "owner_id": m3})["id"]
f3 = post("/features/", {"id": None, "name": "Interface Scanner", "description": "AST-based Python interface discovery tool. Recursively scans source code, extracts public function signatures, uploads to registry, and auto-deprecates removed interfaces.", "status": "stable", "owner_id": m3})["id"]
f4 = post("/features/", {"id": None, "name": "Web Management UI", "description": "Alpine.js single-page admin panel. Member management, standards editor, interface browser, feature workspace with dark mode and responsive layout.", "status": "stable", "owner_id": m2})["id"]
f5 = post("/features/", {"id": None, "name": "AI Chat Assistant", "description": "Per-feature AI discussion room. Supports multiple AI providers (Anthropic / OpenAI / DeepSeek / Qwen) for team requirement discussions and design reviews.", "status": "in_progress", "owner_id": m1})["id"]
f6 = post("/features/", {"id": None, "name": "Issue Tracking Board", "description": "Lightweight issue tracker with status workflow, assignee management, threaded comments, and optional feature association.", "status": "in_progress", "owner_id": m2})["id"]
f7 = post("/features/", {"id": None, "name": "CLI Enhancement", "description": "Interactive init wizard, colorized output, progress bars, and shell auto-completion for the viberails CLI.", "status": "planned", "owner_id": m3})["id"]

# ===== Issues =====
i1 = post("/issues/", {"title": "Blank screen on expired JWT", "description": "Steps to reproduce:\n1. Open the app and wait for login\n2. Manually clear the token from localStorage\n3. Refresh the page\n\nActual: White screen with JSON parse error in console\nExpected: Redirect to login page\n\nRoot cause: api() method does not handle 401 responses.", "status": "open", "assignee_id": m1})["id"]
post(f"/issues/{i1}/comments", {"content": "Add a 401 interceptor in the api() method — clear token and redirect to /login."})
post(f"/issues/{i1}/comments", {"content": "Fixed in PR #128. Now shows a toast 'Session expired' and redirects automatically."})

post("/issues/", {"title": "SQLite connection pool exhausted under load", "description": "Load test shows connection pool exhaustion at 50 concurrent requests.\nCurrent: aiosqlite default pool (5 connections)\nSuggested: increase to 20, add request queuing. Long-term: migrate to PostgreSQL.", "status": "in_progress", "assignee_id": m3})

i3 = post("/issues/", {"title": "Admin cannot delete team members", "description": "Clicking 'Remove' in team settings returns 403 for admin users.\nLocation: server/routes/members.py:85\nCondition: `role === 'owner'` is too restrictive — members with manage permission should also be able to delete non-owner members.", "status": "open", "assignee_id": m1, "feature_id": f1})["id"]
post(f"/issues/{i3}/comments", {"content": "Added a can_delete() helper in delete_member(). PR #132 ready for review."})

post("/issues/", {"title": "viberails sync silent failure on network error", "description": "When running viberails sync without network connectivity, the terminal prints 'Synced' but the .mdc file is not updated. Needs a connectivity check before syncing.", "status": "open", "assignee_id": m3, "feature_id": f2})

post("/issues/", {"title": "Chat messages duplicated on rapid click", "description": "Double-clicking the Send button sends the same message twice, and the AI replies twice.\nFix: disable the button while sending, or add debounce to sendChatMessage().", "status": "open", "assignee_id": m2, "feature_id": f5})

i6 = post("/issues/", {"title": "Code blocks unreadable in dark mode", "description": "Markdown code blocks in standards preview use a light background even in dark mode.\nNeed to add `[data-theme='dark']` styles for `pre` and `code` elements.", "status": "resolved", "assignee_id": m2, "feature_id": f4})["id"]
post(f"/issues/{i6}/comments", {"content": "Fixed by adding dark mode CSS for pre/code with dark background and light text. Commit 3a7e9f2."})

post("/issues/", {"title": "Write deployment & operations guide", "description": "Create a standardized deployment guide covering:\n- Docker Compose setup\n- Environment variable reference\n- Logging & monitoring setup\n- Backup & restore procedures\n- Troubleshooting FAQ", "status": "closed", "assignee_id": m4})

print("\nAll data created successfully!")
print(f"  Members:   {m1} Zhang Ming, {m2} Li Ting, {m3} Wang Hao, {m4} Chen Xue")
print(f"  Features:  7 (stable:4, in_progress:2, planned:1)")
print(f"  Issues:    7 (open:4, in_progress:1, resolved:1, closed:1)")
print(f"  Standards: 4 global + 3 personal")
print(f"  Locked:    3 modules")
