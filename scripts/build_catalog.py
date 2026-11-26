#!/usr/bin/env python3
"""Build everything that is generated from the skill folders.

Outputs:
  catalog/catalog.json            every listed skill, all platforms (committed)
  .claude-plugin/marketplace.json Claude Code marketplace, approved Claude skills only (committed)
  site/index.html                 browsable catalog page (built in CI, not committed)

Settings come from environment variables so the same script works anywhere:
  REGISTRY_REPO  owner/name used in install commands   (default YOUR-ORG/skill-registry)
  REGISTRY_URL   link used by the "Submit a skill" button (default #)
  MARKETPLACE_NAME  name users type after @ in /plugin install (default team-skills)
"""
import json
import os

from registry import ROOT, risky_files, load_meta, skill_dirs

REPO = os.environ.get("REGISTRY_REPO", "YOUR-ORG/skill-registry")
URL = os.environ.get("REGISTRY_URL", "#")
MARKETPLACE = os.environ.get("MARKETPLACE_NAME", "team-skills")


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    skills = []
    for platform, d in skill_dirs():
        meta = load_meta(d)
        if meta.get("status") == "revoked":
            continue
        risky = risky_files(d)
        meta["scripts"] = ", ".join(risky) if risky else "None"
        meta["path"] = f"{platform}/{d.name}"
        meta.setdefault("tools", "Not specified")
        skills.append(meta)
    skills.sort(key=lambda s: (s["platform"], s["id"]))
    dump(ROOT / "catalog" / "catalog.json", skills)

    plugins = [
        {
            "name": s["id"],
            "source": f"./{s['path']}",
            "description": s["description"],
            "version": s["version"],
            "category": s["category"],
        }
        for s in skills
        if s["platform"] == "claude" and s["status"] == "approved"
    ]
    dump(
        ROOT / ".claude-plugin" / "marketplace.json",
        {"name": MARKETPLACE, "owner": {"name": "Skill Registry maintainers"}, "plugins": plugins},
    )

    template = ROOT / "site" / "template.html"
    if template.exists():
        queue_file = ROOT / "catalog" / "queue.json"
        queue = json.loads(queue_file.read_text(encoding="utf-8")) if queue_file.exists() else []
        html = template.read_text(encoding="utf-8")
        safe = lambda obj: json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")
        html = (
            html.replace("/*__SKILLS__*/[]", safe(skills))
            .replace("/*__QUEUE__*/[]", safe(queue))
            .replace("__REPO_URL__", URL)
            .replace("__REPO__", REPO)
            .replace("__MARKETPLACE__", MARKETPLACE)
        )
        (ROOT / "site" / "index.html").write_text(html, encoding="utf-8")

    print(f"Built catalog with {len(skills)} skill(s); {len(plugins)} in the Claude Code marketplace.")


if __name__ == "__main__":
    main()
