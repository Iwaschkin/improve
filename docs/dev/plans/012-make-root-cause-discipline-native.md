---
id: IMP-012
title: Make root-cause discipline native to Improve
status: TODO
priority: P1
effort: M
risk: MED
category: dx
base_commit: 4adde10c1d1d6308c485b87efbbefb6a6a241785
working_tree_clean: false
created_at: 2026-07-19
updated_at: 2026-07-19
scope:
  - skills/improve/SKILL.md
  - skills/improve/references/root-cause-discipline.md
  - skills/improve/references/audit-playbook.md
  - skills/improve/references/plan-template.md
  - skills/improve/references/closing-the-loop.md
dependencies:
  - IMP-005
  - IMP-009
execution_branch: null
execution_base: null
reviewed_commit: null
merged_commit: null
sensitive: false
issue: null
---

## Plan 012: Make root-cause discipline native to Improve

> **Executor instructions**: Make root-cause reasoning an intrinsic Improve
> behavior. The finished `skills/improve/` package must neither invoke, detect,
> import, link to, nor require any other skill. Do not modify this plan or the
> generated plan index. Run permitted checks and report STATUS, HEAD SHA, FILES
> CHANGED, VERIFICATION RESULTS, and NOTES; the reviewer owns lifecycle metadata
> and index regeneration.
>
> **Drift check (run first)**: run
> `git diff --stat 4adde10c1d1d6308c485b87efbbefb6a6a241785..HEAD -- skills/improve/SKILL.md skills/improve/references/root-cause-discipline.md skills/improve/references/audit-playbook.md skills/improve/references/plan-template.md skills/improve/references/closing-the-loop.md`.
> `skills/improve/references/root-cause-discipline.md` does not exist at the
> planned base and is expected to be created. Stop unless IMP-005 (portable
> handoffs) and IMP-009 (reviewer-owned lifecycle and the five-field executor
> report) are VERIFIED, then reconcile this plan with the final workflow
> wording, plan template, and report contract before editing.

## Status

- **Status**: TODO
- **Priority**: P1
- **Effort**: M
- **Risk**: MED
- **Depends on**: IMP-005, IMP-009
- **Category**: dx
- **Planned at**: commit `4adde10c1d1d6308c485b87efbbefb6a6a241785`, 2026-07-19
- **Working tree clean**: false — at planning time the plan backlog and an
  untracked reference folder (`skills/no-quick-fixes/`, see Current state) were
  present; no tracked source file was modified. Refresh from a clean committed
  baseline before automatic execution.
- **Issue**: none

## Why this matters

Improve hands corrective work to a weaker executor, but its current finding,
plan, and review contracts do not require a causal chain or gate symptom-level
workarounds. An executor can therefore make a diagnostic or test disappear by
adding a suppression, retry, weakened type, special case, compatibility shim,
or diluted assertion while still satisfying superficial commands. Improve's
existing evidence, scope, and STOP rules are strong foundations, but they do
not make cause removal an approval condition.

Root-cause discipline should travel inside Improve itself so the same behavior
works from the canonical package in Codex, GitHub Copilot, Claude Code, Cursor,
and other Agent Skills hosts. The advisor must diagnose or label uncertainty,
generated plans must carry the relevant constraint without hidden context,
executors must stop rather than hide a larger problem, and reviewers must reject
symptom silencers even when tests pass.

## Current state

- `skills/improve/SKILL.md:70` requires evidence, impact, effort, fix risk, and
  confidence for every finding, but not an observed symptom, causal status,
  causal chain, correct fix layer, or rejected workaround.
- `skills/improve/references/audit-playbook.md:133` asks only for a short “Fix
  sketch.” It does not distinguish a confirmed cause from a hypothesis, so an
  advisor can overstate a plausible mechanism as fact or recommend a surface
  patch without explaining why it is the correct layer.
- `skills/improve/references/plan-template.md:7-9` requires self-contained
  context, verification, hard boundaries, and escape hatches. It has no native
  root-cause section, workaround gate, cause-removal criterion, or
  compatibility-evidence decision.
- The template's optional “Suggested executor toolkit” at line 108 cannot carry
  a load-bearing policy: availability differs by host and the executor may not
  have another skill installed.
