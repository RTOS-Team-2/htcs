#!/usr/bin/env bash

rm -rf build
mkdir -p build

(cd build && \
cmake .. && \
cmake --build . --target htcs_vehicle)
