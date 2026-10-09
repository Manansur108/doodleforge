"""
Autonomous behavioral steering and ecological sandbox loop.
Implements Reynolds steering behaviors (Seek, Flee, Wander, Arrive, Obstacle Avoidance)
and manages multi-creature sandbox interactions with food particles and energy dynamics.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Tuple
from doodleforge.models import Point2D, SteeringConfig


def clamp_vector(vx: float, vy: float, max_mag: float) -> Tuple[float, float]:
    """Clamps a 2D vector's magnitude to max_mag."""
    mag_sq = vx * vx + vy * vy
    if mag_sq > max_mag * max_mag:
        mag = math.sqrt(mag_sq)
        if mag > 1e-6:
            return ((vx / mag) * max_mag, (vy / mag) * max_mag)
    return (vx, vy)


def normalize_vector(vx: float, vy: float) -> Tuple[float, float]:
    """Normalizes a 2D vector to unit length."""
    mag = math.hypot(vx, vy)
    if mag > 1e-6:
        return (vx / mag, vy / mag)
    return (1.0, 0.0)


class SteeringBehaviors:
    """Calculates steering forces according to Craig Reynolds' model."""

    @staticmethod
    def seek(
        pos: Point2D, vel: Point2D, target: Point2D, max_speed: float, max_force: float
    ) -> Point2D:
        """Steers creature towards target position at max speed."""
        desired_x = target.x - pos.x
        desired_y = target.y - pos.y
        ux, uy = normalize_vector(desired_x, desired_y)
        desired_x = ux * max_speed
        desired_y = uy * max_speed

        steer_x = desired_x - vel.x
        steer_y = desired_y - vel.y
        fx, fy = clamp_vector(steer_x, steer_y, max_force)
        return Point2D(x=fx, y=fy)

    @staticmethod
    def flee(
        pos: Point2D, vel: Point2D, threat: Point2D, max_speed: float, max_force: float
    ) -> Point2D:
        """Steers creature away from a threat position."""
        desired_x = pos.x - threat.x
        desired_y = pos.y - threat.y
        ux, uy = normalize_vector(desired_x, desired_y)
        desired_x = ux * max_speed
        desired_y = uy * max_speed

        steer_x = desired_x - vel.x
        steer_y = desired_y - vel.y
        fx, fy = clamp_vector(steer_x, steer_y, max_force)
        return Point2D(x=fx, y=fy)

    @staticmethod
    def arrive(
        pos: Point2D,
        vel: Point2D,
        target: Point2D,
        max_speed: float,
        max_force: float,
        slowing_radius: float = 80.0,
    ) -> Point2D:
        """Smoothly decelerates creature as it approaches target."""
        dx = target.x - pos.x
        dy = target.y - pos.y
        d = math.hypot(dx, dy)

        if d < 1e-4:
            return Point2D(x=-vel.x * 0.5, y=-vel.y * 0.5)

        speed = max_speed * (d / slowing_radius) if d < slowing_radius else max_speed
        desired_x = (dx / d) * speed
        desired_y = (dy / d) * speed

        steer_x = desired_x - vel.x
        steer_y = desired_y - vel.y
        fx, fy = clamp_vector(steer_x, steer_y, max_force)
        return Point2D(x=fx, y=fy)

    @staticmethod
    def wander(
        pos: Point2D,
        vel: Point2D,
        wander_angle: float,
        config: SteeringConfig,
        angle_change: float = 0.4,
    ) -> Tuple[Point2D, float]:
        """
        Projects a circle ahead of the velocity vector and steers towards a point on its circumference.
        Returns (steering_force, new_wander_angle).
        """
        vx, vy = normalize_vector(vel.x, vel.y)
        circle_center_x = pos.x + vx * config.wander_distance
        circle_center_y = pos.y + vy * config.wander_distance

        # Perturb wander angle
        new_angle = wander_angle + (random.random() - 0.5) * angle_change
        target_x = circle_center_x + math.cos(new_angle) * config.wander_radius
        target_y = circle_center_y + math.sin(new_angle) * config.wander_radius

        steer = SteeringBehaviors.seek(
            pos, vel, Point2D(x=target_x, y=target_y), config.max_speed, config.max_force
        )
        return (steer, new_angle)


