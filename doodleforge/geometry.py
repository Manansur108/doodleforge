"""
Geometry and stroke vector processing algorithms for DoodleForge.
Includes Ramer-Douglas-Peucker simplification, polygon moments,
centroid calculation, closest point/pivot detection, and convex hulls.
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple
from doodleforge.models import Point2D


def distance(p1: Point2D, p2: Point2D) -> float:
    """Euclidean distance between two 2D points."""
    return math.hypot(p1.x - p2.x, p1.y - p2.y)


def perpendicular_distance(point: Point2D, line_start: Point2D, line_end: Point2D) -> float:
    """Perpendicular distance from a point to a line segment."""
    dx = line_end.x - line_start.x
    dy = line_end.y - line_start.y
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq < 1e-9:
        return distance(point, line_start)

    # Cross product magnitude divided by segment length
    cross = abs(dy * point.x - dx * point.y + line_end.x * line_start.y - line_end.y * line_start.x)
    return cross / math.sqrt(seg_len_sq)


def rdp_simplify(points: List[Point2D], epsilon: float = 2.5) -> List[Point2D]:
    """
    Ramer-Douglas-Peucker algorithm to reduce the number of points in a polyline.
    Preserves salient corner features while removing high-frequency jitter.
    """
    if len(points) <= 2:
        return list(points)

    dmax = 0.0
    index = 0
    start = points[0]
    end = points[-1]

    for i in range(1, len(points) - 1):
        d = perpendicular_distance(points[i], start, end)
        if d > dmax:
            index = i
            dmax = d

    if dmax > epsilon:
        rec_results1 = rdp_simplify(points[: index + 1], epsilon)
        rec_results2 = rdp_simplify(points[index:], epsilon)
        return rec_results1[:-1] + rec_results2
    else:
        return [start, end]


def resample_stroke(points: List[Point2D], num_points: int = 32) -> List[Point2D]:
    """
    Resample a polyline stroke into an equidistant sequence of points
    based on cumulative arc length.
    """
    if len(points) <= 1 or num_points <= 1:
        return list(points)

    # Compute cumulative arc lengths
    cum_dists = [0.0]
    total_len = 0.0
    for i in range(1, len(points)):
        d = distance(points[i - 1], points[i])
        total_len += d
        cum_dists.append(total_len)

    if total_len < 1e-6:
        return [points[0]] * num_points

    step = total_len / (num_points - 1)
    resampled: List[Point2D] = [points[0]]

    curr_idx = 0
    for i in range(1, num_points - 1):
        target_dist = i * step
        while curr_idx < len(cum_dists) - 1 and cum_dists[curr_idx + 1] < target_dist:
            curr_idx += 1

        p1 = points[curr_idx]
        p2 = points[curr_idx + 1]
        seg_d = cum_dists[curr_idx + 1] - cum_dists[curr_idx]
        t = (target_dist - cum_dists[curr_idx]) / seg_d if seg_d > 1e-9 else 0.0
        rx = p1.x + t * (p2.x - p1.x)
        ry = p1.y + t * (p2.y - p1.y)
        resampled.append(Point2D(x=rx, y=ry))

    resampled.append(points[-1])
    return resampled


def compute_bounding_box(points: List[Point2D]) -> Tuple[float, float, float, float, float, float]:
    """
    Calculates axis-aligned bounding box.
    Returns: (min_x, min_y, max_x, max_y, width, height)
    """
    if not points:
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    min_x = min(p.x for p in points)
    max_x = max(p.x for p in points)
    min_y = min(p.y for p in points)
    max_y = max(p.y for p in points)
    width = max_x - min_x
    height = max_y - min_y
    return (min_x, min_y, max_x, max_y, width, height)


def compute_centroid_and_area(points: List[Point2D]) -> Tuple[Point2D, float]:
    """
    Computes polygon centroid and signed/unsigned area using Green's Theorem.
    Falls back to mean of points if area is negligible (e.g. open thin line).
    """
    n = len(points)
    if n == 0:
        return (Point2D(x=0.0, y=0.0), 0.0)
    if n < 3:
        mean_x = sum(p.x for p in points) / n
        mean_y = sum(p.y for p in points) / n
        return (Point2D(x=mean_x, y=mean_y), 0.0)

    signed_area = 0.0
    cx = 0.0
    cy = 0.0

    for i in range(n):
        p1 = points[i]
        p2 = points[(i + 1) % n]
        cross = p1.x * p2.y - p2.x * p1.y
        signed_area += cross
        cx += (p1.x + p2.x) * cross
        cy += (p1.y + p2.y) * cross

    signed_area *= 0.5
    abs_area = abs(signed_area)

    if abs_area > 1e-4:
        cx /= (6.0 * signed_area)
        cy /= (6.0 * signed_area)
        return (Point2D(x=cx, y=cy), abs_area)
    else:
        mean_x = sum(p.x for p in points) / n
        mean_y = sum(p.y for p in points) / n
        return (Point2D(x=mean_x, y=mean_y), 0.0)


def compute_moments_and_orientation(points: List[Point2D]) -> Tuple[float, float, float]:
    """
    Computes principal orientation angle (radians) and aspect ratio (eccentricity)
    via second central moments of area.
    Returns: (orientation_radians, aspect_ratio, moment_of_inertia)
    """
    n = len(points)
    if n < 2:
        return (0.0, 1.0, 1.0)

    center, _ = compute_centroid_and_area(points)

    # Compute second central moments
    mu20 = 0.0
    mu02 = 0.0
    mu11 = 0.0

    for p in points:
        dx = p.x - center.x
        dy = p.y - center.y
        mu20 += dx * dx
        mu02 += dy * dy
        mu11 += dx * dy

    mu20 /= n
    mu02 /= n
    mu11 /= n

    # Principal axis orientation
    orientation = 0.5 * math.atan2(2 * mu11, mu20 - mu02)

    # Eigenvalues of covariance matrix
    diff = mu20 - mu02
    disc = math.sqrt(diff * diff + 4 * mu11 * mu11)
    lambda1 = 0.5 * (mu20 + mu02 + disc)
    lambda2 = 0.5 * (mu20 + mu02 - disc)

    aspect_ratio = math.sqrt(lambda1 / max(lambda2, 1e-4)) if lambda1 > 0 else 1.0
    inertia = max(lambda1 + lambda2, 1.0)

    return (orientation, aspect_ratio, inertia)


def distance_point_to_segment(p: Point2D, a: Point2D, b: Point2D) -> Tuple[float, Point2D]:
    """
    Computes minimum Euclidean distance from point P to line segment AB,
    and returns the closest projected point on the segment.
    """
    dx = b.x - a.x
    dy = b.y - a.y
    len_sq = dx * dx + dy * dy

    if len_sq < 1e-9:
        return (distance(p, a), a)

    t = max(0.0, min(1.0, ((p.x - a.x) * dx + (p.y - a.y) * dy) / len_sq))
    proj = Point2D(x=a.x + t * dx, y=a.y + t * dy)
    return (distance(p, proj), proj)


def closest_points_between_polylines(
    poly1: List[Point2D], poly2: List[Point2D]
) -> Tuple[float, Point2D, Point2D]:
    """
    Finds the minimum distance between two polylines and returns:
    (min_distance, point_on_poly1, point_on_poly2)
    This is used to determine anatomical connection pivots (e.g. where a leg meets the torso).
    """
    min_dist = float("inf")
    best_p1 = poly1[0]
    best_p2 = poly2[0]

    # Test vertices of poly1 against segments of poly2
    for p in poly1:
        for i in range(len(poly2) - 1):
            d, proj = distance_point_to_segment(p, poly2[i], poly2[i + 1])
            if d < min_dist:
                min_dist = d
                best_p1 = p
                best_p2 = proj

    # Test vertices of poly2 against segments of poly1
    for p in poly2:
        for i in range(len(poly1) - 1):
            d, proj = distance_point_to_segment(p, poly1[i], poly1[i + 1])
            if d < min_dist:
                min_dist = d
                best_p1 = proj
                best_p2 = p

    return (min_dist, best_p1, best_p2)


def is_closed_contour(points: List[Point2D], threshold: float = 25.0) -> bool:
    """
    Determines if a stroke represents a closed loop/contour based on endpoint proximity.
    """
    if len(points) < 4:
        return False
    return distance(points[0], points[-1]) < threshold


def polygon_convex_hull(points: List[Point2D]) -> List[Point2D]:
    """
    Computes 2D convex hull of a point set using Monotone Chain (Andrew's algorithm).
    """
    if len(points) <= 3:
        return list(points)

    pts = sorted(points, key=lambda p: (p.x, p.y))

    def cross_2d(o: Point2D, a: Point2D, b: Point2D) -> float:
        return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)

    lower: List[Point2D] = []
    for p in pts:
        while len(lower) >= 2 and cross_2d(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper: List[Point2D] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross_2d(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]


def point_in_polygon(point: Point2D, poly: List[Point2D]) -> bool:
    """
    Standard Ray-Casting algorithm to check if a point lies inside a polygon contour.
    """
    n = len(poly)
    if n < 3:
        return False

    inside = False
    for i in range(n):
        p1 = poly[i]
        p2 = poly[(i + 1) % n]
        if (p1.y > point.y) != (p2.y > point.y):
            if p2.y != p1.y:
                x_inters = (p2.x - p1.x) * (point.y - p1.y) / (p2.y - p1.y) + p1.x
                if point.x < x_inters:
                    inside = not inside
    return inside

