---
name: mii-ig-migration
description: Migrates a Simplifier-published MII KDS module Implementation Guide onto the MII KDS
  module template — preserves the module's identity, transfers the FSH artefacts, rewrites
  Simplifier/FQL directives into IG Publisher equivalents, and sets up the bilingual page set.
  Covers both source shapes — a SUSHI/IG-Publisher project, and a Forge-authored repo of raw FHIR
  XML/JSON resources with no sushi-config.yaml or input/fsh, converted with gofsh first. Use when
  moving a KDS module off Simplifier or Forge, when a rendered IG URL and its repo are handed over,
  when FQL blocks or {{tree}} and {{render}} directives stop rendering after such a move, or when
  the user mentions Kerndatensatz, KDS-Modul, Implementierungsleitfaden, Manteldokument,
  sushi-config, ig.ini, gofsh, StructureDefinition XML or the IG Publisher in the context of moving
  a guide. Not for authoring new profiles, creating a module from scratch, or translating a guide
  already on the template — the template ships recipes and an ig-translate skill for those.
license: CC-BY-4.0
allowed-tools: Read Grep Glob WebFetch Bash(npx:*) Bash(bash:*) Bash(python3:*) Bash(curl:*) Bash(find:*) Bash(grep:*) Bash(sed:*) Bash(awk:*) Bash(paste:*) Bash(wc:*) Bash(git clone:*) Bash(git status:*) Bash(git diff:*)
metadata:
  fgdh.tier: "domain"
  fgdh.domain: "fhir-ig"
  fgdh.owner: "@msusky"
  fgdh.language: "en"
  fgdh.status: "stable"
---

# Migrating an MII KDS module IG onto the module template

This skill **supports and partly automates** the migration. It never publishes, and four human review
gates are mandatory. The full procedure, with acceptance criteria per step, is in
[the migration specification](references/migration-spec.md); this file is the operating summary.

## Preconditions

Discover the context: assume none of it, create nothing that is missing.

1. **The source guide.** Two inputs come from the human and cannot be derived: the URL of the
   rendered Simplifier IG and the URL of its source GitHub repository. If either is absent, ask for
   it and stop. Everything else about the module's identity is *read*, not asked (step 2).

2. **The module repository — classify the source shape.** Two shapes are in scope and take
   different routes to the same place; a third is not. Decide first, and record it (spec §5.1b).

   - **Shape A — a SUSHI / IG-Publisher project.** A `sushi-config.yaml` **or** an `ig.ini` at the
     repository root plus an `input/fsh/` — the FHIR IG ecosystem conventions that make this skill
     portable. The FSH exists; step 4 transfers it. `input/fsh/` present but empty → report it; a
     migration with no artefacts to move is a configuration error, not a no-op.
   - **Shape B — a raw FHIR resource repository.** No scaffolding at all (no `sushi-config.yaml`,
     no `ig.ini`, no `input/`) but conformance resources present as `.xml` and/or `.json`.
     **This is the normal state of a module authored in Forge and published on Simplifier, and it
     is fully in scope** — the most authentic case this skill exists for. Step **2b** derives the
     FSH with goFSH; from step 3 the two paths are identical. **Detect it by content, not by folder
     name** (spec §5.1b.1): a file is a FHIR resource if it parses and carries a `resourceType`;
     folder names are hand-chosen and often German, so no conventional-name glob finds them.
     **The rendered guide's narrative is on Simplifier, not in the repository** — no
     `implementation-guides/**` tree, so step 1 takes the page structure from the rendered IG and
     `fql-scan.sh` rightly exits 2 on an empty target set before migration. That is not "no narrative
     in the repository": the reference module ships a 43-line German `README.md` and a 126-line
     CodeSystem mirror. Inventory every narrative-bearing text file, with a disposition each.
   - **Neither** — no scaffolding **and** no FHIR resources: not a FHIR IG project. Say so and stop.
     **Do not scaffold one.** Path B is no exception: it creates no artefacts, deriving FSH from
     resources that already exist, each tracing to a source file (guardrail 3).

3. **The target template.** Determine which state the module is in — discovery only here, the
   skeleton comes in step 3 of the procedure. In every state, read
   `forschungsgruppe-digital-health/mii-kds-module-template` at the ref you intend to use rather
   than relying on this skill's description of it.
   - **Already on the module template** — a vendored `ig-template/`, or an `ig.ini` `template` entry
     pointing at it. A *re-migration*: report what is in place before changing anything.
   - **Plain Simplifier project** — Simplifier files only (`.simplifier/`, `project.yaml`,
     `implementation-guides/`), no IG-Publisher scaffolding. The normal starting state.
   - **Hybrid, or on another template** — IG-Publisher files beside the Simplifier ones: an `ig.ini`
     naming another template, `_genonce.sh` & co., a committed `fsh-generated/` or rendered output
     (possibly live GitHub Pages). Still a migration. Inventory them and record which the template
     replaces (`ig.ini`, `_gen*`/`_update*`), which carry content to transfer (`input/`,
     `fsh-generated/`), and which retire only after Gate D. List **any unrecognized top-level entry**
     too (e.g. `validator/`) with a retain/retire proposal — list, do not remove.

