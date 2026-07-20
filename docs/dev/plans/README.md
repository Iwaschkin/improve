# Implementation Plans

Generated from plan frontmatter. Do not hand-edit this table; update the plan file and rerun the bundled `resources/generate_plan_index.py` helper.

## Execution Order & Status

| Plan | Title | Priority | Effort | Depends on | Status | Status note | Issue |
| ---- | ----- | -------- | ------ | ---------- | ------ | ----------- | ----- |
| IMP-001 | [Establish a repository development guide for agents](001-establish-repo-dev-guide.md) | P2 | S | - | DONE | - | - |
| IMP-002 | [Reject invalid plan metadata and test the generator](002-validate-plan-metadata.md) | P1 | M | - | DONE | - | - |
| IMP-003 | [Adopt trust-aware execution profiles](003-adopt-trust-aware-execution-profiles.md) | P1 | M | - | DONE | landed in 1.x; profile mechanism replaced by the 2.0 trust rule | - |
| IMP-004 | [Make the workflow host-neutral](004-make-workflow-host-neutral.md) | P1 | L | IMP-003 | DONE | - | - |
| IMP-005 | [Make Git and plan handoffs cross-platform](005-make-handoffs-cross-platform.md) | P1 | M | IMP-003, IMP-004 | DONE | - | - |
| IMP-006 | [Align audit commands with the execution safety policy](006-align-audit-command-safety.md) | P2 | S | IMP-003 | DONE | - | - |
| IMP-007 | [Validate the portable skill independently of host packaging](007-validate-portable-skill-package.md) | P2 | M | IMP-004 | DONE | - | - |
| IMP-008 | [Project complete lifecycle state in the plan index](008-project-complete-lifecycle-state.md) | P2 | M | IMP-002, IMP-003, IMP-004 | DONE | landed in 1.x; nine-state lifecycle collapsed to six in 2.0 | - |
| IMP-009 | [Make lifecycle state reviewer-owned and gate execution from plan files](009-make-lifecycle-state-reviewer-owned.md) | P1 | M | IMP-002, IMP-008 | DONE | - | - |
| IMP-010 | [Resolve and propagate one selected plans directory](010-propagate-selected-plans-directory.md) | P2 | M | IMP-009 | DONE | - | - |
| IMP-011 | [Reconcile squash, cherry-pick, and rebased integrations](011-reconcile-non-ancestral-integrations.md) | P2 | M | IMP-010 | DONE | landed in 1.x; evidence ladder reduced to diff comparison in 2.0 | - |
| IMP-012 | [Make root-cause discipline native to Improve](012-make-root-cause-discipline-native.md) | P1 | M | IMP-005, IMP-009 | DONE | - | - |
| IMP-013 | [Add a manual cross-host conformance checklist](013-add-portability-conformance-checklist.md) | P2 | S | IMP-007, IMP-010, IMP-012 | DONE | - | - |

Status values: TODO | EXECUTING | REVIEWED | DONE | BLOCKED | REJECTED

## Execution Records

