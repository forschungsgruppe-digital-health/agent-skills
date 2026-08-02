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

### 5.2 Create the skeleton

Create the skeleton **in place**: on a working branch of the module's existing repository, vendor
the template and run its first-run bootstrap — do not mint a new repository; the module's history,
issues and consumers stay where they are. (A new repository is a human decision, recorded in the
migration report, never a default.) Replace the placeholders (§2.3) using the identity read in
§2.1 — the licence per §2.2 is carried from the source, not left at the template's literal.
**Delete the template's example artefacts** — at the time of writing
`input/fsh/profiles/example-patient.fsh` and
`input/fsh/instances/example-patient-instance.fsh`; confirm the paths in the template you actually
checked out.

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
  render before investing in a supplement** — several do not, and a supplement for one of those is
  silently ignored.

→ **Acceptance:** the IG builds both language variants; translated element texts appear on the
translated artefact pages; no ignored `.po` files were created. Note: **breadcrumbs and the
titles of `pages:`-tree pages stay in the default language on translated variants** — a
known IG-Publisher limitation (see the translation skill's rendering table), not a migration
defect; classify it as `environment` in QA triage, do not chase it.

### 5.6 Build and QA

Run `sushi .`, then the IG Publisher. The target pins the publisher, SUSHI and Jekyll versions in
its build workflow's `env:` block, the publisher jar additionally by SHA-256 — read the pins from
there. A missing Jekyll on the runner surfaces as `Cannot run program "jekyll"`.

→ **Acceptance:** `qa.txt` reports `Errors: 0`; every example validates.

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
complete; the canonical URL diff is empty; the language configuration is English-default with a
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
