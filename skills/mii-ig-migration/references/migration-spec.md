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

**Fourth tier — source shape B (§5.1b).** A Forge-authored repository commonly has neither a
`sushi-config.yaml` nor a `package.json` nor a generated `ImplementationGuide` resource
(`kerndatensatzmodul-consent` has none of the three). Identity then comes from the module's
**published package manifest** on the registry it was published to and from the **canonical URLs the
conformance resources themselves carry**, cross-checked against the rendered Simplifier IG. **The
`sushi-config.yaml` goFSH writes is not a source of identity** — it carries no `id`, `name`, `title`,
`publisher`, `packageId` or `license`, and its `version` is one arbitrary artefact's version
(measured: `1.0.8`, while the published package was `2026.0.1-rc-3`). Reading identity out of it
would silently rename and re-version a published module.

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
- **Shell execution** — SUSHI, the IG Publisher, and goFSH (**required** for source shape B,
  §5.1b; optional for shape A). A **version-pinned** `npx` invocation satisfies this and is the
  sanctioned form — `npx --yes fsh-sushi@3.20.0`, `npx --yes gofsh@2.6.1` (§5.1b.2). An unpinned
  `npx`, or a bare `sushi`/`gofsh` assumed to be on `PATH`, does not: neither tool is normally
  installed, so a bare invocation is unrunnable on the machine this specification describes.
- **HTTP GET against the FHIR package registry** — to resolve a canonical to `<package>@<version>`
  (§5.1b.2) and to resolve floating pins (§2.1).
- **Append-only text output** — write and append `migration-log/run.log` in the format of §10, and
  capture the bundled scripts' stdout and stderr into it.
- **Resource-format detection** — parse XML and JSON well enough to decide whether a file is a FHIR
  resource, which is how source shape B is recognized (§5.1b.1).
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
   repository path. Uncertainty is marked `TODO:REVIEW`, never guessed. This extends to
   **dependencies**: a parent profile that cannot be resolved is escalated, never stubbed,
   substituted or snapshot-generated from a guess (§5.1b.4).
5. **Mandatory sections** required by the Manteldokument must be present. See §9 — the mapping onto
   the template's page set is an open question, so this is currently a Gate B check by hand.
6. **Human in the loop.** The gates in §6 are mandatory. The agent does not publish.
7. **Traceability.** Every step emits run-log lines *as it runs*, to `migration-log/run.log` in the
   normative format of **§10**; every assumption and open point reaches
   `migration-log/migration-report.md`, whose protocol section is generated **from** that log
   (§10.6) rather than written from recollection. A step that produced no log line did not happen
   as far as the report is concerned.
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

→ Output: `migration-log/source-inventory.json`.
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

### 5.1b Source shape B — deriving the FSH from raw FHIR resources (Path B)

Applies when the source repository carries **no IG scaffolding** (no `sushi-config.yaml`, no
`ig.ini`, no `input/`) but does carry conformance resources as `.xml` and/or `.json`. That is the
normal state of a module authored in **Forge** and published on **Simplifier**, and it is in scope.
Path B runs **between §5.1a and §5.2**: §5.2 merges the template skeleton with FSH that must already
exist, and §5.3 has nothing to transfer otherwise. Source shape A skips this section entirely.

Path B is **not** scaffolding a project from nothing, which §5.2 and SKILL.md Precondition 2 forbid.
Every line of FSH it produces is derived from a conformance resource the source already ships, and
therefore traces to a source path under guardrail 4.

**Measurement basis for this section:** goFSH **2.6.1** and SUSHI **3.20.0** (node 22), run end to
end against `medizininformatik-initiative/kerndatensatzmodul-consent` — 32 files, 20 conformance
resources (19 XML + 1 JSON) spread over **five** hand-named directories: `ressourcen-profile/`,
`terminologie/codesystems/`, `terminologie/valuesets/`, `searchparameters/`, `examples/` (plus
`figures/`, `README.md`, `LICENSE`). Read-only: nothing is ever written to the
`medizininformatik-initiative` organisation — the resources were fetched with
`gh api repos/<org>/<repo>/tarball` into a scratch directory.

**Toolchain invocation.** Neither tool is normally installed: on the reference machine
`which gofsh` finds nothing, and `npx` is the only route. A **version-pinned `npx` invocation is
the sanctioned form** and satisfies SKILL.md Precondition 5 — `npx --yes gofsh@2.6.1`,
`npx --yes fsh-sushi@3.20.0`. What that precondition protects is an exact, recorded version, and a
pinned `npx` delivers exactly that; an unpinned `npx gofsh` does not and is forbidden. Two traps:
the npm package for SUSHI is **`fsh-sushi`**, not `sushi`, and `allowed-tools` must grant
`Bash(npx:*)` — a grant of `Bash(gofsh:*)` alone does not match an `npx` command line, so an agent
under a strict permission prompt is blocked before it starts.

#### 5.1b.1 Classify the source by content

A file is a FHIR resource if it parses and carries a `resourceType` — directly in JSON, as the root
element name under the `http://hl7.org/fhir` namespace in XML. **Classify by that, never by folder
name:** the folders are hand-chosen and frequently German, and no glob over conventional IG
directory names finds them.

Consequence for §5.1: **the rendered guide's narrative lives on the Simplifier platform, not in
git.** There is no `implementation-guides/**` tree, so the page structure comes from the rendered IG,
and `fql-scan.sh` correctly exits 2 with an empty target set when run on the unmigrated repository.

**That is not the same as "the repository carries no narrative", and the earlier wording of this
section overclaimed it.** Measured on the reference module: a **43-line German `README.md`** (module
description, contact, contribution and licence notes) and a **126-line markdown mirror of a
CodeSystem**, `terminologie/codesystems/CodeSystem-MiiConsentPolicy.md`, next to the XML it mirrors.
So the classification pass has a third bucket beside "FHIR resource" and "binary asset":
**narrative-bearing text files**. Inventory every one of them with its line count and give it a
recorded disposition — migrated into a page, retained as repository documentation (a `README.md`
usually stays a `README.md`), or superseded by a generated artefact page (the CodeSystem mirror is
rendered by the publisher from the resource itself). A disposition of "none" is a finding, not a
default.

→ **Acceptance:** every file in the repository is classified as FHIR resource, narrative-bearing
text, or binary asset; the resource count is recorded in `migration-log/source-inventory.json`;
every narrative-bearing file has a disposition; and the source shape (A or B) is recorded in the
migration report.

#### 5.1b.2 Convert with goFSH

Four commands, and none of them is optional. The conversion is the single most important stage of
Path B, and until this block existed it left **no line in `run.log` at all** — the raw tool output
went to `migration-log/gofsh.log` and nothing else was recorded, so the one stage that can silently
drop 19 of 20 resources was the one stage invisible to a reviewer.

