---
name: okf-ask
description: >-
  Answer a question from an Open Knowledge Format (OKF) knowledge base by reading the
  markdown directly — progressive disclosure, no vector search, no API key. Use when the
  user asks a question that should be answered from the knowledge base / wiki / "second brain",
  e.g. "what do we know about X", "how do we handle Y", "find the runbook for Z".
allowed-tools: Read, Grep, Bash
---

# Answer from an OKF knowledge base (progressive disclosure)

Do NOT load everything or build an index. Navigate the bundle the way it is designed to be read.
This needs no model key — it is plain file reading.

## Steps

1. **Read the index first.** Read `kb/index.md`, then the relevant subdirectory `index.md` files
   (e.g. `kb/concepts/index.md`, `kb/entities/index.md`). These list every concept as
   `* [Title](path.md) - one-line description`. This is your table of contents.

2. **Pick semantically.** From those titles + descriptions, choose the slug(s) that best match the
   user's question. This is your judgement, not a keyword match.

3. **Open the concept(s).** Read the chosen files under `kb/` (e.g. `kb/concepts/<slug>.md`).

4. **Follow links.** Concepts cross-reference each other with markdown links like
   `[retries](/concepts/retries.md)` and a `## Related` section. Follow the ones relevant to the
   question and read them too.

5. **Fallback.** If no title clearly matches, `grep -ri "<phrase>" kb/` for an exact mention, then
   read the file it points to.

6. **Answer** from what you read, and **cite the concept paths** you used (e.g.
   `kb/concepts/rate-limiting.md`). If the knowledge base does not contain the answer, say so —
   do not invent it.

## Why this way
OKF bundles are built for exactly this: the `index.md` descriptions are the matching surface, and
links are the graph. Reading a handful of small markdown files beats retrieving chunks, and it
keeps the citations exact.
