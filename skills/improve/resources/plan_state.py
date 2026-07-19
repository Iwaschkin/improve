#!/usr/bin/env python3
"""Authoritative plan-state reader, validator, and execution-eligibility gate.

Single strict parser for the documented flat frontmatter subset. Both the
index generator and the execute preflight consume these functions, so
eligibility decisions and index generation can never disagree. The CLI is
read-only: `validate` checks a whole plan directory; `check-executable`
decides whether one plan may be dispatched, from validated plan files only —
the generated README is a projection for humans, never an input.

Exit codes: 0 valid/eligible, 2 invalid plan data or invocation,
3 valid backlog but the selected plan is not eligible.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, TypeAlias, cast

DEFAULT_PLANS_DIR = Path.cwd() / "docs" / "dev" / "plans"
PlanValue: TypeAlias = str | bool | list[str] | None

PLAN_FILENAME_RE = re.compile(r"^(\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
PLAN_ID_RE = re.compile(r"^IMP-(\d{3})$")
FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

STATUS_ENUM = {
    "TODO",
    "EXECUTING",
    "REVIEWED",
    "MERGED",
    "VERIFIED",
    "BLOCKED",
    "REJECTED",
    "ABANDONED",
    "SUPERSEDED",
}
PRIORITY_ENUM = {"P1", "P2", "P3"}
EFFORT_ENUM = {"S", "M", "L"}
RISK_ENUM = {"LOW", "MED", "HIGH"}
CATEGORY_ENUM = {
    "bug",
    "security",
    "perf",
    "tests",
    "tech-debt",
    "migration",
    "dx",
    "docs",
    "direction",
}

PROFILE_ENUM = {"trusted-local", "strict", "manual"}
VERIFICATION_ENUM = {
    "restricted-sandbox",
    "host-approval-policy",
    "user-confirmed-normal-account",
    "not-run",
    "unknown",
}

REQUIRED_FIELDS = (
    "id",
    "title",
    "status",
    "priority",
    "effort",
    "risk",
    "category",
    "base_commit",
    "working_tree_clean",
    "created_at",
    "updated_at",
    "scope",
    "dependencies",
    "execution_branch",
    "execution_base",
    "reviewed_commit",
    "merged_commit",
    "sensitive",
    "issue",
)

# Lifecycle fields introduced after the base schema; optional (absent == null)
# so older plans stay valid, but validated whenever present.
OPTIONAL_NULLABLE_STRINGS = ("execution_locator", "status_note", "skill_version")

REJECTION_KEYS = {"id", "title", "rationale", "evidence", "recorded_at"}


@dataclass
class Diagnostic:
    """One actionable validation error."""

    file: str
    reason: str
    line: int | None = None
    field: str | None = None

    def render(self) -> str:
        location = f"{self.file}:{self.line}" if self.line else self.file
        prefix = f"{location}: {self.field}: " if self.field else f"{location}: "
        return f"ERROR {prefix}{self.reason}"


def split_frontmatter(text: str, file: str, errors: list[Diagnostic]) -> list[str] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        errors.append(Diagnostic(file, "file does not begin with '---' frontmatter", line=1))
        return None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:index]
    errors.append(Diagnostic(file, "frontmatter has no closing '---' delimiter", line=1))
    return None


def parse_value(raw: str) -> PlanValue:
    value = raw.strip()
    if value in {"", "null", "~"}:
        return None
    if value == "[]":
        return []
    if value in {"true", "false"}:
        return value == "true"
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_frontmatter(
    lines: list[str], file: str, errors: list[Diagnostic]
) -> dict[str, PlanValue]:
    data: dict[str, PlanValue] = {}
    current_list: str | None = None
    for line_number, raw_line in enumerate(lines, start=2):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.startswith((" ", "\t")):
            if current_list is not None and raw_line.startswith("  - "):
                item = raw_line.strip()[2:].strip()
                items = cast(list[str], data[current_list])
                items.append(item)
                continue
            errors.append(
                Diagnostic(
                    file,
                    f"unexpected indented line {raw_line.strip()!r}; only '  - item' "
                    "entries under a list key are supported",
                    line=line_number,
                )
            )
            continue
        current_list = None
        if ":" not in raw_line:
            errors.append(
                Diagnostic(
                    file,
                    f"malformed line {raw_line.strip()!r}; expected 'key: value'",
                    line=line_number,
                )
            )
            continue
        key, raw_value = raw_line.split(":", 1)
        key = key.strip()
        if key in data:
            errors.append(
                Diagnostic(file, "duplicate key", line=line_number, field=key)
            )
            continue
        value = parse_value(raw_value)
        if value is None and raw_value.strip() == "":
            data[key] = []
            current_list = key
        else:
            data[key] = value
    return data


def _is_nonempty_str(value: PlanValue) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _check_enum(
    data: dict[str, PlanValue],
    field: str,
    allowed: set[str],
    file: str,
    errors: list[Diagnostic],
) -> None:
    value = data.get(field)
    if not isinstance(value, str) or value not in allowed:
        errors.append(
            Diagnostic(
                file,
                f"expected one of {sorted(allowed)}, got {value!r}",
                field=field,
            )
        )


def _check_bool(
    data: dict[str, PlanValue], field: str, file: str, errors: list[Diagnostic]
) -> None:
    if not isinstance(data.get(field), bool):
        errors.append(
            Diagnostic(
                file,
                f"expected an unquoted boolean (true/false), got {data.get(field)!r}",
                field=field,
            )
        )


def _check_date(
    data: dict[str, PlanValue], field: str, file: str, errors: list[Diagnostic]
) -> date | None:
    value = data.get(field)
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        errors.append(
            Diagnostic(file, f"expected YYYY-MM-DD date, got {value!r}", field=field)
        )
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(
            Diagnostic(file, f"not a real calendar date: {value!r}", field=field)
        )
        return None


def _check_nullable_sha(
    data: dict[str, PlanValue], field: str, file: str, errors: list[Diagnostic]
) -> None:
    value = data.get(field)
    if value is None:
        return
    if not isinstance(value, str) or not FULL_SHA_RE.fullmatch(value):
        errors.append(
            Diagnostic(
                file,
                f"expected null or a full 40-character lowercase hex SHA, got {value!r}",
                field=field,
            )
        )


def validate_plan(
    data: dict[str, PlanValue], filename: str, errors: list[Diagnostic]
) -> None:
    """Validate one plan's fields against the published template schema."""
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(Diagnostic(filename, "required field is missing", field=field))
    if any(e.file == filename and e.reason == "required field is missing" for e in errors):
        return

    filename_match = PLAN_FILENAME_RE.fullmatch(filename)
    if not filename_match:
        errors.append(
            Diagnostic(
                filename,
                "filename must match 'NNN-lowercase-hyphen-slug.md'",
            )
        )

    plan_id = data.get("id")
    id_match = PLAN_ID_RE.fullmatch(plan_id) if isinstance(plan_id, str) else None
    if not id_match:
        errors.append(
            Diagnostic(filename, f"expected 'IMP-NNN', got {plan_id!r}", field="id")
        )
    elif filename_match and id_match.group(1) != filename_match.group(1):
        errors.append(
            Diagnostic(
                filename,
                f"id number {id_match.group(1)} does not match filename prefix "
                f"{filename_match.group(1)}",
                field="id",
            )
        )

    if not _is_nonempty_str(data.get("title")):
        errors.append(Diagnostic(filename, "expected a nonempty string", field="title"))

    _check_enum(data, "status", STATUS_ENUM, filename, errors)
    _check_enum(data, "priority", PRIORITY_ENUM, filename, errors)
    _check_enum(data, "effort", EFFORT_ENUM, filename, errors)
    _check_enum(data, "risk", RISK_ENUM, filename, errors)
    _check_enum(data, "category", CATEGORY_ENUM, filename, errors)

    base_commit = data.get("base_commit")
    if not isinstance(base_commit, str) or not FULL_SHA_RE.fullmatch(base_commit):
        errors.append(
            Diagnostic(
                filename,
                f"expected a full 40-character lowercase hex SHA, got {base_commit!r}",
                field="base_commit",
            )
        )

    _check_bool(data, "working_tree_clean", filename, errors)
    _check_bool(data, "sensitive", filename, errors)

    created = _check_date(data, "created_at", filename, errors)
    updated = _check_date(data, "updated_at", filename, errors)
    if created and updated and updated < created:
        errors.append(
            Diagnostic(
                filename,
                f"updated_at {updated} is earlier than created_at {created}",
                field="updated_at",
            )
        )

    scope = data.get("scope")
    if not isinstance(scope, list) or not scope:
        errors.append(
            Diagnostic(filename, "expected a nonempty list of paths", field="scope")
        )
    else:
        for item in scope:
            if not _is_nonempty_str(item):
                errors.append(
                    Diagnostic(
                        filename, f"scope entries must be nonempty strings, got {item!r}",
                        field="scope",
                    )
                )

    dependencies = data.get("dependencies")
    if not isinstance(dependencies, list):
        errors.append(
            Diagnostic(
                filename,
                f"expected a list (use [] for none), got {dependencies!r}",
                field="dependencies",
            )
        )
    else:
        for item in dependencies:
            if not PLAN_ID_RE.fullmatch(item):
                errors.append(
                    Diagnostic(
                        filename,
                        f"dependency entries must be plan IDs 'IMP-NNN', got {item!r}",
                        field="dependencies",
                    )
                )

    execution_branch = data.get("execution_branch")
    if execution_branch is not None and not _is_nonempty_str(execution_branch):
        errors.append(
            Diagnostic(
                filename,
                f"expected null or a nonempty string, got {execution_branch!r}",
                field="execution_branch",
            )
        )
    _check_nullable_sha(data, "execution_base", filename, errors)
    _check_nullable_sha(data, "reviewed_commit", filename, errors)
    _check_nullable_sha(data, "merged_commit", filename, errors)

    issue = data.get("issue")
    if issue is not None and not _is_nonempty_str(issue):
        errors.append(
            Diagnostic(
                filename, f"expected null or a nonempty string, got {issue!r}",
                field="issue",
            )
        )

    for field in OPTIONAL_NULLABLE_STRINGS:
        value = data.get(field)
        if value is not None and not _is_nonempty_str(value):
            errors.append(
                Diagnostic(
                    filename, f"expected null or a nonempty string, got {value!r}",
                    field=field,
                )
            )
    profile = data.get("execution_profile")
    if profile is not None and (
        not isinstance(profile, str) or profile not in PROFILE_ENUM
    ):
        errors.append(
            Diagnostic(
                filename,
                f"expected null or one of {sorted(PROFILE_ENUM)}, got {profile!r}",
                field="execution_profile",
            )
        )
    _check_nullable_sha(data, "executor_head", filename, errors)
    verification = data.get("verification_environment")
    if verification is not None and (
        not isinstance(verification, str) or verification not in VERIFICATION_ENUM
    ):
        errors.append(
            Diagnostic(
                filename,
                f"expected null or one of {sorted(VERIFICATION_ENUM)}, got {verification!r}",
                field="verification_environment",
            )
        )

    validate_lifecycle(data, filename, errors)


