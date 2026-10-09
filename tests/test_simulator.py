"""
Tests for doodleforge.simulator module.
"""

import pytest
from doodleforge.models import (
    Point2D,
    RigidBodyDef,
    SimulateRequest,
)
from doodleforge.presets import get_bipedal_strider, get_cyber_cheetah, get_wheeled_rover
from doodleforge.simulator import (
    PhysicsSandbox,
    SimBodyState,
    run_headless_simulation,
)


def test_sim_body_state_world_transform():
    body_def = RigidBodyDef(
        id="test_body",
        name="Box",
        part_type="torso",
        position=Point2D(x=100, y=100),
        angle=0.0,
        width=50,
        height=50,
    )
    state = SimBodyState(body_def)
    wx, wy = state.get_world_point(Point2D(x=10, y=20))
    assert wx == 110.0
    assert wy == 120.0


def test_headless_simulation_gravity_and_ground():
    bp = get_bipedal_strider()
    sandbox = PhysicsSandbox(bp, gravity_y=980.0, ground_y=500.0)

    # Initial torso position
    torso_before_y = sandbox.bodies[bp.torso_id].y

    # Advance physics by 0.5s
    for _ in range(30):
        sandbox.step(1.0 / 60.0)

    torso_after_y = sandbox.bodies[bp.torso_id].y
    # Torso drops under gravity towards ground
    assert torso_after_y > torso_before_y
    # But does not pass through infinitely because feet contact ground
    assert torso_after_y < 600.0


def test_headless_simulation_locomotion_progress():
    bp = get_wheeled_rover()
    req = SimulateRequest(blueprint=bp, duration_seconds=1.5, time_step=1.0 / 60.0)
    res = run_headless_simulation(req)

    assert res.blueprint_id == bp.id
    assert len(res.frames) > 0
    # Wheeled rover motor should propel forward (positive X)
    assert res.distance_traveled > 0.0
    assert res.avg_speed > 0.0
    assert res.stability_score > 0.0


def test_headless_simulation_stability_score():
    bp = get_cyber_cheetah()
    req = SimulateRequest(blueprint=bp, duration_seconds=1.0)
    res = run_headless_simulation(req)
    assert 0.0 <= res.stability_score <= 1.0
    assert isinstance(res.summary, str)
