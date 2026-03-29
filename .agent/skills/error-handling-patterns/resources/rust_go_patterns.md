# Rust & Go Error Handling Patterns

## Rust — Result and Option Types

```rust
use std::fs::File;
use std::io::{self, Read};

// ? operator propagates errors automatically
fn read_file(path: &str) -> Result<String, io::Error> {
    let mut file = File::open(path)?;
    let mut contents = String::new();
    file.read_to_string(&mut contents)?;
    Ok(contents)
}

// Custom error enum
#[derive(Debug)]
enum AppError {
    Io(io::Error),
    Parse(std::num::ParseIntError),
    NotFound(String),
    Validation(String),
}

impl From<io::Error> for AppError {
    fn from(error: io::Error) -> Self { AppError::Io(error) }
}

fn read_number_from_file(path: &str) -> Result<i32, AppError> {
    let contents = read_file(path)?;                     // auto-converts io::Error
    let number = contents.trim().parse()
        .map_err(AppError::Parse)?;                      // explicit convert
    Ok(number)
}

// Option for nullable values
fn find_user(id: &str) -> Option<User> {
    users.iter().find(|u| u.id == id).cloned()
}

fn get_user_age(id: &str) -> Result<u32, AppError> {
    find_user(id)
        .ok_or_else(|| AppError::NotFound(id.to_string()))
        .map(|user| user.age)
}
```

## Go — Explicit Error Returns

```go
// Basic pattern
func getUser(id string) (*User, error) {
    user, err := db.QueryUser(id)
    if err != nil {
        return nil, fmt.Errorf("failed to query user: %w", err)  // wrap with %w
    }
    if user == nil {
        return nil, errors.New("user not found")
    }
    return user, nil
}

// Custom error type
type ValidationError struct {
    Field   string
    Message string
}
func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation failed for %s: %s", e.Field, e.Message)
}

// Sentinel errors
var (
    ErrNotFound     = errors.New("not found")
    ErrUnauthorized = errors.New("unauthorized")
)

// Checking and unwrapping
user, err := getUser("123")
if err != nil {
    if errors.Is(err, ErrNotFound) {
        // handle not found
    }
    var valErr *ValidationError
    if errors.As(err, &valErr) {
        fmt.Printf("Validation error on field: %s\n", valErr.Field)
    }
}
```
