"""
Physics Rigging and Constraint Synthesis engine.
Transforms segmented anatomical parts into a fully assembled 2D rigid-body graph
with revolute joints, angular limits, motors, collision groups, and gait configs.
"""

from __future__ import annotations

import math
import uuid
from typing import Dict, List, Optional, Tuple
from doodleforge.geometry import compute_bounding_box, compute_centroid_and_area
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
from doodleforge.segmentation import SegmentedPart, decompose_strokes


def _points_to_local_vertices(points: List[Point2D], center: Point2D) -> List[Point2D]:
    """Converts a contour from world coordinates to local body coordinates relative to center."""
    return [Point2D(x=round(p.x - center.x, 2), y=round(p.y - center.y, 2)) for p in points]


def rig_segmented_parts(
    parts: List[SegmentedPart],
    creature_name: str = "DoodleCreature",
    raw_strokes: Optional[List[Stroke]] = None,
) -> CreatureBlueprint:
    """
    Synthesizes rigid bodies, constraints, motors, and locomotion parameters
    from segmented anatomical parts.
    """
    if not parts:
        # Fallback dummy creature
        torso = RigidBodyDef(
            id="body_torso_0",
            name="Torso",
            part_type=PartType.TORSO,
            position=Point2D(x=400, y=300),
            width=80,
            height=40,
            color="#00e5ff",
        )
        return CreatureBlueprint(
            id=f"creature_{uuid.uuid4().hex[:8]}",
            name=creature_name,
            bodies=[torso],
            joints=[],
            torso_id=torso.id,
            locomotion=LocomotionConfig(gait_type=GaitType.CUSTOM),
            steering=SteeringConfig(),
            raw_strokes=raw_strokes,
        )

    bodies: List[RigidBodyDef] = []
    joints: List[JointDef] = []
    body_id_map: Dict[int, str] = {}  # stroke_index -> primary body id
    torso_id: str = ""

    # Part counts for gait type determination
    leg_count = 0
    wheel_count = 0
    wing_count = 0
    tail_count = 0

    # 1. Create Torso body first
    torso_part = next((p for p in parts if p.part_type == PartType.TORSO), parts[0])
    torso_id = f"body_torso_{torso_part.stroke_index}"
    body_id_map[torso_part.stroke_index] = torso_id

    torso_w = max(torso_part.bbox[4], 30.0)
    torso_h = max(torso_part.bbox[5], 25.0)
    local_verts = _points_to_local_vertices(torso_part.points, torso_part.centroid)

    torso_body = RigidBodyDef(
        id=torso_id,
        name="Torso Core",
        part_type=PartType.TORSO,
        shape="polygon" if len(local_verts) >= 3 else "box",
        position=torso_part.centroid,
        angle=torso_part.orientation * 0.2,  # slight natural tilt
        width=round(torso_w, 1),
        height=round(torso_h, 1),
        vertices=local_verts,
        density=1.6,
        friction=0.5,
        restitution=0.05,
        color="#00e5ff",
        stroke_index=torso_part.stroke_index,
        parent_id=None,
        collision_group=-1,  # group -1 avoids mutual limb jam
    )
    bodies.append(torso_body)

    # 2. Build appendages
    legs: List[Tuple[SegmentedPart, str]] = []
    wings: List[Tuple[SegmentedPart, str]] = []
    tails: List[Tuple[SegmentedPart, str]] = []
    wheels: List[Tuple[SegmentedPart, str]] = []

    for part in parts:
        if part.part_type == PartType.TORSO:
            continue

        p_type = part.part_type
        idx = part.stroke_index
        w = max(part.bbox[4], 15.0)
        h = max(part.bbox[5], 15.0)
        c = part.centroid

        if p_type == PartType.WHEEL:
            wheel_count += 1
            b_id = f"body_wheel_{idx}"
            body_id_map[idx] = b_id
            radius = max(w, h) * 0.5
            wheel_body = RigidBodyDef(
                id=b_id,
                name=f"Wheel {wheel_count}",
                part_type=PartType.WHEEL,
                shape="circle",
                position=c,
                angle=0.0,
                width=radius * 2,
                height=radius * 2,
                radius=round(radius, 1),
                density=1.2,
                friction=0.95,
                restitution=0.1,
                color="#ffeb3b",
                stroke_index=idx,
                parent_id=torso_id,
                collision_group=1,
            )
            bodies.append(wheel_body)
            wheels.append((part, b_id))

        elif p_type == PartType.LEG and part.sub_segments and len(part.sub_segments) == 2:
            # Multi-segment articulated leg (Hip -> Thigh -> Knee -> Shin)
            leg_count += 1
            upper_pts = part.sub_segments[0]
            lower_pts = part.sub_segments[1]

            u_center, _ = compute_centroid_and_area(upper_pts)
            l_center, _ = compute_centroid_and_area(lower_pts)
            u_bbox = compute_bounding_box(upper_pts)
            l_bbox = compute_bounding_box(lower_pts)

            upper_id = f"body_leg_upper_{idx}"
            lower_id = f"body_leg_lower_{idx}"
            body_id_map[idx] = upper_id

            upper_body = RigidBodyDef(
                id=upper_id,
                name=f"Leg {leg_count} (Thigh)",
                part_type=PartType.LEG,
                shape="box",
                position=u_center,
                angle=part.orientation,
                width=max(u_bbox[4], 12.0),
                height=max(u_bbox[5], 20.0),
                vertices=_points_to_local_vertices(upper_pts, u_center),
                density=0.8,
                friction=0.7,
                restitution=0.05,
                color="#00bcd4",
                stroke_index=idx,
                parent_id=torso_id,
                collision_group=-1,
            )
            lower_body = RigidBodyDef(
                id=lower_id,
                name=f"Leg {leg_count} (Shin)",
                part_type=PartType.LEG,
                shape="box",
                position=l_center,
                angle=part.orientation,
                width=max(l_bbox[4], 10.0),
                height=max(l_bbox[5], 20.0),
                vertices=_points_to_local_vertices(lower_pts, l_center),
                density=0.7,
                friction=0.9,  # High ground traction
                restitution=0.02,
                color="#26c6da",
                stroke_index=idx,
                parent_id=upper_id,
                collision_group=-1,
            )
            bodies.extend([upper_body, lower_body])

            # Knee Joint between upper and lower segment
            knee_pivot = upper_pts[-1]
            knee_joint = JointDef(
                id=f"joint_knee_{idx}",
                joint_type=JointType.REVOLUTE,
                body_a_id=upper_id,
                body_b_id=lower_id,
                anchor_a=Point2D(x=knee_pivot.x - u_center.x, y=knee_pivot.y - u_center.y),
                anchor_b=Point2D(x=knee_pivot.x - l_center.x, y=knee_pivot.y - l_center.y),
                world_anchor=knee_pivot,
                stiffness=0.9,
                damping=0.1,
                min_angle=-0.2,
                max_angle=1.2,
                motor=MotorDef(
                    enabled=True,
                    amplitude=0.45,
                    frequency=1.5,
                    phase=0.5,
                    max_torque=90.0,
                ),
            )
            joints.append(knee_joint)
            legs.append((part, upper_id))

        else:
            # Single-segment body (Leg, Head, Wing, Tail, Arm)
            b_id = f"body_{p_type.value}_{idx}"
            body_id_map[idx] = b_id
            color_map = {
                PartType.HEAD: "#e040fb",
                PartType.LEG: "#00e676",
                PartType.WING: "#ff4081",
                PartType.TAIL: "#ff9100",
                PartType.ARM: "#7c4dff",
                PartType.FIN: "#00b0ff",
            }
            body = RigidBodyDef(
                id=b_id,
                name=f"{p_type.value.capitalize()} {idx}",
                part_type=p_type,
                shape="polygon" if len(part.points) >= 4 else "box",
                position=c,
                angle=part.orientation,
                width=w,
                height=h,
                vertices=_points_to_local_vertices(part.points, c),
                density=0.8 if p_type != PartType.WING else 0.35,
                friction=0.85 if p_type == PartType.LEG else 0.4,
                restitution=0.05,
                color=color_map.get(p_type, "#00e5ff"),
                stroke_index=idx,
                parent_id=torso_id,
                collision_group=-1,
            )
            bodies.append(body)

            if p_type == PartType.LEG:
                leg_count += 1
                legs.append((part, b_id))
            elif p_type == PartType.WING:
                wing_count += 1
                wings.append((part, b_id))
            elif p_type == PartType.TAIL:
                tail_count += 1
                tails.append((part, b_id))

    # 3. Create Constraints & Motors connecting each part to Torso
    # Sort legs left to right (by X position) for natural phase progression
    legs_sorted = sorted(legs, key=lambda pair: pair[0].centroid.x)

    # Determine Gait Profile
    if wheel_count >= 1:
        gait_type = GaitType.WHEELED_DRIVE
    elif leg_count == 2:
        gait_type = GaitType.BIPED_STRIDE
    elif leg_count == 4:
        gait_type = GaitType.QUADRUPED_TROT
    elif leg_count >= 5:
        gait_type = GaitType.HEXAPOD_RIPPLE
    elif wing_count >= 2 and leg_count <= 1:
        gait_type = GaitType.AVIAN_FLAP
    elif tail_count >= 1 and leg_count == 0:
        gait_type = GaitType.SERPENTINE_WAVE
    else:
        gait_type = GaitType.QUADRUPED_TROT if leg_count > 0 else GaitType.CUSTOM

    locomotion_config = LocomotionConfig(gait_type=gait_type, base_frequency=1.5, drive_power=1.0)

    # Connect appendages to Torso
    for part in parts:
        if part.part_type == PartType.TORSO:
            continue

        child_id = body_id_map.get(part.stroke_index)
        if not child_id:
            continue

        pivot = part.pivot_to_parent or part.centroid
        anchor_torso = Point2D(x=pivot.x - torso_part.centroid.x, y=pivot.y - torso_part.centroid.y)
        anchor_child = Point2D(x=pivot.x - part.centroid.x, y=pivot.y - part.centroid.y)

        p_type = part.part_type
        joint_id = f"joint_{torso_id}_{child_id}"

        if p_type == PartType.WHEEL:
            # Continuous torque motor
            j = JointDef(
                id=joint_id,
                joint_type=JointType.WHEEL_AXLE,
                body_a_id=torso_id,
                body_b_id=child_id,
                anchor_a=anchor_torso,
                anchor_b=anchor_child,
                world_anchor=pivot,
                stiffness=1.0,
                damping=0.05,
                motor=MotorDef(
                    enabled=True,
                    speed=6.0,  # forward angular speed
                    max_torque=180.0,
                    waveform="constant",
                ),
            )
            joints.append(j)

        elif p_type == PartType.HEAD:
            # Flexible neck / shock absorber
            j = JointDef(
                id=joint_id,
                joint_type=JointType.REVOLUTE,
                body_a_id=torso_id,
                body_b_id=child_id,
                anchor_a=anchor_torso,
                anchor_b=anchor_child,
                world_anchor=pivot,
                stiffness=0.85,
                damping=0.2,
                min_angle=-0.35,
                max_angle=0.35,
                motor=MotorDef(
                    enabled=True,
                    amplitude=0.15,
                    frequency=1.5,
                    phase=0.0,
                    max_torque=50.0,
                ),
            )
            joints.append(j)

        elif p_type == PartType.WING:
            # Flapping motor
            # Wing index among wings
            wing_idx = next((i for i, (w_part, _) in enumerate(wings) if w_part == part), 0)
            wing_phase = 0.0 if wing_idx % 2 == 0 else math.pi
            j = JointDef(
                id=joint_id,
                joint_type=JointType.REVOLUTE,
                body_a_id=torso_id,
                body_b_id=child_id,
                anchor_a=anchor_torso,
                anchor_b=anchor_child,
                world_anchor=pivot,
                stiffness=0.9,
                damping=0.05,
                min_angle=-0.8,
                max_angle=0.8,
                motor=MotorDef(
                    enabled=True,
                    amplitude=0.65,
                    frequency=2.2,
                    phase=wing_phase,
                    max_torque=140.0,
                ),
            )
            locomotion_config.phase_offsets[joint_id] = wing_phase
            locomotion_config.amplitudes[joint_id] = 0.65
            joints.append(j)

        elif p_type == PartType.TAIL:
            # Undulating balance tail
            j = JointDef(
                id=joint_id,
                joint_type=JointType.REVOLUTE,
                body_a_id=torso_id,
                body_b_id=child_id,
                anchor_a=anchor_torso,
                anchor_b=anchor_child,
                world_anchor=pivot,
                stiffness=0.7,
                damping=0.15,
                min_angle=-0.6,
                max_angle=0.6,
                motor=MotorDef(
                    enabled=True,
                    amplitude=0.4,
                    frequency=1.5,
                    phase=math.pi * 0.75,
                    max_torque=60.0,
                ),
            )
            joints.append(j)

        elif p_type == PartType.LEG:
            # Leg Hip joint with gait-specific phase offset
            leg_order_idx = next((i for i, (l_part, _) in enumerate(legs_sorted) if l_part == part), 0)
            n_legs = len(legs_sorted)

            if n_legs == 2:
                # Alternating stride: 0 and pi
                leg_phase = 0.0 if leg_order_idx == 0 else math.pi
            elif n_legs == 4:
                # Quadruped trot: front-left/rear-right pair, front-right/rear-left pair
                # order 0,1,2,3 -> left to right: [0, pi, 0, pi]
                leg_phase = 0.0 if (leg_order_idx % 2 == 0) else math.pi
            elif n_legs >= 5:
                # Wave gait / metachronal wave: phase delay 2pi / n_legs
                leg_phase = (2.0 * math.pi * leg_order_idx) / n_legs
            else:
                leg_phase = 0.0

            j = JointDef(
                id=joint_id,
                joint_type=JointType.REVOLUTE,
                body_a_id=torso_id,
                body_b_id=child_id,
                anchor_a=anchor_torso,
                anchor_b=anchor_child,
                world_anchor=pivot,
                stiffness=0.95,
                damping=0.08,
                min_angle=-0.75,
                max_angle=0.75,
                motor=MotorDef(
                    enabled=True,
                    amplitude=0.55,
                    frequency=1.6,
                    phase=leg_phase,
                    max_torque=150.0,
                ),
            )
            locomotion_config.phase_offsets[joint_id] = leg_phase
            locomotion_config.amplitudes[joint_id] = 0.55
            joints.append(j)

        else:
            # Default revolute attachment
            j = JointDef(
                id=joint_id,
                joint_type=JointType.REVOLUTE,
                body_a_id=torso_id,
                body_b_id=child_id,
                anchor_a=anchor_torso,
                anchor_b=anchor_child,
                world_anchor=pivot,
                stiffness=0.8,
                damping=0.1,
                min_angle=-0.5,
                max_angle=0.5,
            )
            joints.append(j)

    blueprint = CreatureBlueprint(
        id=f"creature_{uuid.uuid4().hex[:8]}",
        name=creature_name,
        bodies=bodies,
        joints=joints,
        torso_id=torso_id,
        locomotion=locomotion_config,
        steering=SteeringConfig(),
        raw_strokes=raw_strokes,
        metadata={
            "leg_count": leg_count,
            "wheel_count": wheel_count,
            "wing_count": wing_count,
            "tail_count": tail_count,
            "body_count": len(bodies),
            "joint_count": len(joints),
        },
    )
    return blueprint


def rig_strokes(
    strokes: List[Stroke],
    creature_name: str = "DoodleCreature",
    simplify_tolerance: float = 2.5,
) -> CreatureBlueprint:
    """End-to-end pipeline: Stroke vectorization -> Semantic segmentation -> Physics Auto-rigging."""
    parts = decompose_strokes(strokes, simplify_tolerance=simplify_tolerance)
    return rig_segmented_parts(parts, creature_name=creature_name, raw_strokes=strokes)
