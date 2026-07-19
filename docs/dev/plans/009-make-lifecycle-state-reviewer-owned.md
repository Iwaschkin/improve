---
id: IMP-009
title: Make lifecycle state reviewer-owned and gate execution from plan files
status: TODO
priority: P1
effort: M
risk: MED
category: bug
base_commit: 4adde10c1d1d6308c485b87efbbefb6a6a241785
created_at: 2026-07-19
updated_at: 2026-07-19
scope:
  - skills/improve/resources/plan_state.py
  - skills/improve/resources/generate_plan_index.py
  - scripts/generate_plan_index_tests.py
  - skills/improve/references/plan-template.md
  - skills/improve/references/closing-the-loop.md
  - skills/improve/SKILL.md
dependencies:
  - IMP-002
  - IMP-008
execution_base: null
reviewed_commit: null
merged_commit: null
sensitive: false
issue: null
---

## Plan 009: Make lifecycle state reviewer-owned and gate execution from plan files

> **Executor instructions**: Treat plan records and their generated index as
> reviewer-owned control-plane state. Implement only the source files listed in
> this plan's Scope; do not modify this plan or `docs/dev/plans/README.md`.
> Report STATUS, HEAD SHA, FILES CHANGED, VERIFICATION RESULTS, and NOTES. The
> reviewer performs lifecycle transitions and regenerates the index after
> reviewing your evidence.
>
> **Drift check (run first)**: run
> `git diff --stat 4adde10c1d1d6308c485b87efbbefb6a6a241785..HEAD -- skills/improve/resources/plan_state.py skills/improve/resources/generate_plan_index.py scripts/generate_plan_index_tests.py skills/improve/references/plan-template.md skills/improve/references/closing-the-loop.md skills/improve/SKILL.md`.
> `plan_state.py` and `generate_plan_index_tests.py` do not exist at the planned
> base. Stop unless IMP-002 (validated generator and fixture suite) and IMP-008
> (final lifecycle schema) have landed, then reconcile this plan with their
> final metadata schema and command policy before editing.

## Why this matters

The generated plan index is a projection for people, not an authorization
source. The current execute preflight nevertheless trusts dependency status in
that generated file. A missing, stale, or hand-edited index can therefore
disagree with the plan frontmatter that is supposed to own lifecycle state.
The workflow also asks an implementation executor to update the selected plan
record even though the executor's implementation boundary excludes it. That
mixes reviewer decisions with unreviewed implementation work and makes it hard
to tell who asserted that a plan was reviewed or verified.

Execution eligibility must be derived from validated plan files. Executors
should return evidence only; the reviewer should own every plan transition and
the subsequent regeneration of the read-only index projection.

## Current state

- `skills/improve/references/closing-the-loop.md:14` says dependencies must show
  VERIFIED in `docs/dev/plans/README.md`; it does not require the authoritative
  dependency plan files to have that state.
- `skills/improve/references/plan-template.md:48-50` tells the executor to
  update the plan frontmatter and regenerate the index when finished.
- `skills/improve/references/closing-the-loop.md:50-51` overrides only index
  regeneration in the executor prompt, leaving the frontmatter mutation
  instruction active.
- `skills/improve/SKILL.md:101` describes lifecycle fields but does not assign
  transition ownership or define an executable-state check.
- `skills/improve/resources/generate_plan_index.py` contains the only plan
  frontmatter reader. After IMP-002 it should reject malformed metadata, but a
  second ad hoc parser would let eligibility and index generation disagree.
- IMP-008 defines the broader lifecycle model. This plan narrows the ownership
  boundary and the pre-dispatch dependency decision without reopening that
  model.

## Commands you will need

| Purpose | Command | Provenance | Execution class | Expected on success |
| --- | --- | --- | --- | --- |
| Plan-state and generator fixtures | `python scripts/generate_plan_index_tests.py` | IMP-002, extended here | EXECUTES_REPOSITORY_CODE | all valid and invalid fixtures pass |
| Validate real plan files | `python skills/improve/resources/plan_state.py --plans-dir docs/dev/plans validate` | added here | EXECUTES_REPOSITORY_CODE | exit 0 and deterministic validation summary |
| Regenerate index | `python skills/improve/resources/generate_plan_index.py --plans-dir docs/dev/plans` | existing, refactored here | EXECUTES_REPOSITORY_CODE | atomic index refresh from validated plans |
| Structural checker | `python scripts/check.py` | existing CI | EXECUTES_REPOSITORY_CODE | exit 0 |
| Checker fixtures | `python scripts/check_tests.py` | existing CI | EXECUTES_REPOSITORY_CODE | all pass |
| Whitespace | `git diff --check` | Git standard | GIT_READ | exit 0 |

