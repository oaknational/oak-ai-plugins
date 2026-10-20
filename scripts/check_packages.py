"""Check the rules the two plugin packages must follow, recomputed from the files.

The Claude plugin and the ChatGPT package describe one product, so facts that
appear in more than one place are copies, and each copy is checked against
its source here. Shapes are held by JSON Schemas that are strict at every
level (no key outside the schema passes), and everything a schema cannot
express is one small check per rule below. Every list this script scans must
be non-empty, so no check passes by reading nothing.

- ChatGPT package: the manifest has exactly the shape OpenAI's portal accepts
  (skills, the one Oak MCP server and listing fields; no hooks or apps), the
  subtitle is at most 30 characters, the category is one of OpenAI's, the
  review block holds exactly five positive and three negative test cases and
  nothing that must stay out of a public repository (the demo video link and
  reviewer account go in the portal's form), `capabilities` stays `[]`, and
  the package root holds exactly the expected entries.
- Merged skills: each ChatGPT skill with no Claude skill of the same name
  derives from the same-named Claude workflow and the agent it delegates to.
  The agent's body is carried byte for byte from its first `##` heading; before
  it come exactly the declared opening paragraph and the agent's own opening
  plus one dependency sentence; the description is the workflow's, word for
  word. Every such skill must be declared below.
- Both packages: the manifests agree field for field, every shipped skill's
  frontmatter meets the Agent Skills specification exactly, both icons are the
  Oak logo kept at assets/oak-national-academy-logo-512.png, and the ChatGPT
  marketplace lists the package under its manifest's name.
- Claude listing: one privacy policy and one terms link across both manifests
  and the plugin README, the repository is this one, the support and
  documentation links are set, and the README's opening, MCP endpoints and
  skills table match the plugin.
- MCP binding: both packages bind only the production server,
  https://mcp.thenational.academy/mcp, under the key `oak-national-academy`,
  and the MCP-enabled skill's compatibility note names the same host.

Ported from the oak-open-curriculum-ecosystem tests
chatgpt-plugin-package-invariants, chatgpt-merged-skill-derivation,
plugin-listing-invariants and plugin-mcp-server-binding (MCP-692, MCP-760,
MCP-766, MCP-302). Needs the pinned packages in scripts/requirements.txt.
Run by CI and by the pre-commit hook:

  python3 scripts/check_packages.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
CLAUDE = "claude/plugins/oak-national-academy"
CHATGPT = "chatgpt/plugins/oak-national-academy"
CLAUDE_MANIFEST = f"{CLAUDE}/.claude-plugin/plugin.json"
CODEX_MANIFEST = f"{CHATGPT}/.codex-plugin/plugin.json"
MARKETPLACE = ".agents/plugins/marketplace.json"
LOGO = "assets/oak-national-academy-logo-512.png"
ICON = "./assets/icon.png"
REPOSITORY = "https://github.com/oaknational/oak-ai-plugins"

# The binding every installing user receives. Renaming the key breaks
# installed users: it went oak-curriculum -> oak-open-curriculum (MCP-536,
# 2026-08-10) -> oak-national-academy (2026-09-30), each by owner decision.
MCP_ENDPOINT = "https://mcp.thenational.academy/mcp"
MCP_KEY = "oak-national-academy"

# The authored edits of each merged skill. A ChatGPT skill with no Claude
# skill of the same name must have an entry here, so nothing derives unchecked.
DECLARED_EDITS = {
    "audit-sequence": {
        "opening": (
            "Audit the draft sequence the user has shared. If they have not given you one, "
            "ask for it before going further."
        ),
        "bears_on": "sequencing",
    },
    "find-misconceptions": {
        "opening": (
            "Find the misconceptions for the topic the user has named. If they have not said "
            "which year group or key stage, ask before going further."
        ),
        "bears_on": "the teaching response",
    },
}

DELEGATE_LINE = re.compile(r"^Delegate to the \*\*([a-z0-9-]+)\*\* agent\.$", re.M)

# --- Schemas -------------------------------------------------------------------

TEXT = {"type": "string", "minLength": 1}
HTTPS = {"type": "string", "pattern": r"^https://[^\s/]+(/\S*)?$"}


def strict(properties: dict, optional: tuple[str, ...] = ()) -> dict:
    """An object with exactly these properties, all required unless named optional."""
    return {
        "type": "object",
        "properties": properties,
        "required": [key for key in properties if key not in optional],
        "additionalProperties": False,
    }


def exactly(count: int, item: dict) -> dict:
    return {"type": "array", "minItems": count, "maxItems": count, "items": item}


SHARED_FIELDS = {
    "name": TEXT,
    "version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"},
    "description": TEXT,
    "author": strict({"name": TEXT, "url": HTTPS}),
    "homepage": HTTPS,
    "repository": HTTPS,
    "license": TEXT,
    "keywords": {"type": "array", "minItems": 1, "items": TEXT},
}

# OpenAI's directory categories, as its `plugin_category_unknown` error names them.
OPENAI_CATEGORIES = [
    "Productivity", "Creativity", "Developer Tools", "Business & Operations",
    "Data & Analytics", "Communication", "Education & Research", "Security",
    "Finance", "Healthcare", "Travel", "Entertainment", "Other",
]

CODEX_MANIFEST_SCHEMA = strict({
    **SHARED_FIELDS,
    "skills": {"const": "./skills/"},
    "mcpServers": {"const": "./.mcp.json"},
    "interface": strict({
        "displayName": TEXT,
        # The portal refuses a subtitle over 30 characters.
        "shortDescription": {**TEXT, "maxLength": 30},
        "longDescription": TEXT,
        "developerName": TEXT,
        "category": {"enum": OPENAI_CATEGORIES},
        # [] is the value the OpenAI sideload accepted on 2026-09-07 (package
        # README); a change needs a fresh ingestion result recorded there.
        "capabilities": {"const": []},
        "websiteURL": HTTPS,
        "privacyPolicyURL": HTTPS,
        "termsOfServiceURL": HTTPS,
        "supportURL": HTTPS,
        "defaultPrompt": {"type": "array", "maxItems": 3, "items": {**TEXT, "maxLength": 128}},
        "logo": {"const": ICON},
        "composerIcon": {"const": ICON},
    }),
    # Exactly five positive and three negative test cases and nothing else:
    # the demo video link and reviewer credentials go in the portal, never here.
    "extensions": strict({
        "com.openai": strict({
            "review": strict({
                "test_cases": strict({
                    "positive": exactly(5, strict({
                        "description": TEXT, "prompt": TEXT,
                        "tools_triggered": TEXT, "expected_behavior": TEXT,
                    })),
                    "negative": exactly(3, strict({
                        "description": TEXT, "prompt": TEXT, "expected_behavior": TEXT,
                    })),
                }),
            }),
            "publication": strict({"release_notes": TEXT}),
        }),
    }),
})

# The listing fields the Claude plugin directory reads, plus the shared fields;
# `claude plugin validate --strict` holds the rest of the manifest.
CLAUDE_MANIFEST_SCHEMA = {
    "type": "object",
    "properties": {
        **SHARED_FIELDS,
        "displayName": TEXT,
        "repository": {"const": REPOSITORY},
        "icon": {"type": "string", "pattern": r"^\./"},
        "privacyPolicyUrl": HTTPS,
        "termsOfServiceUrl": HTTPS,
        "supportUrl": HTTPS,
        "documentationUrl": HTTPS,
    },
    "required": [*SHARED_FIELDS, "displayName", "icon", "privacyPolicyUrl",
                 "termsOfServiceUrl", "supportUrl", "documentationUrl"],
}

MCP_CONFIG_SCHEMA = strict({
    "mcpServers": {
        "type": "object",
        "minProperties": 1,
        "additionalProperties": strict({"type": TEXT, "url": HTTPS}),
    },
})

# The Codex local marketplace: exactly one entry, with policy values Codex accepts.
MARKETPLACE_SCHEMA = strict({
    "name": TEXT,
    "interface": strict({"displayName": TEXT}),
    "plugins": exactly(1, strict({
        "name": TEXT,
        "source": strict({"source": {"const": "local"}, "path": TEXT}),
        "policy": strict({
            "installation": {"enum": ["AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"]},
            "authentication": {"enum": ["ON_INSTALL", "ON_USE"]},
        }),
        "category": TEXT,
    })),
})

# Agent Skills specification fields only, so no host-specific field ships.
SKILL_FRONTMATTER_SCHEMA = strict({
    "name": {"type": "string", "pattern": r"^[a-z0-9]+(-[a-z0-9]+)*$", "maxLength": 64},
    "description": {"type": "string", "minLength": 1, "maxLength": 1024, "pattern": r"^[^<>]*$"},
    "license": TEXT,
    "compatibility": {**TEXT, "maxLength": 500},
    "metadata": strict({"author": TEXT, "version": TEXT}),
}, optional=("compatibility",))

AGENT_FRONTMATTER_SCHEMA = {"type": "object", "properties": {"skills": TEXT}, "required": ["skills"]}
DESCRIPTION_SCHEMA = {"type": "object", "properties": {"description": TEXT}, "required": ["description"]}


def schema_problems(schema: dict, instance: object, where: str) -> list[str]:
    """Every way the instance breaks the schema, each named by its path."""
    errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda e: list(map(str, e.path)))
    return [f"{where}: {'.'.join(str(p) for p in e.path) or '(root)'}: {e.message}" for e in errors]


# --- Reading files ---------------------------------------------------------------

class Unreadable(Exception):
    """A file a check needs is missing or not parseable; the message names it."""


def read(path: str) -> str:
    if not (ROOT / path).is_file():
        raise Unreadable(f"{path}: missing")
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> Any:
    try:
        return json.loads(read(path))
    except json.JSONDecodeError as error:
        raise Unreadable(f"{path}: not valid JSON ({error})") from error


def read_frontmatter(path: str) -> tuple[Any, str]:
    """The parsed frontmatter and the body after it."""
    text = read(path)
    end = text.find("\n---\n", 4)
    if not text.startswith("---\n") or end == -1:
        raise Unreadable(f"{path}: no frontmatter block")
    try:
        return yaml.safe_load(text[4:end]), text[end + 5:]
    except yaml.YAMLError as error:
        raise Unreadable(f"{path}: frontmatter is not valid YAML ({error})") from error


def kind(entry: Path) -> str:
    """What an entry is, without following a symlink."""
    if entry.is_symlink():
        return "symlink"
    return "directory" if entry.is_dir() else "file"


def entries(path: str) -> list[tuple[str, str]]:
    """A directory's entries and their kinds."""
    if not (ROOT / path).is_dir():
        raise Unreadable(f"{path}: missing")
    # Sorted by name explicitly: Path ordering ignores case on Windows.
    return sorted((entry.name, kind(entry)) for entry in (ROOT / path).iterdir())


