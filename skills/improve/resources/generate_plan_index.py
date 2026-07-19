#!/usr/bin/env python3
"""Generate the plan-directory README.md index from plan frontmatter.

Rendering only. Parsing, schema validation, lifecycle invariants, and the
rejections source live in plan_state.py (same directory); this module writes
the index atomically and only when the whole directory validates — invalid
input exits nonzero and preserves the previous index.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, cast

_RESOURCES_DIR = Path(__file__).resolve().parent
if str(_RESOURCES_DIR) not in sys.path:
    sys.path.insert(0, str(_RESOURCES_DIR))

from plan_state import (  # noqa: E402
    PlanValue,
    collect_plans,
    load_rejections,
    plans_dir_display,
    resolve_plans_dir,
)


def escape_cell(text: str) -> str:
    """Keep arbitrary scalar content from corrupting the Markdown table."""
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def cell(value: PlanValue) -> str:
    if value in (None, "", []):
        return "-"
    if isinstance(value, list):
        return escape_cell(", ".join(str(item) for item in value)) if value else "-"
    return escape_cell(str(value))


EXECUTION_DETAIL_FIELDS = (
    "execution_profile",
    "execution_locator",
    "execution_branch",
    "execution_base",
    "executor_head",
    "reviewed_commit",
    "merged_commit",
    "verification_environment",
)


def render_index(
    rows: list[dict[str, PlanValue]], rejections: list[dict[str, Any]]
) -> str:
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
    for row in rows:
        plan_id = cell(row.get("id"))
        title = cell(row.get("title"))
        filename = cell(row.get("file"))
        if row.get("sensitive") is True:
            title = f"{title} (sensitive)"
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
                    cell(row.get("status_note")),
                    cell(row.get("issue")),
                ]
            )
            + " |"
        )
    if not rows:
        lines.append("| - | No plans yet | - | - | - | - | - | - |")
    lines.extend(
        [
            "",
            "Status values: TODO | EXECUTING | REVIEWED | MERGED | VERIFIED | BLOCKED | REJECTED | ABANDONED | SUPERSEDED",
        ]
    )

    detail_rows = [
        row
        for row in rows
        if any(row.get(field) not in (None, "", []) for field in EXECUTION_DETAIL_FIELDS)
    ]
    if detail_rows:
        lines.extend(
            [
                "",
                "## Execution & Verification Details",
                "",
                "| Plan | Profile | Locator | Branch | Execution base | Executor head | Reviewed commit | Merged commit | Verification |",
                "| ---- | ------- | ------- | ------ | -------------- | ------------- | --------------- | ------------- | ------------ |",
            ]
        )
        for row in detail_rows:
            lines.append(
                "| "
                + " | ".join(
                    [cell(row.get("id"))]
                    + [cell(row.get(field)) for field in EXECUTION_DETAIL_FIELDS]
                )
                + " |"
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
        description="Generate the selected plan directory's README.md index"
    )
    parser.add_argument(
        "--plans-dir", required=True, help="selected plans directory"
    )
    args = parser.parse_args()
    plans_dir, problem = resolve_plans_dir(args.plans_dir)
    if plans_dir is None:
        print(f"ERROR {problem}", file=sys.stderr)
        return 2

    rows, errors = collect_plans(plans_dir)
    rejections = load_rejections(plans_dir, errors)
    if errors:
        for error in errors:
            print(error.render(), file=sys.stderr)
        print(
            f"{len(errors)} error(s); index not written, previous index preserved",
            file=sys.stderr,
        )
        return 1

    index_path = plans_dir / "README.md"
    write_index_atomically(index_path, render_index(rows, rejections))
    print(f"wrote {plans_dir_display(plans_dir)}/README.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
