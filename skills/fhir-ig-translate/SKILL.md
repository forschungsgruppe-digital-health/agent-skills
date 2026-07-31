---
name: fhir-ig-translate
description: Sets up the German translation supplements an English-default MII KDS module
  Implementation Guide needs, putting each one exactly where the IG Publisher reads it — either by
  translating from the English source or by harvesting an already-published German rendering. The
  English source stays authoritative and every machine translation needs a bilingual human review.
  Use this skill when a module builds green and a German rendering is wanted, when the /de/ pages
  show English instead of German, when deciding where a .po supplement or a translated page belongs,
  or when the user mentions Übersetzung, translation supplement, input/translations, po file or
  i18n-default-lang. Do not use for measuring or comparing guides, for migrating one onto the
  template, or for the IG template package's own language mechanism; see fhir-ig-analyze and
  mii-ig-migration.
license: CC-BY-4.0
allowed-tools: Read Grep Glob Edit Write Bash(python3:*)
metadata:
  fgdh.tier: "domain"
  fgdh.domain: "fhir-ig"
  fgdh.owner: "@msusky"
  fgdh.language: "en"
  fgdh.status: "experimental"
---

# Translating an English-default MII KDS module IG into German

> **Experimental.** This skill has not been verified against a real task since its last change. Verify its output before relying on it.

Produces the German translation *supplements* of a module IG and puts them exactly where the IG
Publisher looks for them. English is the default language; German is the translation.

## Preconditions

1. **Locate the IG.** From the working directory, expect `input/pagecontent/` together with a
   `sushi-config.yaml` or an `ig.ini`. `scripts/ig-translate.sh` checks this itself and exits 2 with
   a message if the directory is not an IG project — it deliberately does **not** report "nothing to
   translate", which is what a silent failure here looks like.

2. **Confirm the language direction, every time.** Read `i18n-default-lang` in the IG's own
   `sushi-config.yaml`.
   - `en` → this skill applies as written: English source, German translation.
   - `de` → **stop.** The guide is German-led, so the direction is reversed and this skill's file
     layout and guardrails do not apply. Report it and ask. This is not hypothetical: the MII
     reversed this decision once, and a skill that assumed the old direction would put every file in
     the wrong place.

3. **Build first.** The resource supplements need generated resources: the publisher writes
   `fsh-generated/resources/` and generates `.po` templates per resource on each build. Translating
   before a green build means guessing at `msgid` values, which is fabrication.

