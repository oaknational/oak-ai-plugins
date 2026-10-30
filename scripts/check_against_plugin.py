"""Check the README, CHANGELOG and marketplace entries against the packages.

The README restates facts the Claude plugin holds: the skills that ship, the
workflows' commands and the MCP config. The ChatGPT and Microsoft packages
ship the same skills, with each workflow merged into a skill of the same name.
The CHANGELOG's latest entry must be the version every package carries. The Claude
marketplace entry repeats the plugin's display name, description and
keywords; the ChatGPT marketplace entry repeats the package's name. Each is
recomputed from the packages, so none of them can drift from them. Run by CI
and by the pre-commit hook.
"""

import json
import os
import re
import sys

PLUGIN = "claude/plugins/oak-national-academy"
CHATGPT = "chatgpt/plugins/oak-national-academy"
MICROSOFT = "microsoft/plugins/oak-national-academy"


def read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def check_readme() -> list:
    """The README's skills table, commands table and MCP snippet, each
    recomputed from what the plugin ships."""
    readme = read("README.md")
    skills = set(os.listdir(f"{PLUGIN}/skills"))
    workflows = set(os.listdir(f"{PLUGIN}/workflows"))
    chatgpt_skills = set(os.listdir(f"{CHATGPT}/skills"))
    microsoft_skills = set(os.listdir(f"{MICROSOFT}/skills"))
    table = readme.split("## The skills", 1)[1].split("###", 1)[0]
    listed = set(re.findall(r"^\|\s*`([^`]+)`\s*\|", table, re.M))
    commands = set(re.findall(r"^\|\s*`/([a-z-]+)", readme, re.M))
    snippet = json.loads(re.search(r"```json\n(.*?)```", readme, re.S).group(1))
    mcp = json.loads(read(f"{PLUGIN}/.mcp.json"))

    problems = []
    if listed != skills | workflows:
        problems.append(
            f"README: skills table lists {sorted(listed)}, plugin ships {sorted(skills | workflows)}"
        )
    if chatgpt_skills != skills | workflows:
        problems.append(
            f"README: the ChatGPT package ships {sorted(chatgpt_skills)}, "
            f"the skills table lists {sorted(skills | workflows)}"
        )
    if microsoft_skills != skills | workflows:
        problems.append(
            f"README: the Microsoft package ships {sorted(microsoft_skills)}, "
            f"the skills table lists {sorted(skills | workflows)}"
        )
    if commands != workflows:
        problems.append(
            f"README: commands table lists {sorted(commands)}, plugin ships {sorted(workflows)}"
        )
    if snippet != mcp:
        problems.append("README: MCP config snippet differs from the plugin's .mcp.json")
    return problems


def check_changelog(manifests: dict) -> list:
    """The CHANGELOG's latest entry must be each package's version."""
    latest = re.search(r"^## (\S+)", read("CHANGELOG.md"), re.M)
    found = latest.group(1) if latest else "none"
    return [
        f"CHANGELOG: latest entry is {found}, {path} says {manifest['version']}"
        for path, manifest in manifests.items()
        if manifest["version"] != found
    ]


def check_marketplace(manifest: dict) -> list:
    """The marketplace entry must repeat the plugin manifest's fields."""
    marketplace = json.loads(read(".claude-plugin/marketplace.json"))
    entries = [e for e in marketplace["plugins"] if e["source"] == f"./{PLUGIN}"]
    if len(entries) != 1:
        return [f"marketplace: expected one entry with source ./{PLUGIN}, found {len(entries)}"]
    return [
        f"marketplace: {field} differs from the plugin's plugin.json"
        for field in ("name", "displayName", "description", "keywords")
        if entries[0].get(field) != manifest.get(field)
    ]


def check_chatgpt_marketplace(manifest: dict) -> list:
    """The ChatGPT marketplace must list the package under its manifest's name."""
    marketplace = json.loads(read(".agents/plugins/marketplace.json"))
    entries = [e for e in marketplace["plugins"] if e["source"].get("path") == f"./{CHATGPT}"]
    if len(entries) != 1:
        return [
            f"ChatGPT marketplace: expected one entry with path ./{CHATGPT}, found {len(entries)}"
        ]
    if entries[0]["name"] != manifest["name"]:
        return ["ChatGPT marketplace: name differs from the package's plugin.json"]
    return []


def main() -> int:
    manifest = json.loads(read(f"{PLUGIN}/.claude-plugin/plugin.json"))
    chatgpt = json.loads(read(f"{CHATGPT}/.codex-plugin/plugin.json"))
    microsoft = json.loads(read(f"{MICROSOFT}/manifest.json"))
    problems = (
        check_readme()
        + check_changelog({PLUGIN: manifest, CHATGPT: chatgpt, MICROSOFT: microsoft})
        + check_marketplace(manifest)
        + check_chatgpt_marketplace(chatgpt)
    )
    prefix = "::error::" if os.environ.get("GITHUB_ACTIONS") else "error: "
    for problem in problems:
        print(f"{prefix}{problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
