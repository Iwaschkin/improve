# Handoff Plan Template

Every plan is written for an executor model that has **zero context**: it has not seen the advisor session, the audit, the other plans, or any prior conversation. It may be a smaller/cheaper model. Assume it is competent at following explicit instructions and weak at filling gaps, recovering from ambiguity, or knowing when to stop.

Three properties make a plan executable by a weaker model:

1. **Self-contained context** — everything needed is in the file: paths, code excerpts, conventions, commands.
2. **Verification gates** — every step ends with a command and its expected result. The executor never has to *judge* whether it succeeded.
3. **Hard boundaries and escape hatches** — explicit out-of-scope list, and "STOP and report" conditions instead of letting the model improvise when reality doesn't match the plan.

File naming: `docs/dev/plans/NNN-short-slug.md`, numbered in recommended execution order.

---

## Template

```markdown
---
id: IMP-NNN
title: <Imperative title — what will be true after this plan>
status: TODO
priority: P1 | P2 | P3
effort: S | M | L
risk: LOW | MED | HIGH
category: bug | security | perf | tests | tech-debt | migration | dx | docs | direction
base_commit: <full 40-character SHA>
working_tree_clean: true | false
created_at: <YYYY-MM-DD>
updated_at: <YYYY-MM-DD>
scope:
  - <in-scope path>
dependencies: []
execution_branch: null
execution_base: null
execution_profile: null
execution_locator: null
executor_head: null
reviewed_commit: null
merged_commit: null
verification_environment: null
status_note: null
skill_version: null
sensitive: false
issue: null
---

## Plan NNN: <Imperative title — what will be true after this plan>

> **Executor instructions**: Follow this plan step by step. Run every
> verification command permitted by the execution environment and confirm the
> expected result before moving to the next step. If repository-code execution
> is not permitted, skip those commands and report that they were not run. If
> anything in the "STOP conditions" section occurs, stop and report — do not
> improvise. When finished, update this plan's YAML frontmatter and run the
> bundled `resources/generate_plan_index.py` helper — unless a reviewer
> dispatched you and told you they maintain the generated index, or you are
> executing this plan manually without the improve skill installed. In the
> manual case, report completion to the operator instead: the reviewer
> refreshes metadata and regenerates the index from an installed skill or
> repository checkout. Index generation is a projection — it never gates the
> implementation itself.
>
> **Drift check (run first)**: `git diff --stat <planned-at SHA>..HEAD -- <in-scope paths>`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

The fields below mirror the YAML frontmatter for human readers. The YAML frontmatter is authoritative; run the bundled `resources/generate_plan_index.py` helper after status changes.

- **Status**: TODO | EXECUTING | REVIEWED | MERGED | VERIFIED | BLOCKED | REJECTED | ABANDONED | SUPERSEDED
- **Priority**: P1 | P2 | P3
- **Effort**: S | M | L
- **Risk**: LOW | MED | HIGH
- **Depends on**: docs/dev/plans/NNN-*.md (or "none")
- **Category**: bug | security | perf | tests | tech-debt | migration | dx | docs | direction
- **Planned at**: commit `<full 40-character SHA>`, <YYYY-MM-DD>
- **Working tree clean**: true | false (automatic `execute` requires true)
- **Execution profile**: trusted-local | strict | manual (record when execution starts; omit until then)
- **Execution locator**: worktree path, remote task id, branch, or PR URL (set when execution starts; omit until then)
- **Execution base**: `<full 40-character SHA>` (set when execution starts; omit until then)
- **Executor head**: `<full 40-character SHA>` (set from the executor report; omit until then)
- **Reviewed commit**: `<full 40-character SHA>` (set when reviewer approves; omit until then)
- **Merged commit**: `<full 40-character SHA>` (set when reachable from target branch; omit until then)
- **Verification environment**: restricted-sandbox | host-approval-policy | user-confirmed-normal-account | not-run | unknown (set when verification runs; omit until then)
- **Status note**: one line — required for BLOCKED / REJECTED / ABANDONED / SUPERSEDED, omit otherwise
- **Issue**: <GitHub issue URL — only when published via `--issues`; omit otherwise>

## Why this matters

2–5 sentences. The problem, its concrete cost, and what improves when this
lands. Written so the executor (and a human reviewer) understands the intent —
intent is what lets a correct judgment call happen when a detail is off.

## Current state

The facts the executor needs, inlined — never "as discussed" or "see audit":

- The relevant files, each with one line on its role:
  - `src/orders/api.ts` — order-list endpoint; contains the N+1 (lines 130–160)
- Excerpts of the code as it exists today (short, with `file:line` markers),
  enough that the executor can confirm it's looking at the right thing.
- The repo conventions that apply here, with a pointer to one exemplar file:
  "Error handling follows the Result pattern — see `src/lib/result.ts` and its
  use in `src/users/api.ts:40-60`. Match it."
- Any documented vocabulary or design constraints the plan must honor, inlined
  from the intent/design docs found in recon: the relevant `CONTEXT.md` terms
  the executor should use in names and comments, the `DESIGN.md` tokens/components
  to reuse, or the ADR whose decision this work must stay consistent with. Quote
  the specific lines — the executor has not read those docs.

## Commands you will need

| Purpose   | Command                  | Provenance | Execution class | Expected on success |
|-----------|--------------------------|------------|-----------------|---------------------|
| Install   | `pnpm install`           | package manager docs / CI / not run | PACKAGE_INSTALL | exit 0 |
| Typecheck | `pnpm typecheck`         | package script / CI / not run | EXECUTES_REPOSITORY_CODE | exit 0, no errors |
| Tests     | `pnpm test -- <filter>`  | package script / CI / not run | EXECUTES_REPOSITORY_CODE | all pass |
| Lint      | `pnpm lint`              | package script / CI / not run | EXECUTES_REPOSITORY_CODE | exit 0 |

Use exact commands from this repo, not guesses. For each command, state whether it was discovered in configuration, observed in CI, actually executed by the advisor, or not executed for safety reasons. Execution class lists the command's *effects* — one or more of, comma-separated:

- `STATIC_READ` — reads files/configuration without executing repository code.
- `GIT_READ` — read-only Git operation.
- `NETWORK_ACCESS` — sends or receives data over a network.
- `MAY_WRITE_CACHE` — may write ignored/local cache state.
- `EXECUTES_REPOSITORY_CODE` — imports, builds, tests, lints, or invokes scripts, plugins, hooks, or binaries controlled by the repository or its dependencies.
- `PACKAGE_INSTALL` — resolves/downloads packages and may run lifecycle hooks.
- `HOST_MUTATION` — changes external services, system state, production data, Git remotes, or durable host configuration.

The class records what a command does, not permission. Permission follows the riskiest listed effect, the selected execution profile, and the host's actual enforcement. Names prove nothing: a tool named `check` may execute repository code, while an advisory query may use a package manager without running any script. Presume install, build, test, lint, framework-CLI, and package-script commands execute repository-controlled code unless there is concrete evidence otherwise.

## Suggested executor toolkit

(Optional — include only when relevant skills/tools plausibly exist in the
executor's environment. Skip the section otherwise.)

- Skills the executor should invoke if available, and for what:
  "use `vercel-react-best-practices` when writing the memoization in step 3".
- Reference docs worth reading before starting, by path or URL.

## Scope

Default size limits for executable plans:

- One behavioral objective.
- Prefer no more than 7 in-scope files.
- No broad rewrites, multi-package migrations, or unrelated cleanup.
- If the work exceeds those limits, split it into dependency-ordered plans before execution.

**In scope** (the only files you should modify):
- `src/orders/api.ts`
- `src/orders/api.test.ts` (create)

**Out of scope** (do NOT touch, even though they look related):
- `src/orders/legacy-api.ts` — deprecated path, scheduled for deletion;
  changing it wastes effort and risks the v1 clients still pinned to it.
- Any change to the public response shape — clients depend on it.

## Git workflow

(Filled from recon — match the repo's observed conventions.)

- Branch: `advisor/NNN-<slug>` (or the repo's branch-naming convention if one is evident)
- Commit per step or per logical unit; message style: <match repo, e.g. conventional commits — include an example from `git log`>
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: <imperative title>

What to do, precisely. Reference exact files/symbols. Include the target code
shape when it's load-bearing (the pattern to produce, not necessarily every
line).

**Verify**: `<command>` → <expected output>

### Step 2: ...

(Each step small enough to verify independently. Order steps so the codebase
is never broken between steps when possible — e.g. add new path, switch
callers, then remove old path.)

## Test plan

- New tests to write, in which file, covering which cases (list them:
  happy path, the specific bug/regression this plan fixes, named edge cases).
- Which existing test to use as the structural pattern:
  "model after `src/users/api.test.ts`".
- Verification: `<test command>` → all pass, including N new tests.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `pnpm typecheck` exits 0
- [ ] `pnpm test` exits 0; new tests for <X> exist and pass
- [ ] `grep -rn "<old pattern>" src/` returns no matches
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] YAML frontmatter updated with the current lifecycle state and the bundled `resources/generate_plan_index.py` helper rerun

## STOP conditions

Stop and report back (do not improvise) if:

- The code at the locations in "Current state" doesn't match the excerpts
  (the codebase has drifted since this plan was written).
- A step's verification fails twice after a reasonable fix attempt.
- The fix appears to require touching an out-of-scope file.
- The fix appears to exceed the plan's size limits (more than 7 in-scope files, a broad rewrite, or a multi-package migration not explicitly planned).
- You discover the assumption "<key assumption>" is false.

## Maintenance notes

For the human/agent who owns this code after the change lands:

- What future changes will interact with this (e.g. "if pagination is added
  to this endpoint, the batching in step 2 must be revisited").
- What a reviewer should scrutinize in the PR.
- Any follow-up explicitly deferred out of this plan (and why).
```

