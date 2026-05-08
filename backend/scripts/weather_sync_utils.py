"""Shared helpers for scheduler-friendly weather sync scripts."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path


def read_lock_created_at(lock_file: Path) -> datetime | None:
    try:
        content = lock_file.read_text(encoding="utf-8").strip()
        if not content:
            return None
        parsed = datetime.fromisoformat(content)
    except (OSError, ValueError):
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def acquire_lock(lock_file: Path, *, stale_after_minutes: int) -> bool:
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    stale_after = timedelta(minutes=stale_after_minutes)
    created_at = read_lock_created_at(lock_file)
    if created_at is not None and datetime.now(UTC) - created_at > stale_after:
        lock_file.unlink(missing_ok=True)

    try:
        with lock_file.open("x", encoding="utf-8") as handle:
            handle.write(datetime.now(UTC).isoformat())
    except FileExistsError:
        return False
    except OSError:
        return False
    return True


def release_lock(lock_file: Path) -> None:
    lock_file.unlink(missing_ok=True)
