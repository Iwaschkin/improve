---
id: IMP-006
title: Align audit commands with the execution safety policy
status: TODO
priority: P2
effort: S
risk: LOW
category: security
base_commit: 4adde10c1d1d6308c485b87efbbefb6a6a241785
created_at: 2026-07-19
updated_at: 2026-07-19
scope:
  - skills/improve/SKILL.md
  - skills/improve/references/audit-playbook.md
  - skills/improve/references/plan-template.md
  - README.md
dependencies:
  - IMP-003
execution_base: null
reviewed_commit: null
merged_commit: null
sensitive: false
issue: null
---

## Plan 006: Align audit commands with the execution safety policy

> **Executor instructions**: Reconcile the command taxonomy without weakening
> the invariant boundaries from IMP-003. Do not claim a package-manager audit
> command is universally side-effect-free; classify its actual effects. Run
> permitted checks, but do not modify this plan or the generated index. Report
> STATUS, HEAD SHA, FILES CHANGED, VERIFICATION RESULTS, and NOTES; a reviewer
> owns lifecycle metadata and index regeneration.
>
> **Drift check (run first)**: run
> `git diff --stat 4adde10c1d1d6308c485b87efbbefb6a6a241785..HEAD -- skills/improve/SKILL.md skills/improve/references/audit-playbook.md skills/improve/references/plan-template.md README.md`.
> Stop if IMP-003's trust profiles are not present.

## Why this matters

The hard rules treat package-manager commands as repository-code execution,
while the security playbook directs auditors to run ecosystem audit commands.
An agent following both cannot know whether to execute, refuse, or ask. A single
effect-based taxonomy should distinguish static reads, network-only advisory
queries, commands that may run repository scripts, and commands with external
side effects, then map each class to the selected trust profile and host policy.

## Current state

- `skills/improve/SKILL.md:25` says:

  ```markdown
  Treat build, test, lint, framework, package-manager, and install commands as
  repository-code execution even when they are named "checks" ...
  ```

- `skills/improve/references/audit-playbook.md:36` says:

  ```markdown
  run the ecosystem's audit command (`npm audit`, `pip-audit`, `cargo audit`)
  in read-only mode
  ```

- `audit-playbook.md:73-80` separately and correctly requires live evidence,
  verification date, primary source type, reachability, and an `unavailable`
  result when online verification cannot be performed.
- `plan-template.md` defines execution classes including `STATIC_READ`,
  `GIT_READ`, `EXECUTES_REPOSITORY_CODE`, `MAY_WRITE_CACHE`, `NETWORK_ACCESS`,
  `PACKAGE_INSTALL`, and `HOST_MUTATION`, but does not explain combinations or
  approval rules.
- `README.md:86` tells users commands have provenance and safety notes, while
  line 117 repeats the broader repository-code confirmation requirement.
- Preserve the playbook's evidence discipline: report only reachable high/critical
  advisories and mark current-version claims provisional without live evidence.

## Commands you will need

| Purpose | Command | Provenance | Execution class | Expected on success |
| --- | --- | --- | --- | --- |
| Structural validation | `python scripts/check.py` | CI; not run by advisor | EXECUTES_REPOSITORY_CODE | exit 0 |
| Checker fixtures | `python scripts/check_tests.py` | CI; not run by advisor | EXECUTES_REPOSITORY_CODE | all pass |
| Whitespace | `git diff --check` | Git standard | GIT_READ | exit 0 |

Do not run package-manager audit commands while implementing this documentation
plan merely to prove they exist; there is no dependency manifest in this repo.

## Scope

One behavioral objective: give auditors one noncontradictory, effect-based rule
for command discovery, classification, permission, execution, and evidence.

**In scope**:

- `skills/improve/SKILL.md`
- `skills/improve/references/audit-playbook.md`
- `skills/improve/references/plan-template.md`
- `README.md`

**Out of scope**:

- Changing the trust profiles themselves.
- Implementing an ecosystem-specific vulnerability scanner.
- Adding dependencies or network calls to CI.
- Relaxing the requirement for live primary evidence on dependency claims.

## Git workflow

- Branch: `advisor/006-audit-command-safety`
- Commit message: `docs: align audit commands with safety policy`.
- Use one documentation commit.
- Do not push or open a PR unless instructed.

## Steps

### Step 1: Make command classification effect-based

Define these composable effects in `SKILL.md` or the template's command-table
guidance:

