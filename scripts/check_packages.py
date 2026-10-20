"""Check the rules the two plugin packages must follow, recomputed from the files.

The Claude plugin and the ChatGPT package describe one product, so facts that
appear in more than one place are copies, and each copy is checked against
its source here. A shape change fails loudly: every manifest is held to an
exact set of keys, and every list this script scans must be non-empty, so no
check passes by reading nothing.

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
- MCP binding: both packages bind the production server,
  https://mcp.thenational.academy/mcp, under the key `oak-national-academy`,
  and the MCP-enabled skill's compatibility note names the same host.

Ported from the oak-open-curriculum-ecosystem tests
chatgpt-plugin-package-invariants, chatgpt-merged-skill-derivation,
plugin-listing-invariants and plugin-mcp-server-binding (MCP-692, MCP-760,
MCP-766, MCP-302). Run by CI and by the pre-commit hook:

  python3 scripts/check_packages.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
CLAUDE = "claude/plugins/oak-national-academy"
CHATGPT = "chatgpt/plugins/oak-national-academy"
LOGO = "assets/oak-national-academy-logo-512.png"
ICON = "./assets/icon.png"
REPOSITORY = "https://github.com/oaknational/oak-ai-plugins"

# The binding every installing user receives. Renaming the key breaks
# installed users: it went oak-curriculum -> oak-open-curriculum (MCP-536,
# 2026-08-10) -> oak-national-academy (2026-09-30), each by owner decision.
MCP_ENDPOINT = "https://mcp.thenational.academy/mcp"
MCP_KEY = "oak-national-academy"

# OpenAI's directory categories, as its `plugin_category_unknown` error names them.
OPENAI_CATEGORIES = {
    "Productivity", "Creativity", "Developer Tools", "Business & Operations",
    "Data & Analytics", "Communication", "Education & Research", "Security",
    "Finance", "Healthcare", "Travel", "Entertainment", "Other",
}

# The authored edits of each merged skill. A ChatGPT skill with no Claude
# skill of the same name must have an entry here, so nothing derives unchecked.
DECLARED_EDITS = {
    "audit-sequence": {
        "opening": "Audit the draft sequence the user has shared. If they have not given you one, ask for it before going further.",
        "bears_on": "sequencing",
    },
    "find-misconceptions": {
        "opening": "Find the misconceptions for the topic the user has named. If they have not said which year group or key stage, ask before going further.",
        "bears_on": "the teaching response",
    },
}

SKILL_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
DELEGATE_LINE = re.compile(r"^Delegate to the \*\*([a-z0-9-]+)\*\* agent\.$", re.M)

problems: list[str] = []


def problem(message: str) -> None:
    problems.append(message)


def read(path: str) -> str:
    """A file's text; a missing file is a problem, read as empty."""
    if not (ROOT / path).is_file():
        problem(f"{path}: missing")
        return ""
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    """A JSON object; a missing, unreadable or non-object file is a problem, read as empty."""
    text = read(path)
    try:
        value = json.loads(text) if text else {}
    except json.JSONDecodeError as error:
        problem(f"{path}: not valid JSON ({error})")
        return {}
    if not isinstance(value, dict):
        problem(f"{path}: expected a JSON object")
        return {}
    return value


def obj(value: object) -> dict:
    """The value if it is an object, otherwise empty; its shape is reported where it is checked."""
    return value if isinstance(value, dict) else {}


def is_https_url(value: object) -> bool:
    return isinstance(value, str) and urlparse(value).scheme == "https" and bool(urlparse(value).netloc)


def is_text(value: object, max_length: int | None = None) -> bool:
    return isinstance(value, str) and value != "" and (max_length is None or len(value) <= max_length)


def exact_keys(obj: object, where: str, required: set[str], optional: set[str] = frozenset()) -> bool:
    """The object has every required key, no key outside required and optional, and is an object."""
    if not isinstance(obj, dict):
        problem(f"{where}: expected an object")
        return False
    missing, extra = required - obj.keys(), obj.keys() - required - optional
    if missing:
        problem(f"{where}: missing {sorted(missing)}")
    if extra:
        problem(f"{where}: unexpected {sorted(extra)}")
    return not missing and not extra


