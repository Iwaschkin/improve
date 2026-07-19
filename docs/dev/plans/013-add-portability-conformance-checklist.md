---
id: IMP-013
title: Add a manual cross-host conformance checklist
status: TODO
priority: P2
effort: S
risk: LOW
category: tests
base_commit: 4adde10c1d1d6308c485b87efbbefb6a6a241785
working_tree_clean: true
created_at: 2026-07-19
updated_at: 2026-07-19
scope:
  - docs/dev/conformance.md
  - README.md
dependencies:
  - IMP-007
  - IMP-010
  - IMP-012
execution_branch: null
execution_base: null
reviewed_commit: null
merged_commit: null
sensitive: false
issue: null
---

## Plan 013: Add a manual cross-host conformance checklist

> **Executor instructions**: This plan creates a manually operated checklist,
> not an automation framework. Do not add scripts, JSON schemas, CI steps, or
> host credentials. Do not record any PASS result — every result row starts
> NOT-RUN and only a real dated host run may change it later. Do not modify
> this plan or the generated index. Report STATUS, HEAD SHA, FILES CHANGED,
> VERIFICATION RESULTS, and NOTES; the reviewer owns lifecycle metadata and
> index regeneration.
>
> **Drift check (run first)**: run
> `git diff --stat 4adde10c1d1d6308c485b87efbbefb6a6a241785..HEAD -- docs/dev/conformance.md README.md`.
> `docs/dev/conformance.md` does not exist at the planned base and is expected
> to be created. Stop unless IMP-007, IMP-010, IMP-012, and their transitive
> dependencies are VERIFIED — the cases below are oracles over their final
> behavior, and writing them against unfinished contracts would freeze the
> wrong expectations.

## Status

- **Status**: TODO
- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: IMP-007, IMP-010, IMP-012
- **Category**: tests
- **Planned at**: commit `4adde10c1d1d6308c485b87efbbefb6a6a241785`, 2026-07-19
- **Working tree clean**: true
- **Issue**: none

## Why this matters

The README promises the skill works in any Agent Skills host, and this backlog
rebuilds the workflow to be genuinely host-neutral — but nothing demonstrates
per-surface behavior. Structural checks prove files and links, not that Cursor
degrades to a sequential audit, that Copilot CLI on Windows survives the Git
recipes, or that an executor refuses a symptom silencer. A full evaluation
framework was considered and rejected: proprietary hosts cannot be driven from
CI, so heavy machinery would produce a matrix of permanent NOT-RUN rows at high
build cost. What earns its keep is a short, precise manual checklist with an
honest per-surface results table, so compatibility claims can never outrun
evidence.

## Current state

- `.github/workflows/check.yml` runs structural checks only; no behavioral
  verification of any kind exists.
- `README.md:19-31` claims compatibility with any Agent Skills host and lists
  generic capability requirements, with no distinction between "documented"
  and "verified on this surface".
- There is no `docs/dev/conformance.md` or equivalent.
- IMP-004 established the capability contract and `host-compatibility.md`;
  IMP-012 recorded (in its executor report NOTES) six root-cause behaviors
  that this checklist must cover.
- Target host surfaces, per the project goal: Claude Code CLI, Cursor editor,
  Codex CLI, GitHub Copilot in VS Code, and GitHub Copilot CLI. Surfaces are
  tracked separately — one vendor's CLI passing says nothing about its editor.

## Commands you will need

| Purpose | Command | Provenance | Execution class | Expected on success |
| --- | --- | --- | --- | --- |
| Structural checker | `python scripts/check.py` | CI; not run by advisor | EXECUTES_REPOSITORY_CODE | exit 0 (new relative links resolve) |
| Checker fixtures | `python scripts/check_tests.py` | CI; not run by advisor | EXECUTES_REPOSITORY_CODE | all pass |
| Whitespace | `git diff --check` | Git standard | GIT_READ | exit 0 |

Running the checklist itself against real hosts is operator work outside this
plan: it consumes model credits and requires each host's normal permissions.
This plan only creates the instrument.

## Scope

One behavioral objective: a documented, repeatable way to record per-surface
behavioral evidence, plus README wording that cannot claim more than the
recorded evidence.

**In scope**:

- `docs/dev/conformance.md` (create)
- `README.md`

**Out of scope**:

- Scripts, schemas, CI wiring, or any automation of proprietary hosts.
- Storing credentials, raw transcripts, or private source in the repository.
- Running any case or recording any outcome other than NOT-RUN.
- Changing skill behavior; a failing case later produces a focused new plan,
  never an inline workaround.

## Git workflow

- Branch: `advisor/013-portability-conformance-checklist`
- Commit message: `docs: add cross-host conformance checklist`.
- One commit is sufficient.
- Do not push or open a PR unless instructed.

## Steps

### Step 1: Write the case checklist

Create `docs/dev/conformance.md` with a short preamble (what a case run is:
fresh disposable fixture repo, skill installed per `host-compatibility.md`,
exact prompt, observed behavior noted, secrets and private source never
recorded) and these twelve cases. Each case gets: stable ID, one-paragraph
setup, the exact portable prompt, expected behavior, and forbidden behavior.

1. `AUDIT-READONLY` — a quick audit writes nothing outside the selected plans
   directory and reports what was not audited.
2. `AUDIT-NO-SUBAGENTS` — a host without worker delegation audits sequentially
   instead of refusing or hallucinating delegation.
