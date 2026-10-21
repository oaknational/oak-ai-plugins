# Contributing

Thank you for taking an interest in Oak's AI plugins. This repository publishes
the plugins so that anyone can read and install them, but the ways to
contribute differ depending on whether you work at Oak National Academy.

## Are pull requests accepted?

**Not from outside Oak National Academy.** We are not able to review or merge
external pull requests, and we would rather say so plainly than leave one
sitting unanswered.

## What feedback is most useful

We very much want to hear from people using the plugins. The most useful things
you can tell us are:

- **Wrong or unhelpful answers** — a skill or workflow that gave an answer that
  was wrong, out of date or not useful. Say what you asked, what you got, and
  what you expected.
- **Curriculum problems** — a lesson, unit or misconception the plugin reported
  that looks wrong or incomplete.
- **Installation problems** — the plugin not installing, not loading, or not
  connecting to the Oak Curriculum MCP.
- **Gaps** — something you expected the plugin to help with that it doesn't.
- **Documentation that is wrong or unclear** — including anything in this
  repository.

## How to send feedback

Use the AI plugin feedback form:

**<https://survey.hsforms.com/2vy6BnIvzTASqx1DbH8CaJAbvumd>**

GitHub issues are turned off on this repository, so the form is the route that
reaches the team. See [SUPPORT.md](SUPPORT.md) for what is in scope and how
quickly you can expect a reply.

**Do not report security vulnerabilities through the form.** Follow
[SECURITY.md](SECURITY.md) instead.

## Code of conduct

Everyone interacting with this project, including through the feedback form, is
expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## For Oak engineers

1. Change the plugins here, on a branch. A change to a skill both packages
   ship is made in both: the ChatGPT package's copy must match the Claude
   plugin's byte for byte, and `scripts/check_skill_copies.py` fails until it
   does. Raise the version in both manifests and add an entry to
   [CHANGELOG.md](CHANGELOG.md).
2. Open a pull request against `main`. Its title is a
   [Conventional Commit](https://www.conventionalcommits.org/) with the ticket at
   the end when there is one, because pull requests are squash-merged and the title becomes the
   commit on `main`. It needs the required checks and an approving review before
   it can merge. The checks are described in
   [.github/workflows/README.md](.github/workflows/README.md).
3. To release, run the **Release** workflow with the version, first as a dry
   run. It checks the version against both manifests and the latest
   CHANGELOG entry, builds the ChatGPT upload ZIP and creates the release with
   the ZIP attached. Uploading the ZIP to OpenAI's portal stays manual.
4. To run the same checks locally before each commit, install
   [pre-commit](https://pre-commit.com) and the hooks once, as the README
   describes.