# --- Frontmatter -----------------------------------------------------------
# The skills' frontmatter uses a small, fixed part of YAML: `key: value`,
# folded `key: >-` blocks, and one level of nesting. Anything else is refused
# rather than guessed at.

# Unquoted values YAML would read as something other than a string: numbers,
# booleans, null and dates. Quote them ('1.0') to keep them strings.
YAML_TYPED = re.compile(
    r"[-+]?(\d[\d_]*(\.\d*)?([eE][-+]?\d+)?|\.\d+|\.inf|\.nan|0x[0-9a-fA-F]+|0o[0-7]+)"
    r"|true|false|yes|no|on|off|null|~|\d{4}-\d\d-\d\d.*",
    re.I,
)


def scalar(raw: str, where: str) -> str:
    if raw.startswith("'"):
        if not raw.endswith("'") or len(raw) < 2:
            problem(f"{where}: unterminated quoted value {raw!r}")
        return raw[1:-1].replace("''", "'")
    unsupported = (
        raw.startswith(('"', "&", "*", "!", "|", "[", "{", "- ", "@", "`", "%", "?", ">"))
        or ": " in raw or " #" in raw or raw.endswith(":") or YAML_TYPED.fullmatch(raw)
    )
    if unsupported:
        problem(f"{where}: unsupported frontmatter value {raw!r}; quote it or simplify it")
    return raw


def parse_block(lines: list[str], where: str) -> dict:
    result: dict = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.strip():
            continue
        match = re.fullmatch(r"([A-Za-z][\w-]*):(?: (.*))?", line)
        if not match:
            problem(f"{where}: unsupported frontmatter line {line!r}")
            continue
        key, value = match.group(1), (match.group(2) or "").strip()
        if key in result:
            problem(f"{where}: duplicate key {key}")
        indented = []
        while i < len(lines) and (lines[i].startswith("  ") or not lines[i].strip()):
            indented.append(lines[i])
            i += 1
        if value == ">-":
            paragraphs, current = [], []
            for item in indented:
                if not item.strip():
                    if not current:
                        problem(f"{where}: unsupported blank lines in {key}")
                    else:
                        paragraphs.append(" ".join(current))
                    current = []
                elif item.startswith("   "):
                    problem(f"{where}: unsupported indentation under {key}")
                else:
                    current.append(item.strip())
            if current:
                paragraphs.append(" ".join(current))
            result[key] = "\n".join(paragraphs)
        elif value == "":
            result[key] = parse_block([item[2:] for item in indented], f"{where} {key}")
        else:
            if any(item.strip() for item in indented):
                problem(f"{where}: unexpected indented lines after {key}")
            result[key] = scalar(value, f"{where} {key}")
    return result


def split_frontmatter(path: str) -> tuple[dict, str]:
    text = read(path)
    end = text.find("\n---\n", 4)
    if not text.startswith("---\n") or end == -1:
        problem(f"{path}: no frontmatter block")
        return {}, text
    return parse_block(text[4:end].split("\n"), path), text[end + 5:]


# --- ChatGPT package ---------------------------------------------------------

SHARED_FIELDS = {"name", "version", "description", "author", "homepage", "repository", "license", "keywords"}


def check_shared_fields(manifest: dict, where: str) -> None:
    if not is_text(manifest.get("name")):
        problem(f"{where}: name must be set")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(manifest.get("version", ""))):
        problem(f"{where}: version must be MAJOR.MINOR.PATCH")
    for field in ("description", "license"):
        if not is_text(manifest.get(field)):
            problem(f"{where}: {field} must be set")
    for field in ("homepage", "repository"):
        if not is_https_url(manifest.get(field)):
            problem(f"{where}: {field} must be an https URL")
    author = manifest.get("author")
    if exact_keys(author, f"{where} author", {"name", "url"}):
        if not is_text(author["name"]) or not is_https_url(author["url"]):
            problem(f"{where}: author needs a name and an https URL")
    keywords = manifest.get("keywords")
    if not isinstance(keywords, list) or not keywords or not all(is_text(k) for k in keywords):
        problem(f"{where}: keywords must be a non-empty list of words")