- `skills/improve/references/plan-template.md:183` uses a generic “verification
  fails twice” STOP rule. Repeating a speculative fix is not a substitute for
  revisiting a disproven causal assumption.
- `skills/improve/references/closing-the-loop.md:82-84` tells the reviewer to
  judge whether the diff solves the problem and to inspect tests, but it does
  not explicitly inspect causal evidence, symptom silencers, unjustified
  compatibility, or cleanup made possible by the fix.
- `skills/improve/references/closing-the-loop.md:90` permits a minimally adapted
  documented deviation on merit. It does not say that an adaptation which
  suppresses a symptom, contradicts the planned cause, or introduces an
  unearned workaround must be rejected or re-planned.
- `skills/improve/references/root-cause-discipline.md` does not exist. The
  Improve package currently has no internally owned equivalent.
- Provenance note: at planning time an untracked, never-to-be-committed
  reference folder `skills/no-quick-fixes/` existed in the working tree and
  informed the behavioral requirements below. It is transient and may already
  be deleted when this plan executes. This plan is fully self-contained: every
  requirement the implementation needs is stated in the Steps below, and the
  implementation must not read, require, reference, or preserve that folder.
- IMP-013 owns behavioral conformance cases. This plan changes the contracts;
  IMP-013 verifies them per host surface afterward.

The causal failure this plan addresses is:

> corrective finding with symptom-level evidence → self-contained plan without
> an explicit causal contract → weaker executor optimizes for passing commands
> → symptom is suppressed while its cause remains → review can accept a green
> but debt-adding change.

## Commands you will need

| Purpose | Command | Provenance | Execution class | Expected on success |
| --- | --- | --- | --- | --- |
| Structural checker | `python scripts/check.py` | current CI; not run by advisor | EXECUTES_REPOSITORY_CODE | exit 0; internal reference resolves and portable package remains valid |
| Checker fixtures | `python scripts/check_tests.py` | current CI; not run by advisor | EXECUTES_REPOSITORY_CODE | all package fixtures pass |
| Generator fixtures | `python scripts/generate_plan_index_tests.py` | IMP-002 | EXECUTES_REPOSITORY_CODE | all plan-state/index fixtures pass |
| Validate selected backlog | `python skills/improve/resources/plan_state.py --plans-dir docs/dev/plans validate` | IMP-009/IMP-010 | EXECUTES_REPOSITORY_CODE | exit 0 for the literal selected directory |
| Confirm internal link | `rg -n "references/root-cause-discipline.md" skills/improve/SKILL.md` | repository search; any literal text search tool may substitute | STATIC_READ | at least one direct link with its applicability rule |
| Confirm no external coupling | `rg -n -i "no-quick-fixes" skills/improve` | repository search; any literal text search tool may substitute | STATIC_READ | exit 1 and no matches |
| Whitespace | `git diff --check` | Git standard | GIT_READ | exit 0 |

Run repository Python only under the execution authorization/profile produced
by IMP-003. The text-search and Git reads do not execute repository-controlled
code.

## Scope

One behavioral objective: make root-cause diagnosis, planning, execution, and
review a self-contained Improve contract with evidence-backed exceptions.

**In scope**:

- `skills/improve/SKILL.md`
- `skills/improve/references/root-cause-discipline.md` (create)
- `skills/improve/references/audit-playbook.md`
- `skills/improve/references/plan-template.md`
- `skills/improve/references/closing-the-loop.md`

**Out of scope**:

- Behavioral conformance cases and results; IMP-013 owns those and must add
  root-cause cases per Step 5's handoff list.
- Invoking, installing, discovering, or requiring another skill at runtime.
- Reading, modifying, deleting, committing, or preserving the transient
  `skills/no-quick-fixes/` reference folder, whether or not it still exists.
- Copying an external absolute path or sibling-skill path into Improve output.
- Deploying policy into a target repository's `AGENTS.md` or `CLAUDE.md`.
- Turning Improve's advisor into a direct source-code implementer.
- Applying a causal-chain requirement mechanically to roadmap ideas,
  content-only documentation work, or other genuinely non-corrective plans.
