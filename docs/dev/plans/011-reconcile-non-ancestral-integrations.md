---
id: IMP-011
title: Reconcile squash, cherry-pick, and rebased integrations
status: TODO
priority: P2
effort: M
risk: MED
category: bug
base_commit: 4adde10c1d1d6308c485b87efbbefb6a6a241785
created_at: 2026-07-19
updated_at: 2026-07-19
scope:
  - skills/improve/references/closing-the-loop.md
  - skills/improve/references/plan-template.md
  - skills/improve/SKILL.md
  - skills/improve/resources/plan_state.py
  - skills/improve/resources/generate_plan_index.py
  - scripts/generate_plan_index_tests.py
dependencies:
  - IMP-010
execution_base: null
reviewed_commit: null
merged_commit: null
sensitive: false
issue: null
---

## Plan 011: Reconcile squash, cherry-pick, and rebased integrations

> **Executor instructions**: Extend reconciliation conservatively. Commit
> messages and titles are hints, never proof of integration. Do not modify this
> plan or its generated index. Report STATUS, HEAD SHA, FILES CHANGED,
> VERIFICATION RESULTS, and NOTES; the reviewer owns lifecycle metadata and
> index regeneration.
>
> **Drift check (run first)**: run
> `git diff --stat 4adde10c1d1d6308c485b87efbbefb6a6a241785..HEAD -- skills/improve/references/closing-the-loop.md skills/improve/references/plan-template.md skills/improve/SKILL.md skills/improve/resources/plan_state.py skills/improve/resources/generate_plan_index.py scripts/generate_plan_index_tests.py`.
> `plan_state.py` and `generate_plan_index_tests.py` do not exist at the planned
> base. Stop unless IMP-010 is VERIFIED, then preserve its selected-directory
> invariant and IMP-009's reviewer-owned transition boundary.

## Why this matters

The current reconciliation rule recognizes integration only when the exact
reviewed commit is reachable from the target branch. That works for
fast-forwards and ordinary merges, but not for common squash merges,
cherry-picks, or rebases, where equivalent reviewed changes land under new
commit IDs. Such plans can remain REVIEWED forever, their worktrees and branches
cannot be cleaned safely, and later planning may duplicate work already in the
target branch.

Reconciliation needs evidence-based non-ancestral matching while remaining
conservative. It must record the actual target-branch commit, explain how
equivalence was established, and leave ambiguous cases REVIEWED for a human
decision rather than promoting them from a matching title or partial diff.

## Current state

- `skills/improve/references/closing-the-loop.md:115` moves REVIEWED to MERGED
  only when `reviewed_commit` is reachable from the target branch.
- `skills/improve/references/closing-the-loop.md:105` permits worktree cleanup
  and branch deletion only after the reviewed commit is reachable, so equivalent
  rewritten integrations remain stuck.
- `skills/improve/references/plan-template.md:35-36` records only
  `reviewed_commit` and `merged_commit`; it does not record the target branch,
  integration method, verification time, superseding plan, or evidence.
- The generated index projects reviewed/merged SHAs but cannot explain how a
  non-ancestral match was accepted.
- IMP-008 covers lifecycle persistence generally. It does not specify the Git
  evidence needed for rewritten commits or distinguish an actual target commit
  from the reviewed source commit.
- IMP-005 requires independently runnable cross-platform commands, so any Git
  comparison automation must use argument arrays/direct subprocess input rather
  than POSIX pipelines or command substitution.

## Commands you will need

