# Migration specification — Simplifier MII KDS module IG → MII KDS module template

The full procedure, with an acceptance criterion per step. `SKILL.md` is the operating summary;
this is the normative detail.

Vendor-neutral: it is a task specification, applicable to any tool-capable agent with the
capabilities in §3. The agent **supports and partly automates** the migration; final human review
is mandatory and the agent never publishes.

**Verify the target against the target, not against this file.** Every statement here about the
MII KDS module template was true of the template when this skill was reworked (2026-07-31). The
template moves. Where this file and the checked-out template disagree, the template wins, and
saying so in the migration report is part of the job.

---

## 1. Objective

Move a source guide into the target template's format, structurally conformant to the MII KDS
Meta-Manteldokument (current edition) and to the HL7 IG best practices, bilingual with **English as
the default language and German as the translation**.

That language direction is the single most important thing to re-check on every run. It was
previously German-default, and the reversal is not visible from the source guide.

## 2. Inputs

**Provided by a human — these cannot be derived:**

- `SOURCE_RENDERED_IG_URL` — URL of the rendered Simplifier IG.
- `SOURCE_REPO_URL` — URL of its source GitHub repository.
- **Target `version`** — MII CalVer `YYYY.n.n`, **not** SemVer. The only module-identifying value
  that is a human decision; the default is the source's version.

**Not provided — read from the source:** every other module-identifying value. The agent reads them
and carries them over unchanged. It does not invent them and does not ask.

### 2.1 Module identity — where each value comes from

Read from the `sushi-config.yaml` and `package.json` at the root of `SOURCE_REPO_URL` (§2). Absent a `sushi-config.yaml`, read
`package.json` plus the `ImplementationGuide` resource. **When both files exist and disagree on a
field, `sushi-config.yaml` wins** — it is what the build reads; record the disagreement in the
migration report. (Real case: a `package.json` whose `canonical` carries the IG-resource URL
`…/ImplementationGuide/<id>` instead of the canonical base.)

| Field | Read from | Human input? | Written to |
| --- | --- | --- | --- |
| `id` | `sushi-config: id` | derived — the template pattern `mii-ig-<slug>` applies only when the source has none | `sushi-config: id` |
| module title | `sushi-config: title` / `package.json: title` | derived | `title`, menu, README |
| module abbreviation | existing FSH artefact names (`MII_PR_<Module>_…`) | derived — names stay | FSH `name` / `title` |
| `packageId` | `package.json: name` / `sushi-config: packageId` | derived | `sushi-config: packageId` |
| `canonical` | `sushi-config: canonical` / `package.json: canonical` | derived — **never change** | `sushi-config: canonical` |
| `version` | `sushi-config` / `package.json: version` | **yes — confirm or bump** | `sushi-config: version`, release tag |
| `status` / `releaseLabel` | `sushi-config` | derived (confirm) | `sushi-config` |
| `license` | `sushi-config: license` / `package.json: license` | derived — **never change silently** (§2.2) | `sushi-config: license` |
| `copyrightYear` | `sushi-config: copyrightYear` | derived — fills the template's `{{COPYRIGHT_START_YEAR}}` | `sushi-config: copyrightYear` |
| `dependencies` | `sushi-config: dependencies` (+ `package.json`) | derived — resolve `.x` pins | `sushi-config: dependencies` |
| `publisher` / `contact` | `sushi-config: publisher` | derived | `sushi-config: publisher` |

**Third-tier fallback:** when a field exists in neither `sushi-config.yaml` nor `package.json`,
read it from the generated `ImplementationGuide` resource
(`fsh-generated/resources/ImplementationGuide-*.json`) — real modules lack `id` there
(kerndatensatz-labor) or `title` and `license` (kerndatensatzmodul-person, whose `package.json`
also carries no canonical). A value absent everywhere takes the **template default** and is
recorded as a Gate-A note — never adopted silently.

**Resolving floating pins** (`1.5.x`, `2025.0.x`): query the FHIR package registry
(`https://packages.fhir.org/<packageId>` or `packages.simplifier.net`) and pick the **highest
release matching the floating pattern**; when the source's CI logs or package cache prove which
concrete version the last build actually used, prefer that evidence. Record the chosen version
AND its evidence source in the migration report (Gate A) — the pick changes validation behavior.