def check_review_block(extensions: object, where: str) -> None:
    """Exactly five positive and three negative test cases, and nothing else: the
    demo video link and reviewer credentials belong in the portal, never here."""
    if not exact_keys(extensions, where, {"com.openai"}):
        return
    openai = extensions["com.openai"]
    if not exact_keys(openai, f"{where}.com.openai", {"review", "publication"}):
        return
    publication = openai["publication"]
    if exact_keys(publication, f"{where} publication", {"release_notes"}) and not is_text(publication["release_notes"]):
        problem(f"{where}: release_notes must be set")
    review = openai["review"]
    if not exact_keys(review, f"{where} review", {"test_cases"}):
        return
    cases = review["test_cases"]
    if not exact_keys(cases, f"{where} test_cases", {"positive", "negative"}):
        return
    shapes = {
        "positive": (5, {"description", "prompt", "tools_triggered", "expected_behavior"}),
        "negative": (3, {"description", "prompt", "expected_behavior"}),
    }
    for kind, (count, fields) in shapes.items():
        items = cases[kind]
        if not isinstance(items, list) or len(items) != count:
            problem(f"{where}: OpenAI requires exactly {count} {kind} test cases")
            continue
        for index, case in enumerate(items):
            if exact_keys(case, f"{where} {kind}[{index}]", fields):
                if not all(is_text(case[f]) for f in fields):
                    problem(f"{where} {kind}[{index}]: every field must be set")


def check_codex_manifest(manifest: dict) -> None:
    where = f"{CHATGPT}/.codex-plugin/plugin.json"
    exact_keys(manifest, where, SHARED_FIELDS | {"skills", "mcpServers", "interface", "extensions"})
    check_shared_fields(manifest, where)
    if manifest.get("skills") != "./skills/":
        problem(f"{where}: skills must be ./skills/")
    if manifest.get("mcpServers") != "./.mcp.json":
        problem(f"{where}: mcpServers must be ./.mcp.json")
    interface = manifest.get("interface")
    fields = {
        "displayName", "shortDescription", "longDescription", "developerName", "category",
        "capabilities", "websiteURL", "privacyPolicyURL", "termsOfServiceURL", "supportURL",
        "defaultPrompt", "logo", "composerIcon",
    }
    if exact_keys(interface, f"{where} interface", fields):
        for field in ("displayName", "longDescription", "developerName"):
            if not is_text(interface[field]):
                problem(f"{where}: interface.{field} must be set")
        # The portal refuses a subtitle over 30 characters.
        if not is_text(interface["shortDescription"], 30):
            problem(f"{where}: interface.shortDescription must be 1 to 30 characters")
        if not isinstance(interface["category"], str) or interface["category"] not in OPENAI_CATEGORIES:
            problem(f"{where}: interface.category must be one of OpenAI's categories")
        # [] is the value the OpenAI sideload accepted on 2026-09-07 (package
        # README); a change needs a fresh ingestion result recorded there.
        if interface["capabilities"] != []:
            problem(f"{where}: interface.capabilities must stay []")
        for field in ("websiteURL", "privacyPolicyURL", "termsOfServiceURL", "supportURL"):
            if not is_https_url(interface[field]):
                problem(f"{where}: interface.{field} must be an https URL")
        prompts = interface["defaultPrompt"]
        if not isinstance(prompts, list) or len(prompts) > 3 or not all(is_text(p, 128) for p in prompts):
            problem(
                f"{where}: interface.defaultPrompt must be at most 3 prompts of at most 128 characters"
            )
        for field in ("logo", "composerIcon"):
            if interface[field] != ICON:
                problem(f"{where}: interface.{field} must be {ICON}")
    check_review_block(manifest.get("extensions"), f"{where} extensions")


def entries(path: str) -> list[tuple[str, str]]:
    """A directory's entries and their kinds, without following symlinks."""
    result = []
    if not (ROOT / path).is_dir():
        problem(f"{path}: missing")
        return result
    for entry in sorted((ROOT / path).iterdir()):
        kind = "symlink" if entry.is_symlink() else "directory" if entry.is_dir() else "file"
        result.append((entry.name, kind))
    return result


