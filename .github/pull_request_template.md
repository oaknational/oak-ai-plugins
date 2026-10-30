<!-- Title: a Conventional Commit with the ticket at the end when there is one, for example
"fix: correct the tool names in audit-sequence (MCP-123)".
Pull requests are squash-merged, so the title becomes the commit on main. -->

## Description

<!-- What this changes, and why. For a plugin change, name the new plugin version. -->

-

## Issue(s)

Fixes MCP-

## How to test

1.

## Checklist

- [ ] A change to a skill the packages share is made in each package, and the package checks pass
- [ ] The version in every package's manifest has a matching entry at the top of `CHANGELOG.md`, dated the day this merges
- [ ] `claude plugin validate --strict` passes for the plugin and the marketplace
- [ ] The README's skills and commands tables still match what ships
- [ ] The title is a [Conventional Commit](https://www.conventionalcommits.org/) with the ticket at the end, when there is one
- [ ] Licences respected: Oak brand per the [brand guidelines](https://support.thenational.academy/using-the-oak-brand); Oak curriculum data attributed under OGL v3.0
