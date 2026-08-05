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
allowed-tools: Read Grep Glob WebFetch Bash(sushi:*) Bash(gofsh:*) Bash(bash:*) Bash(python3:*) Bash(git clone:*) Bash(git status:*) Bash(git diff:*)
metadata:
  fgdh.tier: "domain"
  fgdh.domain: "fhir-ig"
  fgdh.owner: "@msusky"
  fgdh.language: "en"
  fgdh.status: "stable"
---

# Migrating an MII KDS module IG onto the module template

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

3. **The target template.** Determine which state the module is in — discovery only here; the
   skeleton is created later, in step 3 of the procedure:
   - **Already on the module template** — a vendored `ig-template/` directory, or a `template`
     entry in `ig.ini` pointing at it. Then this is a *re-migration* or a partial one; report
     what is already in place before changing anything.
   - **Plain Simplifier project** — Simplifier files only (`.simplifier/`, `project.yaml`,
     `implementation-guides/`), no IG-Publisher scaffolding. The normal starting state.
   - **Hybrid, or on another template** — IG-Publisher files exist alongside the Simplifier
     files: an `ig.ini` naming some other template (e.g. `fhir.base.template`), `_genonce.sh`
     & co., a committed `fsh-generated/`, or a committed rendered output (which may be live
     GitHub Pages). Still a migration, not a re-migration — but inventory those files and
     record in the migration report which of them the module template replaces (`ig.ini`, the
     `_gen*`/`_update*` scripts), which carry content to transfer (`input/`, `fsh-generated/`),
     and which are retired only after Gate D (the Simplifier project files, a committed
     rendered output). List **any unrecognized top-level entry** too (real modules carry e.g. a
     `validator/` directory) with a retain/retire proposal. Deleting any of them is not this
     skill's work — list, do not remove.

   In every state, read `forschungsgruppe-digital-health/mii-kds-module-template` at the ref
   you intend to use; do not rely on this skill's description of it.

4. **Unreplaced placeholders.** The template does not build until every `{{...}}` placeholder is
   replaced, and an unreplaced one **ships a bogus artefact** rather than failing loudly. Before
   and after migrating, grep the working tree for `{{` and account for every hit. Scope the
   check: exclude `.github/**` (GitHub-Actions `${{ … }}` expressions match the pattern but are
   not placeholders), and count Simplifier directives in narrative sources as accounted — they
   are step-5 material, not placeholders. The template's own `sushi-config.yaml` header block
   enumerates the real placeholders and says which are active.

5. **The toolchain.** `sushi` and the IG Publisher must be runnable; `gofsh` is needed only if the
   source ships JSON/XML rather than FSH. Missing → report which one and **stop after step 2**:
   the inventory and the identity read are still useful, but do not create the skeleton or
   transfer artefacts on top of an unverifiable build. Do not fetch and execute a toolchain to
   get past this.

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
   `.ai-log/source-inventory.json`. When `implementation-guides/` holds **several guide trees**
   (versions × languages + shared assets — a real module ships six), apply spec §5.1a: choose the
   authoritative tree, mark parallel-language trees as harvest seeds, retain the rest.

2. **Read the module's identity — do not ask for it, and do not invent it.** From the source
   repository's `sushi-config.yaml` and `package.json` (or, absent a `sushi-config.yaml`, from
   `package.json` plus the `ImplementationGuide` resource), read `title`, `packageId`, `canonical`,
   `status`, `releaseLabel`, `license`, `dependencies` and `publisher`, and carry them over
   **unchanged**. When the two files disagree on a field, `sushi-config.yaml` wins — it is what
   the build reads; record the disagreement. When a field exists in neither file, read it from
   the generated `ImplementationGuide` resource; a value absent everywhere takes the template's
   default and is recorded at Gate A (spec §2.1). Resolve floating pins (`1.5.x`) to concrete
   versions per the registry procedure in spec §2.1 and record the pick and its evidence.

   The **target version** is the only identity value that is a human decision. It is MII CalVer
   `YYYY.n.n`, not SemVer; the default is the source's version.

   **When the source and the template disagree, the source wins.** The template prescribes
   `canonical: https://www.medizininformatik-initiative.de/fhir/modul-<slug>` and
   `packageId: de.medizininformatikinitiative.kerndatensatz.<slug>`. Those are what a *new* module
   gets. A module that is already published keeps its own values — changing a published canonical
   breaks every consumer of it. Report any divergence explicitly and let a human decide; never
   normalize silently. The same rule covers every identity value the template pre-fills as a
   **literal** rather than a placeholder — `license` above all: the template ships
   `license: CC-BY-4.0` as a literal, so no placeholder check will flag it, and MII modules
   commonly declare `CC0-1.0`. Relicensing is a human decision, never a default.