- **IMP-001** — locator: `manual (implemented directly; no dispatched executor)`, base: `4adde10c1d1d6308c485b87efbbefb6a6a241785`, reviewed: `8e496e5d974f3ab13d6211a9597ba19f5a34713b`, merged: `8e496e5d974f3ab13d6211a9597ba19f5a34713b`, verified: `2026-07-20T00:00:00Z`
- **IMP-002** — locator: `manual (implemented directly; no dispatched executor)`, base: `4adde10c1d1d6308c485b87efbbefb6a6a241785`, reviewed: `83cc18a33637b1df03e1d8118f24ac1995e8ab75`, merged: `83cc18a33637b1df03e1d8118f24ac1995e8ab75`, verified: `2026-07-20T00:00:00Z`
- **IMP-003** — locator: `manual (implemented directly; no dispatched executor)`, base: `4adde10c1d1d6308c485b87efbbefb6a6a241785`, reviewed: `2977bba35756e4fff739a32ec826454bd24ab758`, merged: `2977bba35756e4fff739a32ec826454bd24ab758`, verified: `2026-07-20T00:00:00Z`
- **IMP-004** — locator: `manual (implemented directly; no dispatched executor)`, base: `4adde10c1d1d6308c485b87efbbefb6a6a241785`, reviewed: `90c339663afcaab767089066d6cc7dffa68e3706`, merged: `90c339663afcaab767089066d6cc7dffa68e3706`, verified: `2026-07-20T00:00:00Z`
- **IMP-005** — locator: `manual (implemented directly; no dispatched executor)`, base: `4adde10c1d1d6308c485b87efbbefb6a6a241785`, reviewed: `b252d80bc221ef9aafc2b1f17363e661e6dea539`, merged: `b252d80bc221ef9aafc2b1f17363e661e6dea539`, verified: `2026-07-20T00:00:00Z`
- **IMP-006** — locator: `manual (implemented directly; no dispatched executor)`, base: `4adde10c1d1d6308c485b87efbbefb6a6a241785`, reviewed: `ec9ad7114f1785786e149f664b7f7077568b06e2`, merged: `ec9ad7114f1785786e149f664b7f7077568b06e2`, verified: `2026-07-20T00:00:00Z`
- **IMP-007** — locator: `manual (implemented directly; no dispatched executor)`, base: `4adde10c1d1d6308c485b87efbbefb6a6a241785`, reviewed: `3a6594438865adc60a1e229a808258b73ee2dadf`, merged: `3a6594438865adc60a1e229a808258b73ee2dadf`, verified: `2026-07-20T00:00:00Z`
- **IMP-008** — locator: `manual (implemented directly; no dispatched executor)`, base: `4adde10c1d1d6308c485b87efbbefb6a6a241785`, reviewed: `2a96501f19b401e0f3804c51d7fc3e2a67e463f8`, merged: `2a96501f19b401e0f3804c51d7fc3e2a67e463f8`, verified: `2026-07-20T00:00:00Z`
- **IMP-009** — locator: `manual (implemented directly; no dispatched executor)`, base: `4adde10c1d1d6308c485b87efbbefb6a6a241785`, reviewed: `f30b3a35c64ab8648fcb6a93f8c1d19077087d66`, merged: `f30b3a35c64ab8648fcb6a93f8c1d19077087d66`, verified: `2026-07-20T00:00:00Z`
- **IMP-010** — locator: `manual (implemented directly; no dispatched executor)`, base: `4adde10c1d1d6308c485b87efbbefb6a6a241785`, reviewed: `1f4e015c00330c161bba69811622a0f0949c23a1`, merged: `1f4e015c00330c161bba69811622a0f0949c23a1`, verified: `2026-07-20T00:00:00Z`
- **IMP-011** — locator: `manual (implemented directly; no dispatched executor)`, base: `4adde10c1d1d6308c485b87efbbefb6a6a241785`, reviewed: `6a57612333037f7baa4209f12c31f87ef6460470`, merged: `6a57612333037f7baa4209f12c31f87ef6460470`, verified: `2026-07-20T00:00:00Z`
- **IMP-012** — locator: `manual (implemented directly; no dispatched executor)`, base: `4adde10c1d1d6308c485b87efbbefb6a6a241785`, reviewed: `56add7840be720c1ac35db82ae6eeaebddbb25a4`, merged: `56add7840be720c1ac35db82ae6eeaebddbb25a4`, verified: `2026-07-20T00:00:00Z`
- **IMP-013** — locator: `manual (implemented directly; no dispatched executor)`, base: `4adde10c1d1d6308c485b87efbbefb6a6a241785`, reviewed: `6aaceb04b29ecf5d30c0f6efe73e572406a34964`, merged: `6aaceb04b29ecf5d30c0f6efe73e572406a34964`, verified: `2026-07-20T00:00:00Z`

## Findings Considered and Rejected

None recorded.
