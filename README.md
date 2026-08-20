# agent-skills

An organization-wide catalog of [Agent Skills](https://agentskills.io/specification) for the
Forschungsgruppe Digital Health. Each skill is a directory with a `SKILL.md` conforming to the
open standard, so it installs into any compatible agent — Claude Code, Codex, Cursor, Copilot and
others — rather than into one vendor's format. This repository is the single source of truth from
which people and repositories install the subset relevant to them. There is no server and no
runtime: it is a Git repository with a generated index, and that is deliberate.

## Install

```bash
CATALOG=https://github.com/forschungsgruppe-digital-health/agent-skills/tree/v0.19.0  # x-release-please-version

# See what is available without installing anything.
npx skills add "$CATALOG" --list

# Install specific skills into specific agents.
npx skills add "$CATALOG" --skill skill-authoring --agent claude-code codex --yes
```

`--yes` / `-y` skips the confirmation prompts, which is what you want in CI. `--global` / `-g`
installs at user level instead of into the project.

**Pin the ref, and pin it the right way.** The `/tree/<ref>` form above is what pins;
`owner/repo@v0.1.0` does **not** — in this CLI `@` introduces a skill *name*, and that form
silently installs from the default branch. This was verified, not assumed; see
[docs/consuming-skills.md](docs/consuming-skills.md), which also covers the sync-workflow and
submodule paths and what to do when a release turns out to be bad.

## Catalog

[**CATALOG.md**](CATALOG.md) — every skill, with tier, domain, owner, status and description.

It is generated from the skills themselves and regenerated in CI, which fails if the committed
file no longer matches. So it is provably what the skills declare, not a table someone remembered
to update.

## Machine-readable index

[`skills/index.json`](skills/index.json) is the same information for tooling:

```json
{
  "schemaVersion": "1",
  "version": "0.0.0",
  "generator": "scripts/build_index.py",
  "skills": [
    {
      "url": "skill://skill-authoring/SKILL.md",
      "path": "skills/skill-authoring/SKILL.md",
      "frontmatter": { "name": "…", "description": "…" },
      "metadata": { "fgdh.tier": "universal", "fgdh.domain": "skill-catalog", "…": "…" }
    }
  ]
}
```

`frontmatter` carries only the two fields the open standard defines for discovery; the
organization's `fgdh.*` keys sit in a sibling object so that `frontmatter` stays a faithful subset
of the standard.

The shape mirrors the `skill://index.json` resource proposed in **SEP-2640**, the Skills-over-MCP
extension, so this file could back an MCP server later without restructuring. That proposal is
open and unratified, and `skill://` is a resource URI rather than a path — there is no directory
named `skill:`. See [docs/skills-over-mcp.md](docs/skills-over-mcp.md).

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md). The reasoning behind the rules is in
[docs/authoring-skills.md](docs/authoring-skills.md), the governance in
[docs/lifecycle.md](docs/lifecycle.md), and the branching model in
[docs/branching.md](docs/branching.md).

There is also a skill for it: [`skill-authoring`](skills/skill-authoring/SKILL.md).

## Tier model

Classification has three outcomes; only two of them may be stored.

| Classification | May assume | Admitted here |
| --- | --- | --- |
| `universal` | nothing — conventions, checklists, review procedures | yes |
| `domain` | a toolchain exists; project layout is **discovered**, not assumed | yes |
| `project` | specific files at specific paths | **no** — it belongs in the consuming repository |

`fgdh.tier: "project"` fails validation. The fix is to lift the skill to `domain` by replacing
hard-coded paths with a discovery step and an explicit failure branch — or to move it out. That
lift is what makes a skill survive installation into a repository nobody anticipated.

## Licensing

- **Code and scripts** — [Apache-2.0](LICENSE). This covers `scripts/` anywhere in the
  repository, including inside a skill folder.
- **Documentation and skill prose** — [CC-BY-4.0](LICENSE-docs). This covers `docs/`, this README,
  and each skill's `SKILL.md`, `references/` and `assets/`.

A skill's `license:` field covers its `SKILL.md`, `references/` and `assets/`. A skill needing
different terms declares them in its own bundled license file and points `license:` at that file.

Copyright the contributors. Attribution: *Forschungsgruppe Digital Health, TU Dresden*.

## Continuation

This catalog is built to outlive the project that started it.

Everything here is permissively licensed and there is nothing to operate — no server, no account,
no certificate to renew. If maintenance stops, every pinned tag keeps working exactly as it was,
and anyone may fork the repository and continue the catalog.

**Pin tags rather than tracking the default branch.** That is the single thing a consumer must do
for the guarantee above to hold: a pinned tag is a fixed artifact, whereas `main` is a moving one
even when it is always releasable.
