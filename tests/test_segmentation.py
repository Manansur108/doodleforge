"""
Tests for doodleforge.segmentation module.
"""

import pytest
from doodleforge.models import PartType, Point2D, Stroke
from doodleforge.segmentation import (
    decompose_strokes,
    detect_knee_bend,
)


def test_decompose_single_torso():
    torso_stroke = Stroke(
        points=[
            Point2D(x=100, y=100),
            Point2D(x=200, y=100),
            Point2D(x=200, y=150),
            Point2D(x=100, y=150),
            Point2D(x=100, y=100),
        ],
        closed=True,
    )
    parts = decompose_strokes([torso_stroke])
    assert len(parts) == 1
    assert parts[0].part_type == PartType.TORSO
    assert parts[0].parent_index is None


def test_classify_torso_and_legs():
    # Central torso
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
    # Left leg extending downward
    leg1 = Stroke(
        points=[Point2D(x=120, y=150), Point2D(x=120, y=220)],
    )
    # Right leg extending downward
    leg2 = Stroke(
        points=[Point2D(x=180, y=150), Point2D(x=180, y=220)],
    )

    parts = decompose_strokes([torso, leg1, leg2])
    assert len(parts) == 3
    torso_part = next(p for p in parts if p.part_type == PartType.TORSO)
    leg_parts = [p for p in parts if p.part_type == PartType.LEG]

    assert torso_part is not None
    assert len(leg_parts) == 2
    for leg in leg_parts:
        assert leg.pivot_to_parent is not None


def test_classify_wheel():
    # Torso
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
    # Circular stroke below torso
    wheel = Stroke(
        points=[
            Point2D(x=140, y=170),
            Point2D(x=160, y=170),
            Point2D(x=160, y=190),
            Point2D(x=140, y=190),
            Point2D(x=140, y=170),
        ],
        closed=True,
    )
    parts = decompose_strokes([torso, wheel])
    wheel_parts = [p for p in parts if p.part_type == PartType.WHEEL]
    assert len(wheel_parts) == 1


def test_classify_wing_and_head():
    # Central torso
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
    # High elevated wing stroke
    wing = Stroke(
        points=[Point2D(x=120, y=70), Point2D(x=180, y=60)],
    )
    # Forward head stroke
    head = Stroke(
        points=[Point2D(x=210, y=110), Point2D(x=230, y=110)],
    )

    parts = decompose_strokes([torso, wing, head])
    assert any(p.part_type == PartType.WING for p in parts)
    assert any(p.part_type == PartType.HEAD for p in parts)


def test_detect_knee_bend():
    # Straight leg points
    straight_pts = [Point2D(x=100, y=float(y)) for y in range(0, 100, 10)]
    assert detect_knee_bend(straight_pts) is None

    # Bent leg: goes down then angles 90 degrees right
    bent_pts = [
        Point2D(x=100, y=0),
        Point2D(x=100, y=20),
        Point2D(x=100, y=40),
        Point2D(x=100, y=60),  # knee inflection
        Point2D(x=120, y=70),
        Point2D(x=140, y=80),
        Point2D(x=160, y=90),
    ]
    knee_idx = detect_knee_bend(bent_pts, min_angle_deg=20.0)
    assert knee_idx is not None
    assert 2 <= knee_idx <= 4
