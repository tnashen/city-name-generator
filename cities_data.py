import re
from pathlib import Path

CITIES_FILE = Path(__file__).parent / "cities" / "city_names.txt"
_cache: dict[str, list[str]] = {}

CATEGORIES = ["fantasy", "medieval", "sci-fi", "ancient"]


def _parse() -> dict[str, list[str]]:
    if _cache:
        return _cache
    text    = CITIES_FILE.read_text(encoding="utf-8")
    current = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or ("CITY NAMES" in stripped and stripped.startswith("=")):
            continue
        m = re.match(r"=== (.+) ===", stripped)
        if m:
            current = m.group(1).lower()
            _cache.setdefault(current, [])
        elif current and stripped and not stripped.startswith("="):
            names = [n.strip().rstrip(",") for n in stripped.split(",") if n.strip().rstrip(",")]
            _cache[current].extend(names)
    return _cache


def get_cities(category: str) -> list[str]:
    data = _parse()
    key  = category.lower()
    if key == "all":
        return [c for clist in data.values() for c in clist]
    if key not in data:
        raise ValueError(f"Unknown category '{category}'. Use: all, {', '.join(CATEGORIES)}")
    return data[key]


def stats() -> dict[str, int]:
    data = _parse()
    return {k: len(v) for k, v in data.items()}
