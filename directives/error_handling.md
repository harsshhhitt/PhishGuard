---
description: Apply error handling patterns (retry, circuit breaker, custom exceptions, Result types) when building or improving resilient code
inputs:
  - name: language
    description: Target language (Python, TypeScript, Rust, Go)
  - name: context
    description: What is failing or what needs to be made resilient
outputs:
  - name: error handling code
    description: Implementation using the appropriate pattern
skill: .agent/skills/error-handling-patterns/SKILL.md
---

## Goal
Apply the right error handling pattern for the task at hand and implement it correctly.

## Steps
1. Read `.agent/skills/error-handling-patterns/SKILL.md` for the checklist and language index.
2. Open the relevant `resources/<language>_patterns.md` file for code templates.
3. Choose the pattern: exceptions hierarchy / Result type / circuit breaker / graceful degradation.
4. Implement, ensuring: meaningful messages, resource cleanup, correct log level, no silent swallowing.
5. Test error paths explicitly — don't just test the happy path.

## Edge cases & notes
- For distributed / async systems, always read `resources/universal_patterns.md` for circuit breaker and fallback patterns.
- For form/bulk validation (multiple fields), use the error aggregation pattern (TypeScript file).
- Retry is in `execution/utils.py` (Python) — import from there rather than reimplementing.
