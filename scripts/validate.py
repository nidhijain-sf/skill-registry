#!/usr/bin/env python3
"""Automated gate for skill submissions. Exit code 1 means the PR cannot merge.

Errors block the merge. Warnings do not, but "NEEDS SECURITY REVIEW" lines tell
the human reviewer where to look (CODEOWNERS also routes those files to the
security group).
"""
import re
import sys

from registry import ID_RE, PLATFORMS, frontmatter, load_meta, risky_files, skill_dirs, text_files

TIERS = {"certified", "community"}
STATUSES = {"approved", "deprecated", "revoked"}
REQUIRED = [
    "id", "name", "platform", "category", "tier", "status", "version",
    "owner", "owner_contact", "reviewed", "description", "tags",
]
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PLATFORM_FILE = {"claude": ".claude-plugin/plugin.json", "gemini": "gemini-extension.json", "slack": "manifest.json"}

SECRET_PATTERNS = {
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private key": re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "Slack token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    "hardcoded credential": re.compile(
        r"(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"\s]{12,}['\"]", re.I
    ),
}
EMAIL = re.compile(r"[\w.+-]+@(?!example\.(com|org)\b)[\w-]+\.[\w.]+")
SUSPICIOUS = re.compile(r"(curl|wget)\s|base64\s+(-d|--decode)|\beval\(|\bnc\s+-")


def main():
    errors, warnings, seen = [], [], {}
    count = 0
    for platform, d in skill_dirs():
        count += 1
        where = f"{platform}/{d.name}"
        err = lambda m: errors.append(f"{where}: {m}")
        warn = lambda m: warnings.append(f"{where}: {m}")

        if not (d / "skill.json").exists():
            err("missing skill.json")
            continue
        try:
            meta = load_meta(d)
        except ValueError as e:
            err(f"skill.json is not valid JSON ({e})")
            continue

        for key in REQUIRED:
            if not meta.get(key):
                err(f"skill.json is missing '{key}'")
        if meta.get("id") != d.name:
            err(f"id '{meta.get('id')}' must match the folder name '{d.name}'")
        if meta.get("id") and not ID_RE.match(meta["id"]):
            err("id must be lowercase letters, numbers and hyphens")
        if meta.get("platform") != platform:
            err(f"platform '{meta.get('platform')}' must match the parent folder '{platform}'")
        if meta.get("tier") not in TIERS:
            err(f"tier must be one of {sorted(TIERS)}")
        if meta.get("status") not in STATUSES:
            err(f"status must be one of {sorted(STATUSES)}")
        if meta.get("version") and not SEMVER.match(meta["version"]):
            err("version must look like 1.2.3")
        if meta.get("reviewed") and not DATE.match(meta["reviewed"]):
            err("reviewed must be a date like 2026-11-26")
        if not isinstance(meta.get("tags", []), list):
            err("tags must be a list")
        if len(meta.get("description", "")) > 300:
            warn("description is long; keep it under 300 characters so the catalog card reads well")
        if meta.get("id") in seen:
            err(f"id also used by {seen[meta['id']]}")
        seen[meta.get("id")] = where

        if not (d / PLATFORM_FILE[platform]).exists():
            err(f"missing {PLATFORM_FILE[platform]}")
        if platform == "claude":
            skill_md = d / "skills" / d.name / "SKILL.md"
            if not skill_md.exists():
                err(f"missing skills/{d.name}/SKILL.md")
            else:
                fm = frontmatter(skill_md)
                for k in ("name", "description"):
                    if not fm.get(k):
                        err(f"SKILL.md frontmatter is missing '{k}'")
                tools = fm.get("allowed-tools", "")
                if "Bash" in tools and "Bash(" not in tools:
                    warn("NEEDS SECURITY REVIEW: allowed-tools grants unrestricted Bash")

        for p, text in text_files(d):
            rel = p.relative_to(d).as_posix()
            for label, rx in SECRET_PATTERNS.items():
                if rx.search(text):
                    err(f"possible {label} in {rel}")
            if EMAIL.search(text):
                warn(f"{rel} contains an email address; use a placeholder such as user@example.com")
            if SUSPICIOUS.search(text) and p.suffix != ".md":
                warn(f"NEEDS SECURITY REVIEW: suspicious command pattern in {rel}")

        risky = risky_files(d)
        if risky:
            warn("NEEDS SECURITY REVIEW: scripts, hooks or MCP config: " + ", ".join(risky))

    for w in warnings:
        print(f"warning  {w}")
    for e in errors:
        print(f"ERROR    {e}")
    print(f"\nChecked {count} skill(s): {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
