#!/usr/bin/env python3
"""Pinned instruction-only Agent Skill registry and installer for Open ASS.

Installs reviewed *text* from GitHub commit SHAs without executing scripts.
Git tree blob hashes are verified; existing or modified skill folders are not overwritten.
"""
import argparse
import hashlib
import json
import re
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
CATALOG = "integrations/skills.lock.json"
ALLOWED_EXT = {".md", ".txt", ".json", ".yaml", ".yml", ".toml"}
MAX_FILES = 180
MAX_FILE = 512_000
MAX_SKILL = 4_000_000
MAX_TREE = 8_000_000
SHA = re.compile(r"^[0-9a-f]{40}$")
IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{1,70}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class SkillError(ValueError):
    pass


def check_path(name):
    if not isinstance(name, str) or not name or "\x00" in name or "\\" in name:
        raise SkillError("unsafe path")
    parts = name.split("/")
    if any(part in ("", ".", "..") for part in parts) or name.startswith("/"):
        raise SkillError("path escape: " + name)
    return PurePosixPath(name)


def load(root=ROOT):
    data = json.loads((root / CATALOG).read_text(encoding="utf-8"))
    validate(data)
    return data


def validate(data):
    if not isinstance(data, dict) or data.get("version") != 1:
        raise SkillError("unknown skill catalog version")
    entries, profiles = data.get("skills"), data.get("profiles")
    if not isinstance(entries, list) or not entries:
        raise SkillError("empty skill catalog")
    if not isinstance(profiles, dict) or not profiles:
        raise SkillError("missing skill profiles")
    ids = set()
    for record in entries:
        if not isinstance(record, dict) or not {"id", "source", "revision", "directory", "license", "description"} <= record.keys():
            raise SkillError("invalid skill record")
        sid = record["id"]
        if not isinstance(sid, str) or not IDENTIFIER.fullmatch(sid) or sid in ids:
            raise SkillError("duplicate or invalid skill ID")
        ids.add(sid)
        if not REPO.fullmatch(record["source"]) or not SHA.fullmatch(record["revision"]):
            raise SkillError("skill source must have a repository and full commit SHA: " + sid)
        if record["directory"] != ".":
            check_path(record["directory"])
        if not isinstance(record["description"], str) or not record["description"].strip():
            raise SkillError("missing skill description")
        if not isinstance(record["license"], str) or not record["license"].strip():
            raise SkillError("missing license information")
    for name, included in profiles.items():
        if not IDENTIFIER.fullmatch(name) or not isinstance(included, list) or not included:
            raise SkillError("invalid profile")
        if len(included) != len(set(included)) or any(item not in ids for item in included):
            raise SkillError("unknown or duplicate skill in profile: " + name)
    return True


def selected(catalog, profiles=(), skills=()):
    names = set(skills)
    for profile in profiles:
        if profile not in catalog["profiles"]:
            raise SkillError("unknown profile: " + profile)
        names.update(catalog["profiles"][profile])
    if not names:
        raise SkillError("select at least one profile or skill")
    records = {rec["id"]: rec for rec in catalog["skills"]}
    for name in names:
        if name not in records:
            raise SkillError("unknown skill: " + name)
    return [records[name] for name in sorted(names)]


