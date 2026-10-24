#!/bin/bash
# Snapshot a fail for bench/fails.json: tags the repo at the last commit before the bad turn
# and saves the session up to (not including) that turn.
# usage: bench-snapshot.sh <fail-id> <repo-path> <session.jsonl> <uuid of the user message that started the bad turn>
set -euo pipefail
id=$1 repo=$2 session=$3 uuid=$4
bench=$(cd "$(dirname "$0")/../bench" && pwd)

ts=$(grep -m1 "\"uuid\":\"$uuid\"" "$session" | python3 -c 'import json,sys; print(json.load(sys.stdin)["timestamp"])')
ref=$(git -C "$repo" rev-list -1 --before="$ts" HEAD)
git -C "$repo" tag "fail/$id" "$ref"
git -C "$repo" push -q origin "fail/$id"

mkdir -p "$bench/../tmp/bench-sessions"
awk -v u="\"uuid\":\"$uuid\"" 'index($0, u) {exit} {print}' "$session" | gzip > "$bench/../tmp/bench-sessions/$id.jsonl.gz"
echo "$ref"