4. **Unreplaced placeholders.** The template does not build until every `{{...}}` placeholder is
   replaced, and an unreplaced one **ships a bogus artefact** rather than failing loudly. Before and
   after migrating, grep the tree for `{{` and account for every hit — excluding `.github/**`
   (Actions `${{ … }}` matches the pattern) and counting Simplifier directives in narrative sources
   as accounted (step-5 material). The template's `sushi-config.yaml` header enumerates the real
   placeholders and says which are active.

5. **The toolchain — invoke SUSHI and goFSH only as a version-pinned `npx`.** Neither is normally
   installed (`which gofsh` finds nothing on the reference machine), so **a bare `sushi`/`gofsh` is
   unrunnable and appears nowhere in this skill**: write `npx --yes fsh-sushi@3.20.0` and
   `npx --yes gofsh@2.6.1` — the npm package for SUSHI is **`fsh-sushi`**, not `sushi`. What the "no
   fetching a toolchain" rule protects is an **exact, recorded version**, which the pin supplies and
   an unpinned `npx` does not; let the pin be the record, carried in the log's `cmd=` token.
   (`allowed-tools` grants `Bash(npx:*)`; `Bash(gofsh:*)` never matches an `npx` command line.) goFSH
   is **required for shape B**, for shape A only where the source ships JSON/XML; the IG Publisher is
   needed from step 7. Missing node/npx → say which and **stop after step 2**. A parent package
   without snapshots additionally needs **java and a pinned `validator_cli.jar`** — fetched only when
   that condition is actually detected (spec §5.1b.5), never hand-substituted.

## Procedure

Written in English; the artefacts operated on are German-language KDS documents, and German terms
of art are kept as such. **Output language follows the target template: English is the default
language and German is the translation.** This reverses the older convention — see *Language*
below, and verify it against the target's `sushi-config.yaml` rather than trusting this sentence.

> **Resolve the script path first.** The commands below name tools relative to **this skill's own
> directory**, not to your working directory — which is the project being migrated. Set
> `SKILL_DIR=<the directory containing this SKILL.md>` (e.g. `.claude/skills/mii-ig-migration`) and
> `ML="$SKILL_DIR/scripts/migration-log.sh"`, and use them in every invocation. A bare
> `scripts/...` from the project root does not merely fail: if the project has its own `scripts/`
> with a same-named file, it silently runs **that** instead.

1. **Inventory the source.** From the rendered IG and the source repository, extract every artefact
   (profiles, extensions, value sets, code systems, capability statements, examples) and the
   narrative structure, each with its source path → `migration-log/source-inventory.json`. When
   `implementation-guides/` holds **several guide trees** (versions × languages + shared assets — a
   real module ships six), apply spec §5.1a: pick the authoritative tree, mark parallel-language
   trees as harvest seeds, retain the rest.

