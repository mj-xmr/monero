#!/bin/bash -e

DIR_THIS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source "$DIR_THIS/coverage-common.sh"

build "unit_tests"
report "unit-tests" "tests/unit_tests/unit_tests --gtest_filter="logging*""