A top-level `language:` value in the source is **not** identity: it belongs to the source's old
single-language setup. The target's language configuration is the template's i18n mechanism
(§4.2, §5.5) — do not carry `language:` over into it.

### 2.2 When the source and the template disagree

The template prescribes a canonical and a package id derived from a module slug:

```text
canonical:  https://www.medizininformatik-initiative.de/fhir/modul-<slug>
packageId:  de.medizininformatikinitiative.kerndatensatz.<slug>
```

**Those are what a new module gets. A module that is already published keeps its own values.**
Guardrail 1 wins: changing a published canonical breaks every consumer that resolves it, and it is
the one mistake in a migration that cannot be quietly fixed later.

So: report the divergence explicitly, in the migration report and at Gate A, and let a human
decide. Never normalize silently, and never treat the template's placeholder pattern as an
instruction to rewrite existing identity.

**The same rule covers every identity value the template pre-fills as a literal rather than a
`{{...}}` placeholder — `license` above all.** The template ships `license: CC-BY-4.0` as a
literal, so the placeholder gate in §2.3 never touches it, and MII modules commonly declare
`CC0-1.0`. A migration that leaves the template's licence in place has silently relicensed
published content. Read the source's `license`, carry it over, and treat any divergence exactly
like the canonical: report it, raise it at Gate A, let a human decide.

### 2.3 Placeholders

The template does not build until every `{{...}}` placeholder is replaced, and an unreplaced
placeholder **ships a bogus artefact** rather than failing loudly — for example an invalid
terminology code, which no build error will catch.

The template's `sushi-config.yaml` opens with a header block enumerating its placeholders and
marking which are active on lines the build reads today. Read that block in the checked-out
template; do not work from a list in this file, because the set changes with the template.

Placeholders occur across `sushi-config.yaml`, `ig.ini`, the publication request, the QC rules, the
publication workflow, the narrative pages, the FSH sources including the rulesets library, the
resources directory, and the tests. Filenames are never placeholders — replace contents only.

## 3. Required capabilities

Abstract, so any tool-capable agent can be mapped onto them:

- **Web fetch and extraction** — read and structure the rendered source IG.
- **Repository read** — clone or read the source repository, read-only.
- **File write** — into a working branch of the target repository.
- **Shell execution** — `sushi`, the IG Publisher, optionally `gofsh`.
- **Terminology validation** — optional, against a FHIR terminology server.
- **Version control** — branch and pull request. **No direct push to the default branch.**

`SKILL.md` declares a conservative `allowed-tools` value. That field is experimental and support
varies between agents, so **this list is the normative statement** of what the skill needs; treat
`allowed-tools` as a convenience rather than the contract.

## 4. Guardrails

1. **Canonical URLs and IDs** of existing conformance resources are **not** changed.
2. **Language.** English is the target's default (`i18n-default-lang: en`); German is the
   translation. FHIR artefact identifiers stay English regardless. Verify the parameter in the
   checked-out template on every run. For a German-only source this **inverts the direction**:
   the German text becomes the translation, and the English default pages are produced as
   machine translations of it, each marked `TODO:REVIEW` and reviewed at Gate C — the one
   sanctioned exception to guardrail 4, because every translated page traces to the source page
   it renders.
3. **FHIR version:** R4 (4.0.1).
4. **No fabrication.** Every migrated artefact and narrative section traces to a source URL or
   repository path. Uncertainty is marked `TODO:REVIEW`, never guessed.
5. **Mandatory sections** required by the Manteldokument must be present. See §9 — the mapping onto
   the template's page set is an open question, so this is currently a Gate B check by hand.
6. **Human in the loop.** The gates in §6 are mandatory. The agent does not publish.
7. **Traceability.** Every step, assumption and open point is logged in
   `.ai-log/migration-report.md`.
8. **Template examples are deleted before migrating** — not merged with the module's real examples.
9. **The default branch is not modified.** Work on a branch; deliver a pull request.

### 4.1 The conditional `de-DE` warning