2. **Read the module's identity — do not ask for it, and do not invent it.** From the source's
   `sushi-config.yaml` and `package.json` (absent a `sushi-config.yaml`: `package.json` plus the
   `ImplementationGuide` resource) read `title`, `packageId`, `canonical`, `status`, `releaseLabel`,
   `license`, `dependencies` and `publisher`, and carry them over **unchanged**. On disagreement
   `sushi-config.yaml` wins — it is what the build reads; record it. A field in neither file comes
   from the generated `ImplementationGuide`; absent everywhere it takes the template default, at
   Gate A. Resolve floating pins (`1.5.x`) per spec §2.1, recording the pick and its evidence.
   **Shape B often has none of the three files — and a repository carrying no identity is not an
   identity-less module.** Identity is then RECOVERED from several sources **in this order, each
   field recorded with the source it came from** (spec §2.1; the scripts write the ledger themselves):
   - **P — the published package.** `bash "$SKILL_DIR/scripts/package-identity.sh" --package ID --version V` logs `packageId`, `version`, `description`, `fhirVersions`, `jurisdiction` and the **dependency pins** — source evidence, outranking any `dist-tags.latest` — plus the `canonical` derived from the packaged resources' own urls by common prefix, **unanimous or a WARN, never a majority vote**. No manifest carries `title`, `license` or `publisher`; `author` is a registry account, not a publisher.
   - **R — the source repository.** `bash "$SKILL_DIR/scripts/repo-identity.sh" --dir DIR --repo OWNER/NAME --rendered URL` reads the LICENSE text's **SPDX id — real licence evidence, the field that must never default** (§2.2) — the README's first heading as a `title` candidate, the repo description, and the release tags, whose match with P's version ties that release to the commit. An unrecognized licence text yields nothing (`license-text-unrecognized:`); the GitHub owner is **not** a `publisher`.
   - **H — the Simplifier project / rendered IG.** Measured client-rendered (HTTP 200, ~56 KB, 52 script markers, **no identity metadata in the DOM**), so it is a **human reference at Gate A** for what no machine source carries — not a scrape target. The same script measures that and extracts nothing.

   Whatever no tier yields stays Gate A — measured on the reference module, `publisher` alone.
   Every value is claimed with its evidence (`bash "$ML" claim 2.1 ACTION FIELD VALUE TIER SOURCE`),
   and a second source with a **different** value raises `identity-contradiction:` — **reported,
   never resolved** (measured: goFSH's `version: 1.0.8` against the package's `2026.0.0`; a source
   pin `2.0.2` against `dist-tags.latest` `2.0.3`). `bash "$ML" claims --markdown` is the report's
   identity table. **NEVER ALTER EXISTING METADATA from a recovered value**, even where the recovery
   shows it to be inconsistent: recovery is evidence for Gate A. Spec §2.1.2–§2.1.4.

   Log each value read, and each divergence as a WARN. The **target version** is the only identity
   value that is a human decision: MII CalVer `YYYY.n.n`, not SemVer, defaulting to the source's.
   **When the source and the template disagree, the source wins** — the template's `canonical` and
   `packageId` patterns are what a *new* module gets, and changing a published canonical breaks every
   consumer. Report each divergence and let a human decide; never normalize silently. That covers
   every value the template pre-fills as a **literal** rather than a placeholder, `license` above
   all: the template ships `CC-BY-4.0`, no placeholder check flags it, and MII modules commonly
   declare `CC0-1.0`. Relicensing is a human decision, never a default. Spec §2.2.