- Changing execution profiles, lifecycle fields, selected-directory behavior,
  non-ancestral integration, host adapters, or plan-index semantics.
- Updating README marketing claims or recording unsupported host passes.

## Git workflow

- Branch: `advisor/012-native-root-cause-discipline`.
- Commit message: `feat: make root-cause discipline native to improve`.
- Keep the internal policy and its four workflow integrations together so none
  can land with a hidden external dependency.
- If untracked reference material is present in the working tree, keep it out
  of the commit.
- Do not push, publish, or open a PR unless the operator explicitly instructs
  it.

## Steps

### Step 1: Create an Improve-owned root-cause contract

Create `skills/improve/references/root-cause-discipline.md` as a concise,
one-level bundled reference directly owned by Improve. Write it for Improve's
advisor → plan → executor → reviewer flow; do not copy deployment instructions
or refer to any other skill by name or path. Keep the essential mandate in
`SKILL.md` and the detailed method here rather than duplicating the full policy
across files.

Define applicability first:

- **Corrective** work claims that existing behavior, implementation, test,
  diagnostic, performance, security, migration, or legacy path is wrong or
  should be changed. Root-cause analysis applies.
- **Investigative** work has evidence of a symptom or risk but not a proven
  cause. It records a causal hypothesis and is not allowed to prescribe a fix
  as though the hypothesis were confirmed.
- **Non-corrective** work such as grounded product direction or content-only
  documentation may mark the discipline not applicable with one concrete
  reason. Do not invent a causal chain to fill a template.

Use the explicit causal-status values `CONFIRMED | HYPOTHESIS |
NOT-APPLICABLE`. For CONFIRMED corrective work require this evidence chain:

> input or condition → exercised code path or contract → specific flaw →
> observed symptom or concrete impact.

Adapt the required method to the roles in Improve:

1. Safely reproduce, observe, characterize, or statically prove the condition.
   Security work must not require an unsafe exploit or publish a misuse recipe;
   bounded tests and control/data-flow evidence are valid.
2. Trace and name the cause at a specific line, contract, data shape, state
   transition, or assumption.
3. Specify the correct layer rather than the surface where the symptom appears.
4. Verify that the cause is absent and surrounding behavior remains correct.
5. Remove obsolete branches, scaffolding, duplicate paths, and compatibility
   code made unnecessary by the fix.

Define symptom silencers that require scrutiny: diagnostic suppression;
swallowed errors/default-on-failure; weakened types or contracts; sleep,
timeout, retry, or ordering changes that mask timing faults; one-input special
cases; hardcoding; weakened/skipped/mocked-away tests; guardrail bypasses;
copy-pasted parallel paths; in-scope TODO deferral; and speculative
backward-compatibility shims.

Define one exception gate. A workaround is acceptable only when the record
states all of:

1. the confirmed root cause;
2. why the correct fix is genuinely unavailable within the controlled system,
   with upstream/platform evidence where applicable;
3. the correct fix and an objective removal condition;
4. why the workaround is the narrowest possible and how it is tested.

Define scope and compatibility conservatively. When the correct fix exceeds a
plan, split it during planning or stop during execution; never use scope as a
reason to hide the symptom. Remove obsolete contracts only after checking for
real current consumers. Treat public APIs, persisted data, configuration
formats, network protocols, and documented extension points as
compatibility-sensitive even when a local call search is empty. If consumer
requirements remain material and unknown, stop for user direction rather than
adding or deleting a shim speculatively.

End with separate compact self-checks for the advisor, executor, and reviewer.
Keep the reference host-, language-, and tool-neutral.

**Verify**: the file is linked directly from `SKILL.md`, contains all three
causal statuses and the four-part exception gate, and contains no external
skill name/path, host-specific invocation, or repository-policy deployment
instruction.

### Step 2: Require causal evidence during audit and vetting

Add a concise hard rule to `skills/improve/SKILL.md`: for corrective findings,
identify the cause or label it a hypothesis; never recommend or approve a
symptom silencer without the complete exception gate. Tell the advisor exactly
when to read the bundled reference. Do not broaden the skill description so
Improve starts triggering as a direct debugging/implementation skill.