If the source FSH sets `^language = #de-DE` on resources, the IG Publisher emits a per-resource
language-mismatch warning (resource `de-DE` versus XHTML `de`). It is cosmetic — under BCP 47,
`de-DE` is a subtag of `de` — and an artefact of the i18n feature.

Suppress it by adding an entry with a justifying comment to the module's
`input/ignoreWarnings.txt`, leaving the FSH untouched (guardrail 1). Two details that make the
difference between working and not:

- That file uses **glob matching with `%` wildcards, not regex** (`%text%` = contains,
  case-insensitive).
- The publisher emits the message in German or English depending on JVM locale, so match the
  locale-stable token: `%(de-DE)%`.

## 5. Workflow

### 5.1 Inventory the source

Extract from `SOURCE_RENDERED_IG_URL` and `SOURCE_REPO_URL` the artefact list (profiles,
extensions, value sets, code systems, capability statements, examples) and the narrative structure.

**If the rendered IG cannot be mechanically extracted** — Simplifier project pages and their
guide listings render client-side, so a non-browser agent may find no guide content even at a
URL that returns 200 — derive the narrative structure from the repository instead
(`implementation-guides/**/toc.yaml` and `*.page.md`), mark the rendered-IG cross-check
`TODO:REVIEW` in the inventory, and have Gate B verify against the rendering by hand.

→ Output: `.ai-log/source-inventory.json`.
→ **Acceptance:** the inventory is complete and every entry carries its source path.

### 5.1a Multi-guide Simplifier projects

Real modules ship **several** guide trees under `implementation-guides/` — versions × languages
plus shared assets (kerndatensatzmodul-person: `1.x-DE`, `1.x-EN`, `2024.x-DE`, `2024.x-EN`,
`2025.x-DE`, `Common`). One migration, four dispositions:

1. **Authoritative tree** — the highest-version guide in the module's narrative (source) language.
   Confirm against the rendered IG when reachable; record the choice and the trees' versions in
   the inventory (Gate B reviews it). Steps 5.4/5.5 operate on this tree only.
2. **Parallel-language trees** are **harvest seeds** for the target default language — hand over
   to the translation skill's harvest mode instead of machine-translating from scratch. **Stale-
   version caveat:** when the parallel tree's version lags the authoritative one (person: EN =
   2024.x vs DE = 2025.x), every harvested page gets a per-page `TODO:REVIEW` naming both
   versions; currency is checked at Gate C.
3. **Historical version trees** and shared-asset trees (`Common`): retained unchanged, Gate-D
   retirement set. Assets the authoritative tree references are transferred in step 5.4.
4. **Unrecognized top-level directories** anywhere in the repository (e.g. `validator/`): listed
   in the report with a retain/retire proposal — never silently kept or dropped.

→ **Acceptance:** the inventory records every guide tree with name, language, version, page count
and disposition.

### 5.2 Create the skeleton

Create the skeleton **in place**: on a working branch of the module's existing repository, vendor
the template and run its first-run bootstrap — do not mint a new repository; the module's history,
issues and consumers stay where they are. (A new repository is a human decision, recorded in the
migration report, never a default.) Replace the placeholders (§2.3) using the identity read in
§2.1 — the licence per §2.2 is carried from the source, not left at the template's literal.
**Delete the template's example artefacts** — at the time of writing
`input/fsh/profiles/example-patient.fsh` and
`input/fsh/instances/example-patient-instance.fsh`; confirm the paths in the template you actually
checked out. **Collision rule for the FSH scaffold:** diff the template's `RuleSet:`/`Alias:`
names against the module's FSH before copying; module definitions win, colliding template files
are skipped, the skip list goes into the report (§ SKILL.md step 3 has the known collision set).

→ **Acceptance:** `sushi .` runs without error; no template examples remain; no `{{` left
unaccounted for.

### 5.3 Transfer the artefacts

Move the FSH sources from the source repository. Where only JSON/XML exists, convert with `gofsh`.
IDs and URLs unchanged.

→ **Acceptance:** the SUSHI build produces every artefact, and **the canonical URL diff against the
source is empty.**

