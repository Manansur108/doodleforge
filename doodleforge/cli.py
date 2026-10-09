"""
Command-Line Interface (CLI) for DoodleForge.
"""

from __future__ import annotations

import argparse
import sys
import uvicorn
from doodleforge.models import OptimizeGaitRequest, SimulateRequest
from doodleforge.optimizer import optimize_gait
from doodleforge.presets import get_all_presets, get_preset_by_id
from doodleforge.simulator import run_headless_simulation


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="doodleforge",
        description="DoodleForge: Real-Time Sketch-to-Physics Generative Creature Sandbox",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Run the FastAPI web server")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host address")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port number")
    serve_parser.add_argument("--reload", action="store_true", help="Enable hot reload")

    # presets command
    subparsers.add_parser("presets", help="List available preset creatures")

    # simulate command
    sim_parser = subparsers.add_parser("simulate", help="Run headless physics simulation")
    sim_parser.add_argument("--preset", default="preset_cyber_cheetah", help="Preset creature ID")
    sim_parser.add_argument("--duration", type=float, default=3.0, help="Simulation duration (seconds)")

    # optimize command
    opt_parser = subparsers.add_parser("optimize", help="Run evolutionary gait optimization")
    opt_parser.add_argument("--preset", default="preset_bipedal_strider", help="Preset creature ID")
    opt_parser.add_argument("--generations", type=int, default=10, help="Generations")

    args = parser.parse_args()

    if args.command == "serve" or args.command is None:
        host = getattr(args, "host", "127.0.0.1")
        port = getattr(args, "port", 8000)
        reload = getattr(args, "reload", False)
        print(f"[*] Starting DoodleForge server at http://{host}:{port}")
        uvicorn.run("doodleforge.server:app", host=host, port=port, reload=reload)

    elif args.command == "presets":
        print("\n=== DoodleForge Preset Creatures ===")
        presets = get_all_presets()
        for p in presets:
            print(f"- [{p.id}] {p.name}: {len(p.bodies)} bodies, {len(p.joints)} joints, Gait: {p.locomotion.gait_type.value}")
        print()

    elif args.command == "simulate":
        bp = get_preset_by_id(args.preset)
        if not bp:
            print(f"Error: Preset '{args.preset}' not found.")
            sys.exit(1)

        print(f"[*] Running simulation for '{bp.name}' ({args.duration}s)...")
        req = SimulateRequest(blueprint=bp, duration_seconds=args.duration)
        res = run_headless_simulation(req)
        print("\n=== Simulation Telemetry ===")
        print(f"Distance Traveled: {res.distance_traveled} px")
        print(f"Average Speed:     {res.avg_speed} px/s")
        print(f"Stability Score:   {res.stability_score}")
        print(f"Fell Over:         {res.fell_over}")
        print(f"Summary:           {res.summary}\n")

    elif args.command == "optimize":
        bp = get_preset_by_id(args.preset)
        if not bp:
            print(f"Error: Preset '{args.preset}' not found.")
            sys.exit(1)

        print(f"[*] Running evolutionary gait optimization on '{bp.name}' ({args.generations} gens)...")
        req = OptimizeGaitRequest(blueprint=bp, generations=args.generations)
        res = optimize_gait(req)
        print("\n=== Optimization Results ===")
        print(f"Initial Speed:   {res.initial_speed} px/s")
        print(f"Final Speed:     {res.final_speed} px/s")
        print(f"Improvement:     {res.improvement_pct}%")
        print(f"Fitness History: {res.fitness_history}\n")


if __name__ == "__main__":
    main()
