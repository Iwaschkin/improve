# improve

An agent skill that audits any codebase and writes implementation plans for other agents to execute.

The idea: use your most capable model for the part where intelligence compounds — understanding the codebase, judging what's worth doing, writing the spec — and hand execution to cheaper models. The skill never implements anything itself. The plan is the product.

```text
you             →  /improve                    (expensive model, advises)
docs/dev/plans/ →  001-fix-n-plus-one.md       (self-contained specs)
other agent     →  implements, tests, ships    (cheap model, executes)
```

## Install

```bash
npx skills add Iwaschkin/improve
```

The canonical skill is the `skills/improve/` folder in this repository — copy it into whatever location your host reads skills from ([host-compatibility.md](skills/improve/references/host-compatibility.md) lists the documented per-host locations). The `.claude-plugin/` directory is an optional Claude Code marketplace adapter, not the source of workflow truth; the skill works without it. If you installed an earlier copy (including upstream `shadcn/improve`), re-install or update it — an outdated skill silently runs the old workflow.

Audit and planning are portable across conforming [Agent Skills](https://agentskills.io) hosts with repository access. Automatic execution is supported only on documented host surfaces that provide a writable executor and an enforceable execution boundary appropriate to the selected profile — [skills/improve/references/host-compatibility.md](skills/improve/references/host-compatibility.md) maps each host. This fork is maintained at `Iwaschkin/improve` and is based on upstream `shadcn/improve`; the plans it writes are plain markdown, so any agent (or human) can pick them up.

## Compatibility

Audit and planning need an Agent Skills host with repository file access. `execute` has additional requirements because it dispatches another coding agent and may run repository-code commands.

| Capability | Audit | Plan | Execute |
| ---------- | ----- | ---- | ------- |
| File access | Required | Required | Required |
| Git | Recommended | Required | Required |
| Parallel subagents | Optional | Optional | Recommended |
| Coding CLI | No | No | Optional |
| Secure sandbox | No | No | Required for the strict profile |

Execution runs under a **profile**: `trusted-local` for repos you own (ordinary tests and builds run under your host's normal permission policy), `strict` for unfamiliar or sensitive repos (repository code runs only inside an enforceable sandbox), or `manual` (no automatic execution). High-risk effects — installs with lifecycle scripts, migrations, deployments, credentialed network access — need explicit authorization in every profile. Worktrees stay the default change isolation everywhere; the profile only decides how commands run.

Per-surface support is evidence-bound: **VERIFIED** means current passing runs recorded in the [conformance checklist](docs/dev/conformance.md); **DOCUMENTED** means the host's documentation supports it but no behavioral run is recorded yet; **UNSUPPORTED** means a required capability is absent. Today every target surface — Claude Code CLI, Cursor, Codex CLI, GitHub Copilot (VS Code and CLI) — is DOCUMENTED: mapped in [host-compatibility.md](skills/improve/references/host-compatibility.md), with no recorded behavioral run claiming more.

## Usage

Invocation differs by host — the `/improve` forms below are the Claude Code spelling; substitute your host's:

| Host | Invocation |
| --- | --- |
| Claude Code | `/improve ...` slash command |
| Codex (CLI/IDE) | `$improve` mention, `/skills`, or natural language |
| GitHub Copilot (VS Code, CLI, cloud) | natural language; `/skills` in VS Code chat, `copilot skill` in the CLI |
| Cursor | `/improve` or automatic discovery from the task description |

Natural language matching the skill's description is the portable fallback on every conforming host.

```text
/improve                        full audit → prioritized findings → plans
/improve quick                  cheap pass: hotspots, top findings only
/improve deep                   exhaustive: every package, every category
/improve security               focused audit (also: perf, tests, bugs, ...)
/improve branch                 audit only what the current branch changes
/improve next                   feature suggestions — where to take the project
/improve plan <description>     skip the audit, spec one thing
/improve review-plan <file>     critique and tighten an existing plan
/improve execute <plan>         dispatch a cheaper executor, review its work
/improve reconcile              refresh the backlog: verify, unblock, retire
/improve ... --issues           also publish plans as GitHub issues
```

## How to use

A typical first run, start to finish:

1. Open your agent in the repo and run `/improve` (or `/improve quick` to keep it cheap).
2. It maps the repo, audits it, and comes back with a findings table. Reply with the ones you want planned — "plan 1, 3 and 5".
3. Plans land in `docs/dev/plans/` — one file each, plus an index with the recommended order. Read them; they're meant to be reviewed.
4. Hand a plan to any agent ("implement docs/dev/plans/001-*.md"), or let the skill run it: `/improve execute 001`. It dispatches a cheaper model in an ignored workspace-local disposable worktree, reviews the diff from the recorded literal execution-base SHA to executor `HEAD` before running repository code, and reports back with the execution locator, branch, reviewed commit, execution profile, verification environment, and verdict. Every command runs as its own invocation — no shell state carries between steps. Merging stays up to you.
5. Next session, run `/improve reconcile` to clean up the backlog: verify what landed, refresh what drifted, unblock what got stuck.

Before a PR, `/improve branch` does the same thing scoped to what your branch changes, including committed diffs plus staged, unstaged, and untracked files from `git status --porcelain=v1`.

## Example

A run against [shadcn/ui](https://github.com/shadcn-ui/ui) came back with findings like:

```markdown
| # | Finding                                        | Category  | Effort | Confidence |
|---|------------------------------------------------|-----------|--------|------------|
| 1 | shadow-config duplicated in search.ts/view.ts, | tech-debt | M      | HIGH       |
|   | copies already drifted (TODO at search.ts:31)  |           |        |            |
| 2 | O(n²) icon migration (migrate-icons.ts:168)    | perf      | S      | HIGH       |
```

Columns abbreviated for the example; the full table also carries Impact, Risk, and Evidence.

…and rejected a few, with reasons recorded so they don't come back next run:

```text
- [SEC-01] https_proxy env var "SSRF": by-design — standard proxy convention,
  every CLI honors it. Not a finding.
```

Picking #1 produced [this plan](./examples/001-extract-shadow-config-resolution.md) — current code excerpted, exact steps, the repo's own test/lint commands as verification gates, and STOP conditions for when reality doesn't match.

## How it works

**Recon.** Maps the repo: stack, conventions, and the exact build/test/lint commands, including where each command came from and whether it executes repository code. These become verification gates in every plan, but the plan distinguishes commands that were discovered from commands that were actually run. It also ingests intent and design docs when present — ADRs (`docs/adr/`), PRDs, `CONTEXT.md`, `DESIGN.md`, `PRODUCT.md` — so decided tradeoffs aren't re-flagged as findings, direction suggestions stay grounded in stated product intent, and plans speak the repo's own vocabulary. Composes with any repo that already maintains these docs.

**Audit.** Fans out parallel read-only workers across nine categories when the host supports delegation — and audits sequentially itself when it doesn't: correctness, security, performance, test coverage, tech debt, dependencies & migrations, DX, docs, and direction (feature suggestions — every one must cite evidence from the repo itself, no generic idea-slop). Every finding carries `file:line` evidence, impact, effort, and confidence.

**Vet.** Subagents over-report, so the advisor re-reads every cited location itself before showing you anything — false positives get dropped, wrong attributions get corrected, rejections get recorded.

**Prioritize.** Findings land in a table ordered by leverage (impact ÷ effort, weighted by confidence). You pick what becomes plans.

**Plan.** One file per selected finding, written into `docs/dev/plans/` with an index, priority order, and dependency graph. If that directory already belongs to another system, the skill selects `docs/dev/advisor-plans/` instead — deterministically, on every host — and every later operation (execution worktrees, reconciliation, issues, cleanup, the bundled helpers) uses that same directory; the two are never mixed, and an ambiguous double backlog stops for your decision.

## What makes the plans executable

Plans are written for the weakest plausible executor — a model that has never seen the advisor session and may be much smaller. Three properties carry that:

- **Self-contained.** All context is inlined: exact file paths, current-state code excerpts, repo conventions with an exemplar file, command provenance, and execution-safety notes. No "as discussed above."
- **Verification gates.** Every step ends with a command and its expected output. Done criteria are machine-checkable. The executor never has to judge whether it succeeded.
- **Hard boundaries.** Explicit out-of-scope lists, and STOP conditions — "if X, stop and report" — instead of letting a small model improvise when reality doesn't match the plan.

Each plan also stamps the git commit it was written against, so executors run a mechanical drift check before touching anything.

## Closing the loop

Plans aren't fire-and-forget:

- **`execute <plan>`** dispatches a cheaper executor in an ignored workspace-local disposable git worktree. The executor can be a worktree-isolated subagent or, when the host cannot spawn one, a headless coding CLI run from the prepared worktree. Automatic execution requires a committed baseline (a dirty tree gets explicit safe choices, never an automatic stash) and a selected execution profile: trusted-local, strict, or manual. The advisor checks scope, reads committed and uncommitted diffs, audits tests, then re-runs done criteria as the profile permits. Approval marks the plan REVIEWED; MERGED and VERIFIED happen only after reconciliation on the target branch.
- **`reconcile`** processes what happened since: checks REVIEWED work for merge reachability, verifies MERGED work on the target branch, investigates BLOCKED plans and rewrites around obstacles, refreshes drifted TODO plans, and retires findings that got fixed independently.
- **`--issues`** publishes plans as GitHub issues — same self-contained body, so any agent or human can pick them up where work already lives.

## Hard rules

- Never modifies source code itself. The only writes go to `docs/dev/plans/`; executor worktrees are disposable and ignored under `docs/dev/plans/.worktrees/` by default, executors edit only there, and merging is always yours.
- Never runs commands that mutate your working tree. Commands are classified by their actual effects (read, network, repository-code execution, install, host mutation) — never by name — and permission follows the riskiest effect under the selected execution profile: your host's normal policy for trusted-local repos, an enforceable sandbox for strict, and explicit authorization for high-risk effects everywhere.
- Never reproduces secret values. Locations and credential types only, rotation always recommended.
- Asked to implement? It declines and points at the plan (or offers `execute`).

## License

MIT © shadcn. Fork maintenance by Iwaschkin; original attribution retained.
