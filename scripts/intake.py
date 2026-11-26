#!/usr/bin/env python3
"""Turn a "Submit a skill" issue into skill files plus a pull request description.

Called by .github/workflows/intake.yml. Reads the issue from the GitHub event file, validates every
field strictly, and writes the skill folder into the working tree. The issue text is untrusted, so
it is only ever parsed here, never put into a shell command. Everything that reaches a file name or
branch name has already matched a strict pattern.

Exit code 0: files written, results in --out (title.txt, body.md, branch.txt).
Exit code 2: the form has problems, errors.md in --out lists them. Nothing is written to the repo.
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path

from registry import ID_RE, PLATFORMS, ROOT
from validate import SECRET_PATTERNS

PLATFORM_BY_LABEL = {"Claude Code": "claude", "Gemini": "gemini", "Slackbot": "slack"}
PLATFORM_LABEL = {v: k for k, v in PLATFORM_BY_LABEL.items()}

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .,&'()/+-]{1,59}$")
CATEGORY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 &/-]{1,29}$")
TAG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,23}$")
TEXT_RE = re.compile(r"^[A-Za-z0-9#@][A-Za-z0-9 .,&'()#@/_:-]{1,79}$")
TOOLS_RE = re.compile(r"^[A-Za-z0-9 ,()*:_.-]{0,120}$")
SCOPE_RE = re.compile(r"^[a-z][a-z_.:-]{1,63}$")


def parse_sections(body):
    """Split the issue-form body into {label: value}."""
    parts = re.split(r"^### (.+?)\s*$", body.replace("\r\n", "\n"), flags=re.M)
    sections = {}
    for i in range(1, len(parts) - 1, 2):
        value = parts[i + 1].strip()
        sections[parts[i].strip()] = "" if value == "_No response_" else value
    return sections


def one_line(text):
    return " ".join(text.split())


def collect(sections):
    """Return (fields, errors)."""
    errors = []

    def need(label, pattern=None, what=None):
        value = one_line(sections.get(label, ""))
        if not value:
            errors.append(f"**{label}** is required.")
            return ""
        if pattern and not pattern.match(value):
            errors.append(f"**{label}** {what}")
            return ""
        return value

    f = {}
    platform_label = sections.get("Platform", "").strip()
    f["platform"] = PLATFORM_BY_LABEL.get(platform_label, "")
    if not f["platform"]:
        errors.append("**Platform** must be Claude Code, Gemini or Slackbot.")

    f["id"] = need("Skill id", ID_RE, "must be lowercase letters, numbers and hyphens, such as `release-notes-writer`.")
    if f["id"] and len(f["id"]) > 50:
        errors.append("**Skill id** must be 50 characters or fewer.")
    if f["id"]:
        for p in PLATFORMS:
            if (ROOT / p / f["id"]).exists():
                errors.append(f"**Skill id** `{f['id']}` is already used by a skill in `{p}/`. To change an existing skill, open a pull request.")
    f["name"] = need("Name", NAME_RE, "must be 2 to 60 characters: letters, numbers, spaces and basic punctuation.")
    f["category"] = need("Category", CATEGORY_RE, "must be 2 to 30 characters: letters, numbers, spaces, `&`, `/` and `-`.")

    description = need("Description")
    if description and not 20 <= len(description) <= 300:
        errors.append("**Description** must be between 20 and 300 characters.")
    f["description"] = description

    tags = [t.strip().lower() for t in sections.get("Tags (comma separated)", "").split(",") if t.strip()]
    if not tags or len(tags) > 8 or not all(TAG_RE.match(t) for t in tags):
        errors.append("**Tags** needs 1 to 8 comma-separated words made of letters, numbers and hyphens.")
    f["tags"] = tags

    f["owner"] = need("Owner team", TEXT_RE, "must be 2 to 80 characters with no unusual symbols.")
    f["contact"] = need("Owner contact", TEXT_RE, "must be 2 to 80 characters with no unusual symbols.")

    scripts = sections.get("Scripts, hooks or MCP servers", "")
    if not scripts.startswith("None"):
        errors.append("Skills that need scripts, hooks or MCP servers cannot be submitted through this form. Open a pull request instead, so the security group reviews the code. See CONTRIBUTING.md.")

    tools = one_line(sections.get("Tools or file access", ""))
    scopes_raw = sections.get("Slack scopes (Slackbot only)", "")
    f["scopes"] = [s.strip() for s in scopes_raw.split(",") if s.strip()]
    if f["platform"] == "slack":
        if not f["scopes"] or not all(SCOPE_RE.match(s) for s in f["scopes"]):
            errors.append("**Slack scopes** is required for Slackbot: comma-separated scopes such as `chat:write, commands`.")
        f["tools"] = "Scopes: " + ", ".join(f["scopes"])
    else:
        if not TOOLS_RE.match(tools):
            errors.append("**Tools or file access** may only contain letters, numbers, spaces and `, ( ) * : _ . -`.")
        f["tools"] = tools or "Read"

    instructions = sections.get("Instructions", "").strip()
    if not 50 <= len(instructions) <= 8000:
        errors.append("**Instructions** must be between 50 and 8000 characters.")
    f["instructions"] = instructions

    if "- [x]" not in sections.get("Confirmation", "").lower():
        errors.append("Please tick the confirmation that there are no secrets, customer data or personal data.")

    for label, text in (("Instructions", instructions), ("Description", description)):
        for kind, rx in SECRET_PATTERNS.items():
            if rx.search(text):
                errors.append(f"**{label}** appears to contain a {kind}. Remove it and submit again.")
    return f, errors


def write_files(f):
    today = datetime.date.today().isoformat()
    base = ROOT / f["platform"] / f["id"]
    base.mkdir(parents=True)

    def put(rel, text):
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def js(obj):
        return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"

    put("skill.json", js({
        "id": f["id"], "name": f["name"], "platform": f["platform"], "category": f["category"],
        "tier": "community", "status": "approved", "version": "1.0.0",
        "owner": f["owner"], "owner_contact": f["contact"], "reviewed": today,
        "description": f["description"], "tags": f["tags"], "tools": f["tools"],
    }))
    title_line = f"# {f['name']}\n\n"
    if f["platform"] == "claude":
        put(".claude-plugin/plugin.json", js({"name": f["id"], "version": "1.0.0", "description": f["description"]}))
        put(f"skills/{f['id']}/SKILL.md",
            "---\n"
            f"name: {f['id']}\n"
            f"description: {json.dumps(f['description'], ensure_ascii=False)}\n"
            f"allowed-tools: {f['tools']}\n"
            "---\n\n" + title_line + f["instructions"] + "\n")
    elif f["platform"] == "gemini":
        put("gemini-extension.json", js({"name": f["id"], "version": "1.0.0", "contextFileName": "GEMINI.md"}))
        put("GEMINI.md", title_line + f["instructions"] + "\n")
    else:
        put("manifest.json", js({
            "display_information": {"name": f["name"]},
            "features": {"bot_user": {"display_name": f["id"], "always_online": False}},
            "oauth_config": {"scopes": {"bot": f["scopes"]}},
        }))
        put("README.md", title_line + f["instructions"] + "\n\n## Slack scopes\n\n" + "\n".join(f"- `{s}`" for s in f["scopes"]) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--event", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    event = json.loads(Path(args.event).read_text(encoding="utf-8"))
    issue = event["issue"]
    number = int(issue["number"])
    login = re.sub(r"[^A-Za-z0-9-]", "", issue["user"]["login"])
    repo_url = event.get("repository", {}).get("html_url", "")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    sections = parse_sections(issue.get("body") or "")
    if "Skill id" not in sections:
        errors, f = ["This issue was not created from the **Submit a skill** form."], None
    else:
        f, errors = collect(sections)

    if errors:
        (out / "errors.md").write_text(
            "The skill could not be turned into a pull request yet:\n\n"
            + "\n".join(f"- {e}" for e in errors)
            + "\n\nEdit nothing here. Open a new submission from the catalog page with these fixed.\n",
            encoding="utf-8",
        )
        return 2

    write_files(f)
    label = PLATFORM_LABEL[f["platform"]]
    (out / "title.txt").write_text(f"Add {label} skill: {f['name']}", encoding="utf-8")
    (out / "branch.txt").write_text(f"skill/{f['id']}-{number}", encoding="utf-8")
    (out / "body.md").write_text(
        f"Submitted through the catalog form by @{login}.\n\n"
        f"| | |\n|---|---|\n"
        f"| Platform | {label} |\n| Skill | `{f['id']}` |\n| Category | {f['category']} |\n"
        f"| Owner | {f['owner']} |\n| Access | {f['tools']} |\n| Scripts | None |\n\n"
        f"The skill files were generated from the form. Review them against "
        f"[docs/REVIEW_CHECKLIST.md]({repo_url}/blob/main/docs/REVIEW_CHECKLIST.md). "
        f"Merging approves the skill and lists it on the catalog.\n\n"
        f"Closes #{number}\n",
        encoding="utf-8",
    )
    print(f"Generated {f['platform']}/{f['id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