class FoodPellet:
    """Nutrient pellet in sandbox world that creatures can consume."""

    def __init__(self, id_str: str, position: Point2D, energy_value: float = 35.0):
        self.id = id_str
        self.position = position
        self.energy_value = energy_value
        self.radius: float = 8.0
        self.consumed: bool = False


class CreatureAgent:
    """Autonomous agent wrapping a creature's physical state with behavioral AI."""

    def __init__(self, creature_id: str, position: Point2D, config: SteeringConfig):
        self.creature_id = creature_id
        self.position = position
        self.velocity = Point2D(x=1.0, y=0.0)
        self.config = config
        self.energy: float = 100.0
        self.max_energy: float = 150.0
        self.wander_angle: float = random.uniform(0, 2 * math.pi)
        self.state: str = "wandering"  # "wandering", "seeking_food", "fleeing"

    def update(
        self,
        dt: float,
        food_pellets: List[FoodPellet],
        threats: List[Point2D],
    ) -> Point2D:
        """
        Evaluates perception sensors and applies behavioral arbitration.
        Returns current steering force vector.
        """
        # Deplete energy over time
        self.energy = max(0.0, self.energy - dt * 2.5)

        # 1. Threat avoidance takes highest priority
        for threat in threats:
            d = math.hypot(threat.x - self.position.x, threat.y - self.position.y)
            if d < self.config.perception_radius * 0.7:
                self.state = "fleeing"
                return SteeringBehaviors.flee(
                    self.position, self.velocity, threat, self.config.max_speed * 1.4, self.config.max_force * 1.5
                )

        # 2. Seek nearest food if hungry (energy < 80)
        nearest_food: Optional[FoodPellet] = None
        min_dist = float("inf")

        if self.energy < 80.0:
            for pellet in food_pellets:
                if pellet.consumed:
                    continue
                d = math.hypot(pellet.position.x - self.position.x, pellet.position.y - self.position.y)
                if d < self.config.perception_radius and d < min_dist:
                    min_dist = d
                    nearest_food = pellet

        if nearest_food is not None:
            self.state = "seeking_food"
            # Eat food if close
            if min_dist < 20.0:
                nearest_food.consumed = True
                self.energy = min(self.max_energy, self.energy + nearest_food.energy_value)
                self.state = "satisfied"
            return SteeringBehaviors.seek(
                self.position, self.velocity, nearest_food.position, self.config.max_speed, self.config.max_force
            )

        # 3. Default: Wander smoothly
        self.state = "wandering"
        steer, self.wander_angle = SteeringBehaviors.wander(
            self.position, self.velocity, self.wander_angle, self.config
        )
        return steer


class SandboxEcosystem:
    """Manages multi-creature interactions, food spawning, and ecological dynamics."""

    def __init__(self, world_width: float = 1200.0, world_height: float = 800.0):
        self.world_width = world_width
        self.world_height = world_height
        self.creatures: Dict[str, CreatureAgent] = {}
        self.food_pellets: List[FoodPellet] = []
        self._pellet_counter: int = 0

    def add_creature(self, creature_id: str, pos: Point2D, config: SteeringConfig) -> CreatureAgent:
        agent = CreatureAgent(creature_id, pos, config)
        self.creatures[creature_id] = agent
        return agent

    def spawn_food(self, pos: Optional[Point2D] = None) -> FoodPellet:
        self._pellet_counter += 1
        p = pos or Point2D(
            x=random.uniform(100, self.world_width - 100),
            y=random.uniform(self.world_height - 300, self.world_height - 100),
        )
        pellet = FoodPellet(f"food_{self._pellet_counter}", p)
        self.food_pellets.append(pellet)
        return pellet

    def step(self, dt: float) -> Dict[str, Point2D]:
        """Steps ecosystem forward and returns steering forces for all active creatures."""
        forces: Dict[str, Point2D] = {}
        # Clean up consumed food
        self.food_pellets = [p for p in self.food_pellets if not p.consumed]

        # Auto spawn food if scarce
        if len(self.food_pellets) < 4:
            self.spawn_food()

        for c_id, agent in self.creatures.items():
            force = agent.update(dt, self.food_pellets, threats=[])
            forces[c_id] = force

        return forces