Update Phase 2 and `audit-playbook.md` so each corrective finding includes:

- **Causal status**: CONFIRMED or HYPOTHESIS;
- **Observed condition**: safe reproduction, static evidence, diagnostic, or
  concrete symptom;
- **Causal chain**: the four links, with evidence at each non-obvious link;
- **Correct fix layer**: the contract/module/state boundary that owns the flaw;
- **Rejected shortcuts**: the likely symptom-level responses that would leave
  the cause present;
- the existing impact, effort, risk, confidence, and evidence fields.

Allow `NOT-APPLICABLE` only for a genuinely non-corrective finding and require
one sentence explaining why. A LOW-confidence or otherwise unproven cause must
produce an investigation/characterization plan, not a fix plan. A missing-test
finding may identify an unverified risk rather than fabricate a product bug;
its root-cause objective is the missing verification boundary itself.

Inline the compact causal-status/finding contract in delegated audit prompts,
just as secret-handling and instruction-precedence rules are inlined. Workers
may not inherit the skill or be able to resolve its filesystem path. They return
evidence and causal status only; they never implement a fix.

In Phase 3, require the advisor to open the cited path and verify each link in a
CONFIRMED causal chain. Downgrade unsupported chains to HYPOTHESIS, reject
symptom-only fix sketches, and preserve recorded by-design decisions. Do not
confuse “the code is near the symptom” with proof that it owns the cause.

**Verify**: the finding example and subagent contract distinguish CONFIRMED,
HYPOTHESIS, and NOT-APPLICABLE; a cold reader cannot present an investigative
hypothesis as an implementation-ready fix.

### Step 3: Make generated plans carry the discipline themselves

Extend `plan-template.md` with a required `## Root cause and correct fix`
section. Every generated plan must fill it without referring to this session,
another plan, another skill, or an unavailable reference. For corrective plans
include:

- applicability and causal status;
- safely observed condition/symptom;
- the complete causal chain and supporting `file:line` evidence;
- the correct fix layer and why the symptom surface is not sufficient;
- prohibited/rejected shortcuts specific to this finding;
- known compatibility consumers and how they were established;
- the exception-gate record, normally `none`.

For HYPOTHESIS, the plan objective must be investigation/characterization with
a decision gate before implementation. For NOT-APPLICABLE, give the
finding-specific reason and omit corrective boilerplate.

Add a compact root-cause mandate to the executor instructions generated into
every corrective plan: observe before changing; fix the source; verify cause
removal; clean up obsolete paths; stop if the planned chain is disproved or the
right fix exceeds scope. List the classes of symptom silencer concisely enough
to be actionable without copying the whole internal reference.

Make steps and tests prove causality:

1. characterize the failing/unsafe condition before the implementation change,
   or record why static proof is safer;
2. change the owning contract/layer;
3. remove now-obsolete code and unneeded compatibility paths;
4. rerun the regression plus surrounding behavior and show why it passes
   because the cause is absent.

Replace the generic “verification fails twice” wording with a diagnosis gate:
unexpected failure requires re-observation; if it contradicts the plan's causal
chain, stop and report rather than iterating speculative patches. Add specific
STOP conditions for an unconfirmed cause, required out-of-scope owner,
unearned workaround, unknown compatibility consumer, unsafe reproduction, and
need to weaken a test or guardrail.

Done criteria must require cause-removal evidence, no unearned symptom
silencers, complete cleanup, and an evidence-backed compatibility decision.
Preserve IMP-009's reviewer-owned lifecycle/report contract and IMP-010's
selected-directory placeholders.

**Verify**: a generated corrective plan is fully actionable when copied alone
into a clean executor context and contains no instruction to load another
skill.

### Step 4: Enforce the contract in dispatch and review

Update `closing-the-loop.md` so the executor preamble inlines the compact native
mandate. Do not tell an executor to invoke a named skill or resolve an Improve
reference path. Preserve the five top-level report fields established by
IMP-009, but require these details inside VERIFICATION RESULTS or NOTES:

- observed condition and root-cause result;
- cause-removal and surrounding-behavior evidence;
- workaround/exception record (`none` in the normal case);
- compatibility decision and current-consumer evidence;
- obsolete code/scaffolding removed, or why none existed.