def directories(path: str) -> list[str]:
    return [name for name, kind in entries(path) if kind == "directory"]


# --- Checks: each returns its problems -------------------------------------------

def check_schemas() -> list[str]:
    return [
        *schema_problems(CODEX_MANIFEST_SCHEMA, read_json(CODEX_MANIFEST), CODEX_MANIFEST),
        *schema_problems(CLAUDE_MANIFEST_SCHEMA, read_json(CLAUDE_MANIFEST), CLAUDE_MANIFEST),
        *schema_problems(MCP_CONFIG_SCHEMA, read_json(f"{CLAUDE}/.mcp.json"), f"{CLAUDE}/.mcp.json"),
        *schema_problems(MCP_CONFIG_SCHEMA, read_json(f"{CHATGPT}/.mcp.json"), f"{CHATGPT}/.mcp.json"),
        *schema_problems(MARKETPLACE_SCHEMA, read_json(MARKETPLACE), MARKETPLACE),
    ]


def check_package_layout() -> list[str]:
    expected = {
        CHATGPT: [(".codex-plugin", "directory"), (".mcp.json", "file"), ("README.md", "file"),
                  ("assets", "directory"), ("skills", "directory")],
        f"{CHATGPT}/.codex-plugin": [("plugin.json", "file")],
        f"{CHATGPT}/assets": [("icon.png", "file")],
    }
    return [
        f"{path}: holds {entries(path)}, expected exactly {wanted}"
        for path, wanted in expected.items()
        if entries(path) != wanted
    ]