### 5.4 Migrate the narrative

Move the Manteldokument content into the page set — **which language goes where is decided by
§4.2**: when the source narrative is not in the target's default language (the normal KDS case:
German source, English default), the source text goes to
`input/translations/<source-lang>/pagecontent/` and the default-language `input/pagecontent/*.md`
are produced as machine translations of it, every page marked `TODO:REVIEW` for Gate C.
Translate Simplifier and FQL directives into IG Publisher equivalents:

```bash
bash "$SKILL_DIR/scripts/fql-scan.sh"            # recursive; pre-migration includes implementation-guides/**
bash "$SKILL_DIR/scripts/fql-scan.sh" --strict
```

The scanner prints its scanned-file count and exits 2 on an empty target set — "nothing scanned"
is never "nothing found".

Apply the recommendation per finding; the mapping is in `references/fql-crosswalk.md` and the rules
in `references/fql-rules.tsv`. Ambiguous cases take professional judgement; when in doubt mark
`TODO:REVIEW` (guardrail 4).

Respect the Liquid build guard: no `{% … %}` or `{{ … }}` literals in `pagecontent`, including
inside HTML comments. An invalid `{% … %}` breaks the build hard; an unknown `{{ … }}` silently
empties and leaks into the HTML.

→ **Acceptance:** every page of the template's set exists; each mandatory Manteldokument section has
its home per the mapping in §9, and any the source did not supply is listed in the report as a gap
rather than silently absent; the scan reports no `[UNKNOWN]` and no unintentionally remaining
directives.

### 5.5 Bilingual setup

- **Narrative pages.** The German translation is a same-named file under
  `input/translations/de/pagecontent/`. These **do** render. (An older convention used sibling files
  `input/pagecontent/<name>-<lang>.md` and reported that pages did not translate. Both are
  obsolete.)
- **Menu.** `input/includes/menu.xml`, with a per-language mirror at
  `input/translations/de/includes/menu.xml`. A `menu:` property in `sushi-config.yaml` generates a
  single untranslatable menu that competes with this and must not be used.
- **Resources.** `.po` supplements under `input/translations/de/`. The publisher generates
  templates for every resource on each build; copy the ones you need and translate the `msgstr`
  lines. **Check the template's own translation recipe for which resource types and fields actually
  render before investing in a supplement** — several do not (ValueSet supplements among them), and
  a supplement for one of those is silently ignored.
- **Page titles.** `input/translations/<lang>/ImplementationGuide-<ig-id>.po`, one
  `#: ImplementationGuide.definition.page.title` unit per distinct title of the `pages:` tree.
  Generate it after `sushi .`, seeded from the two menus:

  ```bash
  python3 "$SKILL_DIR/scripts/gen-page-title-po.py" \
    fsh-generated/resources/ImplementationGuide-<ig-id>.json \
    .ai-log/menu-titles-de.txt \
    de input/translations/de/ImplementationGuide-<ig-id>.po
  ```

  Resolve `SKILL_DIR` to the directory holding the skill's `SKILL.md` first; a bare
  `scripts/gen-page-title-po.py` silently runs the *project's* same-named file if it has one.
  See *Mechanism* below — this is **not** a resource supplement and is not subject to the
  supplement type restriction.

  **Regenerating is non-destructive.** The same catalogue is also where the IG's own
  `title`/`description`/`publisher` units, per-artifact units and a gettext header entry live; the
  generator parses an existing file, writes those back verbatim, and lets an existing non-empty
  `msgstr` win over the seed, so a hand translation survives. It reports what it carried over, what
  it dropped (a unit whose title left the `pages:` tree), and every collision where two pages share
  one English title — gettext keys by `msgid`, so those share one unit and cannot be translated
  apart. A seed path that cannot be read is a setup error (exit 2, nothing written); pass `-` to say
  deliberately that there is no seed.

**Mechanism.** Each bullet below carries its own basis; do not lend one bullet's basis to another.

