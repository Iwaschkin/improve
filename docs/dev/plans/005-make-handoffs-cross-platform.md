---
id: IMP-005
title: Make Git and plan handoffs cross-platform
status: TODO
priority: P1
effort: M
risk: LOW
category: dx
base_commit: 4adde10c1d1d6308c485b87efbbefb6a6a241785
created_at: 2026-07-19
updated_at: 2026-07-19
scope:
  - skills/improve/SKILL.md
  - skills/improve/references/closing-the-loop.md
  - skills/improve/references/plan-template.md
  - examples/001-extract-shadow-config-resolution.md
  - README.md
dependencies:
  - IMP-003
  - IMP-004
execution_base: null
reviewed_commit: null
merged_commit: null
sensitive: false
issue: null
---

## Plan 005: Make Git and plan handoffs cross-platform

> **Executor instructions**: Follow the plan in order. Do not replace one
> shell-specific recipe with another. Commands in normative guidance must work
> as separate process invocations on Windows, macOS, and Linux. Do not modify
> this plan or the generated index. Report STATUS, HEAD SHA, FILES CHANGED,
> VERIFICATION RESULTS, and NOTES; a reviewer owns lifecycle metadata and index
> regeneration.
>
> **Drift check (run first)**: run
> `git diff --stat 4adde10c1d1d6308c485b87efbbefb6a6a241785..HEAD -- skills/improve/SKILL.md skills/improve/references/closing-the-loop.md skills/improve/references/plan-template.md examples/001-extract-shadow-config-resolution.md README.md`.
> Stop if IMP-003 or IMP-004 is not present, or if another change has already
> replaced the Git command contract.

## Why this matters

The skill targets Codex, Copilot, Claude Code, and Cursor on multiple operating
systems, but several normative Git recipes assume POSIX command substitution or
a persistent shell variable. Agent shell calls are often separate processes,
so even POSIX hosts cannot rely on state surviving from one tool call to the
next. Plans and executor prompts must carry literal full SHAs, and manual
handoffs must not depend on an installed copy of this skill or an undeclared
Python command name.

## Current state

- `skills/improve/references/closing-the-loop.md:17` records the base with:

  ```text
  EXECUTION_BASE_SHA=$(git rev-parse HEAD)
  ```

  Lines 80 and 82 later use `$EXECUTION_BASE_SHA`. This is POSIX syntax and
  assumes shell state persists.
- `skills/improve/SKILL.md:122` computes the branch scope in one command using
  `$(git merge-base origin/<default> HEAD)`.
- `skills/improve/SKILL.md:126` tells the reviewer to compare
  `$EXECUTION_BASE_SHA..HEAD`.
- `skills/improve/references/plan-template.md` requires a full 40-character
  `base_commit`, but its helper instruction uses the placeholder
  `python <path-to-skill>/resources/generate_plan_index.py`. A manual executor
  may not have the skill installed at that path, and Python 3.10+ is not
  declared even though the bundled generator uses PEP 604 union syntax.
- `examples/001-extract-shadow-config-resolution.md:9`, line 42, and line 55 use
  the short SHA `1994caba0`. The drift check at line 42 omits the in-scope
  `packages/shadcn/src/registry/config.test.ts` path.
- `README.md:56` describes review as `EXECUTION_BASE_SHA..HEAD`, reinforcing the
  variable rather than the value.
- `skills/improve/references/closing-the-loop.md:134` shows the `--issues`
  duplicate search as
  `gh issue list --state all --search "\"IMP-014\" OR \"<plan title>\"" ...`,
  whose nested escaped quotes parse differently under PowerShell and POSIX
  shells.
- CI establishes Python 3.12 as the current tested runtime in
  `.github/workflows/check.yml:17-19`, but this plan does not modify CI.
- Match existing conventions: exact Git commands, full hashes in metadata, and
  explicit command provenance.

## Commands you will need

