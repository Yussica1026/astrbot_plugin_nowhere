"""Regression tests for the latest gameplay fixes."""

from __future__ import annotations

import random
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from starlette.testclient import TestClient

from nowhere import encounters, server, walk, web
from nowhere.state import WorldState


@contextmanager
def _patched_bearing_world(*, freshwater: bool = False):
    """Ocean lies south; a steep dry downhill lies north."""

    def destination(lat, lon, bearing, distance):
        return lat + distance * __import__("math").cos(__import__("math").radians(bearing)), lon

    def elevation(lat, lon):
        return -200.0 if lat > 0 else 0.0

    def surface(lat, lon):
        if lat < 0:
            return "water_fresh" if freshwater else "water_ocean"
        return "grass"

    with (
        patch("nowhere.walk.terrain.destination", side_effect=destination),
        patch("nowhere.walk.terrain.elevation", side_effect=elevation),
        patch("nowhere.walk.terrain.surface", side_effect=surface),
    ):
        yield


def test_toward_sea_prefers_ocean_over_steep_downhill():
    with _patched_bearing_world():
        bearing, _ = walk._pick_semantic_bearing(0.0, 0.0, "toward_sea", 1.0)
    assert 90.0 < bearing < 270.0


def test_toward_sea_does_not_treat_freshwater_as_ocean():
    with _patched_bearing_world(freshwater=True):
        assert walk.water_ahead_km(0.0, 0.0, 180.0, max_km=2.0) is None


def test_city_filter_handles_extended_and_omitted_city_prefixes(monkeypatch):
    pools = {tag: [] for tag in encounters._KNOWN_TAGS}
    pools["americas"] = [
        "纽约街头。热狗摊的油锅在响。",
        "墨西哥城。广场上传来手风琴。",
        "洛杉矶。阳光落在棕榈树上。",
        "没有城市前缀的普通场景。",
    ]
    monkeypatch.setattr(encounters, "_POOL", pools)

    seen = {
        encounters.draw_encounter("city", 34.05, -118.24, random.Random(seed), "洛杉矶")
        for seed in range(100)
    }
    assert not any(text.startswith("纽约") for text in seen if text)
    assert not any(text.startswith("墨西哥城") for text in seen if text)
    assert any(text.startswith("洛杉矶") for text in seen if text)


def test_load_normalizes_naive_landed_at_to_utc(tmp_path, monkeypatch):
    save_file = tmp_path / "journey.json"
    save_file.write_text('{"landed_at": "2026-07-21T12:00:00"}', encoding="utf-8")
    monkeypatch.setattr("nowhere.state._SAVE_FILE", save_file)

    state = WorldState.load()
    assert state is not None
    assert state.landed_at == datetime(2026, 7, 21, 12, tzinfo=timezone.utc)


def test_state_endpoint_reuses_shared_timezone_finder(monkeypatch):
    state = WorldState()
    state.pos = (39.9042, 116.4074)
    state.landed_at = datetime(2026, 7, 21, 0, tzinfo=timezone.utc)
    server._state = state

    calls = []

    class Finder:
        def timezone_at(self, *, lat, lng):
            calls.append((lat, lng))
            return "Asia/Shanghai"

    monkeypatch.setattr(server, "_tf", Finder())
    body = TestClient(web.app).get("/state").json()

    assert calls == [(39.9042, 116.4074)]
    assert body["local_time"].endswith("+08:00")
