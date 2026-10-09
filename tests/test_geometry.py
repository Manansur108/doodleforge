"""
Tests for doodleforge.geometry module.
"""

import math
import pytest
from doodleforge.geometry import (
    closest_points_between_polylines,
    compute_bounding_box,
    compute_centroid_and_area,
    compute_moments_and_orientation,
    distance,
    is_closed_contour,
    point_in_polygon,
    polygon_convex_hull,
    rdp_simplify,
    resample_stroke,
)
from doodleforge.models import Point2D


def test_rdp_simplify_reduces_collinear_points():
    # Straight line with 10 collinear points
    points = [Point2D(x=float(i * 10), y=0.0) for i in range(10)]
    simplified = rdp_simplify(points, epsilon=2.0)
    assert len(simplified) == 2
    assert simplified[0].x == 0.0
    assert simplified[-1].x == 90.0


def test_resample_stroke_equidistant():
    points = [Point2D(x=0, y=0), Point2D(x=100, y=0)]
    resampled = resample_stroke(points, num_points=5)
    assert len(resampled) == 5
    assert math.isclose(resampled[0].x, 0.0, abs_tol=1e-3)
    assert math.isclose(resampled[2].x, 50.0, abs_tol=1e-3)
    assert math.isclose(resampled[4].x, 100.0, abs_tol=1e-3)


def test_compute_bounding_box():
    points = [
        Point2D(x=10, y=20),
        Point2D(x=110, y=20),
        Point2D(x=110, y=70),
        Point2D(x=10, y=70),
    ]
    min_x, min_y, max_x, max_y, width, height = compute_bounding_box(points)
    assert min_x == 10.0
    assert min_y == 20.0
    assert max_x == 110.0
    assert max_y == 70.0
    assert width == 100.0
    assert height == 50.0


def test_compute_centroid_and_area():
    # Unit box of size 40x40 located from (10, 10) to (50, 50)
    points = [
        Point2D(x=10, y=10),
        Point2D(x=50, y=10),
        Point2D(x=50, y=50),
        Point2D(x=10, y=50),
    ]
    centroid, area = compute_centroid_and_area(points)
    assert math.isclose(area, 1600.0, rel_tol=1e-3)
    assert math.isclose(centroid.x, 30.0, abs_tol=1e-2)
    assert math.isclose(centroid.y, 30.0, abs_tol=1e-2)


def test_compute_moments_and_orientation():
    # Elongated horizontal line
    points = [Point2D(x=float(i * 10), y=20.0) for i in range(10)]
    orientation, aspect_ratio, inertia = compute_moments_and_orientation(points)
    assert aspect_ratio > 2.0
    assert inertia > 0.0


def test_closest_points_between_polylines():
    poly1 = [Point2D(x=0, y=0), Point2D(x=10, y=0)]
    poly2 = [Point2D(x=5, y=20), Point2D(x=5, y=30)]
    min_dist, p1, p2 = closest_points_between_polylines(poly1, poly2)
    assert math.isclose(min_dist, 20.0, abs_tol=1e-2)
    assert math.isclose(p1.x, 5.0, abs_tol=1e-2)
    assert math.isclose(p1.y, 0.0, abs_tol=1e-2)
    assert math.isclose(p2.x, 5.0, abs_tol=1e-2)
    assert math.isclose(p2.y, 20.0, abs_tol=1e-2)


def test_polygon_convex_hull_and_point_in_polygon():
    square = [
        Point2D(x=0, y=0),
        Point2D(x=10, y=0),
        Point2D(x=10, y=10),
        Point2D(x=0, y=10),
        Point2D(x=5, y=5),  # Interior point
    ]
    hull = polygon_convex_hull(square)
    assert len(hull) == 4
    assert point_in_polygon(Point2D(x=5, y=5), hull) is True
    assert point_in_polygon(Point2D(x=20, y=20), hull) is False
