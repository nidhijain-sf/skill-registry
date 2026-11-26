#!/usr/bin/env python3
"""Write catalog/queue.json from the open skill pull requests, for the "In review" tab.

Runs in CI (needs the gh CLI and GH_TOKEN). It never reads pull request files, only pull request
metadata, so nothing from an unreviewed submission is executed. If anything goes wrong the queue
is written empty and the page still builds.
"""
import json
import re
import subprocess
import sys

from registry import PLATFORMS, ROOT

LABEL = {"claude": "Claude Code", "gemini": "Gemini", "slack": "Slackbot"}
FIELDS = "number,title,author,url,createdAt,reviewDecision,files,statusCheckRollup,isDraft"


def checks_state(rollup):
    """Return 'done', 'now' or 'fail' for the automated checks."""
    runs = [r for r in rollup or [] if r.get("name") == "validate"]
    if not runs:
        return "now"
    r = runs[-1]
    if r.get("status") != "COMPLETED":
        return "now"
    return "done" if r.get("conclusion") == "SUCCESS" else "fail"


def entry(pr):
    skill = None
    for f in pr.get("files", []):
        parts = f["path"].split("/")
        if len(parts) > 1 and parts[0] in PLATFORMS:
            skill = (parts[0], parts[1])
            break
    if not skill or not pr["url"].startswith("https://github.com/"):
        return None
    platform, sid = skill
    title = pr["title"].split(": ", 1)[-1].strip() or sid
    checks = checks_state(pr.get("statusCheckRollup"))
    approved = pr.get("reviewDecision") == "APPROVED"
    changes = pr.get("reviewDecision") == "CHANGES_REQUESTED"
    steps = [
        ["Submitted", "done"],
        ["Automated checks", checks],
        ["Reviewer approval", "done" if approved else "now" if checks == "done" else ""],
    ]
    q = {
        "name": title[:80],
        "owner": "@" + re.sub(r"[^A-Za-z0-9-]", "", (pr.get("author") or {}).get("login", "unknown")),
        "sub": f"{LABEL[platform]} · opened {pr['createdAt'][:10]} · #{pr['number']}",
        "steps": steps,
        "url": pr["url"],
    }
    if checks == "fail":
        q["fail"] = "Automated checks failed. The author needs to fix the submission."
    elif changes:
        q["fail"] = "A reviewer requested changes."
    return q


def main():
    queue = []
    try:
        out = subprocess.run(
            ["gh", "pr", "list", "--state", "open", "--limit", "100", "--json", FIELDS],
            check=True, capture_output=True, text=True,
        ).stdout
        queue = [e for e in (entry(p) for p in json.loads(out) if not p.get("isDraft")) if e]
    except Exception as exc:  # the page must still build
        print(f"Could not read pull requests, using an empty queue: {exc}", file=sys.stderr)
    (ROOT / "catalog" / "queue.json").write_text(json.dumps(queue, indent=2) + "\n", encoding="utf-8")
    print(f"Queue has {len(queue)} submission(s).")


if __name__ == "__main__":
    main()