def check_package_layout() -> None:
    expected = {
        CHATGPT: [(".codex-plugin", "directory"), (".mcp.json", "file"), ("README.md", "file"),
                  ("assets", "directory"), ("skills", "directory")],
        f"{CHATGPT}/.codex-plugin": [("plugin.json", "file")],
        f"{CHATGPT}/assets": [("icon.png", "file")],
    }
    for path, wanted in expected.items():
        found = entries(path)
        if found != wanted:
            problem(f"{path}: holds {found}, expected exactly {wanted}")


def mcp_servers(path: str) -> dict:
    config = read_json(path)
    servers = config.get("mcpServers") if exact_keys(config, path, {"mcpServers"}) else None
    if not isinstance(servers, dict) or not servers:
        problem(f"{path}: declares no MCP servers")
        return {}
    for key, server in servers.items():
        if exact_keys(server, f"{path} {key}", {"type", "url"}) and not is_https_url(server["url"]):
            problem(f"{path} {key}: url must be an https URL")
    return servers


def check_mcp_binding() -> None:
    """Both packages declare exactly one server: the production endpoint, under the same key."""
    claude = mcp_servers(f"{CLAUDE}/.mcp.json")
    chatgpt = mcp_servers(f"{CHATGPT}/.mcp.json")
    if claude != {MCP_KEY: {"type": "http", "url": MCP_ENDPOINT}}:
        problem(f"{CLAUDE}/.mcp.json: must declare only {MCP_KEY}, http, {MCP_ENDPOINT}")
    # Claude names the transport `http`; OpenAI's format names it `streamable-http`.
    if chatgpt != {MCP_KEY: {"type": "streamable-http", "url": MCP_ENDPOINT}}:
        problem(f"{CHATGPT}/.mcp.json: must declare only {MCP_KEY}, streamable-http, {MCP_ENDPOINT}")
    production = urlparse(MCP_ENDPOINT).netloc
    skill = f"{CLAUDE}/skills/oak-curriculum-principles-mcp-enabled/SKILL.md"
    note = str(split_frontmatter(skill)[0].get("compatibility", ""))
    if production not in note or "oaknational.dev" in note:
        problem(f"{skill}: compatibility note must name {production} and no non-production host")


def check_icons(claude_manifest: dict) -> None:
    logo = ROOT / LOGO
    if not logo.is_file() or logo.stat().st_size == 0:
        problem(f"{LOGO}: the Oak logo is missing or empty")
        return
    claude_icon = claude_manifest.get("icon")
    if not isinstance(claude_icon, str) or not claude_icon.startswith("./"):
        problem(f"{CLAUDE}/.claude-plugin/plugin.json: icon must be a ./ path")
        return
    for icon in (f"{CLAUDE}/{claude_icon[2:]}", f"{CHATGPT}/{ICON[2:]}"):
        if not (ROOT / icon).is_file() or (ROOT / icon).read_bytes() != logo.read_bytes():
            problem(f"{icon}: differs from {LOGO}; copy the logo over it")


def check_marketplace(codex_manifest: dict) -> None:
    path = ".agents/plugins/marketplace.json"
    marketplace = read_json(path)
    if not exact_keys(marketplace, path, {"name", "interface", "plugins"}):
        return
    if not is_text(marketplace["name"]):
        problem(f"{path}: name must be set")
    interface = marketplace["interface"]
    if exact_keys(interface, f"{path} interface", {"displayName"}) and not is_text(interface["displayName"]):
        problem(f"{path}: interface.displayName must be set")
    plugins = marketplace["plugins"]
    if not isinstance(plugins, list) or len(plugins) != 1:
        problem(f"{path}: must list exactly one plugin")
        return
    entry = plugins[0]
    if not exact_keys(entry, f"{path} plugin", {"name", "source", "policy", "category"}):
        return
    if entry["name"] != codex_manifest.get("name"):
        problem(f"{path}: plugin name differs from the package's manifest")
    if not is_text(entry["category"]):
        problem(f"{path}: plugin category must be set")
    if entry["source"] != {"source": "local", "path": f"./{CHATGPT}"}:
        problem(f"{path}: source must be local, ./{CHATGPT}")
    # NOT_AVAILABLE would make it uninstallable; ON_INSTALL would ask for
    # sign-in before any tool is called.
    if entry["policy"] != {"installation": "AVAILABLE", "authentication": "ON_USE"}:
        problem(f"{path}: policy must be AVAILABLE / ON_USE")


