# okf-kit

A tiny, dependency-free toolkit for **Open Knowledge Format (OKF)** bundles.

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

Requires Python 3.10+. One dependency: [PyYAML](https://pyyaml.org/) (robust frontmatter parsing).

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
python3 okfkit.py index      # generate index.md for every directory (the matching surface)
python3 okfkit.py link       # add a "Related" section per concept (mutual top-K on shared tags)
python3 okfkit.py lint       # conformance check — hard errors vs soft warnings
python3 okfkit.py navigate "how do I safely retry a failed request?"
```

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
