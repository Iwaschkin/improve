---
id: IMP-010
title: Resolve and propagate one selected plans directory
status: TODO
priority: P2
effort: M
risk: LOW
category: bug
base_commit: 4adde10c1d1d6308c485b87efbbefb6a6a241785
working_tree_clean: true
created_at: 2026-07-19
updated_at: 2026-07-19
scope:
  - skills/improve/SKILL.md
  - skills/improve/references/closing-the-loop.md
  - skills/improve/references/plan-template.md
  - skills/improve/resources/generate_plan_index.py
  - skills/improve/resources/plan_state.py
  - scripts/generate_plan_index_tests.py
  - README.md
dependencies:
  - IMP-009
execution_branch: null
execution_base: null
reviewed_commit: null
merged_commit: null
sensitive: false
issue: null
---

## Plan 010: Resolve and propagate one selected plans directory

> **Executor instructions**: Make plan-directory selection explicit and carry
> the selected literal path through the complete workflow. Do not modify this
> plan or its generated index. Report STATUS, HEAD SHA, FILES CHANGED,
> VERIFICATION RESULTS, and NOTES; the reviewer owns lifecycle metadata and
> index regeneration.
>
> **Drift check (run first)**: run
> `git diff --stat 4adde10c1d1d6308c485b87efbbefb6a6a241785..HEAD -- skills/improve/SKILL.md skills/improve/references/closing-the-loop.md skills/improve/references/plan-template.md skills/improve/resources/generate_plan_index.py skills/improve/resources/plan_state.py scripts/generate_plan_index_tests.py README.md`.
> `plan_state.py` and `generate_plan_index_tests.py` do not exist at the planned
> base. Stop unless IMP-009 is VERIFIED, then use its final CLI and ownership
> contract rather than reintroducing a parallel directory-resolution path.

## Status

- **Status**: TODO
- **Priority**: P2
- **Effort**: M
- **Risk**: LOW
- **Depends on**: IMP-009
- **Category**: bug
- **Planned at**: commit `4adde10c1d1d6308c485b87efbbefb6a6a241785`, 2026-07-19
- **Working tree clean**: true
- **Issue**: none

## Why this matters

The skill correctly notices that `docs/dev/plans/` may already belong to an
unrelated system and offers `docs/dev/advisor-plans/` as a fallback. That choice
is not propagated. Index generation, execution worktrees, ignore rules,
inlined-plan guidance, reconciliation, issue publication, and cleanup continue
to name `docs/dev/plans/`. A run can therefore create a plan in the safe
alternate directory and later read, write, execute, or delete relative to the
wrong one.

The workflow needs one repository-relative selected plans directory, resolved
once during recon and reused literally for the rest of the session and every
handoff. Helpers should operate only on the explicitly supplied directory.

## Current state

- `skills/improve/SKILL.md:24` and `:99` allow
  `docs/dev/advisor-plans/` when `docs/dev/plans/` is unrelated.
- `skills/improve/SKILL.md:84`, `:91-92`, `:115`, `:125-128` revert to
  `docs/dev/plans/` for defaults, generation, plan review, execution, and issue
  handling.
- `skills/improve/references/plan-template.md:11`, `:65`, and `:200` hard-code
  the default directory into filenames, dependency prose, and index guidance.
- `skills/improve/references/closing-the-loop.md:14`, `:24-27`, `:40`,
  `:50`, `:105`, `:107`, and `:111-119` hard-code it throughout eligibility,
  worktree placement, ignore handling, dispatch, cleanup, and reconciliation.
- `skills/improve/resources/generate_plan_index.py:2`, `:134`, and `:141`
  describe a fixed default even though the implementation accepts a plan
  directory argument.
- There is no session invariant requiring planning, execute, reconcile, review,
  issue, and cleanup modes to use the same directory.

## Commands you will need

| Purpose | Command | Provenance | Execution class | Expected on success |
| --- | --- | --- | --- | --- |
| Directory-selection fixtures | `python scripts/generate_plan_index_tests.py` | IMP-002, extended here | EXECUTES_REPOSITORY_CODE | default, alternate, and arbitrary-path cases pass |
| Validate selected directory | `python skills/improve/resources/plan_state.py --plans-dir docs/dev/plans validate` | IMP-009 | EXECUTES_REPOSITORY_CODE | exit 0 for the literal selected path |
| Regenerate selected index | `python skills/improve/resources/generate_plan_index.py --plans-dir docs/dev/plans` | existing | EXECUTES_REPOSITORY_CODE | only the selected directory index changes |
| Structural checker | `python scripts/check.py` | existing CI | EXECUTES_REPOSITORY_CODE | exit 0 |
| Checker fixtures | `python scripts/check_tests.py` | existing CI | EXECUTES_REPOSITORY_CODE | all pass |
| Whitespace | `git diff --check` | Git standard | GIT_READ | exit 0 |

