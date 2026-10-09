"""
Data models and schemas for DoodleForge.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Point2D(BaseModel):
    """2D coordinate representation."""
    x: float
    y: float

    def to_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)

    @classmethod
    def from_tuple(cls, t: tuple[float, float]) -> Point2D:
        return cls(x=float(t[0]), y=float(t[1]))


class Stroke(BaseModel):
    """A single freehand stroke drawn by the user."""
    points: List[Point2D]
    color: Optional[str] = "#00e5ff"
    stroke_width: Optional[float] = 4.0
    closed: Optional[bool] = False
    timestamp: Optional[float] = None
    part_hint: Optional[str] = None


class PartType(str, Enum):
    """Anatomical part classification."""
    TORSO = "torso"
    HEAD = "head"
    LEG = "leg"
    ARM = "arm"
    WING = "wing"
    TAIL = "tail"
    WHEEL = "wheel"
    FIN = "fin"


class JointType(str, Enum):
    """Mechanical joint constraint type."""
    REVOLUTE = "revolute"    # Pin/hinge joint with optional limits and motor
    DISTANCE = "distance"    # Spring/rod joint
    WELD = "weld"            # Rigid fixed attachment
    PRISMATIC = "prismatic"  # Linear slider
    WHEEL_AXLE = "wheel_axle"# Continuous rotational motor axle


class MotorDef(BaseModel):
    """Motor actuation specification for an articulated joint."""
    enabled: bool = True
    speed: float = 0.0              # Continuous rotation speed (rad/s)
    max_torque: float = 120.0       # Maximum force/torque output
    amplitude: float = 0.6          # Oscillation amplitude (radians)
    frequency: float = 1.5          # Oscillation frequency (Hz)
    phase: float = 0.0              # Phase offset (radians)
    offset: float = 0.0             # Neutral target angle offset (radians)
    waveform: str = "sine"          # "sine", "triangle", "constant"


class JointDef(BaseModel):
    """Joint constraint between two rigid bodies."""
    id: str
    joint_type: JointType = JointType.REVOLUTE
    body_a_id: str
    body_b_id: str
    anchor_a: Point2D               # Local offset or anchor in Body A frame
    anchor_b: Point2D               # Local offset or anchor in Body B frame
    world_anchor: Point2D           # World coordinates of pivot point
    stiffness: float = 0.95         # Constraint rigidity (0.0 to 1.0)
    damping: float = 0.08           # Damping coefficient
    min_angle: Optional[float] = None # Lower angular limit (radians)
    max_angle: Optional[float] = None # Upper angular limit (radians)
    motor: Optional[MotorDef] = None


class RigidBodyDef(BaseModel):
    """Physical rigid body representing an anatomical part."""
    id: str
    name: str
    part_type: PartType
    shape: str = "polygon"          # "polygon", "box", "circle", "capsule"
    position: Point2D               # Center of mass in world coords
    angle: float = 0.0              # Orientation angle (radians)
    width: float = 30.0
    height: float = 30.0
    radius: Optional[float] = None
    vertices: List[Point2D] = Field(default_factory=list) # Local or world contour
    density: float = 1.0
    friction: float = 0.8
    restitution: float = 0.1
    color: str = "#00e5ff"
    stroke_index: int = 0
    parent_id: Optional[str] = None
    collision_group: int = 1


class GaitType(str, Enum):
    """Locomotion coordination profiles."""
    BIPED_STRIDE = "biped_stride"
    QUADRUPED_TROT = "quadruped_trot"
    QUADRUPED_GALLOP = "quadruped_gallop"
    HEXAPOD_RIPPLE = "hexapod_ripple"
    AVIAN_FLAP = "avian_flap"
    SERPENTINE_WAVE = "serpentine_wave"
    WHEELED_DRIVE = "wheeled_drive"
    CUSTOM = "custom"


class LocomotionConfig(BaseModel):
    """Central Pattern Generator (CPG) locomotion setup."""
    gait_type: GaitType = GaitType.QUADRUPED_TROT
    base_frequency: float = 1.5
    drive_power: float = 1.0
    phase_offsets: Dict[str, float] = Field(default_factory=dict) # joint_id -> phase
    amplitudes: Dict[str, float] = Field(default_factory=dict)    # joint_id -> amplitude
    offsets: Dict[str, float] = Field(default_factory=dict)       # joint_id -> angle offset


class SteeringConfig(BaseModel):
    """Autonomous behavioral steering configuration."""
    behavior: str = "wander"        # "wander", "seek", "flee", "flock"
    max_speed: float = 4.0
    max_force: float = 0.5
    wander_radius: float = 60.0
    wander_distance: float = 80.0
    perception_radius: float = 250.0


class CreatureBlueprint(BaseModel):
    """Complete physical specification of a generative rigged creature."""
    id: str
    name: str
    bodies: List[RigidBodyDef]
    joints: List[JointDef]
    torso_id: str
    locomotion: LocomotionConfig
    steering: SteeringConfig = Field(default_factory=SteeringConfig)
    raw_strokes: Optional[List[Stroke]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# API Request / Response schemas

class RigRequest(BaseModel):
    """Request payload to analyze strokes and generate rigged creature."""
    strokes: List[Stroke]
    name: Optional[str] = "Doodle-Creature"
    simplify_tolerance: float = 3.0
    auto_gait: bool = True


class SimulateRequest(BaseModel):
    """Request payload to simulate creature locomotion."""
    blueprint: CreatureBlueprint
    duration_seconds: float = 3.0
    time_step: float = 1.0 / 60.0
    gravity_y: float = 980.0        # px/s^2


class SimulationFrame(BaseModel):
    """Telemetry snapshot at a specific point in time."""
    time: float
    torso_position: Point2D
    torso_velocity: Point2D
    torso_angle: float
    total_energy: float


class SimulateResponse(BaseModel):
    """Results from headless physics simulation."""
    blueprint_id: str
    distance_traveled: float
    avg_speed: float
    stability_score: float
    fell_over: bool
    frames: List[SimulationFrame]
    summary: str


class OptimizeGaitRequest(BaseModel):
    """Request to evolve/optimize creature gait parameters."""
    blueprint: CreatureBlueprint
    generations: int = 12
    population_size: int = 8
    simulation_duration: float = 2.0


class OptimizeGaitResponse(BaseModel):
    """Results from evolutionary gait optimization."""
    optimized_blueprint: CreatureBlueprint
    initial_speed: float
    final_speed: float
    improvement_pct: float
    fitness_history: List[float]
