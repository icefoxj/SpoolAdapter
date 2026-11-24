"""The 3DTesla horizontal logo as CadQuery solids.

Geometry copied from the brand master `3DTeslaWebSite/brand/logo-horizontal-dark.svg` (viewBox 197 x 64):
the yellow emblem (a square with its top-left and bottom-right corners cut at 45 deg), the "3D" mark
stroked inside it, and the "TESLA" lettering beside it. Strokes have square caps and mitred joins, as in
the SVG.

On a two-colour print only two colours exist, so the logo is drawn as the dark-background variant with
TESLA in yellow instead of white: yellow = emblem minus "3D" plus "TESLA"; the base colour shows through
the "3D" strokes.
"""
from __future__ import annotations

import cadquery as cq
import numpy as np

VIEW_W, VIEW_H = 197.0, 64.0                      # SVG units; y points down
EMBLEM = [(14, 0), (64, 0), (64, 50), (50, 64), (0, 64), (0, 14)]

# (translate x, translate y, scale, stroke width in path units, polylines in path units)
MARK_3D = (7.69, 17.0, 4.138, 1.25, [
    [(0.625, 0.625), (3.625, 0.625), (4.625, 1.625), (4.625, 5.625), (3.625, 6.625), (0.625, 6.625)],
    [(2.125, 3.625), (4.625, 3.625)],
    [(7.125, 6.625), (10.125, 6.625), (11.125, 5.625), (11.125, 1.625), (10.125, 0.625), (7.125, 0.625),
     (7.125, 6.625)],
])
TESLA = (77.0, 17.517, 4.138, 1.0, [
    [(0.5, 0.5), (4.5, 0.5)], [(2.5, 0.5), (2.5, 6.5)],                                   # T
    [(10.5, 0.5), (6.5, 0.5), (6.5, 6.5), (10.5, 6.5)], [(6.5, 3.5), (9.5, 3.5)],         # E
    [(16.5, 0.5), (13.5, 0.5), (12.5, 1.5), (12.5, 2.5), (13.5, 3.5), (15.5, 3.5),        # S
     (16.5, 4.5), (16.5, 5.5), (15.5, 6.5), (12.5, 6.5)],
    [(18.5, 0.5), (18.5, 6.5), (22.5, 6.5)],                                              # L
    [(24.5, 6.5), (24.5, 1.5), (25.5, 0.5), (27.5, 0.5), (28.5, 1.5), (28.5, 6.5)],       # A
    [(24.5, 4.0), (28.5, 4.0)],
])


def min_stroke(height):
    """Thinnest stroke of the logo at a given height (mm): TESLA's 1-unit stroke, scaled."""
    k = height / VIEW_H
    return min(MARK_3D[2] * MARK_3D[3], TESLA[2] * TESLA[3]) * k


def width(height):
    return VIEW_W * height / VIEW_H


# ------------------------------------------------------------------------------------------ geometry
def _area(c):
    return 0.5 * np.sum(c[:, 0] * np.roll(c[:, 1], -1) - np.roll(c[:, 0], -1) * c[:, 1])


def stroke_loops(points, w):
    """Polyline -> loops (outer first) of a stroke with mitred joins and square ends (from the house
    mech font, LineFollowerRobot cad/mech.py). A polyline whose last point repeats the first is closed."""
    p = np.asarray(points, dtype=float)
    closed = len(p) > 2 and np.allclose(p[0], p[-1])
    if closed:
        p = p[:-1]
    h = w / 2
    seg = np.roll(p, -1, axis=0) - p if closed else np.diff(p, axis=0)
    d = seg / np.linalg.norm(seg, axis=1, keepdims=True)
    n = np.column_stack([-d[:, 1], d[:, 0]])

    def offset(sign):
        out = []
        if not closed:
            out.append(p[0] + h * (sign * n[0] - d[0]))
        joints = range(len(p)) if closed else range(1, len(p) - 1)
        for j in joints:
            a, b = n[j - 1], n[j]
            out.append(p[j] + sign * h * (a + b) / (1 + a @ b))
        if not closed:
            out.append(p[-1] + h * (sign * n[-1] + d[-1]))
        return np.array(out)

    left, right = offset(1), offset(-1)
    if closed:
        loops = sorted((left, right), key=lambda c: -abs(_area(c)))
        return [[tuple(x) for x in loops[0]], [tuple(x) for x in loops[1]]]
    return [[tuple(x) for x in np.vstack([left, right[::-1]])]]


def prism(pts, z0, z1):
    return cq.Workplane("XY").workplane(offset=z0).polyline(pts).close().extrude(z1 - z0).val()


def fuse(solids):
    out = solids[0]
    for s in solids[1:]:
        out = out.fuse(s)
    return out.clean()


def logo_solid(height, z0, z1, to_xy):
    """Yellow part of the logo as one solid between z0 and z1.

    to_xy(X, Y) maps a point of the SVG (units, y down) to the model's (x, y); it may mirror (the logo
    printed on the bed face is seen from below)."""

    def poly(points):
        return prism([to_xy(x, y) for x, y in points], z0, z1)

    def strokes(spec):
        tx, ty, s, w, lines = spec
        out = []
        for line in lines:
            loops = stroke_loops(line, w)
            outer = poly([(tx + s * x, ty + s * y) for x, y in loops[0]])
            for hole in loops[1:]:
                outer = outer.cut(poly([(tx + s * x, ty + s * y) for x, y in hole]))
            out.append(outer)
        return out

    emblem = poly(EMBLEM)
    for st in strokes(MARK_3D):
        emblem = emblem.cut(st)
    return fuse([emblem] + strokes(TESLA))
