---
id: IMP-002
title: Reject invalid plan metadata and test the generator
status: TODO
priority: P1
effort: M
risk: MED
category: bug
base_commit: 4adde10c1d1d6308c485b87efbbefb6a6a241785
created_at: 2026-07-19
updated_at: 2026-07-19
scope:
  - skills/improve/resources/generate_plan_index.py
  - scripts/generate_plan_index_tests.py
  - skills/improve/references/plan-template.md
  - .github/workflows/check.yml
dependencies: []
execution_base: null
reviewed_commit: null
merged_commit: null
sensitive: false
issue: null
---

## Plan 002: Reject invalid plan metadata and test the generator

> **Executor instructions**: Implement validation before expanding lifecycle
> fields. Use only the Python standard library. Run every permitted verification
> command and stop if preserving malformed-plan compatibility would require
> silent coercion. Do not modify this plan or the generated index. Report
> STATUS, HEAD SHA, FILES CHANGED, VERIFICATION RESULTS, and NOTES; the reviewer
> owns lifecycle metadata and index regeneration.
>
> **Drift check (run first)**: run
> `git diff --stat 4adde10c1d1d6308c485b87efbbefb6a6a241785..HEAD -- skills/improve/resources/generate_plan_index.py scripts/generate_plan_index_tests.py skills/improve/references/plan-template.md .github/workflows/check.yml`.
> The test script does not exist at the planned base and is expected to be
> created. Stop if the generator has already acquired a different schema or
> parser library.

## Why this matters

The generated index is the backlog's control plane, but malformed or missing
frontmatter is currently skipped without an error. A typo can therefore remove
a plan from the index while the command exits successfully, and CI exercises
only an empty plan directory. The generator must fail closed, validate the
published schema, preserve the previous index on failure, and have focused
fixture tests before lifecycle projection becomes more complex in IMP-008.

## Current state

- `skills/improve/resources/generate_plan_index.py:15-22` returns `None` for
  absent or unterminated frontmatter without explaining why.
- Lines 50-51 silently ignore malformed lines without a colon.
- Lines 66-75 scan every Markdown plan but silently `continue` when
  frontmatter is missing:

  ```python
  frontmatter = split_frontmatter(text)
  if frontmatter is None:
      continue
  data = parse_frontmatter(frontmatter)
  data["file"] = path.name
  rows.append(data)
  ```

- Lines 133-143 always write the new index after collecting rows; there is no
  validation phase or atomic-write behavior.
- `.github/workflows/check.yml:22` invokes the generator against
  `"$RUNNER_TEMP/plans"`, which is empty. It proves startup only, not parsing or
  rejection behavior.
- `skills/improve/references/plan-template.md` publishes required fields and
  enums, including full 40-character commit SHAs, but the generator validates
  none of them.
- Existing test style in `scripts/check_tests.py`: standard-library temporary
  directories, generated fixtures, subprocess invocation, explicit expected
  exit status, and readable `PASS`/`FAIL` output. Match that style in the new
  test module.

## Commands you will need

| Purpose | Command | Provenance | Execution class | Expected on success |
| --- | --- | --- | --- | --- |
| Generator tests | `python scripts/generate_plan_index_tests.py` | added by this plan | EXECUTES_REPOSITORY_CODE | exit 0 and all fixtures pass |
| Structural checker | `python scripts/check.py` | CI line 20; not run by advisor | EXECUTES_REPOSITORY_CODE | exit 0 |
| Checker fixtures | `python scripts/check_tests.py` | CI line 21; not run by advisor | EXECUTES_REPOSITORY_CODE | exit 0 |
| Syntax check | `python -m py_compile skills/improve/resources/generate_plan_index.py scripts/generate_plan_index_tests.py` | Python standard library; not run by advisor | MAY_WRITE_CACHE | exit 0 |

Run syntax compilation only where writing `__pycache__` is permitted and
ignored. The required verification is the dedicated fixture suite.

## Scope

One behavioral objective: invalid plan metadata must produce actionable errors,
a nonzero exit, and no partial/overwritten index.

**In scope**:

- `skills/improve/resources/generate_plan_index.py`
- `scripts/generate_plan_index_tests.py` (create)
- `skills/improve/references/plan-template.md`
- `.github/workflows/check.yml`

**Out of scope**:

- New lifecycle fields, rejection storage, and wider index tables; IMP-008 owns
  those after validation exists.
- A third-party YAML dependency or new package-management configuration.
- Rewriting `scripts/check.py`; IMP-007 owns structural package validation.
- Changing plan status semantics.

## Git workflow

- Branch: `advisor/002-validate-plan-metadata`
- Commit message: `test: validate generated plan metadata`.
- Keep implementation and fixtures in one logical commit.
- Do not push or open a PR unless instructed.

## Steps

### Step 1: Introduce explicit parse and validation errors

Replace optional/silent parse results with structured diagnostics containing
the relative file, line where possible, field, and reason. It is acceptable to
define small standard-library dataclasses or custom exceptions inside the
generator; do not add dependencies.

Distinguish at least:

- file does not begin with `---`;
- frontmatter has no closing delimiter;
- malformed top-level line;
- malformed list entry or unexpected indentation;
- duplicate key;
- unsupported scalar/list shape for a known field.

Aggregate errors across all plan files so one run reports the entire repair
set. Exit nonzero if any error exists.

**Verify**: fixtures for each syntax error fail with the filename and a useful
reason in captured output.

### Step 2: Validate the published base schema

Validate these required fields from `plan-template.md`:

- `id`, `title`, `status`, `priority`, `effort`, `risk`, `category`;
- `base_commit`, `working_tree_clean`, `created_at`, `updated_at`;
- nonempty `scope` list and `dependencies` list (empty is valid);
- `execution_branch`, `execution_base`, `reviewed_commit`, `merged_commit`;
- boolean `sensitive`; nullable/string `issue`.