3. **Create the skeleton** (spec §5.2). The migration happens **in place**: on a working branch
   of the module's existing repository, vendor the template checked out in Preconditions 3 and
   run its first-run bootstrap — do not mint a new repository; the module's history, issues and
   consumers stay where they are (a new repository is a human decision, recorded in the
   migration report, never a default). Replace every `{{...}}` placeholder from the identity
   read in step 2. The template's CRMI `meta.profile` claims **require the
   `hl7.fhir.uv.crmi` dependency** — add it to the carried source dependencies and record the
   addition at Gate A (it is template machinery, not source identity). Then **delete the
   template's example artefacts** —
   `input/fsh/profiles/example-patient.fsh` and
   `input/fsh/instances/example-patient-instance.fsh` — so they cannot collide with the module's
   real examples. Verify the paths against the template you actually checked out; example
   filenames are template-version-specific. **Before copying the template's FSH scaffold**
   (`input/fsh/aliases.fsh`, `input/fsh/rulesets/*`), diff its `RuleSet:` and `Alias:` names
   against the module's own FSH: **module definitions win** — the module's FSH is never changed —
   so skip every colliding template file and record the skip list in the migration report. The
   template mirrors MII conventions modules commonly already carry (`aliases.fsh` with `$SCT`,
   `$v2-0203` …; `publisher`/`version`/`translation`/`meta-profile`/`test-data-label`/`license*`
   and the CapabilityStatement support rulesets); overwriting a module's `aliases.fsh` broke a
   real migration with 234 SUSHI errors. Acceptance: `sushi .` runs clean after the merge.

4. **Transfer the artefacts.** Move the FSH sources across; convert JSON/XML with `gofsh` where
   that is all the source has. IDs and URLs unchanged.

5. **Migrate the narrative.** Move the Manteldokument content into `input/pagecontent/*.md` and
   translate Simplifier and FQL directives into IG Publisher equivalents:

   ```bash
   bash "$SKILL_DIR/scripts/fql-scan.sh"                # scan (recursive; see below)
   bash "$SKILL_DIR/scripts/fql-scan.sh" --strict       # exit 1 on any finding, for CI
   ```

   The scan is recursive and, pre-migration, includes `implementation-guides/**` where a
   Simplifier project keeps its pages; it prints how many files it scanned, and a run whose
   target set is empty exits 2 — never read "nothing scanned" as "nothing found".

   Apply the recommendation the scanner prints per finding. The mapping and the reasoning are in
   [the FQL crosswalk](references/fql-crosswalk.md); the machine-readable rules, extensible by
   hand, are [`references/fql-rules.tsv`](references/fql-rules.tsv). Ambiguous cases take
   professional judgement — when in doubt write `TODO:REVIEW` and move on. Do not invent content.

   The template ships a fixed page set, and the Manteldokument's mandatory sections map onto
   *sections within* those pages rather than onto pages of their own — see
   [the section mapping](references/migration-spec.md). **Do not create a page outside the
   template's page set** to hold one of them. For modules with **more than two profiles**, route
   the per-profile narrative to `input/intro-notes/<Type>-<id>-intro.md` (German mirror under
   `input/translations/de/intro-notes/`, same filename — both render atop the artifact page;
   build-verified) and keep `profiles-and-extensions.md` as a short index — see the spec's §9
   homes table.

