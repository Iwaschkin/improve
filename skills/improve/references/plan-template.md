# Handoff Plan Template

Every plan is written for an executor model that has **zero context**: it has not seen the advisor session, the audit, the other plans, or any prior conversation. It may be a smaller/cheaper model. Assume it is competent at following explicit instructions and weak at filling gaps, recovering from ambiguity, or knowing when to stop.

Three properties make a plan executable by a weaker model:

1. **Self-contained context** — everything needed is in the file: paths, code excerpts, conventions, commands.
2. **Verification gates** — every step ends with a command and its expected result. The executor never has to *judge* whether it succeeded.
3. **Hard boundaries and escape hatches** — explicit out-of-scope list, and "STOP and report" conditions instead of letting the model improvise when reality doesn't match the plan.

File naming: `<selected-plans-dir>/NNN-short-slug.md` (default `docs/dev/plans/`; the advisor resolves the selected directory once per the contract in `SKILL.md`), numbered in recommended execution order.

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
created_at: <YYYY-MM-DD>
updated_at: <YYYY-MM-DD>
scope:
  - <in-scope path>
dependencies: []
execution_locator: null
execution_base: null
reviewed_commit: null
merged_commit: null
verified_at: null
superseded_by: null
status_note: null
sensitive: false
issue: null
---

## Plan NNN: <Imperative title — what will be true after this plan>

> **Executor instructions**: Follow this plan step by step. Run every
> verification command your dispatch permits and confirm the expected result
> before moving to the next step; if repository-code execution is not
> permitted, skip those commands and report that they were not run. If
> anything in the "STOP conditions" section occurs, stop and report — do not
> improvise. For corrective plans: observe the stated condition before
> changing anything, fix the owning layer named below, verify the cause is
> absent afterward, and add no suppression, weakened test, retry, special
> case, or shim this plan does not explicitly justify — if the causal chain
> below is disproved, STOP and report rather than silencing the symptom.
> When finished, report STATUS, HEAD SHA, FILES CHANGED, VERIFICATION
> RESULTS, and NOTES. This plan's YAML frontmatter and the generated plan
> index are reviewer-owned — do not modify either.
>
> **Drift check (run first)**: `git diff --stat <base_commit>..HEAD -- <in-scope paths>`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

Lifecycle: status moves TODO → EXECUTING → REVIEWED → DONE (or BLOCKED /
REJECTED), written only by the advisor/reviewer, with the execution fields
filled in as each transition happens. The generated index is the
human-readable projection of this frontmatter — plans carry no duplicate
status section.

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

## Root cause and correct fix

(Required. Fill it from this plan's own evidence — never by referring to the
advisor session, another plan, another skill, or an unavailable reference.)

For corrective plans:

- **Applicability / causal status**: corrective, CONFIRMED (a HYPOTHESIS
  becomes an investigation plan with a decision gate before implementation; a
  NOT-APPLICABLE plan states its finding-specific reason and omits the rest
  of this section).
- **Observed condition**: the safely observed symptom, diagnostic, or static
  proof.
- **Causal chain**: input or condition → exercised code path or contract →
  specific flaw → observed symptom/impact, with `file:line` evidence at each
  non-obvious link.
- **Correct fix layer**: the contract/module/state boundary that owns the
  flaw, and why patching the symptom surface is not sufficient.
- **Prohibited shortcuts**: the symptom-level responses specific to this
  finding that the executor must not take.
- **Compatibility consumers**: known current consumers of any contract this
  plan changes or removes, and how they were established (public APIs,
  persisted data, config formats, protocols, and extension points are
  compatibility-sensitive even when a local call search is empty).
- **Exception gate record**: normally `none`. A planned workaround is
  acceptable only with all four: the confirmed cause; why the correct fix is
  genuinely unavailable here (with upstream/platform evidence); the correct
  fix and an objective removal condition; why this workaround is the
  narrowest possible and how it is tested.

Steps and tests must then prove causality: characterize the failing/unsafe
condition before the implementation change (or record why static proof is
safer), change the owning layer, remove now-obsolete code and unneeded
compatibility paths, and rerun the regression plus surrounding behavior so it
passes because the cause is absent.

## Commands you will need

| Purpose   | Command                  | Provenance | Expected on success |
|-----------|--------------------------|------------|---------------------|
| Install   | `pnpm install`           | package manager docs / CI / not run | exit 0 |
| Typecheck | `pnpm typecheck`         | package script / CI / not run | exit 0, no errors |
| Tests     | `pnpm test -- <filter>`  | package script / CI / not run | all pass |
| Lint      | `pnpm lint`              | package script / CI / not run | exit 0 |

