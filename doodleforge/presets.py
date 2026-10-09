"""
Preset creature blueprints and sketch templates for DoodleForge.
Provides pre-configured creatures across multiple locomotion paradigms
(Biped, Quadruped, Hexapod, Flapper, Serpentine, Wheeled Rover).
"""

from __future__ import annotations

import math
from typing import Dict, List
from doodleforge.models import (
    CreatureBlueprint,
    GaitType,
    JointDef,
    JointType,
    LocomotionConfig,
    MotorDef,
    PartType,
    Point2D,
    RigidBodyDef,
    SteeringConfig,
    Stroke,
)


def get_cyber_cheetah() -> CreatureBlueprint:
    """Fast-running quadruped with 4 legs and counterbalance tail."""
    torso = RigidBodyDef(
        id="cheetah_torso",
        name="Cheetah Torso",
        part_type=PartType.TORSO,
        shape="box",
        position=Point2D(x=400, y=300),
        width=110,
        height=35,
        density=1.5,
        friction=0.5,
        restitution=0.05,
        color="#00e5ff",
        collision_group=-1,
    )
    head = RigidBodyDef(
        id="cheetah_head",
        name="Cheetah Head",
        part_type=PartType.HEAD,
        shape="box",
        position=Point2D(x=475, y=280),
        width=30,
        height=25,
        density=0.8,
        color="#e040fb",
        parent_id="cheetah_torso",
        collision_group=-1,
    )
    tail = RigidBodyDef(
        id="cheetah_tail",
        name="Cheetah Tail",
        part_type=PartType.TAIL,
        shape="box",
        position=Point2D(x=325, y=290),
        width=50,
        height=12,
        density=0.5,
        color="#ff9100",
        parent_id="cheetah_torso",
        collision_group=-1,
    )

    # 4 legs (FL, FR, RL, RR)
    leg_fl = RigidBodyDef(
        id="cheetah_leg_fl",
        name="Front-Left Leg",
        part_type=PartType.LEG,
        shape="box",
        position=Point2D(x=445, y=350),
        width=14,
        height=65,
        density=0.9,
        friction=0.95,
        color="#00e676",
        parent_id="cheetah_torso",
        collision_group=-1,
    )
    leg_fr = RigidBodyDef(
        id="cheetah_leg_fr",
        name="Front-Right Leg",
        part_type=PartType.LEG,
        shape="box",
        position=Point2D(x=435, y=350),
        width=14,
        height=65,
        density=0.9,
        friction=0.95,
        color="#00c853",
        parent_id="cheetah_torso",
        collision_group=-1,
    )
    leg_rl = RigidBodyDef(
        id="cheetah_leg_rl",
        name="Rear-Left Leg",
        part_type=PartType.LEG,
        shape="box",
        position=Point2D(x=365, y=350),
        width=14,
        height=65,
        density=0.9,
        friction=0.95,
        color="#00e676",
        parent_id="cheetah_torso",
        collision_group=-1,
    )
    leg_rr = RigidBodyDef(
        id="cheetah_leg_rr",
        name="Rear-Right Leg",
        part_type=PartType.LEG,
        shape="box",
        position=Point2D(x=355, y=350),
        width=14,
        height=65,
        density=0.9,
        friction=0.95,
        color="#00c853",
        parent_id="cheetah_torso",
        collision_group=-1,
    )

    bodies = [torso, head, tail, leg_fl, leg_fr, leg_rl, leg_rr]

    # Joints
    j_head = JointDef(
        id="j_cheetah_head",
        body_a_id="cheetah_torso",
        body_b_id="cheetah_head",
        anchor_a=Point2D(x=55, y=-10),
        anchor_b=Point2D(x=-15, y=10),
        world_anchor=Point2D(x=455, y=290),
        min_angle=-0.3,
        max_angle=0.3,
        stiffness=0.9,
    )
    j_tail = JointDef(
        id="j_cheetah_tail",
        body_a_id="cheetah_torso",
        body_b_id="cheetah_tail",
        anchor_a=Point2D(x=-55, y=-5),
        anchor_b=Point2D(x=25, y=0),
        world_anchor=Point2D(x=345, y=295),
        min_angle=-0.6,
        max_angle=0.6,
        motor=MotorDef(enabled=True, amplitude=0.3, frequency=1.8, phase=math.pi * 0.5),
    )

    # Trot Gait phases: FL=0, FR=pi, RL=pi, RR=0
    j_fl = JointDef(
        id="j_cheetah_fl",
        body_a_id="cheetah_torso",
        body_b_id="cheetah_leg_fl",
        anchor_a=Point2D(x=45, y=15),
        anchor_b=Point2D(x=0, y=-30),
        world_anchor=Point2D(x=445, y=315),
        min_angle=-0.7,
        max_angle=0.7,
        motor=MotorDef(enabled=True, amplitude=0.55, frequency=1.8, phase=0.0),
    )
    j_fr = JointDef(
        id="j_cheetah_fr",
        body_a_id="cheetah_torso",
        body_b_id="cheetah_leg_fr",
        anchor_a=Point2D(x=35, y=15),
        anchor_b=Point2D(x=0, y=-30),
        world_anchor=Point2D(x=435, y=315),
        min_angle=-0.7,
        max_angle=0.7,
        motor=MotorDef(enabled=True, amplitude=0.55, frequency=1.8, phase=math.pi),
    )
    j_rl = JointDef(
        id="j_cheetah_rl",
        body_a_id="cheetah_torso",
        body_b_id="cheetah_leg_rl",
        anchor_a=Point2D(x=-35, y=15),
        anchor_b=Point2D(x=0, y=-30),
        world_anchor=Point2D(x=365, y=315),
        min_angle=-0.7,
        max_angle=0.7,
        motor=MotorDef(enabled=True, amplitude=0.55, frequency=1.8, phase=math.pi),
    )
    j_rr = JointDef(
        id="j_cheetah_rr",
        body_a_id="cheetah_torso",
        body_b_id="cheetah_leg_rr",
        anchor_a=Point2D(x=-45, y=15),
        anchor_b=Point2D(x=0, y=-30),
        world_anchor=Point2D(x=355, y=315),
        min_angle=-0.7,
        max_angle=0.7,
        motor=MotorDef(enabled=True, amplitude=0.55, frequency=1.8, phase=0.0),
    )

    joints = [j_head, j_tail, j_fl, j_fr, j_rl, j_rr]

    locomotion = LocomotionConfig(
        gait_type=GaitType.QUADRUPED_TROT,
        base_frequency=1.8,
        phase_offsets={
            "j_cheetah_fl": 0.0,
            "j_cheetah_fr": math.pi,
            "j_cheetah_rl": math.pi,
            "j_cheetah_rr": 0.0,
        },
        amplitudes={
            "j_cheetah_fl": 0.55,
            "j_cheetah_fr": 0.55,
            "j_cheetah_rl": 0.55,
            "j_cheetah_rr": 0.55,
        },
    )

    return CreatureBlueprint(
        id="preset_cyber_cheetah",
        name="Cyber-Cheetah",
        bodies=bodies,
        joints=joints,
        torso_id=torso.id,
        locomotion=locomotion,
        steering=SteeringConfig(max_speed=5.5),
        metadata={"category": "Quadruped", "agility": "High"},
    )