def validate_lifecycle(
    data: dict[str, PlanValue], filename: str, errors: list[Diagnostic]
) -> None:
    """Cross-field invariants keyed on status; impossible states fail closed."""
    status = data.get("status")
    if not isinstance(status, str) or status not in STATUS_ENUM:
        return  # already reported by the enum check

    def require(field: str, reason: str) -> None:
        if data.get(field) in (None, "", []):
            errors.append(Diagnostic(filename, reason, field=field))

    executing_or_later = status in {"EXECUTING", "REVIEWED", "MERGED", "VERIFIED"}
    if executing_or_later and data.get("status_note") is None:
        # A status_note may explain a legacy/manual exception to the
        # execution-provenance requirements.
        require("execution_locator", f"status {status} requires an execution locator")
        require("execution_base", f"status {status} requires the execution base SHA")
        require("execution_profile", f"status {status} requires the execution profile")
    if status in {"REVIEWED", "MERGED", "VERIFIED"}:
        require("executor_head", f"status {status} requires the executor head SHA")
        require("reviewed_commit", f"status {status} requires the reviewed commit")
    if status in {"MERGED", "VERIFIED"}:
        require("merged_commit", f"status {status} requires the merged commit")
    if status in {"BLOCKED", "REJECTED", "ABANDONED", "SUPERSEDED"}:
        require("status_note", f"status {status} requires a one-line status_note rationale")
    if status == "VERIFIED" and data.get("verification_environment") in (
        None,
        "not-run",
        "unknown",
    ):
        errors.append(
            Diagnostic(
                filename,
                "VERIFIED requires a verification_environment that actually ran",
                field="verification_environment",
            )
        )


