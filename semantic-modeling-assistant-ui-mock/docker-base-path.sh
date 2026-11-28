#!/bin/sh
# Serves the UI under the public URL path given by BASE_PATH (for example
# /slovniky-ai). The build uses a placeholder base path; every container start
# patches a fresh copy of the untouched build, so BASE_PATH may change between
# restarts.
set -eu

PLACEHOLDER=/__SLOVNIKY_AI_BASE_PATH__
TEMPLATE_DIR=/usr/share/nginx/html-template
HTML_DIR=/usr/share/nginx/html

base_path=$(printf '%s' "${BASE_PATH:-}" | sed -e 's#/*$##' -e 's#^/*#/#' -e 's#^/$##')

case "$base_path" in
  *[!A-Za-z0-9._~/-]*)
    echo "BASE_PATH '$BASE_PATH' may only contain letters, digits and . _ ~ / -" >&2
    exit 1
    ;;
esac

rm -rf "$HTML_DIR"
cp -R "$TEMPLATE_DIR" "$HTML_DIR"
grep -rlF "$PLACEHOLDER" "$HTML_DIR" | while read -r file; do
  sed -i "s#$PLACEHOLDER#$base_path#g" "$file"
done

echo "Serving the UI under '${base_path:-/}'"