Use exact commands from this repo, not guesses. For each command, state whether it was discovered in configuration, observed in CI, actually executed by the advisor, or not executed for safety reasons. Names prove nothing: a tool named `check` may execute repository code. Presume install, build, test, lint, framework-CLI, and package-script commands execute repository-controlled code unless there is concrete evidence otherwise; run only the commands your dispatch permits, and report the rest as not run.

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
- [ ] (corrective plans) The regression demonstrates the cause is absent, the
      diff contains no unjustified symptom silencer, obsolete paths are
      removed, and the compatibility decision matches the evidence in "Root
      cause and correct fix"
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] The final report contains STATUS, HEAD SHA, FILES CHANGED, VERIFICATION
      RESULTS, and NOTES; this plan file and the generated index are unmodified
      (the reviewer owns both)

## STOP conditions

Stop and report back (do not improvise) if:

- The code at the locations in "Current state" doesn't match the excerpts
  (the codebase has drifted since this plan was written).
- A verification fails unexpectedly: re-observe the condition first. If what
  you observe contradicts this plan's causal chain, stop and report — do not
  iterate speculative patches until something passes.
- The fix appears to require touching an out-of-scope file, or the owning
  layer for the confirmed cause lies outside this plan's scope.
- Completing the work would require a workaround the "Root cause and correct
  fix" section does not justify, weakening or skipping a test or guardrail,
  or a compatibility decision about a consumer this plan does not establish.
- Safe observation of a security-sensitive condition is impossible without an
  unsafe reproduction.
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

## Index file: `<selected-plans-dir>/README.md`

Generated from plan frontmatter by the bundled `resources/generate_plan_index.py` helper. The helper requires Python 3.10+: find an interpreter with `python3 --version` where that name is conventional, otherwise `python --version`, and accept only 3.10 or newer. Invoke the helper by the path of the currently loaded skill's `resources/` directory — never a guessed global install path. If no compatible interpreter or helper path is available, leave the plan files as they are and report that index generation is pending; the index never blocks the implementation.

The helper validates every plan against this template's schema before writing: malformed or missing frontmatter, invalid enums, short SHAs, filename/ID mismatches, unresolved or out-of-order dependencies, and impossible lifecycle states (a REVIEWED plan without a reviewed commit, a DONE plan without a merged commit and `verified_at`, a BLOCKED plan without a `status_note`) fail generation with a nonzero exit, and the previous index is preserved unchanged. Fix the reported plan files and rerun. The same helper is the execution-eligibility gate: `--check-executable IMP-NNN` exits 0 only when the plan is TODO and every direct and transitive dependency is DONE.

Closed plans (DONE or REJECTED) may be moved to `<selected-plans-dir>/archive/` to keep the active backlog lean: the helper validates archived plans identically, refuses any open status there, resolves dependency and supersede references against them, and lists them in a compact `Archived Plans` section instead of the main table.

The generated index renders the main status table (with status notes, issue URLs, and a `(sensitive)` marker on plans that must not be published without the confirmation flow), a compact execution-record line for any plan with execution state, and a `Findings Considered and Rejected` section sourced from an optional `rejections.json` beside the plans — a JSON array of objects with exactly `id` (the audit's `[CATEGORY-NN]` finding identifier), `title`, `rationale`, `evidence` (list of `file:line` strings, may be empty), and `recorded_at` (`YYYY-MM-DD`). Write rejections there, never by hand-editing the generated index; an invalid `rejections.json` fails generation and preserves the previous index.

Status values: TODO | EXECUTING | REVIEWED | DONE | BLOCKED | REJECTED.

## Quality bar — check before finishing each plan

- Could a model that has never seen this repo execute this with only the plan file and the repo? If any step requires knowledge from the advisor session, inline that knowledge.
- For a corrective plan: is the causal chain complete and evidenced, the correct fix layer named, and the prohibited-shortcut list specific to this finding rather than boilerplate?
- Is every verification a command with an expected result, not a judgment ("make sure it works")?
- Does every step name exact files and symbols, not "the relevant module"?
- Are the STOP conditions specific to this plan's actual risks, not boilerplate?
- Would a reviewer reading only "Why this matters" + "Done criteria" understand what they're approving?
- No secret values anywhere in the file — locations and credential types only.
- `base_commit` is filled in and the in-scope paths in the drift check match the Scope section.
