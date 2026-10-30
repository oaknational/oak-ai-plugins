# Oak National Academy — Microsoft 365 Copilot package

This directory is the Microsoft 365 Copilot packaging of the Oak plugin, for Microsoft's plugin
store, Copilot Chat and Copilot Cowork. It is a **checked-in copy**, not a build output: its skills
are the ChatGPT package's, in `../../../chatgpt/plugins/oak-national-academy/skills/`. A
correction to a skill lands in the Claude plugin first, is copied to the ChatGPT package, and is
copied on from there, never the other way round. All three packages carry the same version.

## What is here

- `manifest.json` is a Microsoft 365 app manifest, version 1.29. It lists the five skills under
  `agentSkills` and the Oak Curriculum MCP, `https://mcp.thenational.academy/mcp`, under
  `agentConnectors`. It names no tool description file, so Microsoft reads the tool list from the
  server when it connects and the package does not go stale when a tool changes. The `id` is a
  fixed GUID: keep it the same across versions, so an update replaces the app rather than adding a
  second one.
- `skills/` holds the ChatGPT package's five skills, copied byte for byte. Microsoft reads a
  package's skills and connectors and nothing else, so it takes the same skills as ChatGPT: the
  two Claude workflows arrive merged into skills of the same name.
  `scripts/check_skill_copies.py` fails when a copy differs from the ChatGPT one, or when a skill
  is missing or extra.
- `color.png` is the Oak logo at 192×192.

`scripts/check_packages.py` checks the manifest against a strict schema, that its version,
description, name and links agree with the Claude plugin's, that `agentSkills` lists exactly the
skill folders here, that each skill keeps within Microsoft's skill rules, and that the package
holds exactly these files.

## Not finished

- **The outline icon.** Microsoft needs a 32×32 outline icon, white on a transparent background,
  as `outline.png`. The manifest names it, but it is not here yet, so the package cannot be
  uploaded until it is added.
- **Sign-in in Copilot Chat.** The connector has no sign-in settings, so Microsoft registers itself
  with Oak's sign-in on first use. Microsoft supports that in Copilot Cowork but not in Copilot
  Chat, which needs a sign-in client set up for Microsoft and its ID added to the connector
  (MCP-771).
- **The full description** repeats the short one until listing copy for Microsoft is agreed.
- **The upload ZIP** is not built yet, and releases do not attach one.

## Testing in a tenant

Once the outline icon is here, make a ZIP holding `manifest.json`, `color.png`, `outline.png` and
`skills/`, with all four at the ZIP's root. In Copilot Cowork, open **Customize**, then
**Plugins**, select **Add plugin**, choose the ZIP and share it with **Only you**.

Microsoft's guide to the package format and its validation rules:
<https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development>
