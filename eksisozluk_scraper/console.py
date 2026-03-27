"""Console output for eksi-scraper. All terminal output goes through this module."""

import sys
import time

_quiet = False
_verbose = False
_start_time = None
_errors = []
_stats = {
    "threads_ok": 0,
    "threads_failed": 0,
    "total_entries": 0,
}


def _write(msg):
    if not _quiet:
        sys.stderr.write(msg + "\n")
        sys.stderr.flush()


def configure(quiet=False, verbose=False):
    global _quiet, _verbose
    _quiet = quiet
    _verbose = verbose


def session_start(thread_count):
    global _start_time
    _start_time = time.monotonic()
    s = "" if thread_count == 1 else "s"
    _write(f"[eksi-scraper] Scraping {thread_count} thread{s}")


def thread_start(slug, page_count):
    s = "" if page_count == 1 else "s"
    _write(f"[{slug}] Found {page_count} page{s}")


def page_done(slug, page, total, entries, cumulative):
    if _verbose:
        _write(f"[{slug}] Page {page}/{total} ({entries} entries, {cumulative} total)")


def thread_done(slug, entry_count, elapsed, filename):
    _stats["threads_ok"] += 1
    _stats["total_entries"] += entry_count
    _write(f"[{slug}] Done: {entry_count} entries in {elapsed:.1f}s -> {filename}")


def thread_error(slug, err):
    _stats["threads_failed"] += 1
    msg = f"[{slug}] Error: {err}"
    _errors.append(msg)
    _write(msg)


def warn(msg):
    _write(f"[eksi-scraper] Warning: {msg}")


def error(msg):
    _errors.append(msg)
    _write(f"[eksi-scraper] Error: {msg}")


def session_end():
    if _quiet:
        return
    elapsed = time.monotonic() - _start_time if _start_time else 0
    total = _stats["threads_ok"] + _stats["threads_failed"]
    s = "" if total == 1 else "s"
    _write(
        f"[eksi-scraper] Finished: {total} thread{s}, "
        f"{_stats['total_entries']} entries, {elapsed:.1f}s elapsed"
    )
    if _errors:
        _write("")
        _write("Errors:")
        for err in _errors:
            _write(f"  {err}")
