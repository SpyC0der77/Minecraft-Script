#!/bin/sh
set -e

if command -v mcs >/dev/null 2>&1; then
  exec mcs "$@"
fi

if [ -n "$PYTHON" ] && [ -x "$PYTHON" ]; then
  exec "$PYTHON" -m minecraft_script "$@"
fi

for version in 313 312 311 310; do
  dotted_version="${version%??}.${version#?}"
  for candidate in \
    "/c/Python${version}/python.exe" \
    "$LOCALAPPDATA/Programs/Python/Python${version}/python.exe" \
    "$PROGRAMFILES/Python${version}/python.exe" \
    "/usr/local/bin/python${dotted_version}" \
    "/usr/bin/python${dotted_version}" \
    "/usr/local/bin/python3.${version#?}" \
    "/usr/bin/python3.${version#?}"; do
    if [ -x "$candidate" ]; then
      exec "$candidate" -m minecraft_script "$@"
    fi
  done
done

if command -v python3 >/dev/null 2>&1; then
  exec python3 -m minecraft_script "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python -m minecraft_script "$@"
fi

if command -v py >/dev/null 2>&1; then
  exec py -3 -m minecraft_script "$@"
fi

echo "MCS compiler not found. Install minecraft-script (pip install -e .) or set compilerPath in config/mcs-packs.json." >&2
exit 1