| Purpose | Command | Provenance | Execution class | Expected on success |
| --- | --- | --- | --- | --- |
| Structural validation | `python scripts/check.py` | CI; not run by advisor | EXECUTES_REPOSITORY_CODE | exit 0 |
| Checker fixtures | `python scripts/check_tests.py` | CI; not run by advisor | EXECUTES_REPOSITORY_CODE | all pass |
| Python runtime | `python --version` | CI currently selects Python 3.12; not run by advisor | STATIC_READ | reports Python 3.10 or newer |
| Git whitespace | `git diff --check` | Git standard; not run by advisor | GIT_READ | exit 0 |

Use commands as separate invocations. Do not join them with `&&`, `;`, pipes,
subshells, or environment assignments in normative instructions.

## Scope

One behavioral objective: make every handoff, drift check, branch comparison,
and helper invocation independent of shell syntax and hidden session state.

**In scope**:

- `skills/improve/SKILL.md`
- `skills/improve/references/closing-the-loop.md`
- `skills/improve/references/plan-template.md`
- `examples/001-extract-shadow-config-resolution.md`
- `README.md`

**Out of scope**:

- Rewriting the generator parser or schema; IMP-002 and IMP-008 own that.
- Host dispatch primitives; IMP-004 owns those.
- Adding a second implementation of the generator in another language.
- Fetching or changing the historical example's source code.

## Git workflow

- Branch: `advisor/005-cross-platform-handoffs`
- Commit message: `docs: make plan handoffs shell-neutral`.
- One documentation commit is sufficient.
- Do not push or open a PR unless instructed.

## Steps

### Step 1: Replace shell state with captured literal values

In `closing-the-loop.md`, specify this host-neutral sequence:

1. Run `git rev-parse HEAD` as a standalone command.
2. Validate that the output is one 40-character hexadecimal SHA.
3. Copy that literal value into the executor prompt, report, plan metadata, and
   every subsequent `git diff <literal>..HEAD` command.

Use placeholders such as `<full-execution-base-sha>` only when authoring a
template; tell the acting agent to substitute the literal before execution.
Never rely on `$NAME`, `%NAME%`, `$env:NAME`, command substitution, `cd`
persistence, or a shell variable across tool calls.

Make the same change for executor head, reviewed commit, merged commit, and
target branch SHA. Show `git -C <execution-path> ...` only for local locators;
remote adapters must use their native diff/commit identity from IMP-004.

**Verify**: a literal-text search of normative examples finds no use of
`$EXECUTION_BASE_SHA` or `EXECUTION_BASE_SHA=$(...)`.

### Step 2: Split merge-base discovery from branch diffing

Rewrite the `branch` variant as separate operations:

1. discover the default branch without shell substitution;
2. run `git merge-base origin/<default> HEAD`;
3. validate and retain the returned full SHA;
4. run `git diff --name-only <literal-merge-base-sha>..HEAD`;
5. separately inspect staged, unstaged, and untracked paths with
   `git status --porcelain=v1` and relevant Git reads.

State that a host may represent these as separate tool calls rather than shell
commands. Include failure behavior for missing remotes/default branches instead
of guessing `main`.

**Verify**: `SKILL.md` contains no `$(` command substitution.

### Step 3: Make index ownership and runtime requirements explicit

Change the executor contract so the advisor/reviewer owns plan-frontmatter and
generated-index updates whenever it dispatches or reviews work. A manual plan
executor must be able to complete the implementation and return the required
lifecycle report without modifying the plan or having the `improve` skill
installed. Its report must tell the operator that the reviewer will update
metadata and run the generator from an installed skill or repository checkout.

Document Python 3.10+ as the runtime for the bundled generator. Give a
shell-neutral discovery sequence:

1. run `python3 --version` where that command is conventional;
2. if unavailable, run `python --version`;
3. accept only Python 3.10 or newer;
4. invoke the helper using a path resolved from the currently loaded skill,
   never a guessed global path.