def check_mcp_binding() -> list[str]:
    """Both packages declare only the production server, under the same key."""
    problems = []
    # Claude names the transport `http`; OpenAI's format names it `streamable-http`.
    for path, transport in ((f"{CLAUDE}/.mcp.json", "http"), (f"{CHATGPT}/.mcp.json", "streamable-http")):
        expected = {"mcpServers": {MCP_KEY: {"type": transport, "url": MCP_ENDPOINT}}}
        if read_json(path) != expected:
            problems.append(f"{path}: must declare only {MCP_KEY}, {transport}, {MCP_ENDPOINT}")
    skill = f"{CLAUDE}/skills/oak-curriculum-principles-mcp-enabled/SKILL.md"
    frontmatter, _ = read_frontmatter(skill)
    note = str(frontmatter.get("compatibility", "")) if isinstance(frontmatter, dict) else ""
    # The note is prose, so it names the address without https://. Every address
    # ending /mcp in it must be the production one, whole: a longer host that
    # merely contains it, such as wrong-mcp.thenational.academy, does not count.
    production = MCP_ENDPOINT.removeprefix("https://")
    named = re.findall(r"[\w.-]+/mcp(?![\w/.-])", note)
    if not named or any(address != production for address in named):
        problems.append(f"{skill}: compatibility note must name {production} and no other MCP address")
    return problems