The documented commands above demonstrate the default choice. When the
alternate is selected, render each command with the literal
`docs/dev/advisor-plans` argument. Do not rely on a persistent `cd`, shell
variable, environment variable, command substitution, or shell-specific path
syntax to carry the choice.

## Scope

One behavioral objective: choose one plans directory safely and use that same
literal path in every planning and lifecycle operation.

**In scope**:

- `skills/improve/SKILL.md`
- `skills/improve/references/closing-the-loop.md`
- `skills/improve/references/plan-template.md`
- `skills/improve/resources/generate_plan_index.py`
- `skills/improve/resources/plan_state.py`
- `scripts/generate_plan_index_tests.py`
- `README.md`

**Out of scope**:

- Moving, merging, or deleting either existing plan directory automatically.
- Supporting plan directories outside the selected repository root.
- Inferring that arbitrary Markdown in `docs/dev/plans/` belongs to improve.
- Changing plan lifecycle or non-ancestral integration semantics.
- Introducing host-specific state storage for the selected path.

## Git workflow

- Branch: `advisor/010-selected-plans-directory`.
- Commit message: `fix: propagate the selected plans directory`.
- Keep selection rules, all path consumers, helper wording, and fixtures in one
  commit; a partial conversion is more dangerous than the current explicit
  default.
- Do not move real user plans as an implementation shortcut. Tests must use
  temporary fixture repositories/directories.

## Steps

### Step 1: Define a deterministic directory-selection contract

At the first planning/reconciliation recon, inspect plan files rather than
directory names alone and resolve one repository-relative **selected plans
directory**:

1. If neither candidate exists, select `docs/dev/plans/`.
2. If `docs/dev/plans/` contains a recognizable improve backlog, select it.
   Recognition requires validated `IMP-NNN` plan frontmatter, not a README
   phrase alone.
3. If `docs/dev/plans/` exists for an unrelated purpose and
   `docs/dev/advisor-plans/` is absent or contains a recognizable improve
   backlog, select `docs/dev/advisor-plans/`.
4. If both directories contain improve backlogs, or either contains a mixture
   that cannot be classified safely, stop and ask the user which backlog is
   authoritative. Do not combine, renumber, overwrite, or choose by mtime.
5. Reject an absolute path, `..` traversal, or a path resolving outside the
   selected repository root.

Record the choice in the user-facing recon/update and use it for the entire
logical invocation. Subsequent modes that start in a fresh session repeat the
same deterministic recon; when ambiguity remains, they stop rather than
silently selecting a different backlog.

**Verify**: temporary fixtures cover absent, recognized default, unrelated
default, recognized alternate, both-recognized, mixed, absolute, and traversal
cases with deterministic outcomes.

### Step 2: Replace fixed operational paths with one placeholder

Revise `SKILL.md`, `plan-template.md`, and `closing-the-loop.md` to define
`<selected-plans-dir>` once and use that placeholder for every downstream
operation:

- plan creation, numbering, dependency references, plan review, and generated
  README;
- eligibility checks and reviewer lifecycle updates;
- `.worktrees/` placement and the directory-local `.gitignore` entry;
- full plan text inlining and executor prompts;
- issue lookup/publication records;
- execution review, cleanup, orphan detection, and reconcile reads;
- rejection history and any lifecycle notes added by IMP-008.

Examples may show the default and alternate values, but normative steps must
say to replace the placeholder with the already selected literal path. Remove
language that sends only one mode back to the default. Ensure the selected plan
file itself remains inlined when uncommitted regardless of which directory is
chosen.

**Verify**: walk every documented mode (`audit`, planning, `review-plan`,
`execute`, `reconcile`, and `--issues`) with the alternate selected and list all
filesystem paths; none resolve under `docs/dev/plans/`.

### Step 3: Require explicit helper directory inputs

Make `--plans-dir` required for both `generate_plan_index.py` and
`plan_state.py`. Update CLI descriptions and diagnostics to say “selected plans
directory” rather than naming the default. Resolve the supplied path against
the current repository root, reject escape paths, and operate only within it.

Keep the helpers policy-neutral: they validate an explicit directory but do not
guess whether default or alternate should be selected. Selection belongs to
the skill workflow, where ambiguity can be surfaced to the user. A helper must
never scan both directories, copy plans, or create an index in an omitted
default location.

Preserve atomic generation and read-only eligibility. Report the normalized
repository-relative directory in successful output so reviewers can verify the
same location was used without relying on hidden process state.

