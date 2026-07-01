---
name: okf-source
description: >-
  Add a git repository (GitLab/GitHub/…) as a source for the OKF knowledge base, or sync existing
  sources to pull the latest docs. Use when the user says "add this git source", "voeg deze git
  bron toe", "ingest this repo", "add <repo-url> as a source", "sync my sources", or "pull the
  latest docs from the repos".
allowed-tools: Bash, Read, Write
---

# Add / sync git repositories as knowledge sources

Many repos ship their documentation as markdown. Clone them, turn that markdown into OKF, and keep
it fresh. The registry `okf-sources.yaml` is committed; the clones under `raw/git/` are gitignored.

## Add a source

1. Register + clone (shallow):
   ```bash
   okfkit source add <git-url> [--name NAME] [--docs SUBDIR]
   ```
   Use `--docs` when the repo keeps docs in a subfolder (e.g. `--docs docs`). The command prints the
   docs path to ingest.

2. Turn the repo's markdown into OKF concepts. You are the agent, so **structure it yourself** (read
   the cloned `.md` files, write OKF concepts + typed edges into `kb/`) — or, headless, run
   `okfkit structure --raw raw/git/<name>/<docs> --kb kb`.

3. Then the deterministic steps:
   ```bash
   okfkit index --kb kb && okfkit link --kb kb && okfkit graph --kb kb && okfkit validate --kb kb
   ```

4. Report what was added; remind the user to `git add okf-sources.yaml kb/ && git commit`.

## Sync sources (pull changes)

```bash
okfkit source sync            # all sources; or: okfkit source sync <name>
```

This fetches the latest and mirrors each repo to upstream. For any source that changed, re-run the
structure → index → link → validate steps on it so the OKF (nodes + edges) reflects the new docs.

## List / remove

```bash
okfkit source list
okfkit source remove <name>
```

## Notes
- Never commit the clones (`raw/git/`); only the `okf-sources.yaml` manifest and the resulting `kb/`.
- Keep `--docs` tight so you only ingest real documentation, not every stray markdown file.
