# Directive-detection fixture corpus

Both detectors — fql-scan.sh (fql-rules.tsv, normative) and fhir-ig-analysis'
directive_patterns — must score this file identically (modulo the sanctioned
render split). check_directive_rules.py asserts it.

## One hit per label

{{page-title}}
{{index:root}}
{{pagelink:MIIIGModulDokument/Some/Page.page.md}}
{{link:mii-pr-example}}
{{render:implementation-guides/images/Diagram.png}}
{{render:CapabilityStatement}}
{{tree, expand}}
{{xml:Example}}
{{json:Example}}
<fql headers="true"> from StructureDefinition select url </fql>
@```
from StructureDefinition for differential.element select id, short
```
<tabs><tab title="XML"></tab></tabs>

## Traps — none of these is a Simplifier directive (expected: zero findings)

A GitHub-Actions expression looks like this: see workflow docs (dollar-brace form).
<img src="local.png" alt="carried HTML image"/>
Provenance note style: original was https://raw.githubusercontent.com/example/repo/main/input/plantuml/X.svg
https://licensebuttons.net/l/by/4.0/88x31.png