def load_rejections(
    plans_dir: Path, errors: list[Diagnostic]
) -> list[dict[str, Any]]:
    """Load and validate the optional rejections.json finding record."""
    path = plans_dir / "rejections.json"
    if not path.exists():
        return []
    filename = path.name
    try:
        raw: Any = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(Diagnostic(filename, f"not valid JSON: {exc}"))
        return []
    if not isinstance(raw, list):
        errors.append(Diagnostic(filename, "top level must be a JSON array"))
        return []
    entries: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(cast(list[Any], raw)):
        where = f"entry {index}"
        if not isinstance(item, dict):
            errors.append(Diagnostic(filename, f"{where}: must be an object"))
            continue
        entry = cast(dict[str, Any], item)
        keys = set(entry.keys())
        if keys != REJECTION_KEYS:
            errors.append(
                Diagnostic(
                    filename,
                    f"{where}: keys must be exactly {sorted(REJECTION_KEYS)}, got {sorted(keys)}",
                )
            )
            continue
        entry_id = entry.get("id")
        for key in ("id", "title", "rationale"):
            value = entry.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(
                    Diagnostic(filename, f"{where}: {key} must be a nonempty string")
                )
        evidence = entry.get("evidence")
        if not isinstance(evidence, list) or any(
            not isinstance(ref, str) or not ref.strip()
            for ref in cast(list[Any], evidence)
        ):
            errors.append(
                Diagnostic(
                    filename,
                    f"{where}: evidence must be a list of nonempty strings (may be empty)",
                )
            )
        recorded_at = entry.get("recorded_at")
        if not isinstance(recorded_at, str) or not DATE_RE.fullmatch(recorded_at):
            errors.append(
                Diagnostic(filename, f"{where}: recorded_at must be YYYY-MM-DD")
            )
        if isinstance(entry_id, str):
            if entry_id in seen_ids:
                errors.append(
                    Diagnostic(filename, f"{where}: duplicate rejection id {entry_id!r}")
                )
            seen_ids.add(entry_id)
        entries.append(entry)
    return entries