def get_bipedal_strider() -> CreatureBlueprint:
    """Two-legged runner with tall articulated limbs and alternating stride."""
    torso = RigidBodyDef(
        id="strider_torso",
        name="Strider Core",
        part_type=PartType.TORSO,
        shape="box",
        position=Point2D(x=400, y=280),
        width=55,
        height=45,
        density=1.6,
        color="#00e5ff",
        collision_group=-1,
    )
    head = RigidBodyDef(
        id="strider_head",
        name="Sensor Dome",
        part_type=PartType.HEAD,
        shape="box",
        position=Point2D(x=415, y=240),
        width=25,
        height=25,
        density=0.7,
        color="#e040fb",
        parent_id="strider_torso",
        collision_group=-1,
    )
    leg_left = RigidBodyDef(
        id="strider_leg_l",
        name="Left Leg",
        part_type=PartType.LEG,
        shape="box",
        position=Point2D(x=385, y=350),
        width=15,
        height=85,
        density=0.8,
        friction=0.95,
        color="#00e676",
        parent_id="strider_torso",
        collision_group=-1,
    )
    leg_right = RigidBodyDef(
        id="strider_leg_r",
        name="Right Leg",
        part_type=PartType.LEG,
        shape="box",
        position=Point2D(x=415, y=350),
        width=15,
        height=85,
        density=0.8,
        friction=0.95,
        color="#00c853",
        parent_id="strider_torso",
        collision_group=-1,
    )

    j_head = JointDef(
        id="j_strider_head",
        body_a_id="strider_torso",
        body_b_id="strider_head",
        anchor_a=Point2D(x=15, y=-22),
        anchor_b=Point2D(x=0, y=12),
        world_anchor=Point2D(x=415, y=255),
        min_angle=-0.2,
        max_angle=0.2,
    )
    j_leg_l = JointDef(
        id="j_strider_leg_l",
        body_a_id="strider_torso",
        body_b_id="strider_leg_l",
        anchor_a=Point2D(x=-15, y=20),
        anchor_b=Point2D(x=0, y=-40),
        world_anchor=Point2D(x=385, y=305),
        min_angle=-0.75,
        max_angle=0.75,
        motor=MotorDef(enabled=True, amplitude=0.6, frequency=1.4, phase=0.0),
    )
    j_leg_r = JointDef(
        id="j_strider_leg_r",
        body_a_id="strider_torso",
        body_b_id="strider_leg_r",
        anchor_a=Point2D(x=15, y=20),
        anchor_b=Point2D(x=0, y=-40),
        world_anchor=Point2D(x=415, y=305),
        min_angle=-0.75,
        max_angle=0.75,
        motor=MotorDef(enabled=True, amplitude=0.6, frequency=1.4, phase=math.pi),
    )

    return CreatureBlueprint(
        id="preset_bipedal_strider",
        name="Bipedal Strider",
        bodies=[torso, head, leg_left, leg_right],
        joints=[j_head, j_leg_l, j_leg_r],
        torso_id=torso.id,
        locomotion=LocomotionConfig(
            gait_type=GaitType.BIPED_STRIDE,
            base_frequency=1.4,
            phase_offsets={"j_strider_leg_l": 0.0, "j_strider_leg_r": math.pi},
        ),
        steering=SteeringConfig(max_speed=4.0),
    )


