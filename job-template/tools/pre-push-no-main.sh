#!/bin/sh
# pre-push: refuses any push that updates or deletes main or master on the remote; work goes in through a pull request.
# Linked per clone: CLAUDE.md > "In <NAME>'s name".
# git passes the remote's name and URL as $1 and $2, and one "<local ref> <local sha> <remote ref> <remote sha>" per line.
while read -r _ _ remote_ref _; do
	case "$remote_ref" in
	refs/heads/main | refs/heads/master)
		echo "pre-push: no push to ${remote_ref#refs/heads/} on $2; push a branch and open a pull request." >&2
		exit 1 ;;
	esac
done
exit 0