6. **Set up the bilingual pages.** English is the default; German is the translation, living at
   `input/translations/de/pagecontent/<same-filename>.md`. These **do** render. The menu is
   `input/includes/menu.xml` with a per-language mirror at
   `input/translations/de/includes/menu.xml` — not a `menu:` property in `sushi-config.yaml`, which
   would compete with it. Resource translations are `.po` supplements under
   `input/translations/de/`; check the target's own translation recipe for which resource types and
   fields actually render before investing in a supplement. When the source narrative is
   German-only, the German pages come first and the English defaults are produced from them —
   see *Language* below for the one sanctioned exception to the no-fabrication guardrail.
   **Page titles (breadcrumbs, table of contents, `<title>`):** the publisher *does* localize the
   titles of the `pages:` tree, and the only **publisher-level** mechanism for it is an **IG-level
   translation catalogue** `input/translations/<lang>/ImplementationGuide-<ig-id>.po` — it imports
   that file into the IG resource at load time, which is a different mechanism from the resource
   supplements above (their type restriction does not apply here). Without it, the default-language
   title is copied into every language and the `/de/` breadcrumbs stay English. (The retired
   template breadcrumb override reached the same three surfaces, but at *rendering* time by string
   replacement — see the spec's §5.5.) Generate it after `sushi .`:

   ```bash
   python3 "$SKILL_DIR/scripts/gen-page-title-po.py" \
     fsh-generated/resources/ImplementationGuide-<ig-id>.json \
     .ai-log/menu-titles-de.txt \
     de input/translations/de/ImplementationGuide-<ig-id>.po
   ```

   One `#: ImplementationGuide.definition.page.title` unit per **distinct title in the `pages:`
   tree**, and the authoritative source of that set is the **SUSHI-generated ImplementationGuide
   resource** — not the menus. It carries the whole tree including the root `toc.html` page and the
   pages that are not menu entries. Use the two menus only as a **translation seed**: pair the
   labels of `input/includes/menu.xml` and `input/translations/de/includes/menu.xml` by `href` into
   an `English Title => Deutscher Titel` seed file (a working file under `.ai-log/`, not a committed
   artefact — pass `-` when there is deliberately no seed; a seed *path* that does not resolve is a
   setup error and the script stops rather than emitting an untranslated catalogue). Titles the seed
   does not cover are emitted with an **empty `msgstr`** — gettext reads that as untranslated and
   the publisher falls back to English for exactly those entries — and the script names every one of
   them; carry them into the report's ② review queue and have them translated. Two pages sharing one
   English title share **one** unit (gettext keys by `msgid`) and cannot get different translations;
   the script reports every such collision. **Regenerating is non-destructive:** units the generator
   does not own — the IG's own `title`/`description`/`publisher`, per-artifact units, a gettext
   header entry — are written back verbatim, and an existing non-empty `msgstr` wins over the seed,
   so hand translations survive. Change a translation in the `.po`, not in the seed.
   **Precondition:** the target language must appear in a **`translation-sources`** parameter as
   well as in `i18n-lang`; a language declared only in `i18n-lang` has its `.po` files silently
   ignored, so verify this in `sushi-config.yaml` before concluding the catalogue does not work.
   Modules generated from module template **v0.5.0** — the one release that shipped the template
   breadcrumb override plus `input/includes/breadcrumb-titles-de.txt` — should add the catalogue and
   drop the override; see the spec's §5.5. The old mapping file is a usable seed, but not a complete
   one (it was generated from the menus and omits the non-menu pages).

7. **Build and QA.** `sushi .`, then the IG Publisher. The target pins its toolchain in the build
   workflow's `env:` block — read the pins from there rather than from this file. Acceptance:
   `qa.txt` reports `Errors: 0` and every example validates. Then run the **same-module
   verification** with the catalog's `fhir-ig-analysis` skill (measure the unmigrated source and
   the migrated tree, then compare — same `packageId` triggers the verification report
   automatically; the SOURCE is the first input): identity fields, the published artifact set and
   the canonical URLs must all read **IDENTISCH**, and the narrative per-language table goes into
   the migration report's QA triage. A DIVERGIERT there is a stop, not a warning.

