# Browser-Capture-Notizen (gemessen am Erst-Lauf Bildgebung, 2026-08-28)

Alle Punkte sind auf einem realen Lauf gemessen, nicht vermutet. Chrome-Extension
(claude-in-chrome), macOS.

## Simplifier-Guide

- **Guide-Key-Discovery:** `https://simplifier.net/<projekt-slug>/filterprojectguides` (ohne
  Tilde!) liefert `href="/guide/<key>?version=current"` und
  `/published-guide/<key>/versions`. Gemessen 404/leer: `simplifier.net/organization/<org>/~projects`,
  Tilde-Varianten. Der Projekt-Slug taucht in Quell-Guides als
  `simplifier.net/resolve?...scope=<slug>@current` auf.
- **Baum-DOM:** Der Navigationsbaum ist `div.tree-panel > div.tree-content > table.treetable`.
  Zeilen: `tr.treenode`, Wurzel `tr.rootnode`, kollabiert = Klasse `collapsed`.
  **Toggle-Element ist `span.vjoinendexpandable` bzw. `span.vjoinexpandable`** in der Zeile -
  das erste beste `span` der Zeile zu klicken toggelt NICHT zuverlässig.
- **Expandieren iterativ:** Nach jedem Klick-Durchgang tauchen neue kollabierte Kinder auf.
  Das javascript_tool-Snippet mehrfach ausführen, bis `collapsed`-Count 0 (Bildgebung: 8 ->
  41 Knoten in 3 Durchgängen).
- **JS-Blocker der Extension:** Skripte mit `await`/`setTimeout`-Schleifen wurden als
  "[BLOCKED: Cookie/query string data]" abgelehnt; **einfache synchrone Einzeiler mit
  `var`/`forEach` gehen durch.** Deshalb: ein Snippet, mehrfach aufrufen, statt einer Schleife
  mit Warten.
- **Auflösung:** Der Standard-Viewport-Crop des Baums ist ~200 px breit -> im PDF unscharf.
  Fix: `document.querySelector('.tree-panel').style.zoom='2.2'` (plus `background='#ffffff'`),
  dann croppen. Browser-Zoom-Shortcuts (cmd+=) unterstützt das computer-Tool nicht.
- **Langer Baum:** passt bei zoom 2.2 nicht in den Viewport -> Teil 1 croppen, per
  `scroll`-Action (~6 Ticks) weiterscrollen, Teil 2 croppen. Überlappung ist okay und hilft
  beim Lesen.
- **Crop + Speichern:** `computer`-Action `zoom` mit `region` und `save_to_disk: true`;
  gespeicherte Pfade liegen in einem Temp-Verzeichnis -> sofort ins Scratchpad/Zielverzeichnis
  kopieren (Temp kann verschwinden).

## Neuer IG (Template-Build)

- **Servieren statt file://:** `cd output && python3 -m http.server <port>`, dann
  `http://localhost:<port>/de/index.html`. Die **/de/**-Version nehmen - deutscher Guide gegen
  deutschen Guide.
- **Dropdowns:** Klick auf den Menüpunkt öffnet das Dropdown stabil; danach Navbar-Region
  croppen (ca. y=45..230 für kurze, ..420 für lange Dropdowns bei 1568er-Viewport).
- **Artefaktseiten-URL-Schema:** `StructureDefinition-<id>.html` (auch unter /de/). Für das
  Muster-Bild eine Seite mit substanzieller Intro-Note wählen (zentrales Profil des Moduls).
- Der lokale Server muss weiterlaufen, solange der Tab offen bleiben soll.

## PDF (reportlab)

- Helvetica hat **kein ↗ (U+2197)** und keine Unicode-Sub-/Superscripts -> schwarze Kästchen.
  Pfeile als Text umschreiben ("Pfeil-Symbol = extern") oder `&rarr;` (funktioniert).
- Umlaute/ß über HTML-Entities in Paragraph-Markup sind zuverlässig.
- Ergebnis IMMER mit dem Read-Tool (rendert PDF-Seiten als Bilder) sichtprüfen:
  Glyphen, Zeilenumbrüche in der Tabelle (Courier-URLs brechen hart), Bildschärfe.
- Bilder über PIL vermessen und proportional auf max-Breite/Höhe skalieren (der Builder
  macht das); `repeatRows=1` für die Tabellen-Kopfzeile über Seitenumbrüche.
