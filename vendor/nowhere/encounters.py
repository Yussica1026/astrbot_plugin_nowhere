"""Global encounter pool -- literary scene fragments per region.

Loads ``data/encounters.txt`` (one encounter per line, each prefixed with
a ``[region]`` tag) and draws random encounters filtered by geographic region.
"""

from __future__ import annotations

import pathlib
import random

_DATA_DIR = pathlib.Path(__file__).resolve().parent / "data"
_ENCOUNTER_FILE = "encounters.txt"

# Tags that appear in the merged encounter file.
_KNOWN_TAGS = frozenset(
    {"polar", "africa", "asia", "americas", "europe", "oceania", "art", "natural"}
)

# Biome keywords that qualify as "urban" (art encounters mixed in).
_URBAN_BIOMES = frozenset(
    {"city", "town", "village", "settlement", "urban", "suburb", "port"}
)

_CITY_PREFIXES = (
    "洛杉矶", "旧金山", "纽约", "休斯敦", "芝加哥", "迈阿密", "华盛顿",
    "伦敦", "曼彻斯特", "爱丁堡", "巴黎", "里昂", "柏林", "慕尼黑", "汉堡",
    "罗马", "米兰", "威尼斯", "佛罗伦萨", "马德里", "巴塞罗那", "里斯本",
    "东京", "京都", "大阪", "名古屋", "首尔", "曼谷", "河内", "新加坡",
    "悉尼", "墨尔本", "奥克兰", "伊斯坦布尔", "莫斯科", "孟买", "德里",
    "迪拜", "开罗", "开普敦", "约翰内斯堡", "内罗毕", "亚的斯亚贝巴",
    "拉各斯", "马拉喀什", "卡萨布兰卡", "墨西哥城", "哈瓦那", "波哥大",
    "利马", "圣地亚哥", "布宜诺斯艾利斯", "里约", "圣保罗",
)

_POOL: dict[str, list[str]] | None = None


def _load() -> dict[str, list[str]]:
    """Load and partition encounters.txt into per-region pools (cached)."""
    global _POOL
    if _POOL is not None:
        return _POOL

    fp = _DATA_DIR / _ENCOUNTER_FILE
    pools: dict[str, list[str]] = {tag: [] for tag in _KNOWN_TAGS}

    if fp.exists():
        for line in fp.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#") or stripped == "---":
                continue
            # Expect format: [tag] text
            if stripped.startswith("[") and "]" in stripped:
                bracket_end = stripped.index("]")
                tag = stripped[1:bracket_end].lower().strip()
                text = stripped[bracket_end + 1 :].strip()
                # Skip stray section headers (e.g. "[europe] [Europe]")
                if text.startswith("[") and text.endswith("]"):
                    continue
                if tag in pools and text:
                    pools[tag].append(text)

    _POOL = pools
    return _POOL


def _region_for(biome: str, lat: float, lon: float) -> str:
    """Return the region tag for a given position.

    Priority (same geographic logic as before):
      1. polar   -- |lat| > 60
      2. africa  -- roughly -35..37 N, -20..55 E
      3. asia    -- roughly 0..55 N, 60..150 E
      4. americas -- roughly -55..70, -170..-30
      5. europe  -- roughly 35..72 N, -15..40 E
      6. natural -- default for land without strong region signal
    """
    if lat > 60 or lat < -60:
        return "polar"

    if -35 <= lat <= 37 and -20 <= lon <= 55:
        return "africa"

    if 0 <= lat <= 55 and 60 <= lon <= 150:
        return "asia"

    if -55 <= lat <= 70 and -170 <= lon <= -30:
        return "americas"

    # Oceania (Australia, NZ, Pacific)
    if -50 <= lat <= 0 and 110 <= lon <= 180:
        return "oceania"
    if -48 <= lat <= -10 and 160 <= lon <= 180:
        return "oceania"

    if 35 <= lat <= 72 and -15 <= lon <= 40:
        return "europe"

    return "natural"


def draw_encounter(
    biome: str, lat: float, lon: float, rng: random.Random, place_name: str = ""
) -> str | None:
    """Return a random encounter line for the given position, or None.

    1. Determine geographic region from lat/lon.
    2. Build a candidate pool: region lines + optional art/natural lines.
    3. Filter out city-specific encounters for wrong cities.
    4. Filter out climate-inappropriate encounters.
    5. Return a random choice with the ``[tag]`` prefix stripped.
    """
    pools = _load()
    region = _region_for(biome, lat, lon)

    # Start with the geographic region pool.
    candidates: list[str] = list(pools.get(region, []))

    # Mix in "natural" encounters (wilderness flavour).
    candidates.extend(pools.get("natural", []))

    # Mix in "art" encounters for urban / human-settlement biomes.
    biome_lower = biome.lower()
    if any(kw in biome_lower for kw in _URBAN_BIOMES):
        candidates.extend(pools.get("art", []))

    # Filter out city-specific encounters for wrong cities.  City-qualified
    # entries use both exact forms ("巴黎。") and compounds ("巴黎咖啡馆。").
    filtered = []
    for candidate in candidates:
        city = next((name for name in _CITY_PREFIXES if candidate.startswith(name)), None)
        if city is None or not place_name or city in place_name or place_name in city:
            filtered.append(candidate)
    candidates = filtered

    # Filter out climate-inappropriate encounters.
    abs_lat = abs(lat)
    # Tropical/rice paddy scenes only in subtropical/tropical regions (lat < 35)
    if abs_lat >= 35:
        tropical_keywords = ["稻田", "水牛", "梯田", "芭蕉", "椰子", "棕榈", "热带"]
        candidates = [c for c in candidates if not any(kw in c for kw in tropical_keywords)]
    # Snow/ice scenes only in cold regions (lat > 40 or lat < -40)
    if abs_lat < 40:
        cold_keywords = ["雪崩", "冰川", "冻土", "极光", "冰裂缝"]
        candidates = [c for c in candidates if not any(kw in c for kw in cold_keywords)]

    if not candidates:
        return None
    return rng.choice(candidates)