def fetch_bytes(url, limit):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ("api.github.com", "raw.githubusercontent.com"):
        raise SkillError("unapproved download host")
    req = urllib.request.Request(url, headers={"User-Agent": "open-ass-pinned-skills/1", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=25) as res:
        final = urllib.parse.urlparse(res.geturl())
        if final.scheme != "https" or final.hostname not in ("api.github.com", "raw.githubusercontent.com"):
            raise SkillError("unsafe download redirect")
        data = res.read(limit + 1)
    if len(data) > limit:
        raise SkillError("download exceeds size limit")
    return data


def blob_sha(content):
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()


def github_url(record):
    return "https://api.github.com/repos/" + record["source"] + "/git/trees/" + record["revision"] + "?recursive=1"


def raw_url(record, path):
    pieces = [urllib.parse.quote(x, safe="") for x in path.split("/")]
    return "https://raw.githubusercontent.com/" + record["source"] + "/" + record["revision"] + "/" + "/".join(pieces)


def remote_files(record, fetch, cache):
    source_key = (record["source"], record["revision"])
    if source_key not in cache:
        tree = json.loads(fetch(github_url(record), MAX_TREE))
        if tree.get("truncated") or not isinstance(tree.get("tree"), list):
            raise SkillError("missing or truncated upstream tree: " + record["source"])
        cache[source_key] = tree["tree"]
    prefix = "" if record["directory"] == "." else record["directory"] + "/"
    found = []
    for entry in cache[source_key]:
        path = entry.get("path", "")
        if not isinstance(path, str) or not path.startswith(prefix):
            continue
        relative = path[len(prefix):]
        if not relative or "/" in relative and record["directory"] == ".":
            continue  # A root-level SKILL.md is intentionally not expanded into the entire repo.
        check_path(relative)
        if entry.get("type") != "blob" or Path(relative).suffix.lower() not in ALLOWED_EXT:
            continue
        if entry.get("mode") != "100644":
            continue  # Do not download symlinks or executable files.
        if not SHA.fullmatch(str(entry.get("sha", ""))):
            raise SkillError("upstream blob lacks a Git SHA")
        size = entry.get("size")
        if not isinstance(size, int) or size < 0 or size > MAX_FILE:
            raise SkillError("upstream text file exceeds size limit: " + path)
        found.append((path, relative, entry["sha"], size))
    if not any(rel == "SKILL.md" for _, rel, _, _ in found):
        raise SkillError("skill entrypoint missing: " + record["id"])
    if len(found) > MAX_FILES or sum(item[3] for item in found) > MAX_SKILL:
        raise SkillError("skill bundle exceeds size limits: " + record["id"])
    return sorted(found)


def inspect_skill(content, skill_id):
    try:
        doc = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SkillError("SKILL.md is not UTF-8") from exc
    if not doc.startswith("---\n"):
        raise SkillError("missing skill metadata: " + skill_id)
    header = doc[4:].split("\n---", 1)[0]
    names = re.findall(r"^name:\s*['\"]?([a-z][a-z0-9-]*)['\"]?\s*$", header, re.M)
    if names != [skill_id]:
        raise SkillError("upstream skill name mismatches catalog: " + skill_id)


def audit(root=ROOT):
    base = root / ".agents" / "skills"
    results = []
    if not base.exists():
        return results
    for folder in sorted(base.iterdir()):
        if not folder.is_dir():
            continue
        stamp = folder / ".open-ass-source.json"
        if not stamp.exists():
            continue  # Local first-party or unmanaged skills are not overwritten.
        record = json.loads(stamp.read_text(encoding="utf-8"))
        if record.get("id") != folder.name or not SHA.fullmatch(str(record.get("revision", ""))):
            raise SkillError("invalid installed skill provenance: " + folder.name)
        files = record.get("files")
        if not isinstance(files, dict) or "SKILL.md" not in files:
            raise SkillError("invalid installed skill file registry: " + folder.name)
        for path, digest in files.items():
            check_path(path)
            target = (folder / path).resolve()
            if not target.is_relative_to(folder.resolve()) or not target.is_file():
                raise SkillError("installed file missing or unsafe: " + folder.name + "/" + path)
            if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                raise SkillError("installed skill modified: " + folder.name + "/" + path)
        results.append(folder.name)
    return results


def install(records, root=ROOT, fetch=fetch_bytes):
    dest = root / ".agents" / "skills"
    dest.mkdir(parents=True, exist_ok=True)
    installed = set(audit(root))
    for rec in records:
        if (dest / rec["id"]).exists() and rec["id"] not in installed:
            raise SkillError("existing unmanaged skill path: " + rec["id"])
        if rec["id"] in installed:
            raise SkillError("skill already installed; remove manually to change pinned version: " + rec["id"])
    cache = {}
    with tempfile.TemporaryDirectory(prefix=".open-ass-stage-", dir=dest) as temp:
        staging = Path(temp)
        for rec in records:
            rows = remote_files(rec, fetch, cache)
            folder = staging / rec["id"]
            folder.mkdir()
            hashes = {}
            for source, relative, expected, size in rows:
                payload = fetch(raw_url(rec, source), MAX_FILE)
                if len(payload) != size or blob_sha(payload) != expected:
                    raise SkillError("download failed Git blob verification: " + source)
                if relative == "SKILL.md":
                    inspect_skill(payload, rec["id"])
                path = folder / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
                hashes[relative] = hashlib.sha256(payload).hexdigest()
            stamp = {"id": rec["id"], "source": rec["source"], "revision": rec["revision"],
                     "directory": rec["directory"], "license": rec["license"], "files": hashes,
                     "mode": "instruction-only; executable upstream files excluded"}
            (folder / ".open-ass-source.json").write_text(json.dumps(stamp, indent=2) + "\n")
        for rec in records:
            (staging / rec["id"]).rename(dest / rec["id"])
    return [rec["id"] for rec in records]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("check")
    sub.add_parser("audit")
    for op in ("plan", "install"):
        p = sub.add_parser(op)
        p.add_argument("--profile", action="append", default=[])
        p.add_argument("--skill", action="append", default=[])
    args = parser.parse_args()
    try:
        catalog = load()
        if args.cmd == "list":
            for profile, names in catalog["profiles"].items():
                print(profile + ": " + ", ".join(names))
        elif args.cmd == "check":
            names = audit()
            print("Catalog valid; " + str(len(names)) + " managed installed skill(s) verified")
        elif args.cmd == "audit":
            print("Verified installed skills: " + ", ".join(audit()))
        elif args.cmd == "plan":
            for rec in selected(catalog, args.profile, args.skill):
                print(rec["id"] + " <- " + rec["source"] + "@" + rec["revision"][:12] + "/" + rec["directory"])
        elif args.cmd == "install":
            names = install(selected(catalog, args.profile, args.skill))
            print("Installed instruction-only skills: " + ", ".join(names))
    except (SkillError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("skills: " + str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