- `STATIC_READ` — reads files/configuration without executing repository code.
- `GIT_READ` — read-only Git operation.
- `NETWORK_ACCESS` — sends or receives data over a network.
- `MAY_WRITE_CACHE` — may write ignored/local cache state.
- `EXECUTES_REPOSITORY_CODE` — imports, builds, tests, lints, invokes scripts,
  plugins, hooks, or binaries controlled by the repository/dependencies.
- `PACKAGE_INSTALL` — resolves/downloads packages and may run lifecycle hooks.
- `HOST_MUTATION` — changes external services, system state, production data,
  Git remotes, or durable host configuration.

Allow a command to carry multiple effects. Permission follows the riskiest
effect, selected trust profile, and actual host enforcement. Command names do
not determine safety: a tool named `check` may execute code, while an advisory
API query may use a package manager without running lifecycle scripts.

**Verify**: every execution class in `plan-template.md` has one definition and
an approval rule.

### Step 2: Rewrite dependency-audit guidance

Change `audit-playbook.md` so dependency review proceeds in this order:

1. inspect manifests and lockfiles statically;
2. establish reachability from repository imports/build/distribution paths;
3. consult official advisories, vendor documentation, or registries when
   network access is permitted;
4. optionally run an ecosystem audit command only after determining from
   primary documentation that the selected invocation does not install
   packages or execute repository lifecycle/plugin code, and after obtaining
   any required network permission;
5. otherwise record `online_verification: unavailable` and mark the finding
   provisional.

Do not present `npm audit`, `pip-audit`, or `cargo audit` as universally
interchangeable or intrinsically read-only. Examples may remain, labeled as
ecosystem-specific commands whose effects must be checked.

**Verify**: the playbook no longer unconditionally says to run an audit command.

### Step 3: Align planning and user-facing language

Update the plan command table instructions to support multiple effects or a
comma-separated effect list, with exact provenance and whether the advisor ran
the command. Update the README hard rule and recon description to refer to
effect classification and the selected profile rather than banning/confirming
all package-manager commands by name.

Preserve the rule that install, build, test, lint, framework CLI, and package
scripts are presumed to execute repository-controlled code unless the agent
has concrete evidence otherwise.

**Verify**: `python scripts/check.py`, `python scripts/check_tests.py`, and
`git diff --check` exit 0.

## Test plan

- Manually classify these scenarios and ensure the text yields one result:
  - reading `package-lock.json` -> STATIC_READ;
  - querying an official advisory webpage -> NETWORK_ACCESS;
  - an audit command documented to submit a lockfile only -> NETWORK_ACCESS,
    subject to host/network policy;
  - `npm install` -> PACKAGE_INSTALL plus NETWORK_ACCESS and possible
    EXECUTES_REPOSITORY_CODE;
  - `pnpm test` -> EXECUTES_REPOSITORY_CODE and possibly MAY_WRITE_CACHE;
  - deployment CLI -> HOST_MUTATION plus NETWORK_ACCESS.
- Confirm unavailable network produces provisional evidence rather than a
  fabricated current-version claim.
- Behavioral cases are formalized in IMP-013.

## Done criteria

- [ ] One effect taxonomy governs recon, audit, planning, and execution.
- [ ] Commands can carry multiple effects and permission follows the riskiest.
- [ ] Dependency audit commands are optional and capability/evidence-gated.
- [ ] Install and lifecycle-script risk remains explicit.
- [ ] Lack of network evidence produces a provisional finding, not a current
      unsupported assertion.
- [ ] README, SKILL, playbook, and template no longer contradict each other.
- [ ] `python scripts/check.py` exits 0.
- [ ] `python scripts/check_tests.py` exits 0.
- [ ] No files outside the four in-scope paths are modified.
- [ ] The executor report contains STATUS, HEAD SHA, FILES CHANGED,
      VERIFICATION RESULTS, and NOTES; the reviewer owns lifecycle metadata and
      index regeneration.

## STOP conditions

Stop and report if:

- IMP-003's trust profiles are absent or materially different.
- An ecosystem command's documented effects cannot be established; label it
  unknown rather than classifying it as safe.
- The change would authorize network access or repository-code execution
  independently of the host/user permission model.
- More than the four in-scope files are required.

## Maintenance notes

- Reassess example commands when package managers change behavior; effects and
  primary documentation matter more than command names.
- Reviewers should reject language such as “read-only mode” unless the exact
  command's filesystem, script, and network effects are stated.
- This taxonomy should also guide future host adapters and the IMP-013
  conformance cases.
