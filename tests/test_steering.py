"""
Tests for doodleforge.steering module.
"""

import math
import pytest
from doodleforge.models import Point2D, SteeringConfig
from doodleforge.steering import (
    CreatureAgent,
    FoodPellet,
    SandboxEcosystem,
    SteeringBehaviors,
)


def test_steering_seek():
    pos = Point2D(x=0, y=0)
    vel = Point2D(x=0, y=0)
    target = Point2D(x=100, y=0)
    force = SteeringBehaviors.seek(pos, vel, target, max_speed=4.0, max_force=0.5)

    # Force should point in positive X direction
    assert force.x > 0.0
    assert abs(force.y) < 1e-4
    assert math.hypot(force.x, force.y) <= 0.5 + 1e-4


def test_steering_flee():
    pos = Point2D(x=50, y=0)
    vel = Point2D(x=0, y=0)
    threat = Point2D(x=100, y=0)
    force = SteeringBehaviors.flee(pos, vel, threat, max_speed=4.0, max_force=0.5)

    # Force should point away from threat (negative X direction)
    assert force.x < 0.0
    assert abs(force.y) < 1e-4


def test_steering_arrive_deceleration():
    pos = Point2D(x=95, y=0)
    vel = Point2D(x=4, y=0)
    target = Point2D(x=100, y=0)
    force = SteeringBehaviors.arrive(pos, vel, target, max_speed=4.0, max_force=0.5, slowing_radius=50.0)
    assert force is not None


def test_creature_agent_consumes_food():
    config = SteeringConfig(max_speed=4.0, perception_radius=150.0)
    agent = CreatureAgent("agent_1", Point2D(x=100, y=100), config)
    agent.energy = 50.0  # Hungry!

    food = FoodPellet("food_1", Point2D(x=105, y=100), energy_value=30.0)

    # Updating agent when very close (< 20px) should consume food
    force = agent.update(dt=0.1, food_pellets=[food], threats=[])
    assert food.consumed is True
    assert agent.energy > 50.0
    assert agent.state == "satisfied"


def test_sandbox_ecosystem_step():
    eco = SandboxEcosystem(world_width=800, world_height=600)
    eco.add_creature("creature_1", Point2D(x=200, y=200), SteeringConfig())
    forces = eco.step(0.016)

    assert "creature_1" in forces
    assert len(eco.food_pellets) > 0  # auto spawned food
