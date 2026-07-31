# ig-translate — mechanics, file conventions, formats

As of 2026; empirically verified with IG Publisher 2.2.7/2.2.8 +
`fhir2.base.template`. The authoritative tool logic is `scripts/ig-translate.sh`.

## 1. Resource texts (render today)

**Supported resource types** (Publisher constant
`TRANSLATION_SUPPLEMENT_RESOURCE_TYPES`): **StructureDefinition, CodeSystem,
Questionnaire**. Not supported: ValueSet, ImplementationGuide,
CapabilityStatement.

**Placement & naming:** one translation supplement per resource under the
translation-sources folder (`translation-sources: input/translations/<lang>`):

```
input/translations/de/<ResourceType>-<id>.<ext>     # ext ∈ {po, xliff, json}
```

Examples (for a "Dokument" module):
- `input/translations/de/StructureDefinition-mii-pr-dokument-dokument.po`
- `input/translations/de/StructureDefinition-mii-ex-dokument-nlp-processing-status.po`
- `input/translations/de/StructureDefinition-mii-lm-dokument.po`  (Logical Model = StructureDefinition)
- `input/translations/de/CodeSystem-mii-cs-dokument-nlp-processing-status.po`

> A wrong name (for example `ImplementationGuide-…po`, `menu.po`, or any
> non-`{type}-{id}` name) is **ignored** by the Publisher (log: "name is not
> {type}-{id}.xxx" / "resource type … is not supported").

**`.po` format** (preferred; case-insensitive matching, plural forms):

```po
#: StructureDefinition.description
msgid "<exact English source text from the generated resource>"
msgstr "<German translation>"
```

`msgid` MUST match the English source text of the generated resource exactly
(from `fsh-generated/resources/<Type>-<id>.json`). Translatable fields include:
`description`, element `definition`/`comment`/`requirements`, binding
descriptions, CodeSystem `concept.display`/`definition`/`designation`.

## 2. ValueSet / IG title / menu (do NOT render)

There is no supplement mechanism in the current Publisher. Leave these out on
purpose; do not "simulate" them with wrongly named `.po` files (they would only
be ignored). Add them here once a future Publisher supports them.

## 3. Narrative pages (these DO render translated)

**Convention** (as used by the HL7 reference `FHIR/multi-lang-test-ig`): the
translated page goes in the translation-source folder, under `pagecontent/`,
with the **same file name** as the default-language page:

```
input/pagecontent/<name>.md                    # English (default / source)
input/translations/de/pagecontent/<name>.md    # German — renders on /de/<name>.html
```

Content rules:
- Copy structure/headings/links 1:1; leave internal artifact links
  (`StructureDefinition-…html` etc.) **unchanged**.
- Do not translate FHIR identifiers, code values, or canonical URLs.
- Leave embedded HTML/image references unchanged.
- Add a `TODO:REVIEW` header line on machine translation.

> Behaviour today (verified IG Publisher 2.2.11): `/de/<name>.html` renders the
> translated page. A page with no translation file falls back to the English
> source. Do NOT use a `<name>-de.md` sibling in `input/pagecontent/` — the
> toolchain would treat it as a separate page, not a translation.

## 4. Configuration parameters (`sushi-config.yaml`)

```yaml
parameters:
  i18n-default-lang: en          # default (source) language
  i18n-lang:
    - de                         # additional rendered language(s)
  translation-sources:
    - input/translations/de      # folder holding the supplements
```

## 5. Guardrails (summary)

The English source leads · add to the source, never modify it · leave FHIR
identifiers in English · no invention, mark `TODO:REVIEW` · a bilingual human
language review is mandatory · only on confirmation, dry-run default.