If no compatible interpreter or helper path exists, preserve the plan files
and report that index generation is pending. Do not make implementation success
depend on the index projection.

**Verify**: the plan template no longer instructs a zero-context executor to
run an unresolved `<path-to-skill>` command as a required completion gate.

### Step 4: Correct the historical example

Resolve the full 40-character commit corresponding to the documented
`1994caba0` prefix from the authoritative `shadcn-ui/ui` Git history. Replace
the short value in YAML, prose, status, and drift command. If the prefix cannot
be resolved uniquely, stop; do not invent a SHA.

Add `packages/shadcn/src/registry/config.test.ts` to the drift command so it
matches all four frontmatter/scope paths. Retain the clear warning that the
sample is historical and not executable against the current upstream tree.

**Verify**: the example `base_commit` matches `^[0-9a-f]{40}$`, every occurrence
uses that same value, and all four scope paths appear in the drift command.

### Step 5: Align user-facing documentation

Replace README variable notation with phrases such as “the recorded literal
execution-base SHA through executor `HEAD`.” Explain that every command is a
separate invocation and that the reviewer, not a manual executor, normally
regenerates the plan index.

Also make the `--issues` duplicate-search example quoting-portable: replace the
nested-escaped `--search` string in `closing-the-loop.md` with a form that
needs no shell-specific escaping — for example two separate invocations, one
searching the plan id and one the exact title, each passing a single unquoted
or simply quoted term, with the agent merging the results. State that each
command is its own process invocation.

**Verify**: `python scripts/check.py`, `python scripts/check_tests.py`, and
`git diff --check` all exit 0, and the `--issues` example contains no nested
escaped quotes.

## Test plan

- Model a Windows PowerShell host, a POSIX shell host, and a host whose Git
  operations are structured tool calls. Each must be able to follow the same
  ordered sequence without translating variable syntax.
- Check all normative Markdown for command substitution and named shell-state
  variables. Avoid rejecting dollar signs that occur only in quoted external
  documentation or explanatory anti-examples.
- Verify the example's full SHA against the upstream Git object before editing.
- Use `scripts/check_tests.py` as the structural regression suite; behavioral
  cross-host cases are added by IMP-013.

## Done criteria

- [ ] No normative workflow relies on POSIX command substitution or persistent
      shell/environment variables.
- [ ] Branch merge-base discovery and diffing are separate operations with a
      validated literal SHA.
- [ ] Every execution review command uses the recorded full literal base SHA.
- [ ] A manual executor can complete a plan without an installed skill helper.
- [ ] Python 3.10+ and helper-path discovery are documented, with a nonfatal
      pending-index fallback.
- [ ] The example uses one verified 40-character base SHA everywhere.
- [ ] The example drift check contains every in-scope path.
- [ ] The `--issues` duplicate-search guidance works identically under
      PowerShell and POSIX shells.
- [ ] `python scripts/check.py` exits 0.
- [ ] `python scripts/check_tests.py` exits 0.
- [ ] No files outside the five in-scope paths are modified.
- [ ] The executor report contains STATUS, HEAD SHA, FILES CHANGED,
      VERIFICATION RESULTS, and NOTES; the reviewer owns lifecycle metadata and
      index regeneration.

## STOP conditions

Stop and report if:

- The historical short SHA cannot be resolved uniquely from the authoritative
  upstream repository.
- A proposed command requires a particular shell to preserve state.
- IMP-003 or IMP-004 terminology is missing, making the new instructions
  conflict with unresolved earlier policy.
- Runtime portability appears to require a second generator implementation;
  that is a separate design decision.
- More than the five in-scope files are required.

## Maintenance notes

- Review future documentation for hidden command state whenever commands are
  copied from interactive shell examples.
- Full SHAs are deliberately verbose: they are provenance, not presentation.
- Keep index generation deterministic but non-blocking for manual handoffs;
  implementation evidence lives in plan metadata and Git, not only the index.
