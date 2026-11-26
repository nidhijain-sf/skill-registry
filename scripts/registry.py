"""Shared helpers for loading skills from the registry. Standard library only."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLATFORMS = ("claude", "gemini", "slack")
SCRIPT_EXT = {".sh", ".bash", ".zsh", ".py", ".js", ".ts", ".rb", ".ps1"}
RISKY_NAMES = {".mcp.json"}
RISKY_DIRS = {"scripts", "hooks"}


def skill_dirs():
    """Yield (platform, directory) for every skill folder in the registry."""
    for platform in PLATFORMS:
        base = ROOT / platform
        if not base.is_dir():
            continue
        for d in sorted(base.iterdir()):
            if d.is_dir() and not d.name.startswith((".", "_")):
                yield platform, d


def load_meta(d):
    return json.loads((d / "skill.json").read_text(encoding="utf-8"))


def frontmatter(path):
    """Return the simple key: value pairs from a SKILL.md frontmatter block."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    out = {}
    for line in text[3:end].splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def risky_files(d):
    """Files that need a security reviewer: scripts, hooks, MCP server configs."""
    found = []
    for p in sorted(d.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(d)
        if (
            p.suffix in SCRIPT_EXT
            or p.name in RISKY_NAMES
            or any(part in RISKY_DIRS for part in rel.parts[:-1])
        ):
            found.append(rel.as_posix())
    return found


def text_files(d):
    for p in sorted(d.rglob("*")):
        if p.is_file():
            try:
                yield p, p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue


ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