def check_manifests_agree(codex: dict, claude: dict) -> None:
    for field in sorted(SHARED_FIELDS):
        if codex.get(field) != claude.get(field):
            problem(f"manifests: {field} differs between the Claude plugin and the ChatGPT package")
    interface = obj(codex.get("interface"))
    if interface.get("displayName") != claude.get("displayName"):
        problem("manifests: the ChatGPT interface.displayName differs from the Claude displayName")


def skill_dirs(path: str) -> list[str]:
    found = entries(path)
    strays = [name for name, kind in found if kind != "directory"]
    if strays:
        problem(f"{path}: entries that are not skill directories would ship: {strays}")
    skills = [name for name, kind in found if kind == "directory"]
    if not skills:
        problem(f"{path}: holds no skills")
    return skills


def check_skill_frontmatter() -> None:
    for skill in skill_dirs(f"{CHATGPT}/skills"):
        path = f"{CHATGPT}/skills/{skill}/SKILL.md"
        frontmatter = split_frontmatter(path)[0]
        exact_keys(frontmatter, path, {"name", "description", "license", "metadata"}, {"compatibility"})
        name = frontmatter.get("name", "")
        if not SKILL_NAME.fullmatch(str(name)) or len(str(name)) > 64 or name != skill:
            problem(f"{path}: name must be kebab-case, at most 64 characters and match the folder")
        description = frontmatter.get("description", "")
        # The Agent Skills specification caps the description a host routes on at 1024.
        if not is_text(description, 1024) or re.search(r"[<>]", str(description)):
            problem(f"{path}: description must be 1 to 1024 characters with no angle brackets")
        if not is_text(frontmatter.get("license")):
            problem(f"{path}: license must be set")
        if "compatibility" in frontmatter and not is_text(frontmatter["compatibility"], 500):
            problem(f"{path}: compatibility must be 1 to 500 characters")
        metadata = frontmatter.get("metadata")
        if exact_keys(metadata, f"{path} metadata", {"author", "version"}):
            if not is_text(metadata["author"]) or not is_text(metadata["version"]):
                problem(f"{path}: metadata.author and metadata.version must be set")


# --- Merged skills -------------------------------------------------------------

def split_body(body: str, where: str) -> tuple[list[str], str]:
    """Paragraphs before the first `##` heading, and everything from it on."""
    match = re.search(r"^## ", body, re.M)
    if not match:
        problem(f"{where}: no `##` section")
        return [], body
    head = [p.strip() for p in re.split(r"\n\s*\n", body[: match.start()]) if p.strip()]
    return head, body[match.start():]


def check_merged_skills() -> None:
    claude_skills = {name for name, kind in entries(f"{CLAUDE}/skills") if kind == "directory"}
    merged = sorted(s for s in skill_dirs(f"{CHATGPT}/skills") if s not in claude_skills)
    if not merged:
        problem(f"{CHATGPT}/skills: no merged skills found; this check would pass vacuously")
    if merged != sorted(DECLARED_EDITS):
        problem(f"merged skills {merged} differ from those declared in check_packages.py {sorted(DECLARED_EDITS)}")
    for skill in (s for s in merged if s in DECLARED_EDITS):
        workflow_path = f"{CLAUDE}/workflows/{skill}/SKILL.md"
        skill_path = f"{CHATGPT}/skills/{skill}/SKILL.md"
        workflow, workflow_body = split_frontmatter(workflow_path)
        delegate = DELEGATE_LINE.search(workflow_body)
        if not delegate:
            problem(f"{workflow_path}: no 'Delegate to the **<agent>** agent.' line")
            continue
        agent_path = f"{CLAUDE}/agents/{delegate.group(1)}.md"
        if not (ROOT / agent_path).is_file():
            problem(f"{workflow_path}: delegates to {delegate.group(1)}, which has no {agent_path}")
            continue
        agent, agent_body = split_frontmatter(agent_path)
        merged_frontmatter, merged_body = split_frontmatter(skill_path)
        agent_head, agent_sections = split_body(agent_body, agent_path)
        skill_head, skill_sections = split_body(merged_body, skill_path)
        if skill_sections != agent_sections:
            problem(f"{skill_path}: differs from {agent_path} from the first ## heading on")
        dependency = agent.get("skills")
        sentence = (
            f"Apply Oak's six curriculum principles as background where they bear on "
            f"{DECLARED_EDITS[skill]['bears_on']} — the `{dependency}` skill holds them in full."
        )
        expected_head = [DECLARED_EDITS[skill]["opening"], f"{agent_head[0] if agent_head else ''} {sentence}"]
        if len(agent_head) != 1 or skill_head != expected_head:
            problem(
                f"{skill_path}: before the first ## heading it must hold the declared opening, "
                "then the agent's opening plus the dependency sentence"
            )
        if merged_frontmatter.get("description") != workflow.get("description"):
            problem(f"{skill_path}: description differs from {workflow_path}")


