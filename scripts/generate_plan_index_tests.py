#!/usr/bin/env python3
"""Fixture tests for skills/improve/resources/generate_plan_index.py."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = REPO_ROOT / "skills" / "improve" / "resources" / "generate_plan_index.py"

VALID_SHA = "4adde10c1d1d6308c485b87efbbefb6a6a241785"


def plan_frontmatter(**overrides: object) -> str:
    """Build a valid plan file, then apply field overrides.

    An override of None removes the field; a string override replaces the
    rendered line verbatim (so tests can inject malformed values).
    """
    fields: dict[str, str] = {
        "id": "id: IMP-001",
        "title": "title: Test plan",
        "status": "status: TODO",
        "priority": "priority: P1",
        "effort": "effort: S",
        "risk": "risk: LOW",
        "category": "category: bug",
        "base_commit": f"base_commit: {VALID_SHA}",
        "working_tree_clean": "working_tree_clean: true",
        "created_at": "created_at: 2026-07-19",
        "updated_at": "updated_at: 2026-07-19",
        "scope": "scope:\n  - src/example.py",
        "dependencies": "dependencies: []",
        "execution_branch": "execution_branch: null",
        "execution_base": "execution_base: null",
        "reviewed_commit": "reviewed_commit: null",
        "merged_commit": "merged_commit: null",
        "sensitive": "sensitive: false",
        "issue": "issue: null",
    }
    for key, value in overrides.items():
        if value is None:
            fields.pop(key, None)
        else:
            fields[key] = str(value)
    body = "\n".join(fields.values())
    return f"---\n{body}\n---\n\n## Plan\n\nBody text.\n"


def numbered_plan(number: int, dependencies: str = "dependencies: []") -> str:
    return plan_frontmatter(
        id=f"id: IMP-{number:03d}",
        title=f"title: Test plan {number}",
        dependencies=dependencies,
    )


def run_generator(plans_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GENERATOR), "--plans-dir", str(plans_dir)],
        capture_output=True,
        text=True,
    )


def fixture_files(name: str) -> tuple[dict[str, str], bool, list[str]]:
    """Return (files, expect_success, expected stderr substrings)."""
    if name == "valid-single-plan":
        return {"001-test-plan.md": plan_frontmatter()}, True, []
    if name == "valid-dependency-graph":
        return (
            {
                "001-first.md": numbered_plan(1),
                "002-second.md": numbered_plan(
                    2, "dependencies:\n  - IMP-001"
                ),
                "003-third.md": numbered_plan(
                    3, "dependencies:\n  - IMP-001\n  - IMP-002"
                ),
            },
            True,
            [],
        )
    if name == "missing-frontmatter":
        return (
            {"001-test-plan.md": "## Plan\n\nNo frontmatter at all.\n"},
            False,
            ["does not begin with '---'"],
        )
    if name == "unterminated-frontmatter":
        return (
            {"001-test-plan.md": "---\nid: IMP-001\ntitle: Test\n"},
            False,
            ["no closing '---'"],
        )
    if name == "malformed-line":
        return (
            {"001-test-plan.md": plan_frontmatter(title="title Test plan")},
            False,
            ["expected 'key: value'"],
        )
    if name == "unexpected-indentation":
        return (
            {"001-test-plan.md": plan_frontmatter(issue="issue: null\n    stray: value")},
            False,
            ["unexpected indented line"],
        )
    if name == "duplicate-key":
        return (
            {"001-test-plan.md": plan_frontmatter(issue="issue: null\nissue: null")},
            False,
            ["duplicate key"],
        )
    if name == "missing-required-field":
        return (
            {"001-test-plan.md": plan_frontmatter(status=None)},
            False,
            ["status", "required field is missing"],
        )
    if name == "invalid-enum":
        return (
            {"001-test-plan.md": plan_frontmatter(priority="priority: URGENT")},
            False,
            ["priority", "'URGENT'"],
        )
    if name == "short-sha":
        return (
            {"001-test-plan.md": plan_frontmatter(base_commit="base_commit: 4adde10")},
            False,
            ["base_commit", "40-character"],
        )
    if name == "invalid-lifecycle-sha":
        return (
            {"001-test-plan.md": plan_frontmatter(reviewed_commit="reviewed_commit: not-a-sha")},
            False,
            ["reviewed_commit", "40-character"],
        )
    if name == "quoted-boolean":
        return (
            {"001-test-plan.md": plan_frontmatter(sensitive='sensitive: "false"')},
            False,
            ["sensitive", "unquoted boolean"],
        )
    if name == "scalar-scope":
        return (
            {"001-test-plan.md": plan_frontmatter(scope="scope: src/example.py")},
            False,
            ["scope", "nonempty list"],
        )
    if name == "bad-date-order":
        return (
            {
                "001-test-plan.md": plan_frontmatter(
                    created_at="created_at: 2026-07-19",
                    updated_at="updated_at: 2026-07-18",
                )
            },
            False,
            ["updated_at", "earlier than created_at"],
        )
    if name == "filename-id-mismatch":
        return (
            {"002-test-plan.md": plan_frontmatter()},
            False,
            ["id number 001 does not match filename prefix 002"],
        )
    if name == "bad-filename-slug":
        return (
            {"001-Test_Plan.md": plan_frontmatter()},
            False,
            ["NNN-lowercase-hyphen-slug"],
        )
    if name == "duplicate-id":
        return (
            {
                "001-first.md": numbered_plan(1),
                "002-second.md": plan_frontmatter(
                    id="id: IMP-001", title="title: Duplicate"
                ),
            },
            False,
            ["duplicate plan id", "does not match filename prefix"],
        )
    if name == "missing-dependency":
        return (
            {
                "002-second.md": numbered_plan(2, "dependencies:\n  - IMP-001"),
            },
            False,
            ["'IMP-001' does not resolve"],
        )
    if name == "self-dependency":
        return (
            {"001-first.md": numbered_plan(1, "dependencies:\n  - IMP-001")},
            False,
            ["depends on itself"],
        )
    if name == "dependency-cycle":
        return (
            {
                "001-first.md": numbered_plan(1, "dependencies:\n  - IMP-002"),
                "002-second.md": numbered_plan(2, "dependencies:\n  - IMP-001"),
            },
            False,
            ["not numbered earlier", "cycle"],
        )
    if name == "out-of-order-dependency":
        return (
            {
                "001-first.md": numbered_plan(1, "dependencies:\n  - IMP-002"),
                "002-second.md": numbered_plan(2),
            },
            False,
            ["'IMP-002' is not numbered earlier than 'IMP-001'"],
        )
    raise ValueError(f"unknown fixture {name}")


CASES = [
    "valid-single-plan",
    "valid-dependency-graph",
    "missing-frontmatter",
    "unterminated-frontmatter",
    "malformed-line",
    "unexpected-indentation",
    "duplicate-key",
    "missing-required-field",
    "invalid-enum",
    "short-sha",
    "invalid-lifecycle-sha",
    "quoted-boolean",
    "scalar-scope",
    "bad-date-order",
    "filename-id-mismatch",
    "bad-filename-slug",
    "duplicate-id",
    "missing-dependency",
    "self-dependency",
    "dependency-cycle",
    "out-of-order-dependency",
]


def run_case(name: str) -> bool:
    files, expect_success, expected_stderr = fixture_files(name)
    with tempfile.TemporaryDirectory() as tmp:
        plans_dir = Path(tmp) / "plans"
        plans_dir.mkdir()
        sentinel = "# SENTINEL previous index — must survive failed runs\n"
        (plans_dir / "README.md").write_text(sentinel, encoding="utf-8")
        for rel, content in files.items():
            (plans_dir / rel).write_text(content, encoding="utf-8")
        result = run_generator(plans_dir)
        ok = (result.returncode == 0) == expect_success
        if expect_success:
            index = (plans_dir / "README.md").read_text(encoding="utf-8")
            if index == sentinel:
                ok = False
                print(f"  index was not regenerated on success")
            for rel in files:
                if rel.replace(".md", "") not in index:
                    ok = False
                    print(f"  index missing entry for {rel}")
        else:
            index = (plans_dir / "README.md").read_text(encoding="utf-8")
            if index != sentinel:
                ok = False
                print("  previous index was not preserved on failure")
            for expected in expected_stderr:
                if expected not in result.stderr:
                    ok = False
                    print(f"  stderr missing {expected!r}")
        if not ok:
            print(f"  exit={result.returncode} expected success={expect_success}")
            print("  stdout:", result.stdout.strip())
            print("  stderr:", result.stderr.strip())
        return ok


def test_deterministic_output() -> bool:
    """Two runs over the same valid fixture produce identical index bytes."""
    files, _, _ = fixture_files("valid-dependency-graph")
    outputs: list[bytes] = []
    for _ in range(2):
        with tempfile.TemporaryDirectory() as tmp:
            plans_dir = Path(tmp) / "plans"
            plans_dir.mkdir()
            for rel, content in files.items():
                (plans_dir / rel).write_text(content, encoding="utf-8")
            result = run_generator(plans_dir)
            if result.returncode != 0:
                print("  generator failed on valid fixture:", result.stderr.strip())
                return False
            outputs.append((plans_dir / "README.md").read_bytes())
    if outputs[0] != outputs[1]:
        print("  index output is not deterministic")
        return False
    if b"IMP-002" not in outputs[0] or b"IMP-001, IMP-002" not in outputs[0]:
        print("  index content missing expected rows")
        return False
    return True


def main() -> int:
    failures = 0
    for name in CASES:
        if run_case(name):
            print(f"PASS {name}")
        else:
            print(f"FAIL {name}")
            failures += 1
    if test_deterministic_output():
        print("PASS deterministic-output")
    else:
        print("FAIL deterministic-output")
        failures += 1
    if failures:
        print(f"{failures} generator fixture test(s) failed")
        return 1
    print("all generator fixture tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
