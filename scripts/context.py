#!/usr/bin/env python3
"""ICM route verification and transparent, hash-only context planning.

This is a context FILE manifest, not a semantic retriever or permission boundary.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
MANDATORY_STAGES = {"research", "specify", "implement", "verify", "release"}
HEADINGS = ("## Inputs", "## Process", "## Outputs", "## Permissions", "## References")


class ContextError(ValueError):
    pass


def confined_file(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative or "\x00" in relative:
        raise ContextError("unsafe context path")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or any(x in (".", "..") for x in relative.split("/")) or ":" in pure.parts[0]:
        raise ContextError("path must be relative and may not traverse directories")
    parent = root.resolve()
    target = (parent / relative).resolve()
    if not target.is_relative_to(parent):
        raise ContextError("context reference escapes repository: " + relative)
    if not target.is_file():
        raise ContextError("missing context reference: " + relative)
    return target


def validate(root: Path = ROOT) -> dict:
    confined_file(root, "AGENTS.md")
    confined_file(root, "CONTEXT.md")
    try:
        routes = json.loads(confined_file(root, "context/routes.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ContextError("invalid context route registry") from exc
    if set(routes) != {"version", "stages"} or routes["version"] != "0.1":
        raise ContextError("unsupported context route registry")
    stages = routes["stages"]
    if not isinstance(stages, dict) or not MANDATORY_STAGES.issubset(stages):
        raise ContextError("missing required ICM stage")
    for name, entry in stages.items():
        if not name or not all(c.islower() or c.isdigit() or c == "-" for c in name):
            raise ContextError("invalid stage name: " + name)
        if not isinstance(entry, dict) or set(entry) != {"context", "references"}:
            raise ContextError("invalid stage entry: " + name)
        expected = "context/stages/" + name + "/CONTEXT.md"
        if entry["context"] != expected:
            raise ContextError("noncanonical stage context: " + name)
        doc = confined_file(root, entry["context"]).read_text()
        lines = doc.splitlines()
        if len(lines) > 80:
            raise ContextError("stage context exceeds 80 lines: " + name)
        locations = [lines.index(header) if header in lines else -1 for header in HEADINGS]
        if -1 in locations or locations != sorted(locations):
            raise ContextError("stage missing ordered contract sections: " + name)
        for index, start in enumerate(locations):
            end = locations[index + 1] if index + 1 < len(locations) else len(lines)
            if not any(line.strip() and not line.startswith("#") for line in lines[start + 1:end]):
                raise ContextError("empty stage contract section: " + name + " " + HEADINGS[index])
        refs = entry["references"]
        if not isinstance(refs, list) or not refs or len(refs) > 30 or len(refs) != len(set(refs)):
            raise ContextError("invalid or duplicate stage references: " + name)
        for path in refs:
            if path in ("AGENTS.md", "CONTEXT.md", entry["context"]) or path.startswith("context/stages/"):
                raise ContextError("duplicate context-layer authority: " + path)
            confined_file(root, path)
    return routes


def plan(stage: str, working: list[str] | None = None, root: Path = ROOT) -> dict:
    routes = validate(root)
    if stage not in routes["stages"]:
        raise ContextError("unknown stage: " + stage)
    selected = routes["stages"][stage]
    references = ([("orientation", "AGENTS.md"), ("routing", "CONTEXT.md"),
                   ("stage", selected["context"])]
                  + [("reference", x) for x in selected["references"]]
                  + [("working", x) for x in (working or [])])
    files = []
    seen = set()
    for layer, name in references:
        if name in seen:
            raise ContextError("duplicate loaded context: " + name)
        seen.add(name)
        content = confined_file(root, name).read_bytes()
        files.append({"layer": layer, "path": name, "bytes": len(content),
                      "sha256": hashlib.sha256(content).hexdigest()})
    return {"version": "0.1", "stage": stage, "files": files,
            "note": "File selection and hashes only; not proof of what an agent read."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    sub.add_parser("check")
    p = sub.add_parser("plan")
    p.add_argument("stage")
    p.add_argument("--working", action="append", default=[], metavar="PATH")
    args = parser.parse_args()
    try:
        if args.operation == "check":
            stages = validate()["stages"]
            print("ICM context routing valid: " + ", ".join(sorted(stages)))
        else:
            print(json.dumps(plan(args.stage, args.working), indent=2))
    except (ContextError, OSError, UnicodeError, TypeError, KeyError) as exc:
        print("ICM context validation failed: " + str(exc), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