```bash
mkdir -p migration-log
ML="$SKILL_DIR/scripts/migration-log.sh"   # the run-log helper, §10.5
SRC=<source-repo-root>; OUT=<scratch-dir>; GLOG=migration-log/gofsh.log

# (0) Open a run boundary. run.log is append-only across invocations, and this
#     block is re-run whenever the `-d` set changes; without a marker the second
#     run's lines simply continue the first's.
bash "$ML" begin "step 2b — Path B on $SRC"

# (a) Count the INPUTS first, by content and never by folder name (§5.1b.1).
#     Nothing downstream computes this number, and it is the one goFSH's own
#     counts get reconciled against.
N_IN=$(find "$SRC" -type f \( -name '*.json' -o -name '*.xml' \) \
       -exec grep -lE '"resourceType"[[:space:]]*:|xmlns="http://hl7\.org/fhir"' {} + \
       | wc -l | tr -d ' ')
bash "$ML" info 5.1b.2 gofsh-input "counted the conversion inputs by content  inputs=$N_IN src=$SRC"

# (b) Convert. `run` writes the raw tool output to $GLOG -- TRUNCATING it first,
#     so the file holds this invocation only -- logs the command it actually
#     executed, and returns goFSH's real exit status.
bash "$ML" run 5.1b.2 gofsh-convert --raw-log "$GLOG" -- \
  npx --yes gofsh@2.6.1 "$SRC" -o "$OUT" -s file-per-definition -t json-and-xml \
  -d <parent-ig-package>@<version> -d hl7.fhir.r4.core@4.0.1
GOFSH_EXIT=$?

# (c)+(d) Read goFSH's OWN counts back out of that log, labelled, and reconcile
#     them against (a): equal -> one INFO; fewer -> an INFO *and* the mandatory
#     `silent-partial-success:` WARN naming both numbers (§10.4). This is the
#     comparison the `-t` trap below turns on; nothing else performs it.
bash "$SKILL_DIR/scripts/gofsh-results.sh" --log "$GLOG" --inputs "$N_IN" --exit $GOFSH_EXIT
```

Work in a scratch directory outside the module repository. Pin the goFSH version in the command line
itself — that is the record, and `run` copies it verbatim into the log's `cmd=` token.

##### Why (c)+(d) is a bundled script and not three lines of `sed`/`awk`

It **was** three lines of `sed`/`awk`, retyped by each caller, and two defects hid in them. Both
produced a wrong number inside a line that read as entirely normal — the worst failure mode a run log
has, because the reader has nothing to be suspicious of.

1. **The read-back was not re-run-safe.** The parse ran from the FIRST `GoFSH RESULTS` in the raw log
   to end of file, and the raw log was appended to. Re-running the block in the same working
   directory — the ordinary case, an operator adjusting `-d` and repeating the step — left **two**
   tables in one file, and the parse **summed** them: 20 converted became 40, and the reconciliation
   dutifully reported `count-above-expected` against 20 inputs.

   Two fixes were possible, and **both are applied, with one of them primary**: `run` now
   **truncates each raw log per invocation** (§10.5), because a raw log named after one ACTION should
   be the output of the run that produced the run.log lines next to it — that also makes
   `raw_log_lines=` the current run's count rather than the sum of every attempt, and the immediately
   preceding attempt is rolled over to `<ACTION>.prev.log` rather than lost. `gofsh-results.sh`
   **additionally** anchors to the LAST table and WARNs `stale-raw-log:` when it finds more than one,
   so a log assembled some other way (a hand-run `>>`, a restored file) cannot silently produce a
   plausible wrong number either.

2. **The converted count was wrong arithmetic.** It summed the table's cells and dropped only the
   last (Aliases), so **Invariants and Mappings were counted as converted resources** — which the
   inline comment did not say and the code did not show. On the reference module *with* `-d` this was
   invisible, because `-d` drives Mappings to 0; **without** `-d` goFSH reports 12 Mappings, and the
   count came out as 32 against 20 inputs. `gofsh-results.sh` reads each cell **with its label** from
   the table's own header rows and classifies by name:

   | Counted as converted | Never counted |
   | --- | --- |
   | Profiles, Extensions, Logicals, Resources, ValueSets, CodeSystems, Instances | Invariants, Mappings, Aliases |

   Invariants and Mappings are *parts of* a profile — one StructureDefinition contributes many — and
   Aliases are URL shorthands goFSH mints for readability. Counting either compares a per-resource
   input count against a per-fragment output count. A label the script does not model is a **refusal**
   (exit 2), never a guess: a future goFSH layout is a reason to re-measure, not to keep summing.

The script also quotes only the goFSH warnings that bear on **completeness** (`ignor`,
`without corresponding`, `json-only`, `cannot find a definition`, …). Taking the first warning
regardless of relevance put "Encountered 6 definition(s) that were missing an id" next to a ratio it
says nothing about, while the warning that *explains* the ratio — "13 XML definition(s) found without
corresponding JSON definitions … will be ignored" — was never shown.

```text
gofsh-results.sh --log FILE --inputs N [--exit N] [--step S] [--action A]
```

→ **Acceptance for the read-back:** running the block twice in the same directory yields the *same*
counts the second time; and a run without `-d` (Mappings non-zero) still reconciles to the input
count. Measured, both: 20 of 20 on the first and the repeated run; and without `-d`,
`profiles=3 … mappings=12 aliases=14  converted=20` reconciling to `converted 20 of 20 inputs`, where
the old arithmetic produced 32.

**One operational trap when you re-run: clear `$OUT` first.** goFSH refuses a non-empty output
directory and asks for confirmation on the TTY; with no TTY — an agent, CI, a captured shell — it
does not fall back but **fails**: "error Could not use output directory: The current environment
doesn't support interactive reading from TTY", exit 1. That is a loud, correct failure and the
block's `run` reports it as one, after which `gofsh-results.sh` refuses with exit 2 rather than
reporting the *previous* run's table (`setup: no "GoFSH RESULTS" table`). Under the appending raw log
this was precisely the dangerous case: the conversion never ran, and the read-back would still have
found run 1's table in the file and reported a confident `converted 20 of 20`.

`$GLOG` is not decoration: §5.1b.3 reads `migration-log/gofsh.log` as the authoritative name mapping,
so a run that does not write it cannot be post-processed. Note what changed against the older
convention: the raw log is still written, but through `run`, which **preserves goFSH's exit status**
instead of discarding it into a `tee`. The exit status still is not the acceptance signal here — the
counts are, and (d) is where they are compared — but a step whose status is thrown away can no
longer report a failure at all, and that trap cost this specification three of its acceptance
criteria (§10.5).

Measured, both variants of exactly this block on the reference module:

| Variant | Log lines produced |
| --- | --- |
| with `-t json-and-xml` | `converted 20 of 20 inputs  expected=20 actual=20 exit=0` — no WARN |
| without it | `converted 1 of 20 inputs  expected=20 actual=1 exit=0`, immediately followed by `WARN … silent-partial-success: converted 1 of 20 inputs at exit 0` |

##### Assembling the input: point goFSH at the repository root

