#!/usr/bin/env python3
"""Structural checker for the improve skill package."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, cast

DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
INLINE_LINK_RE = re.compile(r"!?\[[^\]]+\]\(([^)\n]+)\)")
REFERENCE_LINK_RE = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+)")
REQUIRED_VARIANTS = {
    "quick",
    "deep",
    "security",
    "branch",
    "next",
    "plan",
    "review-plan",
    "execute",
    "reconcile",
    "--issues",
}


class Checker:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.failures: list[str] = []
        self.skill_name: str | None = None
        self.skill_version: str | None = None
        self.skill_text = ""
        self.readme_text = ""

    def fail(self, msg: str) -> None:
        self.failures.append(msg)
        print(f"FAIL {msg}")

    def ok(self, label: str) -> None:
        print(f"PASS {label}")

    def run(self) -> int:
        self.check_skill_frontmatter()
        plugin = self.check_plugin_manifest()
        self.check_readme_install_target(plugin)
        self.check_markdown_links()
        self.check_invocation_variants()
        self.check_version_agreement(plugin)
        if self.failures:
            return 1
        print("all checks passed")
        return 0

    def check_skill_frontmatter(self) -> None:
        skill_paths = sorted((self.root / "skills").glob("*/SKILL.md"))
        if not skill_paths:
            self.fail("check1: no skills/*/SKILL.md file found")
            return
        if len(skill_paths) > 1:
            rel_paths = ", ".join(
                path.relative_to(self.root).as_posix() for path in skill_paths
            )
            self.fail(
                f"check1: expected one skill, found {len(skill_paths)}: {rel_paths}"
            )
            return

        skill_path = skill_paths[0]
        try:
            self.skill_text = skill_path.read_text(encoding="utf-8")
        except OSError as exc:
            self.fail(
                f"check1: cannot read {skill_path.relative_to(self.root).as_posix()}: {exc}"
            )
            return
        if not self.skill_text.strip():
            self.fail("check1: SKILL.md is empty")
            return

        frontmatter = split_frontmatter(self.skill_text, self.fail)
        if frontmatter is None:
            return
        data = parse_frontmatter(frontmatter, self.fail)

        name = scalar(data.get("name"))
        description = scalar(data.get("description"))
        compatibility = scalar(data.get("compatibility"))
        metadata = data.get("metadata")
        metadata_map = (
            cast(dict[str, Any], metadata) if isinstance(metadata, dict) else {}
        )
        version = scalar(metadata_map.get("version"))

        if not name:
            self.fail("check1: SKILL.md frontmatter missing or empty 'name:' field")
        elif not SKILL_NAME_RE.fullmatch(name):
            self.fail("check1: SKILL.md name must match ^[a-z][a-z0-9-]{1,63}$")
        elif skill_path.parent.name != name:
            self.fail(
                f"check1: skill directory {skill_path.parent.name!r} does not match name {name!r}"
            )
        else:
            self.skill_name = name

        if not description:
            self.fail(
                "check1: SKILL.md frontmatter missing or empty 'description:' field"
            )
        elif len(description) > 1024:
            self.fail("check1: SKILL.md description is longer than 1024 characters")

        if not compatibility:
            self.fail(
                "check1: SKILL.md frontmatter missing or empty 'compatibility:' field"
            )

        if not version:
            self.fail("check1: SKILL.md metadata.version is missing or empty")
        else:
            self.skill_version = version

        if self.skill_name and description and compatibility and self.skill_version:
            self.ok("check1: SKILL.md frontmatter valid")

    def check_plugin_manifest(self) -> dict[str, Any] | None:
        plugin_path = self.root / ".claude-plugin" / "plugin.json"
        try:
            plugin_raw: Any = json.loads(plugin_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self.fail(f"check2: .claude-plugin/plugin.json is not valid JSON: {exc}")
            return None
        except FileNotFoundError:
            self.fail("check2: .claude-plugin/plugin.json not found")
            return None
        if not isinstance(plugin_raw, dict):
            self.fail("check2: .claude-plugin/plugin.json must contain a JSON object")
            return None
        plugin = cast(dict[str, Any], plugin_raw)

        plugin_name = scalar(plugin.get("name"))
        plugin_version = scalar(plugin.get("version"))
        repository = scalar(plugin.get("repository"))
        homepage = scalar(plugin.get("homepage"))
        author = plugin.get("author")
        author_map = cast(dict[str, Any], author) if isinstance(author, dict) else {}
        author_name = scalar(author_map.get("name"))

        if not plugin_name:
            self.fail("check2: plugin.json 'name' is empty or missing")
        if not plugin_version:
            self.fail("check2: plugin.json 'version' is empty or missing")
        if not repository:
            self.fail("check2: plugin.json 'repository' is empty or missing")
        if not homepage:
            self.fail("check2: plugin.json 'homepage' is empty or missing")
        if not author_name:
            self.fail("check2: plugin.json 'author.name' is empty or missing")
        if plugin_name and self.skill_name and plugin_name != self.skill_name:
            self.fail(
                f"check2: plugin.json name {plugin_name!r} != SKILL.md name {self.skill_name!r}"
            )
        elif (
            plugin_name
            and self.skill_name
            and plugin_version
            and repository
            and homepage
            and author_name
        ):
            self.ok(f"check2: plugin.json valid, name={plugin_name!r} matches SKILL.md")
        return plugin

    def check_readme_install_target(self, plugin: dict[str, Any] | None) -> None:
        readme_path = self.root / "README.md"
        try:
            self.readme_text = readme_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            self.fail("check3: README.md not found")
            return

        install_match = re.search(
            r"\bnpx\s+skills\s+add\s+([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)",
            self.readme_text,
        )
        if not install_match:
            self.fail(
                "check3: README.md missing 'npx skills add <owner>/<repo>' install command"
            )
            return
        install_target = install_match.group(1)
        repository = scalar(plugin.get("repository")) if plugin else ""
        repository_target = github_target(repository)
        if repository_target and install_target.lower() != repository_target.lower():
            self.fail(
                f"check3: README install target {install_target!r} != plugin repository {repository_target!r}"
            )
        else:
            self.ok("check3: README install target matches plugin repository")

    def check_markdown_links(self) -> None:
        link_failures: list[str] = []
        skip_dirs = {
            self.root / ".git",
            self.root / "docs" / "dev" / "plans",
            self.root / "docs" / "dev" / "advisor-plans",
            self.root / "scripts" / "check-fixtures",
        }
        for dirpath, dirnames, filenames in os.walk(self.root):
            current_dir = Path(dirpath)
            dirnames[:] = [
                name
                for name in dirnames
                if current_dir / name not in skip_dirs
                and not (current_dir / name).is_relative_to(self.root / ".git")
            ]
            for filename in filenames:
                if not filename.endswith(".md"):
                    continue
                path = current_dir / filename
                text = path.read_text(encoding="utf-8")
                for line_number, target in markdown_links(text):
                    if should_skip_link(target):
                        continue
                    resolved = resolve_link(path.parent, target)
                    if not resolved.exists():
                        rel_path = path.relative_to(self.root).as_posix()
                        target_rel = os.path.relpath(resolved, self.root)
                        message = f"check4: broken link in {rel_path}:{line_number}: {target!r} -> {target_rel!r} not found"
                        link_failures.append(message)
                        self.fail(message)
        if not link_failures:
            self.ok("check4: all relative links resolve")

    def check_invocation_variants(self) -> None:
        if not self.readme_text:
            return
        failures: list[str] = []
        for variant in sorted(REQUIRED_VARIANTS):
            if not readme_has_variant(self.readme_text, variant):
                failures.append(f"README.md missing /improve {variant}")
            if not skill_has_variant(self.skill_text, variant):
                failures.append(f"SKILL.md missing {variant!r} invocation variant")
        for failure in failures:
            self.fail(f"check5: {failure}")
        if not failures:
            self.ok(
                f"check5: all {len(REQUIRED_VARIANTS)} variants present in README.md and SKILL.md"
            )

    def check_version_agreement(self, plugin: dict[str, Any] | None) -> None:
        if plugin is None or not self.skill_version:
            return
        plugin_version = scalar(plugin.get("version"))
        if self.skill_version != plugin_version:
            self.fail(
                f"check6: SKILL.md metadata version {self.skill_version!r} != plugin.json version {plugin_version!r}"
            )
        else:
            self.ok(f"check6: version agrees: {self.skill_version!r}")


def scalar(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def split_frontmatter(text: str, fail: Any) -> list[str] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        fail("check1: SKILL.md does not start with ---")
        return None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:index]
    fail("check1: SKILL.md frontmatter has no closing ---")
    return None


def parse_frontmatter(lines: list[str], fail: Any) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_map: dict[str, str] | None = None
    current_fold_key: str | None = None
    current_fold_lines: list[str] = []

    def finish_fold() -> None:
        nonlocal current_fold_key, current_fold_lines
        if current_fold_key is not None:
            data[current_fold_key] = " ".join(
                line.strip() for line in current_fold_lines
            ).strip()
            current_fold_key = None
            current_fold_lines = []

    for line_number, raw_line in enumerate(lines, start=2):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.startswith((" ", "\t")):
            if current_fold_key is not None:
                current_fold_lines.append(raw_line.strip())
                continue
            if current_map is not None:
                match = re.match(r"^\s+([A-Za-z0-9_-]+):\s*(.*)$", raw_line)
                if not match:
                    fail(
                        f"check1: malformed nested frontmatter line {line_number}: {raw_line!r}"
                    )
                    continue
                current_map[match.group(1)] = unquote(match.group(2).strip())
                continue
            fail(
                f"check1: unexpected indented frontmatter line {line_number}: {raw_line!r}"
            )
            continue

        finish_fold()
        current_map = None
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", raw_line)
        if not match:
            fail(f"check1: malformed frontmatter line {line_number}: {raw_line!r}")
            continue
        key, value = match.group(1), match.group(2).strip()
        if value == ">":
            current_fold_key = key
            current_fold_lines = []
        elif value == "":
            current_map = {}
            data[key] = current_map
        else:
            data[key] = unquote(value)
    finish_fold()
    return data


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def github_target(repository: str) -> str:
    match = re.match(r"https://github\.com/([^/]+/[^/.]+)(?:\.git)?/?$", repository)
    return match.group(1) if match else ""


def markdown_links(text: str) -> list[tuple[int, str]]:
    links: list[tuple[int, str]] = []
    in_fence = False
    fence_marker = ""
    for line_number, line in enumerate(text.splitlines(), start=1):
        fence_match = re.match(r"^(`{3,}|~{3,})", line.strip())
        if fence_match:
            marker = fence_match.group(1)[0]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = ""
            continue
        if in_fence:
            continue
        for match in INLINE_LINK_RE.finditer(line):
            links.append((line_number, first_link_token(match.group(1))))
        reference_match = REFERENCE_LINK_RE.match(line)
        if reference_match:
            links.append((line_number, first_link_token(reference_match.group(1))))
    return links


def first_link_token(target: str) -> str:
    target = target.strip()
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")]
    return target.split()[0]


def should_skip_link(target: str) -> bool:
    return target.startswith(("#", "http://", "https://", "mailto:"))


def resolve_link(base_dir: Path, target: str) -> Path:
    target = target.split("#", 1)[0].split("?", 1)[0]
    return (base_dir / target).resolve()


def readme_has_variant(text: str, variant: str) -> bool:
    if variant == "--issues":
        return re.search(r"(?m)^/improve\b.*--issues\b", text) is not None
    return re.search(rf"(?m)^/improve\s+{re.escape(variant)}(\s|\b)", text) is not None


def skill_has_variant(text: str, variant: str) -> bool:
    return f"`{variant}" in text or f"`{variant}`" in text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate improve skill structure")
    parser.add_argument(
        "--root", default=str(DEFAULT_REPO_ROOT), help="repository root to validate"
    )
    args = parser.parse_args(argv)
    return Checker(Path(args.root).resolve()).run()


if __name__ == "__main__":
    sys.exit(main())
