"""SA-01 spool adapter: a press-fit ring that brings a 195.5 mm spool up to the 199 mm a Creality CFS
grips well.

Design frame = print pose: the ring's axis is Z, the lip lies on the bed (z = 0 .. LIP_T) and the band
rises from it. Mounted, the lip sits on the outer face of the spool's flange, the band wraps the rim, and
the bed face (z = 0) faces outwards with the logo on it. See docs/design.md for the reasoning behind every
number.

    r ->        R_LIP_IN      R_TIP R_RIM R_BORE  R_OUT
                   |            |    |    |      |
    z = H  ........|............|....|....+------+   <- band entry (lead-in cone + chamfer)
                   |            |  ribs   |      |
                   |   flange   |<>|      | band |   <- rolls on the CFS rollers (OD 199)
    z = LIP_T      +============|==+======+      |
    z = 0          +--- lip / logo tab ----------+   <- bed face = outer face, logo inlaid 0.6 mm
"""
from __future__ import annotations

import math

import cadquery as cq

import logo

# -------------------------------------------------------------------------------------------- inputs
RIM_D = 195.5          # measured (user, 2026-11-24): Filamentor spool, flange outside diameter
OD = 199.0             # target (user, 2026-11-24): the Creality spool that runs well in the CFS
                       # (Creality lists 197-202 mm for the CFS; 195.5 is below that range)
FLANGE_T = 3.3         # measured (user, 2026-11-25): Filamentor flange thickness at the rim

# --------------------------------------------------------------------------------- design values (mm)
INTERFERENCE = 0.20    # rib tips vs the rim, on the diameter: the ring stretches this much when fitted
XY_COMP = 0.25         # %: the 3MF is this much larger in X and Y than the model, for the printer's shrinkage.
                       # First print with 0 (v0.1.1, user 2026-11-25): "muito apertado"; 0.25 % opens the rib
                       # tips by 0.49 mm on the diameter; confirmed by the v0.2.0 print ("O tamanho ficou bom")
RIB_N = 60             # axial crush ribs on the bore, one every 6 deg
RIB_H = 0.35           # rib height above the bore
RIB_TIP_W = 0.6        # flat tip width (printable: > one 0.4 mm line)
RIB_BASE_W = 1.6
LIP_T = 1.2            # lip / tab thickness: the only width the adapter adds to the spool, per side
LIP_DEPTH = 3.0        # how far the lip reaches inside the rim, on the flange's outer face
HOOK_N = 5             # snap hooks on the band's entry edge, one every 72 deg, the logo tab midway between two
HOOK_H = 0.5           # how far a hook reaches behind the rim, radially (user, 2026-11-25: "5 pequenos dentinhos";
                       # the v0.3.0 print fits: "Ficou bom")
HOOK_W = 6.0           # hook width at its tip
HOOK_CLEAR = 0.1       # axial clearance between the flange's inner face and the hook's flat catch face
HOOK_LAND = 0.4        # straight land at the hook tip, above the catch face; then a <= 45 deg ramp to the edge
LAYER = 0.2            # layer height: the catch face and the band's top sit on layer boundaries
LEAD_L = 1.4           # lead-in on the rib tips at the entry edge
ENTRY_C = 0.4          # chamfer on the bore at the entry edge
EDGE_C = 0.4           # chamfer on the outside edges and on the bed-face outline

LOGO_H = 13.0          # logo height: 40 mm wide, thinnest stroke 0.84 mm
LOGO_TOP = 96.0        # radius of the logo's top edge (letters point outwards, to the rim); follows the rim
TAB_MARGIN = 2.5       # tab edge to logo
TAB_CUT = 3.0          # 45 deg cut corners of the tab
LIVERY_DEPTH = 0.6     # logo inlay depth: 3 layers of 0.2 mm (house standard)
MIN_STROKE = 0.8       # thinnest stroke or gap allowed on a face that prints on the bed
FACE_MARGIN = 1.0      # logo kept this far inside the flat bed face (clear of every chamfer)

