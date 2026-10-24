#!/bin/sh
# The agents' Chrome: its own profile in the repo, CDP on 127.0.0.1:9222, kept alive by launchd. Rules: tools.md > "Browser".
# macOS sends Dock clicks and links to the oldest running Chrome, so the owner's own Chrome must start first.
# When the owner's restarts (a Chrome update, a quit), this one becomes the oldest: exit and let launchd start it again.
REPO=$(cd "$(dirname "$0")/../.." && pwd)
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
owners_pid() { pgrep -f 'MacOS/Google Chrome( --|$)' | while read -r p; do
  ps -o command= -p "$p" | grep -q playwright-profile || echo "$p"; done | head -1; }

[ -n "$(owners_pid)" ] || { open -g -a "Google Chrome"; sleep 5; }
owners=$(owners_pid)

# A shared Chrome started outside this script: watch it instead of launching again, since a second launch
# only hands about:blank to it as a new tab and exits, and launchd then repeats that every run.
shared=$(pgrep -f 'MacOS/Google Chrome --.*playwright-profile' | head -1)
[ -n "$shared" ] || { "$CHROME" \
  --user-data-dir="$REPO/.playwright-profile" \
  --remote-debugging-port=9222 \
  --use-mock-keychain \
  --password-store=basic \
  --disable-background-timer-throttling \
  --disable-backgrounding-occluded-windows \
  --disable-renderer-backgrounding \
  --no-first-run \
  --no-default-browser-check \
  about:blank &
shared=$!; }

while kill -0 "$shared" 2>/dev/null; do
  sleep 30
  now=$(owners_pid)
  [ -z "$now" ] || [ "$now" = "$owners" ] || break
done
kill "$shared" 2>/dev/null
wait "$shared"
