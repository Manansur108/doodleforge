"""
Tests for doodleforge.locomotion module.
"""

import math
import pytest
from doodleforge.locomotion import GaitController, get_default_gait_phases
from doodleforge.models import (
    GaitType,
    JointDef,
    JointType,
    LocomotionConfig,
    MotorDef,
    Point2D,
)


def test_gait_controller_target_angle():
    joint = JointDef(
        id="j_test",
        joint_type=JointType.REVOLUTE,
        body_a_id="b1",
        body_b_id="b2",
        anchor_a=Point2D(x=0, y=0),
        anchor_b=Point2D(x=0, y=0),
        world_anchor=Point2D(x=0, y=0),
        min_angle=-1.0,
        max_angle=1.0,
        motor=MotorDef(
            enabled=True,
            amplitude=0.5,
            frequency=1.0,
            phase=0.0,
            offset=0.0,
            waveform="sine",
        ),
    )
    config = LocomotionConfig(base_frequency=1.0, drive_power=1.0)
    controller = GaitController(config)

    # At t=0, target angle is 0
    angle_0 = controller.evaluate_target_angle(joint, 0.0)
    assert math.isclose(angle_0, 0.0, abs_tol=1e-3)

    # At t=0.25 (quarter period = pi/2 phase), sin is 1.0 -> target angle is amplitude
    angle_quarter = controller.evaluate_target_angle(joint, 0.25)
    assert math.isclose(angle_quarter, 0.5, abs_tol=1e-3)


def test_gait_controller_motor_torque_pd():
    joint = JointDef(
        id="j_test",
        joint_type=JointType.REVOLUTE,
        body_a_id="b1",
        body_b_id="b2",
        anchor_a=Point2D(x=0, y=0),
        anchor_b=Point2D(x=0, y=0),
        world_anchor=Point2D(x=0, y=0),
        motor=MotorDef(
            enabled=True,
            amplitude=0.5,
            frequency=1.0,
            phase=0.0,
            max_torque=100.0,
        ),
    )
    config = LocomotionConfig(base_frequency=1.0)
    controller = GaitController(config)

    # If target is 0.5 and current is 0.0 (and 0 velocity), torque should be positive
    torque = controller.compute_motor_torque(joint, current_angle=0.0, current_angular_velocity=0.0, t=0.25)
    assert torque > 0.0
    assert torque <= joint.motor.max_torque


def test_default_gait_phases_profiles():
    # Biped
    biped_phases = get_default_gait_phases(GaitType.BIPED_STRIDE, ["j1", "j2"])
    assert biped_phases["j1"] == 0.0
    assert biped_phases["j2"] == math.pi

    # Quadruped Trot (alternate pairs)
    quad_phases = get_default_gait_phases(GaitType.QUADRUPED_TROT, ["j1", "j2", "j3", "j4"])
    assert quad_phases["j1"] == 0.0
    assert quad_phases["j2"] == math.pi
    assert quad_phases["j3"] == 0.0
    assert quad_phases["j4"] == math.pi

    # Hexapod Ripple
    hex_phases = get_default_gait_phases(GaitType.HEXAPOD_RIPPLE, [f"j{i}" for i in range(6)])
    assert len(hex_phases) == 6
    assert hex_phases["j0"] == 0.0