BED = (256.0, 256.0)   # Creality Hi 260 x 260, minus 4 mm for a skirt
PETG_DENSITY = 1.27    # g/cm3, for the mass estimate

# ------------------------------------------------------------------------------------------- derived
def _layer_ceil(z):
    return math.ceil(z / LAYER - 1e-6) * LAYER


def configure(rim_d=None, od=None, interference=None, comp=None, flange_t=None):
    """Set the inputs (for another spool: python build.py --rim 194.8 --od 199 --flange 2.5) and derive
    the rest."""
    global RIM_D, OD, INTERFERENCE, XY_COMP, FLANGE_T, R_OUT, R_RIM, R_TIP, R_BORE, R_LIP_IN, H, BAND_L, BAND_T
    global LOGO_W, TAB_W, TAB_Y, LOGO_TOP, Z_CATCH, R_HOOK
    RIM_D = RIM_D if rim_d is None else rim_d
    OD = OD if od is None else od
    INTERFERENCE = INTERFERENCE if interference is None else interference
    XY_COMP = XY_COMP if comp is None else comp
    FLANGE_T = FLANGE_T if flange_t is None else flange_t
    R_OUT = OD / 2
    R_RIM = RIM_D / 2
    R_TIP = (RIM_D - INTERFERENCE) / 2
    R_BORE = R_TIP + RIB_H
    R_LIP_IN = R_RIM - LIP_DEPTH
    # hooks: flat catch face just above the flange's inner face, tip HOOK_H inside the rim, then a land and
    # a 45 deg ramp up to the band's entry edge (the band is as long as the hooks need)
    Z_CATCH = _layer_ceil(LIP_T + FLANGE_T + HOOK_CLEAR)
    R_HOOK = R_RIM - HOOK_H
    H = _layer_ceil(Z_CATCH + HOOK_LAND + (R_BORE + ENTRY_C - R_HOOK))
    BAND_L = H - LIP_T
    BAND_T = R_OUT - R_BORE
    LOGO_TOP = R_RIM - 1.75                       # 96.0 for the 195.5 mm rim
    LOGO_W = logo.width(LOGO_H)
    TAB_W = LOGO_W + 2 * TAB_MARGIN
    TAB_Y = LOGO_TOP - LOGO_H - TAB_MARGIN      # straight inner edge of the tab


configure()


# ------------------------------------------------------------------------------------------ geometry
def _polar(r, a):
    return (r * math.cos(a), r * math.sin(a))


def bore_outline():
    """Closed polyline of the ribbed bore. Ribs are centred between the 6 deg marks so that none sits
    on the tab's centre line (cosmetic only)."""
    pitch = 2 * math.pi / RIB_N
    a_base = (RIB_BASE_W / 2) / R_BORE
    a_tip = (RIB_TIP_W / 2) / R_TIP
    pts = []
    for i in range(RIB_N):
        c = (i + 0.5) * pitch
        pts += [_polar(R_BORE, c - a_base), _polar(R_TIP, c - a_tip), _polar(R_TIP, c + a_tip),
                _polar(R_BORE, c + a_base)]
        gap0, gap1 = c + a_base, c + pitch - a_base
        for k in range(1, 4):                    # the bore between ribs, as 4 chords (0.007 mm sag)
            pts.append(_polar(R_BORE, gap0 + (gap1 - gap0) * k / 4))
    return pts


def tab_outline():
    """The logo tab in the lip plane, centred on +Y; its top runs into the lip."""
    w, y0, c = TAB_W / 2, TAB_Y, TAB_CUT
    top = R_LIP_IN + 3.0
    return [(-w, top), (-w, y0 + c), (-w + c, y0), (w - c, y0), (w, y0 + c), (w, top)]


def _revolve(profile):
    """Solid of revolution about Z of a closed (r, z) profile."""
    return cq.Workplane("XZ").polyline(profile).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()