8. **Report.** Write `.ai-log/migration-report.md` **from
   [the report template](references/migration-report-template.md)** — it is built around three
   reviewer queues (① decide, ② review, ③ triage) so the report is a work instrument, not a
   protocol: every open decision, every `TODO:REVIEW`, and every QA finding lands in exactly one
   queue with a concrete next action and an owner, QA provenance requires proof (build the
   unmigrated source to claim "pre-existing"), and the L0 box + mini-glossary keep it readable
   for people new to FHIR IGs. Every open point is either addressed or explicitly queued.

9. **Open a pull request** with the report as its description. **Do not publish.** Determine the
   target branch from the module repository's own branching convention — **discover it, do not
   assume it**: the default branch, the bases of previously merged pull requests, and
   CONTRIBUTING/README are the evidence. The template previews every non-`main` branch to
   `gh-pages` under `branches/<branch>/` and reserves `main` and tags for formal publication, so
   a working branch gets a preview without touching the default branch. If the module repository
   has a different convention, follow that one and say which you followed — and if its
   conventional PR base is itself the publication branch (for example GitHub Pages served from
   it), say so in the pull request description and at Gate D: there, merging publishes.

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
- **A German-only source inverts the direction — and that is this skill's to handle.** The normal
  KDS case: the source's entire narrative is German, while the target's default language is
  English, so the migration makes the German text the *translation* of English pages that do not
  yet exist. Transfer the source text into `input/translations/de/pagecontent/` (it is the
  translation now) and produce the default-language `input/pagecontent/*.md` as **machine
  translations of the German source, every page marked `TODO:REVIEW`**, reviewed at Gate C. This
  is the one sanctioned exception to guardrail 3 (no fabrication): the translation traces to the
  source page it renders, and the German text stays the authoritative reference until Gate C
  signs the English pages off. A top-level `language:` value in the source's `sushi-config.yaml`
  is part of its old single-language setup, not identity — do not carry it into the template's
  i18n configuration.

## Verification

```bash
grep -rn '{{' . --include='*.yaml' --include='*.yml' --include='*.md' --include='*.json' | grep -v '\${{'
sushi .
bash "$SKILL_DIR/scripts/fql-scan.sh" --strict
```

- Every `{{...}}` placeholder accounted for — an unreplaced one ships a bogus artefact silently.
- `sushi .` completes without error.
- IG Publisher `qa.txt` reports `Errors: 0`; every example validates.
- **Canonical URL diff against the source is empty.** This is the guardrail-1 check and the one
  that matters most; a non-empty diff is a stop, not a warning. The mechanical form of this and
  the two checks below is `fhir-ig-analysis`' same-module comparison (step 7) — its Befund block
  must read IDENTISCH for identity, published artifact set, and canonical URLs.
- **The `license` (and every other identity value) diff against the source is empty**, or the
  divergence is reported and human-decided — never silently normalized to a template value.
- `fql-scan.sh --strict` exits 0 **and reports a non-zero scanned-file count**, or every
  remaining finding is a deliberate `TODO:REVIEW`. An empty target set exits 2 and is not a pass.
- No `[UNKNOWN]` findings; an unknown directive means a rule is missing from `fql-rules.tsv`.
- The IG builds both language variants and the German pages render.
- `input/translations/de/ImplementationGuide-<ig-id>.po` exists, has a
  `#: ImplementationGuide.definition.page.title` unit for **every** distinct title in the `pages:`
  tree, and any empty `msgstr` is in the report's ② review queue. `de` appears in a
  `translation-sources` parameter — not only in `i18n-lang`. Confirm on the built output, not on
  the source: a `/de/` page's breadcrumb renders German.
- Template example artefacts are gone.
- The default branch is unchanged, and `.ai-log/migration-report.md` exists.

## Mandatory human review gates

