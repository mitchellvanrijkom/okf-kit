---
name: okf-check
description: >-
  Check that an Open Knowledge Format (OKF) knowledge base is conformant and healthy. Use when the
  user says "validate the knowledge base", "lint the OKF bundle", "is this conformant", "check the
  wiki", or before committing changes to a bundle.
allowed-tools: Bash
---

# Check an OKF knowledge base

Two checks, run both. Prefer `uv run okfkit …`; fall back to `okfkit …`.

1. **Fast local lint** (no dependencies, splits hard errors from soft warnings):
   ```bash
   uv run okfkit lint --kb kb
   ```
   - Exit 1 = hard error (unparseable frontmatter or missing/empty `type`) — must fix.
   - Exit 0 with warnings = fine (missing recommended fields, broken links are tolerated by spec).

2. **Authoritative validate** (runs okflint, the Google-spec linter):
   ```bash
   uv run okfkit validate --kb kb
   ```

## Report
Summarise: conformant yes/no, number of hard errors, and a short list of warnings worth acting on
(e.g. concepts missing a `description`, or genuinely broken links). Do not treat warnings as
failures. If there are hard errors, point at the exact file + field and offer to fix.
