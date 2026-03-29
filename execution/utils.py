"""
utils.py — Shared utilities for all execution scripts.

Provides:
  - load_env()       : load .env into os.environ
  - get_logger()     : structured console logger
  - retry()          : decorator for retrying flaky calls
"""

import functools
import logging
import os
import sys
import time
from pathlib import Path

# ── .env loading ──────────────────────────────────────────────────────────────

def load_env(env_path: str | None = None) -> None:
    """
    Load variables from a .env file into os.environ.
    Searches for .env in the current directory and its parents if no path given.
    Requires: pip install python-dotenv
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        print(
            "[utils] WARNING: python-dotenv not installed. "
            "Run: pip install python-dotenv",
            file=sys.stderr,
        )
        return

    if env_path:
        load_dotenv(env_path, override=False)
    else:
        # Walk up from script location to find .env
        here = Path(__file__).resolve().parent
        for directory in [here, *here.parents]:
            candidate = directory / ".env"
            if candidate.exists():
                load_dotenv(candidate, override=False)
                break


# ── Logging ───────────────────────────────────────────────────────────────────

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Return a logger that writes to stderr.
    Log level is controlled by the LOG_LEVEL env variable (default: INFO).
    """
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


# ── Retry decorator ───────────────────────────────────────────────────────────

def retry(
    max_attempts: int = 3,
    delay: float = 2.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """
    Decorator: retry a function up to `max_attempts` times on failure.

    Args:
        max_attempts: total tries before giving up.
        delay:        initial wait in seconds between attempts.
        backoff:      multiplier applied to delay after each failure.
        exceptions:   tuple of exception types to catch.

    Example:
        @retry(max_attempts=5, delay=1.0, exceptions=(requests.HTTPError,))
        def fetch(url): ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger("retry")
            wait = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts:
                        logger.error(
                            "All %d attempts failed for %s. Last error: %s",
                            max_attempts, func.__name__, exc,
                        )
                        raise
                    logger.warning(
                        "Attempt %d/%d failed for %s: %s — retrying in %.1fs",
                        attempt, max_attempts, func.__name__, exc, wait,
                    )
                    time.sleep(wait)
                    wait *= backoff
        return wrapper
    return decorator


# ── Self-test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    load_env()
    log = get_logger("utils")
    log.info("Utils loaded OK.")

    @retry(max_attempts=3, delay=0.1)
    def _flaky(n={"c": 0}):
        n["c"] += 1
        if n["c"] < 3:
            raise ValueError("simulated transient error")
        return "success"

    result = _flaky()
    log.info("Retry decorator works — got: %s", result)
    print("Utils loaded OK.")
