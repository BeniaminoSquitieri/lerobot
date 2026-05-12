#!/usr/bin/env bash
set -euo pipefail

if ! command -v doxygen >/dev/null 2>&1; then
  echo "Error: doxygen is not installed." >&2
  echo >&2
  echo "Install it with one of:" >&2
  echo "  sudo apt install doxygen graphviz" >&2
  echo "  conda install -c conda-forge doxygen graphviz" >&2
  exit 2
fi

doxygen docs/doxygen/Doxyfile

echo "Generated docs at docs/doxygen/build/html/index.html"