Run repository code only under the execution profile and host permission
decision established by IMP-003. The read-only Git commands remain useful when
repository-code execution is not authorized.

## Scope

One behavioral objective: make validated plan files the sole source of
execution eligibility and reserve lifecycle mutations for the reviewer.

**In scope**:

- `skills/improve/resources/plan_state.py` (create)
- `skills/improve/resources/generate_plan_index.py`
- `scripts/generate_plan_index_tests.py`
- `skills/improve/references/plan-template.md`
- `skills/improve/references/closing-the-loop.md`
- `skills/improve/SKILL.md`

**Out of scope**:

- Choosing or propagating an alternate plan directory; IMP-010 owns that.
- Recognizing squash, cherry-pick, or rebased integration; IMP-011 owns that.
- Letting the helper mutate lifecycle state automatically.
- Changing the statuses and transition meanings established by IMP-008.
- Editing any existing project plan as part of executor implementation.

## Git workflow

- Branch: `advisor/009-reviewer-owned-lifecycle`.
- Commit message: `fix: make plan eligibility authoritative`.
- Keep shared parsing, the read-only eligibility command, tests, and workflow
  wording in one commit so no documentation path can invoke an unchecked gate.
- The implementation commit must not contain a lifecycle transition for this
  plan or a generated project-plan index; the reviewer records those separately
  after review.

## Steps

### Step 1: Extract one strict plan-state reader

Create `skills/improve/resources/plan_state.py` and move the validated loading,
normalization, and cross-plan checks established by IMP-002 into importable
functions. `generate_plan_index.py` must import those functions rather than
retaining a second parser. Keep the module standard-library-only and free of
import-time filesystem writes.

The shared reader must return typed normalized records only after validating:

- filename/id/number agreement and monotonic topological order;
- required keys, scalar/list types, enum values, full SHA/null fields, and
  allowed status-dependent combinations;
- unique plan IDs and filenames;
- every dependency exists, is not self-referential, and forms an acyclic graph;
- every dependency points to an earlier plan number.

Diagnostics must include the plan path and field, remain stable enough for
fixture assertions, and never fall back to partially parsed values. Preserve
IMP-002's atomic index-write behavior: invalid input leaves an existing index
unchanged.

**Verify**: the generator and plan-state CLI reject exactly the same malformed
fixtures with the same primary diagnostic.

### Step 2: Add a read-only execution eligibility command

Give `plan_state.py` two explicit subcommands:

- `validate` validates the whole selected plan directory and exits without
  changing files;
- `check-executable IMP-NNN` validates the whole directory, then checks that the
  selected plan exists, has status TODO, and every transitive and direct
  dependency has status VERIFIED.

Use exit code `0` for eligible/valid, `2` for invalid plan data or invocation,
and `3` for a valid backlog whose selected plan is ineligible. Print a concise,
deterministically ordered explanation suitable for an agent transcript. For an
ineligible plan, list every blocking dependency with its authoritative status,
not only the first one.

The command must read plan frontmatter directly. A missing README, a stale
README, or a README claiming VERIFIED while its plan says TODO must have no
effect. Do not silently regenerate the index during a preflight and do not
change the selected plan to EXECUTING; those are reviewer actions after the
gate succeeds.

**Verify**: a fixture with a falsified README and a TODO dependency exits `3`,
while the same plans with that dependency set to VERIFIED exit `0` whether the
README is correct, stale, or absent.

### Step 3: Make the reviewer the lifecycle writer

Update `SKILL.md`, `plan-template.md`, and `closing-the-loop.md` so the workflow
has one unambiguous owner:

1. The planner/reviewer creates and refreshes plan metadata and the index.
2. Immediately before dispatch, the reviewer runs `check-executable` using the
   literal plan ID and selected plans directory.
3. If eligible, the reviewer records EXECUTING plus the execution branch/base,
   validates the plans, and regenerates the index before dispatch.
4. The executor treats the selected plan record and generated index as
   read-only, changes implementation scope only, and returns `STATUS`, `HEAD
   SHA`, `FILES CHANGED`, `VERIFICATION RESULTS`, and `NOTES`.
5. After independently reviewing the commit/diff and permitted checks, the
   reviewer records REVIEWED or BLOCKED and regenerates the index.
6. Reconcile remains responsible for later integration and verification
   transitions.

Remove every generic instruction for an executor to edit its plan frontmatter
or index. The selected plan record and generated index remain outside the
executor diff even when the implementation itself updates the skill's template
or helper source files. If an implementation unexpectedly changes control-plane
records, the reviewer must reject or isolate those changes before accepting the
implementation.

