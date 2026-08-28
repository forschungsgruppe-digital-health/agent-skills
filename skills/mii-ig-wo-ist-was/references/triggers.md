# Trigger-Prompts

Prompts, die DIESE Skill aktivieren sollen:

1. "Kannst du ein kurzes Wo-Ist-Was-PDF machen, gerne mit Simplifier-Screenshots des
   hierarchischen Navbars und Verweisen auf die Position im neuen IG?" (der Original-Prompt
   des Erst-Laufs, Modul Bildgebung)
2. "Mach das Umzugs-PDF für das Modul Labor - die Migration ist durch."
3. "Die TF KDS braucht einen Überblick, wo die alten Simplifier-Seiten im neuen IG gelandet sind."
4. "Wo ist was im neuen Bildgebungs-IG? Bitte als PDF für die Modul-Autoren."
5. "Erstell die Orientierungshilfe alt->neu für das migrierte Consent-Modul, visuell und als Tabelle."

Prompts, die eine NACHBAR-Skill aktivieren sollen:

1. "Migriere das Modul Prozedur vom Simplifier-Setup aufs MII-KDS-Modul-Template." ->
   `mii-ig-migration` (die Migration selbst; dieses PDF setzt deren page-map.tsv voraus)
2. "Wie groß und wie reif ist der Bildgebungs-IG im Vergleich zu kerndatensatz-basis?" ->
   `fhir-ig-analysis` (Vermessung/Vergleich, kein Orientierungs-PDF)