def hook_angles():
    """Hook centres (rad): one every 360/HOOK_N deg, the logo tab (+Y) midway between two."""
    step = 2 * math.pi / HOOK_N
    return [math.pi / 2 + step / 2 + k * step for k in range(HOOK_N)]


def hook_profile():
    """(r, z) section of a hook: flat catch face, land at the tip, ramp to the band's entry edge. Its outer
    side runs 0.6 mm into the band wall for the union."""
    r_wall = R_BORE + 0.6
    return [(r_wall, Z_CATCH), (R_HOOK, Z_CATCH), (R_HOOK, Z_CATCH + HOOK_LAND), (R_BORE + ENTRY_C, H), (r_wall, H)]


def hooks():
    """The HOOK_N snap hooks, each HOOK_W wide at its tip (radial side faces)."""
    full = _revolve(hook_profile())
    half = HOOK_W / 2 / R_HOOK
    out = []
    for a in hook_angles():
        wedge = (cq.Workplane("XY").workplane(offset=-1)
                 .polyline([(0, 0), _polar(R_OUT + 5, a - half), _polar(R_OUT + 5, a + half)]).close()
                 .extrude(H + 2).val())
        out.append(full.intersect(wedge))
    return out


def logo_to_xy(x, y):
    """SVG point -> model XY. The logo is read from below (the bed face is the outer face when
    mounted), so it is mirrored: the reader's right is -X. Letter tops point to +Y (the rim)."""
    k = LOGO_H / logo.VIEW_H
    u = (x - logo.VIEW_W / 2) * k
    v = LOGO_TOP - y * k
    return (-u, v)


def ring_body():
    """The ring without the logo pocket."""
    body = (cq.Workplane("XY").circle(R_OUT).extrude(H).val()
            .cut(cq.Workplane("XY").workplane(offset=-1).polyline(bore_outline()).close().extrude(H + 2).val()))
    lip = (cq.Workplane("XY").circle(R_BORE + 0.2).circle(R_LIP_IN).extrude(LIP_T).val())
    # The tab's straight sides run up into the band; clipped to the bore so its top corners stay inside
    # the ring (unclipped they stood 0.8 mm proud of the rolling surface, v0.1.0).
    tab = (cq.Workplane("XY").polyline(tab_outline()).close().extrude(LIP_T).val()
           .intersect(cq.Workplane("XY").circle(R_BORE + 0.2).extrude(LIP_T).val()))
    body = body.fuse(lip).fuse(tab).clean()

    # Lead-in: one cone through the rib tips LEAD_L below the entry edge and ENTRY_C outside the bore at
    # the edge, so the ribs ramp up and the bore gets its entry chamfer in the same cut.
    slope = (R_BORE + ENTRY_C - R_TIP) / LEAD_L
    z_lo = H - LEAD_L - 0.5
    cone = _revolve([(0, z_lo), (R_TIP - 0.5 * slope, z_lo), (R_BORE + ENTRY_C, H),
                     (R_BORE + ENTRY_C + slope, H + 1), (0, H + 1)])
    body = body.cut(cone)
    # snap hooks on the entry edge (added after the lead-in cut: they carry their own ramp)
    for hook in hooks():
        body = body.fuse(hook)
    body = body.clean()
    # outside edges: entry edge and bed edge
    body = body.cut(_revolve([(R_OUT - EDGE_C, H + 0.01), (R_OUT + 0.01, H - EDGE_C - 0.01),
                              (R_OUT + 1, H - EDGE_C - 0.01), (R_OUT + 1, H + 1), (R_OUT - EDGE_C, H + 1)]))
    body = body.cut(_revolve([(R_OUT - EDGE_C, -0.01), (R_OUT + 0.01, EDGE_C + 0.01),
                              (R_OUT + 1, EDGE_C + 0.01), (R_OUT + 1, -1), (R_OUT - EDGE_C, -1)]))
    # bed-face chamfer along the lip's inner edge and the tab outline (seen as a 45 deg bevel, and it
    # keeps the first layer free of elephant's foot there)
    inner = [e for e in body.Edges()
             if abs(e.BoundingBox().zmin) < 1e-6 and abs(e.BoundingBox().zmax) < 1e-6
             and max(math.hypot(v.X, v.Y) for v in e.Vertices()) < R_BORE]
    body = body.chamfer(EDGE_C, None, inner)
    return body