def validate_graph(
    rows: list[dict[str, PlanValue]], errors: list[Diagnostic]
) -> None:
    """Validate cross-plan rules: uniqueness, dependency resolution, order."""
    by_id: dict[str, dict[str, PlanValue]] = {}
    for row in rows:
        plan_id = row.get("id")
        if not isinstance(plan_id, str):
            continue
        if plan_id in by_id:
            errors.append(
                Diagnostic(
                    str(row.get("file")),
                    f"duplicate plan id {plan_id!r} (also in {by_id[plan_id].get('file')})",
                    field="id",
                )
            )
            continue
        by_id[plan_id] = row

    for row in rows:
        plan_id = row.get("id")
        filename = str(row.get("file"))
        dependencies = row.get("dependencies")
        if not isinstance(plan_id, str) or not isinstance(dependencies, list):
            continue
        id_match = PLAN_ID_RE.fullmatch(plan_id)
        for dep in dependencies:
            if not PLAN_ID_RE.fullmatch(dep):
                continue
            if dep == plan_id:
                errors.append(
                    Diagnostic(filename, "plan depends on itself", field="dependencies")
                )
                continue
            if dep not in by_id:
                errors.append(
                    Diagnostic(
                        filename,
                        f"dependency {dep!r} does not resolve to any plan",
                        field="dependencies",
                    )
                )
                continue
            dep_match = PLAN_ID_RE.fullmatch(dep)
            if id_match and dep_match and int(dep_match.group(1)) >= int(id_match.group(1)):
                errors.append(
                    Diagnostic(
                        filename,
                        f"dependency {dep!r} is not numbered earlier than {plan_id!r}; "
                        "filename order must be a valid execution order",
                        field="dependencies",
                    )
                )

    # Cycle detection. With the earlier-number rule enforced above a cycle is
    # impossible, but the rule may itself be violated, so detect cycles
    # independently to report them as such.
    visiting: set[str] = set()
    done: set[str] = set()

    def visit(plan_id: str, filename: str) -> None:
        if plan_id in done:
            return
        if plan_id in visiting:
            errors.append(
                Diagnostic(filename, f"dependency cycle involving {plan_id!r}", field="dependencies")
            )
            return
        visiting.add(plan_id)
        row = by_id.get(plan_id)
        deps = row.get("dependencies") if row else None
        if isinstance(deps, list):
            for dep in deps:
                if dep in by_id:
                    visit(dep, filename)
        visiting.discard(plan_id)
        done.add(plan_id)

    for row in rows:
        plan_id = row.get("id")
        if isinstance(plan_id, str) and plan_id in by_id:
            visit(plan_id, str(row.get("file")))