The reference module keeps its 20 resources in **five** hand-named directories, and §5.1b.1 forbids
finding them by folder name. There is nevertheless no staging step, because **goFSH walks a
directory tree recursively** and ignores everything that is not a FHIR resource.

Measured, all three runs with the same flags and `-d` set:

| Input given to goFSH | Result |
| --- | --- |
| the repository root (5 nested resource dirs, `figures/`, `README.md`, `LICENSE`) | 3 profiles / 3 ValueSets / 3 CodeSystems / 11 instances / 8 aliases, exit 0, 2 warnings |
| a staged flat directory holding all 20 resources | identical counts — and the derived FSH tree is **byte-identical** (`diff -r` clean, `sushi-config.yaml` included) |
| the repository root plus a non-FHIR `package.json` and a non-FHIR `project.xml` | identical counts, FSH byte-identical to the root run; both files silently ignored |

So the procedure is: **give goFSH the repository root**, then reconcile its counts against the §5.1
inventory. Stage a flat directory only for a positive reason, and record it — the two that occur in
practice are a repository that vendors a *foreign* module's resources (a second module, a
`validator/` fixture set) which would otherwise be converted as if they were this module's, and a
selective re-run over a subset while investigating. Staging is a filter, never a workaround for
"goFSH did not find my files": if a resource is missing from the counts, the cause is `-t`
(see below), not the directory depth.

**`-t json-and-xml` is mandatory and its absence fails silently.** goFSH's default is `json-only`
(the values are `json-only`, `xml-only`, `json-and-xml`). Measured without the flag on the Consent
resources: **exit 0**, "0 Errors", **one** resource converted, and only a warning — "13 XML
definition(s) found without corresponding JSON definitions … will be ignored since GoFSH is running
in json-only mode". With the flag, the same input: **3 profiles, 3 value sets, 3 code systems,
11 instances** — 20 in total, matching the 20 inputs — exit 0. The exit code is therefore not
evidence; the artefact counts are.

Quote **goFSH's own 13** when quoting goFSH. The input holds **19** XML files; goFSH's pairing check
counts 13 of them as XML definitions lacking a JSON counterpart, and the difference is six files,
exactly the six `SearchParameter`s. Naming the wrong number in a report is how a reader loses trust
in the rest of it, so state which is which when both appear. Neither is the number the decision turns
on: that is `converted 1 of 20`, which block (d) above emits and WARNs on.

And that WARN is the *only* thing that catches it. Measured end to end on the no-flag run:
`postprocess-gofsh.py` exits 0 reporting "nothing to repair", and SUSHI exits 0 with 0 errors —
because the 19 missing resources cannot fail a check that never sees them. Every downstream signal
is green on a conversion that dropped 95 % of the module.

**Every foreign parent IG is declared with `-d <package>@<version>`.** Discover them from the
resources — the `baseDefinition` of each StructureDefinition and every other canonical pointing
outside the module — and resolve each canonical to its publishing package. goFSH names what it
cannot resolve: "Cannot reliably export top-level caret rules for `MII_PR_Consent_DocumentReference`
because GoFSH cannot find a definition for its parent: `http://fhir.de/ConsentManagement/
StructureDefinition/DocumentReference`. If its parent is from another IG, run GoFSH again declaring
that IG as a dependency." Measured: `-d de.einwilligungsmanagement@2.0.3 -d hl7.fhir.r4.core@4.0.1`
removed both such warnings. Re-run goFSH with the dependencies rather than patching a
dependency-less conversion — the derived output differs (measured: 12 mappings / 14 aliases without,
0 mappings / 8 aliases with), so the two runs are not the same FSH with better warnings. Record the
difference.

##### Resolving a canonical to `<package>@<version>`

`-d` takes a package id and a version, and a Forge-authored repository states **neither**: in the
reference module the string `de.einwilligungsmanagement` appears nowhere, and no version of it does
either. All you have is the canonical in a `baseDefinition`. Resolve it against the **FHIR package
registry**, which indexes packages by the canonicals they publish:

```bash
CANON='http://fhir.de/ConsentManagement/StructureDefinition/DocumentReference'
curl -s "https://packages.fhir.org/catalog?op=find&canonical=$CANON"
#   -> [{"Name":"de.einwilligungsmanagement","Description":"Einwilligungsmanagement Release 2.0.3…",
#        "FhirVersion":"R4"}]
curl -s https://packages.fhir.org/de.einwilligungsmanagement | python3 -m json.tool | head -40
#   -> "dist-tags": {"latest": "2.0.3"}, plus every published version
```

Measured on the reference module (2026-08-05): the **full resource canonical** resolves — the
registry matches on prefix, so trimming the `/StructureDefinition/<id>` tail first is optional, and
the trimmed IG canonical `http://fhir.de/ConsentManagement` returns the same single hit. Query the
registry once **per distinct canonical host+path prefix**, not once per resource.

Picking the version is a judgement, so record it and its evidence (§2.1's floating-pin rule applies
unchanged):

1. If the source repository, its CI logs or a committed package cache name a concrete version, that
   evidence wins — it is what the module was actually authored against.
2. Otherwise take `dist-tags.latest` and say so. For the reference module that is `2.0.3`, and the
   registry's own description string ("Einwilligungsmanagement Release 2.0.3") corroborates it.
3. A canonical that resolves to **no** package, or to more than one, is a Gate-A escalation — name
   it in the report and stop guessing. Never invent a package id from the canonical's shape.

Re-run goFSH after every change to the `-d` set, and check the unresolved-parent warnings are gone;
that warning, and not the exit code, is the acceptance signal.

**goFSH writes a `sushi-config.yaml` — `sushi init` is not needed, and that file is a starting point,
never identity.** Measured output for Consent: `canonical`, `fhirVersion: 4.0.1`, `FSHOnly: true`,
`applyExtensionMetadataToRoot: false`, `status: active`, `version: 1.0.8`, plus the declared
dependencies. It carries **no** `id`, `name`, `title`, `publisher`, `packageId` or `license`, and its
`version` is one arbitrary profile's version — `1.0.8` against the module's published package
`2026.0.1-rc-3`. Identity is read per §2.1 from the authoritative sources; goFSH's guess is used only
to run SUSHI in the scratch directory and is never carried into the module.

→ **Acceptance:** the run's artefact counts reconcile against the §5.1 inventory; no unresolved-parent
warning remains; the goFSH version, the `-d` set and the count difference between the dependency-less
and dependency-declared runs are recorded in the report.

#### 5.1b.3 Mechanical post-processing

SUSHI is run **twice** here, before and after the repair, and both runs are measured into the log.
That before/after pair (41 → 5 on the reference module) is Path B's headline claim and the number a
reviewer most needs; until this block existed it was captured nowhere at all.