def get_hexapod_scuttler() -> CreatureBlueprint:
    """Stable 6-legged insect using tripod ripple locomotion."""
    torso = RigidBodyDef(
        id="hex_torso",
        name="Hexapod Carapace",
        part_type=PartType.TORSO,
        shape="box",
        position=Point2D(x=400, y=300),
        width=120,
        height=30,
        density=1.5,
        color="#00e5ff",
        collision_group=-1,
    )

    bodies = [torso]
    joints = []
    phase_offsets = {}
    amplitudes = {}

    # 6 legs spaced across the chassis
    x_positions = [-50, -30, -10, 10, 30, 50]
    for i, x_offset in enumerate(x_positions):
        leg_id = f"hex_leg_{i}"
        leg = RigidBodyDef(
            id=leg_id,
            name=f"Leg {i+1}",
            part_type=PartType.LEG,
            shape="box",
            position=Point2D(x=400 + x_offset, y=340),
            width=10,
            height=50,
            density=0.7,
            friction=0.9,
            color="#26c6da" if i % 2 == 0 else "#00e676",
            parent_id="hex_torso",
            collision_group=-1,
        )
        bodies.append(leg)

        # Tripod gait: alternate legs between 0 and pi
        phase = 0.0 if (i % 2 == 0) else math.pi
        joint_id = f"j_hex_{i}"
        j = JointDef(
            id=joint_id,
            body_a_id="hex_torso",
            body_b_id=leg_id,
            anchor_a=Point2D(x=x_offset, y=15),
            anchor_b=Point2D(x=0, y=-22),
            world_anchor=Point2D(x=400 + x_offset, y=315),
            min_angle=-0.6,
            max_angle=0.6,
            motor=MotorDef(enabled=True, amplitude=0.45, frequency=2.0, phase=phase),
        )
        joints.append(j)
        phase_offsets[joint_id] = phase
        amplitudes[joint_id] = 0.45

    return CreatureBlueprint(
        id="preset_hexapod_scuttler",
        name="Hexapod Scuttler",
        bodies=bodies,
        joints=joints,
        torso_id=torso.id,
        locomotion=LocomotionConfig(
            gait_type=GaitType.HEXAPOD_RIPPLE,
            base_frequency=2.0,
            phase_offsets=phase_offsets,
            amplitudes=amplitudes,
        ),
        steering=SteeringConfig(max_speed=3.8),
    )


