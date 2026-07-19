#!/usr/bin/env python3
"""Generate docs/dev/plans/README.md from plan frontmatter.

Parses a documented flat subset of YAML frontmatter (scalars and one-level
``- item`` lists), validates every plan against the schema published in
references/plan-template.md, and regenerates the index only when the whole
plan directory is valid. Invalid input exits nonzero and leaves any existing
index untouched; successful runs replace the index atomically.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import TypeAlias, cast

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


def cell(value: PlanValue) -> str:
    if value in (None, "", []):
        return "-"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "-"
    return str(value)


def render_index(rows: list[dict[str, PlanValue]]) -> str:
    lines = [
        "# Implementation Plans",
        "",
        "Generated from plan frontmatter. Do not hand-edit this table; update the plan file and rerun the bundled `resources/generate_plan_index.py` helper.",
        "",
        "## Execution Order & Status",
        "",
        "| Plan | Title | Priority | Effort | Depends on | Status | Execution base | Reviewed commit | Merged commit |",
        "| ---- | ----- | -------- | ------ | ---------- | ------ | -------------- | --------------- | ------------- |",
    ]
    for row in rows:
        plan_id = cell(row.get("id"))
        title = cell(row.get("title"))
        filename = cell(row.get("file"))
        if filename != "-":
            title = f"[{title}]({filename})"
        lines.append(
            "| "
            + " | ".join(
                [
                    plan_id,
                    title,
                    cell(row.get("priority")),
                    cell(row.get("effort")),
                    cell(row.get("dependencies")),
                    cell(row.get("status")),
                    cell(row.get("execution_base")),
                    cell(row.get("reviewed_commit")),
                    cell(row.get("merged_commit")),
                ]
            )
            + " |"
        )
    if not rows:
        lines.append("| - | No plans yet | - | - | - | - | - | - | - |")
    lines.extend(
        [
            "",
            "Status values: TODO | EXECUTING | REVIEWED | MERGED | VERIFIED | BLOCKED | REJECTED | ABANDONED | SUPERSEDED",
            "",
        ]
    )
    return "\n".join(lines)


def write_index_atomically(index_path: Path, content: str) -> None:
    handle = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        dir=index_path.parent,
        prefix=".index-",
        suffix=".tmp",
        delete=False,
    )
    try:
        with handle:
            handle.write(content)
        os.replace(handle.name, index_path)
    except BaseException:
        Path(handle.name).unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate docs/dev/plans/README.md")
    parser.add_argument(
        "--plans-dir", default=str(DEFAULT_PLANS_DIR), help="plan directory"
    )
    args = parser.parse_args()
    plans_dir = Path(args.plans_dir)
    plans_dir.mkdir(parents=True, exist_ok=True)

    rows, errors = collect_plans(plans_dir)
    if errors:
        for error in errors:
            print(error.render(), file=sys.stderr)
        print(
            f"{len(errors)} error(s); index not written, previous index preserved",
            file=sys.stderr,
        )
        return 1

    index_path = plans_dir / "README.md"
    write_index_atomically(index_path, render_index(rows))
    print(f"wrote {index_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