2b. **Source shape B only — derive the FSH from the raw resources.** Runs **before** the skeleton,
   which step 3 merges into FSH that must already exist. Work in a scratch directory outside the
   module repository; skip for shape A. **Spec §5.1b is normative here** (measured with goFSH
   **2.6.1** and SUSHI **3.20.0** on `medizininformatik-initiative/kerndatensatzmodul-consent`).

   ```bash
   mkdir -p migration-log
   ML="$SKILL_DIR/scripts/migration-log.sh"   # run-log helper — see *Run log* below
   SRC=<source-repo-root>; OUT=<scratch-dir>; GLOG=migration-log/gofsh.log
   SUSHI="npx --yes fsh-sushi@3.20.0"
   E() { grep -oE '[0-9]+ Errors' "$1" | tail -1 | cut -d' ' -f1 | grep . || echo n/a; }
   bash "$ML" begin "step 2b — Path B on $SRC"   # run boundary: re-runs stay separable
   rm -rf "$OUT"     # goFSH refuses a non-empty -o dir; $OUT is derived, so clearing is safe

   N_IN=$(find "$SRC" -type f \( -name '*.json' -o -name '*.xml' \) \
          -exec grep -lE '"resourceType"[[:space:]]*:|xmlns="http://hl7\.org/fhir"' {} + \
          | wc -l | tr -d ' ')                                     # inputs, BY CONTENT
   bash "$ML" info 5.1b.2 gofsh-input "inputs=$N_IN src=$SRC"

   bash "$ML" run 5.1b.2 gofsh-convert --raw-log "$GLOG" -- \
     npx --yes gofsh@2.6.1 "$SRC" -o "$OUT" -s file-per-definition -t json-and-xml \
     -d <parent-ig-package>@<version> -d hl7.fhir.r4.core@4.0.1
   GOFSH_EXIT=$?
   bash "$SKILL_DIR/scripts/gofsh-results.sh" --log "$GLOG" --inputs "$N_IN" \
     --exit $GOFSH_EXIT                          # <- the mandatory WARN fires here
   # A failed conversion is a stop: everything below measures $OUT (spec §5.1b.2).
   [ "$GOFSH_EXIT" -eq 0 ] || { bash "$ML" error 5.1b.2 gofsh-convert \
     "conversion failed — not measuring \$OUT; fix the cause and re-run"; exit 1; }

   bash "$ML" run 5.1b.3 sushi-before --raw-log migration-log/sushi-before.log -- \
     bash -c "cd '$OUT' && $SUSHI ."                               # the 41 of "41 -> 5"
   B=$(E migration-log/sushi-before.log); bash "$ML" info 5.1b.3 sushi-before "errors=$B"
   bash "$ML" run 5.1b.3 postprocess-gofsh --emits-runlog -- \
     python3 "$SKILL_DIR/scripts/postprocess-gofsh.py" "$OUT/input/fsh" --gofsh-log "$GLOG"
   bash "$ML" run 5.1b.3 sushi-after --raw-log migration-log/sushi-after.log \
     --expected-nonzero 'shape B: unresolvable parents are a Gate-A escalation (§5.1b.4)' -- \
     bash -c "cd '$OUT' && $SUSHI ."                               # the 5
   A=$(E migration-log/sushi-after.log)   # n/a when a run printed no count (crash/kill)
   case "$B$A" in *n/a*) R="resolved=not-measured";; *) R="resolved=$(( B - A ))";; esac
   bash "$ML" info 5.1b.3 sushi-after "errors=$A $R  before=$B"
   ```

   Run verbatim, in that order, from the same directory: the post-processor reads `$GLOG`, and the
   `E` helper reads each SUSHI error count back out of its raw log into an INFO line — that pair
   **is** the 41 → 5 evidence, and it is in the block, not only in the spec. `gofsh-results.sh`
   reads goFSH's own RESULTS table back, labels every cell, counts converted **resources** only
   (never Invariants/Mappings/Aliases) and reconciles them against `$N_IN`. **That reconciliation is
   the point of the whole block** — goFSH's exit code is not the signal, its counts are — and `run`
   keeps each real exit status, truncating each raw log per invocation so a re-run measures itself
   and not the sum of both.

   - **Point goFSH at the repository ROOT, not at one resource folder.** The reference module keeps its
     20 resources in **five** hand-named directories and needs no staging: measured, goFSH walks the tree
     recursively and the FSH from the root is **byte-identical** to that from a staged flat directory.
     Stage only for a recorded reason (spec §5.1b.2).
   - **`-t json-and-xml` is mandatory; its absence fails SILENTLY.** goFSH defaults to `json-only`:
     on Consent (19 XML + 1 JSON) the flagless run **exited 0, reported "0 Errors" and converted
     exactly ONE resource**, warning only that "**13** XML definition(s)" lacked a JSON counterpart —
     goFSH's own count, not the input's 19 files (the difference is the six `SearchParameter`s); say
     which you mean. The deciding number is neither: it is `converted 1 of 20`, which
     `gofsh-results.sh` emits and WARNs on. Reconcile against step 1's inventory, never the exit code.
   - **Declare every foreign parent IG with `-d <package>@<version>`,** found in the resources' own
     `baseDefinition` canonicals; goFSH's "cannot find a definition for its parent … declaring that
     IG as a dependency" is the signal. Re-run rather than patch the dependency-less output — the two
     differ (12 mappings / 14 aliases without, 0 / 8 with). A Forge repo names neither package nor
     version: resolve it against the FHIR package registry (spec §5.1b.2); no hit is a Gate-A stop.
   - **goFSH writes the `sushi-config.yaml` itself but it is a STARTING POINT, NOT IDENTITY**: no
     `id`/`name`/`title`/`publisher`/`packageId`/`license`, an **untrusted `version`** (measured
     `1.0.8` — one profile's — against the module's published `2026.0.0`), and `dependencies` that
     are only whatever `-d` set you passed. Recover identity per step 2 instead.
   - **The script's two passes are mechanical:** `fhir_comments` rules and unquoted code-reference
     systems whose name carries whitespace, repaired with the name goFSH itself reports. It classifies
     before writing, writes nothing on a shape it does not model, and is idempotent. Give it the
     **whole** FSH tree — a narrowed path cannot see the declarations it checks against, so it refuses
     (exit 1, which `run` returns and a `tee` would have hidden).
   - **Then SUSHI must compile clean apart from genuinely unresolvable parents** — measured
     **41 errors before, 5 after**, both logged by the block above. A parse error stops SUSHI reading
     the rest of a file while it still *exports* the instance, silently truncated ("exported" is not
     "converted"): the three Consent examples carried **1** nested provision each before, 27 / 6 / 3
     after. SUSHI's exit status is its error count, so `sushi-after` exits 5 — the anticipated
     shape-B outcome, which `--expected-nonzero` logs as an escalation rather than as a failure.
   - **A parent package that ships no snapshots blocks import** — SUSHI cannot read such a parent at
     all, blocking those profiles and every instance declaring `InstanceOf` them. **Detect it, then
     generate the snapshots with a real generator; never hand-roll one** (spec §5.1b.5):
     `bash "$SKILL_DIR/scripts/parent-snapshots.sh" detect --package ID --version V` counts them (measured: 21 SDs, **0**
     snapshots, in *both* candidate versions — another version does not fix it), and
     `… build … --validator validator_cli.jar --install --require <parent-url>…`
     drives the **official HL7 generator** (`java -jar validator_cli.jar snapshot`, ProfileUtilities),
     verifies every result (**a snapshot whose element count matches only the differential is WRONG**
     and is refused), and installs a **new** cache entry `<id>#<version>-snapshots` — upstream is
     never overwritten. A generator refusal is an upstream defect to escalate, not to hand-finish;
     what the rebuild costs CI (it is local-only) is a Gate-A decision. Approximating a merge —
     slicing, cardinalities, element order — fabricates a parent (guardrails 1 and 3). Then re-pin,
     re-run SUSHI and log **both** error counts: measured on Consent, **5 → 0**.
     **goFSH-invented ids and GUID-named files** go to the ② queue: minted ids become the module's,
     so Gate A confirms them.
   - **Acceptance:** counts match the inventory; the script exits 0; every remaining SUSHI error is a
     named unresolvable-parent escalation; all of it is in `run.log`. **Path B does not by itself produce
     a clean build**, so every "clean build" criterion below (steps 3 and 7, *Verification*) is read for
     shape B through the **shape-B qualifier**, spec §5.1b.4: no mechanical error left, every residual in
     the ① queue with a Gate-A decision, no parent fabricated. A tolerated error count is not a pass.

