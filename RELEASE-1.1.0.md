# 1.1.0 — independent code review plan

11 November 2026.

Adds one shared `hire-code-review` skill for Claude Code and Codex. It verifies
the current public Git repository and previews a free Speedbot Hire plan for
one independent reviewer. The user reviews the scope and terms before deciding
whether to authorize publication or payment separately.

## Verification

The package checks and Claude Code's native manifest validator passed. An
isolated MCP fixture used Speedbot's Hire schema and planner with the skill's
example. It returned a voluntary Work draft with read-only planning and no
publication authorization. The fixture created zero agents and zero hires.

| Date (UTC) | Client | Result |
| --- | --- | --- |
| 2026-11-11 15:08 | Claude Code 2.1.322 | Failed. The CLI required an authenticated session before running the skill. |
| 2026-11-11 15:08 | Codex CLI 0.167.0-alpha.4 | Failed. A read-only filesystem prevented the app server from starting. |

Both client attempts were configured for the isolated MCP endpoint.