| Purpose | Command | Provenance | Execution class | Expected on success |
| --- | --- | --- | --- | --- |
| Direct ancestry probe | `git merge-base --is-ancestor <reviewed-commit> <target-branch>` | Git standard | GIT_READ | exit 0 only for direct/merged ancestry; exit 1 is a normal non-match |
| Commit-equivalence probe | `git cherry <target-branch> <reviewed-commit> <execution-base>` | Git standard | GIT_READ | `-` rows identify patch-equivalent commits; output still requires complete-range evaluation |
| Range comparison | `git range-diff <execution-base>..<reviewed-commit> <candidate-base>..<candidate-target>` | Git standard | GIT_READ | reviewed mapping for a known candidate range |
| Plan-state fixtures | `python scripts/generate_plan_index_tests.py` | IMP-002, extended here | EXECUTES_REPOSITORY_CODE | lifecycle and temporary-Git fixtures pass |
| Validate plans | `python skills/improve/resources/plan_state.py --plans-dir docs/dev/plans validate` | IMP-009 | EXECUTES_REPOSITORY_CODE | exit 0 |
| Regenerate index | `python skills/improve/resources/generate_plan_index.py --plans-dir docs/dev/plans` | existing | EXECUTES_REPOSITORY_CODE | new lifecycle fields project correctly |
| Structural checker | `python scripts/check.py` | existing CI | EXECUTES_REPOSITORY_CODE | exit 0 |
| Whitespace | `git diff --check` | Git standard | GIT_READ | exit 0 |

Replace placeholders with previously validated literal refs and the literal
selected plans directory. Treat exit code `1` from `--is-ancestor` as evidence
to continue conservative reconciliation, not as a command failure. Run
repository tests only under the authorization/profile rules from IMP-003.

## Scope

One behavioral objective: recognize and record reviewed work integrated through
commit-rewriting workflows without accepting false positives.

**In scope**:

- `skills/improve/references/closing-the-loop.md`
- `skills/improve/references/plan-template.md`
- `skills/improve/SKILL.md`
- `skills/improve/resources/plan_state.py`
- `skills/improve/resources/generate_plan_index.py`
- `scripts/generate_plan_index_tests.py`

**Out of scope**:

- Automatically merging, rebasing, cherry-picking, reverting, or rewriting Git
  history.
- Deleting a worktree or branch before integration and verification evidence is
  recorded.
- Trusting commit messages, branch names, PR titles, issue links, or timestamps
  as proof of content equivalence.
- Querying a remote provider without operator authorization and an available
  host-neutral adapter.
- General duplicate-code detection beyond the recorded execution range and
  plan scope.

## Git workflow

- Branch: `advisor/011-non-ancestral-reconciliation`.
- Commit message: `fix: reconcile rewritten integrations`.
- Keep schema, validation, index projection, reconciliation algorithm, and Git
  fixtures together so no new field is accepted without evidence semantics.
- Use generated temporary repositories for tests; never rewrite the user's real
  history to demonstrate a case.

## Steps

### Step 1: Record integration and verification evidence explicitly

Extend plan frontmatter and its template with:

- `target_branch: null | <full-ref-or-documented-branch-name>`;
- `integration_method: null | direct | merge | cherry-pick | squash | rebase | tree-equivalent`;
- `integration_evidence: []` as a flat list of concise evidence records;
- `verified_at: null | <ISO-8601 UTC timestamp>`;
- `superseded_by: null | IMP-NNN`.

Retain `merged_commit` for compatibility, but redefine it precisely as the
actual target-branch commit at which the complete reviewed change is known to
be integrated. For a rewritten multi-commit range, use the final target commit
that completes the range and list the mapped range/commits in
`integration_evidence`. Never copy `reviewed_commit` into `merged_commit` when
that object is not reachable from the target branch.

Add shared validation invariants:

- REVIEWED requires full `execution_base` and `reviewed_commit` SHAs;
- MERGED requires REVIEWED fields plus `target_branch`, a non-null integration
  method, full `merged_commit`, and nonempty evidence;
- `merged_commit` must resolve and be reachable from `target_branch` during live
  reconciliation, even when `reviewed_commit` is not;
- VERIFIED requires all MERGED fields plus `verified_at`;
- SUPERSEDED requires a valid, non-self `superseded_by` plan ID;
- fields forbidden by earlier states remain null/empty rather than carrying
  stale assertions.

Update the generated index to include target branch, integration method,
actual target commit, verification time, and superseding plan. Keep detailed
evidence in the plan file to avoid an unreadably wide index.

**Verify**: valid state fixtures render deterministically and each missing,
malformed, contradictory, or self-referential field fails before index output
is replaced.

