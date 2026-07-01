# okf-kit — Full Guide

A complete, copy-paste walkthrough. Everything below was run for real; the outputs are verbatim.
Written to be reproducible on a fresh machine (including Windows + WSL) with zero guesswork, and
readable by an agent so it can drive the tool for you.

- [1. Mental model — two layers](#1-mental-model)
- [2. Install (WSL / Linux / macOS)](#2-install)
- [3. Bundle layout](#3-bundle-layout)
- [4. Produce: `structure` (LLM)](#4-produce-structure)
- [5. `index` — the matching surface](#5-index)
- [6. `link` — cross-links](#6-link)
- [7. `lint` — fast conformance (hard vs soft)](#7-lint)
- [8. `validate` — okflint (Google spec)](#8-validate)
- [9. `navigate` — progressive-disclosure retrieval](#9-navigate)
- [10. End-to-end example](#10-end-to-end)
- [11. Environment variables](#11-environment-variables)
- [12. Troubleshooting](#12-troubleshooting)
- [13. For your agent / LLM](#13-for-your-agent)

---

## 1. Mental model

okf-kit is two layers. You can use them separately.

| Layer | Command(s) | Needs a model? |
|-------|-----------|----------------|
| **Produce** — raw notes/docs → structured OKF concepts | `structure` | Yes — your key/gateway, from env |
| **Consume + maintain** — index, link, lint, validate, answer | `index` `link` `lint` `validate` `navigate` | No |

The knowledge lives as plain markdown in git. Retrieval is **progressive disclosure**: read the
generated `index.md` (titles + one-line descriptions), pick the concept that matches, open it,
follow its links. No vector database.

---

## 2. Install

You need Python 3.12+ and [uv](https://docs.astral.sh/uv/). On Windows (WSL), Linux, or macOS:

```bash
# uv (one line, no admin rights needed)
curl -LsSf https://astral.sh/uv/install.sh | sh
exec $SHELL                       # reload PATH

# get okf-kit
git clone https://github.com/mitchellvanrijkom/okf-kit
cd okf-kit
uv sync                           # creates .venv from uv.lock (pyyaml, okflint, beartype)
uv sync --extra llm               # add this only if you want the `structure` (LLM) command
```

Run any command with `uv run okfkit <command>`:

```bash
uv run okfkit --help
```

```
usage: okfkit [-h] {structure,index,link,lint,validate,navigate} ...
```

> Prefer a global command? `uv tool install .` installs `okfkit` on your PATH (then drop the
> `uv run` prefix). For the LLM extra with a tool install: `uv tool install ".[llm]"`.

---

## 3. Bundle layout

An OKF bundle is just a directory of markdown files. okf-kit uses `kb/` by default (override with
`--kb`). A concept is one markdown file with YAML frontmatter; the **only required field is `type`**.

```
kb/
├── index.md              # generated · carries okf_version: "0.1"
├── log.md                # reserved · optional update history
├── concepts/
│   ├── index.md          # generated
│   ├── idempotency.md
│   └── …
└── entities/
    └── …
```

A single concept file (`kb/concepts/idempotency.md`):

```markdown
---
type: Concept
title: Idempotency
description: An operation that can be applied many times without changing the result beyond the first.
tags: [reliability, retries, data]
---
# Idempotency
An operation is idempotent when running it repeatedly yields the same result as running it once.
It is essential for safe [retries](/concepts/retries.md).
```

Cross-links are standard markdown links, bundle-relative and absolute: `/concepts/retries.md`.

---

## 4. Produce: `structure`

Turn a folder of raw sources (`raw/`) — meeting transcripts, exported Confluence pages, Jira
tickets — into OKF concept files. This is the only command that calls a model.

```bash
export OKFKIT_API_KEY="…"                       # required
export OKFKIT_BASE_URL="https://<gateway>/v1"   # optional: any OpenAI-compatible gateway
export OKFKIT_MODEL="gpt-4o-mini"               # optional: default model

uv run okfkit structure --raw raw --kb kb
```

Output shape:

```
[structure] 12 source(s) -> 34 concept(s) (model=gpt-4o-mini)
```

Each source is split into atomic concepts. A produced file looks exactly like the hand-written one
in §3 — `type` set, a one-sentence `description`, `tags`, and a clean markdown body, plus a
`resource:` pointing back at the source it came from. After `structure`, always run `index` →
`link` → `validate`.

> Keys never live in the repo. They are read from the environment only. Nothing is written to disk
> except the markdown concepts.

---

## 5. `index`

Generates an `index.md` in every directory. **This is the matching surface** an agent reads first.

```bash
uv run okfkit index
```

```
[index] 3 index.md geschreven (6 concepten)
```

Root `kb/index.md` (the only index that carries frontmatter, per spec §11):

```markdown
---
okf_version: "0.1"
---

# Subdirectories

* [concepts](concepts/) - 5 concept(s)
* [entities](entities/) - 1 concept(s)
```

`kb/concepts/index.md`:

```markdown
# Concepts

* [Backpressure](backpressure.md) - A feedback signal that slows producers when consumers cannot keep up.
* [Caching](caching.md) - Storing computed or fetched results to serve future requests faster.
* [Idempotency](idempotency.md) - An operation that can be applied many times without changing the result beyond the first.
* [Rate Limiting](rate-limiting.md) - Bounding how many requests a client may make in a time window.
* [Retries](retries.md) - Re-attempting a failed operation, usually with backoff, to handle transient errors.
```

---

## 6. `link`

Adds a `## Related` section to each concept, linking the mutual top-K concepts by shared tags
(mutual = A links B only if each is in the other's top-K — this prevents "everything links to
everything"). Idempotent: run it as often as you like.

```bash
uv run okfkit link --top 5
```

```
[link] 6 concepten gelinkt (mutual top-5 op gedeelde tags)
```

---

## 7. `lint`

Fast, dependency-light conformance check. It splits results the way the spec intends (OKF §9):

- **Hard errors** → non-conformant, exit code **1**: unparseable frontmatter, missing/empty `type`.
- **Soft warnings** → non-blocking, exit code **0**: missing recommended fields, broken links.

```bash
uv run okfkit lint
```

```
OKF v0.1 conformance — kb   (6 concepten)
  ! warn   concepts/backpressure.md: recommended field `resource` absent
  ! warn   concepts/backpressure.md: recommended field `timestamp` absent
  ! warn   concepts/backpressure.md: broken link -> /concepts/nonexistent.md
  … (recommended-field warnings for the other files) …

✓ conformant — 0 errors, 13 warning(s) (non-blocking)
```

A broken link is a **warning**, not an error — the spec says consumers must tolerate them (§5.3).
Remove a `type` field and lint fails hard:

```
  ✗ ERROR  concepts/caching.md: required field `type` absent or empty
✗ non-conformant — 1 error(s), 13 warning(s)   # exit 1
```

---

## 8. `validate`

Runs **okflint** — the independent, Google-spec conformance linter — against an auto-generated
manifest. Use this as the authoritative check (and in CI). `lint` is the fast local view; `validate`
is the canonical one.

```bash
uv run okfkit validate
```

```
✅ All files are OKF-conformant.
🔎 Indexing vault: 1 root
   10 .md files indexed
📦 Scanning bundle: 1 root
   10 files found
Files: 10 (6 concepts)
OKF status: {'conformant': 6, 'partial': 0, 'non_conformant': 0}
Wikilinks: 0 of which 0 broken
MD links: 35 of which 1 broken
Split candidates: 0
```

---

## 9. `navigate`

The retrieval demo, end to end. Reads the index, picks the matching concept, opens it, follows its
links. (The pick here is a transparent lexical proxy; in production your agent does the *semantic*
pick by reading the same index — see §13.)

```bash
uv run okfkit navigate "how do I safely retry a failed request?"
```

```
── STAP 1: index (titel + description) — 6 concepten ──
  concepts/backpressure            A feedback signal that slows producers when consumers cannot keep up.
  concepts/caching                 Storing computed or fetched results to serve future requests faster.
  concepts/idempotency             An operation that can be applied many times without changing the result beyond the first.
  concepts/rate-limiting           Bounding how many requests a client may make in a time window.
  concepts/retries                 Re-attempting a failed operation, usually with backoff, to handle transient errors.
  entities/token-bucket            A rate-limiting algorithm that grants requests while tokens are available.

── STAP 2: gekozen voor "how do I safely retry a failed request?" ──
  concepts/rate-limiting  —  Bounding how many requests a client may make in a time window.

── STAP 3: open concepts/rate-limiting.md ──
  # Rate Limiting
  Rate limiting protects a service from overload by capping request frequency …
  ## Related
  * [Backpressure](/concepts/backpressure.md)
  * [Retries](/concepts/retries.md)
  …

── STAP 4: volg links ──
  → /concepts/retries.md
  → /concepts/backpressure.md
  …
```

---

## 10. End-to-end

From raw sources to an answerable knowledge base, in five commands:

```bash
# 0. put raw sources (transcripts, exported Confluence/Jira as .md) in raw/
uv run okfkit structure     # raw/  -> kb/concepts/*.md   (LLM; needs env keys)
uv run okfkit index         # write index.md everywhere
uv run okfkit link          # cross-link
uv run okfkit validate      # okflint conformance gate
git add kb/ && git commit -m "kb: update"   # git is the store — no database, no binary index
```

Then ask it (from your agent, or the demo):

```bash
uv run okfkit navigate "your question"
```

---

## 11. Environment variables

| Variable | Used by | Meaning |
|----------|---------|---------|
| `OKFKIT_API_KEY`  | `structure` | API key for your model. **Required** for `structure`. Never committed. |
| `OKFKIT_BASE_URL` | `structure` | Optional. Any OpenAI-compatible endpoint. Omit for OpenAI itself. |
| `OKFKIT_MODEL`    | `structure` | Optional. Default model id (also settable per-run with `--model`). |

Consume/maintain commands (`index`, `link`, `lint`, `validate`, `navigate`) use **no** environment
and **no** network.

---

## 12. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `okflint: No module named 'beartype'` | okflint forgets to declare beartype; okf-kit pins it. Run `uv sync` (don't `pip install okflint` bare). |
| `requires-python … not satisfied` | okflint needs Python ≥3.12. Use `uv python install 3.12` or point uv at a 3.12+ interpreter. |
| `structure needs the llm extra` | `uv sync --extra llm` (installs `openai`). |
| `set OKFKIT_API_KEY …` | Export the key (and optionally `OKFKIT_BASE_URL`) before `structure`. |
| `VIRTUAL_ENV … does not match` warning | Harmless; happens if another venv is active. Ignore, or `deactivate` first. |
| `okflint not found` | You skipped `uv sync`, or you're not using `uv run`. okflint is a declared dependency. |

---

## 13. For your agent

You do not have to type CLI commands. Install the bundled skills (see the repo `skills/` folder and
`.claude-plugin/`), then talk to your agent in plain language:

- *"Build a knowledge base from the files in `raw/`."* → the agent runs `structure → index → link → validate`.
- *"What do we know about idempotency?"* → the agent answers by **progressive disclosure**:

  1. Read `kb/index.md` (and subdir `index.md` files) — the titles + descriptions.
  2. Pick the slug(s) that semantically match the question.
  3. Read those concept files under `kb/`.
  4. Follow their `[[/…]]` markdown links to neighbouring concepts.
  5. Answer from what was read, citing the concept paths. Fall back to `grep -r` for exact phrases.

That loop needs **no** model key — it is plain file reading. Only *building* the base (`structure`)
uses a model.
