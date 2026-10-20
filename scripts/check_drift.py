"""Alarm when a published plugin falls behind its source repository.

For each publish in PROVENANCE.json, fetches the source repository's
current plugin manifest from its default branch and compares versions.
A mismatch means the ecosystem has released a plugin version this
repository doesn't publish yet — run the "Sync plugin from the
ecosystem" workflow to catch up.

Run weekly by CI (the "Publish drift" workflow), whose failure is the
alarm: issues are off here by design, so a red scheduled run is the
signal — GitHub emails it only to whoever last edited the workflow
file, so keep that a maintainer. Version-only on purpose: the
fidelity check already proves the copy matches its pinned commit, and
the ecosystem bumps the manifest version whenever the plugin changes.

Run it locally the same way: python3 scripts/check_drift.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BRANCH = "main"


def source_manifest_version(publish: dict) -> str:
    owner_repo = publish["source_repo"].removeprefix("https://github.com/")
    url = (
        f"https://raw.githubusercontent.com/{owner_repo}/{DEFAULT_BRANCH}/"
        f"{publish['source_path']}/{publish['manifest']}"
    )
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)["version"]


def main() -> int:
    provenance = json.loads((ROOT / "PROVENANCE.json").read_text(encoding="utf-8"))
    problems = []
    for publish in provenance["publishes"]:
        source_version = source_manifest_version(publish)
        if source_version != publish["plugin_version"]:
            problems.append(
                f"{publish['path']}: the source publishes {source_version}, this "
                f"repository still publishes {publish['plugin_version']} — run the "
                '"Sync plugin from the ecosystem" workflow'
            )
        else:
            print(
                f"{publish['path']}: up to date with the source at "
                f"{source_version}"
            )
    prefix = "::error::" if os.environ.get("GITHUB_ACTIONS") else "error: "
    for problem in problems:
        print(f"{prefix}{problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
