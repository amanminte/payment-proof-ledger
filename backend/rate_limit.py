"""In-memory rate limiter for authentication & authorization endpoints.

Policy: After 5 failed attempts, locks out the client/IP for 5 minutes (300s).
"""
from datetime import datetime, timedelta, timezone
import threading

MAX_ATTEMPTS = 5
LOCK_SECONDS = 300  # 5 minutes


class RateLimiter:
    def __init__(self, max_attempts=MAX_ATTEMPTS, lock_seconds=LOCK_SECONDS):
        self.max_attempts = max_attempts
        self.lock_seconds = lock_seconds
        self._lock = threading.Lock()
        self._failures = {}  # key -> list of datetime
        self._locked_until = {}  # key -> datetime

    def check_lockout(self, key, now=None):
        """Check if `key` is currently locked out. Returns (is_locked, remaining_seconds)."""
        now = now or datetime.now(timezone.utc)
        with self._lock:
            until = self._locked_until.get(key)
            if until:
                if now < until:
                    rem = int((until - now).total_seconds())
                    return True, max(1, rem)
                else:
                    # Lockout expired
                    del self._locked_until[key]
                    self._failures.pop(key, None)
            return False, 0

    def record_failure(self, key, now=None):
        """Record a failed attempt. If limit reached, locks out for `lock_seconds`.
        
        Returns (is_locked, remaining_seconds, attempts_used).
        """
        now = now or datetime.now(timezone.utc)
        with self._lock:
            # First check if already locked
            until = self._locked_until.get(key)
            if until and now < until:
                rem = int((until - now).total_seconds())
                return True, max(1, rem), self.max_attempts

            # Prune failures older than lock window
            cutoff = now - timedelta(seconds=self.lock_seconds)
            history = [t for t in self._failures.get(key, []) if t > cutoff]
            history.append(now)
            self._failures[key] = history

            if len(history) >= self.max_attempts:
                lock_time = now + timedelta(seconds=self.lock_seconds)
                self._locked_until[key] = lock_time
                return True, self.lock_seconds, len(history)

            return False, 0, len(history)

    def reset(self, key):
        """Reset failures and lock for a given key upon successful auth."""
        with self._lock:
            self._failures.pop(key, None)
            self._locked_until.pop(key, None)

    def clear_all(self):
        """Clear all state (for tests)."""
        with self._lock:
            self._failures.clear()
            self._locked_until.clear()


limiter = RateLimiter()
