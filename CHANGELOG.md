# Changelog

Each version is the version of the plugins this repository publishes, the Claude plugin and the ChatGPT package, both copied from [oak-open-curriculum-ecosystem](https://github.com/oaknational/oak-open-curriculum-ecosystem). This file records what was published here and when. What changed in the plugins themselves is in [the Claude plugin's changelog](claude/plugins/oak-national-academy/CHANGELOG.md).

## 1.1.0 — 2026-10-19

- Publishes the Claude plugin and the ChatGPT package 1.1.0, copied from oak-open-curriculum-ecosystem at 386f3f8bf (release v1.186.0), without the `evals/` folders.
- First publication of the ChatGPT package, under `chatgpt/plugins/oak-national-academy`, with a ChatGPT and Codex marketplace file at `.agents/plugins/marketplace.json`.
- The ChatGPT upload ZIP workflow builds the ZIP OpenAI's plugin portal takes, with the manifest's name set to the live app's ID, and attaches it to the release.
- The sync, the Sync fidelity check, the drift check and the README, CHANGELOG and marketplace checks cover both packages. A sync copies both from one commit, and refuses one whose packages carry different versions.
- The Claude plugin changes only its version.

## 0.1.6 — 2026-10-01

- Publishes the Claude plugin 0.1.6, copied from oak-open-curriculum-ecosystem at a7cf0cc19, without the `evals/` folders. 0.1.5 was not published here; its changes are included.
- The plugin gains support, documentation and terms of service links for its directory listing, and names this repository as its repository.
- New listing text: a one-line description, and a README that says who the plugin is for and the DfE standards it is designed in line with, warns against entering pupil data, and links Oak's and Anthropic's privacy policies.
- The copy matches its source exactly, so no differences are recorded.

## 0.1.4 — 2026-09-30

- Publishes the Claude plugin 0.1.4, copied from oak-open-curriculum-ecosystem at 20589f260 (release v1.185.4), without the `evals/` folders. The plugin's 0.1.4 changelog entry names that release, ahead of the source.
- The plugin is renamed `oak-national-academy` and moves to `claude/plugins/oak-national-academy`. A `renames` entry in the marketplace moves existing installs to the new name.

## 0.1.3 — 2026-09-29

- First publication: the Claude plugin 0.1.3, copied from oak-open-curriculum-ecosystem at 9772f3385 (release v1.185.3), without the `evals/` folders. The plugin's 0.1.3 changelog entry names that release, ahead of the source.
- Adds the Claude Code marketplace, the README, CODEOWNERS, a pull request template, a .gitignore, pre-commit hooks, Dependabot for GitHub Actions, and CI: plugin validation, checks of the README, CHANGELOG and marketplace entry against the plugin, markdownlint, Prettier, gitleaks over the full history, internal link checking and a pull request title check.
