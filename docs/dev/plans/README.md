# Implementation Plans

Generated from plan frontmatter. Do not hand-edit this table; update the plan file and rerun the bundled `resources/generate_plan_index.py` helper.

## Execution Order & Status

| Plan | Title | Priority | Effort | Depends on | Status | Status note | Issue |
| ---- | ----- | -------- | ------ | ---------- | ------ | ----------- | ----- |
| IMP-001 | [Establish a repository development guide for agents](001-establish-repo-dev-guide.md) | P2 | S | - | TODO | - | - |
| IMP-002 | [Reject invalid plan metadata and test the generator](002-validate-plan-metadata.md) | P1 | M | - | TODO | - | - |
| IMP-003 | [Adopt trust-aware execution profiles](003-adopt-trust-aware-execution-profiles.md) | P1 | M | - | TODO | - | - |
| IMP-004 | [Make the workflow host-neutral](004-make-workflow-host-neutral.md) | P1 | L | IMP-003 | TODO | - | - |
| IMP-005 | [Make Git and plan handoffs cross-platform](005-make-handoffs-cross-platform.md) | P1 | M | IMP-003, IMP-004 | TODO | - | - |
| IMP-006 | [Align audit commands with the execution safety policy](006-align-audit-command-safety.md) | P2 | S | IMP-003 | TODO | - | - |
| IMP-007 | [Validate the portable skill independently of host packaging](007-validate-portable-skill-package.md) | P2 | M | IMP-004 | TODO | - | - |
| IMP-008 | [Project complete lifecycle state in the plan index](008-project-complete-lifecycle-state.md) | P2 | M | IMP-002, IMP-003, IMP-004 | TODO | - | - |
| IMP-009 | [Make lifecycle state reviewer-owned and gate execution from plan files](009-make-lifecycle-state-reviewer-owned.md) | P1 | M | IMP-002, IMP-008 | TODO | - | - |
| IMP-010 | [Resolve and propagate one selected plans directory](010-propagate-selected-plans-directory.md) | P2 | M | IMP-009 | TODO | - | - |
| IMP-011 | [Reconcile squash, cherry-pick, and rebased integrations](011-reconcile-non-ancestral-integrations.md) | P2 | M | IMP-010 | TODO | - | - |
| IMP-012 | [Make root-cause discipline native to Improve](012-make-root-cause-discipline-native.md) | P1 | M | IMP-005, IMP-009 | TODO | - | - |
| IMP-013 | [Add a manual cross-host conformance checklist](013-add-portability-conformance-checklist.md) | P2 | S | IMP-007, IMP-010, IMP-012 | TODO | - | - |

Status values: TODO | EXECUTING | REVIEWED | DONE | BLOCKED | REJECTED

## Findings Considered and Rejected

None recorded.
