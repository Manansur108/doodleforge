"""
Central Pattern Generator (CPG) and Procedural Gait Engine.
Produces coordinated oscillatory trajectories for articulated joints,
manages gait phase offsets, and drives real-time PD motor torque controllers.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional
from doodleforge.models import GaitType, JointDef, LocomotionConfig, MotorDef


class GaitController:
    """
    Central Pattern Generator (CPG) synthesizing coordinated motor angles
    and torque commands for all joints of a creature.
    """

    def __init__(self, config: LocomotionConfig):
        self.config = config
        self.time: float = 0.0
        self.kp: float = 120.0  # Proportional gain for PD motor
        self.kd: float = 8.0    # Derivative gain for damping

    def set_frequency(self, freq: float) -> None:
        self.config.base_frequency = max(0.1, freq)

    def set_power(self, power: float) -> None:
        self.config.drive_power = max(0.0, min(3.0, power))

    def evaluate_target_angle(self, joint: JointDef, t: float) -> float:
        """
        Calculates the instantaneous target angle for a joint motor at time t.
        Applies asymmetric stance-swing kinematics if configured.
        """
        motor = joint.motor
        if not motor or not motor.enabled:
            return 0.0

        if motor.waveform == "constant":
            # For wheels, target is continuous rotation
            return motor.speed * t

        # Retrieve phase and amplitude overrides from config
        joint_id = joint.id
        phase_offset = self.config.phase_offsets.get(joint_id, motor.phase)
        amplitude = self.config.amplitudes.get(joint_id, motor.amplitude) * self.config.drive_power
        offset = self.config.offsets.get(joint_id, motor.offset)
        freq = self.config.base_frequency

        omega = 2.0 * math.pi * freq
        cycle_angle = (omega * t + phase_offset) % (2.0 * math.pi)

        if motor.waveform == "triangle":
            # Linear ramp up/down
            tri = 2.0 * abs(2.0 * (cycle_angle / (2.0 * math.pi) - math.floor(cycle_angle / (2.0 * math.pi) + 0.5))) - 1.0
            target = offset + amplitude * tri
        else:
            # Asymmetric stance-swing sinusoidal profile:
            # Slower stance phase (ground push), quicker swing phase (recovery)
            sine_val = math.sin(cycle_angle)
            if sine_val < 0:
                # Swing phase
                sine_val *= 1.15
            target = offset + amplitude * sine_val

        # Clamp within joint angle limits if defined
        if joint.min_angle is not None:
            target = max(joint.min_angle, target)
        if joint.max_angle is not None:
            target = min(joint.max_angle, target)

        return target

    def compute_motor_torque(
        self,
        joint: JointDef,
        current_angle: float,
        current_angular_velocity: float,
        t: float,
    ) -> float:
        """
        Computes the corrective torque output via PD control law:
        tau = Kp * (theta_target - theta_current) - Kd * angular_velocity
        """
        motor = joint.motor
        if not motor or not motor.enabled:
            return 0.0

        if motor.waveform == "constant":
            # Velocity control for continuous drive wheels
            target_vel = motor.speed * self.config.drive_power
            vel_err = target_vel - current_angular_velocity
            torque = self.kp * 0.3 * vel_err
            return max(-motor.max_torque, min(motor.max_torque, torque))

        target_angle = self.evaluate_target_angle(joint, t)
        angle_err = target_angle - current_angle
        torque = self.kp * angle_err - self.kd * current_angular_velocity

        max_t = motor.max_torque * self.config.drive_power
        return max(-max_t, min(max_t, torque))


def get_default_gait_phases(gait_type: GaitType, joint_ids: List[str]) -> Dict[str, float]:
    """
    Returns reference phase offsets for standard biological locomotion gaits.
    """
    n = len(joint_ids)
    if n == 0:
        return {}

    phases: Dict[str, float] = {}

    if gait_type == GaitType.BIPED_STRIDE:
        # Alternating left and right stride
        for i, j_id in enumerate(joint_ids):
            phases[j_id] = 0.0 if (i % 2 == 0) else math.pi

    elif gait_type == GaitType.QUADRUPED_TROT:
        # Diagonal synchronization (FL+RR in phase 0, FR+RL in phase pi)
        for i, j_id in enumerate(joint_ids):
            phases[j_id] = 0.0 if (i % 2 == 0) else math.pi

    elif gait_type == GaitType.QUADRUPED_GALLOP:
        # Front pair vs rear pair with 90-degree phase delay
        for i, j_id in enumerate(joint_ids):
            if i < n // 2:
                phases[j_id] = 0.0 if i == 0 else 0.25 * math.pi
            else:
                phases[j_id] = math.pi if i == n // 2 else 1.25 * math.pi

    elif gait_type == GaitType.HEXAPOD_RIPPLE:
        # Metachronal wave progression across 6 legs
        for i, j_id in enumerate(joint_ids):
            phases[j_id] = (2.0 * math.pi * i) / max(n, 1)

    elif gait_type == GaitType.AVIAN_FLAP:
        # Wings flap synchronously downwards together
        for i, j_id in enumerate(joint_ids):
            phases[j_id] = 0.0

    elif gait_type == GaitType.SERPENTINE_WAVE:
        # Undulating travelling wave from head to tail
        phase_step = math.pi * 0.4
        for i, j_id in enumerate(joint_ids):
            phases[j_id] = i * phase_step

    else:
        for i, j_id in enumerate(joint_ids):
            phases[j_id] = (math.pi * i) / max(n, 1)

    return phases
