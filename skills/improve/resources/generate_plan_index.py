#!/usr/bin/env python3
"""Generate docs/dev/plans/README.md from plan frontmatter."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TypeAlias, cast

DEFAULT_PLANS_DIR = Path.cwd() / "docs" / "dev" / "plans"
PlanValue: TypeAlias = str | bool | list[str] | None


def split_frontmatter(text: str) -> list[str] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:index]
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


def parse_frontmatter(lines: list[str]) -> dict[str, PlanValue]:
    data: dict[str, PlanValue] = {}
    current_list: str | None = None
    for raw_line in lines:
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.startswith("  - ") and current_list:
            value = raw_line.strip()[2:].strip()
            items = cast(list[str], data.setdefault(current_list, []))
            items.append(value)
            continue
        current_list = None
        if ":" not in raw_line:
            continue
        key, raw_value = raw_line.split(":", 1)
        key = key.strip()
        value = parse_value(raw_value)
        data[key] = value
        if value is None and raw_value.strip() == "":
            data[key] = []
            current_list = key
    return data


def plan_rows(plans_dir: Path) -> list[dict[str, PlanValue]]:
    rows: list[dict[str, PlanValue]] = []
    if not plans_dir.exists():
        return rows
    for path in sorted(plans_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        frontmatter = split_frontmatter(text)
        if frontmatter is None:
            continue
        data = parse_frontmatter(frontmatter)
        data["file"] = path.name
        rows.append(data)
    return rows


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate docs/dev/plans/README.md")
    parser.add_argument("--plans-dir", default=str(DEFAULT_PLANS_DIR), help="plan directory")
    args = parser.parse_args()
    plans_dir = Path(args.plans_dir)
    plans_dir.mkdir(parents=True, exist_ok=True)
    index_path = plans_dir / "README.md"
    index_path.write_text(render_index(plan_rows(plans_dir)), encoding="utf-8")
    print(f"wrote {index_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
