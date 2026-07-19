---
id: IMP-007
title: Validate the portable skill independently of host packaging
status: TODO
priority: P2
effort: M
risk: LOW
category: dx
base_commit: 4adde10c1d1d6308c485b87efbbefb6a6a241785
created_at: 2026-07-19
updated_at: 2026-07-19
scope:
  - scripts/check.py
  - scripts/check_tests.py
  - README.md
  - .claude-plugin/plugin.json
  - .claude-plugin/marketplace.json
dependencies:
  - IMP-004
execution_base: null
reviewed_commit: null
merged_commit: null
sensitive: false
issue: null
---

## Plan 007: Validate the portable skill independently of host packaging

> **Executor instructions**: Keep `skills/improve/` as the canonical artifact.
> Treat `.claude-plugin/` as an optional distribution adapter: validate it when
> present, but do not make it a prerequisite for an otherwise valid Agent
> Skills package. Use the official Agent Skills name rules cited below. Run all
> permitted checks, but do not modify this plan or the generated index. Report
> STATUS, HEAD SHA, FILES CHANGED, VERIFICATION RESULTS, and NOTES; the reviewer
> owns lifecycle metadata and index regeneration.
>
> **Drift check (run first)**: run
> `git diff --stat 4adde10c1d1d6308c485b87efbbefb6a6a241785..HEAD -- scripts/check.py scripts/check_tests.py README.md .claude-plugin/plugin.json .claude-plugin/marketplace.json`.
> Stop if IMP-004's host-neutral compatibility language is not present or if
> the project has adopted a different canonical packaging format.

## Why this matters

The package checker currently defines validity partly in terms of a mandatory
Claude plugin manifest and a slash-command README. That contradicts the goal of
using one canonical Agent Skill across Codex, GitHub Copilot, Claude Code, and
Cursor. It also implements a skill-name regex that rejects some names allowed by
the open standard and accepts malformed hyphen placement. Validation should
have a host-neutral core plus optional adapter checks, while retaining the
Claude wrapper for users who want that installation route.

## Current state

- `scripts/check.py:15` defines:

  ```python
  SKILL_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
  ```

  This requires at least two characters and a leading letter, while allowing
  trailing or consecutive hyphens. The current Agent Skills specification uses
  1-64 lowercase alphanumeric/hyphen characters with no leading, trailing, or
  consecutive hyphen. Authoritative source:
  `https://agentskills.io/specification`.
- `scripts/check.py:48-54` always calls `check_plugin_manifest` as part of the
  core run.
- Lines 131-177 fail when `.claude-plugin/plugin.json` is absent and compare its
  name/version with the skill.
- Lines 179-204 validate the README install target against the Claude plugin's
  repository field.
- Lines 240-254 and 391-398 require every README variant to appear as a line
  starting `/improve`, making one host's invocation syntax part of package
  validity.
- `scripts/check_tests.py:69-74` includes `.claude-plugin/plugin.json` in every
  base fixture, so no fixture proves the portable core stands alone.
- `.claude-plugin/marketplace.json:4` still names upstream author `shadcn` as
  marketplace owner even though `plugin.json:6` and `SKILL.md:11` identify
  `Iwaschkin` as the fork maintainer. Its description calls the catalog simply
  “the improve plugin” rather than an optional Claude adapter.
- `README.md:15-19` presents one generic installer but does not give explicit
  per-host/manual placement guidance or explain that `.claude-plugin` is
  optional.
- Preserve the existing checker style: numbered checks, accumulated failures,
  standard library only, temporary fixtures, and readable `PASS` output.

## Commands you will need

