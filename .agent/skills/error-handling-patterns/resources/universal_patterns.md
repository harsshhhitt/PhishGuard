# Universal Patterns

## Circuit Breaker (Python)

Prevents cascading failures in distributed systems by stopping calls to a failing service.

```python
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED   = "closed"     # Normal operation
    OPEN     = "open"       # Failing — reject all requests
    HALF_OPEN = "half_open" # Testing recovery

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=timedelta(seconds=60), success_threshold=2):
        self.failure_threshold  = failure_threshold
        self.timeout            = timeout
        self.success_threshold  = success_threshold
        self.failure_count      = 0
        self.success_count      = 0
        self.state              = CircuitState.CLOSED
        self.last_failure_time  = None

    def call(self, func):
        if self.state == CircuitState.OPEN:
            if datetime.now() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise Exception("Circuit breaker is OPEN")
        try:
            result = func()
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self):
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Usage
cb = CircuitBreaker()
def fetch_data():
    return cb.call(lambda: external_api.get_data())
```

## Graceful Degradation (Python)

Fall back to a secondary source when the primary fails.

```python
from typing import Callable, TypeVar, Optional
T = TypeVar('T')

def with_fallback(primary: Callable[[], T], fallback: Callable[[], T], log_error=True) -> T:
    try:
        return primary()
    except Exception as e:
        if log_error:
            logger.error(f"Primary function failed: {e}")
        return fallback()

# Example: cache-first with DB fallback
def get_user_profile(user_id: str) -> UserProfile:
    return with_fallback(
        primary=lambda: fetch_from_cache(user_id),
        fallback=lambda: fetch_from_database(user_id)
    )

def _try(func: Callable[[], Optional[T]]) -> Optional[T]:
    try:
        return func()
    except Exception:
        return None

# Multiple fallbacks
def get_exchange_rate(currency: str) -> float:
    return (
        _try(lambda: provider_1.get_rate(currency))
        or _try(lambda: provider_2.get_rate(currency))
        or _try(lambda: cache.get_rate(currency))
        or DEFAULT_RATE
    )
```