**Verify**: a repository search finds no executor-facing instruction to update
the selected plan or generated index, and every dispatch path invokes the
authoritative check before recording EXECUTING.

### Step 4: Add regression fixtures for authority and ownership

Extend `scripts/generate_plan_index_tests.py` with temporary plan directories
covering:

- verified direct and transitive dependencies;
- TODO, BLOCKED, REJECTED, ABANDONED, and SUPERSEDED blockers;
- missing selected plan and a selected plan already EXECUTING;
- stale README says VERIFIED while dependency frontmatter says TODO;
- stale README says TODO while dependency frontmatter says VERIFIED;
- no README at all;
- malformed, duplicate, missing, cyclic, and out-of-order dependencies;
- generator and eligibility CLI diagnostic parity;
- no filesystem changes from `validate` or `check-executable`.

Also add a small contract assertion over the executor prompt/template that
requires the five report fields and forbids instructions to modify the selected
plan record or generated index. Prefer testing stable markers or helper-rendered
prompt text over brittle full-document snapshots.

**Verify**: the fixture script passes from the repository root on Windows and
POSIX without PyYAML, shell pipelines, or network access.

### Step 5: Wire the shared checks into the documented workflow

Update command examples and prose to call the helper through a resolved skill
root, use a literal selected plan ID/path, and keep each command independently
runnable as required by IMP-005. Document that the generated README is useful
for discovery and reporting only; operational decisions always re-read and
validate plan files.

Do not add automatic lifecycle writes to either helper. If a future workflow
wants transactional state transitions, it needs a separate plan with locking,
expected-old-state checks, recovery semantics, and explicit reviewer authority.

**Verify**: follow the execute preflight from a fresh shell using only the
documentation, and confirm that deliberately corrupting the index cannot alter
the decision.

## Test plan

- Run all new valid/invalid plan-state fixtures in
  `scripts/generate_plan_index_tests.py`.
- Build a temporary three-plan chain and prove transitive TODO blocks the third
  plan even when the generated index claims all dependencies are VERIFIED.
- Delete the temporary index and prove plan validation and eligibility still
  work; regenerate it and prove the rows match the same normalized records.
- Capture before/after recursive file hashes around both read-only subcommands
  to prove they do not write.
- Exercise the documented reviewer/executor prompt rendering and assert the
  five-field report contract is present while lifecycle-write instructions are
  absent.
- Run the structural checker, checker fixtures, and `git diff --check`.

## Done criteria

- [ ] Generator and eligibility decisions consume one strict shared parser and
      validator.
- [ ] `validate` and `check-executable` are deterministic, read-only, and have
      documented exit codes.
- [ ] Eligibility comes exclusively from validated plan files, including all
      transitive dependency statuses.
- [ ] A missing, stale, or falsified README cannot permit or block execution.
- [ ] Executor instructions prohibit selected-plan and generated-index writes
      and require the five-field evidence report.
- [ ] Reviewer instructions own TODO -> EXECUTING -> REVIEWED/BLOCKED and index
      regeneration; reconcile owns later transitions.
- [ ] Invalid metadata still preserves the last valid generated index.
- [ ] Authority, ownership, transitive dependency, and no-write fixtures pass.
- [ ] Existing structural, checker, and generator checks pass.
- [ ] No files outside the six in-scope paths are modified.
- [ ] The executor report contains STATUS, HEAD SHA, FILES CHANGED,
      VERIFICATION RESULTS, and NOTES; the reviewer owns lifecycle metadata and
      index regeneration.

## STOP conditions

Stop and report if:

- IMP-002 or IMP-008 lands with a different schema or lifecycle authority
  model; refresh this plan rather than creating competing rules.
- The generator cannot import the shared reader when invoked exactly as
  documented on both Windows and POSIX; fix module layout before duplicating
  parsing logic.
- A valid eligibility decision would require trusting generated or free-form
  prose rather than plan frontmatter.
- The change would make either read-only subcommand mutate metadata or the
  index.
- More than the six in-scope files are required; split CI wiring or automated
  transition tooling into a focused follow-up plan.

## Maintenance notes

- Treat plan frontmatter as authoritative data and the README/status prose as
  projections. Add new operational consumers through `plan_state.py`.
- When lifecycle fields or statuses change, update shared validation,
  generation, eligibility fixtures, and template prose together, and refresh
  the IMP-013 conformance cases that observe them.
- Keep eligibility conservative: unknown status or invalid dependency data is
  a visible stop, never an implicit pass.
- Reviewer ownership is an audit boundary, not just wording; preserve it in all
  future executor adapters.
