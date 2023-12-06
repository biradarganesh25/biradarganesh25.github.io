#!/bin/sh
style=${1:-pygments}
tmp=
trap 'rm -f "$tmp"' EXIT
tmp=$(mktemp)
echo '$highlighting-css$' > "$tmp"
echo '`test`{.py}' | pandoc --highlight-style=$style --template=$tmp --metadata title="python"