def collect_plans(
    plans_dir: Path,
) -> tuple[list[dict[str, PlanValue]], list[Diagnostic]]:
    rows: list[dict[str, PlanValue]] = []
    errors: list[Diagnostic] = []
    if not plans_dir.exists():
        return rows, errors
    for path in sorted(plans_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        frontmatter = split_frontmatter(text, path.name, errors)
        if frontmatter is None:
            continue
        data = parse_frontmatter(frontmatter, path.name, errors)
        validate_plan(data, path.name, errors)
        data["file"] = path.name
        rows.append(data)
    validate_graph(rows, errors)
    return rows, errors




def transitive_dependencies(
    plan_id: str, by_id: dict[str, dict[str, PlanValue]]
) -> list[str]:
    """All direct and transitive dependency IDs, deterministic order."""
    seen: list[str] = []
    stack = [plan_id]
    visited: set[str] = set()
    while stack:
        current = stack.pop()
        row = by_id.get(current)
        deps = row.get("dependencies") if row else None
        if not isinstance(deps, list):
            continue
        for dep in sorted(deps):
            if dep not in visited:
                visited.add(dep)
                seen.append(dep)
                stack.append(dep)
    return sorted(seen)


def check_executable(
    rows: list[dict[str, PlanValue]], plan_id: str
) -> tuple[int, list[str]]:
    """Decide eligibility for one plan from validated rows only."""
    by_id = {
        str(row.get("id")): row for row in rows if isinstance(row.get("id"), str)
    }
    if plan_id not in by_id:
        return 2, [f"plan {plan_id!r} does not exist in the selected plans directory"]
    messages: list[str] = []
    plan = by_id[plan_id]
    status = plan.get("status")
    if status != "TODO":
        messages.append(
            f"{plan_id} has status {status}; only TODO plans are dispatchable"
        )
    blockers = [
        (dep, str(by_id[dep].get("status")))
        for dep in transitive_dependencies(plan_id, by_id)
        if dep in by_id and by_id[dep].get("status") != "VERIFIED"
    ]
    for dep, dep_status in blockers:
        messages.append(f"dependency {dep} is {dep_status}, not VERIFIED")
    if messages:
        return 3, messages
    return 0, [f"{plan_id} is eligible: TODO with all dependencies VERIFIED"]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate plan frontmatter and gate execution eligibility"
    )
    parser.add_argument("--plans-dir", required=True, help="selected plans directory")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate the whole plan directory")
    check = subparsers.add_parser(
        "check-executable", help="check whether one plan may be dispatched"
    )
    check.add_argument("plan_id", help="plan ID, e.g. IMP-003")
    args = parser.parse_args()

    plans_dir = Path(args.plans_dir)
    if not plans_dir.is_dir():
        print(f"ERROR plans directory not found: {plans_dir}", file=sys.stderr)
        return 2
    rows, errors = collect_plans(plans_dir)
    load_rejections(plans_dir, errors)
    if errors:
        for error in errors:
            print(error.render(), file=sys.stderr)
        print(f"{len(errors)} validation error(s)", file=sys.stderr)
        return 2

    if args.command == "validate":
        print(f"valid: {len(rows)} plan(s) in {plans_dir}")
        return 0

    code, messages = check_executable(rows, args.plan_id)
    stream = sys.stdout if code == 0 else sys.stderr
    for message in messages:
        print(message, file=stream)
    return code


if __name__ == "__main__":
    sys.exit(main())
