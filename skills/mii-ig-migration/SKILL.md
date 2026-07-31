---
name: mii-ig-migration
description: Migrates an existing Simplifier-published MII KDS module Implementation Guide onto
  the MII KDS module template — preserves the module's identity from its own sushi-config.yaml,
  transfers the FSH artefacts, rewrites Simplifier and FQL render directives into IG Publisher
  equivalents, and sets up the bilingual page set. Use this skill when moving a KDS module off
  Simplifier or Forge, when a rendered Simplifier IG URL and its source GitHub repository are
  handed over for migration, when narrative pages full of FQL blocks or {{tree}} and {{render}}
  directives stop rendering after such a move and need converting, or when the user mentions
  Kerndatensatz, KDS-Modul, Implementierungsleitfaden, Manteldokument, sushi-config, ig.ini,
  gofsh or the IG Publisher in the context of moving an existing guide. Do not use for authoring
  new profiles, for creating a module from scratch, or for translating a guide already on the
  template; the module template ships recipes and an ig-translate skill for those.
license: CC-BY-4.0
allowed-tools: Read Grep Glob WebFetch Bash(sushi:*) Bash(gofsh:*) Bash(git clone:*) Bash(git status:*) Bash(git diff:*)
metadata:
  fgdh.tier: "domain"
  fgdh.domain: "fhir-ig"
  fgdh.owner: "@msusky"
  fgdh.language: "en"
  fgdh.status: "experimental"
---

# Migrating an MII KDS module IG onto the module template

> **Experimental.** This skill has not been verified against a real task since its last change. Verify its output before relying on it.

This skill **supports and partly automates** the migration. It never publishes, and four human
review gates are mandatory. The full procedure, with acceptance criteria per step, is in
[the migration specification](references/migration-spec.md); this file is the operating summary.

## Preconditions

Discover the context. Do not assume any of it, and do not create what is missing.

1. **The source guide.** Two inputs come from the human and cannot be derived: the URL of the
   rendered Simplifier IG, and the URL of its source GitHub repository. If either is absent, ask
   for it and stop. Everything else about the module's identity is *read*, not asked (step 2).

2. **The module repository.** Identify it by locating, from the repository root, a
   `sushi-config.yaml` **or** an `ig.ini`, together with an `input/fsh/` directory. These are FHIR
   IG ecosystem conventions rather than one project's layout, which is what makes this skill
   portable.
   - Neither present → this is not a FHIR IG project. Say so and stop. Do not scaffold one.
   - `input/fsh/` present but empty → report it; a migration with no artefacts to move is a
     configuration error, not a no-op.

3. **The target template.** Determine which state the module is in:
   - **Already on the template** — a vendored `ig-template/` directory, or a `template` entry in
     `ig.ini` pointing at it. Then this is a *re-migration* or a partial one; report what is
     already in place before changing anything.
   - **Not yet on the template** — create the module repository from
     `forschungsgruppe-digital-health/mii-kds-module-template` and migrate into it. Read that
     repository at the ref you intend to use; do not rely on this skill's description of it.

4. **Unreplaced placeholders.** The template does not build until every `{{...}}` placeholder is
   replaced, and an unreplaced one **ships a bogus artefact** rather than failing loudly. Before
   and after migrating, grep the working tree for `{{` and account for every hit. The template's
   own `sushi-config.yaml` header block enumerates them and says which are active.

5. **The toolchain.** `sushi` and the IG Publisher must be runnable; `gofsh` is needed only if the
   source ships JSON/XML rather than FSH. Missing → report which one and stop before step 3. Do
   not fetch and execute a toolchain to get past this.

## Procedure

Written in English; the artefacts operated on are German-language KDS documents, and German terms
of art are kept as such. **Output language follows the target template: English is the default
language and German is the translation.** This reverses the older convention — see *Language*
below, and verify it against the target's `sushi-config.yaml` rather than trusting this sentence.


> **Resolve the script path first.** The commands below name the tool relative to **this skill's
> own directory**, not to your working directory — which is the project you are operating on. Set
> `SKILL_DIR` to the directory containing this `SKILL.md` (you just read it, so you know where it
> is) and use it in every invocation:
>
> ```bash
> SKILL_DIR=<the directory containing this SKILL.md>   # e.g. .claude/skills/mii-ig-migration
> ```
>
> Running a bare `scripts/...` from the project root does not merely fail — if the project happens
> to have its own `scripts/` directory with a same-named file, it silently runs **that** instead.

1. **Inventory the source.** From the rendered IG and the source repository, extract every
   artefact (profiles, extensions, value sets, code systems, capability statements, examples) and
   the narrative structure. Record each entry with its source path. Write
   `.ai-log/source-inventory.json`.

