---
id: IMP-001
title: Establish a repository development guide for agents
status: TODO
priority: P2
effort: S
risk: LOW
category: dx
base_commit: 4adde10c1d1d6308c485b87efbbefb6a6a241785
working_tree_clean: true
created_at: 2026-07-19
updated_at: 2026-07-19
scope:
  - AGENTS.md
  - CLAUDE.md
dependencies: []
execution_branch: null
execution_base: null
reviewed_commit: null
merged_commit: null
sensitive: false
issue: null
---

## Plan 001: Establish a repository development guide for agents

> **Executor instructions**: Follow this plan step by step. Run every
> verification command permitted by the execution environment and confirm the
> expected result before moving on. If repository-code execution is not
> permitted, skip those commands and report that they were not run. If any STOP
> condition occurs, stop and report; do not improvise. Do not modify this plan
> or the generated index. Report STATUS, HEAD SHA, FILES CHANGED, VERIFICATION
> RESULTS, and NOTES; the reviewer owns lifecycle metadata and index
> regeneration.
>
> **Drift check (run first)**: run
> `git diff --stat 4adde10c1d1d6308c485b87efbbefb6a6a241785..HEAD -- AGENTS.md CLAUDE.md`.
> Neither file exists at the planned base; both are expected to be created. If
> either already exists with content, stop and report — merging with existing
> agent instructions is a user decision.

## Status

- **Status**: TODO
- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `4adde10c1d1d6308c485b87efbbefb6a6a241785`, 2026-07-19
- **Working tree clean**: true
- **Issue**: none

## Why this matters

This repository ships a skill whose own audit playbook calls a missing
`AGENTS.md` a high-leverage gap "for repos where agents will execute the
plans" — and this backlog is exactly that: a dozen plans about to be executed
by agents in this repository. Today an executor has to infer the verification
commands, the documentation conventions, the stdlib-only Python policy, and
the single-skill packaging rule from scattered files. A short root-level guide
removes that inference, is read natively by GitHub Copilot, Cursor, and Codex,
and reaches Claude Code through a one-line `CLAUDE.md` import. Doing it first
makes every subsequent plan in this backlog cheaper and safer to execute.

## Current state

- No `AGENTS.md`, `CLAUDE.md`, or `CONTRIBUTING` file exists anywhere in the
  repository.
- Verification commands exist but are only discoverable from CI:
  `.github/workflows/check.yml:20-22` runs `python scripts/check.py`,
  `python scripts/check_tests.py`, and one generator invocation on Python 3.12.
- Conventions currently implicit in the codebase:
  - documentation is normative product content — imperative Markdown, bold
    rules, compact tables, exact commands (see `skills/improve/SKILL.md`);
  - Python is standard-library-only, typed, `from __future__ import
    annotations`, no third-party dependencies (see `scripts/check.py` and
    `skills/improve/resources/generate_plan_index.py`);
  - CI actions are pinned to full commit SHAs with read-only permissions;
  - `scripts/check.py:60-71` enforces exactly one `skills/*/SKILL.md`;
  - `scripts/check.py:256-265` enforces version agreement between `SKILL.md`
    `metadata.version` and `.claude-plugin/plugin.json`.
- The plan backlog lives in `docs/dev/plans/` with a generated `README.md`
  index that must never be hand-edited.
- Transient development reference material (currently an untracked
  `skills/no-quick-fixes/` folder) is intentionally uncommitted and may be
  deleted at any time; nothing may depend on it.

## Commands you will need

| Purpose | Command | Provenance | Execution class | Expected on success |
| --- | --- | --- | --- | --- |
| Structural checker | `python scripts/check.py` | `.github/workflows/check.yml:20`; not run by advisor | EXECUTES_REPOSITORY_CODE | exit 0 and `all checks passed` |
| Checker fixtures | `python scripts/check_tests.py` | `.github/workflows/check.yml:21`; not run by advisor | EXECUTES_REPOSITORY_CODE | all fixtures pass |
| Whitespace | `git diff --check` | Git standard; not run by advisor | GIT_READ | exit 0 |

The structural checker's link check (`check4`) walks every Markdown file in the
repository, so any relative link written into `AGENTS.md` must resolve.

## Scope

One behavioral objective: any agent opening this repository cold can find what
the project is, how to verify a change, and which conventions to match, without
reading CI or source first.

**In scope** (create only):

- `AGENTS.md`
- `CLAUDE.md`

