#!/usr/bin/env bash
# fql-scan -- find Simplifier and FQL render directives in narrative pages and
# name the HL7 IG Publisher equivalent for each finding.
#
# It REPORTS ONLY. It never transforms: the transformation takes professional
# judgement per finding, and a script that guessed would violate the skill's
# no-fabrication guardrail. See references/fql-crosswalk.md.
#
# Mapping rules come from references/fql-rules.tsv, which is the single source
# of truth and is extensible by hand -- add a line
# `LABEL<TAB>ERE-pattern<TAB>recommendation`.
#
# Run it from the root of the module repository being migrated:
#
#   scripts/fql-scan.sh                          # scans input/pagecontent/*.md
#   scripts/fql-scan.sh input/pagecontent/x.md   # specific files or directories
#   scripts/fql-scan.sh --strict                 # exit 1 if anything was found
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
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) ARGS="$ARGS $a" ;;
  esac
done
[ -n "$ARGS" ] || ARGS="input/pagecontent"

if [ ! -f "$RULES" ]; then
  echo "ERROR: rules file not found: $RULES" >&2
  echo "The skill directory appears incomplete -- references/fql-rules.tsv is required." >&2
  exit 2
fi

# Collect target files (.md only).
TARGETS=""
for p in $ARGS; do
  if [ -d "$p" ]; then
    for f in "$p"/*.md; do [ -e "$f" ] && TARGETS="$TARGETS $f"; done
  elif [ -f "$p" ]; then
    TARGETS="$TARGETS $p"
  else
    echo "WARNING: no such file or directory: $p" >&2
  fi
done
if [ -z "$TARGETS" ]; then
  echo "No .md target files under: $ARGS"
  exit 0
fi

echo "== fql-scan (rules: $RULES) =="
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
  echo "No Simplifier or FQL directives found."
else
  echo "$total mapped finding(s), $unknown unknown."
  echo "Transform per references/fql-crosswalk.md; when in doubt mark TODO:REVIEW."
  echo "Rule missing or imprecise? Add a line to $RULES (LABEL<TAB>ERE-pattern<TAB>recommendation)."
fi

if [ "$STRICT" = 1 ] && [ "$total_all" -gt 0 ]; then
  exit 1
fi
exit 0