If execution reveals a different cause, a blocked correct layer, or materially
larger scope, require STATUS STOPPED with evidence. The executor must not use a
suppression or compatibility shim to preserve COMPLETE status.

Add a reviewer self-check before APPROVE:

1. Reconstruct the causal chain from original condition to symptom and compare
   it with the actual diff.
2. Inspect every hunk and new test for diagnostic suppression, swallowed
   errors, weakened types/contracts, sleeps/retries/timeouts, special cases,
   hardcoding, weakened/skipped tests, guardrail bypasses, duplicated paths,
   in-scope TODOs, speculative shims, and dead code.
3. For any apparent workaround, require every exception-gate item in the change
   and tests; absence means REVISE or BLOCK.
4. Verify the regression demonstrates cause removal rather than merely a green
   symptom and that surrounding behavior still passes.
5. Verify old paths were removed unless a named current consumer or contractual
   surface requires them.

Clarify the documented-deviation rule: a deviation is acceptable only if it
preserves the verified causal objective, stays in scope, and passes the
workaround/compatibility gates. A minimally explained symptom silencer is not a
meritorious adaptation. During reconcile, use BLOCKED evidence to correct the
causal model and re-plan; do not rewrite a plan around a quiet workaround.

**Verify**: the dispatch prompt and reviewer checklist remain host-neutral,
self-contained, and able to reject a passing diff that uses a retry, suppression,
or diluted assertion instead of removing the cause.

### Step 5: Hand the behavioral oracle to IMP-013

This plan does not create conformance artifacts. Record in the executor NOTES
that IMP-013's checklist must cover at least these behaviors so the reviewer
carries them forward:

- ambiguous evidence yields HYPOTHESIS plus an investigation plan, never an
  invented confirmed cause;
- a corrective plan carries the complete causal contract and is actionable
  cold;
- an executor confronted with an easy suppression/retry/loosened assertion
  fixes the owning flaw or stops;
- a correct fix outside plan scope produces STOPPED with the required scope,
  not an out-of-scope edit or an in-scope hack;
- a genuine third-party/platform defect passes only with the full four-part
  exception gate and a removal condition;
- review rejects a green diff whose tests pass because of a symptom silencer.

**Verify**: the NOTES section of the executor report lists these six behaviors
for the reviewer.

### Step 6: Prove the Improve package is independently complete

The canonical `skills/improve/` folder must contain every instruction and
reference needed for audit, planning, dispatch, and review when copied alone.
Its Markdown links must resolve within that package, and no Improve behavior
may depend on any other skill being installed or present in the repository.

Run both repository searches in the command table. The internal reference link
must be present; the external-coupling search must return no matches. Inspect
generated plan examples and executor prompts as well as the source package — an
external dependency hidden only in emitted output still fails this plan.

**Verify**: structural, checker-fixture, generator/plan-state, link,
independence-search, and whitespace commands all produce their expected results
with no change outside Scope.

## Test plan

- Validate the internal reference link and absence of any external skill name
  or path in `skills/improve/` and in a representative generated plan and
  executor prompt.
- Use audit fixtures for CONFIRMED, HYPOTHESIS, and NOT-APPLICABLE findings;
  ensure unsupported causal links are downgraded rather than confidently
  invented.
- Generate one corrective, one investigative, and one direction plan. Confirm
  the first carries a full causal contract, the second stops before an
  unproven implementation, and the third does not fabricate corrective
  boilerplate.
- Review executor fixtures containing each symptom silencer class, including a
  green test suite with a diluted assertion. Each must be rejected unless the
  external-workaround fixture satisfies the complete exception gate.
- Exercise both compatibility branches: a demonstrated public/persisted
  consumer is preserved; a proven-dead internal path is removed fully without
  a speculative shim.
- Exercise the correct-fix-outside-scope case and assert STOPPED plus a refined
  plan recommendation, with neither an out-of-scope edit nor an in-scope hack.
- Run `python scripts/check.py`, `python scripts/check_tests.py`,
  `python scripts/generate_plan_index_tests.py`, the plan-state validator, both
  text searches, and `git diff --check`.

