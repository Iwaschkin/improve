---
id: IMP-003
title: Adopt trust-aware execution profiles
status: TODO
priority: P1
effort: M
risk: MED
category: security
base_commit: 4adde10c1d1d6308c485b87efbbefb6a6a241785
created_at: 2026-07-19
updated_at: 2026-07-19
scope:
  - skills/improve/SKILL.md
  - skills/improve/references/closing-the-loop.md
  - skills/improve/references/plan-template.md
  - README.md
dependencies: []
execution_base: null
reviewed_commit: null
merged_commit: null
sensitive: false
issue: null
---

## Plan 003: Adopt trust-aware execution profiles

> **Executor instructions**: Follow this plan step by step. Run every
> verification command permitted by the execution environment and confirm the
> expected result before moving on. If repository-code execution is not
> permitted, skip those commands and report that they were not run. If any
> STOP condition occurs, stop and report; do not improvise. Do not modify this
> plan or the generated index. When finished, report STATUS, HEAD SHA, FILES
> CHANGED, VERIFICATION RESULTS, and NOTES; the reviewer owns lifecycle metadata
> and index regeneration.
>
> **Drift check (run first)**: run
> `git diff --stat 4adde10c1d1d6308c485b87efbbefb6a6a241785..HEAD -- skills/improve/SKILL.md skills/improve/references/closing-the-loop.md skills/improve/references/plan-template.md README.md`.
> If any in-scope file changed, compare the excerpts below with the live files.
> Stop if the policy has already been materially redesigned.

## Why this matters

The execution guidance currently treats every repository as though it may be
hostile and combines three distinct concerns: protecting Git changes,
protecting the host process, and preserving an independent reviewer. That is
safe but unnecessarily obstructive for the maintainer's primary use case:
running the skill against projects they wrote and control. A risk-based policy
should retain reviewable diffs and explicit approval for dangerous effects
while allowing ordinary tests and sequential execution under the host's normal
permission model.

## Current state

- `skills/improve/SKILL.md:24-25` makes a disposable worktree central to
  `execute` and classifies every build, test, lint, framework, package-manager,
  and install command as repository-code execution requiring a restricted
  environment or per-execution confirmation:

  ```markdown
  The `execute` variant may create and maintain an ignored workspace-local
  disposable worktree under `docs/dev/plans/.worktrees/` ...

  Treat build, test, lint, framework, package-manager, and install commands as
  repository-code execution ... run them only in a restricted execution
  environment or after explicit user confirmation.
  ```

- `skills/improve/references/closing-the-loop.md:16-18` makes a completely clean
  target tree a hard precondition and requires an execution-environment
  decision before dispatch.
- `skills/improve/references/closing-the-loop.md:22-29` mandates an ignored,
  workspace-local worktree and can require changing
  `docs/dev/plans/.gitignore` before execution. This clashes with the clean-tree
  precondition when the plan directory itself is newly created and uncommitted.
- `skills/improve/references/closing-the-loop.md:100` correctly explains that a
  worktree isolates files rather than processes, but applies that warning to
  all verification regardless of repository trust or command risk.
- `README.md:110-117` repeats the strict model as the only automatic execution
  shape.
- `skills/improve/references/plan-template.md` records command execution classes
  but does not record which trust profile authorized execution.
- The repository's documentation convention is imperative Markdown with bold
  rules, compact tables, exact commands, and explicit STOP behavior. Preserve
  that style; use the existing execution-environment table and report format in
  `closing-the-loop.md` as the structural exemplar.

## Commands you will need

| Purpose | Command | Provenance | Execution class | Expected on success |
| --- | --- | --- | --- | --- |
| Structural validation | `python scripts/check.py` | `.github/workflows/check.yml:20`; not run by advisor | EXECUTES_REPOSITORY_CODE | exit 0 and `all checks passed` |
| Checker fixtures | `python scripts/check_tests.py` | `.github/workflows/check.yml:21`; not run by advisor | EXECUTES_REPOSITORY_CODE | exit 0 and all fixtures pass |
| Inspect policy terms | `git diff --check` | Git standard; not run by advisor | GIT_READ | exit 0 with no whitespace errors |

