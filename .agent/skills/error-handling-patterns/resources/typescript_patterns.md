# TypeScript / JavaScript Error Handling Patterns

## Custom Error Classes

```typescript
class ApplicationError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500,
    public details?: Record<string, any>,
  ) {
    super(message);
    this.name = this.constructor.name;
    Error.captureStackTrace(this, this.constructor);
  }
}

class ValidationError extends ApplicationError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, "VALIDATION_ERROR", 400, details);
  }
}

class NotFoundError extends ApplicationError {
  constructor(resource: string, id: string) {
    super(`${resource} not found`, "NOT_FOUND", 404, { resource, id });
  }
}
```

## Result Type Pattern

```typescript
type Result<T, E = Error> = { ok: true; value: T } | { ok: false; error: E };

const Ok  = <T>(value: T): Result<T, never>  => ({ ok: true, value });
const Err = <E>(error: E): Result<never, E>  => ({ ok: false, error });

function parseJSON<T>(json: string): Result<T, SyntaxError> {
  try {
    return Ok(JSON.parse(json) as T);
  } catch (error) {
    return Err(error as SyntaxError);
  }
}

// Consuming
const result = parseJSON<User>(userJson);
if (result.ok) {
  console.log(result.value.name);
} else {
  console.error("Parse failed:", result.error.message);
}
```

## Async Error Handling

```typescript
async function fetchUserOrders(userId: string): Promise<Order[]> {
  try {
    const user = await getUser(userId);
    return await getOrders(user.id);
  } catch (error) {
    if (error instanceof NotFoundError) return [];
    if (error instanceof NetworkError) return retryFetchOrders(userId);
    throw error; // Re-throw unexpected errors
  }
}
```

## Error Aggregation (multi-field validation)

```typescript
class ErrorCollector {
  private errors: Error[] = [];
  add(error: Error)    { this.errors.push(error); }
  hasErrors()          { return this.errors.length > 0; }
  throw(): never {
    if (this.errors.length === 1) throw this.errors[0];
    throw new AggregateError(this.errors, `${this.errors.length} errors occurred`);
  }
}

function validateUser(data: any): User {
  const errors = new ErrorCollector();
  if (!data.email) errors.add(new ValidationError("Email is required"));
  if (!data.name || data.name.length < 2)
    errors.add(new ValidationError("Name must be at least 2 characters"));
  if (errors.hasErrors()) errors.throw();
  return data as User;
}
```
