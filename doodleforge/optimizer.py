"""
Evolutionary Gait Optimizer.
Tunes Central Pattern Generator (CPG) parameters (motor frequencies, phase offsets, amplitudes)
using an elitist evolutionary strategy evaluated against headless physics simulations.
"""

from __future__ import annotations

import copy
import math
import random
from typing import List, Tuple
from doodleforge.models import (
    CreatureBlueprint,
    OptimizeGaitRequest,
    OptimizeGaitResponse,
    SimulateRequest,
)
from doodleforge.simulator import run_headless_simulation


def _evaluate_fitness(blueprint: CreatureBlueprint, duration: float = 2.0) -> Tuple[float, float]:
    """
    Simulates creature and calculates combined fitness:
    fitness = horizontal_speed + stability * 30 - fall_penalty
    Returns (fitness, avg_speed)
    """
    req = SimulateRequest(
        blueprint=blueprint,
        duration_seconds=duration,
        time_step=1.0 / 60.0,
    )
    res = run_headless_simulation(req)

    # Fitness formulation
    speed_term = res.avg_speed
    stability_term = res.stability_score * 40.0
    fall_penalty = 250.0 if res.fell_over else 0.0

    fitness = speed_term + stability_term - fall_penalty
    return (fitness, res.avg_speed)


def _mutate_blueprint(blueprint: CreatureBlueprint, mutation_rate: float = 0.25) -> CreatureBlueprint:
    """Clones and perturbs gait parameters with Gaussian noise."""
    mutated = copy.deepcopy(blueprint)
    loco = mutated.locomotion

    # Mutate base frequency
    if random.random() < 0.6:
        loco.base_frequency = max(0.5, min(4.0, loco.base_frequency + random.gauss(0, 0.25)))

    # Mutate phase offsets and amplitudes for each joint
    for joint in mutated.joints:
        j_id = joint.id
        cur_phase = loco.phase_offsets.get(j_id, 0.0)
        cur_amp = loco.amplitudes.get(j_id, 0.5)

        if random.random() < mutation_rate:
            new_phase = (cur_phase + random.gauss(0, 0.5)) % (2.0 * math.pi)
            loco.phase_offsets[j_id] = new_phase
            if joint.motor:
                joint.motor.phase = new_phase

        if random.random() < mutation_rate:
            new_amp = max(0.1, min(1.2, cur_amp + random.gauss(0, 0.15)))
            loco.amplitudes[j_id] = new_amp
            if joint.motor:
                joint.motor.amplitude = new_amp

    return mutated


def optimize_gait(request: OptimizeGaitRequest) -> OptimizeGaitResponse:
    """
    Runs evolutionary gait optimization over N generations
    to maximize forward walking velocity and balance stability.
    """
    best_blueprint = copy.deepcopy(request.blueprint)
    best_fitness, initial_speed = _evaluate_fitness(best_blueprint, request.simulation_duration)

    fitness_history: List[float] = [round(best_fitness, 2)]

    for gen in range(request.generations):
        # Generate mutated candidates
        candidates = [
            _mutate_blueprint(best_blueprint, mutation_rate=0.35)
            for _ in range(request.population_size)
        ]

        # Evaluate candidate population
        improved = False
        for cand in candidates:
            cand_fitness, cand_speed = _evaluate_fitness(cand, request.simulation_duration)
            if cand_fitness > best_fitness:
                best_fitness = cand_fitness
                best_blueprint = cand
                improved = True

        fitness_history.append(round(best_fitness, 2))

    # Evaluate final achieved speed
    _, final_speed = _evaluate_fitness(best_blueprint, request.simulation_duration)

    improvement_pct = 0.0
    if abs(initial_speed) > 1e-3:
        improvement_pct = max(0.0, ((final_speed - initial_speed) / max(0.1, abs(initial_speed))) * 100.0)
    elif final_speed > initial_speed:
        improvement_pct = 100.0

    return OptimizeGaitResponse(
        optimized_blueprint=best_blueprint,
        initial_speed=round(initial_speed, 2),
        final_speed=round(final_speed, 2),
        improvement_pct=round(improvement_pct, 1),
        fitness_history=fitness_history,
    )