2. **Read the module's identity — do not ask for it, and do not invent it.** From the source
   repository's `sushi-config.yaml` and `package.json` (or, absent a `sushi-config.yaml`, from
   `package.json` plus the `ImplementationGuide` resource), read `title`, `packageId`, `canonical`,
   `status`, `releaseLabel`, `dependencies` and `publisher`, and carry them over **unchanged**.
   Resolve floating pins (`1.5.x`) to concrete versions.

   The **target version** is the only identity value that is a human decision. It is MII CalVer
   `YYYY.n.n`, not SemVer; the default is the source's version.

   **When the source and the template disagree, the source wins.** The template prescribes
   `canonical: https://www.medizininformatik-initiative.de/fhir/modul-<slug>` and
   `packageId: de.medizininformatikinitiative.kerndatensatz.<slug>`. Those are what a *new* module
   gets. A module that is already published keeps its own values — changing a published canonical
   breaks every consumer of it. Report any divergence explicitly and let a human decide; never
   normalize silently.

3. **Transfer the artefacts.** Move the FSH sources across; convert JSON/XML with `gofsh` where
   that is all the source has. IDs and URLs unchanged. **Delete the template's example artefacts
   before migrating** — `input/fsh/profiles/example-patient.fsh` and
   `input/fsh/instances/example-patient-instance.fsh` — so they cannot collide with the module's
   real examples. Verify the paths against the template you actually checked out; example
   filenames are template-version-specific.

4. **Migrate the narrative.** Move the Manteldokument content into `input/pagecontent/*.md` and
   translate Simplifier and FQL directives into IG Publisher equivalents:

   ```bash
   "$SKILL_DIR/scripts/fql-scan.sh"                    # scan input/pagecontent
   "$SKILL_DIR/scripts/fql-scan.sh" --strict           # exit 1 on any finding, for CI
   ```

   Apply the recommendation the scanner prints per finding. The mapping and the reasoning are in
   [the FQL crosswalk](references/fql-crosswalk.md); the machine-readable rules, extensible by
   hand, are [`references/fql-rules.tsv`](references/fql-rules.tsv). Ambiguous cases take
   professional judgement — when in doubt write `TODO:REVIEW` and move on. Do not invent content.

   The template ships a fixed page set, and the Manteldokument's mandatory sections map onto
   *sections within* those pages rather than onto pages of their own — see
   [the section mapping](references/migration-spec.md). **Do not create a page outside the
   template's page set** to hold one of them.

5. **Set up the bilingual pages.** English is the default; German is the translation, living at
   `input/translations/de/pagecontent/<same-filename>.md`. These **do** render. The menu is
   `input/includes/menu.xml` with a per-language mirror at
   `input/translations/de/includes/menu.xml` — not a `menu:` property in `sushi-config.yaml`, which
   would compete with it. Resource translations are `.po` supplements under
   `input/translations/de/`; check the target's own translation recipe for which resource types and
   fields actually render before investing in a supplement.

6. **Build and QA.** `sushi .`, then the IG Publisher. The target pins its toolchain in the build
   workflow's `env:` block — read the pins from there rather than from this file. Acceptance:
   `qa.txt` reports `Errors: 0` and every example validates.

7. **Report.** Write `.ai-log/migration-report.md`: the mapping table, the assumptions, every
   `TODO:REVIEW`, and the QA summary. Every open point is either addressed or explicitly marked.

8. **Open a pull request** with the report as its description. **Do not publish.** Determine the
   target branch from the module repository's own branching convention — do not assume one. The
   template previews every non-`main` branch to `gh-pages` under `branches/<branch>/` and reserves
   `main` and tags for formal publication, so a working branch gets a preview without touching the
   default branch. If the module repository has a different convention, follow that one and say
   which you followed.

## Guardrails

Binding. A migration that violates one is wrong even if it builds.

1. **Canonical URLs and IDs of existing conformance resources are never changed.**
2. **FHIR R4 (4.0.1).**
3. **No fabrication.** Every artefact and every narrative section traces to a source URL or repo
   path. Uncertainty is marked `TODO:REVIEW`, never guessed. (Note: `TODO:REVIEW` is this skill's
   marker for the migrated guide. The catalog's own marker for unfinished skill content is
   `TODO(owner):` — different things, do not mix them.)
4. **Human in the loop.** The review gates below are mandatory. The agent does not publish.
5. **Template examples are deleted before migrating**, never merged with the module's own.
6. **The default branch is not modified.** Work on a branch, deliver a pull request.
7. **Traceability.** Every step, assumption and open point is logged in
   `.ai-log/migration-report.md`.
