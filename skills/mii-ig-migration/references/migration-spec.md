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
`package.json` plus the `ImplementationGuide` resource.

| Field | Read from | Human input? | Written to |
| --- | --- | --- | --- |
| module title | `sushi-config: title` / `package.json: title` | derived | `title`, menu, README |
| module abbreviation | existing FSH artefact names (`MII_PR_<Module>_…`) | derived — names stay | FSH `name` / `title` |
| `packageId` | `package.json: name` / `sushi-config: packageId` | derived | `sushi-config: packageId` |
| `canonical` | `sushi-config: canonical` / `package.json: canonical` | derived — **never change** | `sushi-config: canonical` |
| `version` | `sushi-config` / `package.json: version` | **yes — confirm or bump** | `sushi-config: version`, release tag |
| `status` / `releaseLabel` | `sushi-config` | derived (confirm) | `sushi-config` |
| `dependencies` | `sushi-config: dependencies` (+ `package.json`) | derived — resolve `.x` pins | `sushi-config: dependencies` |
| `publisher` / `contact` | `sushi-config: publisher` | derived | `sushi-config: publisher` |

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
   checked-out template on every run.
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

→ Output: `.ai-log/source-inventory.json`.
→ **Acceptance:** the inventory is complete and every entry carries its source path.

### 5.2 Create the skeleton

Create the module repository from the template, run its first-run bootstrap, and replace the
placeholders (§2.3) using the identity read in §2.1. **Delete the template's example artefacts**
— at the time of writing `input/fsh/profiles/example-patient.fsh` and
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

Move the Manteldokument content into `input/pagecontent/*.md`. Translate Simplifier and FQL
directives into IG Publisher equivalents:

```bash
scripts/fql-scan.sh
scripts/fql-scan.sh --strict
```

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
translated artefact pages; no ignored `.po` files were created.

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

Determine the target branch from the module repository's own convention — do not assume one. The
template previews every non-`main` branch to `gh-pages` under `branches/<branch>/` and reserves
`main` and tags for formal publication, so a working branch gets a rendered preview without
touching the default branch. If the module repository uses a different convention, follow it and
record which you followed.

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
reference module, whose `input/pagecontent/` set is identical to the template's. It is evidence
about what the MII actually does, not an interpretation of the Manteldokument's wording.

| Manteldokument section | Where it lives | Evidence |
| --- | --- | --- |
| **Bezüge zu anderen Modulen** | `index.md` § *Related guides* — the template ships a `TODO:` there instructing the author to name the module's formal dependencies. The machine-readable form is `dependencies` in `sushi-config.yaml`. Cross-references are additionally described in `implementer-guidance.md`. | template `index.md`; basis `implementer-guidance.md` lists "Module dependencies and cross-references" |
| **Referenzen** | `index.md` § *Related guides* for external guides and the FHIR IG Registry; `downloads.md` for package and artefact references; inline artefact links throughout the narrative | template `index.md`; basis `downloads.md` |
| **Anwendungsfälle / Szenarien** | `guidance.md`, which routes to `implementer-guidance.md` and `researcher-guidance.md`; `general-requirements.md`, which frames the requirements in terms of MII use cases; `examples.md` for the concrete scenarios | basis `general-requirements.md` (German) refers to "die Anwendungsfälle der Medizininformatik-Initiative"; basis `researcher-guidance.md` covers identifying data elements for a research question |

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
