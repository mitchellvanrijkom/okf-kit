---
name: okf-build
description: >-
  Build or update an Open Knowledge Format (OKF) knowledge base from raw sources
  (transcripts, exported Confluence pages, Jira tickets). Use when the user says
  things like "build a knowledge base", "ingest these docs", "structure my notes
  into OKF", "turn raw/ into a wiki", or "update the knowledge base".
allowed-tools: Read, Write, Bash
---

# Build an OKF knowledge base

You are the agent, and **you are the model** — so you do the structuring step yourself, in
context. Do **not** shell out to `claude -p` or `okfkit structure`; that headless path is only for
cron/scripts with no agent driving them. Here, you read the sources and write the concepts
directly, then hand the deterministic plumbing to the CLI.

## Steps

1. **Read the raw sources.** List and read the `.md` files under `raw/` (transcripts, exported
   Confluence/Jira). If `raw/` is empty, tell the user where to drop files and stop.

2. **Structure them yourself** into atomic OKF concepts. For each source, split it into
   one-idea-per-concept and write each as `kb/concepts/<slug>.md` (use `kb/entities/<slug>.md` for
   specific named things — people, orgs, products). Rules:
   - One concept = one afgebakend, reusable idea. Drop noise (chit-chat, pure task assignments).
   - Use **canonical titles** so the same idea from different sources shares a slug (append the new
     source instead of making a near-duplicate page).
   - Neutral markdown prose, no speaker names.
   - Frontmatter: `type` (required — `Concept` / `Reference` / `Runbook` / `Decision` / `Note` /
     an entity subtype), a one-sentence `description`, `tags`, and `resource:` pointing at the
     source file it came from. Cross-reference related concepts with markdown links like
     `[retries](/concepts/retries.md)`.

3. **Generate the index** (the matching surface):
   ```bash
   okfkit index --kb kb        # or: uv run okfkit index
   ```

4. **Cross-link:**
   ```bash
   okfkit link --kb kb
   ```

5. **Validate** (okflint conformance gate):
   ```bash
   okfkit validate --kb kb
   ```

6. **Report**: how many sources you read, how many concept pages exist now, and the validate
   result. Remind the user to `git add kb/ && git commit` — git is the store.

## Notes
- You (the agent) do step 2. Steps 3–5 are deterministic CLI, no model.
- If validate reports hard errors, fix them (usually a missing `type`). Broken links are warnings,
  not failures.
- The `okfkit structure` CLI command exists for headless automation (a scheduled job with no agent).
  Inside this skill, ignore it and structure the content yourself.