8. **No Liquid literals in `pagecontent`, including inside HTML comments.** Jekyll evaluates
   `{% … %}` and `{{ … }}` everywhere: an invalid `{% … %}` **breaks the build hard**, and an
   unknown `{{ … }}` silently becomes an empty string and leaks into the HTML. Describe mechanisms
   in prose. This matters more on this template than on most, because the template's own files are
   full of `{{PLACEHOLDER}}` values.

## Language

Three facts, easy to conflate:

- **The target template's default language is English**, with German as the translation
  (`i18n-default-lang: en`). Verify this in the target's `sushi-config.yaml` on every run — it is
  the value most likely to move, and it was reversed once already.
- **FHIR artefact identifiers stay English** regardless.
- **A `de-DE` mismatch warning is conditional.** It fires only when the source FSH sets
  `^language = #de-DE` on resources, producing a per-resource warning (resource `de-DE` vs XHTML
  `de`). It is cosmetic — `de-DE` is a subtag of `de` — and is suppressed by adding an entry with
  a justifying comment to the module's `input/ignoreWarnings.txt`, leaving the FSH untouched
  (guardrail 1). That file uses **glob matching with `%` wildcards, not regex**, and the publisher
  emits the message in German or English depending on JVM locale, so match the locale-stable
  token: `%(de-DE)%`.

## Verification

```bash
grep -rn '{{' . --include='*.yaml' --include='*.yml' --include='*.md' --include='*.json'
sushi .
"$SKILL_DIR/scripts/fql-scan.sh" --strict
```

- Every `{{...}}` placeholder accounted for — an unreplaced one ships a bogus artefact silently.
- `sushi .` completes without error.
- IG Publisher `qa.txt` reports `Errors: 0`; every example validates.
- **Canonical URL diff against the source is empty.** This is the guardrail-1 check and the one
  that matters most; a non-empty diff is a stop, not a warning.
- `fql-scan.sh --strict` exits 0, or every remaining finding is a deliberate `TODO:REVIEW`.
- No `[UNKNOWN]` findings; an unknown directive means a rule is missing from `fql-rules.tsv`.
- The IG builds both language variants and the German pages render.
- Template example artefacts are gone.
- The default branch is unchanged, and `.ai-log/migration-report.md` exists.

## Mandatory human review gates

| Gate | After step | What is reviewed |
| --- | --- | --- |
| **A** | 3 | Canonical URL and ID preservation; artefact completeness |
| **B** | 4 | The narrative, especially any section added to satisfy the Manteldokument |
| **C** | 5 | Language handling and translation |
| **D** | before merge | Release per KDS governance (TF KDS / AG IOP / NSG) |

Gate D is organizational, not technical. Nothing publishes before it.

## Mandatory sections

The Manteldokument requires sections that the template's English-named page set does not name.
They are not missing: they live **inside** pages. The mapping, derived from
`medizininformatik-initiative/kerndatensatz-basis` — the MII's own reference module, whose page set
is identical to the template's — is in [the migration specification](references/migration-spec.md).

Two things to carry into step 4:

- **Never create a page outside the template's page set** to hold one of these sections. The page
  set and the menu are owned by the module template, and an extra page is an unlisted orphan.
- **The reference module itself is incomplete on use cases** — its researcher guidance says in as
  many words that detail will follow in a future version. A migrated module is not held to a higher
  standard than `kerndatensatz-basis`; record the gap in the report rather than inventing content
  to fill it.

## Scope and delimitation

Covers **moving an existing guide onto the template**: identity preservation, artefact transfer,
directive translation, bilingual setup, and the QA that proves it.

Does not cover, deliberately:

- **Authoring new profiles or remodelling content.** Migration is not an opportunity to change
  normative decisions.
- **Creating a module from scratch** — the module template ships its own recipe for that.
- **Translating a guide already on the template** — the module template ships an `ig-translate`
  skill. This skill only sets translation up as part of a migration.
- **Publishing.** No release, no registry entry, no package push.
- **Filling in missing domain content.** If the source lacks something, that is a `TODO:REVIEW`
  for a human, not something to write.

If a skill of this name is provided both by this catalog and locally, the local one wins.

## Provenance

Derived from `skills/mii-ig-migration` in
`forschungsgruppe-digital-health/mii-kds-sample-ig-inoffiziell` at commit
`bd38e2722a594254f3450e73c3fcdbfc2c47b7e8`.

Reworked on 2026-07-31 for a changed target template. The rework was driven by a 38-row fact
inventory; the substantive changes were that the target's default language had been reversed from
German to English, that the `hl7-ig-build` branch convention no longer exists, and that several
tool and example paths had moved. The original bundled `references/agent-manifest.yaml` was dropped
because it duplicated the guardrails and had already gone stale against them. See the repository
history for the diff.

Original licence: CC-BY-4.0, as declared by the source repository and the source skill.
`scripts/` is Apache-2.0, matching this repository's code licence.
