---
name: mii-ig-wo-ist-was
description: Produces a short "Wo ist was?" orientation PDF after an MII KDS module migration
  from Simplifier onto the MII KDS module template (IG Publisher) - screenshots of the old
  Simplifier navigation tree and the new topic menus, the artifact-page-with-intro pattern as
  an image, and the complete mapping table of every old page to its new location, derived from
  the migration's page-map.tsv. Use this skill when a migration performed with mii-ig-migration
  is done (page-map.tsv exists) and someone asks "wo ist was", "Wo-ist-was-PDF", "Umzugs-PDF",
  "Überblick für die Modul-Autoren/TF-KDS", or a module team needs to find their content in the
  new guide. Do not use for performing the migration itself (see mii-ig-migration) or for
  measuring an IG (see fhir-ig-analysis).
license: CC-BY-4.0
metadata:
  fgdh.tier: "domain"
  fgdh.domain: "fhir-ig"
  fgdh.owner: "@ThomasDeBe"
  fgdh.language: "de"
  fgdh.status: "experimental"
---

# Wo-ist-was-PDF nach einer Modul-Migration

> **Experimental.** This skill has not been verified against a real task since its last change. Verify its output before relying on it.

Ziel: ein **6-seitiges A4-PDF**, das einem Modul-Autor ohne Migrationskontext in fünf Minuten
zeigt, wo jeder Inhalt seines alten Simplifier-Guides im neuen IG-Publisher-IG steckt -
**visuell** (Screenshots alt/neu) **und in Textform** (Zuordnungstabelle). Die Wahrheit über
die Zuordnung ist IMMER die `migration-log/page-map.tsv` des Migrations-Branches (generiert +
reviewt); das PDF ist ihre Renderung für Menschen, nie eine eigene Recherche.

Feste Seitenstruktur (bewährt am Erst-Lauf Modul Bildgebung, 2026-08-28):

| Seite | Inhalt |
|---|---|
| 1 | Titel, Alt/Neu/Stand-Kasten, **die drei Grundideen** (Themen-Menü statt Baum · Profilseiten werden Artefaktseiten · MII-weites verlinkt statt kopiert) |
| 2 | Screenshot: der **vollständig ausgeklappte Simplifier-Navigationsbaum** (zweispaltig, wenn zu lang) |
| 3 | Screenshots: die **neuen Menü-Dropdowns** (Anleitung, Konformität, Artefakte - deutsche Sprachversion) |
| 4 | Screenshot + Erklärung: **das wichtigste Muster** - eine Artefaktseite mit dem alten Seitentext als Intro und den generierten Tabs |
| 5-6 | **Zuordnungstabelle** (jede alte Seite -> neuer Ort + Datei/URL, gruppiert nach altem Baum), Kasten "Neu dazugekommen / Entfallen", Versions-Delta-Hinweis |

## Preconditions

Erkennen, nicht annehmen:

1. **Der Migrations-Branch.** Ein Checkout mit `migration-log/page-map.tsv` (v2:
   `source_page  target  reason  branch  measure`) und `migration-log/source-inventory.json`.
   Fehlt die page-map, STOPP: erst die Migration (mii-ig-migration, Schritt 5.4c) - dieses
   PDF ohne Map wäre Recherche statt Renderung.
2. **Der publizierte Simplifier-Guide.** Guide-Key über
   `https://simplifier.net/<projekt-slug>/filterprojectguides` entdecken (liefert
   `href="/guide/<key>?version=current"`; gemessen: die `~`-Endpunkte und
   `organization/<org>/~projects` liefern 404/nichts). Den Projekt-Slug trägt die Quelle oft
   selbst in `simplifier.net/resolve?...scope=<slug>@current`-Links. Publizierte Version von
   `/published-guide/<key>/versions` notieren. Kein Guide auffindbar -> beim Menschen
   nachfragen, nie einen Key konstruieren.
3. **Der neue IG, gerendert.** Lokaler Build (`output/index.html`) oder das
   gh-pages-Preview `.../branches/<branch-slug>/`. Lokal: aus `output/` per
   `python3 -m http.server <freier Port>` servieren und `http://localhost:<port>/de/index.html`
   verwenden - `file://` ist mit der Chrome-Extension unzuverlässig, und die **deutsche**
   Sprachversion ist die Vergleichsbasis gegen den deutschen Simplifier-Guide. Kein Build
   vorhanden -> erst bauen (Publisher-Aufruf und Umgebungs-Workarounds stehen im
   Migrations-Run-Log des Branches).
4. **Werkzeuge.** Chrome-Extension (claude-in-chrome) für die Screenshots; Python mit
   `reportlab` und `Pillow` für den Builder (`python3 -c "import reportlab, PIL"` prüfen).

