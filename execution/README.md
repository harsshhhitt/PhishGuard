# Execution Scripts

Execution scripts are **Layer 3** of the 3-layer agent architecture. They are deterministic Python scripts that do the actual work: API calls, data processing, file I/O, and database interactions.

---

## Conventions

| Rule | Detail |
|---|---|
| **CLI** | Use `argparse`. Every script must be runnable from the command line. |
| **Secrets** | Load from `.env` via `python-dotenv`. Never hard-code keys. |
| **Logging** | Use `utils.get_logger(__name__)`. Log to stderr; data output to stdout or files. |
| **Exit codes** | `0` = success, `1` = runtime error, `2` = bad arguments. |
| **Idempotent** | Re-running with the same inputs should produce the same output safely. |
| **Documented** | Top-of-file docstring + inline comments on non-obvious logic. |

---

## Shared utilities

`utils.py` — always import from here:

```python
from utils import get_logger, load_env, retry
```

---

## Adding a new script

1. Check this folder — does a script already do what you need?
2. If not, create `execution/<verb>_<noun>.py`.
3. Add a corresponding directive in `directives/<verb>_<noun>.md`.
4. Test it standalone before the orchestrator calls it.
