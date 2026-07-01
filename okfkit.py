#!/usr/bin/env python3
"""okf-kit — a small toolkit for Open Knowledge Format (OKF) bundles.

Plain markdown in git. Produce with an LLM (your key, your gateway); consume with zero LLM.
Retrieval is *progressive disclosure*: read the generated index, pick the concept,
open it, follow its links.

Commands:
  okfkit structure Raw sources -> OKF concepts via an LLM (OpenAI-compatible, keys from env).
  okfkit index     Generate index.md for every directory (the matching surface).
  okfkit link      Add a "Related" section per concept (mutual top-K on shared tags).
  okfkit lint      Fast dependency-light conformance check (hard errors vs soft warnings).
  okfkit validate  Run okflint, the Google-spec conformance linter.
  okfkit navigate  Progressive-disclosure lookup: index -> pick concept -> links.

OKF v0.1 in one line: a directory of markdown files with YAML frontmatter; the only
required field is `type`. index.md and log.md are reserved. See SPEC referenced in README.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml  # PyYAML — robust frontmatter parsing (nested/multiline/quoted)

RESERVED = {"index.md", "log.md"}
RECOMMENDED = ("title", "description", "resource", "tags", "timestamp")

# ------------------------------------------------------------------ frontmatter

def parse(text: str) -> tuple[dict, str, bool]:
    """Return (frontmatter, body, ok). ok=False if a frontmatter block is present but unparseable
    (unclosed fence, YAML error, or a non-mapping root)."""
    if not text.startswith("---\n"):
        return {}, text, True
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text, False  # opened but never closed
    body = text[end + 4:].lstrip("\n")
    try:
        data = yaml.safe_load(text[4:end])
    except yaml.YAMLError:
        return {}, body, False
    if data is None:
        return {}, body, True  # empty frontmatter block is valid
    if not isinstance(data, dict):
        return {}, body, False  # frontmatter must be a mapping
    return data, body, True


def is_empty(v) -> bool:
    """OKF `type` presence check (cf. mdsmith MDS071): nil / blank string / [] / {} == empty."""
    if v is None:
        return True
    if isinstance(v, str):
        return v.strip() == ""
    if isinstance(v, (list, dict)):
        return len(v) == 0
    return False  # numbers / booleans count as present


def slug_of(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")[:-3]


# ------------------------------------------------------------------ links (AST-safe)

_FENCE = re.compile(r"```.*?```", re.S)
_INLINE = re.compile(r"`[^`]*`")
_MDLINK = re.compile(r"\[[^\]]+\]\(([^)\s]+\.md)\)")


def outgoing_links(body: str) -> list[str]:
    """Markdown .md links, ignoring anything inside fenced or inline code (no regex-in-code bug)."""
    stripped = _INLINE.sub("", _FENCE.sub("", body))
    return _MDLINK.findall(stripped)


def load(root: Path) -> list[dict]:
    docs = []
    for p in sorted(root.rglob("*.md")):
        if p.name in RESERVED:
            continue
        raw = p.read_text(encoding="utf-8")
        fm, body, ok = parse(raw)
        tags = fm.get("tags", [])
        if isinstance(tags, str):
            tags = [tags] if tags else []
        docs.append({"path": p, "slug": slug_of(p, root), "fm": fm, "body": body,
                     "parse_ok": ok, "type": fm.get("type", ""),
                     "title": fm.get("title") or p.stem.replace("-", " ").title(),
                     "description": fm.get("description", ""), "tags": tags})
    return docs


# ------------------------------------------------------------------ commands

# ------------------------------------------------------------------ structure (LLM produce)

STRUCTURE_PROMPT = """You split a raw source document into atomic Open Knowledge Format concepts.
Return ONLY a JSON array. Each element:
{"type": "Concept|Reference|Runbook|Decision|Note", "title": "...", "description": "one sentence",
 "tags": ["...","..."], "body": "clean markdown"}
Rules: one idea per concept; drop noise; use canonical titles so the same idea from different
sources shares a slug; neutral prose, no speaker names.

