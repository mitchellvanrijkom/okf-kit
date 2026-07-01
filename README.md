# okf-kit

A small toolkit for **Open Knowledge Format (OKF)** bundles.

Plain markdown in git. No database, no embeddings, no API keys, no network. Retrieval is
**progressive disclosure**: read the generated index, pick the concept, open it, follow its links —
the same way an agent (or a human) navigates a well-organised wiki.

> OKF v0.1 in one line: a directory of markdown files with YAML frontmatter; the only required
> field is `type`. `index.md` and `log.md` are reserved filenames.

## Why

Most "AI knowledge base" tools bolt a vector database onto your notes. OKF's own design does not:
knowledge lives as portable markdown, and consumers read an index and traverse links. `okf-kit` is
the smallest honest implementation of that idea — pure Python standard library, ~230 lines, runs
anywhere (including WSL), and never puts a derived artifact in your git history.

## Install

Requires Python 3.12+. One dependency: [PyYAML](https://pyyaml.org/) (robust frontmatter parsing).

Install the `okfkit` CLI (PyYAML is pulled in automatically):

```bash
uv tool install .          # from a clone
pipx install .             # alternative
uvx --from git+https://github.com/mitchellvanrijkom/okf-kit okfkit --help   # no clone
```

Or run from a clone after `pip install pyyaml`:

```bash
python3 okfkit.py --help
```

## Commands

```bash
okfkit structure             # raw sources -> OKF concepts via an LLM (keys from env; needs the llm extra)
okfkit index                 # generate index.md for every directory (the matching surface)
okfkit link                  # add a "Related" section per concept (mutual top-K on shared tags)
okfkit lint                  # fast, dependency-light conformance check — hard errors vs soft warnings
okfkit validate              # run okflint, the Google-spec conformance linter
okfkit graph                 # derive the typed graph (nodes=nouns, edges=verbs)
okfkit source add <git-url>  # add a git repo as a source (source list / sync / remove)
okfkit navigate "how do I safely retry a failed request?"
```

The **produce** side (`structure`) drives a language model you already have logged in — **no API token**:
`--provider claude` (your local Claude Code CLI, default), `--provider opencode` (e.g. GitHub Copilot),
or `--provider openai` (then set `OKFKIT_API_KEY`/`OKFKIT_BASE_URL` in env; `uv sync --extra llm`).
Everything else runs with no model at all.

### `index`
Writes an `index.md` in every directory listing its concepts (`* [Title](file.md) - description`)
and subdirectories. This is what a consuming agent reads *first* — the titles and one-line
descriptions are the matching surface it reasons over. The bundle-root `index.md` carries the only
permitted frontmatter: `okf_version: "0.1"`.

### `lint`
Splits results the way the spec intends (OKF §9):
- **Hard errors** (non-conformant, exit 1): unparseable frontmatter, missing/empty `type`.
- **Soft warnings** (non-blocking, exit 0): missing recommended fields, broken cross-links.

A consumer must never reject a bundle over soft issues.

### `navigate`
Demonstrates progressive-disclosure retrieval end to end: read the index → pick the matching
concept → open it → follow its links. The pick here is a transparent lexical proxy; in production a
language model does the *semantic* pick by reading the same index.

## How links work

Cross-links are standard markdown links to other concepts, e.g. `[retries](/concepts/retries.md)`.
Links inside fenced or inline code are ignored, so a code sample never creates a false edge.

## Layout

```
kb/
├── index.md              # generated · carries okf_version
├── log.md                # reserved · update history
├── concepts/
│   ├── index.md          # generated
│   ├── idempotency.md
│   └── …
└── entities/
    └── …
```

## License

MIT. See [LICENSE](LICENSE).

## Develop (uv)

```bash
uv sync                                    # create env from uv.lock
uv run python -m unittest discover -s tests -v
uv run okfkit lint
```

## Full guide

A complete, copy-paste walkthrough with real outputs (reproducible on WSL/Linux/macOS, and readable by
an agent): **[docs/GUIDE.md](docs/GUIDE.md)**.

## Skills — talk to it, don't type commands

This repo ships as a Claude Code plugin with three skills (in [`skills/`](skills/)), so you can
drive okf-kit in plain language:

| Skill | Say something like | It does |
|-------|--------------------|---------|
| `okf-build` | "build a knowledge base from `raw/`" | `structure` → `index` → `link` → `validate` |
| `okf-ask`   | "what do we know about idempotency?" | reads the index, opens the right concept, follows links (no model key) |
| `okf-check` | "is the bundle conformant?" | `lint` + `validate` |

Install the plugin:

```bash
# in Claude Code
/plugin marketplace add mitchellvanrijkom/okf-kit
/plugin install okf-kit
```