def check_icons() -> list[str]:
    logo = ROOT / LOGO
    if not logo.is_file() or logo.stat().st_size == 0:
        return [f"{LOGO}: the Oak logo is missing or empty"]
    claude_icon = str(read_json(CLAUDE_MANIFEST)["icon"])
    return [
        f"{icon}: differs from {LOGO}; copy the logo over it"
        for icon in (f"{CLAUDE}/{claude_icon.removeprefix('./')}", f"{CHATGPT}/{ICON.removeprefix('./')}")
        if not (ROOT / icon).is_file() or (ROOT / icon).read_bytes() != logo.read_bytes()
    ]


def check_marketplace_entry() -> list[str]:
    entry = read_json(MARKETPLACE)["plugins"][0]
    problems = []
    if entry["name"] != read_json(CODEX_MANIFEST)["name"]:
        problems.append(f"{MARKETPLACE}: plugin name differs from the package's manifest")
    if entry["source"]["path"] != f"./{CHATGPT}":
        problems.append(f"{MARKETPLACE}: source path must be ./{CHATGPT}")
    # NOT_AVAILABLE would make it uninstallable; ON_INSTALL would ask for
    # sign-in before any tool is called.
    if entry["policy"] != {"installation": "AVAILABLE", "authentication": "ON_USE"}:
        problems.append(f"{MARKETPLACE}: policy must be AVAILABLE / ON_USE")
    return problems


def check_manifests_agree() -> list[str]:
    codex, claude = read_json(CODEX_MANIFEST), read_json(CLAUDE_MANIFEST)
    problems = [
        f"manifests: {field} differs between the Claude plugin and the ChatGPT package"
        for field in SHARED_FIELDS
        if codex[field] != claude[field]
    ]
    pairs = (("displayName", "displayName"), ("privacyPolicyURL", "privacyPolicyUrl"),
             ("termsOfServiceURL", "termsOfServiceUrl"))
    problems += [
        f"manifests: the ChatGPT interface.{codex_field} differs from the Claude {claude_field}"
        for codex_field, claude_field in pairs
        if codex["interface"][codex_field] != claude[claude_field]
    ]
    return problems


def check_skill_frontmatter() -> list[str]:
    root = f"{CHATGPT}/skills"
    strays = [name for name, kind in entries(root) if kind != "directory"]
    problems = [f"{root}: entries that are not skill directories would ship: {strays}"] if strays else []
    skills = directories(root)
    if not skills:
        problems.append(f"{root}: holds no skills")
    for skill in skills:
        path = f"{root}/{skill}/SKILL.md"
        frontmatter, _ = read_frontmatter(path)
        found = schema_problems(SKILL_FRONTMATTER_SCHEMA, frontmatter, path)
        problems += found
        if not found and frontmatter["name"] != skill:
            problems.append(f"{path}: name {frontmatter['name']} does not match its folder")
    return problems


def split_body(body: str, where: str) -> tuple[list[str], str]:
    """Paragraphs before the first `##` heading, and everything from it on."""
    match = re.search(r"^## ", body, re.M)
    if not match:
        raise Unreadable(f"{where}: no `##` section")
    head = [p.strip() for p in re.split(r"\n\s*\n", body[: match.start()]) if p.strip()]
    return head, body[match.start():]


