# Python Error Handling Patterns

## Custom Exception Hierarchy

```python
class ApplicationError(Exception):
    def __init__(self, message: str, code: str = None, details: dict = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.utcnow()

class ValidationError(ApplicationError):
    pass

class NotFoundError(ApplicationError):
    pass

class ExternalServiceError(ApplicationError):
    def __init__(self, message: str, service: str, **kwargs):
        super().__init__(message, **kwargs)
        self.service = service

# Usage
def get_user(user_id: str) -> User:
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise NotFoundError("User not found", code="USER_NOT_FOUND",
                            details={"user_id": user_id})
    return user
```

## Context Manager for Resource Cleanup

```python
from contextlib import contextmanager

@contextmanager
def database_transaction(session):
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

## Retry with Exponential Backoff

```python
import time
from functools import wraps

def retry(max_attempts=3, backoff_factor=2.0, exceptions=(Exception,)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt < max_attempts - 1:
                        time.sleep(backoff_factor ** attempt)
                    else:
                        raise
        return wrapper
    return decorator

@retry(max_attempts=3, exceptions=(NetworkError,))
def fetch_data(url: str) -> dict:
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return response.json()
```

## Comprehensive Example

```python
def process_order(order_id: str) -> Order:
    try:
        if not order_id:
            raise ValidationError("Order ID is required")

        order = db.get_order(order_id)
        if not order:
            raise NotFoundError("Order", order_id)

        try:
            payment_result = payment_service.charge(order.total)
        except PaymentServiceError as e:
            logger.error(f"Payment failed for order {order_id}: {e}")
            raise ExternalServiceError(
                "Payment processing failed", service="payment_service",
                details={"order_id": order_id}
            ) from e

        order.status = "completed"
        order.payment_id = payment_result.id
        db.save(order)
        return order

    except ApplicationError:
        raise  # Re-raise known errors as-is
    except Exception as e:
        logger.exception(f"Unexpected error processing order {order_id}")
        raise ApplicationError("Order processing failed", code="INTERNAL_ERROR") from e
```
