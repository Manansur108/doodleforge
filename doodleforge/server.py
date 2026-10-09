"""
FastAPI Server and REST API for DoodleForge.
Exposes endpoints for sketch vectorization, auto-rigging, headless simulation,
evolutionary gait optimization, preset libraries, and serves interactive frontend assets.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from doodleforge.models import (
    CreatureBlueprint,
    OptimizeGaitRequest,
    OptimizeGaitResponse,
    RigRequest,
    SimulateRequest,
    SimulateResponse,
)
from doodleforge.optimizer import optimize_gait
from doodleforge.presets import get_all_presets, get_preset_by_id
from doodleforge.rigging import rig_strokes
from doodleforge.simulator import run_headless_simulation

app = FastAPI(
    title="DoodleForge API",
    description="Real-Time Sketch-to-Physics Generative Creature Sandbox",
    version="0.1.0",
)

# CORS middleware for local frontend dev or external canvas embeds
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to static frontend assets
STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.get("/api/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "DoodleForge", "version": "0.1.0"}


@app.post("/api/rig", response_model=CreatureBlueprint)
def rig_sketch(req: RigRequest) -> CreatureBlueprint:
    """
    Parses freehand sketch strokes, identifies anatomical limbs and pivots,
    and returns a fully rigged physics blueprint with joints and gait motors.
    """
    if not req.strokes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one stroke is required to rig a creature.",
        )

    blueprint = rig_strokes(
        strokes=req.strokes,
        creature_name=req.name or "DoodleCreature",
        simplify_tolerance=req.simplify_tolerance,
    )
    return blueprint


@app.post("/api/simulate", response_model=SimulateResponse)
def simulate_creature(req: SimulateRequest) -> SimulateResponse:
    """
    Executes a headless 2D rigid-body physics simulation of the creature,
    evaluating horizontal locomotion speed, balance stability, and trajectory.
    """
    result = run_headless_simulation(req)
    return result


@app.post("/api/optimize-gait", response_model=OptimizeGaitResponse)
def optimize_creature_gait(req: OptimizeGaitRequest) -> OptimizeGaitResponse:
    """
    Applies evolutionary strategy to tune motor frequencies and joint phase offsets,
    optimizing forward walking velocity and stability.
    """
    result = optimize_gait(req)
    return result


@app.get("/api/presets", response_model=List[CreatureBlueprint])
def list_presets() -> List[CreatureBlueprint]:
    """Returns library of pre-designed creatures."""
    return get_all_presets()


@app.get("/api/presets/{preset_id}", response_model=CreatureBlueprint)
def get_preset(preset_id: str) -> CreatureBlueprint:
    """Fetches a specific preset creature by ID."""
    bp = get_preset_by_id(preset_id)
    if not bp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset creature '{preset_id}' not found.",
        )
    return bp


@app.post("/api/export")
def export_blueprint(blueprint: CreatureBlueprint) -> Dict[str, Any]:
    """Exports and validates creature blueprint as a portable JSON specification."""
    return {
        "status": "success",
        "blueprint_id": blueprint.id,
        "name": blueprint.name,
        "blueprint": blueprint.model_dump(),
    }


# Mount static files and root route
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", response_class=HTMLResponse)
    def index():
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return HTMLResponse("<h1>DoodleForge backend running. Static index.html not found.</h1>")
