"""Load domain-stdlib JSON files from a directory.

Schema:
{
  "name": "search",
  "version": "1.0.0",
  "driver_hint": "search",
  "seed_pairs": [{"ns": "search", "name": "hits"}]
}
"""

from __future__ import annotations

import json
from pathlib import Path

from cek_host.structure import StructureError

from .domain_stdlib import DomainStdlib, REGISTRY, Registry


def parse_stdlib(doc: dict) -> DomainStdlib:
    name = str(doc.get("name") or "").strip()
    version = str(doc.get("version") or "1")
    hint = str(doc.get("driver_hint") or "")
    raw = doc.get("seed_pairs") or []
    pairs: list[tuple[str, str]] = []
    for item in raw:
        if isinstance(item, dict):
            pairs.append((str(item.get("ns") or ""), str(item.get("name") or "")))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            pairs.append((str(item[0]), str(item[1])))
        else:
            raise StructureError(f"{name}: bad seed_pairs entry")
    if doc.get("core"):
        raise StructureError("loaded stdlibs cannot claim core=true")
    return DomainStdlib(
        name=name,
        version=version,
        seed_pairs=tuple(pairs),
        driver_hint=hint,
        core=False,
    )


def load_file(path: Path, *, registry: Registry | None = None) -> DomainStdlib:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise StructureError(f"{path}: stdlib JSON must be an object")
    stdlib = parse_stdlib(doc)
    (registry or REGISTRY).register(stdlib)
    return stdlib


def load_dir(directory: Path | str, *, registry: Registry | None = None) -> list[DomainStdlib]:
    root = Path(directory)
    if not root.is_dir():
        raise FileNotFoundError(str(root))
    loaded: list[DomainStdlib] = []
    for path in sorted(root.glob("*.stdlib.json")):
        loaded.append(load_file(path, registry=registry))
    return loaded


def bundled_dir() -> Path:
    """Stdlibs shipped inside the cek_surface package."""
    return Path(__file__).resolve().parent / "stdlibs"


def load_bundled(*, registry: Registry | None = None) -> list[DomainStdlib]:
    return load_dir(bundled_dir(), registry=registry)