def get_pterodactyl_flapper() -> CreatureBlueprint:
    """Flying avian creature with aerodynamic body and flapping wings."""
    torso = RigidBodyDef(
        id="flapper_torso",
        name="Avian Body",
        part_type=PartType.TORSO,
        shape="box",
        position=Point2D(x=400, y=280),
        width=70,
        height=30,
        density=0.8,
        color="#00e5ff",
        collision_group=-1,
    )
    wing_left = RigidBodyDef(
        id="flapper_wing_l",
        name="Left Wing",
        part_type=PartType.WING,
        shape="box",
        position=Point2D(x=330, y=260),
        width=75,
        height=14,
        density=0.35,
        color="#ff4081",
        parent_id="flapper_torso",
        collision_group=-1,
    )
    wing_right = RigidBodyDef(
        id="flapper_wing_r",
        name="Right Wing",
        part_type=PartType.WING,
        shape="box",
        position=Point2D(x=470, y=260),
        width=75,
        height=14,
        density=0.35,
        color="#ff4081",
        parent_id="flapper_torso",
        collision_group=-1,
    )

    j_wl = JointDef(
        id="j_flapper_wl",
        body_a_id="flapper_torso",
        body_b_id="flapper_wing_l",
        anchor_a=Point2D(x=-35, y=-5),
        anchor_b=Point2D(x=35, y=0),
        world_anchor=Point2D(x=365, y=265),
        min_angle=-0.8,
        max_angle=0.8,
        motor=MotorDef(enabled=True, amplitude=0.7, frequency=2.4, phase=0.0),
    )
    j_wr = JointDef(
        id="j_flapper_wr",
        body_a_id="flapper_torso",
        body_b_id="flapper_wing_r",
        anchor_a=Point2D(x=35, y=-5),
        anchor_b=Point2D(x=-35, y=0),
        world_anchor=Point2D(x=435, y=265),
        min_angle=-0.8,
        max_angle=0.8,
        motor=MotorDef(enabled=True, amplitude=0.7, frequency=2.4, phase=0.0),
    )

    return CreatureBlueprint(
        id="preset_pterodactyl_flapper",
        name="Pterodactyl Flapper",
        bodies=[torso, wing_left, wing_right],
        joints=[j_wl, j_wr],
        torso_id=torso.id,
        locomotion=LocomotionConfig(
            gait_type=GaitType.AVIAN_FLAP,
            base_frequency=2.4,
            phase_offsets={"j_flapper_wl": 0.0, "j_flapper_wr": 0.0},
        ),
        steering=SteeringConfig(max_speed=6.0),
    )


def get_wheeled_rover() -> CreatureBlueprint:
    """Motorized rover vehicle with chassis and dual continuous rotation wheels."""
    chassis = RigidBodyDef(
        id="rover_chassis",
        name="Rover Chassis",
        part_type=PartType.TORSO,
        shape="box",
        position=Point2D(x=400, y=320),
        width=110,
        height=32,
        density=1.8,
        color="#00e5ff",
        collision_group=-1,
    )
    wheel_front = RigidBodyDef(
        id="rover_wheel_f",
        name="Front Wheel",
        part_type=PartType.WHEEL,
        shape="circle",
        position=Point2D(x=445, y=345),
        width=40,
        height=40,
        radius=20,
        density=1.2,
        friction=0.98,
        color="#ffeb3b",
        parent_id="rover_chassis",
        collision_group=1,
    )
    wheel_rear = RigidBodyDef(
        id="rover_wheel_r",
        name="Rear Wheel",
        part_type=PartType.WHEEL,
        shape="circle",
        position=Point2D(x=355, y=345),
        width=40,
        height=40,
        radius=20,
        density=1.2,
        friction=0.98,
        color="#ffeb3b",
        parent_id="rover_chassis",
        collision_group=1,
    )

    j_wf = JointDef(
        id="j_rover_wf",
        joint_type=JointType.WHEEL_AXLE,
        body_a_id="rover_chassis",
        body_b_id="rover_wheel_f",
        anchor_a=Point2D(x=45, y=15),
        anchor_b=Point2D(x=0, y=0),
        world_anchor=Point2D(x=445, y=345),
        motor=MotorDef(enabled=True, speed=8.0, waveform="constant", max_torque=200.0),
    )
    j_wr = JointDef(
        id="j_rover_wr",
        joint_type=JointType.WHEEL_AXLE,
        body_a_id="rover_chassis",
        body_b_id="rover_wheel_r",
        anchor_a=Point2D(x=-45, y=15),
        anchor_b=Point2D(x=0, y=0),
        world_anchor=Point2D(x=355, y=345),
        motor=MotorDef(enabled=True, speed=8.0, waveform="constant", max_torque=200.0),
    )

    return CreatureBlueprint(
        id="preset_wheeled_rover",
        name="Wheeled Dune Rover",
        bodies=[chassis, wheel_front, wheel_rear],
        joints=[j_wf, j_wr],
        torso_id=chassis.id,
        locomotion=LocomotionConfig(gait_type=GaitType.WHEELED_DRIVE, base_frequency=2.0),
        steering=SteeringConfig(max_speed=7.0),
    )


ALL_PRESETS = [
    get_cyber_cheetah,
    get_bipedal_strider,
    get_hexapod_scuttler,
    get_pterodactyl_flapper,
    get_wheeled_rover,
]


def get_preset_by_id(preset_id: str) -> CreatureBlueprint | None:
    """Finds preset blueprint by ID string."""
    for factory in ALL_PRESETS:
        bp = factory()
        if bp.id == preset_id:
            return bp
    return None


def get_all_presets() -> List[CreatureBlueprint]:
    """Returns initialized instances of all presets."""
    return [factory() for factory in ALL_PRESETS]
