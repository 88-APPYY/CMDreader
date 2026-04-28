"""Persist reading progress (chapter index + line offset) per book."""
from __future__ import annotations
import json
from pathlib import Path

_STORE = Path.home() / ".novel_reader_bookmarks.json"


def _load() -> dict:
    if _STORE.exists():
        try:
            return json.loads(_STORE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(data: dict) -> None:
    _STORE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get(book_path: str) -> tuple[int, int]:
    """Return (chapter_index, line_offset). Defaults to (0, 0)."""
    data = _load()
    entry = data.get(str(Path(book_path).resolve()), {})
    return entry.get("chapter", 0), entry.get("line", 0)


def save(book_path: str, chapter: int, line: int) -> None:
    data = _load()
    data[str(Path(book_path).resolve())] = {"chapter": chapter, "line": line}
    _save(data)


def list_bookmarks() -> dict:
    return _load()
