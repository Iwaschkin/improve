#!/usr/bin/env python3
"""Fixture tests for skills/improve/resources/generate_plan_index.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = REPO_ROOT / "skills" / "improve" / "resources" / "generate_plan_index.py"

VALID_SHA = "4adde10c1d1d6308c485b87efbbefb6a6a241785"
OTHER_SHA = "1234567890abcdef1234567890abcdef12345678"


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
        "created_at": "created_at: 2026-07-19",
        "updated_at": "updated_at: 2026-07-19",
        "scope": "scope:\n  - src/example.py",
        "dependencies": "dependencies: []",
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


def numbered_plan(number: int, dependencies: str = "dependencies: []", **overrides: object) -> str:
    return plan_frontmatter(
        id=f"id: IMP-{number:03d}",
        title=f"title: Test plan {number}",
        dependencies=dependencies,
        **overrides,
    )


EXECUTION_RECORD = (
    "execution_locator: docs/dev/plans/.worktrees/001-test-plan\n"
    f"execution_base: {VALID_SHA}"
)


def done_plan(number: int, dependencies: str = "dependencies: []") -> str:
    """A DONE plan carrying its complete execution record."""
    return numbered_plan(
        number,
        dependencies,
        issue="issue: null\n"
        f"execution_locator: docs/dev/plans/.worktrees/{number:03d}-test\n"
        f"execution_base: {VALID_SHA}\n"
        f"reviewed_commit: {OTHER_SHA}\n"
        f"merged_commit: {OTHER_SHA}\n"
        "verified_at: 2026-07-19T12:00:00Z\n"
        "verification_environment: host-policy",
        status="status: DONE",
    )


def run_generator(plans_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    # The helper enforces repository-root containment: run from the fixture
    # root with a relative directory, the way the documented workflow does.
    return subprocess.run(
        [sys.executable, str(GENERATOR), "--plans-dir", plans_dir.name, *args],
        capture_output=True,
        text=True,
        cwd=plans_dir.parent,
    )


def snapshot(directory: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(directory)): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def check(condition: bool, label: str, failures: list[str]) -> None:
    if not condition:
        failures.append(label)


def fixture_files(name: str) -> tuple[dict[str, str], bool, list[str]]:
    """Return (files, expect_success, expected stderr substrings)."""
    if name == "valid-single-plan":
        return {"001-test-plan.md": plan_frontmatter()}, True, []
    if name == "valid-dependency-graph":
        return (
            {
                "001-first.md": numbered_plan(1),
                "002-second.md": numbered_plan(2, "dependencies:\n  - IMP-001"),
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
    if name == "invalid-status":
        # Statuses removed by the lifecycle collapse must be rejected loudly.
        return (
            {"001-test-plan.md": plan_frontmatter(status="status: VERIFIED")},
            False,
            ["status", "'VERIFIED'"],
        )
    if name == "short-sha":
        return (
            {"001-test-plan.md": plan_frontmatter(base_commit="base_commit: 4adde10")},
            False,
            ["base_commit", "40-character"],
        )
    if name == "invalid-lifecycle-sha":
        return (
            {
                "001-test-plan.md": plan_frontmatter(
                    issue="issue: null\nreviewed_commit: not-a-sha"
                )
            },
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
                "002-second.md": plan_frontmatter(id="id: IMP-001", title="title: Duplicate"),
            },
            False,
            ["duplicate plan id", "does not match filename prefix"],
        )
    if name == "missing-dependency":
        return (
            {"002-second.md": numbered_plan(2, "dependencies:\n  - IMP-001")},
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
    if name == "lifecycle-valid-reviewed":
        return (
            {
                "001-test-plan.md": plan_frontmatter(
                    status="status: REVIEWED",
                    issue="issue: null\n" + EXECUTION_RECORD + f"\nreviewed_commit: {OTHER_SHA}",
                )
            },
            True,
            [],
        )
    if name == "lifecycle-valid-done":
        return {"001-test-plan.md": done_plan(1)}, True, []
    if name == "lifecycle-executing-missing-record":
        return (
            {"001-test-plan.md": plan_frontmatter(status="status: EXECUTING")},
            False,
            ["execution_locator", "execution_base"],
        )
    if name == "lifecycle-reviewed-missing-commit":
        return (
            {
                "001-test-plan.md": plan_frontmatter(
                    status="status: REVIEWED", issue="issue: null\n" + EXECUTION_RECORD
                )
            },
            False,
            ["reviewed_commit", "REVIEWED requires"],
        )
    if name == "lifecycle-done-missing-merge":
        return (
            {
                "001-test-plan.md": plan_frontmatter(
                    status="status: DONE",
                    issue="issue: null\n" + EXECUTION_RECORD + f"\nreviewed_commit: {OTHER_SHA}",
                )
            },
            False,
            ["merged_commit", "verified_at", "verification_environment"],
        )
    if name == "lifecycle-blocked-without-note":
        return (
            {"001-test-plan.md": plan_frontmatter(status="status: BLOCKED")},
            False,
            ["status_note", "BLOCKED requires"],
        )
    if name == "invalid-verified-at":
        return (
            {
                "001-test-plan.md": plan_frontmatter(
                    issue="issue: null\nverified_at: yesterday"
                )
            },
            False,
            ["verified_at", "'yesterday'"],
        )
    if name == "superseded-self":
        return (
            {
                "001-test-plan.md": plan_frontmatter(
                    status="status: REJECTED",
                    issue="issue: null\nstatus_note: replaced\nsuperseded_by: IMP-001",
                )
            },
            False,
            ["cannot supersede itself"],
        )
    if name == "superseded-unresolved":
        return (
            {
                "001-test-plan.md": plan_frontmatter(
                    status="status: REJECTED",
                    issue="issue: null\nstatus_note: replaced\nsuperseded_by: IMP-009",
                )
            },
            False,
            ["superseded_by 'IMP-009' does not resolve"],
        )
    if name == "sensitive-marker":
        return (
            {"001-test-plan.md": plan_frontmatter(sensitive="sensitive: true")},
            True,
            [],
        )
    if name == "pipe-escaping":
        return (
            {"001-test-plan.md": plan_frontmatter(title="title: Fix a | b handling")},
            True,
            [],
        )
    if name == "issue-rendered":
        return (
            {
                "001-test-plan.md": plan_frontmatter(
                    issue="issue: https://github.com/example/repo/issues/7"
                )
            },
            True,
            [],
        )
    if name == "rejections-valid":
        return (
            {
                "001-test-plan.md": plan_frontmatter(),
                "rejections.json": json.dumps(
                    [
                        {
                            "id": "SEC-01",
                            "title": "https_proxy SSRF",
                            "rationale": "by-design proxy convention",
                            "evidence": ["src/net.ts:12"],
                            "recorded_at": "2026-07-19",
                        }
                    ]
                ),
            },
            True,
            [],
        )
    if name == "rejections-malformed-json":
        return (
            {"001-test-plan.md": plan_frontmatter(), "rejections.json": "[not json"},
            False,
            ["rejections.json", "not valid JSON"],
        )
    if name == "rejections-duplicate-id":
        entry: dict[str, object] = {
            "id": "SEC-01",
            "title": "t",
            "rationale": "r",
            "evidence": [],
            "recorded_at": "2026-07-19",
        }
        return (
            {
                "001-test-plan.md": plan_frontmatter(),
                "rejections.json": json.dumps([entry, dict(entry)]),
            },
            False,
            ["duplicate rejection id"],
        )
    if name == "archive-valid":
        return (
            {
                "archive/001-first.md": done_plan(1),
                "002-second.md": numbered_plan(2, "dependencies:\n  - IMP-001"),
            },
            True,
            [],
        )
    if name == "archive-nonterminal":
        return (
            {"archive/001-first.md": numbered_plan(1)},
            False,
            ["archive/001-first.md", "DONE or REJECTED"],
        )
    if name == "archive-duplicate-id":
        return (
            {
                "001-first.md": numbered_plan(1),
                "archive/001-first.md": done_plan(1),
            },
            False,
            ["duplicate plan id"],
        )
    if name == "rejections-bad-schema":
        return (
            {
                "001-test-plan.md": plan_frontmatter(),
                "rejections.json": json.dumps(
                    [{"id": "SEC-01", "title": "t", "rationale": "r"}]
                ),
            },
            False,
            ["keys must be exactly"],
        )
    raise ValueError(f"unknown fixture {name}")


# Success-case content assertions: substrings the generated index must contain.
EXTRA_INDEX_ASSERTS = {
    "valid-single-plan": ["None recorded."],
    "lifecycle-valid-reviewed": [
        "## Execution Records",
        "docs/dev/plans/.worktrees/001-test-plan",
        OTHER_SHA,
    ],
    "lifecycle-valid-done": ["DONE", "2026-07-19T12:00:00Z", "host-policy"],
    "sensitive-marker": ["(sensitive)"],
    "pipe-escaping": ["Fix a \\| b handling"],
    "issue-rendered": ["https://github.com/example/repo/issues/7"],
    "rejections-valid": [
        "## Findings Considered and Rejected",
        "[SEC-01] https_proxy SSRF: by-design proxy convention",
        "src/net.ts:12",
    ],
    "archive-valid": [
        "## Archived Plans",
        "(archive/001-first.md) (DONE)",
        "IMP-002",
    ],
}


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
    "invalid-status",
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
    "lifecycle-valid-reviewed",
    "lifecycle-valid-done",
    "lifecycle-executing-missing-record",
    "lifecycle-reviewed-missing-commit",
    "lifecycle-done-missing-merge",
    "lifecycle-blocked-without-note",
    "invalid-verified-at",
    "superseded-self",
    "superseded-unresolved",
    "sensitive-marker",
    "pipe-escaping",
    "issue-rendered",
    "rejections-valid",
    "rejections-malformed-json",
    "rejections-duplicate-id",
    "rejections-bad-schema",
    "archive-valid",
    "archive-nonterminal",
    "archive-duplicate-id",
]


def run_case(name: str) -> bool:
    files, expect_success, expected_stderr = fixture_files(name)
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / ".git").mkdir()
        plans_dir = Path(tmp) / "plans"
        plans_dir.mkdir()
        sentinel = "# SENTINEL previous index — must survive failed runs\n"
        (plans_dir / "README.md").write_text(sentinel, encoding="utf-8")
        for rel, content in files.items():
            target = plans_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        result = run_generator(plans_dir)
        ok = (result.returncode == 0) == expect_success
        index = (plans_dir / "README.md").read_text(encoding="utf-8")
        if expect_success:
            if index == sentinel:
                ok = False
                print("  index was not regenerated on success")
            for rel in files:
                if rel != "rejections.json" and rel.replace(".md", "") not in index:
                    ok = False
                    print(f"  index missing entry for {rel}")
            for expected in EXTRA_INDEX_ASSERTS.get(name, []):
                if expected not in index:
                    ok = False
                    print(f"  index missing expected content {expected!r}")
        else:
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
            (Path(tmp) / ".git").mkdir()
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


def test_check_executable() -> bool:
    """Eligibility gate: authoritative frontmatter, README-immune, read-only."""
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / ".git").mkdir()
        plans_dir = Path(tmp) / "plans"
        plans_dir.mkdir()
        (plans_dir / "001-first.md").write_text(done_plan(1), encoding="utf-8")
        (plans_dir / "002-second.md").write_text(
            numbered_plan(2, "dependencies:\n  - IMP-001"), encoding="utf-8"
        )

        # Eligible with no README at all.
        result = run_generator(plans_dir, "--check-executable", "IMP-002")
        check(result.returncode == 0, "eligible plan exits 0 without README", failures)

        # A falsified README must have no effect in either direction.
        (plans_dir / "README.md").write_text(
            "| IMP-001 | ... | BLOCKED |\n| IMP-002 | ... | DONE |\n", encoding="utf-8"
        )
        result = run_generator(plans_dir, "--check-executable", "IMP-002")
        check(result.returncode == 0, "falsified README cannot block", failures)

        before = snapshot(plans_dir)
        run_generator(plans_dir, "--check-executable", "IMP-002")
        check(snapshot(plans_dir) == before, "gate mode writes nothing", failures)

        result = run_generator(plans_dir, "--check-executable", "IMP-999")
        check(result.returncode == 2, "missing plan id exits 2", failures)

        result = run_generator(plans_dir, "--check-executable", "IMP-001")
        check(result.returncode == 3, "non-TODO selected plan exits 3", failures)

    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / ".git").mkdir()
        plans_dir = Path(tmp) / "plans"
        plans_dir.mkdir()
        (plans_dir / "001-first.md").write_text(numbered_plan(1), encoding="utf-8")
        (plans_dir / "002-second.md").write_text(
            numbered_plan(2, "dependencies:\n  - IMP-001"), encoding="utf-8"
        )
        (plans_dir / "003-third.md").write_text(
            numbered_plan(3, "dependencies:\n  - IMP-002"), encoding="utf-8"
        )
        # README claims everything is DONE; frontmatter says TODO.
        (plans_dir / "README.md").write_text(
            "| IMP-001 | DONE |\n| IMP-002 | DONE |\n", encoding="utf-8"
        )
        result = run_generator(plans_dir, "--check-executable", "IMP-003")
        check(result.returncode == 3, "transitive TODO blocks despite README", failures)
        check(
            "IMP-001" in result.stderr and "IMP-002" in result.stderr,
            "all transitive blockers are listed",
            failures,
        )

    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / ".git").mkdir()
        plans_dir = Path(tmp) / "plans"
        plans_dir.mkdir()
        (plans_dir / "001-first.md").write_text(
            plan_frontmatter(priority="priority: URGENT"), encoding="utf-8"
        )
        result = run_generator(plans_dir, "--check-executable", "IMP-001")
        check(result.returncode == 2, "invalid backlog exits 2 in gate mode", failures)

    for failure in failures:
        print(f"  {failure}")
    return not failures


def test_selected_directory_containment() -> bool:
    """The helper acts only on the explicit directory, inside the repo root."""
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".git").mkdir()
        default_dir = root / "docs" / "dev" / "plans"
        alternate = root / "docs" / "dev" / "advisor-plans"
        default_dir.mkdir(parents=True)
        alternate.mkdir(parents=True)
        # Unrelated content in the default location; a real backlog in the
        # alternate. Sentinel bytes prove the other directory is untouched.
        (default_dir / "README.md").write_text(
            "# Roadmap\n\nUnrelated planning system.\n", encoding="utf-8"
        )
        (default_dir / "notes.md").write_text("unrelated notes\n", encoding="utf-8")
        (alternate / "001-test-plan.md").write_text(plan_frontmatter(), encoding="utf-8")
        before_default = snapshot(default_dir)

        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--plans-dir", "docs/dev/advisor-plans"],
            capture_output=True,
            text=True,
            cwd=root,
        )
        check(result.returncode == 0, "generator runs on the alternate directory", failures)
        check(
            "docs/dev/advisor-plans/README.md" in result.stdout,
            "generator reports the repository-relative selected path",
            failures,
        )
        check((alternate / "README.md").exists(), "alternate index was written", failures)
        check(
            snapshot(default_dir) == before_default,
            "unrelated default directory is byte-for-byte untouched",
            failures,
        )

        # Windows-style separators at the input boundary resolve identically.
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--plans-dir", "docs\\dev\\advisor-plans"],
            capture_output=True,
            text=True,
            cwd=root,
        )
        check(result.returncode == 0, "backslash input path resolves", failures)

        # The documented repo-relative invocation works from a subdirectory.
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--plans-dir", "docs/dev/advisor-plans"],
            capture_output=True,
            text=True,
            cwd=root / "docs",
        )
        check(
            result.returncode == 0,
            "subdirectory invocation resolves against the repository root",
            failures,
        )

        # Escapes and omissions fail before any read or write.
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--plans-dir", "../outside"],
            capture_output=True,
            text=True,
            cwd=root,
        )
        check(result.returncode == 2, "traversal outside the root exits 2", failures)
        check(
            "outside the" in result.stderr and "repository root" in result.stderr,
            "escape diagnostic names the containment rule",
            failures,
        )
        result = subprocess.run(
            [sys.executable, str(GENERATOR)], capture_output=True, text=True, cwd=root
        )
        check(result.returncode == 2, "omitted --plans-dir fails with usage", failures)
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--plans-dir", "does/not/exist"],
            capture_output=True,
            text=True,
            cwd=root,
        )
        check(result.returncode == 2, "nonexistent directory exits 2", failures)

    with tempfile.TemporaryDirectory() as tmp:
        # A .git *file* (linked worktree) anchors the root the same way.
        root = Path(tmp)
        (root / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
        plans = root / "plans"
        plans.mkdir()
        (plans / "001-test-plan.md").write_text(plan_frontmatter(), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--plans-dir", "plans"],
            capture_output=True,
            text=True,
            cwd=root,
        )
        check(result.returncode == 0, ".git file (worktree) marks the root", failures)

    with tempfile.TemporaryDirectory() as tmp:
        # Outside any repository the helper refuses to run. Guarded: skip if
        # the machine's temp directory itself sits inside someone's repo.
        root = Path(tmp)
        (root / "plans").mkdir()
        if not any((p / ".git").exists() for p in (root, *root.parents)):
            result = subprocess.run(
                [sys.executable, str(GENERATOR), "--plans-dir", "plans"],
                capture_output=True,
                text=True,
                cwd=root,
            )
            check(result.returncode == 2, "no enclosing repository exits 2", failures)
            check(
                "not inside a git repository" in result.stderr,
                "no-repo diagnostic names the cause",
                failures,
            )

    for failure in failures:
        print(f"  {failure}")
    return not failures


def test_archive_lifecycle() -> bool:
    """Archived closed plans satisfy dependencies and leave the active table."""
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".git").mkdir()
        plans_dir = root / "plans"
        (plans_dir / "archive").mkdir(parents=True)
        (plans_dir / "archive" / "001-first.md").write_text(
            done_plan(1), encoding="utf-8"
        )
        (plans_dir / "002-second.md").write_text(
            numbered_plan(2, "dependencies:\n  - IMP-001"), encoding="utf-8"
        )
        result = run_generator(plans_dir)
        check(result.returncode == 0, "archive-backed backlog generates", failures)
        index = (plans_dir / "README.md").read_text(encoding="utf-8")
        check(
            not any(line.startswith("| IMP-001 ") for line in index.splitlines()),
            "archived plan is out of the active table",
            failures,
        )
        check("## Archived Plans" in index, "archived section is rendered", failures)
        result = run_generator(plans_dir, "--check-executable", "IMP-002")
        check(
            result.returncode == 0, "archived DONE dependency satisfies the gate", failures
        )

        # A rejected dependency must still block, archived or not.
        (plans_dir / "archive" / "001-first.md").write_text(
            numbered_plan(
                1,
                status="status: REJECTED",
                issue="issue: null\nstatus_note: replaced",
            ),
            encoding="utf-8",
        )
        result = run_generator(plans_dir, "--check-executable", "IMP-002")
        check(result.returncode == 3, "archived REJECTED dependency blocks", failures)
    for failure in failures:
        print(f"  {failure}")
    return not failures


def test_docs_contract() -> bool:
    """Executor-facing prose keeps the reviewer-ownership and gate contract."""
    failures: list[str] = []
    template = (
        REPO_ROOT / "skills" / "improve" / "references" / "plan-template.md"
    ).read_text(encoding="utf-8")
    closing = (
        REPO_ROOT / "skills" / "improve" / "references" / "closing-the-loop.md"
    ).read_text(encoding="utf-8")
    skill = (REPO_ROOT / "skills" / "improve" / "SKILL.md").read_text(encoding="utf-8")
    hosts = (
        REPO_ROOT / "skills" / "improve" / "references" / "host-compatibility.md"
    ).read_text(encoding="utf-8")
    playbook = (
        REPO_ROOT / "skills" / "improve" / "references" / "audit-playbook.md"
    ).read_text(encoding="utf-8")
    check(
        "STATUS, HEAD SHA, FILES CHANGED," in template,
        "template requires the five-field executor report",
        failures,
    )
    check(
        "reviewer-owned" in template and "reviewer-owned" in closing,
        "executor-facing prose declares plan records reviewer-owned",
        failures,
    )
    check(
        "--check-executable" in closing,
        "dispatch preconditions use the authoritative gate",
        failures,
    )
    for field in ("STATUS:", "HEAD SHA:", "FILES CHANGED:", "VERIFICATION RESULTS:", "NOTES:"):
        check(
            field in closing,
            f"dispatch report format carries the plan's {field.rstrip(':')} field",
            failures,
        )
    for name, text in (("SKILL.md", skill), ("closing-the-loop.md", closing)):
        check(
            "enforced sandbox" in text,
            f"{name} carries the untrusted-repo sandbox exception",
            failures,
        )
    check(
        "Enforced sandbox" in hosts,
        "capability contract lists the enforced-sandbox capability",
        failures,
    )
    for name, text in (("plan-template.md", template), ("closing-the-loop.md", closing)):
        check(
            "verification_environment" in text,
            f"{name} carries the verification_environment field",
            failures,
        )
    check(
        "canonical prefixes" in playbook
        and all(f"`{p}`" in playbook for p in ("BUG", "SEC", "PERF", "TEST", "DEBT", "DEP", "DX", "DOCS", "DIR")),
        "playbook defines the canonical finding-ID prefixes",
        failures,
    )
    for failure in failures:
        print(f"  {failure}")
    return not failures


def main() -> int:
    failures = 0
    for name in CASES:
        if run_case(name):
            print(f"PASS {name}")
        else:
            print(f"FAIL {name}")
            failures += 1
    for label, test in (
        ("deterministic-output", test_deterministic_output),
        ("check-executable", test_check_executable),
        ("selected-directory-containment", test_selected_directory_containment),
        ("archive-lifecycle", test_archive_lifecycle),
        ("docs-contract", test_docs_contract),
    ):
        if test():
            print(f"PASS {label}")
        else:
            print(f"FAIL {label}")
            failures += 1
    if failures:
        print(f"{failures} generator fixture test(s) failed")
        return 1
    print("all generator fixture tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
