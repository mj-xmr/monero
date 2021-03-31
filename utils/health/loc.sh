#!/bin/bash -e

DIR_OUT="build/loc"
mkdir -p $DIR_OUT

LOC_ALL=$(find ./ -type f \( -iname \*.cpp -o -iname \*.hpp -o -iname \*.c -o -iname \*.h \) -print0 | xargs -0 cat | wc -l)
LOC_HEAD=$(find ./ -type f \( -iname \*.hpp  -o -iname \*.h \) -print0 | xargs -0 cat | wc -l)

echo "$LOC_ALL $LOC_HEAD" > "$DIR_OUT/kpis.txt"
