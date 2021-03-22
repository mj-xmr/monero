#!/bin/bash -e

DIR_BUILD="build/release"
mkdir -p "${DIR_BUILD}" && cd "${DIR_BUILD}"

cmake -S "../.." -DCMAKE_BUILD_TYPE=Release -DUSE_CCACHE=ON -DUSE_UNITY=ON -DBUILD_SHARED_LIBS=ON -DBUILD_TESTS=ON -DBoost_INCLUDE_DIR="/home/enjo/devel/lib/tree/include" 

make

