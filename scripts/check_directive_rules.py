#!/usr/bin/env python3
"""Keep the two directive-detection taxonomies in sync across skills.

Two files in this catalog detect the same Simplifier/FQL directives:

- ``skills/mii-ig-migration/references/fql-rules.tsv`` — the NORMATIVE label
  taxonomy, driving ``fql-scan.sh`` and the migration skill's Definition of
  Done.
- ``skills/fhir-ig-analysis/references/report-content.json`` — a DERIVED
  pattern set under ``directive_patterns``, driving the analysis skill's
  directive metric.

Both are hand-extensible, and they drifted once (11 vs 12 labels, 129 vs 130
findings on the same corpus — dry-run finding F-09). This check makes the drift
a CI failure instead of a silent disagreement.

The only sanctioned divergence is a finer split on the analysis side, declared
in ``SPLITS`` below: extending either file means either mirroring the label or
extending ``SPLITS`` deliberately in the same change.

Deterministic: exit 0 when the taxonomies agree, 1 with a per-label report when
they do not, 2 when an input file is missing or unparsable.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TSV = ROOT / "skills" / "mii-ig-migration" / "references" / "fql-rules.tsv"
JSON_ = ROOT / "skills" / "fhir-ig-analysis" / "references" / "report-content.json"

# Sanctioned refinements: one tsv label may map to a SET of analysis labels.
SPLITS = {"render": {"render-image", "render-resource"}}


def tsv_labels(path: pathlib.Path) -> set[str]:
    labels: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 3 and parts[0].strip():
            labels.add(parts[0].strip())
    return labels


def main() -> int:
    try:
        tsv = tsv_labels(TSV)
    except OSError as exc:
        print(f"::error::cannot read {TSV}: {exc}")
        return 2
    try:
        patterns = json.loads(JSON_.read_text(encoding="utf-8")).get("directive_patterns")
    except (OSError, json.JSONDecodeError) as exc:
        print(f"::error::cannot read {JSON_}: {exc}")
        return 2
    if not isinstance(patterns, dict) or not patterns:
        print(f"::error::{JSON_} has no directive_patterns object")
        return 2
    analysis = set(patterns)

    expected = set()
    for label in tsv:
        expected |= SPLITS.get(label, {label})

    missing_in_analysis = sorted(expected - analysis)
    extra_in_analysis = sorted(analysis - expected)

    print(f"fql-rules.tsv: {len(tsv)} label(s); directive_patterns: {len(analysis)} label(s); "
          f"sanctioned splits: {sorted(SPLITS)}")
    ok = True
    for label in missing_in_analysis:
        print(f"::error::label '{label}' exists in fql-rules.tsv (possibly via a split) "
              f"but not in report-content.json directive_patterns")
        ok = False
    for label in extra_in_analysis:
        print(f"::error::label '{label}' exists in report-content.json directive_patterns "
              f"but has no counterpart in fql-rules.tsv — mirror it there, or add a "
              f"deliberate entry to SPLITS in {pathlib.Path(__file__).name}")
        ok = False
    # Behavior-level assertion (issue #34): both detectors score the shared
    # fixture corpus identically — label sets can agree while patterns drift
    # (the render-image <img>/raw-URL false positives were invisible to the
    # set comparison above). The corpus carries one hit per label plus traps
    # (carried HTML, provenance URLs) that must score zero.
    corpus = pathlib.Path(__file__).resolve().parent / "fixtures" / "directive-corpus.md"
    if not corpus.exists():
        print(f"::error::fixture corpus missing: {corpus}")
        return 2
    lines = corpus.read_text(encoding="utf-8").splitlines()
    trap_start = next(i for i, l in enumerate(lines) if l.startswith("## Traps"))

    import subprocess, tempfile, collections
    # analysis-side: apply directive_patterns per line (mirrors scan_directives)
    pats = {k: re.compile(v) for k, v in patterns.items()}
    ana = collections.Counter()
    ana_trap_hits = []
    for i, ln in enumerate(lines):
        for label, rx in pats.items():
            if rx.search(ln):
                ana[label] += 1
                if i > trap_start:
                    ana_trap_hits.append((label, ln.strip()[:60]))
    # scanner-side: run fql-scan.sh on the corpus
    r = subprocess.run(["bash", str(ROOT / "skills" / "mii-ig-migration" / "scripts" / "fql-scan.sh"),
                        str(corpus)], capture_output=True, text=True)
    scan = collections.Counter(re.findall(r"\[([a-z-]+)\]", r.stdout))
    scan_trap_hits = [l for l in r.stdout.splitlines()
                      if ":" in l and "[" in l and any(
                          int(m) > trap_start + 1 for m in re.findall(r":(\d+)\s+\[", l))]
    # fold the sanctioned split for comparison
    ana_folded = collections.Counter()
    for label, n in ana.items():
        folded = next((k for k, v in SPLITS.items() if label in v), label)
        ana_folded[folded] += n
    if ana_trap_hits:
        for label, ln in ana_trap_hits:
            print(f"::error::directive_patterns scores a TRAP line as '{label}': {ln}")
        ok = False
    if scan_trap_hits:
        for l in scan_trap_hits:
            print(f"::error::fql-scan scores a TRAP line: {l.strip()[:100]}")
        ok = False
    if dict(ana_folded) != dict(scan):
        print(f"::error::corpus counts diverge — analysis (folded): {dict(ana_folded)} vs fql-scan: {dict(scan)}")
        ok = False
    else:
        print(f"corpus counts agree: {dict(scan)}")
    if ok:
        print("directive-rule taxonomies are in sync (labels + corpus behavior)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
