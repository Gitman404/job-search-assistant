import json
from pathlib import Path
from typing import Any


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"seen": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def is_seen(state: dict[str, Any], *, source: str, external_id: str) -> bool:
    seen = state.setdefault("seen", {})
    ids = seen.setdefault(source, {})
    return external_id in ids


def mark_seen(state: dict[str, Any], *, source: str, external_id: str, meta: dict[str, Any]) -> None:
    seen = state.setdefault("seen", {})
    ids = seen.setdefault(source, {})
    ids[external_id] = meta



