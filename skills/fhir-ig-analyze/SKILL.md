---
name: fhir-ig-analyze
description: Measures one or more FHIR Implementation Guides read-only and reports the numbers as
  JSON and Markdown — scope, complexity, content hygiene, duplication, linguistics, maturity and
  risk — and compares several IGs side by side using normalised metrics. It builds, changes and
  publishes nothing. Use this skill when reviewing or QA-ing an MII KDS module IG before a release,
  when comparing a module against kerndatensatz-basis or another Implementierungsleitfaden, when
  tracking how a module grows between releases, or when someone asks how large, how clean or how
  mature a guide actually is. Do not use for migrating a guide onto the module template or for
  translating one; see mii-ig-migration and fhir-ig-translate.
license: CC-BY-4.0
allowed-tools: Read Grep Glob Bash(python3:*) Bash(git clone:*)
metadata:
  fgdh.tier: "domain"
  fgdh.domain: "fhir-ig"
  fgdh.owner: "@msusky"
  fgdh.language: "en"
  fgdh.status: "experimental"
---

# Measuring a FHIR Implementation Guide

> **Experimental.** This skill has not been verified against a real task since its last change. Verify its output before relying on it.

Measures a FHIR IG objectively and reports what it counted. **Strictly read-only:** it never
builds, changes, or publishes anything, and it does not forecast.

## Preconditions

Discover the context; do not assume it, and never create it.

1. **The tool.** `python3` must be runnable. The analyser is standard-library only — nothing to
   install. If `python3` is absent, say so and stop; do not fetch an interpreter.

2. **The subject.** One or more IGs, each given as a **local path**, a **git URL**, or a **package
   `.tgz`**. `run` resolves each itself (shallow clone for a URL, download for a package). Nothing
   needs to be discovered inside the repository beyond what the tool reads.
   - A local path with neither `sushi-config.yaml` nor `input/` is not an IG project. Report that
     and stop.
   - A git URL requires network access; if cloning fails, report the failure rather than reporting
     an empty measurement.

3. **Static by default, and know what that costs.** Without a build, the analysis is **static**:
   sushi-config/package metadata, FSH counts, narrative, directives, dependencies, linguistics,
   duplication, hygiene. Build-derived metrics (`qa.json`: errors, warnings, broken links,
   validation) stay `null` and are marked *Build* in the catalog. A package `.tgz` yields a further
   **reduced** analysis — generated resources only.

   State which mode produced the numbers whenever you report them. A `null` is not a zero.

## Procedure

**The generated reports are in German**; this skill's instructions are in English. That is
deliberate and does not follow from either fact on its own — the report prose was inherited and has
not been translated. Do not "fix" it silently, and do not translate the numbers.

1. **Measure.** One IG or several, from the IG's root or anywhere:

   ```bash
   python3 scripts/ig-stats.py run <input…> [-o OUTDIR] [--label a,b]
   ```

   With two or more inputs this writes one report per IG **plus** `compare-report.md`
   automatically.

2. **Power-user entry points**, when you want the stages separately:

   ```bash
   python3 scripts/ig-stats.py analyze <ig-dir> [-o stats.json]
   python3 scripts/ig-stats.py report  <stats.json>  [-o report.md]
   python3 scripts/ig-stats.py compare <stats.json…> [-o compare.md]
   ```

3. **Read the mandatory-page finding carefully.** The page set the tool checks against lives in
   [`references/report-content.json`](references/report-content.json) under `mandatory_pages` and is
   **hand-editable on purpose**. It is seeded with the MII KDS module template's actual page names.

   If a measured IG legitimately uses a different page set, correct the list rather than reporting
   its pages as missing — and say in your report which list you used. A page-completeness metric is
   only as good as the set it compares against.

4. **Report both artefacts.** The JSON is the durable one: it has a fixed schema, so a series of
   runs diffs cleanly and shows how a module grows between releases. The Markdown is for people.

5. **Compare only on normalised metrics.** Absolute counts across IGs of different size say almost
   nothing; the comparison report aggregates a Σ total for scope but the fair columns are the
   normalised ones.

