# Host Compatibility

The core workflow in `SKILL.md` is written against the **capability contract**
below, never against one vendor's tool names. This file maps the contract onto
documented host surfaces. Read only the section for the host you are running
in, at the phase that needs it (audit delegation or `execute` dispatch).

## Capability contract

| Capability | Needed for | When missing |
| --- | --- | --- |
| Repository read access | Everything | Stop — nothing works without it |
| Plan-directory write access | Planning | Stop and say the managed directory cannot be written; produce findings only |
| Bounded read-only worker delegation | Parallel audit (optional) | Audit sequentially yourself in category-priority order |
| Skill-resource visibility to workers | Cheap delegated prompts | Inline the finding contract and category guidance into each worker prompt |
| Isolated writable executor | Automatic `execute` | Hand the plan over for manual execution |
| Enforceable command permission/sandbox policy | strict-profile execution | Executor edits files only; verification reported as skipped |
| Executor continuation or redispatch | REVISE round | Redispatch fresh with the full plan, prior report, current SHAs, and the feedback |
| Execution locator (local path, task id, branch, or PR URL) | Review and reconcile | Without any locator, automatic execution is off — manual handoff |
| Git base/head identity and diff access | Review, drift checks, reconcile | Automatic execution is off — manual handoff |

Degradation is always explicit: say which capability is missing and which
fallback you are using. Never describe a prompt instruction as an enforceable
tool restriction, and never invent a host API you have not confirmed exists.

**Cross-provider fallback is never silent.** Launching a different vendor's
CLI as the executor changes data routing, credentials, billing, and policy.
Offer it; proceed only on explicit user selection.

## Host surfaces

Statuses: `documented` (host documentation supports it; not behaviorally
verified by this project) | `behaviorally verified` (a dated conformance run
passed — see `docs/dev/conformance.md` in this repository when present) |
`unknown`. All entries below were checked against vendor documentation on
2026-07-19; re-verify links before relying on a capability in a new host
version. No surface is behaviorally verified until a conformance run records
it.

### Claude Code (CLI and IDE extensions) — `documented`

- Skills: personal, project (`.claude/skills/`), and plugin skills; invoked as
  `/improve ...` or by description match. Docs:
  `https://code.claude.com/docs/en/skills`
- Workers: read-only exploration subagents and general-purpose subagents are
  available (`https://code.claude.com/docs/en/sub-agents`); worktree-isolated
  dispatch exists for writable executors.
- Continuation: subagents can be sent follow-up messages for REVISE rounds.
- Isolation: permission modes and sandboxing vary by installation; confirm the
  actual enforcement before calling an execution "strict".

### Codex (CLI and IDE) — `documented`

- Skills: repository (`.agents/skills/`, scanned upward), user, admin, and
  system locations; invoked with `/skills`, a `$` mention, or by description
  match. Docs: `https://developers.openai.com/codex/skills`
- Workers: subagents exist and are spawned only on explicit request — a
  delegating audit must ask for them explicitly. Docs:
  `https://developers.openai.com/codex/subagents`
- Continuation: agent threads are inspectable via `/agent`; for headless
  `codex exec` runs, redispatch with restated context.
- Isolation: approval/sandbox configuration is Codex-managed; verify what is
  actually enforced before strict execution.

### GitHub Copilot (VS Code, CLI, cloud agent) — `documented`

- Skills: project `.github/skills/`, `.claude/skills/`, or `.agents/skills/`;
  personal `~/.copilot/skills` or `~/.agents/skills`. VS Code: `/skills` in
  chat (`https://code.visualstudio.com/docs/agent-customization/agent-skills`);
  CLI: `copilot skill` subcommand
  (`https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills`);
  cloud agent
  (`https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills`).
- Workers: no general parallel read-only subagent fan-out is documented for
  the editor or CLI surfaces — default to the sequential audit fallback.
- Continuation: none documented for a dispatched executor; use redispatch.
- The cloud agent surface executes remotely: use a task/branch/PR locator,
  not a local worktree path.

### Cursor (editor and CLI) — `documented`

- Skills: project `.cursor/skills/`, personal `~/.cursor/skills/`; invoked by
  description match or `/skill-name`. Docs:
  `https://cursor.com/docs/context/skills`
- Workers: subagents exist on recent versions (see the Cursor changelog);
  capability varies by version — confirm before fanning out, else audit
  sequentially.
- Continuation: none documented for dispatched executors; use redispatch.
- Isolation: no enforceable sandbox is documented for arbitrary repository
  commands; treat strict-profile execution as unavailable unless the user
  provides an external boundary.

## Other Agent Skills hosts

Any host implementing the Agent Skills format
(`https://agentskills.io/specification`) can run audit and planning if it
grants repository read and plan-directory write access. Map the remaining
capabilities honestly using the contract above; when a capability cannot be
confirmed from that host's documentation, treat it as missing and use the
fallback.
