#!/bin/bash -e

echo "Info"
find ./ -type f \( -iname \*.cpp -o -iname \*.hpp -o -iname \*.c -o -iname \*.h \) | wc -l

mkdir -p build && cd build

date +"%T.%N" > "files.txt"
date +"%T.%N" > "files2.txt"

