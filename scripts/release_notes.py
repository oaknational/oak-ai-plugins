"""Check a release version and write its notes from the CHANGELOG.

A release must carry the version both manifests hold and the CHANGELOG's
latest entry names, so this script refuses any other version. The notes are
that CHANGELOG entry, followed by the install commands.

Run by the "Release" workflow before it builds the ChatGPT upload ZIP and
creates the release; runs locally too:

  python3 scripts/release_notes.py --version 1.2.0 --out notes.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFESTS = (
    "claude/plugins/oak-national-academy/.claude-plugin/plugin.json",
    "chatgpt/plugins/oak-national-academy/.codex-plugin/plugin.json",
)
INSTALL = """
## Install in Claude Code

```text
/plugin marketplace add oaknational/oak-ai-plugins
/plugin install oak-national-academy@oak-ai-plugins
```
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="version to release, without the v")
    parser.add_argument("--out", required=True, help="where to write the release notes")
    args = parser.parse_args()

    problems = []
    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version):
        problems.append(f"{args.version} is not MAJOR.MINOR.PATCH")
    for manifest in MANIFESTS:
        found = json.loads((ROOT / manifest).read_text(encoding="utf-8")).get("version")
        if found != args.version:
            problems.append(f"{manifest} says {found}")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    entry = re.search(r"^## (\S+) — .*?\n(.*?)(?=^## |\Z)", changelog, re.M | re.S)
    if not entry or entry.group(1) != args.version:
        problems.append(f"CHANGELOG.md's latest entry is {entry.group(1) if entry else 'missing'}")
    if problems:
        for problem in problems:
            print(f"error: cannot release {args.version}: {problem}")
        return 1

    Path(args.out).write_text(entry.group(2).strip() + "\n" + INSTALL, encoding="utf-8")
    print(f"Release notes for {args.version} written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