## Procedure

Ausgabesprache des PDFs ist Deutsch (Zielgruppe: Modul-Autoren, TF KDS).

1. **Simplifier-Baum screenshotten.** Guide im Browser öffnen, Baum per JavaScript
   vollständig expandieren, `.tree-panel` per CSS-`zoom` (~2.2) vergrößern, mit der
   `zoom`-Screenshot-Action croppen (`save_to_disk: true`), bei langem Baum in zwei Teilen.
   Die gemessenen DOM-Selektoren, der JS-Blocker-Workaround und die Auflösungs-Falle stehen in
   [references/capture-notes.md](references/capture-notes.md) - vor dem ersten Versuch lesen.
2. **Neue Menüs + Artefaktseite screenshotten.** Auf `/de/index.html` je Dropdown
   (Anleitung, Konformität, Artefakte) anklicken und die Navbar-Region croppen. Dann EINE
   repräsentative Artefaktseite mit substanzieller Intro-Note (zentrales Profil des Moduls):
   oberer Seitenteil mit Breadcrumb, Tabs und Intro-Text. Gespeicherte Screenshots sofort aus
   dem Temp-Verzeichnis in ein Arbeitsverzeichnis kopieren.
3. **Zuordnungstabelle aus der page-map ableiten.** Übersetzungsregeln:
   `input/intro-notes/<Type>-<id>-intro.md` -> "Artefaktseite <deutscher Artefaktname> (Intro
   oben, Tabs darunter)" + `<Type>-<id>.html`; `input/pagecontent/<x>.md` -> "Menüpfad ->
   Seitentitel" + `<x>.html`; `RETIRED` -> "entfällt" MIT dem Grund aus der reason-Spalte.
   Extension-Familien dürfen zu einer Zeile zusammengefasst werden; Gruppierung = die Ebenen
   des alten Baums. Dazu die zwei Kästen "Neu ohne Simplifier-Vorgänger" (Artefakt-Übersicht,
   Beispiele, Downloads, Metadaten, Versionierung, Übersetzungshinweise, EN-Version) und
   "Entfallen / ersetzt" (leere Index-Stubs, FQL/XML/JSON-Blöcke -> Tabs, SP-Tabellen ->
   CapabilityStatement, Conformance-/Namenskonventions-Boilerplate -> Meta-Modul, plus
   modulspezifische RETIREDs) sowie der Versions-Delta-Hinweis (publizierter Guide-Stand vs.
   migrierter Branch-Stand, mit den konkret abweichenden Artefakten).
4. **content.json befüllen** nach dem Schema von
   [references/example-bildgebung.json](references/example-bildgebung.json) (der vollständige
   Erst-Lauf-Inhalt). Texte sind reportlab-Paragraph-Markup: Umlaute als UTF-8 oder Entities,
   `&rarr;` für Pfeile - **keine Unicode-Pfeile/Sub-/Superscripts** (Helvetica rendert sie
   als schwarze Kästchen).
5. **PDF bauen:**

   ```bash
   python3 scripts/build_pdf.py --content content.json --shots <screenshot-dir> --out <Modul>-wo-ist-was.pdf
   ```

   Der Builder trägt das feste Layout und bricht mit Namensliste ab, wenn Screenshots fehlen.

## Verification

- `build_pdf.py` exit 0; das PDF hat 5-7 Seiten.
- **Sichtprüfung jeder Seite** (das Read-Tool rendert PDF-Seiten als Bilder): keine schwarzen
  Glyph-Kästchen, Tabellen-Kopf wiederholt sich über Seitenumbrüche, Courier-URLs brechen
  lesbar, Screenshots scharf (Baum-Text lesbar).
- Stichprobe: drei Tabellenzeilen gegen `migration-log/page-map.tsv` rückverfolgen (Ziel und
  RETIRED-Gründe müssen der Map entsprechen, Zeile für Zeile) - und zwei genannte Ziel-URLs im
  gerenderten IG tatsächlich öffnen.
- Beide Versionsstände (publizierter Guide, migrierter Branch) sind im PDF benannt; Branch/PR
  und Erstellungsdatum stehen in der Quellenzeile.

## Scope and delimitation

Deckt ab: das Orientierungs-PDF nach einer vollzogenen Migration - Screenshots, Zuordnung,
Deltas. Deckt bewusst NICHT ab: die Migration selbst und ihre page-map (`mii-ig-migration`);
IG-Vermessung und Vergleiche (`fhir-ig-analysis`); Übersetzung eines Guides
(`fhir-ig-translation`); jede inhaltliche Bewertung der Migration (die gehört in deren
Report und Gates). Existiert dieselbe Skill lokal UND im Katalog, gewinnt die lokale Kopie.
