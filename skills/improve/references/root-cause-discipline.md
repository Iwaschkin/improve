# Root-Cause Discipline

Improve hands corrective work to a weaker executor and judges the result. A
change that makes a symptom disappear without the cause being understood and
removed is not a fix — it is deferred debt that passes green checks. This
reference makes cause removal a condition of every corrective finding, plan,
execution, and approval. It is host-, language-, and tool-neutral.

## Applicability

Decide first which kind of work this is; do not force the discipline onto
work it does not fit.

- **Corrective** — the finding claims existing behavior, implementation,
  test, diagnostic, performance, security posture, migration, or legacy path
  is wrong or must change. Root-cause analysis applies in full.
- **Investigative** — there is evidence of a symptom or risk but no proven
  cause. Record a causal *hypothesis*; it may not prescribe a fix as though
  confirmed. The resulting plan investigates and characterizes, with a
  decision gate before any implementation.
- **Non-corrective** — grounded product direction, content-only
  documentation, and similar work may mark the discipline `NOT-APPLICABLE`
  with one concrete reason. Never invent a causal chain to fill a template.

Causal status is always one of `CONFIRMED | HYPOTHESIS | NOT-APPLICABLE`.

## The causal chain

`CONFIRMED` corrective work requires this evidence chain, with support at
every non-obvious link:

> input or condition → exercised code path or contract → specific flaw →
> observed symptom or concrete impact

If the explanation contains "somehow", "for some reason", or "this makes it
pass", the cause is not confirmed — the status is HYPOTHESIS. Proximity is
not causality: code being *near* the symptom does not prove it owns the flaw.

## Required method

1. **Observe safely.** Reproduce, characterize, or statically prove the
   condition before changing anything. Security work must not require an
   unsafe exploit or publish a misuse recipe — bounded tests and
   control/data-flow evidence are valid observation.
2. **Trace and name the cause** at a specific line, contract, data shape,
   state transition, or assumption.
3. **Fix at the owning layer**, not the surface where the symptom appears —
   even when the owning layer is farther away or harder.
4. **Verify the cause is absent** and surrounding behavior remains correct;
   the symptom must be gone *because* the cause is gone.
5. **Clean up** the branches, scaffolding, duplicate paths, and compatibility
   code the fix made unnecessary.

## Symptom silencers

These require scrutiny wherever they appear in a fix sketch, a plan step, an
executor diff, or a test: diagnostic suppression; swallowed errors or
default-on-failure; weakened types or contracts; sleep, timeout, retry, or
ordering changes that mask timing faults; one-input special cases;
hardcoding; weakened, skipped, or mocked-away tests; guardrail bypasses;
copy-pasted parallel paths; in-scope TODO deferral; and speculative
backward-compatibility shims. None is acceptable as a response to a problem
that is not understood.

## The exception gate

A workaround is acceptable only when the change itself records **all four**:

1. the confirmed root cause, specifically;
2. why the correct fix is genuinely unavailable within the controlled system,
   with upstream or platform evidence where applicable;
3. the correct fix and an objective condition for removing the workaround;
4. why this workaround is the narrowest possible and how it is tested.

Anything less means the workaround is not earned — keep investigating, or
stop and report.

## Scope and compatibility

- When the correct fix exceeds the plan, split it during planning or STOP
  during execution. Scope is never a reason to hide the symptom.
- Remove obsolete contracts fully — update callers, delete the old path — but
  only after checking for real current consumers. Public APIs, persisted
  data, configuration formats, network protocols, and documented extension
  points are compatibility-sensitive even when a local call search is empty.
- If a material consumer question cannot be answered from evidence, stop for
  user direction rather than adding or deleting a shim speculatively.

## Self-checks

**Advisor** (audit and vet): every corrective finding carries a causal status;
every CONFIRMED chain has its links verified against the cited code; unproven
chains are downgraded to HYPOTHESIS; no fix sketch recommends a symptom
silencer without the full exception gate.

**Executor**: the condition was observed (or statically proven) before the
change; the diff changes the owning layer; the regression passes because the
cause is absent; obsolete paths are removed; if the planned chain was
disproved or the correct fix left scope, the result is STOPPED with evidence —
never a quiet workaround to preserve COMPLETE.

**Reviewer**: the causal chain reconstructs from condition to symptom and
matches the diff; no hunk or test contains an unearned silencer; any apparent
workaround carries the complete exception gate; tests demonstrate cause
removal rather than a green symptom; old paths are gone unless a named
current consumer requires them.
