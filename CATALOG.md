<!-- GENERATED FILE -- do not edit by hand. -->
<!-- Regenerate with: python scripts/build_index.py -->

# Catalog

Every skill in this repository, generated from the frontmatter of each `SKILL.md`.
CI regenerates this file and fails if it changes, so what you read here is provably
what the skills declare.

The machine-readable equivalent is [`skills/index.json`](skills/index.json).

| Skill | Tier | Domain | Owner | Status | Description |
| --- | --- | --- | --- | --- | --- |
| [`mii-ig-migration`](skills/mii-ig-migration/SKILL.md) | domain | fhir-ig | @msusky | experimental | Migrates an existing Simplifier-published MII KDS module Implementation Guide onto the MII KDS module template — reads the module's identity from its own sushi-config.yaml and preserves it, transfers the FSH artefacts, rewrites Simplifier and FQL render directives into IG Publisher equivalents, and sets up the bilingual page set. Use this skill when moving a KDS module off Simplifier or Forge, when a rendered Simplifier IG URL and its source GitHub repository are handed over for migration, or when the user mentions Kerndatensatz, KDS-Modul, Implementierungsleitfaden, Manteldokument, sushi-config, ig.ini, gofsh or the IG Publisher in the context of moving an existing guide. Do not use for authoring new profiles, for creating a module from scratch, or for translating a guide that is already on the template; the module template ships its own recipes and an ig-translate skill for those. |
| [`skill-authoring`](skills/skill-authoring/SKILL.md) | universal | skill-catalog | @msusky | experimental | Writes a new Agent Skill for the FGDH catalog, or brings an existing one up to the catalog contract. Use this skill when adding a skill, filling in a SKILL.md, choosing between the universal and domain tier, writing or sharpening a description so it triggers reliably, setting the fgdh.tier / fgdh.domain / fgdh.owner / fgdh.language / fgdh.status metadata keys, splitting an over-long body into references, or fixing a validation error such as tier/rejected, name/directory, path/absolute or one of the mirror/ rules. Do not use for deciding whether a skill should exist at all, for retiring one, or for release mechanics; those are governance questions answered by the catalog's lifecycle document. |
