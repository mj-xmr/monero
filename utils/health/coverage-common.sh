#!/bin/bash -e

DIR_CWD=`pwd`
DIR_BUILD_TMP="/tmp/monero/coverage"
DIR_BUILD="build/coverage"
#rm "${DIR_BUILD}"/* -fr || true
#rm "${DIR_BUILD_TMP}"/* -fr || true
mkdir -p "${DIR_BUILD}" && cd "${DIR_BUILD}"

PROG_LCOV="lcov"
PROG_GENHTML="genhtml"
GEN="CodeBlocks - Unix Makefiles"

find_prog() {
	PROG="$1"
	if $(hash $PROG); then
		echo "Found: $PROG"
	else
		echo "Couldn't find: $PROG"
		exit 1
	fi
}

build() {
	MAKE_OPTIONS="$1"
	cmake -S "../.." -B "$DIR_BUILD_TMP" -DCOVERAGE=ON -DCMAKE_BUILD_TYPE=Debug -DUSE_CCACHE=ON -DUSE_UNITY=ON -DBUILD_SHARED_LIBS=ON -DBUILD_TESTS=ON -G "${GEN}" -DBoost_INCLUDE_DIR="/home/enjo/devel/lib/tree/include"
	cd "$DIR_BUILD_TMP"
	make $MAKE_OPTIONS
}

zero() {
	rm -f "$FBASE" "$FTEST" "$FFLTR" "$FTOTAL" || true

	$PROG_LCOV --zerocounters --directory "$DIR"
	$PROG_LCOV --capture --initial --directory "$DIR" --output-file "$FBASE"
}

generate() {
	$PROG_LCOV --capture --directory "$DIR" --output-file "$FTEST"
	$PROG_LCOV --add-tracefile "$FBASE" --add-tracefile "$FTEST" --output-file "$FTOTAL"
	rm -rf "$DIR_REPORT"
	mkdir -p "$DIR_REPORT"
	$PROG_LCOV --remove "$FTOTAL" '/usr/include/*' '/usr/lib/*' '*/build/*' '*tests/*' '/home/enjo/devel/lib/tree/*' -o "$FFLTR"
	$PROG_GENHTML --ignore-errors source "$FFLTR" --legend --title $PROJ --output-directory="$DIR_REPORT" 2>&1 | tee "$LOG"
	KPI_LINES=$(grep "  lines" 	"$LOG" | awk '{print $2}' | sed 's/.$//')
	KPI_FUNCS=$(grep "  functions" 	"$LOG" | awk '{print $2}' | sed 's/.$//')
	if [ -z "$var" ]; then
		echo "$KPI_LINES $KPI_FUNCS" > "kpis.txt"
	else
		echo "-3" > "kpis.txt"
	fi
	echo "Report written to: $DIR_REPORT/index.html"
	
	if [ ! -L "$PROJ" ]; then
		ln -s "$DIR_REPORT"
	fi
	echo "Archiving the report..."
	tar -cJhf "$ARCHIVE" "$PROJ"

	echo "Archive stored to: `pwd`/$ARCHIVE"
	cp -v $ARCHIVE "$DIR_CWD/$DIR_BUILD"
	cp -v "kpis.txt" "$DIR_CWD/$DIR_BUILD"
}

report() {
	PROJ="$1-lcov"
	COMMAND=$2
	
	DIR="."
	DIR_OUT=/tmp/lcov
	PATH_OUT_BASE="$DIR_OUT/$PROJ"
	DIR_REPORT="$PATH_OUT_BASE"
	FBASE="$PATH_OUT_BASE"_base.info
	FTEST="$PATH_OUT_BASE"_test.info
	FFLTR="$PATH_OUT_BASE"_filtered.info
	FTOTAL="$PATH_OUT_BASE"_total.info
	LOG="$PATH_OUT_BASE"-log.txt
	ARCHIVE="$PROJ.tar.xz"
	
	mkdir -p "$DIR_OUT"
	
	zero
	$COMMAND || true # Failing tests aren't a reason to abort the report generation
	generate
}

# Make sure we've got everything
find_prog $PROG_LCOV
find_prog $PROG_GENHTML


