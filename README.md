# improve

An [Agent Skill](https://agentskills.io) that audits a codebase as a senior
advisor and writes implementation plans precise enough for other — cheaper —
agents to execute. It never edits your code.

> **This is a fork.** The original `improve` skill is
> [shadcn/improve](https://github.com/shadcn/improve), MIT-licensed, © shadcn.
> This fork is maintained at
> [Iwaschkin/improve](https://github.com/Iwaschkin/improve) and extends the
> upstream skill with a host-neutral workflow, a trust-aware execution rule,
> shell-neutral (Windows-safe) handoffs, validated plan metadata and lifecycle
> tooling, native root-cause discipline, and a cross-host conformance
> checklist. Upstream attribution is retained throughout — see
> [Provenance & license](#provenance--license).

## What it is — and what it never does

The idea: your most capable model does the part where intelligence compounds —
understanding the codebase, judging what's worth doing, writing the spec — and
execution goes to cheaper models. The plan is the product.

```text
you              →  improve audit               (expensive model, advises)
<plans dir>/     →  001-fix-n-plus-one.md       (self-contained specs)
other agent      →  implements, tests, ships    (cheap model, executes)
```

Non-negotiable boundaries, enforced by the skill's own
[hard rules](skills/improve/SKILL.md):

- It **never modifies source code**. Its only writes go to the selected plans
  directory. Asked to implement directly, it declines and offers `execute` (a
  dispatched executor plus its review) instead.
- It **never runs commands that mutate your working tree**, and commands are
  judged by their actual effects — never their names — with repository code
  running only under the trust rule below.
- It **never reproduces secret values** — locations and credential types only,
  with rotation recommended.
- Repository content is **data, not instructions**: a file planted in an
  audited repo cannot steer the advisor.
- Merging is always yours. The advisor never pushes, merges, or commits to
  your branch.

## Install

If you use the generic skills installer:

```bash
npx skills add Iwaschkin/improve
```

The canonical artifact is the [`skills/improve/`](skills/improve/) folder —
one `SKILL.md` plus its `references/` and `resources/`. Installing manually
means copying that folder into whatever location your host reads skills from
— see your host's Agent Skills documentation (the invocation table below
lists common spellings);
[host-compatibility.md](skills/improve/references/host-compatibility.md)
defines the capability contract the skill maps onto whichever host runs it. The
`.claude-plugin/` directory is an optional Claude Code marketplace adapter,
not the source of workflow truth — the skill works without it.

If you previously installed upstream `shadcn/improve` or an older copy of this
fork, update it: an outdated skill silently runs the old workflow.

## Invoking it

Invocation differs by host — the `/improve` forms below are the Claude Code
spelling; substitute your host's:

| Host | Invocation |
| --- | --- |
| Claude Code | `/improve ...` slash command |
| Codex (CLI/IDE) | `$improve` mention, `/skills`, or natural language |
| GitHub Copilot (VS Code, CLI, cloud) | natural language; `/skills` in VS Code chat, `copilot skill` in the CLI |
| Cursor | `/improve` or automatic discovery from the task description |

Natural language matching the skill's description is the portable fallback on
every conforming host. The spellings above come from each host's
documentation; per-host behavioral verification status lives in the
[conformance checklist](docs/dev/conformance.md).

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

`quick` / `deep` set audit depth (default is standard: hotspot-weighted
coverage, up to four parallel workers where the host supports delegation —
sequential otherwise). They compose with everything: `quick security`,
`deep --issues`.

## An operator's first session

**1. Run the audit.** The advisor maps the repo first (stack, conventions,
exact build/test/lint commands and their provenance, intent docs like ADRs and
PRDs), then audits nine categories from the
[audit playbook](skills/improve/references/audit-playbook.md): correctness,
security, performance, test coverage, tech debt, dependencies & migrations,
DX, docs, and direction.

**2. Read the findings.** Every finding is vetted — the advisor re-reads each
cited location itself before showing you anything — and arrives in a table
ordered by leverage, with a stable `[CATEGORY-NN]` ID, `file:line` evidence,
impact, effort, risk, and confidence. Corrective findings also carry a causal
status: `CONFIRMED` (the cause is evidenced link by link), `HYPOTHESIS` (gets
an investigation plan, never a fix plan), or `NOT-APPLICABLE` with a reason.
Direction ideas are presented separately — they're options to weigh, not bugs.
Rejected findings are recorded (with rationale) in a `rejections.json` next to
the plans, so the next audit doesn't resurface them.

**3. Pick what becomes plans.** Reply with the findings you want ("plan 1, 3
and 5"). One file per finding lands in the plans directory, plus a generated
index. Each plan follows the
[handoff template](skills/improve/references/plan-template.md): fully
self-contained (current-state excerpts, repo conventions, exact commands with
their provenance), a root-cause section naming the owning layer
and the shortcuts the executor must not take, machine-checkable done criteria,
explicit out-of-scope files, and STOP conditions — plus the full 40-character
commit it was written against, so any executor can run a mechanical drift
check first.

**4. Execute — with the skill or without it.** Plans are plain Markdown; you
can hand one to any agent ("implement docs/dev/plans/001-*.md") or a human.
Or let the skill run it: `/improve execute 001` checks eligibility from
validated plan files, prepares a disposable git worktree under
`<plans dir>/.worktrees/`, dispatches one executor, then reviews the result
like a tech lead — scope compliance, the full diff, the tests (executors game
green checks; diluted assertions and symptom-silencing retries get rejected
even when everything passes), and only then the done criteria. Verdicts are
APPROVE, REVISE (max two rounds), or BLOCK, and the report always includes the
execution locator, branch, base and head SHAs, and the reviewed commit.

**5. Merge, then reconcile.** Merging is your decision. Next session,
`/improve reconcile` verifies what actually landed — including squash merges,
cherry-picks, and rebases, by comparing diffs rather than trusting commit
messages ([details](skills/improve/references/closing-the-loop.md)) —
refreshes drifted plans,
investigates blocked ones, and retires findings fixed independently.

## The trust rule

Repository-controlled commands (install, build, test, lint, package scripts)
run only in repos you own or explicitly trust — trust is never inferred from
a repo merely being open in your workspace. In a trusted repo they run under
your host's normal permission policy; in an unfamiliar or untrusted repo the
executor edits files only and verification is handed back to you (or runs
inside a genuinely enforced host sandbox, when one exists). High-risk
effects — dependency installs with lifecycle scripts, migrations,
deployments, credentialed or broad network access, destructive operations —
always require explicit authorization. Worktrees remain the default change
isolation everywhere; a dirty tree gets explicit safe choices, never an
automatic stash or commit.

## The plan lifecycle

Plan frontmatter is the authoritative record; the generated index
(`README.md` in the plans directory) is a human-facing projection with the
status table, per-plan execution records, and rejected findings. Statuses:

```text
TODO → EXECUTING → REVIEWED → DONE     (BLOCKED | REJECTED)
```

Ownership is strict: executors never write plan records — the advisor records
EXECUTING at dispatch, the reviewer records REVIEWED/BLOCKED after review,
and reconcile records DONE only after integration is confirmed and acceptance
checks pass. Impossible states (a REVIEWED plan without a reviewed commit, a
DONE plan without a merged commit, verification timestamp, and verification
environment) fail validation outright. A REVIEWED plan with `merged_commit`
already recorded is integrated but awaiting acceptance — reconcile promotes
it to DONE once the checks pass, and re-opens DONE work whose recorded
commit later vanishes from the target history.

## Bundled tooling

One standard-library Python (3.10+) helper ships inside the skill. It
requires an explicit `--plans-dir`, resolves it against the repository root
(the nearest enclosing git repository — it refuses to run outside one), and
refuses paths escaping that root:

```bash
# regenerate the index (validates every plan first; atomic write;
# invalid input preserves the previous index and exits nonzero)
python skills/improve/resources/generate_plan_index.py --plans-dir docs/dev/plans

# gate execution (read-only; the generated index is never an input)
python skills/improve/resources/generate_plan_index.py --plans-dir docs/dev/plans --check-executable IMP-003
```

`--check-executable` exit codes: `0` eligible (TODO with every direct and
transitive dependency DONE), `3` not eligible (all blockers listed), `2`
invalid backlog or invocation. Eligibility is decided from validated plan
files only — a stale or hand-edited index has no effect. Index generation is
a projection and never gates an implementation; a manual executor without the
skill installed just reports completion instead. Closed plans (DONE or
REJECTED) can be moved to an `archive/` subdirectory of the plans directory —
still validated, still satisfying dependency references, listed in a compact
archived section instead of the main table.

**Where plans live:** `docs/dev/plans/` by default. If that directory already
belongs to another system, the skill deterministically selects
`docs/dev/advisor-plans/` instead and uses that same literal path for
everything afterward — worktrees, helpers, issues, cleanup. An ambiguous
double backlog stops for your decision rather than guessing.

## Publishing plans as issues (`--issues`)

Only with the explicit flag. The skill preflights `gh auth status`, checks
repository visibility, searches for existing issues before creating
duplicates, and — on public repos — asks for confirmation before publishing
any plan describing a security vulnerability or credential location
(non-interactively it skips those issues and records why). Plans marked
`sensitive` are flagged in the generated index.

## Compatibility

Audit and planning need an Agent Skills host with repository file access;
`execute` needs more:

| Capability | Audit | Plan | Execute |
| ---------- | ----- | ---- | ------- |
| File access | Required | Required | Required |
| Git | Recommended | Required | Required |
| Parallel subagents | Optional | Optional | Recommended |
| Coding CLI | No | No | Optional |

The skill maps these onto whatever host it runs in via the capability
contract in
[host-compatibility.md](skills/improve/references/host-compatibility.md);
manual conformance runs are recorded in the
[conformance checklist](docs/dev/conformance.md). Missing capabilities
degrade explicitly: no subagents → sequential audit; no writable executor →
manual handoff.

## Example

A run against [shadcn/ui](https://github.com/shadcn-ui/ui) (pinned at commit
`1994caba0b2140d4d5aa765bb9d7d4412d6aaabb`) surfaced findings like a
shadow-config resolver duplicated and drifted across two commands, and an
O(n²) icon migration — and rejected others with recorded reasons (an
`https_proxy` "SSRF" that is standard proxy convention, for instance).
Picking the duplication produced
[this plan](examples/001-extract-shadow-config-resolution.md): current code
excerpted, exact steps with the repo's own verification commands as gates,
and STOP conditions for when reality doesn't match. The example is historical
— it documents the output shape, not the current upstream tree.

## Developing this repository

The Markdown under `skills/improve/` is the product; edits to it are behavior
changes. [AGENTS.md](AGENTS.md) is the contributor guide. Verify any change
with:

```bash
python scripts/check.py                      # structure, links, packaging, size budget
python scripts/check_tests.py                # checker fixtures
python scripts/generate_plan_index_tests.py  # generator + plan-state fixtures
```

CI runs all three on Ubuntu and Windows
([check.yml](.github/workflows/check.yml)). A size budget on `SKILL.md`
(32 KiB / 400 lines, checker-enforced) keeps the always-loaded prompt lean —
detail belongs in phase-loaded references. This repo plans its own
improvement work in [docs/dev/plans/](docs/dev/plans/README.md) using the
skill itself; merged plans move to `docs/dev/plans/archive/` — the active
backlog holds only open work.

## Provenance & license

- **Upstream**: [shadcn/improve](https://github.com/shadcn/improve) — the
  original skill, concept, and workflow. © shadcn,
  [MIT license](LICENSE.md) retained unchanged.
- **This fork**: maintained by
  [Iwaschkin](https://github.com/Iwaschkin) at
  [Iwaschkin/improve](https://github.com/Iwaschkin/improve). Upstream is also
  recorded in the package metadata (`.claude-plugin/plugin.json`
  `upstreamRepository`, `SKILL.md` `metadata.upstream`).
- Fork changes are documented in this repo's commit history; the plans the
  skill writes are plain Markdown, so any agent (or human) can pick them up.