4. **Know which repository's problem this is.** Multi-language support is split, and the split is
   about *documentation ownership*, not about paths:
   - **This skill** covers a concrete module IG's content: supplements and translated pages under
     `input/translations/<lang>/`.
   - **The IG template package**
     (<https://github.com/forschungsgruppe-digital-health/ig-template-mii-kds>) owns the language
     *mechanism* and *policy* — language-neutral header/footer/CSS, the base template's inherited
     UI strings, and the en-default decision itself. If the task is "keep the template's overrides
     language-neutral", that is the template package's own skill, not this one.

## Procedure

**Output language: German.** These instructions are English; what the skill produces is German
prose for the `/de/` rendering. Neither follows from the other, so it is stated here.

1. **Scan** to get the target path for every page and resource:

   ```bash
   scripts/ig-translate.sh --scan de              # from the IG root
   scripts/ig-translate.sh --scan de path/to/ig   # or point at it
   ```

2. **Resource supplements.** One file per StructureDefinition, CodeSystem or Questionnaire at
   `input/translations/de/<Type>-<id>.po`, where `msgid` is the **exact** English source text from
   `fsh-generated/resources/<Type>-<id>.json` and `msgstr` is the German. Copy the publisher's
   generated template rather than hand-writing the `msgid`.

3. **Narrative pages.** One translation per page at
   `input/translations/de/pagecontent/<same-filename>.md` — the *same* file name, the same structure,
   the same links, FHIR identifiers unchanged. **Never** a `<name>-de.md` sibling in
   `input/pagecontent/`: the toolchain renders that as a separate page, not as a translation.

4. **Menu**, if the IG has one: `input/translations/de/includes/menu.xml`, mirroring
   `input/includes/menu.xml`. A `menu:` property in `sushi-config.yaml` generates one
   untranslatable menu and competes with this — it must not be used alongside.

5. **Validate, then build:**

   ```bash
   scripts/ig-translate.sh --validate de
   ```

6. **Bilingual human review is mandatory** before the German rendering is trusted. Mark every
   machine translation `TODO:REVIEW` until a human has signed it off.

### Harvest mode — adopting an existing German rendering

When a German version already exists somewhere, harvest it instead of re-translating:

1. Fill in [`references/harvest-config.yaml`](references/harvest-config.yaml): where the German text
   comes from (a parallel rendered German guide for narrative; FSH `translation` extensions or
   `designation`s for resource texts) and the page/artefact mapping.
2. **Resources:** move the existing German designations or translation extensions into
   `input/translations/de/<Type>-<id>.po`.
3. **Narrative:** copy the German page content into
   `input/translations/de/pagecontent/<name>.md`, citing the source path per page. Invent nothing;
   mark anything unclear `TODO:REVIEW`.
4. Validate, build and review as above.

## What the toolchain actually renders

Verified with **IG Publisher 2.2.11** and `fhir2.base.template` 0.1.0 (2026-07).

| Content | Translatable? | Mechanism |
| --- | --- | --- |
| **Narrative pages** (`input/pagecontent/<name>.md`) | **Yes, renders** | `input/translations/<lang>/pagecontent/<same-filename>` — the whole page renders on `/<lang>/`. No file → falls back to the default-language source. |
| Resource texts of **StructureDefinition, CodeSystem, Questionnaire** (`description`, designations, element `definition`) | **Yes, renders** | Supplement `input/translations/<lang>/<Type>-<id>.{po\|xliff\|json}` |
| **Menu** (`input/includes/menu.xml`) | **Yes** | `input/translations/<lang>/includes/menu.xml` |
| **ValueSet**, some **ImplementationGuide** title fields, `concept.display` / `concept.definition` | **Partial / No** | Not applied from a plain `.po` supplement on this toolchain |

Treat this table as ground truth, and **re-verify it whenever the pinned IG Publisher or base
template version changes.** Read the pins from the IG's own build workflow, not from this file.

Two obsolete claims, recorded so they are not reintroduced: an earlier version of this skill used a
`<name>-<lang>.md` sibling for pages and stated that narrative pages were "not yet" renderable.
Both were wrong. The correct mechanism is a translation-source folder, as HL7's own
[`FHIR/multi-lang-test-ig`](https://github.com/FHIR/multi-lang-test-ig) demonstrates.

## Verification

```bash
scripts/ig-translate.sh --validate de
```

- Exit 2 with a clear message when run outside an IG — a silent empty scan is the failure mode this
  guards against.
- `--validate` reports `[OK]` per supplement and per page, and no `[WARN]`.
- Every `.po` filename is `<Type>-<id>` and matches a real `fsh-generated/resources/<Type>-<id>.json`.
- No supplement exists for an unsupported type, and no `menu.po` exists — the publisher ignores both.
- Every translated page has an English source page of the same name.
- After a build, `/de/` artefact pages show the translated element texts and `/de/` narrative pages
  render in German.
- The English `input/pagecontent/` and the FSH sources are **unchanged** — `git diff` on them is
  empty.

## Guardrails

- **The English source stays leading and binding.** A translation is a rendering aid, never the
  normative text.
- **Never change the source.** Translations are additive under `input/translations/<lang>/`.
- **FHIR identifiers stay English** — `name`, `id`, codes are not translated.
- **No invention.** Mark every machine translation `TODO:REVIEW`; bilingual human review is
  mandatory.
- **Only on confirmation.** The default is a dry-run scan.
- **Propose, do not merge.** Deliver changes as a pull request. **Determine the target branch from
  the repository's own convention** — do not assume one. An earlier version of this skill hard-coded
  `dev`, which is one repository's convention and wrong everywhere else.

## Scope and delimitation

Covers **producing and placing a module IG's German translation supplements**, in both directions of
provenance: translating the English source, or harvesting an existing German rendering.

Deliberately not covered:

- **Measuring or comparing guides** — see `fhir-ig-analyze`.
- **Migrating a guide onto the module template** — see `mii-ig-migration`, which sets translation up
  as one step of a migration and then hands over to this skill.
- **The IG template package's language mechanism and policy** — a different repository's skill; see
  Preconditions 4.
- **Translating into a language other than German**, or a German-led guide. The mechanism generalises
  but the guardrails here assume en → de; stop and ask.
- **Deciding whether a translation is good.** That is the mandatory human review, not this skill.

If a skill of this name is provided both by this catalog and locally, the local one wins.

## References

- [`references/translate-spec.md`](references/translate-spec.md) — the full mechanics, file
  conventions and formats.
- [`references/harvest-config.yaml`](references/harvest-config.yaml) — configuration schema for
  harvest mode.
- [`references/triggers.md`](references/triggers.md) — the Gate 3 prompt set.
- [`scripts/ig-translate.sh`](scripts/ig-translate.sh) — scan and validate; dry-run by design, it
  writes nothing.

## Provenance

Derived from `skills/ig-translate` in
`forschungsgruppe-digital-health/mii-kds-module-template` at commit
`b5beedb17a66a4397d597429668c7b6d54202c62`, which in turn adapted the `ig-translate` skill of
`forschungsgruppe-digital-health/mii-kds-sample-ig-inoffiziell` (CC-BY-4.0) and refocused it on the
module side. Both steps of that lineage are recorded deliberately.

Reworked on 2026-07-31 for this catalog. Beyond the catalog contract, three substantive changes:

- The helper now ships **with** the skill. It previously lived in the source repository's `scripts/`
  and was referenced by parent traversal.
- `scripts/ig-translate.sh` operates on the **current working directory** and detects whether it is
  an IG project. It previously did `cd "$(dirname "$0")/.."`, assuming it sat in
  `<module-repo>/scripts/`; installed as part of a skill that `cd` reaches the skill directory, and
  the scan would have reported every page as missing.
- The `dev` branch target was removed from the description and the guardrails, and replaced by
  discovering the repository's own convention.

Original licence: CC-BY-4.0, as declared by both source repositories. `scripts/` is Apache-2.0,
matching this repository's code licence.