| Purpose | Command | Provenance | Execution class | Expected on success |
| --- | --- | --- | --- | --- |
| Structural checker | `python scripts/check.py` | CI line 20; not run by advisor | EXECUTES_REPOSITORY_CODE | exit 0 and all checks pass |
| Checker fixtures | `python scripts/check_tests.py` | CI line 21; not run by advisor | EXECUTES_REPOSITORY_CODE | all fixtures pass |
| Generator tests | `python scripts/generate_plan_index_tests.py` | IMP-002; run if available | EXECUTES_REPOSITORY_CODE | all fixtures pass |
| JSON syntax | `python -m json.tool .claude-plugin/plugin.json` | Python standard library | STATIC_READ | normalized JSON, exit 0 |
| Marketplace JSON syntax | `python -m json.tool .claude-plugin/marketplace.json` | Python standard library | STATIC_READ | normalized JSON, exit 0 |

## Scope

One behavioral objective: validate a standards-compliant canonical skill even
without optional host packaging, while validating any present Claude adapter
consistently.

**In scope**:

- `scripts/check.py`
- `scripts/check_tests.py`
- `README.md`
- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`

**Out of scope**:

- Creating manifests or plugins for Codex, Copilot, or Cursor.
- Changing the skill's workflow content; IMP-004 owns that.
- Replacing the frontmatter parser with a third-party YAML dependency.
- Publishing packages or running networked registry validation.

## Git workflow

- Branch: `advisor/007-portable-package-validation`
- Commit message: `test: validate portable skill packaging`.
- Keep checker changes, fixtures, docs, and adapter metadata together.
- Do not push, publish, or open a PR unless instructed.

## Steps

### Step 1: Implement the official skill-name constraints

Replace the current regex-only assumption with explicit validation equivalent
to:

- length is 1 through 64 characters;
- characters are lowercase ASCII letters, digits, or hyphens;
- first and last characters are alphanumeric;
- `--` is forbidden.

A regex such as `^[a-z0-9]+(?:-[a-z0-9]+)*$` plus an explicit length check is
acceptable. Error messages must identify the violated rule rather than cite an
outdated regex. Continue requiring the skill directory name to equal the
frontmatter name.

Add fixtures proving:

- `a`, `1`, `a1`, and `1-skill` are valid names;
- uppercase, underscore, leading hyphen, trailing hyphen, consecutive hyphen,
  empty, and 65-character names fail;
- directory/name mismatch still fails.

**Verify**: `python scripts/check_tests.py` -> all name fixtures pass.

### Step 2: Separate core validation from optional adapter validation

Refactor `Checker.run()` conceptually into:

1. canonical Agent Skill/project checks that always run;
2. optional host-adapter checks that run only when the adapter exists.

Absence of `.claude-plugin/plugin.json` must not fail a valid core fixture. If
the file exists, malformed JSON, missing required manifest fields, or
name/version disagreement must still fail. If `marketplace.json` exists,
validate it as a JSON object with a nonempty owner, plugin entry for `improve`,
and source pointing at the repository root. Do not require a marketplace file
when the plugin manifest is absent.

Keep `compatibility` and `metadata.version` as this repository's documented
release-policy fields even though only `name` and `description` are mandatory
in the open base format. Label project-policy failures separately from base
spec failures so users can distinguish them.

**Verify**: fixtures cover valid core without plugin, valid core with plugin,
invalid present plugin, version mismatch, invalid present marketplace, and no
marketplace.

### Step 3: Decouple README validation from slash syntax and Claude metadata

Continue checking that `npx skills add <owner>/<repo>` is present for the
supported generic installer. When a plugin manifest exists, its repository may
cross-check that target; when it does not, validate only command shape unless a
canonical repository source is available from host-neutral metadata.

Validate that all invocation variant names are documented in the README, but
do not require every variant to begin with `/improve`. Accept a dedicated usage
block/table containing the variant tokens and let IMP-004's host invocation
table explain the prefix. Continue requiring the variants in `SKILL.md`.

Add fixtures for host-neutral usage text without slash prefixes and retain a
failure fixture for a genuinely missing variant.

**Verify**: `python scripts/check_tests.py` -> invocation fixtures pass.

### Step 4: Correct and position the Claude adapter

Change `.claude-plugin/marketplace.json` owner to `Iwaschkin`, matching the fork
maintainer. Describe it as the Claude Code marketplace adapter for the portable
`improve` skill. Retain upstream attribution in `plugin.json` and the README;
do not erase `shadcn` authorship history.

Review `plugin.json` wording so it does not imply Claude-only behavior or
unverified universal automatic execution. Keep version `1.1.0` unless release
policy explicitly requires a version bump in a separate release task.

Update README installation documentation with:

- generic `npx skills add Iwaschkin/improve` route;
- canonical folder `skills/improve/` in this repository;
- a link to `host-compatibility.md` for current host-specific locations;
- an explanation that `.claude-plugin` is an optional adapter, not the source
  of workflow truth;
- guidance to verify/update an installed copy so users do not unknowingly run
  an older upstream skill.

**Verify**: both JSON-tool commands, `python scripts/check.py`, and
`python scripts/check_tests.py` exit 0.

### Step 5: Enforce a size budget for the core instruction file

`SKILL.md` is loaded as prompt text on every invocation, and eight of the
backlog's plans add instruction mass to it or its references. Unchecked growth
degrades adherence, especially on hosts with tighter context budgets. Add a
checker rule that measures `skills/improve/SKILL.md` and fails when it exceeds
a documented budget of 32 KiB or 400 lines (roughly twice its current size).
The failure message must say the remedy is moving detail into a phase-loaded
reference, not raising the budget. Document the budget and its rationale in a
comment beside the constant.

Add fixtures: the current real file passes; a generated oversized fixture
fails with the budget named in the diagnostic. Reference files are exempt —
they are loaded only at the phase that needs them, which is the pressure valve
this rule is designed to preserve.

**Verify**: `python scripts/check_tests.py` -> size-budget fixtures pass.

## Test plan

- Expand the existing generated-fixture matrix rather than committing fixture
  directories.
- Ensure every invalid-name fixture fails for the intended rule; assert a
  diagnostic substring where practical, not only exit status.
- Test four packaging states: core only, core+plugin, core+plugin+marketplace,
  and malformed optional adapter.
- Test host-neutral variant documentation independently of slash invocation.
- Retain broken-link and version-agreement coverage.

## Done criteria

- [ ] Skill names exactly follow current Agent Skills length/character/hyphen
      constraints.
- [ ] A valid canonical skill passes when `.claude-plugin` is absent.
- [ ] A present Claude plugin/marketplace is still fully validated.
- [ ] README variant validation is independent of `/improve` syntax.
- [ ] Generic installer validation works with and without Claude metadata.
- [ ] Marketplace owner and description identify the maintained fork and
      optional adapter role while preserving upstream attribution.
- [ ] README documents canonical, generic, and host-specific installation paths.
- [ ] The checker enforces the documented `SKILL.md` size budget with positive
      and negative fixtures.
- [ ] `python scripts/check.py` exits 0.
- [ ] `python scripts/check_tests.py` exits 0 with all new fixtures.
- [ ] No files outside the five in-scope paths are modified.
- [ ] The executor report contains STATUS, HEAD SHA, FILES CHANGED,
      VERIFICATION RESULTS, and NOTES; the reviewer owns lifecycle metadata and
      index regeneration.

## STOP conditions

Stop and report if:

- The official Agent Skills specification has changed from the constraints
  cited in Current state; record the live rules and adapt the fixtures instead
  of using this plan's stale regex suggestion.
- The generic installer requires Claude metadata to resolve this repository;
  establish that from primary documentation before retaining the coupling.
- Making the plugin optional would break an explicitly supported release
  workflow not documented in the repository.
- A version bump or marketplace publication is required; separate that external
  release action from this implementation.
- More than the five in-scope files are required.

## Maintenance notes

- The checker should distinguish open-format validity, this repository's policy,
  and optional adapter validity in its output.
- Never add a host wrapper to core validation merely because it is currently
  the easiest installation route.
- Repository policy is exactly one canonical skill in `skills/` (`improve`).
  Keep the one-skill check, and make its failure message state that
  development-only reference material must live outside `skills/` or remain
  untracked.
- Recheck the open specification during future releases and keep positive edge
  fixtures for minimum/maximum valid names.