3. **Create the skeleton** (spec §5.2). The migration happens **in place**: on a working branch of
   the module's existing repository, vendor the template checked out in Preconditions 3 and run its
   first-run bootstrap — do not mint a new repository; history, issues and consumers stay where they
   are (a new repository is a human decision, recorded in the report, never a default). Replace
   every `{{...}}` placeholder from the identity read in step 2. The template's CRMI `meta.profile`
   claims **require the `hl7.fhir.uv.crmi` dependency** — add it to the carried source dependencies
   and record it at Gate A (template machinery, not source identity). Then **delete the template's
   example artefacts** (`input/fsh/profiles/example-patient.fsh`,
   `input/fsh/instances/example-patient-instance.fsh` — verify the paths against the template you
   actually checked out) so they cannot collide with the module's real examples. **Before copying
   the template's FSH scaffold** (`input/fsh/aliases.fsh`, `input/fsh/rulesets/*`), diff its
   `RuleSet:`/`Alias:` names against the module's FSH: **module definitions win** — the module's FSH
   is never changed — so skip every colliding template file and log the skip list. Overwriting a
   module's `aliases.fsh` broke a real migration with 234 SUSHI errors. Acceptance:
   `bash "$ML" run 5.2 sushi-skeleton -- npx --yes fsh-sushi@3.20.0 .` runs clean (shape B: as
   qualified in step 2b), and the skip list is in the log.

4. **Transfer the artefacts.** Move the FSH sources across; convert JSON/XML with a pinned
   `npx --yes gofsh@2.6.1` where that is all the source has — for shape B that happened in step 2b,
   so what moves here is its post-processed output. IDs and URLs unchanged.

5. **Migrate the narrative.** Move the Manteldokument content into `input/pagecontent/*.md` and
   translate Simplifier and FQL directives into IG Publisher equivalents:

   ```bash
   bash "$ML" run 5.4 fql-scan --emits-runlog -- bash "$SKILL_DIR/scripts/fql-scan.sh" --strict
   ```

   The scan is recursive and, pre-migration, includes `implementation-guides/**` where a Simplifier
   project keeps its pages; it logs how many files it scanned per target, WARNs when a named
   directory contributed none, and exits 2 on an empty target set — never read "nothing scanned" as
   "nothing found". `--strict` exits 1 on any finding, for CI; `run` keeps both statuses where a
   `tee` would report 0. Apply the recommendation printed per finding; the mapping is in [the FQL
   crosswalk](references/fql-crosswalk.md), the rules in
   [`references/fql-rules.tsv`](references/fql-rules.tsv). In doubt, write `TODO:REVIEW`.

   The Manteldokument requires sections the template's English-named page set does not name. They
   are not missing: they map onto *sections within* the fixed page set, never onto pages of their own
   — **never create a page outside it**, an extra page is an unlisted orphan the menu cannot reach.
   The mapping is [spec](references/migration-spec.md) §9, which also records that the reference
   module is itself incomplete on use cases: record such a gap in the report, never fill it. With
   **more than two profiles**, route the per-profile narrative to
   `input/intro-notes/<Type>-<id>-intro.md` (German mirror under
   `input/translations/de/intro-notes/`, same filename — both render atop the artifact page,
   build-verified) and keep `profiles-and-extensions.md` as a short index.

