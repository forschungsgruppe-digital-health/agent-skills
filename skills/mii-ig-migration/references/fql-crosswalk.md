# Simplifier and FQL directives → HL7 IG Publisher crosswalk

Simplifier renders narrative pages with its own directive syntax, including FQL query blocks. The
IG Publisher renders them with Jekyll/Liquid over fragments it generates itself. Migration means
translating between the two, and this file is the mapping plus the reasoning behind it.

## The authoritative rule file

The machine-readable rules are [`fql-rules.tsv`](fql-rules.tsv), tab-separated as
`LABEL ⟶ ERE pattern ⟶ recommendation`. The scanner `scripts/fql-scan.sh` reads **only** that
file, so the table below is documentation and the TSV is the contract.

**Extend it by hand** when a directive is not covered: add one line with a unique label, an ERE
pattern (write curly braces as `\{ \}` so egrep does not read them as an interval), and a
recommendation. The scanner reports uncovered directive-shaped lines as `[UNKNOWN]`, which is the
prompt to add a rule rather than to ignore the line.

Two constraints on patterns, both learned by getting them wrong: ERE has **no lookahead**, so keep
patterns non-overlapping or a single finding is counted twice; and the second pass only skips lines
a specific rule already matched, keyed on `file:line`.

## Mapping table

| Simplifier / FQL | HL7 IG Publisher equivalent |
| --- | --- |
| `{{page-title}}` | remove — the title comes from the template's page set and `input/includes/menu.xml` |
| `{{index:root}}` | remove — the table of contents and navigation are generated |
| `{{pagelink: …, hint: MII_PR_X}}` | `[Text](StructureDefinition-mii-pr-x.html)` (hint = artefact `name` → `id`) |
| `{{link:<id>}}` | artefact link `[Text](<Type>-<id>.html)` |
| `{{render:<image>}}` (png/jpg/svg…) | copy the image into `input/images/` and use `<img src="file">` |
| `{{render:<canonical>}}` (resource) | usually remove — the artefact page is generated — **or** include the matching fragment |
| `{{tree}}` / `{{tree, expand}}` | the `-snapshot` fragment (or `-dict` / `-diff`) |
| `{{xml}}` | the `-xml` fragment |
| `{{json}}` | the `-json-html` fragment |
| `<fql … for differential.element select id, short>` | element table: the `-dict` fragment |
| `<fql>` metadata (url/status/version) | drop it — the publisher generates the header |
| FQL code block (`@` plus a fenced block) | treat as `<fql>` |
| `<tabs>` / `<tab>` (rendering/XML/JSON) | the matching fragment per tab |

`<Type>` is one of `StructureDefinition`, `CodeSystem`, `ValueSet`, `CapabilityStatement`, …;
`<id>` is the artefact `id`. Fragment views available per StructureDefinition include `snapshot`,
`diff`, `dict`, `snapshot-by-mustsupport`, `bindings`, `obligations`, `inv`, `search-params`,
`maps`, `xml` and `json-html`. The publisher generates them under `_includes/`, and the HL7 base
template uses the same fragments in its own layouts — which is why relying on them is safe rather
than clever.

The exact `{% include %}` syntax is deliberately **not** written out in this file. See the build
guard below.

## Build guard: no Liquid literals in `pagecontent`

The IG Publisher renders `pagecontent` pages through Jekyll, and **Liquid evaluates `{% … %}` and
`{{ … }}` everywhere — including inside `<!-- … -->` comments.**

- An invalid `{% … %}` — for instance an example `include` written in a comment — **breaks the
  build hard.**
- A `{{ … }}` with unknown content silently becomes an empty string. No error, but it leaks into
  the HTML.

So: in `pagecontent`, including provenance and TODO comments, write **no** Liquid or Simplifier
directive literals. Describe the mechanism in prose. The real `{% include %}` belongs outside
comments, in the page body where it is meant to run.

This matters more on the MII KDS module template than on most, because the template's own files
are full of `{{PLACEHOLDER}}` values that must be replaced before the guide builds at all.

## Replacing FQL query tables

FQL's main use in KDS guides is generating tables over resource contents. There are two
replacements, and choosing between them is a judgement call:

- **Element or dataset table** (FQL `for differential.element select id, short`) → the `-dict`
  fragment, which renders the element dictionary with paths and definitions inline; or a static
  Markdown table when the FQL query was doing something the dictionary does not express.
- **Cross-resource table** (FQL over several resources) → Liquid over `site.data.*`
  (`structuredefinitions.json`, `resources.json`, `artifacts.json`), iterating and emitting table
  rows. The publisher populates those data files, so this is the supported route rather than a
  workaround.

## Procedure

1. **Scan.** `scripts/fql-scan.sh [path…]` lists file, line, directive and recommendation per
   finding; `[UNKNOWN]` marks directives no rule covered.
2. **Transform.** Apply the recommendation per finding. Ambiguous cases — `{{render:<canonical>}}`
   as remove versus include, `<fql>` as `-dict` versus a static table — take professional
   judgement. When in doubt, mark `TODO:REVIEW` and **invent nothing**.
3. **Re-scan.** `scripts/fql-scan.sh --strict` should exit 0, with the only acceptable exception
   being findings deliberately left as marked `TODO:REVIEW`.
