#!/usr/bin/env bash
set -euo pipefail

doxygen docs/doxygen/Doxyfile
echo "Generated docs at docs/doxygen/build/html/index.html"
