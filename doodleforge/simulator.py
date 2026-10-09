"""
Pure-Python 2D Rigid-Body Physics Simulator for Headless Creature Locomotion Benchmarking.
Implements symplectic Euler integration, revolute & distance joint constraint relaxation,
ground contact collision with Coulomb friction, and telemetry evaluation.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple
from doodleforge.locomotion import GaitController
from doodleforge.models import (
    CreatureBlueprint,
    JointDef,
    Point2D,
    RigidBodyDef,
    SimulateRequest,
    SimulateResponse,
    SimulationFrame,
)


class SimBodyState:
    """Internal physics state for a rigid body in the simulation."""

    def __init__(self, defn: RigidBodyDef):
        self.defn = defn
        self.id = defn.id
        self.x = defn.position.x
        self.y = defn.position.y
        self.vx = 0.0
        self.vy = 0.0
        self.angle = defn.angle
        self.angular_vel = 0.0

        # Calculate mass and moment of inertia
        width = max(defn.width, 10.0)
        height = max(defn.height, 10.0)
        area = width * height
        self.mass = max(0.5, (area * 0.001) * defn.density)
        self.inv_mass = 1.0 / self.mass
        # Box moment of inertia: I = m * (w^2 + h^2) / 12
        self.inertia = max(1.0, (self.mass * (width * width + height * height)) / 12.0)
        self.inv_inertia = 1.0 / self.inertia

    def get_world_point(self, local_offset: Point2D) -> Tuple[float, float]:
        """Transforms a local body offset into world coordinates."""
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        wx = self.x + (local_offset.x * cos_a - local_offset.y * sin_a)
        wy = self.y + (local_offset.x * sin_a + local_offset.y * cos_a)
        return (wx, wy)

    def get_bottom_y(self) -> float:
        """Estimates the lowest point of the body."""
        half_h = self.defn.height * 0.5
        half_w = self.defn.width * 0.5
        # Conservative bounding radius
        r = math.hypot(half_w, half_h)
        return self.y + r


class PhysicsSandbox:
    """Headless 2D physics simulation environment."""

    def __init__(
        self,
        blueprint: CreatureBlueprint,
        gravity_y: float = 980.0,
        ground_y: float = 550.0,
    ):
        self.blueprint = blueprint
        self.gravity_y = gravity_y
        self.ground_y = ground_y
        self.gait_controller = GaitController(blueprint.locomotion)

        # Initialize body states
        self.bodies: Dict[str, SimBodyState] = {
            b.id: SimBodyState(b) for b in blueprint.bodies
        }
        self.joints: List[JointDef] = blueprint.joints
        self.time: float = 0.0

    def step(self, dt: float) -> None:
        """Advances physics simulation by dt seconds."""
        # 1. Apply gravity & motor actuation
        for body in self.bodies.values():
            body.vy += self.gravity_y * dt

        # 2. Joint Motor Torques & Angle Limits
        for joint in self.joints:
            b_a = self.bodies.get(joint.body_a_id)
            b_b = self.bodies.get(joint.body_b_id)
            if not b_a or not b_b:
                continue

            rel_angle = b_b.angle - b_a.angle
            rel_ang_vel = b_b.angular_vel - b_a.angular_vel

            # Compute PD torque
            torque = self.gait_controller.compute_motor_torque(
                joint, rel_angle, rel_ang_vel, self.time
            )

            # Apply action-reaction torque
            b_b.angular_vel += (torque * b_b.inv_inertia) * dt
            b_a.angular_vel -= (torque * b_a.inv_inertia) * dt

        # 3. Integrate velocities to positions (Semi-implicit Euler)
        for body in self.bodies.values():
            # Linear damping
            body.vx *= 0.999
            body.vy *= 0.999
            body.angular_vel *= 0.995

            body.x += body.vx * dt
            body.y += body.vy * dt
            body.angle += body.angular_vel * dt

        # 4. Solve Joint Pin Position Constraints (relaxation iterations)
        for _ in range(4):
            for joint in self.joints:
                b_a = self.bodies.get(joint.body_a_id)
                b_b = self.bodies.get(joint.body_b_id)
                if not b_a or not b_b:
                    continue

                w_ax, w_ay = b_a.get_world_point(joint.anchor_a)
                w_bx, w_by = b_b.get_world_point(joint.anchor_b)

                err_x = w_bx - w_ax
                err_y = w_by - w_ay
                dist = math.hypot(err_x, err_y)

                if dist > 0.01:
                    total_inv_mass = b_a.inv_mass + b_b.inv_mass
                    if total_inv_mass > 1e-6:
                        corr_ratio_a = b_a.inv_mass / total_inv_mass
                        corr_ratio_b = b_b.inv_mass / total_inv_mass

                        b_a.x += err_x * corr_ratio_a * 0.5
                        b_a.y += err_y * corr_ratio_a * 0.5
                        b_b.x -= err_x * corr_ratio_b * 0.5
                        b_b.y -= err_y * corr_ratio_b * 0.5

                        # Velocity correction
                        b_a.vx += (err_x / dt) * corr_ratio_a * 0.2
                        b_a.vy += (err_y / dt) * corr_ratio_a * 0.2
                        b_b.vx -= (err_x / dt) * corr_ratio_b * 0.2
                        b_b.vy -= (err_y / dt) * corr_ratio_b * 0.2

        # 5. Ground contact and Coulomb friction solver
        for body in self.bodies.values():
            half_h = body.defn.height * 0.5
            bottom = body.y + half_h

            if bottom > self.ground_y:
                penetration = bottom - self.ground_y
                # Position correction
                body.y -= penetration

                # Restitution and normal impulse
                if body.vy > 0:
                    body.vy = -body.vy * body.defn.restitution
                    if abs(body.vy) < 20.0:
                        body.vy = 0.0

                # Tangential friction traction (enables walking!)
                friction = body.defn.friction
                body.vx *= max(0.0, 1.0 - friction * 0.4)

                # Wheel rolling propulsion
                if body.defn.part_type.value == "wheel":
                    body.vx += body.angular_vel * (body.defn.width * 0.5) * 0.15

        self.time += dt


def run_headless_simulation(request: SimulateRequest) -> SimulateResponse:
    """
    Simulates creature locomotion over a defined duration and returns
    locomotion displacement, speed, stability, and trajectory telemetry.
    """
    blueprint = request.blueprint
    sandbox = PhysicsSandbox(blueprint, gravity_y=request.gravity_y)
    dt = request.time_step
    steps = int(request.duration_seconds / dt)

    torso_body = sandbox.bodies.get(blueprint.torso_id)
    if not torso_body:
        torso_body = next(iter(sandbox.bodies.values()), None)

    if not torso_body:
        return SimulateResponse(
            blueprint_id=blueprint.id,
            distance_traveled=0.0,
            avg_speed=0.0,
            stability_score=0.0,
            fell_over=True,
            frames=[],
            summary="Simulation failed: No valid rigid bodies found.",
        )

    initial_x = torso_body.x
    initial_y = torso_body.y
    frames: List[SimulationFrame] = []
    sample_interval = max(1, steps // 40)

    fell_over = False
    max_tilt = 0.0

    for step_i in range(steps):
        sandbox.step(dt)

        tilt = abs(torso_body.angle)
        if tilt > max_tilt:
            max_tilt = tilt
        if tilt > math.pi * 0.55:  # more than 100 degrees tilt
            fell_over = True

        if step_i % sample_interval == 0:
            total_energy = 0.5 * torso_body.mass * (torso_body.vx**2 + torso_body.vy**2)
            frames.append(
                SimulationFrame(
                    time=round(sandbox.time, 3),
                    torso_position=Point2D(x=round(torso_body.x, 2), y=round(torso_body.y, 2)),
                    torso_velocity=Point2D(x=round(torso_body.vx, 2), y=round(torso_body.vy, 2)),
                    torso_angle=round(torso_body.angle, 3),
                    total_energy=round(total_energy, 2),
                )
            )

    final_x = torso_body.x
    distance_traveled = final_x - initial_x
    avg_speed = distance_traveled / request.duration_seconds

    # Stability score: 1.0 is upright and smooth, drops if high tilt or falling
    stability = max(0.0, 1.0 - (max_tilt / math.pi) * 0.8)
    if fell_over:
        stability *= 0.3

    summary = (
        f"Simulated {request.duration_seconds:.1f}s: Traveled {distance_traveled:.1f}px "
        f"at {avg_speed:.1f}px/s. Stability: {stability:.2f}. "
        f"{'Creature remained upright.' if not fell_over else 'Creature lost balance.'}"
    )

    return SimulateResponse(
        blueprint_id=blueprint.id,
        distance_traveled=round(distance_traveled, 2),
        avg_speed=round(avg_speed, 2),
        stability_score=round(stability, 3),
        fell_over=fell_over,
        frames=frames,
        summary=summary,
    )
