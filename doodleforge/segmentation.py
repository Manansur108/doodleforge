"""
Multimodal stroke-to-anatomy segmentation and semantic decomposition pipeline.
Parses freehand sketches into anatomical components (Torso, Head, Legs, Wings, Tail, Wheels)
and computes accurate skeletal pivot attachment coordinates.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple
from doodleforge.geometry import (
    closest_points_between_polylines,
    compute_bounding_box,
    compute_centroid_and_area,
    compute_moments_and_orientation,
    distance,
    is_closed_contour,
    rdp_simplify,
)
from doodleforge.models import PartType, Point2D, Stroke


class SegmentedPart:
    """Intermediate anatomical representation of a classified stroke."""

    def __init__(
        self,
        stroke_index: int,
        part_type: PartType,
        points: List[Point2D],
        centroid: Point2D,
        area: float,
        bbox: Tuple[float, float, float, float, float, float],
        orientation: float,
        aspect_ratio: float,
        pivot_to_parent: Optional[Point2D] = None,
        parent_index: Optional[int] = None,
        sub_segments: Optional[List[List[Point2D]]] = None,
    ):
        self.stroke_index = stroke_index
        self.part_type = part_type
        self.points = points
        self.centroid = centroid
        self.area = area
        self.bbox = bbox  # min_x, min_y, max_x, max_y, width, height
        self.orientation = orientation
        self.aspect_ratio = aspect_ratio
        self.pivot_to_parent = pivot_to_parent
        self.parent_index = parent_index
        self.sub_segments = sub_segments or []


def detect_knee_bend(points: List[Point2D], min_angle_deg: float = 35.0) -> Optional[int]:
    """
    Detects if a leg stroke has a distinct knee joint inflection point.
    Returns the index of the knee pivot point if detected.
    """
    if len(points) < 5:
        return None

    n = len(points)
    # Check inner points (ignore endpoints)
    start_idx = max(1, int(n * 0.25))
    end_idx = min(n - 1, int(n * 0.75))

    max_deflection = 0.0
    best_idx = None

    for i in range(start_idx, end_idx):
        p_prev = points[max(0, i - 2)]
        p_curr = points[i]
        p_next = points[min(n - 1, i + 2)]

        v1 = (p_curr.x - p_prev.x, p_curr.y - p_prev.y)
        v2 = (p_next.x - p_curr.x, p_next.y - p_curr.y)

        len1 = math.hypot(v1[0], v1[1])
        len2 = math.hypot(v2[0], v2[1])

        if len1 > 1e-4 and len2 > 1e-4:
            dot = (v1[0] * v2[0] + v1[1] * v2[1]) / (len1 * len2)
            dot = max(-1.0, min(1.0, dot))
            angle = math.acos(dot)  # deflection angle in radians
            angle_deg = math.degrees(angle)
            if angle_deg > min_angle_deg and angle_deg > max_deflection:
                max_deflection = angle_deg
                best_idx = i

    return best_idx


def decompose_strokes(
    raw_strokes: List[Stroke], simplify_tolerance: float = 2.5
) -> List[SegmentedPart]:
    """
    Analyzes, classifies, and decomposes an arbitrary list of drawn strokes
    into structured anatomical parts with parent-child linkage and pivot joints.
    """
    if not raw_strokes:
        return []

    # 1. Simplify and extract geometric descriptors
    simplified_strokes: List[List[Point2D]] = []
    stroke_metrics = []

    for idx, s in enumerate(raw_strokes):
        pts = rdp_simplify(s.points, epsilon=simplify_tolerance)
        if len(pts) < 2:
            pts = list(s.points) if len(s.points) >= 2 else [Point2D(x=0, y=0), Point2D(x=10, y=10)]

        centroid, area = compute_centroid_and_area(pts)
        bbox = compute_bounding_box(pts)
        orient, aspect_ratio, _ = compute_moments_and_orientation(pts)
        closed = s.closed or is_closed_contour(pts)

        simplified_strokes.append(pts)
        stroke_metrics.append({
            "index": idx,
            "points": pts,
            "centroid": centroid,
            "area": area,
            "bbox": bbox,
            "orientation": orient,
            "aspect_ratio": aspect_ratio,
            "closed": closed,
            "hint": s.part_hint,
        })

    # Overall bounding box of all strokes
    all_points = [p for pts in simplified_strokes for p in pts]
    glob_min_x, glob_min_y, glob_max_x, glob_max_y, glob_w, glob_h = compute_bounding_box(all_points)
    glob_w = max(glob_w, 1.0)
    glob_h = max(glob_h, 1.0)

    # 2. Identify Torso (core central mass)
    torso_idx = 0
    best_torso_score = -1e9

    for m in stroke_metrics:
        if m["hint"] == "torso":
            torso_idx = m["index"]
            break

        idx = m["index"]
        c = m["centroid"]
        _, _, _, _, w, h = m["bbox"]
        norm_y = (c.y - glob_min_y) / glob_h
        norm_x = (c.x - glob_min_x) / glob_w

        # Prefer large area, moderate aspect ratio, central vertical position
        area_score = m["area"] if m["area"] > 50 else (w * h * 0.4)
        center_penalty = (abs(norm_y - 0.45) * 1.5 + abs(norm_x - 0.5)) * 400.0
        closed_bonus = 200.0 if m["closed"] else 0.0

        score = area_score - center_penalty + closed_bonus
        if score > best_torso_score:
            best_torso_score = score
            torso_idx = idx

    torso_metric = stroke_metrics[torso_idx]
    torso_c = torso_metric["centroid"]
    torso_pts = torso_metric["points"]

    # 3. Classify all strokes
    parts: List[SegmentedPart] = []

    # First add Torso
    torso_part = SegmentedPart(
        stroke_index=torso_idx,
        part_type=PartType.TORSO,
        points=torso_pts,
        centroid=torso_c,
        area=torso_metric["area"],
        bbox=torso_metric["bbox"],
        orientation=torso_metric["orientation"],
        aspect_ratio=torso_metric["aspect_ratio"],
        pivot_to_parent=None,
        parent_index=None,
    )
    parts.append(torso_part)

    # Determine creature forward facing direction based on other strokes
    # Default right-facing (+x), check if features concentrate to the left or right
    left_count = 0
    right_count = 0
    for m in stroke_metrics:
        if m["index"] == torso_idx:
            continue
        if m["centroid"].x > torso_c.x:
            right_count += 1
        else:
            left_count += 1
    facing_right = right_count >= left_count

    # Classify non-torso strokes
    for m in stroke_metrics:
        idx = m["index"]
        if idx == torso_idx:
            continue

        pts = m["points"]
        c = m["centroid"]
        _, _, _, _, w, h = m["bbox"]
        dx = c.x - torso_c.x
        dy = c.y - torso_c.y
        norm_y = (c.y - glob_min_y) / glob_h
        is_closed = m["closed"]
        aspect = m["aspect_ratio"]

        # Compute closest points to torso for attachment pivot
        min_dist, limb_pivot, torso_pivot = closest_points_between_polylines(pts, torso_pts)
        pivot = Point2D(x=(limb_pivot.x + torso_pivot.x) * 0.5, y=(limb_pivot.y + torso_pivot.y) * 0.5)

        # Explicit user hint override
        if m["hint"]:
            part_type = PartType(m["hint"])
        elif is_closed and aspect < 1.45 and dy > -10 and (w * h < torso_metric["bbox"][4] * torso_metric["bbox"][5] * 0.6):
            # Wheel: round closed loop in bottom half
            part_type = PartType.WHEEL
        elif dy < -15 and abs(dx) < glob_w * 0.35 and w > h * 1.2:
            # Wing: high elevated wide stroke
            part_type = PartType.WING
        elif dy < 5 and ((facing_right and dx > glob_w * 0.12) or (not facing_right and dx < -glob_w * 0.12)):
            # Head: forward upper quadrant
            part_type = PartType.HEAD
        elif ((facing_right and dx < -glob_w * 0.15) or (not facing_right and dx > glob_w * 0.15)) and abs(dy) < glob_h * 0.4:
            # Tail: rearward trailing stroke
            part_type = PartType.TAIL
        elif dy >= -5:
            # Below or level with torso -> Leg
            part_type = PartType.LEG
        elif dy < -10:
            # Upper appendage -> Wing or Arm
            part_type = PartType.WING if w > h else PartType.ARM
        else:
            part_type = PartType.LEG

        # Check for knee bend if it's a leg
        sub_segs = None
        if part_type == PartType.LEG:
            knee_idx = detect_knee_bend(pts)
            if knee_idx is not None and 2 <= knee_idx <= len(pts) - 3:
                upper_leg = pts[: knee_idx + 1]
                lower_leg = pts[knee_idx:]
                sub_segs = [upper_leg, lower_leg]

        part = SegmentedPart(
            stroke_index=idx,
            part_type=part_type,
            points=pts,
            centroid=c,
            area=m["area"],
            bbox=m["bbox"],
            orientation=m["orientation"],
            aspect_ratio=aspect,
            pivot_to_parent=pivot,
            parent_index=torso_idx,
            sub_segments=sub_segs,
        )
        parts.append(part)

    return parts