| Gate | After step | What is reviewed |
| --- | --- | --- |
| **A** | 4 | Canonical URL, ID **and licence/identity** preservation; artefact completeness |
| **B** | 5 | The narrative, especially any section added to satisfy the Manteldokument |
| **C** | 6 | Language handling and translation, including machine-translated default pages |
| **D** | before merge | Release per KDS governance (TF KDS / AG IOP / NSG) |

Gate D is organizational, not technical. Nothing publishes before it.

## Mandatory sections

The Manteldokument requires sections that the template's English-named page set does not name.
They are not missing: they live **inside** pages. The mapping, derived from
`medizininformatik-initiative/kerndatensatz-basis` — the MII's own reference module, whose page set
matches the template's except for two template-only pages (`security-and-privacy`,
`rendering-artifacts`) — is in [the migration specification](references/migration-spec.md).

Two things to carry into step 5:

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

Revised on 2026-08-01 after the skill's first real-task exercise (a dry run against
`kerndatensatz-dokument`): the identity read-list gained `license` and a
sushi-config-wins conflict rule; target-state discovery gained the hybrid/other-template state;
skeleton creation became an explicit in-place procedure step; the German-only-source language
inversion, the branch-convention discovery recipe, and the scoped placeholder check were added;
`fql-scan.sh` became recursive with an empty-target failure. The dry-run findings live in the
`mii-kds-dokument-ig-inoffiziell` sandbox under `docs/reports/dry-run-2026-07-31/`.

Revised on 2026-08-02 after the first full migration (Dokument, steps 1–7 incl. build): step 8
now prescribes the bundled report template (three reviewer queues, proof-backed QA provenance);
the crosswalk fixed the nonexistent `-xml` fragment (it is `-xml-html`; one bad include fails the
whole Jekyll run), prefers artefact-page links over inline serializations/tabs, prescribes
float-safe width-capped image markup, warns that kramdown IAL heading ids are not applied, and
sanctions mechanically *extracted* (never invented) tables for FQL projections no publisher view
renders; spec §9 gained the Datensatz/logical-models split, the Suchparameter page, and the
example-serialization homes.

Revised on 2026-08-05 to retire a false claim: earlier revisions stated that the IG Publisher cannot
localize the titles of the `pages:` tree and that an `ImplementationGuide-<id>.po` is ignored. It is
not — a catalogue in a `translation-sources` folder is imported into the IG resource at load time,
and its `#: ImplementationGuide.definition.page.title` units localize breadcrumbs, the
table-of-contents page body and the page `<title>`. Evidence, in the order it carries weight: our
own build on IG Publisher **2.2.11** (the migrated Dokument guide, breadcrumb override deleted, 23
units supplied — German `/de/` breadcrumbs incl. the root *Inhaltsverzeichnis*, German TOC body,
German `<title>`, differing `titlelang` per language in `temp/pages/_data/pages.json`, build health
unchanged); the HL7 reference guide `FHIR/multi-lang-test-ig` (live build by publisher 2.0.13) with
`/fr/` as a controlled negative because it is missing from `translation-sources`; and prior art in
our own organisation — both MII template repos already carry such a catalogue on `dev`, citing the
MII's `kerndatensatz-basis` module, verified 2026-07-30. Step 6 and spec §5.5 now prescribe the
catalogue, `scripts/gen-page-title-po.py` generates it non-destructively (hand-added and
hand-translated units survive regeneration), and the record of the breadcrumb override was corrected:
it shipped in **one** template release, v0.5.0, and is being retired. Deliberately **not** claimed,
because it was not tested on 2.2.11: the navigation menu, and the IG's own
description/publisher/name and artifact names.

Original licence: CC-BY-4.0, as declared by the source repository and the source skill.
`scripts/` is Apache-2.0, matching this repository's code licence.

Promoted to `stable` on 2026-08-05: two full real-task migrations (Dokument, Person), both passing the same-module verification (identity, published artifact set, canonical URLs all IDENTISCH) with baseline-proven QA. The trigger set in
[references/triggers.md](references/triggers.md) was exercised by those runs.
