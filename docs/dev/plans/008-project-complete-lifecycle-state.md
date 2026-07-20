---
id: IMP-008
title: Project complete lifecycle state in the plan index
status: DONE
priority: P2
effort: M
risk: MED
category: dx
base_commit: 4adde10c1d1d6308c485b87efbbefb6a6a241785
created_at: 2026-07-19
updated_at: 2026-07-20
scope:
  - skills/improve/resources/generate_plan_index.py
  - scripts/generate_plan_index_tests.py
  - skills/improve/references/plan-template.md
  - skills/improve/references/closing-the-loop.md
  - skills/improve/SKILL.md
dependencies:
  - IMP-002
  - IMP-003
  - IMP-004
execution_base: 4adde10c1d1d6308c485b87efbbefb6a6a241785
reviewed_commit: 2a96501f19b401e0f3804c51d7fc3e2a67e463f8
merged_commit: 2a96501f19b401e0f3804c51d7fc3e2a67e463f8
execution_locator: manual (implemented directly; no dispatched executor)
verified_at: 2026-07-20T00:00:00Z
status_note: landed in 1.x; nine-state lifecycle collapsed to six in 2.0
sensitive: false
issue: null
---

## Plan 008: Project complete lifecycle state in the plan index

> **Executor instructions**: Start from IMP-002's validated generator. Extend
> the schema and tests together; do not add a lifecycle fact that cannot be
> represented in plan metadata or a documented auxiliary source. Run all
> permitted checks. Do not modify this plan or the generated index. Report
> STATUS, HEAD SHA, FILES CHANGED, VERIFICATION RESULTS, and NOTES; the reviewer
> owns lifecycle metadata and index regeneration.
>
> **Drift check (run first)**: run
> `git diff --stat 4adde10c1d1d6308c485b87efbbefb6a6a241785..HEAD -- skills/improve/resources/generate_plan_index.py scripts/generate_plan_index_tests.py skills/improve/references/plan-template.md skills/improve/references/closing-the-loop.md skills/improve/SKILL.md`.
> Stop unless IMP-002's explicit validation and generator fixture suite are
> present, IMP-003 has defined the trust-profile names this schema reuses, and
> IMP-004 has defined the execution-locator concept.

## Why this matters

The workflow asks operators to retain execution location, branch, executor
head, verification environment, issue URL, blocked/rejected rationale, and
dependency context, but the generated index exposes only execution base,
reviewed commit, and merged commit. Important handoff state therefore lives in
chat or prose and disappears across sessions. The plan schema and index should
represent every lifecycle fact that `execute` and `reconcile` require, without
making local filesystem paths mandatory for remote agents.

## Current state

- `generate_plan_index.py:95-96` defines only these lifecycle columns:

  ```markdown
  | Plan | Title | Priority | Effort | Depends on | Status |
  Execution base | Reviewed commit | Merged commit |
  ```

- Lines 98-119 render only `dependencies`, `status`, `execution_base`,
  `reviewed_commit`, and `merged_commit`; `issue` is parsed but never displayed.
- `plan-template.md` frontmatter includes `execution_branch`, but the generator
  does not render it. It has no execution locator, executor-head SHA,
  verification profile/environment, or status rationale field.
- `closing-the-loop.md:57-69` requires executor reports to include worktree
  path, branch, base, head, verification environment, steps, and STOP reason.
- `closing-the-loop.md:94-98` requires verdict reports to retain location,
  branch, base, executor head, reviewed commit, and verification environment.
- `closing-the-loop.md:104-107` needs worktree path/branch for cleanup, while a
  cross-host workflow may have only a remote task, branch, or PR locator.
- `SKILL.md:74` promises a generated index section for findings considered and
  rejected, but the generator has no source for audit findings that never
  became plans.
- The validated flat frontmatter/list subset from IMP-002 is the schema
  convention. Do not introduce arbitrary nested YAML.

## Commands you will need

| Purpose | Command | Provenance | Execution class | Expected on success |
| --- | --- | --- | --- | --- |
| Generator tests | `python scripts/generate_plan_index_tests.py` | IMP-002 | EXECUTES_REPOSITORY_CODE | all cases pass |
| Structural checker | `python scripts/check.py` | CI; not run by advisor | EXECUTES_REPOSITORY_CODE | exit 0 |
| Checker fixtures | `python scripts/check_tests.py` | CI; not run by advisor | EXECUTES_REPOSITORY_CODE | exit 0 |
| Whitespace | `git diff --check` | Git standard | GIT_READ | exit 0 |

