#!/usr/bin/env bash
# ig-translate — helper for translating an IG-Publisher-based FHIR IG into a
# non-default language.
# Deterministically determines the target files the IG PUBLISHER EXPECTS for
# translations and validates the naming/placement conventions. It does NOT
# translate itself (an agent/human does that) and creates nothing without being
# asked.
#
# Run it from the root of the module IG you are translating, or pass that root as
# a third argument:
#
#   scripts/ig-translate.sh --scan <lang>              # target path per page/resource
#   scripts/ig-translate.sh --validate <lang>          # check existing translation files
#   scripts/ig-translate.sh --scan <lang> path/to/ig   # operate on another directory
#
# <lang> is REQUIRED and is not defaulted. It used to default to 'de', which
# meant a run could silently target a language nobody chose. Derive it from the
# guide's own sushi-config.yaml (i18n-lang), never from habit.
#
# Portability note: this operates on the CURRENT WORKING DIRECTORY, not on a path
# derived from the script's own location. The original did
# `cd "$(dirname "$0")/.."`, which assumed the script sat in <module-repo>/scripts/.
# Installed as part of a skill it sits in <somewhere>/skills/<name>/scripts/, where
# that `cd` reaches the skill directory instead of the IG — and the scan would then
# silently report every page as missing.
#
# Verified: translation supplements render only for StructureDefinition,
# CodeSystem, Questionnaire (Publisher restriction). A narrative page is
# translated by mirroring input/pagecontent/<name>.md (the default language)
# into input/translations/<lang>/pagecontent/<name>.md — the SAME file name; a
# <name>-<lang>.md sibling is rendered as a separate page, not as a translation.
# Bash 3.2 compatible.
set -u

MODE=""
LANG_CODE=""
case "${1:-}" in
  --scan) MODE=scan; LANG_CODE="${2:-}";;
  --validate) MODE=validate; LANG_CODE="${2:-}";;
  *) echo "Usage: $0 --scan <lang> | --validate <lang> [ig-root]" >&2; exit 2;;
esac

if [ -z "$LANG_CODE" ]; then
  echo "ERROR: a target language is required, e.g. '$0 $1 de'." >&2
  echo "       Take it from the guide's sushi-config.yaml (parameters.i18n-lang)." >&2
  echo "       It is deliberately not defaulted: a default would silently target a" >&2
  echo "       language nobody chose." >&2
  exit 2
fi

IG_ROOT="${3:-.}"
cd "$IG_ROOT" || { echo "ERROR: cannot enter '$IG_ROOT'" >&2; exit 2; }

# Detect that this really is a FHIR IG project before reporting anything. Without
# this the scan happily lists zero pages and zero resources, which reads exactly
# like "nothing to translate" instead of "you are in the wrong directory".
if [ ! -d input/pagecontent ] && [ ! -f sushi-config.yaml ] && [ ! -f ig.ini ]; then
  echo "ERROR: '$(pwd)' does not look like a FHIR IG project." >&2
  echo "       Expected input/pagecontent/, sushi-config.yaml or ig.ini." >&2
  echo "       Run this from the module IG's root, or pass the root as a third argument." >&2
  exit 2
fi

SUPPORTED="StructureDefinition CodeSystem Questionnaire"   # Publisher supplement types
TSRC="input/translations/$LANG_CODE"
GEN="fsh-generated/resources"

# List "<ResourceType> <id>" per generated resource (only supported types matter)
list_resources() {
  [ -d "$GEN" ] || return 0
  python3 - "$GEN" <<'PY'
import json,sys,glob,os
gen=sys.argv[1]
for f in sorted(glob.glob(os.path.join(gen,"*.json"))):
    try: d=json.load(open(f,encoding="utf-8"))
    except Exception: continue
    rt=d.get("resourceType"); rid=d.get("id")
    if rt and rid: print(rt, rid)
PY
}

echo "== ig-translate --$MODE $LANG_CODE =="

if [ "$MODE" = scan ]; then
  echo "-- Narrative pages --"
  if [ -d input/pagecontent ]; then
    for p in input/pagecontent/*.md; do
      [ -e "$p" ] || continue
      base="$(basename "$p" .md)"
      tgt="$TSRC/pagecontent/${base}.md"
      [ -e "$tgt" ] && st="[present]" || st="[missing]"
      echo "   $p -> $tgt $st"
    done
  fi
  echo "-- Resource supplements (render: only SD/CS/Questionnaire) --"
  list_resources | while read -r rt rid; do
    case " $SUPPORTED " in
      *" $rt "*)
        tgt="$TSRC/${rt}-${rid}.po"
        [ -e "$tgt" ] && st="[present]" || st="[missing]"
        echo "   $rt/$rid -> $tgt $st";;
      *)
        echo "   $rt/$rid -> (no supplement support; skipped)";;
    esac
  done
  echo
  echo "Note: a supplement's msgid = the exact DEFAULT-LANGUAGE source text from $GEN/<Type>-<id>.json."
  exit 0
fi

# --- validate ---
fail=0
echo "-- checking existing supplements ($TSRC) --"
if [ -d "$TSRC" ]; then
  for f in "$TSRC"/*.po "$TSRC"/*.xliff "$TSRC"/*.json; do
    [ -e "$f" ] || continue
    bn="$(basename "$f")"; stem="${bn%.*}"
    rt="${stem%%-*}"; rid="${stem#*-}"
    case "$bn" in menu.*) echo "   [WARN] $bn — ignored by the Publisher (not {Type}-{id})"; fail=1; continue;; esac
    case " $SUPPORTED " in
      *" $rt "*) ;;
      *) echo "   [WARN] $bn — type '$rt' is NOT supported as a supplement (ignored)"; fail=1; continue;;
    esac
    if [ -f "$GEN/${rt}-${rid}.json" ]; then echo "   [OK]   $bn"; else echo "   [WARN] $bn — no matching resource $GEN/${rt}-${rid}.json"; fail=1; fi
  done
else
  echo "   (no directory $TSRC)"
fi
echo "-- checking existing page translations ($TSRC/pagecontent) --"
if [ -d "$TSRC/pagecontent" ]; then
  for f in "$TSRC"/pagecontent/*.md; do
    [ -e "$f" ] || continue
    bn="$(basename "$f")"; src="input/pagecontent/$bn"
    if [ -f "$src" ]; then echo "   [OK]   $bn"; else echo "   [WARN] $bn — no default-language source page $src"; fail=1; fi
  done
else
  echo "   (no directory $TSRC/pagecontent)"
fi
echo
[ "$fail" = 0 ] && echo "Validation: no findings." || echo "Validation: findings present (see [WARN])."
exit 0