```bash
SUSHI="npx --yes fsh-sushi@3.20.0"          # pinned, per §5.1b's toolchain rule

# (a) the baseline, before any repair
bash "$ML" run 5.1b.3 sushi-before --raw-log migration-log/sushi-before.log -- \
  bash -c "cd '$OUT' && $SUSHI ."
S_BEFORE=$?
E_BEFORE=$(grep -oE '[0-9]+ Errors' migration-log/sushi-before.log | tail -1 | cut -d' ' -f1)
bash "$ML" info 5.1b.3 sushi-before \
  "baseline before post-processing  errors=$E_BEFORE exit=$S_BEFORE raw_log=migration-log/sushi-before.log"

# (b) the repair. --emits-runlog: the script already prints §10.2 lines, so its
#     own INFO/WARN/ERROR reach run.log instead of only its raw log.
bash "$ML" run 5.1b.3 postprocess-gofsh --emits-runlog -- \
  python3 "$SKILL_DIR/scripts/postprocess-gofsh.py" "$OUT/input/fsh" --gofsh-log "$GLOG"
PP=$?
bash "$ML" info 5.1b.3 postprocess-gofsh "acceptance: exit status  exit=$PP  (0 required)"

# (c) the same measurement again, and the residual errors named line by line.
#     --expected-nonzero: for shape B this run's non-zero exit is the DOCUMENTED
#     outcome (§5.1b.4), so it is logged as an escalation to be queued, not as a
#     step that failed. The status is still returned verbatim.
bash "$ML" run 5.1b.3 sushi-after --raw-log migration-log/sushi-after.log \
  --expected-nonzero 'shape B: residual unresolvable-parent errors are a Gate-A escalation (§5.1b.4)' -- \
  bash -c "cd '$OUT' && $SUSHI ."
S_AFTER=$?
E_AFTER=$(grep -oE '[0-9]+ Errors' migration-log/sushi-after.log | tail -1 | cut -d' ' -f1)
OLDIFS=$IFS; IFS=$'\n'; RESID=($(grep -E '^error ' migration-log/sushi-after.log | cut -c1-140)); IFS=$OLDIFS
bash "$ML" info 5.1b.3 sushi-after \
  "after post-processing  errors=$E_AFTER exit=$S_AFTER resolved=$(( E_BEFORE - E_AFTER )) raw_log=migration-log/sushi-after.log" \
  "every residual error below is a Gate-A escalation (§5.1b.4), not a defect to work around:" \
  "${RESID[@]}"
```

**SUSHI's exit status is its error count**, so `run` reports `exit=41` before the repair and `exit=5`
after. The first stays an ERROR, and correctly so: its acceptance criterion is not met, and the fix —
"either fix and re-run" — is literally the next line of the block. The second is different. It is the
snapshot blocker, which §5.1b.4 turns into report ① entries rather than a failure to fix, yet `run`'s
generic ERROR text told the reader that this documented, anticipated result "did NOT meet its
acceptance criterion … either fix and re-run or take it to the report's decision queue". A log that describes its
expected outcome as a failure trains its reader to discount every ERROR in it. `--expected-nonzero`
therefore logs that one step as a WARN whose detail begins `anticipated-nonzero-exit:` and whose
continuations state the qualifier — escalated, never ignored, and still a queue entry per §10.6. The
generic ERROR is untouched for every other step, and an `--expected-nonzero` step that exits **0**
says so on its `done` line, so a stale anticipation is visible rather than silently confirmed. What
would *not* be acceptable is either line with nothing in the log naming which five errors they were —
which is why the residual lines are passed as continuations.

**SUSHI's exit status is also eight bits**, and this is the one step where that matters: a status
that IS an error count is truncated modulo 256, so exactly 256 errors exit **0**. Measured: a probe
exiting 256 logged `exit=0` and returned 0, indistinguishable from a clean run. `run` therefore
cross-checks the status against the `N Errors` line in the raw log and WARNs
`exit-status-truncated:` (or `exit-status-disagrees:`) when the two disagree — which is why
`E_BEFORE`/`E_AFTER` above are read out of the log and not taken from `$?`.

`migration-log/gofsh.log` is the file §5.1b.2 wrote; the two stages are a pair and run in that order,
from the same working directory. **Give the script the whole FSH tree**
(`input/fsh`, or the goFSH output root), never a single sub-directory: a code reference is only
repaired once the normalized name has been confirmed against the entity declarations, and those live
in sibling directories — a narrowed `FSH_DIR` turns a repairable reference into a refusal (exit 1)
or, when the tree carries no references at all, into a `silent-partial-success` WARN.

Two defects of the XML sources survive into the FSH. Both are mechanical — neither is a modelling
decision — and both are fatal to SUSHI:

1. **`fhir_comments` rules.** XML comments become assignment rules on a `.fhir_comments` element,
   which is an XML-serialization construct and not a FHIR element: "The element or path you
   referenced does not exist: `status.fhir_comments`". Measured: 53 occurrences in 4 instance files,
   **30 SUSHI errors**. The script preserves each one's text as an FSH `//` comment by default —
   the text is authored source content (in Consent, German annotations explaining each provision) and
   a migration does not silently discard it; `--drop-comments` removes them instead.
2. **Bare system names containing whitespace in code references.** goFSH normalizes a CodeSystem
   name with spaces for the entity declaration and reports it — "has name with whitespace (MII CS
   Consent Policy). Converting whitespace to underscores (MII_CS_Consent_Policy)" — but still emits
   the un-normalized name in the references to it, producing unparseable FSH
   (`… .code = MII CS Consent Policy#2.16…5.3.6 "MDAT erheben"`). SUSHI reports "extraneous input
   'CS'" and "Cannot find definition for Instance: MII". Measured: 39 references in 3 files,
   **6 SUSHI errors**. The repair uses the name goFSH itself reports, applied only after that name
   has been confirmed to exist as a declared entity in the same FSH tree.

This one is the more dangerous defect, and the reason it cannot be left for later: **an FSH parse
error stops SUSHI reading the rest of that file, and SUSHI still exports the instance, silently
truncated.** Measured on the three Consent examples: **1** nested provision each before the repair,
**27 / 6 / 3** after. "It exported" is not "it converted".

The CodeSystem's own `* ^name = "MII CS Consent Policy"` caret rule is **not** touched — it is a real
element value of a published resource (guardrail 1), and SUSHI only warns about it. The script
classifies every occurrence before writing, writes nothing at all when it meets a shape it does not
model (exit 1, occurrences listed), and is idempotent.

→ **Acceptance:** the script exits 0 — **as returned by `run`, not as reported by a `tee` pipeline**;
`npx --yes fsh-sushi@3.20.0 .` in the scratch directory reports no `fhir_comments` error and no FSH
parse error; the exported instances are compared against the source resources for truncation, not
merely counted; and both SUSHI runs, their error counts and the residual errors are in `run.log`.

#### 5.1b.4 Residual blockers — a Gate-A escalation