def derivation_problems(skill: str) -> list[str]:
    workflow_path = f"{CLAUDE}/workflows/{skill}/SKILL.md"
    skill_path = f"{CHATGPT}/skills/{skill}/SKILL.md"
    workflow, workflow_body = read_frontmatter(workflow_path)
    delegate = DELEGATE_LINE.search(workflow_body)
    if not delegate:
        return [f"{workflow_path}: no 'Delegate to the **<agent>** agent.' line"]
    agent_path = f"{CLAUDE}/agents/{delegate.group(1)}.md"
    agent, agent_body = read_frontmatter(agent_path)
    merged, merged_body = read_frontmatter(skill_path)
    problems = [
        *schema_problems(AGENT_FRONTMATTER_SCHEMA, agent, agent_path),
        *schema_problems(DESCRIPTION_SCHEMA, workflow, workflow_path),
        *schema_problems(DESCRIPTION_SCHEMA, merged, skill_path),
    ]
    if problems:
        return problems
    agent_head, agent_sections = split_body(agent_body, agent_path)
    skill_head, skill_sections = split_body(merged_body, skill_path)
    if skill_sections != agent_sections:
        problems.append(f"{skill_path}: differs from {agent_path} from the first ## heading on")
    sentence = (
        "Apply Oak's six curriculum principles as background where they bear on "
        f"{DECLARED_EDITS[skill]['bears_on']} — the `{agent['skills']}` skill holds them in full."
    )
    expected_head = [DECLARED_EDITS[skill]["opening"], f"{agent_head[0]} {sentence}" if agent_head else ""]
    if len(agent_head) != 1 or skill_head != expected_head:
        problems.append(
            f"{skill_path}: before the first ## heading it must hold the declared opening, "
            "then the agent's opening plus the dependency sentence"
        )
    if merged["description"] != workflow["description"]:
        problems.append(f"{skill_path}: description differs from {workflow_path}")
    return problems


def check_merged_skills() -> list[str]:
    merged = sorted(set(directories(f"{CHATGPT}/skills")) - set(directories(f"{CLAUDE}/skills")))
    if not merged:
        return [f"{CHATGPT}/skills: no merged skills found; this check would pass vacuously"]
    if merged != sorted(DECLARED_EDITS):
        return [f"merged skills {merged} differ from those declared in check_packages.py {sorted(DECLARED_EDITS)}"]
    return [problem for skill in merged for problem in derivation_problems(skill)]


def readme_link_problems(readme: str, privacy_url: str) -> list[str]:
    # Other services' privacy policies may be linked; only links on Oak's host must be the one policy.
    oak_host = urlparse(privacy_url).netloc
    links = re.findall(r"\[([^\]]*)\]\(([^)\s]+)\)", readme)
    oak_privacy = [url for text, url in links if "privacy" in text.lower() and urlparse(url).netloc == oak_host]
    if oak_privacy != [privacy_url]:
        return [f"{CLAUDE}/README.md: must link Oak's privacy policy once, at {privacy_url}"]
    return []


def check_claude_readme() -> list[str]:
    path = f"{CLAUDE}/README.md"
    readme, manifest = read(path), read_json(CLAUDE_MANIFEST)
    problems = readme_link_problems(readme, manifest["privacyPolicyUrl"])
    opening = re.match(r"# .+\n\n(.+)\n", readme)
    if not opening or opening.group(1) != manifest["description"]:
        problems.append(f"{path}: the first paragraph must be the manifest description, word for word")
    declared = sorted(server["url"] for server in read_json(f"{CLAUDE}/.mcp.json")["mcpServers"].values())
    named = sorted(url for url in re.findall(r"https://[^\s)>]+", readme) if url.endswith("/mcp"))
    if named != declared:
        problems.append(f"{path}: names MCP endpoints {named}, the plugin declares {declared}")
    shipped = sorted(directories(f"{CLAUDE}/skills") + directories(f"{CLAUDE}/workflows"))
    tabled = sorted(re.findall(r"^\| `([a-z0-9-]+)`", readme, re.M))
    if not shipped or tabled != shipped:
        problems.append(f"{path}: its table lists {tabled}, the plugin ships {shipped}")
    return problems


# These run only once the schemas pass, so each can rely on the shapes they hold.
CHECKS_AFTER_SCHEMAS = (
    check_package_layout, check_mcp_binding, check_icons, check_marketplace_entry,
    check_manifests_agree, check_skill_frontmatter, check_merged_skills, check_claude_readme,
)


def run_checks() -> list[str]:
    try:
        problems = check_schemas()
        if problems:
            return problems
        for check in CHECKS_AFTER_SCHEMAS:
            problems += check()
        return problems
    except Unreadable as error:
        return [str(error)]


def main() -> int:
    problems = run_checks()
    prefix = "::error::" if os.environ.get("GITHUB_ACTIONS") else "error: "
    for problem in problems:
        print(f"{prefix}{problem}")
    if not problems:
        print("Packages: both manifests, the ChatGPT package, the merged skills, the listing and the MCP binding check out.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