- **Observed on our own build** (IG Publisher 2.2.11, our pin, on the migrated MII KDS *Dokument*
  guide with the breadcrumb override deleted and 23 `page.title` units supplied): the `/de/`
  breadcrumbs render German down to the root label *Inhaltsverzeichnis*, the table-of-contents page
  body renders German, the browser `<title>` renders German, and `temp/pages/_data/pages.json`
  carries a differing `titlelang` per language for all 23 pages (none before). Build health was
  unchanged (SUSHI 0 errors, `qa.txt` at the established `err=7` baseline).
- **Not observed, not tested** on 2.2.11: the left-hand **navigation menu**, and the IG's own
  `description`, `publisher`, `name` and artifact names/descriptions. Do not claim them. Menus have
  their own per-language file (`input/translations/<lang>/includes/menu.xml`) in any case.
- **Read from the publisher source, not proven by our build:** an `ImplementationGuide-<id>.po`
  found under a folder listed in a **`translation-sources`** parameter is imported into the IG
  resource at load time (`PublisherIGLoader` → `importFromTranslations`), and the renderer reads the
  resulting translation extensions into its per-language `titlelang`/`breadcrumblang` maps; this is
  a different code path from resource supplements, whose `TRANSLATION_SUPPLEMENT_RESOURCE_TYPES`
  list (StructureDefinition, CodeSystem, Questionnaire) does not constrain it. This explains the
  observation; it is not the evidence for it. (Over-trusting exactly that constant is what produced
  the earlier false claim that page titles cannot be translated at all — a source constant is a
  hypothesis until a build confirms the outcome.)
- **Corroboration outside our build:** the HL7 reference guide `FHIR/multi-lang-test-ig` (live build
  produced by publisher **2.0.13**, not our pin) renders localized breadcrumbs under `/es/` and
  `/nl/` while `/fr/` — declared in `i18n-lang` but absent from `translation-sources` — is *not*
  localized, a controlled negative for the footgun below. Inside our own organisation, both MII
  template repos already ship such a catalogue on their `dev` branch, and `ig-template-mii-kds`
  records the same mechanism in use by the MII's own `kerndatensatz-basis` module
  (`ImplementationGuide-mii-ig-base.po`), verified 2026-07-30.

Two consequences worth knowing: the authoritative title set is the **SUSHI-generated
ImplementationGuide resource** (it holds the whole tree including the root `toc.html` page and the
pages that are not menu entries — in the Dokument guide the menus covered only 19 of 23 titles), and
an empty `msgstr` is treated by gettext as untranslated, so the publisher falls back to the default
language for that entry alone. **Footgun:** a language declared in `i18n-lang` but absent from every
`translation-sources` parameter has its `.po` files silently ignored — that, and not a publisher
limitation, is the usual cause of English breadcrumbs on a `/de/` page.

**Migration path for existing modules.** Exactly one module-template release — **v0.5.0** — shipped
a template override of `includes/fragment-pagebegin.html` plus
`input/includes/breadcrumb-titles-de.txt`, which rewrite the *rendered* breadcrumb HTML by string
replacement. That override was a misdiagnosis of the publisher's behaviour (it was introduced on the
template's `main` branch, bypassing `dev`, which never carried it) and is being retired; v0.4.0 and
earlier never had it, and the template's `dev` branch carries the correct `.po` instead. So the
catalogue is the only *publisher-level* mechanism for page titles — the override was a second,
*rendering-time* one, and it is going away. A module generated from v0.5.0 should therefore **add an
`ImplementationGuide-<id>.po` and drop the override** in the same change; leaving the override in
place while re-vendoring a newer template reverts its German breadcrumbs to English. The old mapping
file's content is a valid seed for the `.po`; it is not a complete one, because it was generated
from the menus and therefore omits the non-menu pages.

→ **Acceptance:** the IG builds both language variants; translated element texts appear on the
translated artefact pages; no ignored `.po` files were created;
`input/translations/<lang>/ImplementationGuide-<ig-id>.po` exists and carries a page-title unit for
**every** distinct title in the `pages:` tree (the generated ImplementationGuide resource is the
reference set — a unit count below it is a defect), with every empty `msgstr` listed in the report's
② review queue rather than left silent; the target language is present in a `translation-sources`
parameter as well as in `i18n-lang`; and the German breadcrumb is confirmed **on the built output**
(a `/de/` page renders e.g. `Inhaltsverzeichnis / …`), not inferred from the source.

