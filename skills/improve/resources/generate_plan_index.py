#!/usr/bin/env python3
"""Plan-backlog helper: validate frontmatter, generate the index, gate execution.

One strict parser for the documented flat frontmatter subset serves both
jobs, so eligibility decisions and index generation can never disagree.

Default invocation (`--plans-dir <dir>`) validates every plan and writes the
directory's README.md index atomically — invalid input exits nonzero and
preserves the previous index. With `--check-executable IMP-NNN` the helper
instead decides, read-only, whether that plan may be dispatched: the plan
files are authoritative; the generated README is never an input.

The selected directory is resolved against the repository root — the nearest
ancestor of the working directory containing `.git` — and the helper refuses
to run outside a repository or on paths escaping it. Closed plans (status
DONE or REJECTED) may live in an `archive/` subdirectory: they are validated
like any plan, still resolve dependency and supersede references, and render
in a compact archived section instead of the main table.

Exit codes: 0 success/eligible, 1 invalid plan data (generate), 2 invalid
invocation or plan data (gate), 3 valid backlog but the plan is not eligible.
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

PlanValue: TypeAlias = str | bool | list[str] | None

PLAN_FILENAME_RE = re.compile(r"^(\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
PLAN_ID_RE = re.compile(r"^IMP-(\d{3})$")
FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

STATUS_ENUM = {"TODO", "EXECUTING", "REVIEWED", "DONE", "BLOCKED", "REJECTED"}
ARCHIVABLE_STATUSES = {"DONE", "REJECTED"}
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
    "created_at",
    "updated_at",
    "scope",
    "dependencies",
    "sensitive",
    "issue",
)

# Execution-record fields; optional (absent == null), validated when present.
OPTIONAL_SHAS = ("execution_base", "reviewed_commit", "merged_commit")
OPTIONAL_STRINGS = ("execution_locator", "status_note", "issue")

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
                items = cast(list[str], data[current_list])
                items.append(raw_line.strip()[2:].strip())
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
            errors.append(Diagnostic(file, "duplicate key", line=line_number, field=key))
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
            Diagnostic(file, f"expected one of {sorted(allowed)}, got {value!r}", field=field)
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
        errors.append(Diagnostic(file, f"not a real calendar date: {value!r}", field=field))
        return None


def validate_plan(
    data: dict[str, PlanValue], filename: str, errors: list[Diagnostic]
) -> None:
    """Validate one plan's fields against the published template schema."""
    missing = [field for field in REQUIRED_FIELDS if field not in data]
    for field in missing:
        errors.append(Diagnostic(filename, "required field is missing", field=field))
    if missing:
        return

    filename_match = PLAN_FILENAME_RE.fullmatch(filename.rsplit("/", 1)[-1])
    if not filename_match:
        errors.append(
            Diagnostic(filename, "filename must match 'NNN-lowercase-hyphen-slug.md'")
        )

    plan_id = data.get("id")
    id_match = PLAN_ID_RE.fullmatch(plan_id) if isinstance(plan_id, str) else None
    if not id_match:
        errors.append(Diagnostic(filename, f"expected 'IMP-NNN', got {plan_id!r}", field="id"))
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

    if not isinstance(data.get("sensitive"), bool):
        errors.append(
            Diagnostic(
                filename,
                f"expected an unquoted boolean (true/false), got {data.get('sensitive')!r}",
                field="sensitive",
            )
        )

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
    if not isinstance(scope, list) or not scope or not all(
        _is_nonempty_str(item) for item in scope
    ):
        errors.append(
            Diagnostic(filename, "expected a nonempty list of paths", field="scope")
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

    for field in OPTIONAL_SHAS:
        value = data.get(field)
        if value is not None and (
            not isinstance(value, str) or not FULL_SHA_RE.fullmatch(value)
        ):
            errors.append(
                Diagnostic(
                    filename,
                    f"expected null or a full 40-character lowercase hex SHA, got {value!r}",
                    field=field,
                )
            )
    for field in OPTIONAL_STRINGS:
        value = data.get(field)
        if value is not None and not _is_nonempty_str(value):
            errors.append(
                Diagnostic(
                    filename, f"expected null or a nonempty string, got {value!r}", field=field
                )
            )
    verified_at = data.get("verified_at")
    if verified_at is not None and (
        not isinstance(verified_at, str) or not TIMESTAMP_RE.fullmatch(verified_at)
    ):
        errors.append(
            Diagnostic(
                filename,
                f"expected null or a UTC timestamp YYYY-MM-DDTHH:MM:SSZ, got {verified_at!r}",
                field="verified_at",
            )
        )
    superseded_by = data.get("superseded_by")
    if superseded_by is not None:
        if not isinstance(superseded_by, str) or not PLAN_ID_RE.fullmatch(superseded_by):
            errors.append(
                Diagnostic(
                    filename,
                    f"expected null or a plan ID 'IMP-NNN', got {superseded_by!r}",
                    field="superseded_by",
                )
            )
        elif superseded_by == data.get("id"):
            errors.append(
                Diagnostic(filename, "a plan cannot supersede itself", field="superseded_by")
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

    if status in {"EXECUTING", "REVIEWED", "DONE"}:
        require("execution_locator", f"status {status} requires an execution locator")
        require("execution_base", f"status {status} requires the execution base SHA")
    if status in {"REVIEWED", "DONE"}:
        require("reviewed_commit", f"status {status} requires the reviewed commit")
    if status == "DONE":
        require(
            "merged_commit",
            "status DONE requires the merged commit — the actual target-branch "
            "commit at which the reviewed change is integrated",
        )
        require("verified_at", "status DONE requires the verified_at timestamp")
    if status in {"BLOCKED", "REJECTED"}:
        require("status_note", f"status {status} requires a one-line status_note rationale")


def load_rejections(plans_dir: Path, errors: list[Diagnostic]) -> list[dict[str, Any]]:
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
        if set(entry.keys()) != REJECTION_KEYS:
            errors.append(
                Diagnostic(
                    filename,
                    f"{where}: keys must be exactly {sorted(REJECTION_KEYS)}, "
                    f"got {sorted(entry.keys())}",
                )
            )
            continue
        for key in ("id", "title", "rationale"):
            if not _is_nonempty_str(entry.get(key)):
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
            errors.append(Diagnostic(filename, f"{where}: recorded_at must be YYYY-MM-DD"))
        entry_id = entry.get("id")
        if isinstance(entry_id, str):
            if entry_id in seen_ids:
                errors.append(
                    Diagnostic(filename, f"{where}: duplicate rejection id {entry_id!r}")
                )
            seen_ids.add(entry_id)
        entries.append(entry)
    return entries


def validate_graph(rows: list[dict[str, PlanValue]], errors: list[Diagnostic]) -> None:
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
        filename = str(row.get("file"))
        superseded_by = row.get("superseded_by")
        if isinstance(superseded_by, str) and superseded_by not in by_id:
            errors.append(
                Diagnostic(
                    filename,
                    f"superseded_by {superseded_by!r} does not resolve to any plan",
                    field="superseded_by",
                )
            )
        plan_id = row.get("id")
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
                Diagnostic(
                    filename, f"dependency cycle involving {plan_id!r}", field="dependencies"
                )
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


def collect_plans(plans_dir: Path) -> tuple[list[dict[str, PlanValue]], list[Diagnostic]]:
    rows: list[dict[str, PlanValue]] = []
    errors: list[Diagnostic] = []

    def read_plan(path: Path, display: str, archived: bool) -> None:
        text = path.read_text(encoding="utf-8")
        frontmatter = split_frontmatter(text, display, errors)
        if frontmatter is None:
            return
        data = parse_frontmatter(frontmatter, display, errors)
        validate_plan(data, display, errors)
        if archived and data.get("status") in STATUS_ENUM - ARCHIVABLE_STATUSES:
            errors.append(
                Diagnostic(
                    display,
                    "archived plans must be closed — status DONE or REJECTED",
                    field="status",
                )
            )
        data["file"] = display
        data["archived"] = archived
        rows.append(data)

    for path in sorted(plans_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        read_plan(path, path.name, archived=False)
    archive_dir = plans_dir / "archive"
    if archive_dir.is_dir():
        for path in sorted(archive_dir.glob("*.md")):
            if path.name == "README.md":
                continue
            read_plan(path, f"archive/{path.name}", archived=True)
    validate_graph(rows, errors)
    return rows, errors


def find_repository_root(start: Path) -> Path | None:
    """Nearest ancestor (including start) containing `.git` — dir or file.

    A `.git` file marks a linked git worktree; both forms anchor the root.
    """
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def resolve_plans_dir(supplied: str, root: Path) -> tuple[Path | None, str | None]:
    """Resolve the selected plans directory inside the repository root.

    Selection policy (default vs `advisor-plans`, ambiguity handling) belongs
    to the skill workflow; the helper only validates an explicitly supplied
    directory — relative arguments resolve against the repository root, so
    the documented invocation works from any subdirectory — and refuses to
    operate outside that root. Windows-style separators are normalized at
    this input boundary so the same repository-relative argument works
    identically on every platform.
    """
    raw = Path(supplied.replace("\\", "/"))
    resolved = (raw if raw.is_absolute() else root / raw).resolve()
    if not resolved.is_relative_to(root):
        return None, (
            f"selected plans directory {supplied!r} resolves outside the "
            f"repository root {root}"
        )
    if not resolved.is_dir():
        return None, f"selected plans directory not found: {supplied}"
    return resolved, None


def plans_dir_display(plans_dir: Path, root: Path) -> str:
    """Repository-relative forward-slash form for reports and logs."""
    try:
        return plans_dir.resolve().relative_to(root).as_posix()
    except ValueError:
        return plans_dir.as_posix()


def transitive_dependencies(
    plan_id: str, by_id: dict[str, dict[str, PlanValue]]
) -> list[str]:
    """All direct and transitive dependency IDs, deterministic order."""
    seen: set[str] = set()
    stack = [plan_id]
    while stack:
        row = by_id.get(stack.pop())
        deps = row.get("dependencies") if row else None
        if not isinstance(deps, list):
            continue
        for dep in deps:
            if dep not in seen:
                seen.add(dep)
                stack.append(dep)
    return sorted(seen)


def check_executable(rows: list[dict[str, PlanValue]], plan_id: str) -> tuple[int, list[str]]:
    """Decide eligibility for one plan from validated rows only."""
    by_id = {str(row.get("id")): row for row in rows if isinstance(row.get("id"), str)}
    if plan_id not in by_id:
        return 2, [f"plan {plan_id!r} does not exist in the selected plans directory"]
    messages: list[str] = []
    if by_id[plan_id].get("status") != "TODO":
        messages.append(
            f"{plan_id} has status {by_id[plan_id].get('status')}; "
            "only TODO plans are dispatchable"
        )
    for dep in transitive_dependencies(plan_id, by_id):
        if dep in by_id and by_id[dep].get("status") != "DONE":
            messages.append(f"dependency {dep} is {by_id[dep].get('status')}, not DONE")
    if messages:
        return 3, messages
    return 0, [f"{plan_id} is eligible: TODO with all dependencies DONE"]


def escape_cell(text: str) -> str:
    """Keep arbitrary scalar content from corrupting the Markdown table."""
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def cell(value: PlanValue) -> str:
    if value in (None, "", []):
        return "-"
    if isinstance(value, list):
        return escape_cell(", ".join(str(item) for item in value))
    return escape_cell(str(value))


def linked_title(row: dict[str, PlanValue]) -> str:
    """Title cell: sensitive marker appended, linked to the plan file."""
    title = cell(row.get("title"))
    if row.get("sensitive") is True:
        title = f"{title} (sensitive)"
    filename = cell(row.get("file"))
    if filename != "-":
        title = f"[{title}]({filename})"
    return title


EXECUTION_RECORD_FIELDS = (
    ("execution_locator", "locator"),
    ("execution_base", "base"),
    ("reviewed_commit", "reviewed"),
    ("merged_commit", "merged"),
    ("verified_at", "verified"),
    ("superseded_by", "superseded by"),
)


def render_index(rows: list[dict[str, PlanValue]], rejections: list[dict[str, Any]]) -> str:
    active = [row for row in rows if row.get("archived") is not True]
    archived = [row for row in rows if row.get("archived") is True]
    lines = [
        "# Implementation Plans",
        "",
        "Generated from plan frontmatter. Do not hand-edit this table; update the plan file and rerun the bundled `resources/generate_plan_index.py` helper.",
        "",
        "## Execution Order & Status",
        "",
        "| Plan | Title | Priority | Effort | Depends on | Status | Status note | Issue |",
        "| ---- | ----- | -------- | ------ | ---------- | ------ | ----------- | ----- |",
    ]
    for row in active:
        title = linked_title(row)
        lines.append(
            "| "
            + " | ".join(
                [
                    cell(row.get("id")),
                    title,
                    cell(row.get("priority")),
                    cell(row.get("effort")),
                    cell(row.get("dependencies")),
                    cell(row.get("status")),
                    cell(row.get("status_note")),
                    cell(row.get("issue")),
                ]
            )
            + " |"
        )
    if not active:
        lines.append("| - | No plans yet | - | - | - | - | - | - |")
    lines.extend(
        ["", "Status values: TODO | EXECUTING | REVIEWED | DONE | BLOCKED | REJECTED"]
    )

    records = [
        (row, parts)
        for row in active
        if (
            parts := [
                f"{label}: `{cell(row.get(field))}`"
                for field, label in EXECUTION_RECORD_FIELDS
                if row.get(field) not in (None, "", [])
            ]
        )
    ]
    if records:
        lines.extend(["", "## Execution Records", ""])
        for row, parts in records:
            lines.append(f"- **{cell(row.get('id'))}** — " + ", ".join(parts))

    if archived:
        lines.extend(["", "## Archived Plans", ""])
        for row in archived:
            lines.append(
                f"- **{cell(row.get('id'))}** — {linked_title(row)} "
                f"({cell(row.get('status'))})"
            )

    lines.extend(["", "## Findings Considered and Rejected", ""])
    if rejections:
        for entry in rejections:
            evidence_list = cast(list[Any], entry.get("evidence") or [])
            evidence = ", ".join(str(ref) for ref in evidence_list)
            suffix = f" (evidence: {escape_cell(evidence)})" if evidence else ""
            lines.append(
                f"- [{escape_cell(str(entry.get('id')))}] "
                f"{escape_cell(str(entry.get('title')))}: "
                f"{escape_cell(str(entry.get('rationale')))} "
                f"(recorded {entry.get('recorded_at')}){suffix}"
            )
    else:
        lines.append("None recorded.")
    lines.append("")
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
    parser = argparse.ArgumentParser(
        description="Validate plan frontmatter, generate the index, or gate execution"
    )
    parser.add_argument("--plans-dir", required=True, help="selected plans directory")
    parser.add_argument(
        "--check-executable",
        metavar="IMP-NNN",
        help="instead of writing the index, check whether this plan may be dispatched",
    )
    args = parser.parse_args()

    root = find_repository_root(Path.cwd().resolve())
    if root is None:
        print(
            "ERROR working directory is not inside a git repository; the "
            "selected plans directory is repository-relative",
            file=sys.stderr,
        )
        return 2
    plans_dir, problem = resolve_plans_dir(args.plans_dir, root)
    if plans_dir is None:
        print(f"ERROR {problem}", file=sys.stderr)
        return 2

    rows, errors = collect_plans(plans_dir)
    rejections = load_rejections(plans_dir, errors)
    if errors:
        for error in errors:
            print(error.render(), file=sys.stderr)
        if args.check_executable:
            print(f"{len(errors)} validation error(s)", file=sys.stderr)
            return 2
        print(
            f"{len(errors)} error(s); index not written, previous index preserved",
            file=sys.stderr,
        )
        return 1

    if args.check_executable:
        code, messages = check_executable(rows, args.check_executable)
        stream = sys.stdout if code == 0 else sys.stderr
        for message in messages:
            print(message, file=stream)
        return code

    index_path = plans_dir / "README.md"
    write_index_atomically(index_path, render_index(rows, rejections))
    print(f"wrote {plans_dir_display(plans_dir, root)}/README.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
