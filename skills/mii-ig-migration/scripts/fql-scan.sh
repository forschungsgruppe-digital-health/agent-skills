#!/usr/bin/env bash
# fql-scan -- find Simplifier and FQL render directives in narrative pages and
# name the HL7 IG Publisher equivalent for each finding.
#
# It REPORTS ONLY. It never transforms: the transformation takes professional
# judgement per finding, and a script that guessed would violate the skill's
# no-fabrication guardrail. See references/fql-crosswalk.md.
#
# Mapping rules come from references/fql-rules.tsv, which is the single source
# of truth for THIS scanner and is extensible by hand -- add a line
# `LABEL<TAB>ERE-pattern<TAB>recommendation`. (The fhir-ig-analysis skill keeps
# a derived pattern set; the catalog's check_directive_rules.py keeps the two
# label taxonomies in sync.)
#
# Run it from the root of the module repository being migrated:
#
#   fql-scan.sh                          # input/pagecontent, plus implementation-guides
#                                        #   when present (Simplifier layout), RECURSIVE
#   fql-scan.sh some/dir a/file.md       # specific files or directories (dirs recursive)
#   fql-scan.sh --strict                 # exit 1 if anything was found
#
# Exit codes: 0 = scanned (findings are informational without --strict);
# 1 = --strict and findings exist; 2 = setup error: missing rules file, or an
# EMPTY TARGET SET -- an empty scan is never a pass.
#
# Bash 3.2 compatible, because macOS still ships 3.2.
#
# Portability note: this resolves its rules file relative to ITSELF, not
# relative to a repository root. The original lived at <repo>/tools/ and did
# `cd "$(dirname "$0")/.."`, which broke the moment the script moved. A skill is
# installed into repositories nobody anticipated, so the only safe anchor is the
# script's own location.
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR" && cd .. && pwd)"
RULES="$SKILL_ROOT/references/fql-rules.tsv"

STRICT=0
ARGS=""
for a in "$@"; do
  case "$a" in
    --strict) STRICT=1 ;;
    -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
    *) ARGS="$ARGS $a" ;;
  esac
done
if [ -z "$ARGS" ]; then
  ARGS="input/pagecontent"
  # A Simplifier project keeps its narrative under implementation-guides/**/*.page.md.
  # A pre-migration scan that misses those reads "0 directives" on a module that has
  # hundreds -- so the default includes the directory whenever it exists.
  [ -d implementation-guides ] && ARGS="$ARGS implementation-guides"
fi

if [ ! -f "$RULES" ]; then
  echo "ERROR: rules file not found: $RULES" >&2
  echo "The skill directory appears incomplete -- references/fql-rules.tsv is required." >&2
  exit 2
fi

# Collect target files (.md only; directories are searched RECURSIVELY -- a flat
# glob missed the nested implementation-guides/**/*.page.md layout entirely).
TARGETS=""
for p in $ARGS; do
  if [ -d "$p" ]; then
    for f in $(find "$p" -type f -name '*.md' | sort); do TARGETS="$TARGETS $f"; done
  elif [ -f "$p" ]; then
    TARGETS="$TARGETS $p"
  else
    echo "WARNING: no such file or directory: $p" >&2
  fi
done
if [ -z "$TARGETS" ]; then
  echo "ERROR: empty target set -- no .md files under: $ARGS" >&2
  echo "       An empty scan is never a pass. Point the scanner at the narrative" >&2
  echo "       sources (input/pagecontent, or implementation-guides for a" >&2
  echo "       Simplifier project), or run it from the module repository's root." >&2
  exit 2
fi
NFILES=0
for f in $TARGETS; do NFILES=$((NFILES + 1)); done

echo "== fql-scan (rules: $RULES) =="
echo "Scanning $NFILES file(s)."
total=0
MATCHED=""   # "file:line" per specific-rule hit, so the unknown pass can skip them

while IFS="$(printf '\t')" read -r label regex recommendation; do
  case "$label" in ''|\#*) continue ;; esac
  [ -n "$regex" ] || continue
  for f in $TARGETS; do
    while IFS= read -r hit; do
      [ -n "$hit" ] || continue
      ln="${hit%%:*}"
      txt="${hit#*:}"
      snip="$(printf '%s' "$txt" | sed 's/^[[:space:]]*//' | cut -c1-80)"
      echo "  $f:$ln  [$label]"
      echo "      found:  $snip"
      echo "      action: $recommendation"
      MATCHED="$MATCHED
$f:$ln"
      total=$((total + 1))
    done <<EOF
$(grep -nE "$regex" "$f" 2>/dev/null)
EOF
  done
done < "$RULES"

# Second pass: directive-shaped lines that no rule covered. An [UNKNOWN] is the
# signal to add a rule, not to ignore the line.
unknown=0
GENERIC='\{\{[A-Za-z]|<fql|@```|</?tab'
for f in $TARGETS; do
  while IFS= read -r hit; do
    [ -n "$hit" ] || continue
    ln="${hit%%:*}"
    txt="${hit#*:}"
    case "$MATCHED" in *"$f:$ln"*) continue ;; esac
    snip="$(printf '%s' "$txt" | sed 's/^[[:space:]]*//' | cut -c1-80)"
    echo "  $f:$ln  [UNKNOWN]"
    echo "      found:  $snip"
    echo "      action: no rule matched -- review, and add a line to fql-rules.tsv if it recurs."
    unknown=$((unknown + 1))
  done <<EOF
$(grep -nE "$GENERIC" "$f" 2>/dev/null)
EOF
done

echo
total_all=$((total + unknown))
if [ "$total_all" -eq 0 ]; then
  echo "No Simplifier or FQL directives found in $NFILES scanned file(s)."
else
  echo "$total mapped finding(s), $unknown unknown, in $NFILES scanned file(s)."
  echo "Transform per references/fql-crosswalk.md; when in doubt mark TODO:REVIEW."
  echo "Rule missing or imprecise? Add a line to $RULES (LABEL<TAB>ERE-pattern<TAB>recommendation)."
fi

if [ "$STRICT" = 1 ] && [ "$total_all" -gt 0 ]; then
  exit 1
fi
exit 0