Source file: %s
---
%s
---
Only the JSON array."""


def _llm_complete(prompt: str, model: str) -> str:
    """One completion against an OpenAI-compatible endpoint. Keys come from env, never the repo.
    Split out so tests can monkeypatch it without a network call."""
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("`structure` needs the llm extra:  uv sync --extra llm   (or: pip install openai)")
    key = os.environ.get("OKFKIT_API_KEY")
    if not key:
        sys.exit("set OKFKIT_API_KEY (and optionally OKFKIT_BASE_URL for a gateway) in your env")
    base = os.environ.get("OKFKIT_BASE_URL")
    client = OpenAI(base_url=base, api_key=key) if base else OpenAI(api_key=key)
    resp = client.chat.completions.create(
        model=model, temperature=0.2, messages=[{"role": "user", "content": prompt}])
    return resp.choices[0].message.content or ""


def _structure_one(text: str, fname: str, model: str) -> list[dict]:
    raw = _llm_complete(STRUCTURE_PROMPT % (fname, text[:12000]), model).strip()
    raw = re.sub(r"^```(?:json)?\n?|\n?```$", "", raw).strip()
    data = json.loads(raw)
    return data if isinstance(data, list) else [data]


def cmd_structure(args) -> int:
    raw_dir, kb = Path(args.raw), Path(args.kb)
    kb.mkdir(parents=True, exist_ok=True)
    sources = sorted(p for p in raw_dir.rglob("*.md") if p.name not in RESERVED)
    if not sources:
        print(f"[structure] no .md sources in {raw_dir}/")
        return 1
    total = 0
    for src in sources:
        for c in _structure_one(src.read_text(encoding="utf-8"), src.name, args.model):
            meta = {"type": c.get("type", "Note"), "title": c.get("title", "untitled"),
                    "description": c.get("description", ""),
                    "resource": str(src.relative_to(raw_dir.parent) if raw_dir.parent in src.parents else src),
                    "tags": c.get("tags", [])}
            slug = re.sub(r"[^\w]+", "-", meta["title"].lower()).strip("-") or "untitled"
            fm = "---\n" + yaml.safe_dump({k: v for k, v in meta.items() if v}, sort_keys=False).strip() + "\n---\n"
            (kb / "concepts").mkdir(exist_ok=True)
            (kb / "concepts" / f"{slug}.md").write_text(fm + "\n" + c.get("body", "").strip() + "\n", encoding="utf-8")
            total += 1
    print(f"[structure] {len(sources)} source(s) -> {total} concept(s) (model={args.model})")
    return 0


# ------------------------------------------------------------------ validate (okflint)

def cmd_validate(args) -> int:
    """Run okflint — the Google-spec conformance linter — with an auto-generated manifest."""
    import shutil
    import subprocess
    import tempfile
    if not shutil.which("okflint"):
        sys.exit("okflint not found. Install it:  uv sync   (okflint is a dependency)")
    kb = Path(args.kb).resolve()
    manifest = Path(tempfile.mkdtemp()) / "okf-base.yaml"
    manifest.write_text(
        f'base:\n  name: {kb.name}\n  roots:\n    - path: "{kb}"\n'
        f'  reserved_files:\n    index: index.md\n    log: log.md\n', encoding="utf-8")
    rc = 0
    for sub in (["validate", "--manifest", str(manifest)], ["audit", "--manifest", str(manifest)]):
        print(f"$ okflint {' '.join(sub[:1])}")
        rc = subprocess.run(["okflint"] + sub).returncode or rc
    return rc


def cmd_index(args) -> int:
    root = Path(args.kb)
    docs = load(root)
    by_dir: dict[Path, list] = {}
    for d in docs:
        by_dir.setdefault(d["path"].parent, []).append(d)
    all_dirs = {p for p in [root, *root.rglob("*")] if p.is_dir()}
    written = 0
    for directory in sorted(all_dirs, key=lambda x: str(x)):
        lines = []
        subdirs = sorted([c for c in directory.iterdir() if c.is_dir()])
        concepts = sorted(by_dir.get(directory, []), key=lambda d: d["title"].lower())
        if not subdirs and not concepts:
            continue
        is_root = directory == root
        if subdirs:
            lines.append("# Subdirectories\n")
            for sd in subdirs:
                n = len([f for f in sd.rglob("*.md") if f.name not in RESERVED])
                lines.append(f"* [{sd.name}]({sd.name}/) - {n} concept(s)")
            lines.append("")
        if concepts:
            lines.append("# Concepts\n")
            for c in concepts:
                lines.append(f"* [{c['title']}]({c['path'].name}) - {c['description']}")
        header = '---\nokf_version: "0.1"\n---\n\n' if is_root else ""
        (directory / "index.md").write_text(header + "\n".join(lines).strip() + "\n", encoding="utf-8")
        written += 1
    print(f"[index] {written} index.md geschreven ({len(docs)} concepten)")
    return 0


def cmd_link(args) -> int:
    root = Path(args.kb)
    docs = load(root)
    K = args.top
    def score(a, b):
        return len(set(a["tags"]) & set(b["tags"]))
    topk = {}
    for d in docs:
        cand = sorted(((score(d, o), o["slug"]) for o in docs if o["slug"] != d["slug"]),
                      key=lambda x: (-x[0], x[1]))
        topk[d["slug"]] = [sl for s, sl in cand[:K] if s > 0]
    by_slug = {d["slug"]: d for d in docs}
    for d in docs:
        related = [by_slug[sl] for sl in topk[d["slug"]] if d["slug"] in topk[sl]]  # mutual
        body = re.sub(r"\n#+ Related\n.*?(?=\n#+ |\Z)", "", d["body"], flags=re.S).rstrip()
        if related:
            rel = "\n".join(f"* [{r['title']}](/{r['slug']}.md)" for r in related)
            body += f"\n\n## Related\n{rel}\n"
        head = d["path"].read_text(encoding="utf-8")
        fm_raw = head[:head.find("\n---", 4) + 4] if head.startswith("---\n") else ""
        d["path"].write_text((fm_raw + "\n\n" if fm_raw else "") + body.strip() + "\n", encoding="utf-8")
    print(f"[link] {len(docs)} concepten gelinkt (mutual top-{K} op gedeelde tags)")
    return 0


def cmd_lint(args) -> int:
    root = Path(args.kb)
    docs = load(root)
    slugs = {d["slug"] for d in docs}
    hard, soft = [], []
    for d in docs:
        rel = d["path"].relative_to(root)
        if not d["parse_ok"]:
            hard.append(f"{rel}: frontmatter block opened but not closed")
            continue
        if is_empty(d["type"]):
            hard.append(f"{rel}: required field `type` absent or empty")
        for f in RECOMMENDED:
            if is_empty(d["fm"].get(f)):
                soft.append(f"{rel}: recommended field `{f}` absent")
        for tgt in outgoing_links(d["body"]):
            t = tgt.lstrip("/")[:-3]
            if t not in slugs:
                soft.append(f"{rel}: broken link -> {tgt}")
    print(f"OKF v0.1 conformance — {root}   ({len(docs)} concepten)")
    for h in hard:
        print(f"  \033[31m✗ ERROR\033[0m  {h}")
    for s in soft[: args.max_soft]:
        print(f"  \033[33m! warn \033[0m  {s}")
    if len(soft) > args.max_soft:
        print(f"  … +{len(soft) - args.max_soft} more warnings")
    if hard:
        print(f"\n\033[31m✗ non-conformant\033[0m — {len(hard)} error(s), {len(soft)} warning(s)")
        return 1
    print(f"\n\033[32m✓ conformant\033[0m — 0 errors, {len(soft)} warning(s) (non-blocking)")
    return 0


def cmd_navigate(args) -> int:
    """Progressive disclosure: read index -> pick concept -> show body head + links + grep fallback."""
    root = Path(args.kb)
    docs = load(root)
    query = args.query
    print(f"── STAP 1: index (titel + description) — {len(docs)} concepten ──")
    for d in sorted(docs, key=lambda x: x["slug"]):
        print(f"  {d['slug']:<32} {d['description']}")
    terms = {w for w in re.findall(r"[a-z0-9]{3,}", query.lower())}
    scored = sorted(docs, key=lambda d: -sum(t in (d["title"] + " " + d["description"] + " " + d["slug"]).lower() for t in terms))
    hit = scored[0] if scored and sum(t in (scored[0]["title"] + scored[0]["description"] + scored[0]["slug"]).lower() for t in terms) else None
    print(f"\n── STAP 2: gekozen voor \"{query}\" ──")
    if not hit:
        print("  geen semantische match — fallback: grep")
        for d in docs:
            if any(t in d["body"].lower() for t in terms):
                print(f"    grep-hit: {d['slug']}")
        return 0
    print(f"  {hit['slug']}  —  {hit['description']}")
    print(f"\n── STAP 3: open {hit['slug']}.md ──")
    print("\n".join("  " + l for l in hit["body"].strip().splitlines()[:10]))
    print(f"\n── STAP 4: volg links ──")
    for tgt in outgoing_links(hit["body"]) or ["(geen)"]:
        print(f"  → {tgt}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="okfkit", description="Tiny dependency-free OKF toolkit.")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn, extra in [("structure", cmd_structure, "structure"), ("index", cmd_index, None),
                            ("link", cmd_link, "top"), ("lint", cmd_lint, "max_soft"),
                            ("validate", cmd_validate, None), ("navigate", cmd_navigate, "query")]:
        sp = sub.add_parser(name)
        sp.add_argument("--kb", default="kb")
        if extra == "top":
            sp.add_argument("--top", type=int, default=5)
        if extra == "max_soft":
            sp.add_argument("--max-soft", type=int, default=50, dest="max_soft")
        if extra == "query":
            sp.add_argument("query")
        if extra == "structure":
            sp.add_argument("--raw", default="raw")
            sp.add_argument("--model", default=os.environ.get("OKFKIT_MODEL", "gpt-4o-mini"))
        sp.set_defaults(func=fn)
    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