6. **Set up the bilingual pages.** English is the default; German is the translation, a same-named
   file under `input/translations/de/pagecontent/`. These **do** render. The menu is
   `input/includes/menu.xml` with a per-language mirror at
   `input/translations/de/includes/menu.xml` — never a `menu:` property in `sushi-config.yaml`,
   which competes with it. Resource translations are `.po` supplements under
   `input/translations/de/`; check the target's recipe for which resource types actually render
   before investing in one. A German-only source inverts the direction — see *Language* below.
   **Page titles (breadcrumbs, table of contents, `<title>`) — full recipe in spec §5.5.** The
   publisher *does* localize them, through one IG-level catalogue
   `input/translations/<lang>/ImplementationGuide-<ig-id>.po` (imported into the IG resource at load
   time — not a resource supplement, so their type restriction does not apply). Generate it after the
   step-3 SUSHI run from the SUSHI-generated ImplementationGuide resource, the authoritative title
   set — the menus serve only as a translation seed:

   ```bash
   bash "$ML" run 5.5 gen-page-title-po --emits-runlog -- \
     python3 "$SKILL_DIR/scripts/gen-page-title-po.py" \
       fsh-generated/resources/ImplementationGuide-<ig-id>.json \
       migration-log/menu-titles-de.txt \
       de input/translations/de/ImplementationGuide-<ig-id>.po
   ```

   `migration-log/menu-titles-de.txt` is a **required argument with no default** (one
   `English Title => Deutscher Titel` per line; build it, and the `-` "no seed" option, per spec §5.5
   — an unresolvable path is a setup error, never a silent empty seed). Regenerating is
   non-destructive; an empty `msgstr` means untranslated and goes to the ② queue. **Footgun:** the
   language must appear in **`translation-sources`**, not only `i18n-lang`, or every `.po` is
   silently ignored. Modules from template **v0.5.0** also drop its breadcrumb override.

7. **Build and QA.** SUSHI, then the IG Publisher — both through `bash "$ML" run 5.6 …`, so the two
   numbers this step exists to produce end up in the log: SUSHI's error count, and `qa.txt`'s summary
   line copied into an INFO (spec §5.6 has the block). The target pins its toolchain in the build
   workflow's `env:` block — read the pins from there rather than from this file. Acceptance:
   `qa.txt` reports `Errors: 0` and every example validates — shape B: as qualified in step 2b, the
   named escalations excepted and every *other* error still a stop. Then run the **same-module
   verification** with `fhir-ig-analysis` (measure the unmigrated source, then the migrated tree — an
   equal `packageId` triggers the comparison; the SOURCE is the first input): identity, published
   artifact set and canonical URLs must all read **IDENTISCH** and a DIVERGIERT is a stop; the
   narrative per-language table goes into the report's QA triage.

8. **Report.** Write `migration-log/migration-report.md` **from
   [the report template](references/migration-report-template.md)** — built around three reviewer
   queues (① decide, ② review, ③ triage) so the report is a work instrument: every open decision,
   every `TODO:REVIEW` and every QA finding lands in exactly one queue with a concrete next action
   and an owner, QA provenance requires proof (build the unmigrated source to claim "pre-existing"),
   and the L0 box + mini-glossary keep it readable for people new to FHIR IGs. **The protocol section
   is generated FROM `migration-log/run.log`** (spec §10.6): every claim traces to a log line, every
   WARN and ERROR lands in a queue, and where the two disagree the log is right.

9. **Open a pull request** with the report as its description. **Do not publish.** Determine the
   target branch from the module repository's own convention — **discover it, do not assume it**:
   the default branch, the bases of merged pull requests, CONTRIBUTING/README. The template previews
   every non-`main` branch to `gh-pages` under `branches/<branch>/` and reserves `main` and tags for
   publication, so a working branch previews without touching the default branch. Follow a different
   convention where the repository has one and say so — and if that PR base is itself the publication
   branch, say so in the PR and at Gate D: there, merging publishes.

## Run log

**What it is for, once: so a human reader can reconstruct which steps ran and what each produced — the command actually executed, the counts it returned, the status it exited with — without re-running anything and without trusting recollection.** `migration-log/run.log`: plain text, append-only, committed with the branch. The report's protocol section is generated **from** it (step 8), so it cannot claim what the run did not do. Spec §10 is normative. **Emit every line through the bundled helper**, `ML="$SKILL_DIR/scripts/migration-log.sh"` — including from the many steps that run no bundled script.

| Call | Emits |
| --- | --- |
| `bash "$ML" begin LABEL` | one numbered `run-boundary` line — call it first in every block, so a second invocation does not concatenate into the first |
| `bash "$ML" info\|warn\|error STEP ACTION DETAIL [CONT …]` | one line plus indented continuations |
| `bash "$ML" ratio [--exit N] STEP ACTION VERB NOUN EXPECTED ACTUAL [CONT …]` | an INFO naming both counts — plus the mandatory WARN when ACTUAL < EXPECTED |
| `bash "$ML" run STEP ACTION [--emits-runlog] [--raw-log F] [--expected-nonzero WHY] -- CMD …` | the command actually executed, its output at `migration-log/<ACTION>.log` (**truncated per invocation**), and its **real exit status**, returned rather than swallowed |