# --- Claude listing ------------------------------------------------------------

def check_claude_listing(claude: dict, codex: dict) -> None:
    where = f"{CLAUDE}/.claude-plugin/plugin.json"
    if claude.get("repository") != REPOSITORY:
        problem(f"{where}: repository must be {REPOSITORY}")
    for field in ("privacyPolicyUrl", "termsOfServiceUrl", "supportUrl", "documentationUrl"):
        if not is_https_url(claude.get(field)):
            problem(f"{where}: {field} must be an https URL")
    interface = obj(codex.get("interface"))
    if interface.get("privacyPolicyURL") != claude.get("privacyPolicyUrl"):
        problem("manifests: the two privacy policy links differ")
    if interface.get("termsOfServiceURL") != claude.get("termsOfServiceUrl"):
        problem("manifests: the two terms of service links differ")

    readme_path = f"{CLAUDE}/README.md"
    readme = read(readme_path)
    opening = re.match(r"# .+\n\n(.+)\n", readme)
    if not opening or opening.group(1) != claude.get("description"):
        problem(f"{readme_path}: the first paragraph must be the manifest description, word for word")
    # Other services' privacy policies may be linked; only links on Oak's host must be the one policy.
    oak_host = urlparse(str(claude.get("privacyPolicyUrl"))).netloc
    links = [m.group(2) for m in re.finditer(r"\[([^\]]*privacy[^\]]*)\]\(([^)]+)\)", readme, re.I)]
    if [url for url in links if urlparse(url).netloc == oak_host] != [claude.get("privacyPolicyUrl")]:
        problem(f"{readme_path}: must link Oak's privacy policy once, at the manifest's URL")
    servers = obj(read_json(f"{CLAUDE}/.mcp.json").get("mcpServers"))
    declared = sorted(str(obj(server).get("url")) for server in servers.values())
    named = sorted(re.findall(r"https://[^\s)>]+/mcp\b", readme))
    if not declared or named != declared:
        problem(f"{readme_path}: names MCP endpoints {named}, the plugin declares {declared}")
    shipped = sorted(
        name
        for root in ("skills", "workflows")
        for name, kind in entries(f"{CLAUDE}/{root}")
        if kind == "directory"
    )
    tabled = sorted(re.findall(r"^\| `([a-z0-9-]+)`", readme, re.M))
    if not shipped or tabled != shipped:
        problem(f"{readme_path}: its table lists {tabled}, the plugin ships {shipped}")


def main() -> int:
    claude = read_json(f"{CLAUDE}/.claude-plugin/plugin.json")
    codex = read_json(f"{CHATGPT}/.codex-plugin/plugin.json")
    try:
        check_codex_manifest(codex)
        check_shared_fields(claude, f"{CLAUDE}/.claude-plugin/plugin.json")
        check_package_layout()
        check_mcp_binding()
        check_icons(claude)
        check_marketplace(codex)
        check_manifests_agree(codex, claude)
        check_skill_frontmatter()
        check_merged_skills()
        check_claude_listing(claude, codex)
    except (OSError, TypeError, AttributeError, KeyError, ValueError) as error:
        # A shape no check anticipated: report it rather than pass or crash unexplained.
        problem(f"could not finish the checks on this input ({type(error).__name__}: {error})")

    prefix = "::error::" if os.environ.get("GITHUB_ACTIONS") else "error: "
    for message in problems:
        print(f"{prefix}{message}")
    if not problems:
        print("Packages: both manifests, the ChatGPT package, the merged skills, the listing and the MCP binding check out.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