**Out of scope**:

- Any change to `skills/improve/` — this guide is for developing the repo, not
  part of the shipped skill package.
- Any change to `scripts/`, CI, or packaging metadata.
- Deploying discipline or policy content into other repositories.
- Duplicating the plan backlog's content — link to it instead.

## Git workflow

- Branch: `advisor/001-repo-dev-guide`
- Commit message: `docs: add agent development guide`, matching recent `docs:`
  commits such as `docs: limit executable plan scope`.
- One commit is sufficient.
- Do not push or open a PR unless the operator instructs it.

## Steps

### Step 1: Write `AGENTS.md`

Create a concise (roughly one screen, not a manual) root `AGENTS.md` covering,
in this order:

1. **What this repo is** — a portable Agent Skill (`skills/improve/`) plus its
   validation tooling. The Markdown under `skills/improve/` is the product;
   edits to it are behavior changes, not documentation polish.
2. **Verify a change** — the exact commands from the table above, each on its
   own line, with expected results. State Python 3.10+ locally, 3.12 in CI.
3. **Conventions** — imperative normative Markdown matching the existing
   files; Python is standard-library-only with no new dependencies; CI actions
   stay pinned to commit SHAs with read-only permissions.
4. **Packaging rules** — exactly one skill lives in `skills/` (`improve`);
   development-only reference material stays untracked or outside `skills/`;
   `SKILL.md` `metadata.version` and `.claude-plugin/plugin.json` `version`
   must change together (the checker enforces both rules).
5. **Plan backlog** — improvement work is planned in `docs/dev/plans/`;
   `docs/dev/plans/README.md` is generated (rerun
   `python skills/improve/resources/generate_plan_index.py --plans-dir
   docs/dev/plans`), never hand-edited; plan frontmatter is the authoritative
   lifecycle record.
6. **Release checklist** — bump both version fields together, run all checks,
   and update compatibility/conformance documentation when behavior changed.

Use relative links sparingly and only to files that exist.

**Verify**: `python scripts/check.py` -> exit 0 (all links in `AGENTS.md`
resolve; no other check regresses).

### Step 2: Write `CLAUDE.md`

Create a root `CLAUDE.md` whose body is a single import line referencing
`AGENTS.md` (the `@AGENTS.md` form), so Claude Code reads the same guide that
Copilot, Cursor, and Codex read natively. Add nothing else — one source of
truth.

**Verify**: `python scripts/check.py` -> exit 0, and `CLAUDE.md` contains no
content other than the import reference.

## Test plan

- No new automated tests; this is documentation for humans and agents.
- Cold-read check: a reader given only `AGENTS.md` must be able to answer —
  how do I verify a change, what Python constraints apply, where do plans
  live, what must never be hand-edited, and what must stay out of `skills/`.
  If any answer is missing, the guide is incomplete.
- `python scripts/check.py` and `python scripts/check_tests.py` both exit 0.

## Done criteria

- [ ] `AGENTS.md` exists at the repository root and covers purpose,
      verification commands, conventions, packaging rules, backlog workflow,
      and the release checklist.
- [ ] `CLAUDE.md` exists and contains only the `AGENTS.md` import.
- [ ] Every relative link in both files resolves (`check4` passes).
- [ ] `python scripts/check.py` exits 0.
- [ ] `python scripts/check_tests.py` exits 0.
- [ ] No files outside the two in-scope paths are modified.
- [ ] The executor report contains STATUS, HEAD SHA, FILES CHANGED,
      VERIFICATION RESULTS, and NOTES; the reviewer owns lifecycle metadata and
      index regeneration.

## STOP conditions

Stop and report if:

- `AGENTS.md` or `CLAUDE.md` already exists with content — merging is a user
  decision.
- The guide seems to require documenting behavior that contradicts what the
  checker actually enforces; the checker is authoritative, report the
  discrepancy instead of documenting around it.
- More than the two in-scope files are needed.

## Maintenance notes

- Keep the guide short. Later plans change facts this guide states (IMP-002
  adds Windows CI, IMP-007 changes checker policy, IMP-009/IMP-010 change
  helper invocations). Executors stay inside their plan's scope, so refreshing
  `AGENTS.md` is a reviewer follow-up when accepting those plans — a stale
  guide is worse than none.
- The guide describes this repository only. Skill behavior for audited target
  repositories lives in `skills/improve/` and must not leak in here.
