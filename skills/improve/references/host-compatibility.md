# Host Compatibility

The core workflow in `SKILL.md` is written against the **capability contract**
below, never against one vendor's tool names. Map the contract onto whatever
host you are running in by checking what that host actually provides at the
phase that needs it (audit delegation or `execute` dispatch) — its
documentation, its available tools, or a direct probe. Never invent a host API
you have not confirmed exists.

## Capability contract

| Capability | Needed for | When missing |
| --- | --- | --- |
| Repository read access | Everything | Stop — nothing works without it |
| Plan-directory write access | Planning | Stop and say the plans directory cannot be written; produce findings only |
| Bounded read-only worker delegation | Parallel audit (optional) | Audit sequentially yourself in category-priority order |
| Skill-resource visibility to workers | Cheap delegated prompts | Inline the finding contract and category guidance into each worker prompt |
| Isolated writable executor | Automatic `execute` | Hand the plan over for manual execution |
| Enforced sandbox for repository-code execution | Untrusted-repo verification (optional) | Executor edits files only; verification reported as skipped; done criteria handed to the user |
| Executor continuation or redispatch | REVISE round | Redispatch fresh with the full plan, prior report, current SHAs, and the feedback |
| Execution locator (local path, task id, branch, or PR URL) | Review and reconcile | Without any locator, automatic execution is off — manual handoff |
| Git base/head identity and diff access | Review, drift checks, reconcile | Automatic execution is off — manual handoff |

Degradation is always explicit: say which capability is missing and which
fallback you are using. Never describe a prompt instruction as an enforceable
tool restriction.

**Cross-provider fallback is never silent.** Launching a different vendor's
CLI as the executor changes data routing, credentials, billing, and policy.
Offer it; proceed only on explicit user selection.

Any host implementing the Agent Skills format
(`https://agentskills.io/specification`) can run audit and planning if it
grants repository read and plan-directory write access. When a capability
cannot be confirmed from the host's documentation or surface, treat it as
missing and use the fallback.