Path B does **not** by itself produce a clean build, and the specification does not claim it does.
Measured on Consent: **41 SUSHI errors before post-processing, 5 after** — the 36 mechanical ones
resolved, and the remainder the genuine architectural blocker:
`de.einwilligungsmanagement@2.0.3` ships its profiles **without snapshots**, so SUSHI cannot import
them at all ("Structure Definition `http://fhir.de/ConsentManagement/StructureDefinition/
{DocumentReference,DomainReference,Provenance}` is missing a snapshot. Snapshot is required for
import."). That blocks the three profiles and, consequentially, the instances declaring `InstanceOf`
them.

Two options, both **human decisions taken at Gate A**: obtain a snapshot-bearing build of the parent
package, or record the affected profiles as blocked and migrate the rest. **Inventing a parent is
forbidden** — no local stub, no substituted base resource, no snapshot generated from a guess
(guardrails 1 and 4).

**goFSH-invented ids** are a review-queue item, not an error. Measured: "Encountered 6 definition(s)
that were missing an id", each named, and where no name could be derived goFSH wrote GUID-named files
(`instances/34150a23-b1c8-404f-874f-e042a30435d2.fsh`). Those minted ids become the module's ids, so
they go into the report's ② review queue and are confirmed by a human at Gate A.

→ **Acceptance:** every remaining SUSHI error is named in the migration report as an
unresolvable-parent escalation with its decision option, every invented id and GUID-named file is in
the ② review queue, and no parent has been fabricated.

##### The shape-B qualifier (normative — it overrides every "clean build" criterion below)

Several later acceptance criteria are written around a clean build: "SUSHI runs without error"
(§5.2), "`qa.txt` reports `Errors: 0`" (§5.6), "builds cleanly" (§7), and the same three in SKILL.md.
**Read every one of them through this qualifier when the source shape is B.** Where a foreign parent
package ships no snapshots, a clean build is not reachable by migration alone, and the flat criterion
would mark a correct migration as failed — or, worse, invite someone to fabricate a parent to satisfy
it.

For shape B, "clean" means all four of:

1. **no mechanical error remains** — nothing of the two families §5.1b.3 repairs, and
   `postprocess-gofsh.py` exits 0;
2. **every residual error is named** in the report's ① decision queue, with its resource, its cause
   and its decision options;
3. **a Gate-A decision is recorded** for each (obtain a snapshot-bearing parent build, or migrate
   the rest and record the affected profiles as blocked);
4. **no parent was fabricated** — no stub, no substituted base, no guessed snapshot.

A residual error count that is merely tolerated is not a pass, and neither is a zero reached by
inventing a parent. For source shape A the flat criteria stand unqualified.

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

→ **Acceptance:** `npx --yes fsh-sushi@3.20.0 .`, run through the helper so its exit status survives
(`bash "$ML" run 5.2 sushi-skeleton --raw-log migration-log/sushi-skeleton.log -- npx --yes
fsh-sushi@3.20.0 .`), runs without error — **shape B: as qualified in §5.1b.4** — no template
examples remain; no `{{` left unaccounted for; the skipped-collision list is in the log.

### 5.3 Transfer the artefacts

Move the FSH sources from the source repository. Where only JSON/XML exists, convert with `gofsh`;
for source shape B that conversion and its post-processing already happened in §5.1b, so what moves
here is that output. IDs and URLs unchanged — including the ids goFSH minted for resources that had
none, which are confirmed at Gate A rather than re-minted here.

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
bash "$ML" run 5.4 fql-scan --emits-runlog -- \
  bash "$SKILL_DIR/scripts/fql-scan.sh"            # recursive; findings are informational
bash "$ML" run 5.4 fql-scan-strict --emits-runlog -- \
  bash "$SKILL_DIR/scripts/fql-scan.sh" --strict   # exit 1 on any finding, for CI
```

The scanner prints its scanned-file count and exits 2 on an empty target set — "nothing scanned"
is never "nothing found". Run it through the helper rather than `… | tee -a`, or both of those exit
statuses — the `--strict` gate and the empty-target refusal — are replaced by `tee`'s 0 (§10.5).

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
  Generate it after the SUSHI run of §5.2, seeded from the two menus:

  ```bash
  bash "$ML" run 5.5 gen-page-title-po --emits-runlog -- \
    python3 "$SKILL_DIR/scripts/gen-page-title-po.py" \
      fsh-generated/resources/ImplementationGuide-<ig-id>.json \
      migration-log/menu-titles-de.txt \
      de input/translations/de/ImplementationGuide-<ig-id>.po
  ```

  Resolve `SKILL_DIR` to the directory holding the skill's `SKILL.md` first; a bare
  `scripts/gen-page-title-po.py` silently runs the *project's* same-named file if it has one.
  See *Mechanism* below — this is **not** a resource supplement and is not subject to the
  supplement type restriction.

  **Producing `migration-log/menu-titles-de.txt`, the seed.** It is a required positional argument
  with no default, so it has to exist before the generator runs. Its format is **one
  `English Title => Deutscher Titel` per line**; blank lines and `#` comments are skipped, and a line
  without the ` => ` separator (spaces on both sides, exactly one occurrence taken as the split) is
  reported as malformed and ignored. The seed is *only* a seed: an existing non-empty `msgstr` in the
  target `.po` wins over it, and a title the seed does not cover is emitted untranslated and named in
  the run summary. There is no obligation to seed at all — **pass `-`** to say deliberately that
  there is no seed. What is forbidden is a path that does not resolve: that is a setup error (exit 2,
  nothing written), never a silent "no seed".

  The two menus are the natural source, because they are structurally mirrored translations of each
  other. Pair their link labels **positionally** — not by `href`, because a dropdown parent and its
  first child share one `href` and pairing on it produces a cross-product:

  ```bash
  mkdir -p migration-log        # shape A never ran §5.1b.2, so it may not exist yet
  labels() { grep -o '<a [^>]*href="[^"]*"[^>]*>[^<]*' "$1" \
             | sed 's/.*"[^>]*>//' | sed 's/[[:space:]]*$//'; }
  labels input/includes/menu.xml                    > migration-log/.menu-en.txt
  labels input/translations/de/includes/menu.xml    > migration-log/.menu-de.txt

  # Same anchor count is the precondition for pairing by position; when it does not
  # hold the menus are not mirrors and the seed would be silently wrong.
  bash "$ML" ratio 5.5 menu-seed paired anchors \
    "$(wc -l < migration-log/.menu-en.txt | tr -d ' ')" \
    "$(wc -l < migration-log/.menu-de.txt | tr -d ' ')"

  paste -d'\t' migration-log/.menu-en.txt migration-log/.menu-de.txt \
    | awk -F'\t' 'NF==2 && $1!="" && $2!="" && $1!=$2 {print $1" => "$2}' \
    | sort -u > migration-log/menu-titles-de.txt
  bash "$ML" info 5.5 menu-seed "wrote the page-title seed  entries=$(wc -l \
    < migration-log/menu-titles-de.txt | tr -d ' ') out=migration-log/menu-titles-de.txt"
  ```

  Measured against the module template's own pair of menus: 27 anchors each, 23 distinct seed
  entries. The seed covers only menu entries, so pages that are not in the menu (Table of Contents,
  Downloads, Translation Information, Metadata Overview) stay untranslated and are named by the
  generator — that is the ② review queue, not a defect in the seed. A module generated from template
  **v0.5.0** can seed from its `input/includes/breadcrumb-titles-de.txt` instead, which is already in
  this exact format; it is likewise incomplete, for the same reason.

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

Run SUSHI, then the IG Publisher — both through the run-log helper, so the two numbers this step
exists to produce (SUSHI's error count and `qa.txt`'s `Errors:`) end up in the log rather than only
on someone's terminal. The target pins the publisher, SUSHI and Jekyll versions in its build
workflow's `env:` block, the publisher jar additionally by SHA-256 — **read the pins from there**,
and use them here instead of the versions written below.

```bash
bash "$ML" run 5.6 sushi-build --raw-log migration-log/sushi-build.log -- \
  npx --yes fsh-sushi@3.20.0 .
SUSHI_EXIT=$?
bash "$ML" info 5.6 sushi-build "errors=$(grep -oE '[0-9]+ Errors' migration-log/sushi-build.log \
  | tail -1 | cut -d' ' -f1) exit=$SUSHI_EXIT raw_log=migration-log/sushi-build.log"

bash "$ML" run 5.6 ig-publisher --raw-log migration-log/qa-build.log -- \
  <the publisher invocation pinned in the target's build workflow>
bash "$ML" info 5.6 ig-publisher "qa=$(grep -m1 -E '^(Errors|Warnings|Info)' output/qa.txt) \
  qa_txt=output/qa.txt raw_log=migration-log/qa-build.log"
```

A missing Jekyll on the runner surfaces as `Cannot run program "jekyll"`. Copy `qa.txt`'s summary
line into the log as above: the file itself is build output that may not be committed, and a report
claiming `Errors: 0` needs a log line behind it (§10.6).

→ **Acceptance:** `qa.txt` reports `Errors: 0` — **shape B: as qualified in §5.1b.4**, where the
residual errors are the named escalations and every *other* error is still a stop; every example
validates (an example blocked by an unresolvable parent is named, not counted as validated); the
same-module comparison of the catalog's `fhir-ig-analysis` skill (source first, migrated tree
second — equal `packageId` triggers it) reads **IDENTISCH** for identity fields, published artifact
set and canonical URLs, and its narrative per-language table is carried into the report's QA triage.
The IDENTISCH criteria are **not** qualified by shape: they are identity checks, and a DIVERGIERT is
a stop in either shape.

### 5.7 Report

Write `migration-log/migration-report.md`: mapping table, assumptions, the `TODO:REVIEW` list, the QA
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
| **A** | §5.3 | Canonical URL and ID preservation; artefact completeness; any identity divergence per §2.2; for source shape B additionally the ids goFSH minted (§5.1b.4) and the decision on any unresolvable parent |
| **B** | §5.4 | The narrative, especially sections added to satisfy the Manteldokument, and section completeness by hand while §9 is open |
| **C** | §5.5 | Language handling and translation |
| **D** | before merge | Release per KDS governance (TF KDS / AG IOP / NSG) |

Gate D is organizational. Nothing publishes before it.

## 7. Definition of done

SUSHI and the IG Publisher build cleanly (`Errors: 0`) — **for source shape B read that through the
shape-B qualifier of §5.1b.4, never flatly**; the Manteldokument crosswalk is complete; the
`fhir-ig-analysis` same-module verification reads IDENTISCH (identity, published artifact set,
canonical URLs); the language configuration is English-default with a German translation; every
placeholder is replaced; template examples are removed; the default branch is unchanged; a pull
request carries `migration-report.md`; all review gates are signed off.

That qualifier, in full: when a foreign parent package ships no snapshots, a clean build is **not**
reachable by migration alone, and §5.1b.4 defines what "clean" means then in four conditions — not a
silently tolerated error count, and not a fabricated parent. The sentence above is the one people
quote, so it carries the marker itself rather than relying on this paragraph being read too.

And, for every shape: the migration report's protocol section is generated from
`migration-log/run.log` (§10), so a run whose log is missing or was written after the fact is not
done either.

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

## 10. The run log (normative)

**What the run log is for, in one sentence: so that a human reader can reconstruct which steps ran
and what each one produced — the command actually executed, the counts it actually returned, the
status it actually exited with — without re-running anything and without trusting anybody's
recollection.** Writing the report from recollection at the end lets it drift from what actually
executed; that has already produced two documented false claims in this project's history. So the
log is the primary record, the report's protocol section is generated **from** it (§10.6), and a
step that emitted no line did not happen as far as a reviewer is concerned.

Everything below follows from that: every step emits at least one line (§10.2, §10.3); a tool that
succeeds while under-producing is called out rather than averaged away (§10.4); and §10.5 is the
bundled helper that makes both affordable — including for the many steps that run no bundled script.

### 10.1 Where it lives

`migration-log/run.log` in the module repository being migrated, alongside the other run artefacts:

```text
migration-log/
  run.log                  the run log — plain UTF-8 text, append-only, committed
  migration-report.md      the report (§5.7), whose protocol section is generated from run.log
  source-inventory.json    §5.1
  gofsh.log                raw tool output, referenced by path from run.log (shape B)
  <action>.log             per-step raw tool output, one file per ACTION, written by
                           the helper's `run` wrapper — sushi-before.log, sushi-after.log,
                           qa-build.log, fql-scan.log … Each is named by the run.log line
                           that produced it, so a claim in the log can be checked against
                           the tool output it came from. TRUNCATED PER INVOCATION: it holds
                           the CURRENT run of that ACTION, never every attempt concatenated
                           — otherwise a read-back of it (§5.1b.2) sums two runs.
  <action>.prev.log        the immediately preceding attempt, rolled over by `run` so a
                           re-run does not destroy what the last one produced; named in the
                           new run's `start` line as `prev_raw_log=`.
  menu-titles-de.txt       working seed for §5.5 (how to produce it: §5.5)
```

`run.log`, `migration-report.md` and `source-inventory.json` are **committed with the migration
branch** — they are the audit trail the pull request is reviewed against. The raw tool logs and
working files may be committed or not; either way they are referenced from `run.log` by path, and a
referenced file that is absent from the branch is named as such in the report.

**Naming note.** This directory used to be called `.ai-log/`. It was renamed because it is a
human-facing audit artefact, not a machine's scratch space, and because "AI" framing is being removed
from these projects. **Repositories migrated before the rename still carry `.ai-log/`. Leave them
alone** — do not rename, move or dual-write them: the old directory is part of a merged, reviewed
history, and rewriting it would invalidate references from pull requests and reports that cite it.
A re-migration of such a repository writes the new directory and says in its report that an older
`.ai-log/` exists.

### 10.2 The line format

One event per line. Fields are separated by **exactly two spaces**:

```text
<TIMESTAMP>  <LEVEL>  <STEP>  <ACTION>  <DETAIL>
```

| Field | Form | Notes |
| --- | --- | --- |
| `TIMESTAMP` | `YYYY-MM-DDTHH:MM:SSZ` | UTC, second resolution, ISO 8601 |
| `LEVEL` | `INFO `, `WARN `, `ERROR` | padded to five characters, so the columns line up |
| `STEP` | the spec section, e.g. `5.1b.3`, `5.4`, `2.1`; `pre.<n>` for a precondition | one identifier, no spaces |
| `ACTION` | a kebab-case slug naming what was done, e.g. `gofsh-convert` | stable across runs, so a step is greppable |
| `DETAIL` | free text plus `key=value` tokens | see below |

`DETAIL` carries, for anything that ran, **the command actually executed** as
``cmd=`…` `` — the real command line, not a paraphrase or a placeholder-bearing template — and its
**measured outcome** as `key=value` tokens: `exit=`, counts (`files=`, `errors=`, `units=`), and
paths. Continuation lines are indented **four spaces** and belong to the line above; use them for
lists (findings, names, remediation prose), never for a second event.

Every procedure step emits at least one INFO line. A step that ran no command still emits one
recording its outcome (`pre.2  classify-source-shape  shape=B resources=20 dirs=5`).

**Do not hand-assemble these lines.** `scripts/migration-log.sh` (§10.5) emits the format, including
the timestamp, and appends to the run log itself. Hand-formatting is how a timestamp ends up local
instead of UTC and a level ends up unpadded.

**Reading it back.** The log is complete rather than curated — the bundled scripts list every change
they made, and that verbosity is the point on review day. Two filters make it navigable:
`grep -E '  (WARN |ERROR)  ' migration-log/run.log` for everything a human must look at, and
`grep -F 'silent-partial-success:' migration-log/run.log` for the §10.4 class alone. Each WARN class
carries its own leading token so the classes stay separable — `silent-partial-success:`,
`count-above-expected:`, `anticipated-nonzero-exit:`, `exit-status-truncated:`,
`exit-status-disagrees:`, `stale-raw-log:` — and `  run-boundary  ` splits the file by invocation.

### 10.3 Levels

- **INFO** — a step ran; here is its measured outcome. Facts only, no interpretation.
- **WARN** — the run continues, but a human must look. Mandatory for the silent-partial-success rule
  (§10.4) and used for: an identity divergence between source and template, an empty `msgstr`, a
  template file skipped on a name collision, an applied default, an `[UNKNOWN]` directive.
- **ERROR** — the step did not meet its acceptance criterion. Either the run stops, or the item
  becomes an entry in the report's ① decision queue. An ERROR is never left only in the log.

A non-zero exit that is the step's **documented, anticipated** outcome is a WARN, not an ERROR — the
criterion is met AS QUALIFIED (§5.1b.4). It is marked as such at the call site with
`run --expected-nonzero WHY` (§10.5), never by weakening the ERROR text, and it still owes the ①
queue an entry per item. The one instance in this specification is the shape-B `sushi-after` run.

### 10.4 The silent-partial-success rule (mandatory WARN)

**Whenever a tool reports success while producing less than its input implies, the step MUST emit a
WARN naming both numbers.** Exit code 0 is not evidence of completeness; the counts are, and the
reconciliation has to be visible in the log rather than performed in someone's head.

The canonical case is goFSH without `-t json-and-xml`. It exits 0 and prints "0 Errors" while
converting **one** of the twenty input resources. The log must show both facts, adjacent — this is
the verbatim output of the §5.1b.2 block on the reference module, no-flag variant:

```text
2026-08-05T22:29:04Z  INFO   5.1b.2  gofsh-convert  goFSH RESULTS table  profiles=0 extensions=0 logicals=0 resources=0 valuesets=0 codesystems=1 instances=0 invariants=0 mappings=0 aliases=1  gofsh_log=migration-log/gofsh.log
2026-08-05T22:29:04Z  INFO   5.1b.2  gofsh-convert  converted 1 of 20 inputs  expected=20 actual=1 exit=0
    goFSH said: warn  13 XML definition(s) found without corresponding JSON definitions (for example, …
2026-08-05T22:29:04Z  WARN   5.1b.2  gofsh-convert  silent-partial-success: converted 1 of 20 inputs at exit 0
    Exit status is not evidence of completeness; these two counts are.
    Reconcile against the step-1 inventory before continuing.
```

**Quote goFSH's own number, which is 13, not the input's 19.** The reference module's input carries
19 XML files; goFSH reports "13 XML definition(s) found without corresponding JSON definitions",
because that is what *its* pairing check counts — the difference is six files, exactly the six
`SearchParameter`s. Both numbers are true of different things, so name which is which whenever both
appear: 13 = XML definitions without a JSON counterpart *as goFSH counts them*; 19 = XML files in the
input. The number the reconciliation actually turns on is neither: it is **1 converted of 20 inputs**.

The INFO line alone is not enough — a reader scanning for problems filters on WARN and ERROR, and
"converted 1 of 20" reads as a normal count until something calls it out. The WARN detail **starts
with the literal token `silent-partial-success:`** so the whole class is greppable:
`grep -F 'silent-partial-success:' migration-log/run.log`.

**Why this rule needs a mechanism and not just a paragraph.** Measured on the reference module, the
no-flag run end to end: goFSH exit 0, "0 Errors"; `postprocess-gofsh.py` exit 0, "nothing to repair";
SUSHI exit 0, 0 errors. **Every step reports success, and 19 of 20 resources are simply absent.**
The single line in the entire log that says otherwise is the WARN above. A rule that depends on
somebody remembering to compare two numbers by hand does not fire on the run where it matters — so
§10.5's `ratio` helper performs the comparison, and the block in §5.1b.2 calls it.

Other instances of the same class, all implemented in the bundled scripts: a scan whose target
directory contributed zero files while the run continued; a page-title catalogue written with empty
`msgstr` units; a repair pass that found none of the references the goFSH log said it would.

### 10.5 Emitting the log — `scripts/migration-log.sh`

A convention nothing implements is decoration. The bundled helper is what turns §10.2–§10.4 into
lines on disk; **wire every stage through it**, including the ones that run no bundled script. It is
both a sourceable library and a CLI, because an agent's shell state does not survive between tool
calls:

```bash
ML="$SKILL_DIR/scripts/migration-log.sh"

bash "$ML" begin "step 2b — Path B on $SRC"
bash "$ML" info 2.1 read-identity "packageId=…  canonical=…  license=CC0-1.0 (source) vs CC-BY-4.0 (template)"
bash "$ML" warn 2.2 identity-divergence "license differs; source wins (§2.2) — Gate A decides"
bash "$ML" ratio --exit 0 5.1b.2 gofsh-convert converted inputs 20 1
bash "$ML" run  5.4 fql-scan --emits-runlog -- bash "$SKILL_DIR/scripts/fql-scan.sh" --strict
```

| Subcommand / function | What it does |
| --- | --- |
| `begin [LABEL]` | one numbered `run-boundary` line, so a second invocation's lines do not concatenate into the first's. Call it once, first, in every block |
| `info` / `warn` / `error` STEP ACTION DETAIL [CONT …] | one §10.2 line plus indented continuations; appends to the run log **and** echoes to the terminal |
| `ratio [--exit N] STEP ACTION VERB NOUN EXPECTED ACTUAL [CONT …]` | the §10.4 rule: an INFO naming both numbers, plus a `silent-partial-success:` WARN when ACTUAL < EXPECTED (and a distinct `count-above-expected:` WARN when it is greater, which must not pollute a grep for the former) |
| `run STEP ACTION [--emits-runlog] [--raw-log FILE] [--expected-nonzero WHY] -- CMD …` | runs CMD, writes its output to `migration-log/<ACTION>.log` (**truncated per invocation**), logs the command **actually executed** and its **measured exit status**, ERRORs on non-zero — and **returns the command's real exit status** |

**The run log is append-only; the raw logs are not.** That difference is deliberate and is the fix
for a class of defect rather than one instance of it. `run.log` accumulates, because it is the audit
trail — which is exactly why `begin` exists, to mark where each invocation starts within it. A raw
log named `<ACTION>.log` is instead the output of the run whose lines sit beside it, so appending
made every read-back of one wrong on a re-run (§5.1b.2's summed RESULTS tables) and made
`raw_log_lines=` the total of every attempt. `run` truncates it and rolls the previous attempt over
to `<ACTION>.prev.log`, naming it in the start line as `prev_raw_log=`.

**An exit status is eight bits.** The shell reports `status mod 256`, so a tool whose status IS its
error count — SUSHI's is — reports 0 for exactly 256 errors and 5 for 261. Measured: a probe exiting
256 logged `exit=0` and returned 0. Nothing can recover the real number from the status afterwards,
so `run` cross-checks it against the `N Errors` line the tool printed and WARNs when the two
disagree: `exit-status-truncated:` when the printed count is congruent to the status modulo 256 (the
truncation case, proven), `exit-status-disagrees:` when a zero status stands against a non-zero
printed count. Both are distinct greppable tokens and neither pollutes `silent-partial-success:`.

**`--expected-nonzero WHY` marks an anticipated non-zero exit.** Exactly one step in this
specification has one — the shape-B `sushi-after` run, whose residual unresolvable-parent errors are
a §5.1b.4 Gate-A escalation. Without the flag `run` told its reader that this documented outcome
"did NOT meet its acceptance criterion", which is both wrong and corrosive: a log that calls its
expected result a failure teaches its reader to skim past every ERROR. Marked, the step logs a WARN
beginning `anticipated-nonzero-exit:` and carrying the reason and the §5.1b.4 pointer — the
acceptance criterion is met AS QUALIFIED, the items behind it still go to the ① queue individually,
and the status is still returned verbatim. Genuine failures keep the unchanged ERROR, and a marked
step that exits 0 says so on its `done` line rather than confirming a stale anticipation in silence.

**`run` exists because `tee` throws the exit status away, and the acceptance criteria in this
specification ARE exit statuses.** A pipeline's status is its *last* command's, and `tee` succeeds:
under the previous convention `… 2>&1 | tee -a migration-log/run.log`, a step that failed read as a
step that passed. Measured: `postprocess-gofsh.py` on a too-narrow `FSH_DIR` exits 1, the tee
pipeline reported 0; `npx --yes fsh-sushi@3.20.0 .` on raw goFSH output exits **41**, the tee
pipeline reported 0. `run` takes the status from `PIPESTATUS[0]` and returns it, so `$?` after it is
the tool's own. Do **not** pipe the helper's own output into `tee -a migration-log/run.log`: it
writes that file itself, and a `tee` on top duplicates every line.

`--emits-runlog` says the wrapped command already prints §10.2-format lines — `postprocess-gofsh.py`,
`gen-page-title-po.py` and `fql-scan.sh` do, with the spec section as `STEP` (5.1b.3, 5.5, 5.4) and
their own name as `ACTION`. Their output is then appended to the run log as well as to the raw log,
so tool and skill output read as one stream and their WARNs reach §10.6's queues. Without the flag
only the wrapper's lines reach the run log and the raw output is referenced from them by path.

**One execution, one `start`, one `done`, one `cmd=`.** Those three scripts emit their own `start`
and `done` lines, and through `run` that produced a second pair per execution, with a *different*
`cmd=` (the script's own name against the wrapper's full interpreter command line) — two openings and
two closings a reader has no way to reconcile into one run. `run` therefore exports
`MIGRATION_LOG_WRAPPED=1`, and a wrapped script demotes its own two lines to `params` (its resolved
arguments, no `cmd=`) and `result` (its measured counts). Run directly — still supported, and how the
scripts are unit-tested — nothing changes.

**Chronological by construction.** Every line is appended by the helper with a single `>>`, so
ordering does not depend on how streams are later merged. The three bundled scripts keep the
INFO/WARN-to-stdout, ERROR-to-stderr split — but they now **flush every line**, because stdout is
block-buffered when it is a pipe while stderr is not: measured before the fix, an ERROR written last
appeared *first* in the captured log, ahead of INFO lines emitted seconds earlier. A log that claims
to read as one chronological stream has to actually be one.

Where the log is written is `$MIGRATION_LOG_DIR/run.log`, default `migration-log/run.log`; set
`MIGRATION_LOG_DIR` for a repository that still carries `.ai-log/` (§10.1).

### 10.6 The report is generated from the log

**Rule: the migration report's protocol/audit section is produced FROM `migration-log/run.log`, never
written from recollection.** Concretely:

- Every claim in the protocol section traces to a log line. A claim with no line behind it is a
  defect in the report, and the fix is to re-run the step, not to add the sentence.
- The protocol section is the log grouped by `STEP`, in step order, each group followed by that
  step's acceptance verdict (met / not met / met-as-qualified per §5.1b.4).
- Every WARN and ERROR in the log appears in one of the three reviewer queues — a WARN that reaches
  nobody is the failure mode this convention exists to prevent.
- Tool versions, pins and the `-d` set are read out of the `cmd=` tokens, not restated from memory.

The counts elsewhere in the report — artefact totals, QA findings, translated units — come from the
same lines. Where the report and the log disagree, the log is right.

## Appendix — vendor-neutral prompt scaffold

> **Role:** You are a migration assistant for FHIR Implementation Guides.
> **Task:** Move the source guide (`SOURCE_RENDERED_IG_URL`, `SOURCE_REPO_URL`) onto the MII KDS
> module template according to this specification.
> **Constraints:** The guardrails in §4 are binding. Work the steps in §5 in order, emit a run-log
> line per step to `migration-log/run.log` in the format of §10 (WARN on any silent partial success),
> generate the report's protocol section from that log into
> `migration-log/migration-report.md`, stop at every review gate in §6 and hand over to a human. Do not
> change existing canonical URLs or IDs; where the source and the template disagree on identity,
> report it and stop rather than normalizing. Invent no domain content; mark uncertainty
> `TODO:REVIEW`. Do not publish. Delete the template's example artefacts before migrating. Replace
> every `{{...}}` placeholder and verify none remain. Do not modify the default branch.