**Never `… 2>&1 | tee -a migration-log/run.log`.** A pipeline's status is `tee`'s, and this skill's
acceptance criteria *are* exit statuses: measured, that pipeline reported **0** where `fsh-sushi`
exited **41** and `postprocess-gofsh.py` exited **1**, so failed steps read as passed. `run` takes
the status from `PIPESTATUS[0]`; `--emits-runlog` folds in the bundled scripts' own lines (wrapped,
they log `params`/`result` rather than a second `start`/`done`). **An exit status is eight bits** —
256 SUSHI errors report as `exit=0` — so `run` cross-checks it against the raw log's error count and
WARNs (`exit-status-truncated:`) on disagreement. `--expected-nonzero WHY` marks the one step whose
non-zero exit is the documented outcome (shape-B `sushi-after`), logging a WARN naming the
escalation rather than an ERROR calling the expected result a failure.

```text
2026-08-05T22:29:04Z  INFO   5.1b.2  gofsh-convert  converted 1 of 20 inputs  expected=20 actual=1 exit=0
2026-08-05T22:29:04Z  WARN   5.1b.2  gofsh-convert  silent-partial-success: converted 1 of 20 inputs at exit 0
```

`<UTC ISO-8601>  <LEVEL>  <STEP>  <ACTION>  <DETAIL>`, two spaces between fields; `LEVEL` is
`INFO `/`WARN `/`ERROR` padded to five, `STEP` the spec section (`5.1b.3`, `5.4`, `pre.5`), `ACTION`
a stable slug, `DETAIL` the command **actually executed** as ``cmd=`…` `` plus measured `key=value`
outcomes. Continuations are indented four spaces; every step emits at least one INFO line.
**WARN is mandatory for silent partial success**: when a tool reports success while producing less
than its input implies, name **both** numbers in a WARN beginning `silent-partial-success:`. Use
`ratio`, never do it by hand — on that run every other signal is green (postprocess "nothing to
repair", SUSHI 0 errors) while 19 of 20 resources are missing. Read the log back with
`grep -E '  (WARN |ERROR)  '`.

## Guardrails

Binding — a migration that violates one is wrong even if it builds.

1. **Canonical URLs and IDs of existing conformance resources are never changed.**
2. **FHIR R4 (4.0.1).**
3. **No fabrication.** Every artefact and narrative section traces to a source URL or repo path;
   uncertainty is marked `TODO:REVIEW`, never guessed. (`TODO:REVIEW` marks the migrated guide; the
   catalog's marker for unfinished *skill* content is `TODO(owner):` — do not mix them.)
4. **Human in the loop.** The review gates below are mandatory. The agent does not publish.
5. **Template examples are deleted before migrating**, never merged with the module's own.
6. **The default branch is not modified.** Work on a branch, deliver a pull request.
7. **Traceability.** Every step emits run-log lines as it runs, through `scripts/migration-log.sh`
   (*Run log*, above), and every assumption and open point reaches
   `migration-log/migration-report.md`, whose protocol section is generated **from** that log.
8. **No Liquid literals in `pagecontent`, including inside HTML comments.** Jekyll evaluates `{% … %}`
   and `{{ … }}` everywhere: an invalid `{% … %}` **breaks the build hard**, an unknown `{{ … }}`
   silently empties and leaks into the HTML. Describe such mechanisms in prose.

## Language

Three facts, easy to conflate.

- **The target template's default language is English**, German the translation
  (`i18n-default-lang: en`). Verify it in the target's `sushi-config.yaml` on every run — it moved once
  already. **FHIR artefact identifiers stay English** regardless.
- **A `de-DE` mismatch warning is conditional** — it fires only when the source FSH sets
  `^language = #de-DE`, is cosmetic, and is suppressed in `input/ignoreWarnings.txt` (glob with `%`
  wildcards, not regex; match `%(de-DE)%`), leaving the FSH untouched. Spec §4.1.
- **A German-only source inverts the direction — and that is this skill's to handle.** The normal KDS
  case: the source's narrative is German while the target's default is English, so the German text
  becomes the *translation* of English pages that do not yet exist. Transfer it to
  `input/translations/de/pagecontent/` and produce `input/pagecontent/*.md` as **machine translations of
  it, every page marked `TODO:REVIEW`**, reviewed at Gate C — the one sanctioned exception to guardrail
  3, since each traces to the page it renders. A top-level `language:` in the source is old
  single-language setup, not identity.

## Verification

```bash
grep -rn '{{' . --include='*.yaml' --include='*.yml' --include='*.md' --include='*.json' | grep -v '\${{'
bash "$ML" run 7 sushi-verify -- npx --yes fsh-sushi@3.20.0 .
bash "$ML" run 5.4 fql-scan --emits-runlog -- bash "$SKILL_DIR/scripts/fql-scan.sh" --strict
```

- Every `{{...}}` placeholder accounted for — an unreplaced one ships a bogus artefact silently.
  SUSHI completes without error, and `qa.txt` reports `Errors: 0` with every example validating —
  both shape B: as qualified in step 2b. The IDENTISCH checks below are **not** qualified by shape.
  **Shape B also:** goFSH ran with `-t json-and-xml`, its counts reconcile against the step-1
  inventory, every foreign parent IG was declared with `-d`, `postprocess-gofsh.py` exits 0.
- **Canonical URL diff against the source is empty** — a non-empty diff is a stop, not a warning. Its
  mechanical form is `fhir-ig-analysis`' same-module comparison (step 7): IDENTISCH for identity,
  artifact set and canonical URLs. **The `license` and every other identity value** likewise, or the
  divergence is reported and human-decided.
- `fql-scan.sh --strict` exits 0 **and reports a non-zero scanned-file count**, or every finding is a
  deliberate `TODO:REVIEW`. An empty target set exits 2 and is not a pass. No `[UNKNOWN]` findings.
- **Identity:** every field in `migration-log/identity-claims.tsv` names the source it was read from;
  `bash "$ML" claims` lists each contradiction as a ① decision (it exits 1 while one is open); the
  fields no tier yielded are named at Gate A; **no existing metadata was rewritten** from a recovered
  value. **Parent snapshots (§5.1b.5):** `parent-snapshots.sh detect` exits 0 for every parent, or the
  rebuild is installed as `<id>#<version>-snapshots` with upstream re-verified untouched, every
  generated snapshot larger than its own differential, each generator refusal named — and the SUSHI
  error counts **before and after** the re-pin are both in the log.
- The IG builds both language variants and the German pages render.
  `input/translations/de/ImplementationGuide-<ig-id>.po` has a page-title unit for **every** distinct
  title in the `pages:` tree, every empty `msgstr` is in the ② queue, and `de` appears in a
  `translation-sources` parameter — not only in `i18n-lang`. Confirm on the **built output** (a `/de/`
  breadcrumb renders German). Template example artefacts are gone.
- `migration-log/run.log` exists, every step appears in it with the command it ran and what that
  measurably produced, and every WARN/ERROR is in a report queue. `grep -F 'silent-partial-success:'`
  returns nothing, or each hit is resolved; the protocol section was generated from it, not recalled.

## Mandatory human review gates

| Gate | After step | What is reviewed |
| --- | --- | --- |
| **A** | 4 | Canonical URL, ID **and licence/identity** preservation; artefact completeness; for shape B also the ids goFSH minted and every unresolvable-parent decision |
| **B** | 5 | The narrative, especially any section added to satisfy the Manteldokument |
| **C** | 6 | Language handling and translation, including machine-translated default pages |
| **D** | before merge | Release per KDS governance (TF KDS / AG IOP / NSG) — organizational, not technical. Nothing publishes before it. |

## Scope and delimitation

Covers **moving an existing guide onto the template**: identity preservation, artefact transfer,
directive translation, bilingual setup, and the QA that proves it. Does not cover, deliberately:
**authoring new profiles or remodelling content** (migration never changes normative decisions);
**creating a module from scratch** (the module template ships its own recipe); **translating a guide
already on the template** (the template's `ig-translate` skill); **publishing** (no release, no registry
entry, no package push); and **filling in missing domain content** (a gap in the source is a
`TODO:REVIEW`, not a writing task). If the catalog and a local copy both provide this skill, local wins.

## Provenance

Derived from `skills/mii-ig-migration` in
`forschungsgruppe-digital-health/mii-kds-sample-ig-inoffiziell` at commit
`bd38e2722a594254f3450e73c3fcdbfc2c47b7e8`. **The dated revision history — every change and the
measurement that forced it — is [references/provenance.md](references/provenance.md)**; it is
history, and nothing in it changes what to do on a run.

Original licence: CC-BY-4.0, as declared by the source repository and the source skill; `scripts/` is
Apache-2.0, matching this repository's code licence. Promoted to `stable` on 2026-08-05 after two full
real-task migrations (Dokument, Person), both passing the same-module verification (identity, artifact
set, canonical URLs all IDENTISCH) with baseline-proven QA; the trigger set in
[references/triggers.md](references/triggers.md) was exercised by those runs.