def build():
    """Returns (ring with the logo pocket, logo inlay), both in print pose."""
    body = ring_body()
    mark = logo.logo_solid(LOGO_H, -1.0, LIVERY_DEPTH, logo_to_xy)
    inlay = mark.intersect(cq.Workplane("XY").rect(4 * R_OUT, 4 * R_OUT).extrude(LIVERY_DEPTH).val())
    ring = body.cut(mark)
    return ring, inlay


# -------------------------------------------------------------------------------------------- checks
def flat_bed_face(body):
    """The flat part of the bed face (z = 0) of the un-pocketed ring."""
    faces = [f for f in body.Faces()
             if f.geomType() == "PLANE" and abs(f.BoundingBox().zmax) < 1e-6 and f.BoundingBox().xlen > OD / 2]
    assert len(faces) == 1, f"expected one flat bed face, found {len(faces)}"
    return faces[0]


def checks(ring, inlay, body=None):
    """Design checks; returns a list of (name, ok, detail)."""
    body = body or ring_body()
    out = []

    def check(name, ok, detail):
        out.append((name, bool(ok), detail))

    bb = ring.BoundingBox()
    check("outside diameter", abs(bb.xlen - OD) < 0.02 and abs(bb.ylen - OD) < 0.02,
          f"{bb.xlen:.2f} x {bb.ylen:.2f} mm (target {OD})")
    # the bounding box alone misses features off the X/Y axes (the v0.1.0 tab corners): test the volume
    rolling = cq.Solid.makeCylinder(R_OUT + 1e-3, H + 2, cq.Vector(0, 0, -1))
    proud = ring.cut(rolling).Volume() + inlay.cut(rolling).Volume()
    check("nothing outside the rolling surface", proud < 1e-6, f"{proud:.4f} mm3 beyond D {OD}")
    check("rim inside the bore, ribs bite", R_TIP < R_RIM < R_BORE,
          f"rib tips D {2 * R_TIP:.2f} < rim D {RIM_D} < bore D {2 * R_BORE:.2f}")
    check("band wall", BAND_T >= 1.4, f"{BAND_T:.2f} mm (>= 1.4, about 3.5 lines of 0.42 mm)")
    check("ribs printable", RIB_TIP_W >= 0.45 and RIB_H >= 0.2, f"tip {RIB_TIP_W} mm, height {RIB_H} mm")
    check("hoop strain when fitted", INTERFERENCE / RIM_D < 0.004,
          f"{100 * INTERFERENCE / RIM_D:.2f} % (PETG and PLA stay elastic far beyond 1 %)")
    k = xy_scale()
    check("print compensation", 0 <= XY_COMP <= 1.0 and 197.0 <= OD * k <= 202.0,
          f"3MF {XY_COMP:g} % larger in X/Y: outside D {OD * k:.2f}, rib tips D {2 * R_TIP * k:.2f} as drawn "
          f"(CFS 197-202)")
    check("fits the bed", bb.xlen * k <= BED[0] and bb.ylen * k <= BED[1],
          f"{bb.xlen * k:.0f} x {bb.ylen * k:.0f} on {BED}")
    check("height", abs(bb.zlen - H) < 0.01, f"{bb.zlen:.2f} mm")

    # hooks
    flange_top = LIP_T + FLANGE_T
    check("hooks catch behind the flange", 0.05 <= Z_CATCH - flange_top <= 0.3 and R_HOOK < R_RIM,
          f"catch face at z {Z_CATCH:.2f} = lip {LIP_T} + flange {FLANGE_T} + {Z_CATCH - flange_top:.2f}; "
          f"tip {HOOK_H} mm behind the rim (D {2 * R_HOOK:.2f})")
    check("ribs grip the whole flange", H - LEAD_L >= flange_top,
          f"full rib height up to z {H - LEAD_L:.2f} >= flange top {flange_top:.2f}")

    def inside(r, z0, z1, shape=ring):
        return shape.intersect(cq.Solid.makeCylinder(r, z1 - z0, cq.Vector(0, 0, z0))).Volume()

    seat = inside(R_TIP - 0.01, LIP_T + 0.01, Z_CATCH - 0.01)
    check("flange seat free", seat < 1e-6,
          f"{seat:.4f} mm3 of ring inside the rib tips between the lip and the hooks")
    r_in = R_TIP - 0.01                             # inside the rib tips: only the hooks reach there
    tips = inside(r_in, Z_CATCH + 0.01, Z_CATCH + HOOK_LAND - 0.01)
    expect = HOOK_N * (HOOK_W / 2 / R_HOOK) * (r_in ** 2 - R_HOOK ** 2) * (HOOK_LAND - 0.02)
    check("hooks present", abs(tips / expect - 1) < 0.02,
          f"{HOOK_N} hooks, {tips:.3f} mm3 inside the rib tips at the land (expected {expect:.3f})")
    ramp = math.degrees(math.atan2(R_BORE + ENTRY_C - R_HOOK, H - Z_CATCH - HOOK_LAND))
    check("hooks printable", R_BORE - R_HOOK <= 1.0 and ramp <= 45.0,
          f"flat catch overhang {R_BORE - R_HOOK:.2f} mm (<= 1.0), ramp {ramp:.0f} deg from vertical")
    check("snap-over strain", 2 * HOOK_H / RIM_D < 0.01,
          f"{200 * HOOK_H / RIM_D:.2f} % if all hooks pass at once (elastic); one side first needs far less")
    check("logo strokes", logo.min_stroke(LOGO_H) >= MIN_STROKE,
          f"thinnest {logo.min_stroke(LOGO_H):.2f} mm (>= {MIN_STROKE})")

    # the logo stays FACE_MARGIN inside the flat bed face: clear of every chamfer and edge
    face = flat_bed_face(body)
    outer = face.outerWire().offset2D(-FACE_MARGIN)[0]
    holes = [w.offset2D(FACE_MARGIN)[0] for w in face.innerWires()]
    safe = cq.Solid.extrudeLinear(cq.Face.makeFromWires(outer, holes), cq.Vector(0, 0, LIVERY_DEPTH + 1)) \
        .moved(cq.Location(cq.Vector(0, 0, -0.5)))
    stray = inlay.cut(safe).Volume()
    check("logo inside the flat bed face", stray < 1e-6,
          f"{stray:.4f} mm3 of logo within {FACE_MARGIN} mm of an edge")
    ib = inlay.BoundingBox()
    check("logo inlay slab", abs(ib.zmin) < 1e-6 and abs(ib.zmax - LIVERY_DEPTH) < 1e-6,
          f"z {ib.zmin:.2f}..{ib.zmax:.2f} mm, {ib.xlen:.1f} x {ib.ylen:.1f} mm")
    overlap = ring.intersect(inlay).Volume()
    check("ring and logo do not overlap", overlap < 1e-6, f"{overlap:.5f} mm3")
    check("solids valid", ring.isValid() and inlay.isValid(), "OCC validity")
    return out


def xy_scale():
    """Factor applied to X and Y when the 3MF is written (the model itself is the fitted size)."""
    return 1 + XY_COMP / 100


def mass_g(shape):
    return shape.Volume() / 1000 * PETG_DENSITY