## Verification

```bash
python3 scripts/ig-stats.py run <ig-dir> -o /tmp/igstats
python3 -c "import json;d=json.load(open('/tmp/igstats/<name>-stats.json'));print(d['mode'],d['schemaVersion'])"
```

- The run exits 0 and writes one `*-stats.json` and one `*-report.md` per input.
- With ≥2 inputs, `compare-report.md` exists.
- `mode` in the JSON matches what you claim (`static` / `reduced`), and `schemaVersion` is present.
- **Every metric you quote is either a counted number or `null`** — never an estimate. If a field is
  `null`, report it as not derivable statically rather than as zero.
- The mandatory-page result is plausible against the IG you measured. All-missing usually means the
  wrong page set, not a broken IG.

## Scope and delimitation

Covers **measurement and comparison**: what is in an IG, how clean it is, how it compares, how it
changes over time.

Deliberately not covered:

- **Effort forecasting.** The tool reports what it counted. It does not estimate person-days, cost
  or a readiness score, and an earlier version of this skill that framed the numbers as migration
  scoping was narrowed on purpose. Do not reintroduce it: a measurement dressed as a forecast is
  the least trustworthy thing this skill could produce.
- **Migration** onto the MII KDS module template — see `mii-ig-migration`.
- **Translation** — see `fhir-ig-translate`.
- **Convention and naming checks** against the MII meta wiki or the metadata contract. Those are a
  different check, and the module template ships its own skill for them.
- **Building or publishing anything.** Read-only is a guardrail, not a default.

If a skill of this name is provided both by this catalog and locally, the local one wins.

## Guardrails

- **Read-only.** Never modify the analysed IG; never force a build.
- **Measurement, not forecasting.** See above.
- **Fair comparison only via normalised metrics.**
- **No invention.** A missing input yields `null`, never a guess. Heuristic metrics are marked as
  heuristics in the catalog and must be reported as such.

## References

- [`references/metrics-catalog.md`](references/metrics-catalog.md) — the parameter catalog
  (groups A–N), each metric with its source and its use. Hand-extensible; this is the SSOT for what
  is measured.
- [`references/ig-stats-schema.json`](references/ig-stats-schema.json) — the schema of
  `ig-stats.json`.
- [`references/report-content.json`](references/report-content.json) — plain-language texts,
  glossary, directive patterns, metric explanations, and the `mandatory_pages` list. Hand-editable.
- [`references/triggers.md`](references/triggers.md) — the Gate 3 prompt set.
- [`scripts/ig-stats.py`](scripts/ig-stats.py) — the analyser (`run` / `analyze` / `report` /
  `compare`).

## Provenance

Derived from `skills/ig-analyze` in
`forschungsgruppe-digital-health/mii-kds-module-template` at commit
`b5beedb17a66a4397d597429668c7b6d54202c62`, which in turn adapted the `ig-analyze` skill of
`forschungsgruppe-digital-health/mii-kds-sample-ig-inoffiziell` (CC-BY-4.0). Both steps of that
lineage are recorded deliberately.

Reworked on 2026-07-31 for this catalog. Beyond the catalog contract, three substantive changes:

- The analyser now ships **with** the skill. It previously lived in the source repository's
  `scripts/` and was referenced by parent traversal, so the skill pointed at a file it could not
  reach once installed elsewhere.
- `scripts/ig-stats.py` locates `references/report-content.json` relative to **its own path**. It
  previously built that path from a computed repository root plus a hard-coded
  `skills/ig-analyze/references/…`, which broke twice here: there is no repository root to compute,
  and the skill was renamed.
- The mandatory-page list moved out of the code into `references/report-content.json` and was
  corrected. The inherited list named eleven pages of which **six do not exist** in the template
  modules are built from (`use-cases`, `data-sets`, `uml`, `context`, `references`,
  `security-privacy`), so every measurement reported six false missing pages.

Original licence: CC-BY-4.0, as declared by both source repositories. `scripts/` is Apache-2.0,
matching this repository's code licence.
