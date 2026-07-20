# Developing this repository

This repo ships a portable Agent Skill — `skills/improve/` — plus the tooling
that validates it. The Markdown under `skills/improve/` **is the product**:
edits to `SKILL.md` or its references change the skill's behavior, and are
reviewed as behavior changes, not documentation polish.

## Verify a change

Run each command from the repository root; all must succeed before a commit:

- `python scripts/check.py` — structural checks; expect exit 0 and
  `all checks passed`.
- `python scripts/check_tests.py` — checker fixture suite; expect all PASS.
- `git diff --check` — no whitespace errors.

Python 3.10+ locally; CI pins 3.12 (see `.github/workflows/check.yml`).

## Conventions

- Normative Markdown is imperative and specific: bold rules, compact tables,
  exact commands with expected results. Match the style of
  `skills/improve/SKILL.md`.
- Python is standard-library-only, typed, and starts with
  `from __future__ import annotations`. Do not add dependencies, package
  managers, or config files for tooling.
- CI actions stay pinned to full commit SHAs with read-only permissions.

## Packaging rules

- Exactly one skill lives in `skills/` (`improve`). Development-only reference
  material stays untracked or outside `skills/` — the checker fails on a
  second `skills/*/SKILL.md`.
- `skills/improve/SKILL.md` `metadata.version` and
  `.claude-plugin/plugin.json` `version` must change together; the checker
  enforces agreement.
- `.claude-plugin/` is a distribution adapter for Claude Code, not the source
  of workflow truth.

## Plan backlog

Improvement work is planned in `docs/dev/plans/` — one self-contained plan per
file, YAML frontmatter as the authoritative lifecycle record. Once a plan's
work is merged and verified, delete the plan file and regenerate the index —
the commit history is the record; the backlog holds only open work.
`docs/dev/plans/README.md` is **generated**; never hand-edit it. Regenerate
with:

```bash
python skills/improve/resources/generate_plan_index.py --plans-dir docs/dev/plans
```

## Release checklist

1. Bump both version fields together (`SKILL.md` metadata and `plugin.json`).
2. Run all verification commands above.
3. If behavior changed, update the compatibility/conformance documentation to
   match what is actually verified.
