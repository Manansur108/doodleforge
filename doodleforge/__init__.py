"""
DoodleForge: Real-Time Sketch-to-Physics Generative Creature Sandbox.

An interactive generative framework where freehand sketches of creatures,
monsters, and contraptions are parsed into rigged 2D physical bodies with joints,
springs, and procedural locomotion.
"""

__version__ = "0.1.0"
__author__ = "Manan Sur"

from doodleforge.models import (
    CreatureBlueprint,
    GaitType,
    JointDef,
    JointType,
    LocomotionConfig,
    PartType,
    Point2D,
    RigidBodyDef,
    SteeringConfig,
    Stroke,
)

__all__ = [
    "CreatureBlueprint",
    "GaitType",
    "JointDef",
    "JointType",
    "LocomotionConfig",
    "PartType",
    "Point2D",
    "RigidBodyDef",
    "SteeringConfig",
    "Stroke",
]
