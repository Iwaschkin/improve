#!/usr/bin/env python3
"""Fixture tests for scripts/check.py."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER = REPO_ROOT / "scripts" / "check.py"

BASE_README = """# improve

## Install

```bash
npx skills add Iwaschkin/improve
```

## Usage

```text
/improve                        full audit -> prioritized findings -> plans
/improve quick                  cheap pass
/improve deep                   exhaustive pass
/improve security               focused audit
/improve branch                 branch audit
/improve next                   feature suggestions
/improve plan <description>     write one plan
/improve review-plan <file>     critique a plan
/improve execute <plan>         dispatch executor
/improve reconcile              refresh backlog
/improve ... --issues           publish plans
```
"""

BASE_SKILL = """---
name: improve
description: Test improve skill fixture.
license: MIT
compatibility: >
  Audit and planning require Agent Skills support and file access.
metadata:
  author: Iwaschkin
  version: "1.1.0"
---

# Improve

Invocation variants: `quick`, `deep`, `security`, `branch`, `next`, `plan`,
`review-plan`, `execute`, `reconcile`, and `--issues`.
"""

BASE_PLUGIN: dict[str, object] = {
    "name": "improve",
    "description": "Fixture plugin manifest.",
    "version": "1.1.0",
    "author": {"name": "Iwaschkin", "url": "https://github.com/Iwaschkin"},
    "homepage": "https://github.com/Iwaschkin/improve",
    "repository": "https://github.com/Iwaschkin/improve",
    "license": "MIT",
}


def base_files(skill_dir: str = "improve") -> dict[str, str]:
    return {
        "README.md": BASE_README,
        f"skills/{skill_dir}/SKILL.md": BASE_SKILL,
        ".claude-plugin/plugin.json": json.dumps(BASE_PLUGIN, indent=2),
    }


def fixture_files(name: str) -> tuple[dict[str, str], bool]:
    files = base_files()
    if name == "valid-minimal":
        return files, True
    if name == "valid-complete":
        files["README.md"] += "\nSee [reference](docs/reference.md).\n"
        files["docs/reference.md"] = "# Reference\n"
        return files, True
    if name == "invalid-name":
        files["skills/improve/SKILL.md"] = BASE_SKILL.replace(
            "name: improve", "name: Bad Name"
        )
        return files, False
    if name == "directory-name-mismatch":
        return base_files(skill_dir="not-improve"), False
    if name == "missing-frontmatter":
        files["skills/improve/SKILL.md"] = "# Improve\n"
        return files, False
    if name == "malformed-frontmatter":
        files["skills/improve/SKILL.md"] = "---\nname improve\n---\n# Improve\n"
        return files, False
    if name == "broken-reference":
        files["README.md"] += "\n[Broken](missing.md)\n"
        return files, False
    if name == "version-mismatch":
        plugin = dict(BASE_PLUGIN)
        plugin["version"] = "9.9.9"
        files[".claude-plugin/plugin.json"] = json.dumps(plugin, indent=2)
        return files, False
    if name == "missing-variant":
        files["README.md"] = BASE_README.replace(
            "/improve execute <plan>         dispatch executor\n", ""
        )
        return files, False
    if name == "empty-skill":
        files["skills/improve/SKILL.md"] = ""
        return files, False
    if name == "invalid-plugin-json":
        files[".claude-plugin/plugin.json"] = "{not json\n"
        return files, False
    if name == "core-only-no-plugin":
        del files[".claude-plugin/plugin.json"]
        return files, True
    if name == "core-plus-marketplace":
        files[".claude-plugin/marketplace.json"] = json.dumps(
            {
                "name": "improve",
                "owner": {"name": "Iwaschkin"},
                "plugins": [{"name": "improve", "source": "./"}],
            },
            indent=2,
        )
        return files, True
    if name == "marketplace-empty-owner":
        files[".claude-plugin/marketplace.json"] = json.dumps(
            {"name": "improve", "owner": {}, "plugins": [{"name": "improve", "source": "./"}]},
            indent=2,
        )
        return files, False
    if name == "marketplace-missing-plugin-entry":
        files[".claude-plugin/marketplace.json"] = json.dumps(
            {"name": "improve", "owner": {"name": "Iwaschkin"}, "plugins": []},
            indent=2,
        )
        return files, False
    if name == "marketplace-without-plugin":
        del files[".claude-plugin/plugin.json"]
        files[".claude-plugin/marketplace.json"] = json.dumps(
            {"name": "improve", "owner": {"name": "Iwaschkin"}, "plugins": [{"name": "improve", "source": "./"}]},
            indent=2,
        )
        return files, False
    if name.startswith("name-valid-"):
        skill_name = name.removeprefix("name-valid-")
        return renamed_skill_files(skill_name), True
    if name.startswith("name-invalid-"):
        skill_name = INVALID_NAMES[name.removeprefix("name-invalid-")]
        return renamed_skill_files(skill_name), False
    if name == "variant-token-no-slash":
        files["README.md"] = HOST_NEUTRAL_README
        return files, True
    if name == "oversized-skill":
        files["skills/improve/SKILL.md"] = BASE_SKILL + ("filler line\n" * 500)
        return files, False
    raise ValueError(f"unknown fixture {name}")


INVALID_NAMES = {
    "uppercase": "Improve",
    "underscore": "im_prove",
    "leading-hyphen": "-improve",
    "trailing-hyphen": "improve-",
    "double-hyphen": "im--prove",
    "too-long": "a" * 65,
}

HOST_NEUTRAL_README = """# improve

