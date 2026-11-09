#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
if command -v uv >/dev/null 2>&1; then
 uv build --wheel --out-dir "$tmp/dist" "$root"
 uv venv --python 3.10 "$tmp/env"
 uv pip install --python "$tmp/env/bin/python" "$tmp"/dist/*.whl
else
 python -m pip wheel --no-deps --wheel-dir "$tmp/dist" "$root"
 python -m venv "$tmp/env"
 "$tmp/env/bin/python" -m pip install "$tmp"/dist/*.whl
fi
mkdir "$tmp/outside"
cd "$tmp/outside"
env -u PYTHONPATH "$tmp/env/bin/python" "$root/tools/verify_installed.py" "$root/docs/audits.json" "$root"
env -u PYTHONPATH "$tmp/env/bin/cutlab" "$root/examples/demo.json" --output "$tmp/console.json"
env -u PYTHONPATH "$tmp/env/bin/python" -m cutlab "$root/examples/demo.json" --output "$tmp/module.json"
cmp "$tmp/console.json" "$tmp/module.json"
"$tmp/env/bin/python" -c 'import json,sys; r=json.load(open(sys.argv[1])); assert r["minimum"]=="3" and r["optimal_masks"]==[0,3]; print("Installed console/module CLIs, all 24 base reports and five origins passed")' "$tmp/console.json"

env -u PYTHONPATH "$tmp/env/bin/cutlab" "$root/examples/path.json" --path --output "$tmp/path-console.json"
env -u PYTHONPATH "$tmp/env/bin/python" -m cutlab "$root/examples/path.json" --path --output "$tmp/path-module.json"
cmp "$tmp/path-console.json" "$tmp/path-module.json"
"$tmp/env/bin/python" -c 'import json,sys; r=json.load(open(sys.argv[1])); assert r["knots"]==["-4","1/4","2","4"]; assert [x["optimal_masks"] for x in r["cells"]]==[[7],[0],[1]]; print("Installed affine path CLIs and all 18 path reports passed")' "$tmp/path-console.json"
