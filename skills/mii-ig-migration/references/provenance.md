# Provenance and revision history — `mii-ig-migration`

The dated record of what changed in this skill and what measurement forced it. It lives here rather
than in `SKILL.md` because it is history: an agent activating the skill pays for the body on every
run, and none of the entries below changes what it should do. `SKILL.md`'s *Provenance* section
carries the attribution and the licence, which do not move.

## Revision history

Derived from `skills/mii-ig-migration` in
`forschungsgruppe-digital-health/mii-kds-sample-ig-inoffiziell` at commit
`bd38e2722a594254f3450e73c3fcdbfc2c47b7e8`. **2026-07-31** — reworked for a changed target template
(38-row fact inventory): default language reversed German→English, the `hl7-ig-build` branch
convention gone, tool and example paths moved, `references/agent-manifest.yaml` dropped.

**2026-08-01 / 08-02** — first dry run (`kerndatensatz-dokument`) and first full migration (Dokument,
steps 1–7 incl. build): identity gained `license` and a sushi-config-wins rule; target-state discovery
gained the hybrid state; skeleton creation became in-place; the German-only inversion, branch-convention
discovery, scoped placeholder check, recursive `fql-scan.sh` with an empty-target failure, the report
template, the `-xml` → `-xml-html` crosswalk fix and spec §9's Datensatz split all arrived.

**2026-08-05** — retired a false claim: earlier revisions said the IG Publisher cannot localize
`pages:` titles and that an `ImplementationGuide-<id>.po` is ignored. It can, and it is not. Step 6 and
spec §5.5 prescribe the catalogue, `scripts/gen-page-title-po.py` generates it non-destructively, and
§5.5 carries the evidence (our build on IG Publisher 2.2.11, the HL7 `multi-lang-test-ig` `/fr/`
controlled negative) plus what is deliberately not claimed: the menu and the IG's own description.

**2026-08-05** — added **source shape B** (Precondition 2, step 2b, spec §5.1b,
`scripts/postprocess-gofsh.py`), because the previous binary "IG project or stop" gate refused exactly
the modules the skill exists for. Measured end to end against
`medizininformatik-initiative/kerndatensatzmodul-consent` (32 files, read-only; goFSH 2.6.1, SUSHI
3.20.0); deliberately **not** claimed: that Path B produces a clean build. Hardened the same day after
an operator followed it literally and it stopped on itself — pinned `npx`, the repository root as
input, the retired "no narrative" overclaim, the shape-B qualifier on three "clean build" criteria, the
canonical→package recipe for `-d`, four `postprocess-gofsh.py` fixes — and the **run-log convention**
(spec §10) was written in that pass, `.ai-log/` becoming `migration-log/`.

**2026-08-06 — the run log made real.** An operator ran Path B verbatim and almost nothing emitted the
log the convention describes: the goFSH stage wrote no `run.log` line, the mandatory WARN never fired
because nothing compared input to output, SUSHI's 41 → 5 was captured nowhere, and a step running no
bundled script had no way to emit a line. `scripts/migration-log.sh` now supplies `info`/`warn`/`error`,
a `ratio` implementing §10.4, and a `run` wrapper **returning the wrapped command's real exit status** —
the previous `2>&1 | tee -a run.log` reported 0 for a SUSHI run that exited 41. A re-measurement then
found the read-back itself defective, fixed at the cause: raw logs truncated per invocation and the
goFSH table parsed **with its labels** by `scripts/gofsh-results.sh`, so a re-run no longer sums two
tables and Mappings/Invariants are no longer counted as converted resources; `run` gained the 8-bit
exit-status cross-check, `--expected-nonzero` for the anticipated shape-B `sushi-after` and a `begin`
run-boundary; wrapped scripts log `params`/`result`, not a second `start`/`done`; the step-2b block logs
both SUSHI error counts. Measured: 20 of 20 converted with `-t json-and-xml` (no WARN), 1 of 20 without
(WARN), 41 → 5 across the repair, identical on a second run in place.

**2026-08-06 — identity recovered from the published package.** The Consent run stopped at Gate A claiming identity had *no* authoritative source. Measured against `de.medizininformatikinitiative.kerndatensatz.consent@2026.0.0`, the package tarball yields `packageId`, `version` **2026.0.0**, description, `fhirVersions`, `jurisdiction` and the dependency pins, and its 13 resource urls agree unanimously on the canonical — so the genuine Gate-A remainder is three fields (`title`, `license`, `publisher`), not all of them. Spec §2.1.1 ranks that tier (below a repo-local `sushi-config.yaml`, above the goFSH config and every inference), `scripts/package-identity.sh` performs it, and §5.1b.2's version rule now consults the source package **before** `dist-tags.latest` — which had put the parent at `de.einwilligungsmanagement@2.0.3` where the source pins **2.0.2**.

**2026-08-06 — the rest of the identity chain, and the missing-parent-snapshot blocker made executable.** Tier P recovered most of a bare repository's identity but stopped at three fields, and the parent-snapshot condition was still only an escalation. Both now have procedures with evidence. **Identity (§2.1, §2.1.2–§2.1.4):** the tier order is explicit (C, P, J, I, R, H, T; goFSH's config is tier G and never identity), tier **R** — the source repository — supplies the `license` no package manifest carries (`scripts/repo-identity.sh`; measured on Consent: the LICENSE text and GitHub's own detection both read **CC-BY-4.0**, README heading a `title` candidate, tag `2026.0.0` tying the release to the commit), and tier **H** — the Simplifier project page — is documented as *client-rendered* (measured HTTP 200, ~56 KB, 52 script markers, no identity metadata in the DOM) and therefore a **human** reference, not a scrape target. Every field is recorded with its source in `migration-log/identity-claims.tsv` via `migration-log.sh claim`, and a second source disagreeing raises `identity-contradiction:` — reported, never resolved. Gate A for the reference module narrowed from seven fields to three (tier P) to **one, `publisher`** (tier R). **Parent snapshots (§5.1b.5, `scripts/parent-snapshots.sh`):** detection counts the package's snapshots (measured: `de.einwilligungsmanagement` 21 SDs / **0** snapshots in *both* 2.0.2 and 2.0.3), and generation drives the **official** HL7 generator — `java -jar validator_cli.jar snapshot`, ProfileUtilities — never a hand-rolled merge, verifying every result against its own differential and its base's element count so that a differential-only fake cannot pass (DocumentReference 61/45/8, Provenance 65/32/20, Consent 132/57/32). Measured on Consent: 18 of 21 generated, the other three refused by the generator as malformed **upstream** differentials and escalated rather than hand-finished; the rebuild installed as the new cache entry `de.einwilligungsmanagement#2.0.2-snapshots` with upstream re-verified untouched; SUSHI **5 errors → 0**, all three `missing a snapshot` errors and both consequential `InstanceOf … not found` errors gone. The revision history moved out of `SKILL.md` into this file in the same change, to pay for the new normative content within the body budget.