## Done criteria

- [ ] Improve owns a concise bundled `references/root-cause-discipline.md` with
      no external skill dependency or deployment flow.
- [ ] SKILL.md defines when the discipline applies and points directly to the
      internal reference without broadening Improve into an implementer skill.
- [ ] Corrective findings record causal status, observed condition, complete
      chain or hypothesis, correct layer, and rejected shortcuts.
- [ ] Investigative and non-corrective findings cannot masquerade as confirmed
      root-cause fixes.
- [ ] Generated corrective plans are standalone and contain cause-level steps,
      tests, done criteria, compatibility evidence, and STOP conditions.
- [ ] Executors stop when the causal model is disproved or the correct fix is
      out of scope instead of adding a symptom silencer.
- [ ] Review explicitly rejects unearned suppressions, swallowed failures,
      weakened types/tests, retries/sleeps, special cases, hardcoding,
      duplicated paths, TODO deferral, and compatibility shims.
- [ ] Legitimate external workarounds require the full documented exception
      gate and an objective removal condition.
- [ ] Public/persisted contracts and real consumers receive evidence-based
      compatibility treatment; dead internal paths are removed fully.
- [ ] The six behavioral-oracle items for IMP-013 are recorded in the executor
      report NOTES.
- [ ] The Improve package passes structural validation with no other skill
      folder present.
- [ ] External-coupling search returns no matches under `skills/improve/`.
- [ ] Existing structural, checker-fixture, generator/plan-state, and
      whitespace checks pass.
- [ ] No files outside the five in-scope paths are modified; specifically,
      `AGENTS.md`, `CLAUDE.md`, and any transient `skills/no-quick-fixes/`
      folder are untouched.
- [ ] The executor report contains STATUS, HEAD SHA, FILES CHANGED,
      VERIFICATION RESULTS, and NOTES; the reviewer owns lifecycle metadata and
      index regeneration.

## STOP conditions

Stop and report if:

- IMP-005 or IMP-009 is not VERIFIED, or their final workflow, plan schema,
  report format, or selected-directory behavior differs from the assumptions
  above.
- The target source baseline is still dirty. This plan was authored with
  `working_tree_clean: false`; refresh its base commit, evidence, and drift
  check from a clean committed baseline before automatic execution.
- Implementing the policy would require importing, invoking, detecting, or
  linking to another installed skill or any file outside `skills/improve/`.
- A corrective finding lacks enough evidence for a causal chain. Mark it
  HYPOTHESIS and plan investigation; do not invent certainty.
- Safe observation is impossible for a security-sensitive condition. Use
  bounded static evidence or stop; do not construct a harmful reproduction.
- Compatibility depends on an unknown real consumer whose answer would change
  the implementation. Request user direction before adding or deleting a shim.
- Proposed wording would be copied verbatim from material whose reuse or
  attribution requirements are unclear. Write an Improve-specific contract
  from the behavioral requirements in this plan or resolve provenance first.
- More than the five in-scope files are required, or implementation begins to
  change lifecycle, packaging, host-adapter, or repository-policy behavior.

## Maintenance notes

- The internal reference is Improve's canonical policy. It has no upstream to
  synchronize with; evolve it only through this repository's own review.
- The untracked `skills/no-quick-fixes/` folder was planning-time reference
  material only. Once this plan is VERIFIED it has no remaining purpose and
  the operator may delete it.
- Keep the mandate short in SKILL.md, the detailed method in one internal
  reference, and only role-specific fields/checks in the audit, plan, and
  closing-loop documents; avoid copy-pasted policy drift.
- A `quick` audit reduces breadth, not causal rigor. It may return fewer
  findings or more HYPOTHESIS results, never lower the workaround gate.
- New symptom-silencer classes require an audit rule, plan/review check, and a
  negative conformance fixture (IMP-013) in the same change.
- Treat false CONFIRMED causes and false APPROVE verdicts as higher-risk than a
  conservative HYPOTHESIS or STOPPED result.
- Revisit compatibility rules whenever Improve is used on public libraries,
  persisted schemas, protocols, configuration formats, or extension systems;
  local call graphs alone are not proof that a contract is unused.
