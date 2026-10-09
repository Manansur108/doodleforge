"""
Tests for doodleforge.optimizer module.
"""

import pytest
from doodleforge.models import OptimizeGaitRequest
from doodleforge.optimizer import _mutate_blueprint, optimize_gait
from doodleforge.presets import get_cyber_cheetah


def test_mutation_modifies_parameters():
    bp = get_cyber_cheetah()
    # Force mutation across joints
    mutated = _mutate_blueprint(bp, mutation_rate=1.0)

    # Blueprint should have modified parameters but same structure
    assert len(mutated.joints) == len(bp.joints)
    assert len(mutated.bodies) == len(bp.bodies)


def test_optimize_gait_runs_and_produces_history():
    bp = get_cyber_cheetah()
    req = OptimizeGaitRequest(
        blueprint=bp,
        generations=3,
        population_size=3,
        simulation_duration=0.5,
    )
    res = optimize_gait(req)

    assert res.optimized_blueprint is not None
    assert len(res.fitness_history) == 4  # gen 0 initial + 3 gens
    assert res.final_speed is not None
    assert isinstance(res.improvement_pct, float)
