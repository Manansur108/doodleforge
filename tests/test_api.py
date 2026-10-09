"""
Tests for FastAPI REST API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from doodleforge.presets import get_bipedal_strider
from doodleforge.server import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "DoodleForge"


def test_presets_endpoints():
    # List all presets
    resp = client.get("/api/presets")
    assert resp.status_code == 200
    presets = resp.json()
    assert len(presets) >= 5

    # Get specific preset
    resp = client.get("/api/presets/preset_cyber_cheetah")
    assert resp.status_code == 200
    cheetah = resp.json()
    assert cheetah["name"] == "Cyber-Cheetah"

    # 404 for unknown preset
    resp = client.get("/api/presets/non_existent_preset")
    assert resp.status_code == 404


def test_rig_endpoint():
    payload = {
        "strokes": [
            {
                "points": [{"x": 100, "y": 100}, {"x": 200, "y": 100}, {"x": 200, "y": 150}, {"x": 100, "y": 150}],
                "color": "#00e5ff",
                "closed": True,
            },
            {
                "points": [{"x": 150, "y": 150}, {"x": 150, "y": 220}],
                "color": "#00e676",
                "closed": False,
            },
        ],
        "name": "API-Crawler",
    }
    resp = client.post("/api/rig", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "API-Crawler"
    assert len(data["bodies"]) == 2
    assert len(data["joints"]) == 1


def test_simulate_endpoint():
    bp = get_bipedal_strider()
    payload = {
        "blueprint": bp.model_dump(),
        "duration_seconds": 1.0,
    }
    resp = client.post("/api/simulate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "distance_traveled" in data
    assert "avg_speed" in data
    assert "stability_score" in data


def test_optimize_gait_endpoint():
    bp = get_bipedal_strider()
    payload = {
        "blueprint": bp.model_dump(),
        "generations": 2,
        "population_size": 2,
        "simulation_duration": 0.5,
    }
    resp = client.post("/api/optimize-gait", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "optimized_blueprint" in data
    assert "fitness_history" in data


def test_export_endpoint():
    bp = get_bipedal_strider()
    resp = client.post("/api/export", json=bp.model_dump())
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["blueprint_id"] == bp.id


def test_index_page():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "DoodleForge" in resp.text