Enforce:

- `id` matches `IMP-NNN` and `NNN` matches the filename prefix;
- plan filenames match `NNN-lowercase-hyphen-slug.md`;
- status, priority, effort, risk, and category use template enums;
- `base_commit` is exactly 40 lowercase hexadecimal characters;
- lifecycle commit fields are null or exactly 40 lowercase hexadecimal chars;
- dates use `YYYY-MM-DD` and `updated_at` is not earlier than `created_at`;
- booleans remain booleans rather than quoted strings;
- scope/dependency items are nonempty strings;
- IDs and filenames are unique;
- every dependency resolves to another plan ID and no plan depends on itself;
- the dependency graph is acyclic.
- filename/plan-number order is a valid topological order: every dependency
  appears earlier than its dependent plan. Reject an out-of-order graph rather
  than presenting filename order as executable order.

Allow unknown fields so IMP-008 and future compatible extensions can be
introduced without breaking older generators, but never ignore malformed known
fields.

**Verify**: one valid multi-plan dependency fixture passes; fixtures for each
constraint fail.

### Step 3: Protect the existing index on failure

Parse and validate all plans before rendering. If validation fails, do not
create or replace `README.md`. When validation succeeds, write to a temporary
file in the same directory and atomically replace the index so interruption
cannot leave a partial file.

Do not treat `README.md` as a plan. At this stage every other `*.md` in the
plans directory is a plan and must validate; IMP-008 may add a separately named
machine-readable rejection source.

**Verify**: a fixture starts with a sentinel README, introduces an invalid plan,
runs the generator, and confirms the sentinel is byte-for-byte unchanged.

### Step 4: Add the fixture suite

Create `scripts/generate_plan_index_tests.py` following
`scripts/check_tests.py` conventions. Generate fixtures at runtime inside a
temporary directory rather than committing fixture trees. Cover at minimum:

- valid single plan;
- valid ordered dependency graph;
- missing/unterminated/malformed frontmatter;
- missing required field and invalid enum;
- short/invalid SHA;
- quoted boolean and non-list scope;
- filename/ID mismatch and duplicate ID;
- missing dependency, self-dependency, and cycle;
- dependency that exists but is numbered after its dependent plan;
- invalid plan preserves existing README;
- valid run creates deterministic index content.

Print individual case names and a final summary. Make failures include captured
stdout/stderr.

**Verify**: `python scripts/generate_plan_index_tests.py` -> all cases pass.

### Step 5: Replace the empty CI smoke test

Add the dedicated test command to `.github/workflows/check.yml`. Retain one
successful generator invocation if desired, but it must use a valid fixture or
the test suite rather than an empty directory. Keep the existing pinned actions,
read-only permissions, Python 3.12, and five-minute timeout.

Run the check job on both `ubuntu-latest` and `windows-latest` through a
strategy matrix so the checker, checker fixtures, and generator suite are
exercised on POSIX and Windows path/temp-file semantics in CI, not only in
local claims. Apply the pinned action SHAs and read-only permissions to both
matrix legs.

Update `plan-template.md` to state that malformed plans fail index generation
and that the prior index is retained. Do not document IMP-008 fields yet.

**Verify**: all three Python test/check commands exit 0 and `git diff --check`
exits 0.

## Test plan

- The new fixture suite is the primary regression test and must exercise both
  subprocess exit status and filesystem effects.
- Use minimal but complete frontmatter builders so a fixture fails only for its
  intended reason.
- Include Windows-safe temporary paths and invoke the generator with
  `sys.executable`, not a hardcoded `python` inside the test process.
- Assert deterministic ordering by filename/ID and exact README bytes for at
  least one valid fixture.

## Done criteria

- [ ] No malformed or missing-frontmatter plan is silently skipped.
- [ ] Every published required field and enum is validated.
- [ ] Full SHA, filename/ID, dependency existence, and cycle rules are enforced.
- [ ] Filename order is verified as a valid dependency order; out-of-order
      dependencies fail closed.
- [ ] All validation errors name the offending file and field/reason.
- [ ] Invalid input exits nonzero and preserves the previous index unchanged.
- [ ] Successful generation replaces the index atomically and deterministically.
- [ ] `python scripts/generate_plan_index_tests.py` exits 0.
- [ ] `python scripts/check.py` exits 0.
- [ ] `python scripts/check_tests.py` exits 0.
- [ ] CI runs the generator fixture suite rather than only an empty smoke test.
- [ ] CI runs the checker, checker fixtures, and generator suite on both
      `ubuntu-latest` and `windows-latest`.
- [ ] No files outside the four in-scope paths are modified.
- [ ] The executor report contains STATUS, HEAD SHA, FILES CHANGED,
      VERIFICATION RESULTS, and NOTES; the reviewer owns lifecycle metadata and
      index regeneration.

## STOP conditions

Stop and report if:

- Correct parsing requires accepting arbitrary YAML beyond the documented flat
  scalar/list subset; propose a dependency/design plan instead of writing a
  partial YAML implementation.
- Existing committed plans violate the published template in a way that shows
  the template, not the plans, is authoritative but wrong.
- Atomic replacement is unavailable on a supported platform using
  `Path.replace`; document the platform evidence before choosing another
  mechanism.
- IMP-008 has already introduced fields without tests; reconcile its schema
  rather than discarding them.
- More than the four in-scope files are required.

## Maintenance notes

- Keep parser scope explicit. A strict documented subset is safer than a
  home-grown parser that appears to support all YAML.
- Any new required field must add both a positive and negative fixture in the
  same change.
- Reviewers should scrutinize silent coercion and write-before-validate paths;
  those recreate the original bug under a different shape.
