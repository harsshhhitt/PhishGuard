---
name: error-handling-patterns
description: Master error handling patterns across languages including exceptions, Result types, error propagation, and graceful degradation to build resilient applications. Use when implementing error handling, designing APIs, or improving application reliability.
---

# Error Handling Patterns

## When to Use This Skill
- Implementing error handling in new features
- Designing error-resilient APIs
- Handling async/concurrent errors
- Implementing retry, circuit breaker, or fallback patterns
- Improving error messages for users and developers

## Error Categories

| Category | Examples |
|---|---|
| **Recoverable** | Network timeouts, missing files, invalid input, rate limits |
| **Unrecoverable** | OOM, stack overflow, programming bugs |

**Philosophy:**
- **Exceptions** — unexpected/exceptional conditions
- **Result/Either types** — expected failures, validation
- **Panics** — unrecoverable programmer errors

## Checklist
- [ ] Identify error category (recoverable vs unrecoverable)
- [ ] Choose the right pattern for the language (see resources/)
- [ ] Add meaningful error messages (what happened + how to fix)
- [ ] Clean up resources (try-finally, context managers, defer)
- [ ] Log at the right level — error for unexpected, not for expected failures
- [ ] Handle async errors explicitly (no unhandled promise rejections)
- [ ] Validate input early — fail fast

## Language-Specific Patterns

See the `resources/` folder for full code examples:

| Language | File |
|---|---|
| Python | [python_patterns.md](resources/python_patterns.md) |
| TypeScript / JavaScript | [typescript_patterns.md](resources/typescript_patterns.md) |
| Rust & Go | [rust_go_patterns.md](resources/rust_go_patterns.md) |

## Universal Patterns

See [universal_patterns.md](resources/universal_patterns.md) for:
- **Circuit Breaker** — prevent cascading failures in distributed systems
- **Error Aggregation** — collect multiple errors before failing (e.g., form validation)
- **Graceful Degradation** — fallback to secondary source on failure

## Best Practices

1. **Fail fast** — validate input early
2. **Preserve context** — include stack traces, timestamps, metadata
3. **Meaningful messages** — explain what happened and how to fix it
4. **Handle at the right level** — catch where you can meaningfully respond
5. **Never swallow errors silently** — log or re-throw
6. **Don't log + re-throw** — creates duplicate log entries
7. **Type-safe errors** — use typed error hierarchies

## Common Pitfalls

- `except Exception` / broad catches that hide bugs
- Empty catch blocks
- Forgetting to close files/connections (missing finally/defer)
- Vague error messages ("Error occurred")
- Ignoring unhandled async rejections
