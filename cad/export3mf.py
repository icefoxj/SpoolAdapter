"""Two-colour 3MF writer (copied from the LF-01 tooling, LineFollowerRobot cad/export3mf.py).

Same format as the other projects (OutageAlarm make_3mf.py, Tab5 stand write_3mf): core 3MF
(2015/02) with no slicer extensions, one named mesh per part grouped in a single object.
Creality Print / Bambu Studio / OrcaSlicer / PrusaSlicer load it as one object whose parts each
take their own filament; the colours are base materials, a hint the slicer may ignore.

Before writing, every mesh is checked: closed and consistently oriented, positive volume, the
printed part on the bed (z = 0), and each inlay exactly LIVERY_DEPTH thick everywhere.

Here the base part is the ring (graphite) and the inlay is the 3DTesla logo (yellow), in the bed face.
"""
from __future__ import annotations

import math
import zipfile
from collections import Counter
from pathlib import Path

from spool_adapter import LIVERY_DEPTH

LAYER = 0.2
GREY = ("Grey", "#A7ABB1")
YELLOW = ("Yellow", "#FFCC00")
GRAPHITE = ("Graphite", "#303236")


class MeshError(RuntimeError):
    pass


def mesh(shape, tol=0.01, ang=0.15):
    """Indexed, welded triangle mesh of a cadquery shape: (vertices, triangles).

    `tol` is an absolute chordal deviation in mm. cadquery's tessellate() meshes with a tolerance
    relative to the edge size, which left the 199 mm rolling surface an 84-gon (0.07 mm flats); the
    shape is meshed here first with an absolute tolerance, and tessellate() keeps that mesh."""
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.BRepTools import BRepTools
    BRepTools.Clean_s(shape.wrapped)
    BRepMesh_IncrementalMesh(shape.wrapped, tol, False, ang, True)
    verts, tris = shape.tessellate(tol, ang)
    index, out_v, out_t = {}, [], []
    remap = []
    for v in verts:
        key = (round(v.x, 5), round(v.y, 5), round(v.z, 5))
        if key not in index:
            index[key] = len(out_v)
            out_v.append(key)
        remap.append(index[key])
    for a, b, c in tris:
        t = (remap[a], remap[b], remap[c])
        if len(set(t)) == 3:
            out_t.append(t)
    return out_v, out_t


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def check_closed(name, tris):
    edges = Counter((t[i], t[(i + 1) % 3]) for t in tris for i in range(3))
    bad = sum(1 for (a, b), n in edges.items() if n != 1 or edges.get((b, a)) != 1)
    if bad:
        raise MeshError(f"{name}: {bad} open, shared or flipped edges")


def volume(verts, tris):
    return sum(_dot(verts[a], _cross(verts[b], verts[c])) for a, b, c in tris) / 6


def layers(verts, tris):
    found = set()
    for t in tris:
        zs = [verts[i][2] for i in t]
        lo, hi = min(zs), max(zs)
        for k in range(max(0, math.floor(lo / LAYER - 0.5)), math.ceil(hi / LAYER - 0.5) + 1):
            if lo < (k + 0.5) * LAYER < hi:
                found.add(k)
    return found


def _num(x):
    s = f"{x:.5f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def write_3mf(path, meshes, name):
    """meshes: list of (part name, verts, tris, (colour name, '#RRGGBB'))."""
    model = ['<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources>'
             '<basematerials id="1">']
    colours = list(dict.fromkeys(c for _, _, _, c in meshes))
    model += [f'<base name="{c}" displaycolor="{rgb}FF"/>' for c, rgb in colours]
    model.append("</basematerials>")
    for i, (part, verts, tris, colour) in enumerate(meshes):
        model.append(f'<object id="{i + 2}" name="{part}" type="model" pid="1" '
                     f'pindex="{colours.index(colour)}"><mesh><vertices>')
        model += [f'<vertex x="{_num(x)}" y="{_num(y)}" z="{_num(z)}"/>' for x, y, z in verts]
        model.append("</vertices><triangles>")
        model += [f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris]
        model.append("</triangles></mesh></object>")
    group = len(meshes) + 2
    model.append(f'<object id="{group}" name="{name}" type="model"><components>')
    model += [f'<component objectid="{i}"/>' for i in range(2, group)]
    model.append(f'</components></object></resources><build><item objectid="{group}"/></build></model>')
    types = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
             "</Types>")
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", "".join(model))


def two_colour(path, name, plate_shape, inlay_shape, base=GRAPHITE, accent=YELLOW):
    """Check and write a plate + inlay pair (both already in print pose). Returns the layer count."""
    pv, pt = mesh(plate_shape)
    iv, it = mesh(inlay_shape, tol=0.01)
    check_closed(name + " plate", pt)
    check_closed(name + " inlay", it)
    if volume(pv, pt) <= 0 or volume(iv, it) <= 0:
        raise MeshError(f"{name}: inside-out or empty mesh")
    zp = min(v[2] for v in pv)
    if abs(zp) > 1e-3:
        raise MeshError(f"{name}: plate not on the bed (z min {zp:.3f})")
    zi = [v[2] for v in iv]
    if abs(min(zi)) > 1e-3 or abs(max(zi) - LIVERY_DEPTH) > 1e-3:
        raise MeshError(f"{name}: inlay is not a {LIVERY_DEPTH} mm slab on the bed (z {min(zi):.3f}..{max(zi):.3f})")
    off = [z for z in zi if 1e-3 < z < LIVERY_DEPTH - 1e-3]
    if off:
        raise MeshError(f"{name}: {len(off)} inlay vertices off its two faces: the livery runs onto a chamfer, "
                        "an edge or a hole")
    ks = layers(iv, it)
    write_3mf(path, [(name, pv, pt, base), (name + "_logo", iv, it, accent)], name)
    return len(ks)