**Verify**: omitting `--plans-dir` fails with usage and writes nothing; valid
default, alternate, and nested temporary paths affect only their explicit
target; outside-root inputs fail before reading or writing plan content.

### Step 4: Add wrong-directory regression fixtures

Extend `scripts/generate_plan_index_tests.py` with isolated temporary
repositories that place distinct sentinel plans/indexes in both candidate
directories. Cover:

- empty repository selects the default;
- unrelated default content selects the alternate without touching the
  unrelated files;
- recognized default backlog remains the selection;
- recognized alternate backlog is reused;
- two valid backlogs produce an explicit ambiguity stop;
- malformed or mixed content is not classified as safely reusable;
- generation, validation, and eligibility act only on the supplied directory;
- worktree/ignore/prompt/reconcile path rendering uses the same selected path;
- missing CLI argument and path escape attempts make no filesystem changes.

Use different plan IDs/statuses and pre-existing index hashes in each directory
so a test cannot pass while accidentally reading one directory and writing the
other. Test Windows separators at input boundaries while normalizing documented
repository-relative paths to forward slashes.

**Verify**: all fixtures pass on Windows and POSIX with no network access or
third-party packages.

### Step 5: Align user-facing documentation and conformance expectations

Update the root README's planning/lifecycle examples to describe the default,
the collision-safe alternate, and the one-directory invariant. Make clear that
the alternate is not Claude-specific and works identically in Codex, GitHub
Copilot, Claude Code, Cursor, and other Agent Skills hosts.

Keep selection, plan output, eligibility, execution worktree path,
reconciliation, and cleanup observable from the outside (paths in reports and
generated artifacts) so IMP-013's `PLANS-DIR-ALTERNATE` conformance case can
later exercise the full flow and confirm no write lands in the unrelated
default directory. Do not record a host conformance result as part of this
change.

**Verify**: README examples and all skill references use the same terms.

## Test plan

- Run selection fixtures for absent, default, alternate, conflicting, mixed,
  and path-escape repositories.
- Put sentinel content and pre-hashed indexes in both candidate directories;
  run each helper against one literal path and assert every byte in the other
  directory is unchanged.
- Render all documented operational paths with
  `docs/dev/advisor-plans` selected and assert no operational output contains
  `docs/dev/plans`.
- Invoke each helper without `--plans-dir` and with absolute/outside-root input;
  assert a nonzero exit and no writes.
- Run a Windows path-separator fixture and a POSIX fixture without persistent
  shell state.
- Run structural, checker, and generator tests plus `git diff --check`.

## Done criteria

- [ ] Selection has deterministic default, reuse, collision, and ambiguity
      rules based on validated plan content.
- [ ] One repository-relative selected path is reused across planning,
      review, execute, issues, reconciliation, worktrees, ignore rules, cleanup,
      rejection history, and index generation.
- [ ] Every normative command contains the selected literal path and requires
      no persistent shell or environment state.
- [ ] Both helpers require `--plans-dir`, reject repository escapes, and never
      guess or write to an omitted default.
- [ ] Alternate-directory workflows do not read or mutate an unrelated
      `docs/dev/plans/` tree.
- [ ] Ambiguous dual backlogs stop for user direction without moving, merging,
      deleting, or renumbering plans.
- [ ] Default, alternate, conflict, sentinel, and escape regression fixtures
      pass on Windows and POSIX.
- [ ] README terminology matches the implemented directory contract.
- [ ] Existing structural, checker, and generator checks pass.
- [ ] No files outside the seven in-scope paths are modified.
- [ ] The executor report contains STATUS, HEAD SHA, FILES CHANGED,
      VERIFICATION RESULTS, and NOTES; the reviewer owns lifecycle metadata and
      index regeneration.

## STOP conditions

Stop and report if:

- IMP-009 exposes a different helper invocation or authoritative state source;
  refresh this plan rather than adding compatibility branches.
- Existing content cannot be classified confidently as an improve backlog or
  unrelated content; preserve it and request user selection.
- Correct behavior would require moving, merging, deleting, or renumbering
  existing user plans.
- A selected path resolves outside the repository or aliases the other
  candidate through a symlink/junction; do not write until containment and
  identity are unambiguous.
- Any mode still needs an implicit default after selection; finish propagation
  before accepting the change.
- More than the seven in-scope files are required; split host adapter or
  migration work into a separate plan.

## Maintenance notes

- New plan consumers must accept `<selected-plans-dir>` explicitly and join
  child paths from it; never add a new independent default.
- Keep selection policy in the workflow and path validation/operation in the
  helpers so noninteractive tools cannot silently resolve ambiguity.
- Test both candidate directories whenever lifecycle, worktree, issue, or
  cleanup behavior changes.
- An alternate directory is a collision-avoidance mechanism, not a second
  concurrent backlog.