## Scope

One behavioral objective: make the generated backlog a complete, portable
projection of execution, review, merge, verification, dependency, issue, and
rejection state.

**In scope**:

- `skills/improve/resources/generate_plan_index.py`
- `scripts/generate_plan_index_tests.py`
- `skills/improve/references/plan-template.md`
- `skills/improve/references/closing-the-loop.md`
- `skills/improve/SKILL.md`

**Out of scope**:

- Host dispatch implementation and host capability discovery; IMP-004 owns it.
- Trust profile definitions; IMP-003 owns them.
- A database or non-file backlog service.
- Automatically publishing issues, merging branches, or deleting worktrees.
- General YAML support beyond IMP-002's validated subset.

## Git workflow

- Branch: `advisor/008-complete-lifecycle-index`
- Commit message: `feat: project complete plan lifecycle state`.
- Keep schema, rendering, documentation, and fixtures in one logical commit.
- Do not push or open a PR unless instructed.

## Steps

### Step 1: Define portable lifecycle fields

Extend the plan template and IMP-002 validation with these fields:

- `execution_profile`: null or `trusted-local | strict | manual`;
- `execution_locator`: null or a nonempty string identifying a local worktree,
  remote task, branch/PR URL, or other host-native execution artifact;
- `execution_branch`: existing nullable branch name;
- `execution_base`: existing nullable full SHA;
- `executor_head`: nullable full SHA after execution;
- `reviewed_commit`: existing nullable full SHA;
- `merged_commit`: existing nullable full SHA;
- `verification_environment`: null or `restricted-sandbox |
  host-approval-policy | user-confirmed-normal-account | not-run | unknown`;
- `status_note`: null or a concise one-line blocked/rejected/abandoned/superseded
  rationale;
- `skill_version`: null or the improve version (from `SKILL.md`
  `metadata.version`) that wrote the plan, so template drift across versions is
  detectable;
- `issue`: existing nullable URL.

Deliberately omitted: a `dependency_notes` list. The `dependencies` field plus
plan prose already carry that information; do not add fields the workflow never
reads back.

Define cross-field invariants:

- EXECUTING and later execution-derived states require `execution_locator`,
  `execution_base`, and `execution_profile` unless `status_note` explains a
  legacy/manual exception.
- REVIEWED requires `executor_head` and `reviewed_commit`.
- MERGED/VERIFIED require `reviewed_commit` and `merged_commit`.
- BLOCKED, REJECTED, ABANDONED, and SUPERSEDED require `status_note`.
- VERIFIED cannot use `verification_environment: not-run` or `unknown`.
- TODO normally leaves execution fields null.

Keep `execution_locator` opaque and human-readable. Do not parse it as a local
path or URL because host adapters own its meaning.

**Verify**: positive and negative fixtures cover every cross-field invariant.

### Step 2: Render status and execution projections separately

Keep the main execution-order table readable. Include:

- plan, title, priority, effort, dependencies, status, status note, and issue.

Add a second `Execution and verification details` table for plans with any
execution state, containing:

- plan, profile, locator, branch, execution base, executor head, reviewed
  commit, merged commit, and verification environment.

Escape Markdown table delimiters and newlines in scalar cells so metadata
cannot corrupt the generated table. Preserve deterministic plan ordering.

Append a `(sensitive)` marker (space-separated) to the title cell when
`sensitive: true`, so
operators see at a glance which plans must not be published as issues on a
public repository without the confirmation flow.

**Verify**: an exact-output fixture covers TODO, BLOCKED, REVIEWED, MERGED, and
VERIFIED plans plus an issue URL and a sensitive plan.

### Step 3: Give rejected audit findings a durable source

Define `docs/dev/plans/rejections.json` as the optional machine-readable source
for vetted findings that were considered but never became executable plans.
Use a top-level array of objects with exactly:

- `id` — original finding ID;
- `title` — concise finding title;
- `rationale` — why it was rejected;
- `evidence` — list of repository `file:line` references or an empty list when
  rejection was based on external/design evidence;
- `recorded_at` — `YYYY-MM-DD`.

Use the Python standard library JSON parser. Validate shape, duplicate IDs,
dates, and nonempty title/rationale. On invalid JSON or schema, fail generation
and preserve the previous README exactly as with invalid plans. Render a
`Findings considered and rejected` section; render an explicit `None recorded`
when the file does not exist or is an empty valid array.

