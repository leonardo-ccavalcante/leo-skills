#!/usr/bin/env python3
"""
bake_config.py - write a completed workspace config into a fresh .skill package.

The installed skill folder is usually read-only, so Setup cannot save the
config in place. This script copies the skill to a temporary folder, swaps in
the completed references/workspace-config.md, checks the package and zips it
as <skill-name>.skill, ready to install and share with the team.

Standard library only.

Usage:
    python3 bake_config.py --config /path/to/completed-workspace-config.md [--out DIR] [--force]
"""

import argparse
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

EXCLUDE_DIRS = {"__pycache__", "node_modules", ".git", "evals"}
EXCLUDE_FILES = {".DS_Store"}
EXCLUDE_SUFFIXES = {".pyc"}


def read_skill_name(skill_md):
    text = skill_md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        raise SystemExit("SKILL.md has no YAML frontmatter.")
    name = re.search(r"^name:\s*(.+?)\s*$", m.group(1), re.MULTILINE)
    if not name:
        raise SystemExit("SKILL.md frontmatter has no name.")
    value = name.group(1).strip().strip("\"'")
    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", value):
        raise SystemExit("Skill name %r is not kebab-case." % value)
    return value


def default_out_dir():
    outputs = Path("/mnt/user-data/outputs")
    if outputs.is_dir():
        return outputs
    return Path.cwd()


def should_skip(rel):
    if any(part in EXCLUDE_DIRS for part in rel.parts[:-1]):
        return True
    if rel.name in EXCLUDE_FILES:
        return True
    return rel.suffix in EXCLUDE_SUFFIXES


def main(argv=None):
    p = argparse.ArgumentParser(description="Bake a completed workspace config into a .skill package.")
    p.add_argument("--config", required=True, help="Path to the completed workspace-config.md")
    p.add_argument("--out", help="Output directory (default: /mnt/user-data/outputs if present, else current directory)")
    p.add_argument("--force", action="store_true", help="Bake even if the config is not marked CONFIGURED")
    args = p.parse_args(argv)

    skill_root = Path(__file__).resolve().parent.parent
    skill_md = skill_root / "SKILL.md"
    if not skill_md.exists():
        raise SystemExit("SKILL.md not found next to scripts/ (looked in %s)." % skill_root)
    name = read_skill_name(skill_md)

    config_path = Path(args.config).resolve()
    if not config_path.exists():
        raise SystemExit("Config file not found: %s" % config_path)
    config_text = config_path.read_text(encoding="utf-8")
    status = re.search(r"^status:\s*(\S+)", config_text, re.MULTILINE)
    status_value = status.group(1) if status else "(missing)"
    if status_value != "CONFIGURED" and not args.force:
        raise SystemExit(
            "Config status is %s. Set 'status: CONFIGURED' once Setup is complete, "
            "or pass --force to bake anyway." % status_value
        )
    if "# Workspace config" not in config_text:
        raise SystemExit("This does not look like a workspace config (missing '# Workspace config' heading).")

    out_dir = Path(args.out).resolve() if args.out else default_out_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / (name + ".skill")

    with tempfile.TemporaryDirectory() as tmp:
        staged = Path(tmp) / name
        staged.mkdir()
        copied = 0
        for src in sorted(skill_root.rglob("*")):
            if not src.is_file():
                continue
            rel = src.relative_to(skill_root)
            if should_skip(rel):
                continue
            dest = staged / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
            copied += 1

        config_dest = staged / "references" / "workspace-config.md"
        config_dest.parent.mkdir(parents=True, exist_ok=True)
        config_dest.write_text(config_text, encoding="utf-8")

        skill_mds = [x for x in staged.rglob("SKILL.md")]
        if len(skill_mds) != 1:
            raise SystemExit("Package must contain exactly one SKILL.md, found %d." % len(skill_mds))

        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(staged.rglob("*")):
                if f.is_file():
                    z.write(f, Path(name) / f.relative_to(staged))

    with zipfile.ZipFile(target) as z:
        names = z.namelist()
        baked = z.read("%s/references/workspace-config.md" % name).decode("utf-8")
    ok = baked == config_text and ("%s/SKILL.md" % name) in names

    print("Skill: %s" % name)
    print("Files packaged: %d" % len(names))
    print("Config status: %s" % status_value)
    print("Config baked correctly: %s" % ("yes" if ok else "NO"))
    print("Package: %s" % target)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
