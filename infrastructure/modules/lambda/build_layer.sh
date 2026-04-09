#!/bin/bash
set -e
SOURCE_DIR=$1
OUTPUT_ZIP=$2

mkdir -p build/python
cp -r "$SOURCE_DIR" build/python/
cd build
zip -qr layer_shared.zip python/
cd ..
mv build/layer_shared.zip "$OUTPUT_ZIP"
rm -rf build