The CI workflow uses Python 3.12. The advisor did not run repository scripts
because the available restricted sandbox could not start and unsandboxed
repository-code execution was not authorized.

## Scope

One behavioral objective: replace the universal strict execution policy with
explicit trust profiles while retaining non-negotiable safety boundaries.

**In scope** (the only files to modify):

- `skills/improve/SKILL.md` — top-level rules and `execute` summary.
- `skills/improve/references/closing-the-loop.md` — detailed preconditions,
  dispatch, review, and cleanup policy.
- `skills/improve/references/plan-template.md` — plan metadata/report guidance
  for the selected profile.
- `README.md` — user-facing explanation and examples.

**Out of scope**:

- Host-specific subagent names, invocation syntax, and adapters; IMP-004 handles
  those after this policy is settled.
- Shell portability and literal-SHA command recipes; IMP-005 handles those.
- Any change allowing automatic merge, push, deployment, destructive cleanup,
  production access, or secret disclosure.
- Source implementation outside documentation and skill instructions.

## Git workflow

- Branch: `advisor/003-trust-aware-execution-profiles`
- Use one logical commit after all documentation agrees.
- Commit message style: `docs: define trust-aware execution profiles`, matching
  recent `docs:` commits such as `docs: limit executable plan scope`.
- Do not push or open a PR unless the operator instructs it.

## Steps

### Step 1: Define three execution profiles

Add one authoritative section near the start of `closing-the-loop.md` defining:

1. **Trusted local** — for repositories the user owns or explicitly trusts.
   Use the host's normal approval policy. Prefer a worktree for rollback,
   parallelism, or reviewer separation, but do not require one for a single
   sequential executor. Ordinary build, test, typecheck, and lint commands may
   run when the host policy permits them.
2. **Strict** — for external, unfamiliar, security-sensitive, or explicitly
   untrusted work. Require an enforceable sandbox/container/VM boundary before
   running repository-controlled code. Worktree isolation remains separate and
   is still recommended for change isolation.
3. **Manual** — produce or hand over the plan without automatic execution when
   the required host capabilities or approvals are absent.

State that trust is never inferred solely from being inside the current
workspace. Use an explicit user statement, an invocation modifier, or a
documented default configured for this personal fork. If no signal exists,
default to strict for external repositories and trusted-local only when the
user has identified the project as their own.

Define invariant boundaries shared by all profiles: no secret reproduction;
no automatic push, merge, deployment, release, destructive Git/filesystem
operation, database migration, production/service access, or cross-provider
data transfer without explicit authorization.

**Verify**: `python scripts/check.py` -> exit 0.

### Step 2: Separate Git isolation from process isolation

Rewrite the dispatch preconditions and worktree section so they use precise
terms:

- **Change isolation** means a worktree, branch, or recorded clean diff boundary.
- **Process isolation** means OS/container/VM restrictions on filesystem,
  network, credentials, services, and subprocesses.
- **Reviewer separation** means the advisor does not author the executor's
  implementation.

Make a host-managed or manually created worktree the preferred path, not a hard
requirement in trusted-local sequential execution. State explicitly that the
worktree remains the recommended default in every profile — it is what keeps
the advisor/executor boundary reviewable as a diff rather than merely asserted
— and that trusted-local only removes it as a hard blocker for a single
sequential executor. Do not require `docs/dev/plans/.gitignore` to be changed
before dispatch. If the host chooses its own safe worktree location, accept it
and record the locator.

Replace the hard clean-tree stop with explicit choices:

- execute committed `HEAD` and state that uncommitted changes are excluded;
- ask the user to commit the relevant baseline;
- use an already isolated checkout whose base can be recorded; or
- fall back to manual handoff.

Never stash, discard, or commit user changes automatically. A plan written from
dirty state remains non-automatic until its relevant baseline is committed or
the user explicitly selects committed `HEAD` knowing local changes are absent
from execution.