Update `SKILL.md` vet/reconcile guidance to write this source, not hand-edit the
generated index. Rejection `id` values must trace back to the audit: add an ID
column (`[CATEGORY-NN]`, the playbook's finding identifier) to the Phase 3
findings table in `SKILL.md` so a rejection record, the presented finding, and
any later re-audit all reference the same stable identifier. Do not create a
repository-level `rejections.json` in this implementation unless there is an
actual rejection to record; tests generate fixtures in temporary directories.

**Verify**: fixtures cover absent, empty, valid, duplicate-ID, malformed JSON,
and invalid-object cases.

### Step 4: Align execute, verdict, reconcile, and cleanup instructions

Update `closing-the-loop.md` so every dispatch/review transition updates the
authoritative plan fields before regenerating the index. Use
`execution_locator` instead of assuming a local worktree path. Cleanup applies
only when the locator is a local worktree managed by the current operator;
remote task/branch/PR cleanup follows host policy and requires explicit user
authority.

Define transition ownership:

- advisor sets EXECUTING metadata before dispatch;
- reviewer sets REVIEWED or BLOCKED plus status note after review;
- reconcile sets MERGED and VERIFIED only after reachability/verification;
- operator decisions set ABANDONED/SUPERSEDED with rationale.

IMP-009 later narrows enforcement of this ownership (executors never write
plan records); keep the wording here compatible with that boundary.

**Verify**: every required report fact has a named metadata destination and
every lifecycle transition states who writes it.

### Step 5: Expand the fixture suite

Add tests for rendering and validation of all new fields and transitions. Test
Markdown escaping with a safe synthetic title/note containing `|` and a
newline. Assert no secrets or arbitrary repository content are transformed;
the generator is a projection, not an evaluator.

**Verify**: `python scripts/generate_plan_index_tests.py`,
`python scripts/check.py`, and `python scripts/check_tests.py` all exit 0.

## Test plan

- Build all lifecycle fixtures in `scripts/generate_plan_index_tests.py` using
  temporary plans and `rejections.json`.
- Test valid and invalid state transitions as static metadata snapshots; the
  generator need not maintain a history database.
- Assert exact generated Markdown for both tables, the sensitive marker, and
  rejections.
- Assert invalid auxiliary JSON leaves an existing README unchanged.
- Assert local and remote locator strings render identically as opaque text.

## Done criteria

- [ ] Every fact required by execute/review/reconcile has an authoritative
      metadata field or documented rejection source.
- [ ] Cross-field lifecycle invariants reject impossible states.
- [ ] The main table remains readable and a separate execution-detail table
      exposes complete provenance.
- [ ] Issue URLs, status rationales, sensitive markers, profile, locator,
      executor head, verification environment, and skill version are generated.
- [ ] The Phase 3 findings table carries the `[CATEGORY-NN]` finding ID that
      rejection records reference.
- [ ] Vetted rejected findings persist through validated `rejections.json` and
      appear in the generated index.
- [ ] Local cleanup is never inferred for remote execution locators.
- [ ] Markdown cell content is escaped deterministically.
- [ ] `python scripts/generate_plan_index_tests.py` exits 0.
- [ ] `python scripts/check.py` and `python scripts/check_tests.py` exit 0.
- [ ] No files outside the five in-scope paths are modified.
- [ ] The executor report contains STATUS, HEAD SHA, FILES CHANGED,
      VERIFICATION RESULTS, and NOTES; the reviewer owns lifecycle metadata and
      index regeneration.

## STOP conditions

Stop and report if:

- IMP-002 validation and atomic index protection are not present.
- A lifecycle requirement cannot be represented without nested YAML; prefer a
  flat field or documented JSON source rather than expanding the parser ad hoc.
- Host-specific locator parsing is proposed in the generator.
- The new tables become unreadable enough to require a UI or database; keep the
  Markdown projection compact and propose a separate direction plan.
- More than the five in-scope files are needed.

## Maintenance notes

- Adding a lifecycle status now requires updating validation, cross-field
  invariants, rendering, transition guidance, and fixtures together.
- `status_note` is concise provenance, not a place to paste logs or secrets.
- Keep the index reproducible from plan files plus `rejections.json`; chat
  history must never be required to reconstruct backlog state.