## Install

```bash
npx skills add Iwaschkin/improve
```

## Usage

Invocation variants (spelled per host): `quick`, `deep`, `security`, `branch`,
`next`, `plan`, `review-plan`, `execute`, `reconcile`, and `--issues`.
"""


def renamed_skill_files(skill_name: str) -> dict[str, str]:
    """A fixture whose skill uses `skill_name` for both folder and frontmatter."""
    files = base_files(skill_dir=skill_name)
    files[f"skills/{skill_name}/SKILL.md"] = BASE_SKILL.replace(
        "name: improve", f"name: {skill_name}"
    )
    plugin = dict(BASE_PLUGIN)
    plugin["name"] = skill_name
    files[".claude-plugin/plugin.json"] = json.dumps(plugin, indent=2)
    return files


def write_fixture(root: Path, files: dict[str, str]) -> None:
    for relative_path, content in files.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def run_fixture(name: str, parent: Path) -> bool:
    fixture_root = parent / name
    if fixture_root.exists():
        shutil.rmtree(fixture_root)
    files, should_pass = fixture_files(name)
    write_fixture(fixture_root, files)
    result = subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(fixture_root)],
        check=False,
        capture_output=True,
        text=True,
    )
    passed = result.returncode == 0
    if passed == should_pass:
        print(f"PASS {name}")
        return True
    expected = "pass" if should_pass else "fail"
    print(f"FAIL {name}: expected {expected}, got exit {result.returncode}")
    print(result.stdout)
    print(result.stderr)
    return False


def main() -> int:
    fixtures = [
        "valid-minimal",
        "valid-complete",
        "invalid-name",
        "directory-name-mismatch",
        "missing-frontmatter",
        "malformed-frontmatter",
        "broken-reference",
        "version-mismatch",
        "missing-variant",
        "empty-skill",
        "invalid-plugin-json",
        "core-only-no-plugin",
        "core-plus-marketplace",
        "marketplace-empty-owner",
        "marketplace-missing-plugin-entry",
        "marketplace-without-plugin",
        "name-valid-a",
        "name-valid-1",
        "name-valid-a1",
        "name-valid-1-skill",
        "name-invalid-uppercase",
        "name-invalid-underscore",
        "name-invalid-leading-hyphen",
        "name-invalid-trailing-hyphen",
        "name-invalid-double-hyphen",
        "name-invalid-too-long",
        "variant-token-no-slash",
        "oversized-skill",
    ]
    with tempfile.TemporaryDirectory() as temp_dir:
        parent = Path(temp_dir)
        results = [run_fixture(name, parent) for name in fixtures]
    if not all(results):
        return 1
    print("all checker fixture tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
