<!-- GENERATED FILE -- do not edit by hand. -->
<!-- Regenerate with: python scripts/build_index.py -->

# Catalog

Every skill in this repository, generated from the frontmatter of each `SKILL.md`.
CI regenerates this file and fails if it changes, so what you read here is provably
what the skills declare.

The machine-readable equivalent is [`skills/index.json`](skills/index.json).

| Skill | Tier | Domain | Owner | Status | Description |
| --- | --- | --- | --- | --- | --- |
| [`skill-authoring`](skills/skill-authoring/SKILL.md) | universal | skill-catalog | @msusky | experimental | Writes a new Agent Skill for the FGDH catalog, or brings an existing one up to the catalog contract. Use this skill when adding a skill, filling in a SKILL.md, choosing between the universal and domain tier, writing or sharpening a description so it triggers reliably, setting the fgdh.tier / fgdh.domain / fgdh.owner / fgdh.language / fgdh.status metadata keys, splitting an over-long body into references, or fixing a validation error such as tier/rejected, name/directory, path/absolute or one of the mirror/ rules. Do not use for deciding whether a skill should exist at all, for retiring one, or for release mechanics; those are governance questions answered by the catalog's lifecycle document. |
