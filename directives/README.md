# Directives

Directives are **Layer 1** of the 3-layer agent architecture. They are SOPs written in plain Markdown that tell the orchestrator (the LLM) *what* to do, *which scripts* to use, and *what the expected outputs* are.

---

## Directive format

```
---
description: one-line summary of what this SOP achieves
inputs:
  - name: <input name>
    description: what it is
outputs:
  - name: <output name>
    description: where it ends up
script: execution/<script_name>.py
---

## Goal
What this directive achieves and why.

## Steps
1. Gather inputs …
2. Run `python execution/<script>.py --arg value`
3. Verify output …

## Edge cases & notes
- Rate limits, retries, gotchas discovered during runs.
```

---

## Naming convention

| Pattern | Example |
|---|---|
| `<verb>_<noun>.md` | `scrape_website.md` |
| `<verb>_<noun>.md` | `export_to_sheets.md` |
| `<verb>_<noun>.md` | `summarise_papers.md` |

---

## Living documents

After every run, update the directive with:
- New edge cases discovered
- Better CLI flags that worked
- Any API limits hit

This is the **self-annealing loop**: break → fix → document → stronger system.