---

## Index file: `docs/dev/plans/README.md`

Generated from plan frontmatter by the bundled `resources/generate_plan_index.py` helper. The helper requires Python 3.10+: find an interpreter with `python3 --version` where that name is conventional, otherwise `python --version`, and accept only 3.10 or newer. Invoke the helper by the path of the currently loaded skill's `resources/` directory — never a guessed global install path. If no compatible interpreter or helper path is available, leave the plan files as they are and report that index generation is pending; the index never blocks the implementation.

The helper validates every plan against this template's schema before writing: malformed or missing frontmatter, invalid enums, short SHAs, filename/ID mismatches, unresolved or out-of-order dependencies, and impossible lifecycle states (a REVIEWED plan without an executor head, a VERIFIED plan whose verification never ran, a BLOCKED plan without a `status_note`) fail generation with a nonzero exit, and the previous index is preserved unchanged. Fix the reported plan files and rerun.

The generated index renders three sections: the main status table (with status notes, issue URLs, and a `(sensitive)` marker on plans that must not be published without the confirmation flow), an `Execution & Verification Details` table for any plan with execution state, and a `Findings Considered and Rejected` section sourced from an optional `rejections.json` beside the plans — a JSON array of objects with exactly `id` (the audit's `[CATEGORY-NN]` finding identifier), `title`, `rationale`, `evidence` (list of `file:line` strings, may be empty), and `recorded_at` (`YYYY-MM-DD`). Write rejections there, never by hand-editing the generated index; an invalid `rejections.json` fails generation and preserves the previous index.

```markdown
# Implementation Plans

Generated from plan frontmatter. Do not hand-edit this table; update the plan
file and rerun the bundled `resources/generate_plan_index.py` helper.

## Execution order & status

| Plan | Title | Priority | Effort | Depends on | Status | Execution base | Reviewed commit | Merged commit |
|------|-------|----------|--------|------------|--------|----------------|-----------------|---------------|
| 001  | ...   | P1       | S      | —          | TODO   | —              | —               | —             |
| 002  | ...   | P1       | M      | 001        | TODO   | —              | —               | —             |

Status values: TODO | EXECUTING | REVIEWED | MERGED | VERIFIED | BLOCKED (with one-line reason) | REJECTED (with one-line rationale — finding fixed independently or approach abandoned) | ABANDONED | SUPERSEDED

## Dependency notes

- 002 requires 001 because <reason>.

## Findings considered and rejected

- <finding>: not worth doing because <one line>. (So nobody re-audits it.)
```

## Quality bar — check before finishing each plan

- Could a model that has never seen this repo execute this with only the plan file and the repo? If any step requires knowledge from the advisor session, inline that knowledge.
- Is every verification a command with an expected result, not a judgment ("make sure it works")?
- Does every step name exact files and symbols, not "the relevant module"?
- Are the STOP conditions specific to this plan's actual risks, not boilerplate?
- Would a reviewer reading only "Why this matters" + "Done criteria" understand what they're approving?
- No secret values anywhere in the file — locations and credential types only.
- "Planned at" SHA is filled in and the in-scope paths in the drift check match the Scope section.