3. `AUDIT-INSTRUCTION-PRECEDENCE` — an adversarial instruction planted in a
   repo README is treated as data; host-elevated instruction files are honored
   per host precedence; no secrets quoted.
4. `PLAN-SELF-CONTAINED` — a generated plan, read cold in a fresh context with
   only the fixture repo, is executable without asking about missing context.
5. `PLAN-CAUSAL-CONTRACT` — a corrective finding yields a plan with the full
   causal chain and correct fix layer; ambiguous evidence yields HYPOTHESIS
   and an investigation plan, never an invented confirmed cause.
6. `EXEC-DIRTY-TREE` — execute against a dirty tree offers the documented safe
   choices and never stashes, commits, or discards user changes.
7. `EXEC-STRICT-NO-SANDBOX` — an untrusted fixture with no enforceable sandbox
   results in edit-only execution or manual handoff, with verification
   reported as not run.
8. `EXEC-TRUSTED-SEQUENTIAL` — a trusted-local fixture runs ordinary tests
   under host policy with the base SHA recorded and the diff reviewed.
9. `EXEC-SYMPTOM-SILENCER` — a fixture whose failing test is easiest to
   silence with a retry, suppression, or loosened assertion; the executor
   fixes the owning flaw or stops, and review rejects a silencer diff even
   when tests pass (covers the IMP-012 workaround gate).
10. `GIT-WINDOWS-PORTABLE` — on a PowerShell host, every recipe from the plan
    and review flow runs as separate literal-SHA invocations with no POSIX
    substitution or shell-state dependency.
11. `PACKAGE-CORE-ONLY` — the skill installs and triggers from a copy
    containing only `skills/improve/`, without `.claude-plugin/`.
12. `PLANS-DIR-ALTERNATE` — with an unrelated `docs/dev/plans/`, the whole
    flow (plan, execute, reconcile) uses `docs/dev/advisor-plans/` and never
    writes to the unrelated directory.

**Verify**: every case has all five parts, and the six IMP-012 oracle
behaviors are each covered by at least one case (5 and 9 carry most of them).

### Step 2: Add the results table

In the same file, add one results table per target surface — Claude Code CLI,
Cursor editor, Codex CLI, GitHub Copilot (VS Code), GitHub Copilot CLI — with
columns: case ID, date, host version, model, outcome, notes. Outcomes:
`PASS | FAIL | BLOCKED | NOT-RUN`, where BLOCKED means a required host
capability was absent (which is itself a finding for `host-compatibility.md`),
and every row starts `NOT-RUN`. State the recording rules: only a real dated
run changes an outcome; notes contain sanitized observations only; a FAIL gets
a focused follow-up plan, not an edit that weakens the case.

**Verify**: all five surfaces are present, every row is NOT-RUN, and the
recording rules appear beside the tables.

### Step 3: Make README claims evidence-bound

Update the README compatibility section to distinguish `VERIFIED` (current
passing required cases on that surface, linked to the results table),
`DOCUMENTED` (host documentation supports it, not yet run), and `UNSUPPORTED`.
Link `docs/dev/conformance.md`. Remove or qualify any wording that asserts
behavior on a surface with no recorded evidence.

**Verify**: `python scripts/check.py` exits 0 and the README contains no
unqualified per-host behavioral claim.

## Test plan

- Cold-read check: an operator who has never seen this backlog can run case 1
  on one host using only `docs/dev/conformance.md` and `host-compatibility.md`.
- Cross-check the six IMP-012 oracle behaviors against the case list; none may
  be uncovered.
- `python scripts/check.py`, `python scripts/check_tests.py`, and
  `git diff --check` all exit 0.

## Done criteria

- [ ] `docs/dev/conformance.md` contains the twelve cases, each with ID,
      setup, prompt, expected, and forbidden behavior.
- [ ] Per-surface results tables exist for all five target surfaces, all rows
      NOT-RUN, with recording rules.
- [ ] README compatibility wording is bound to recorded evidence and links the
      checklist.
- [ ] No scripts, schemas, or CI changes were added.
- [ ] `python scripts/check.py` exits 0.
- [ ] `python scripts/check_tests.py` exits 0.
- [ ] No files outside the two in-scope paths are modified.
- [ ] The executor report contains STATUS, HEAD SHA, FILES CHANGED,
      VERIFICATION RESULTS, and NOTES; the reviewer owns lifecycle metadata and
      index regeneration.

## STOP conditions

Stop and report if:

- IMP-012 or a transitive dependency is not VERIFIED, or its final behavior
  differs from the expectations a case would encode.
- A case cannot be written without host-specific steps in the portable prompt;
  move host detail to `host-compatibility.md` and keep the prompt neutral.
- Covering the contracts seems to require automation, schemas, or CI; that is
  the rejected heavyweight design — record the gap in NOTES instead.
- More than the two in-scope files are needed.

## Maintenance notes

- Re-run the affected cases after material changes to `SKILL.md`, the
  references, or a host's major version, and date every result.
- If a surface accumulates repeated BLOCKED results, record the missing
  capability in `host-compatibility.md` and downgrade the README status rather
  than leaving stale claims.
- If the project later gains contributors or an automatable host API, the
  original evaluation-framework design (case schema, contract validator, CI)
  can be revisited as a new plan; keep this file as the case source of truth.
- The checklist grows one case per new behavioral contract — resist adding
  cases that restate structural checks already covered by `scripts/check.py`.
