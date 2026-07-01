---
name: okf-build
description: >-
  Build or update an Open Knowledge Format (OKF) knowledge base from raw sources
  (transcripts, exported Confluence pages, Jira tickets). Use when the user says
  things like "build a knowledge base", "ingest these docs", "structure my notes
  into OKF", "turn raw/ into a wiki", or "update the knowledge base".
allowed-tools: Bash, Read
---

# Build an OKF knowledge base

Run the okf-kit produce → consume pipeline. Assume the working directory is an okf-kit checkout
(or `okfkit` is installed on PATH). Prefer `uv run okfkit …`; fall back to `okfkit …`.

## Steps

1. **Check inputs.** Confirm raw sources exist under `raw/` (`.md` files — transcripts, exported
   Confluence/Jira). If `raw/` is empty, tell the user where to drop files and stop.

2. **Pick the LLM backend** for step 3 (no API token by default):
   - `--provider claude` (default) — the user's local Claude Code CLI (`claude -p`). No key.
   - `--provider opencode` — the `opencode` CLI (e.g. GitHub Copilot backend). No key.
   - `--provider openai` — an OpenAI-compatible endpoint; only this one needs `OKFKIT_API_KEY`
     (and optionally `OKFKIT_BASE_URL`) in the environment. Never write keys to disk.
   Default to `claude` unless the user asks otherwise.

3. **Structure** raw sources into OKF concepts:
   ```bash
   uv run okfkit structure --raw raw --kb kb
   ```

4. **Index** — generate the `index.md` matching surface:
   ```bash
   uv run okfkit index --kb kb
   ```

5. **Link** — add cross-links:
   ```bash
   uv run okfkit link --kb kb
   ```

6. **Validate** — run the okflint conformance gate:
   ```bash
   uv run okfkit validate --kb kb
   ```

7. **Report** back: how many sources were processed, how many concept pages exist now, and the
   validate result. Remind the user to `git add kb/ && git commit` — git is the store.

## Notes
- Steps 4–6 need no model and no network. Only step 3 uses the LLM.
- If validate reports hard errors, show them and offer to fix (usually a missing `type`).
- Broken links are warnings, not errors — do not treat them as failures.