### 5.6 Build and QA

Run `sushi .`, then the IG Publisher. The target pins the publisher, SUSHI and Jekyll versions in
its build workflow's `env:` block, the publisher jar additionally by SHA-256 — read the pins from
there. A missing Jekyll on the runner surfaces as `Cannot run program "jekyll"`.

→ **Acceptance:** `qa.txt` reports `Errors: 0`; every example validates; the same-module
comparison of the catalog's `fhir-ig-analysis` skill (source first, migrated tree second — equal
`packageId` triggers it) reads **IDENTISCH** for identity fields, published artifact set and
canonical URLs, and its narrative per-language table is carried into the report's QA triage.

### 5.7 Report

Write `.ai-log/migration-report.md`: mapping table, assumptions, the `TODO:REVIEW` list, the QA
summary, and any source-versus-template identity divergence from §2.2.

→ **Acceptance:** every open point is addressed or explicitly marked.

### 5.8 Pull request

Open a pull request with the report as its description. **Do not publish.**

Determine the target branch from the module repository's own convention — **discover it, do not
assume it**: the default branch, the bases of previously merged pull requests, and
CONTRIBUTING/README are the evidence. The template previews every non-`main` branch to `gh-pages`
under `branches/<branch>/` and reserves `main` and tags for formal publication, so a working
branch gets a rendered preview without touching the default branch. If the module repository uses
a different convention, follow it and record which you followed — and when the discovered PR base
is itself the publication branch (for example GitHub Pages served from it), say so in the pull
request description and at Gate D: there, merging publishes.

## 6. Mandatory human review gates

| Gate | After | Reviewed |
| --- | --- | --- |
| **A** | §5.3 | Canonical URL and ID preservation; artefact completeness; any identity divergence per §2.2 |
| **B** | §5.4 | The narrative, especially sections added to satisfy the Manteldokument, and section completeness by hand while §9 is open |
| **C** | §5.5 | Language handling and translation |
| **D** | before merge | Release per KDS governance (TF KDS / AG IOP / NSG) |

Gate D is organizational. Nothing publishes before it.

## 7. Definition of done

`sushi .` and the IG Publisher build cleanly (`Errors: 0`); the Manteldokument crosswalk is
complete; the `fhir-ig-analysis` same-module verification reads IDENTISCH (identity, published
artifact set, canonical URLs); the language configuration is English-default with a
German translation; every placeholder is replaced; template examples are removed; the default
branch is unchanged; a pull request carries `migration-report.md`; all review gates are signed off.

## 8. Non-goals

No content remodelling. No change to normative decisions. No independent publication. No invention
of missing domain content.

## 9. Mandatory-section mapping

The Manteldokument requires sections whose names do not appear in the template's page set. **They
map onto sections *within* pages, not onto pages of their own.** That is why the page set looks
like it is missing them and is not.

The mapping below is derived from `medizininformatik-initiative/kerndatensatz-basis` — the MII's own
reference module, whose `input/pagecontent/` set matches the template's except for two
template-only pages (`security-and-privacy.md`, `rendering-artifacts.md`, which basis lacks) and
one basis-only file (`ImplementationGuide-mii-ig-base.md`). It is evidence about what the MII
actually does, not an interpretation of the Manteldokument's wording. The two template-only pages
also mean the reference module itself scores 10/11 on the analysis skill's mandatory-page list —
expect the same of any module whose page set predates them.