### Step 2: Specify an evidence ladder for reconciliation

In `closing-the-loop.md`, reconcile a REVIEWED plan against its recorded target
branch in this order:

1. Confirm every recorded SHA/ref resolves locally and refresh the target ref
   only when remote access is authorized. Record the exact target tip inspected.
2. Run the direct ancestry probe. If the reviewed commit is reachable, classify
   a fast-forward/direct inclusion or a merge, identify the actual target
   commit, and retain the ancestry evidence.
3. If ancestry fails, compare the complete execution range
   `execution_base..reviewed_commit` with a known target candidate range. Use
   `git cherry` for one-to-one patch equivalence and `git range-diff` for a
   provided rebase/cherry-pick range; require every reviewed commit to map and
   investigate extra target commits.
4. For a known squash candidate, compare the aggregate reviewed diff and final
   scoped tree state with the candidate commit's full parent diff and resulting
   tree. Inspect extra files and changes, not only the plan scope.
5. Use `tree-equivalent` only after a reviewer has inspected the complete
   relevant diffs and explicitly confirms equivalence that Git patch identity
   cannot prove.
6. If the candidate range is unknown, only partially equivalent, contains
   unexplained extra changes, or has multiple plausible matches, leave the plan
   REVIEWED and report exactly what evidence/user input is missing.

Provider/PR metadata may supply a target branch, merge strategy, and candidate
commit/range, but is locator evidence only. Content comparison is still
required. Commit messages and titles may help locate candidates but can never
advance status.

Where Python automation feeds output from one Git process into another (for
example stable patch IDs), use `subprocess.run` with argument arrays and byte
input, `shell=False`, bounded captured output, and explicit return-code
handling. Do not introduce shell pipelines, substitutions, or host-specific
quoting.

**Verify**: the documented decision table gives an unambiguous status/method
for direct, merge, cherry-pick, squash, rebase, partial, extra-change, and
ambiguous cases.

### Step 3: Separate integration from target-branch verification

After equivalence is established, the reviewer records MERGED with the actual
target commit, method, target branch, and concise evidence, then regenerates
the selected index. MERGED alone does not claim that acceptance criteria pass.

Run the plan's permitted acceptance checks against a worktree/ref exactly at
the recorded target commit. Only after independently confirming all done
criteria should the reviewer set VERIFIED and `verified_at`, regenerate the
index, and consider cleanup. If tests cannot be run under the current profile,
leave MERGED and report the manual verification command instead of treating
content equivalence as test success.

If target history later removes the recorded commit, reconcile must flag the
record for investigation; it must not silently select a new same-message
commit. If the change is reverted, record a focused follow-up plan or lifecycle
note according to IMP-008 rather than preserving a misleading current-support
claim.

**Verify**: a squash fixture advances REVIEWED -> MERGED after content review,
remains MERGED when acceptance checks are unavailable/fail, and reaches
VERIFIED only with a timestamp after checks pass at the recorded target commit.

### Step 4: Make cleanup depend on recorded integration evidence

Update cleanup rules so direct reachability of `reviewed_commit` is one valid
case, not the only case. An executor worktree/branch becomes cleanup-eligible
only after:

- status is VERIFIED;
- `merged_commit` resolves and is reachable from the recorded target branch;
- integration method/evidence is internally valid;
- required acceptance checks were run at that target commit;
- the reviewer has confirmed no unique uncommitted executor changes remain.

Retain the existing ask-before-delete behavior for orphans and unexpected
worktrees. Deleting a branch is never part of equivalence detection. A stale or
ambiguous REVIEWED plan remains intact even when a likely same-title target
commit exists.

**Verify**: rewritten-integration fixtures are cleanup-eligible only after
VERIFIED, while false-positive and incomplete-evidence fixtures retain their
worktree/branch recommendation.

### Step 5: Add temporary-Git regression coverage

Extend `scripts/generate_plan_index_tests.py` with standard-library fixtures
that initialize isolated repositories and create:

