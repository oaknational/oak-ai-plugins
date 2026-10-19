"""Build the ZIP that OpenAI's plugin portal takes for the ChatGPT package.

The portal takes the whole package as one ZIP with the manifest at its
root, and refuses any package `name` other than the live app's ID. The
published copy keeps `oak-national-academy`, the name Codex and workspace
installs show, so this script writes every file of the copy unchanged
except the manifest, whose `name` it sets to the app ID. Entries are
sorted and carry fixed timestamps, so the same copy always builds the
same ZIP.

Run by the "ChatGPT upload ZIP" workflow, which attaches the ZIP to a
release, and by the Plugin validation job; runs locally too:

  python3 scripts/build_chatgpt_zip.py --out oak-national-academy-chatgpt.zip
"""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "chatgpt" / "plugins" / "oak-national-academy"
MANIFEST = ".codex-plugin/plugin.json"
OPENAI_APP_ID = "app-6aa0141317a08191a8e8f74fbabeeff1"
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def entry(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    return info


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="path of the ZIP to write")
    args = parser.parse_args()

    manifest = json.loads((PACKAGE / MANIFEST).read_text(encoding="utf-8"))
    manifest["name"] = OPENAI_APP_ID
    files = sorted(p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob("*") if p.is_file())

    with zipfile.ZipFile(args.out, "w") as zf:
        for name in files:
            if name == MANIFEST:
                data = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode()
            else:
                data = (PACKAGE / name).read_bytes()
            zf.writestr(entry(name), data)
    print(f"Wrote {args.out}: {len(files)} files, version {manifest['version']}")


if __name__ == "__main__":
    main()