| Manteldokument section | Where it lives | Evidence |
| --- | --- | --- |
| **Bezüge zu anderen Modulen** | **`implementer-guidance.md` is the primary home** for the substance: module dependencies, cross-module references, and any compared/derived-profile discussion. `index.md` § *Related guides* carries only a **short link list** (the template's `TODO:` there asks for names, not prose). The machine-readable form is `dependencies` in `sushi-config.yaml`. Learned on the first full migration's review: routing the context *prose* onto `index.md` makes the landing page read as misplaced — the index stays lean. | basis `implementer-guidance.md` lists "Module dependencies and cross-references"; template `index.md` |
| **Referenzen** | **`implementer-guidance.md`** for reference *discussion* (compared specifications, alignment notes); `index.md` § *Related guides* only as a short link list of external guides and the FHIR IG Registry; `downloads.md` for package and artefact references; inline artefact links throughout the narrative | basis `implementer-guidance.md`; template `index.md`; basis `downloads.md` |
| **Anwendungsfälle / Szenarien** | `guidance.md`, which routes to `implementer-guidance.md` and `researcher-guidance.md`; `general-requirements.md`, which frames the requirements in terms of MII use cases; `examples.md` for the concrete scenarios. Scenario *narratives* (use-case descriptions with diagrams) default to `general-requirements.md` per the basis evidence; `implementer-guidance.md` is the better home when the scenarios are written as implementation instructions. Either way, record the choice as `TODO:REVIEW` for Gate B — reviewers reasonably disagree on this one. | basis `general-requirements.md` (German) refers to "die Anwendungsfälle der Medizininformatik-Initiative"; basis `researcher-guidance.md` covers identifying data elements for a research question |

Further recurring source-section homes, learned on the Dokument migration (same rule: sections
within existing pages, never new pages):

| Source section | Where it lives | Why |
| --- | --- | --- |
| **Datensatz / Informationsmodell page** (dataset narrative + logical-model rendering) | split: the narrative on `datasets-and-descriptions.md`, the logical-model rendering (`-snapshot` include) on `logical-models.md`, cross-linked | the template ships **both** pages; putting everything on one leaves the other an empty stub that reads as missing content |
| **Per-profile Suchparameter section** | `search-parameters-and-operations.md`, with a link back from the profile's section on `profiles-and-extensions.md` | the template has a dedicated page for it; a stub next to a filled profile page confuses readers |
| **Per-profile example serializations** (inline XML/JSON, tabs) | links to the example artefact pages (whose tabs render the serializations); `examples.md` lists all examples | inlined dumps duplicate the artefact pages and bloat the narrative — see the crosswalk's tabs rule |
| **Per-profile narrative pages, N > 2 profiles** | one `input/intro-notes/<Type>-<id>-intro.md` per artifact, German mirror at `input/translations/de/intro-notes/<same filename>` — **both render atop the respective artifact page** (verified on a real build: no cross-language leakage); `profiles-and-extensions.md` becomes a short per-profile index with links | the template wires `path-pages: input/intro-notes`; five per-profile pages ≈ 4,400 words (kerndatensatzmodul-person) would make one section-per-profile page unreadable |

### Two consequences for step 5.4

**Never create a page outside the template's page set** to hold one of these sections. The page set
and the menu are owned by the module template (`pages:` plus `input/includes/menu.xml` and its
per-language mirror); an extra page is an unlisted orphan that the QA flags and that no menu
reaches.

**The reference module is itself incomplete on use cases.** `kerndatensatz-basis` opens its
researcher guidance with a note that detailed guidance "will be added in a future version of this
implementation guide". A migrated module therefore cannot be held to a higher standard than the
reference, and guardrail 4 forbids writing the missing content. Record the gap in the migration
report and raise it at Gate B; do not fill it.

So §5.4's acceptance criterion is: each of the three sections has a **named home** in the page set
per the table above, and any that the source guide did not supply is listed in the report as a gap
rather than silently absent.

## Appendix — vendor-neutral prompt scaffold

> **Role:** You are a migration assistant for FHIR Implementation Guides.
> **Task:** Move the source guide (`SOURCE_RENDERED_IG_URL`, `SOURCE_REPO_URL`) onto the MII KDS
> module template according to this specification.
> **Constraints:** The guardrails in §4 are binding. Work the steps in §5 in order, log to
> `.ai-log/migration-report.md`, stop at every review gate in §6 and hand over to a human. Do not
> change existing canonical URLs or IDs; where the source and the template disagree on identity,
> report it and stop rather than normalizing. Invent no domain content; mark uncertainty
> `TODO:REVIEW`. Do not publish. Delete the template's example artefacts before migrating. Replace
> every `{{...}}` placeholder and verify none remain. Do not modify the default branch.
