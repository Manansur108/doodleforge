"""
Tests for doodleforge.rigging module.
"""

import pytest
from doodleforge.models import GaitType, JointType, PartType, Point2D, Stroke
from doodleforge.rigging import rig_strokes


def test_rig_strokes_biped():
    torso = Stroke(
        points=[
            Point2D(x=100, y=100),
            Point2D(x=200, y=100),
            Point2D(x=200, y=150),
            Point2D(x=100, y=150),
            Point2D(x=100, y=100),
        ],
        closed=True,
    )
    leg_l = Stroke(points=[Point2D(x=120, y=150), Point2D(x=120, y=220)])
    leg_r = Stroke(points=[Point2D(x=180, y=150), Point2D(x=180, y=220)])

    bp = rig_strokes([torso, leg_l, leg_r], creature_name="Bipedal-Runner")

    assert bp.name == "Bipedal-Runner"
    assert bp.torso_id.startswith("body_torso")
    assert len(bp.bodies) == 3
    assert len(bp.joints) == 2
    assert bp.locomotion.gait_type == GaitType.BIPED_STRIDE

    # Check that legs have motorized revolute joints
    for joint in bp.joints:
        assert joint.joint_type == JointType.REVOLUTE
        assert joint.motor is not None
        assert joint.motor.enabled is True


def test_rig_strokes_wheeled():
    torso = Stroke(
        points=[
            Point2D(x=100, y=100),
            Point2D(x=200, y=100),
            Point2D(x=200, y=140),
            Point2D(x=100, y=140),
            Point2D(x=100, y=100),
        ],
        closed=True,
    )
    wheel = Stroke(
        points=[
            Point2D(x=140, y=150),
            Point2D(x=160, y=150),
            Point2D(x=160, y=170),
            Point2D(x=140, y=170),
            Point2D(x=140, y=150),
        ],
        closed=True,
    )

    bp = rig_strokes([torso, wheel], creature_name="Monocycle")
    assert bp.locomotion.gait_type == GaitType.WHEELED_DRIVE

    wheel_joints = [j for j in bp.joints if j.joint_type == JointType.WHEEL_AXLE]
    assert len(wheel_joints) == 1
    assert wheel_joints[0].motor.waveform == "constant"


def test_collision_filtering_and_angular_limits():
    torso = Stroke(
        points=[Point2D(x=0, y=0), Point2D(x=50, y=0), Point2D(x=50, y=30), Point2D(x=0, y=30)],
        closed=True,
    )
    leg = Stroke(points=[Point2D(x=25, y=30), Point2D(x=25, y=80)])

    bp = rig_strokes([torso, leg])
    for body in bp.bodies:
        # Check collision group is set to avoid limb jamming
        assert body.collision_group is not None

    for joint in bp.joints:
        if joint.joint_type == JointType.REVOLUTE:
            assert joint.min_angle is not None
            assert joint.max_angle is not None
            assert joint.min_angle <= joint.max_angle