- fast-forward/direct integration;
- a true merge commit;
- one and multiple cherry-picked commits;
- a single squash commit;
- a rebased multi-commit range;
- same commit message with different content;
- partial cherry-pick/squash missing one reviewed change;
- candidate commit with the reviewed changes plus unexplained extra files;
- multiple equivalent/ambiguous candidate ranges;
- rewritten integration whose executor branch has already been deleted;
- recorded target commit not reachable from the stated target branch.

Assert classification, actual target SHA, evidence, allowed transition, index
projection, and cleanup eligibility. Normalize Git identity/config inside each
temporary repository; do not depend on the developer's global Git config,
default branch name, remote network, shell, or current repository history.

**Verify**: fixtures pass on Windows and POSIX, and deliberately misleading
messages/titles never produce MERGED or VERIFIED.

## Test plan

- Build temporary direct, merge, cherry-pick, squash, and rebase histories and
  assert complete-range classification plus the exact reachable target SHA.
- Test negative histories with same messages, partial changes, extra changes,
  ambiguous candidates, and unreachable recorded commits; all must remain
  REVIEWED or fail validation with actionable evidence.
- Validate lifecycle cross-fields for every status, including VERIFIED without
  `verified_at` and SUPERSEDED without `superseded_by`.
- Confirm generation is atomic and projects method/target/verification fields
  while retaining detailed evidence in the plan.
- Simulate acceptance checks unavailable and failing after successful
  equivalence; status must stop at MERGED.
- Exercise cleanup decisions for ancestral and rewritten integrations.
- Run structural, checker, and generator/plan-state tests plus
  `git diff --check`.

## Done criteria

- [ ] Plan schema records target branch, integration method/evidence, actual
      target commit, verification timestamp, and superseding plan.
- [ ] Shared validation enforces status-dependent cross-field invariants and
      preserves the previous index on invalid data.
- [ ] Direct, merge, cherry-pick, squash, rebase, and reviewer-confirmed tree
      equivalence have documented evidence requirements.
- [ ] `merged_commit` always identifies a commit reachable from the recorded
      target branch, never a rewritten source SHA that is absent there.
- [ ] Messages, titles, timestamps, and provider metadata cannot independently
      advance lifecycle status.
- [ ] Partial, extra-change, unknown-range, and ambiguous matches remain
      REVIEWED with actionable diagnostics.
- [ ] VERIFIED requires acceptance checks at the recorded target commit plus
      `verified_at`.
- [ ] Cleanup works for proven rewritten integrations and remains conservative
      for incomplete evidence.
- [ ] Temporary-Git positive and false-positive regression fixtures pass on
      Windows and POSIX.
- [ ] Existing structural, checker, and generator checks pass.
- [ ] No files outside the six in-scope paths are modified.
- [ ] The executor report contains STATUS, HEAD SHA, FILES CHANGED,
      VERIFICATION RESULTS, and NOTES; the reviewer owns lifecycle metadata and
      index regeneration.

## STOP conditions

Stop and report if:

- IMP-008, IMP-009, or IMP-010 lands with incompatible lifecycle fields,
  ownership, or directory semantics; refresh this plan first.
- A candidate cannot be proven from complete Git content/range evidence without
  relying on a title, message, timestamp, or guess.
- The target ref or recorded commit cannot be resolved safely under current
  remote-access permissions.
- A candidate contains unexplained extra changes or only a subset of the
  reviewed range; leave the plan REVIEWED.
- Verification would require executing repository code without the required
  profile/authorization; leave the plan MERGED and hand over the exact checks.
- More than the six in-scope files are required; split provider-specific PR
  lookup or richer Git adapter work into a separate plan.

## Maintenance notes

- Git hosting terminology varies; lifecycle evidence should describe content
  and reachability, not assume a provider's “merged” label proves equivalence.
- Retain enough concise evidence to repeat the decision after branches are
  deleted, but avoid embedding large diffs or sensitive source in frontmatter.
- Add a negative fixture whenever a new equivalence heuristic is introduced;
  false MERGED/VERIFIED states are more damaging than a conservative REVIEWED
  state.
- Re-run reconciliation after target-history rewrites and treat missing
  recorded commits as an investigation signal.