**Verify**: inspect the resulting policy and confirm that the words `worktree`
and `sandbox` are each defined independently and that a dirty main checkout no
longer causes an unconditional stop.

### Step 3: Classify high-risk commands independently of repository ownership

Retain mandatory strict handling for:

- unfamiliar dependency installation and package lifecycle scripts;
- database/schema migrations;
- deployment, release, infrastructure, or production commands;
- commands using credentials, external services, or broad network access;
- destructive filesystem/Git operations or elevated privileges;
- code copied from or controlled by an untrusted source.

For trusted-local mode, ordinary tests/builds remain subject to the host's
existing permission and sandbox policy rather than an additional confirmation
invented by this skill. Record the selected profile and actual enforcement in
the executor report; never describe a prompt-only restriction as a sandbox.

**Verify**: the execution report format distinguishes selected trust profile,
actual process boundary, and verification result.

### Step 4: Align the plan template and README

Update `plan-template.md` so plans record the selected execution profile in the
human-readable status and command guidance. Do not add lifecycle frontmatter
fields in this plan; IMP-008 owns schema expansion. A prose placeholder is
enough until that dependency lands.

Update the README compatibility, workflow, closing-loop, and hard-rules text to
explain that worktrees are preferred change isolation and restricted sandboxes
are conditional process isolation. Show trusted-local as the intended personal
project path without suggesting that ownership makes installs, migrations, or
deployments harmless.

**Verify**: `python scripts/check.py` and `python scripts/check_tests.py` -> both
exit 0.

## Test plan

- Use existing `scripts/check_tests.py` as the structural pattern: it constructs
  temporary repositories, runs the checker, and compares exit status.
- No new automated fixture file is required in this documentation-only plan.
- Manually walk through these policy scenarios and confirm the outcome is
  unambiguous:
  - owned repository, one executor, ordinary unit tests -> trusted-local may run
    under host policy without a worktree;
  - owned repository, two parallel executors -> prefer separate worktrees;
  - dirty tree -> offer committed-HEAD/manual choices, never stash automatically;
  - external repository with install scripts -> strict sandbox or no execution;
  - owned repository with production migration -> explicit authorization still
    required;
  - no writable executor -> manual handoff.
- Behavioral verification per host surface is deferred to IMP-013's
  conformance checklist.

## Done criteria

- [ ] The skill defines trusted-local, strict, and manual execution profiles in
      one authoritative location.
- [ ] Worktree/change isolation is not described as process sandboxing.
- [ ] Trusted-local sequential execution can proceed without a mandatory
      worktree when the user and host policy permit it.
- [ ] A dirty main tree produces explicit safe choices rather than an
      unconditional stop or automatic stash/commit.
- [ ] High-risk external effects still require explicit authorization or strict
      isolation regardless of repository ownership.
- [ ] `README.md`, `SKILL.md`, `closing-the-loop.md`, and `plan-template.md` do
      not contradict one another.
- [ ] `python scripts/check.py` exits 0.
- [ ] `python scripts/check_tests.py` exits 0.
- [ ] No files outside the four in-scope paths are modified.
- [ ] The executor report contains STATUS, HEAD SHA, FILES CHANGED,
      VERIFICATION RESULTS, and NOTES; the reviewer owns lifecycle metadata and
      index regeneration.

## STOP conditions

Stop and report if:

- The maintainer wants automatic deployment, migration, push, merge, or
  destructive cleanup included in trusted-local mode; that is a separate
  authority decision and must not be inferred here.
- A supported host cannot expose whether command execution is sandboxed or
  approval-gated; describe it as unknown and retain manual fallback rather than
  claiming enforcement.
- The change requires redesigning host-specific dispatch APIs before the trust
  policy can be stated; leave those details for IMP-004.
- More than the four in-scope files are needed.

## Maintenance notes

- Treat the profile definitions as policy, not marketing. Future host adapters
  must map real controls to them and report gaps honestly.
- Reviewers should look for accidental weakening of the invariant boundaries
  when simplifying trusted-local flow.
- If this fork is later distributed primarily for third-party audits, revisit
  the default profile but keep the same three-level model.
