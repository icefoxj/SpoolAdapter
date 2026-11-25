"""Build SA-01: model, checks, the two-colour 3MFs and the renders, for both variants.

    python build.py              checks + 3MFs + renders (with hooks and without)
    python build.py --no-render  checks + 3MFs (what CI runs)
    python build.py --variant no-hooks
                                 only one variant (hooks | no-hooks | both, the default)
    python build.py --rim 194.8 --od 199 --flange 2.5
                                 another spool: checks + its own 3MFs (the renders show the default)
    python build.py --comp 0.35  looser (more shrinkage compensation); --comp 0.15 tighter

Outputs (repository root):
    3mf/SpoolAdapter_195.5-to-199mm_2color.3mf           with the five snap hooks (6.2 mm), print pose
    3mf/SpoolAdapter_195.5-to-199mm_no-hooks_2color.3mf  without hooks (5.2 mm, the v0.2.0 ring)
    docs/img/sa01_*.png                                  renders and the dimensioned profiles
"""
from __future__ import annotations

import argparse
import math
import os
import sys
import time

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import export3mf  # noqa: E402
import spool_adapter as sa  # noqa: E402

REPO = os.path.normpath(os.path.join(HERE, ".."))
IMG = os.path.join(REPO, "docs", "img")


DEFAULT_FIT = (sa.INTERFERENCE, sa.XY_COMP)
VARIANTS = {"hooks": True, "no-hooks": False}


def out_3mf():
    name = f"SpoolAdapter_{sa.RIM_D:g}-to-{sa.OD:g}mm_2color.3mf"
    if not sa.HOOKS:
        name = name.replace("_2color", "_no-hooks_2color")
    if abs(sa.INTERFERENCE - DEFAULT_FIT[0]) > 1e-9:
        name = name.replace("_2color", f"_fit{sa.INTERFERENCE:g}_2color")
    if abs(sa.XY_COMP - DEFAULT_FIT[1]) > 1e-9:
        name = name.replace("_2color", f"_comp{sa.XY_COMP:g}_2color")
    return os.path.join(REPO, "3mf", name)

# The spool in the renders is an illustration: only its diameter and flange thickness are measured.
SPOOL_W = 60.0         # outside width over the flanges (typical 1 kg spool)
FLANGE_T = sa.FLANGE_T
CORE_D = 90.0
HUB_D = 55.0
FILL_D = 172.0


def log(*a):
    print(*a, flush=True)


# ------------------------------------------------------------------------------------------- renders
def spool():
    """Flanges, core and filament of a generic spool, axis along X, centred on the origin."""
    def cyl(r, x0, x1):
        return cq.Solid.makeCylinder(r, x1 - x0, cq.Vector(x0, 0, 0), cq.Vector(1, 0, 0))

    w = SPOOL_W / 2
    flanges = [cyl(sa.R_RIM, x0, x0 + FLANGE_T).cut(cyl(HUB_D / 2, x0 - 1, x0 + FLANGE_T + 1))
               for x0 in (-w, w - FLANGE_T)]
    core = cyl(CORE_D / 2, -w + FLANGE_T, w - FLANGE_T).cut(cyl(HUB_D / 2, -w, w))
    fill = cyl(FILL_D / 2, -w + FLANGE_T, w - FLANGE_T).cut(cyl(CORE_D / 2, -w, w))
    return flanges, core, fill


def ring_locations():
    """Ring design frame -> its place on the right (+X) and left flange: lip on the flange's outer face,
    band over the rim, tab at the top."""
    w = SPOOL_W / 2
    right = cq.Location(cq.Plane(cq.Vector(w + sa.LIP_T, 0, 0), cq.Vector(0, -1, 0), cq.Vector(-1, 0, 0)))
    left = cq.Location(cq.Plane(cq.Vector(-w - sa.LIP_T, 0, 0), cq.Vector(0, 1, 0), cq.Vector(1, 0, 0)))
    return right, left


def renders(ring, inlay):
    import render as rd
    flanges, core, fill = spool()
    right, left = ring_locations()
    on_spool = ([(f, None, "spool") for f in flanges] + [(core, None, "spool"), (fill, None, "filament")]
                + [(s, loc, c) for loc in (right, left) for s, c in ((ring, "graphite"), (inlay, "livery"))])

    def out(name):
        p = os.path.join(IMG, name)
        log(f"   render -> {os.path.relpath(p, REPO)}")
        return p

    def section(path):
        """Section at the first hook's angle (in the variant without hooks: the same place, for comparison),
        with the flange: ring + flange, rotated to +Y."""
        a = 90.0 - math.degrees(sa.hook_angles()[0])
        rot = cq.Location(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), a)
        window = cq.Solid.makeBox(7, 15, 12, cq.Vector(-7, 86, -2))
        flange = cq.Solid.makeCylinder(sa.R_RIM, FLANGE_T, cq.Vector(0, 0, sa.LIP_T))
        cut = [(ring.moved(rot).intersect(window), None, "graphite"),
               (flange.intersect(window), None, "spool")]
        rd.render(cut, path, cam=(80, 112, 34), focal=(-2, 94, 2.5), zoom=1.2, tol=0.01)

    if not sa.HOOKS:
        # the variant without hooks: its section and its profile
        section(out("sa01_nohooks_section.png"))
        profile(out("sa01_nohooks_profile.png"))
        return

    # hero: the spool with both rings, seen from the logo side
    rd.render(on_spool, out("sa01_hero.png"), cam=(430, -300, 230), focal=(0, 0, 0), zoom=1.25)
    # the ring alone, outer face (the bed face, where the logo is)
    part = [(ring, None, "graphite"), (inlay, None, "livery")]
    rd.render(part, out("sa01_ring.png"), cam=(60, -260, -330), focal=(0, 0, 0), up=(0, 1, 0), zoom=1.3)
    # close-up of the bore: a snap hook between the crush ribs, and the lead-in (print pose, from inside)
    rd.render(part, out("sa01_ribs.png"), cam=(-16, -70, 28), focal=(0, -97.5, 3.6), up=(0, 0, 1), zoom=9.0,
              tol=0.01)
    # close-up of the logo tab, from outside
    rd.render(part, out("sa01_tab.png"), cam=(25, 20, -120), focal=(0, 89, 0), up=(0, 1, 0), zoom=3.4)
    # section through a hook: the flange held between the lip and the hook
    section(out("sa01_section.png"))
    # print pose on the Creality Hi plate (260 x 260)
    bed = cq.Solid.makeBox(260, 260, 2, cq.Vector(-130, -130, -2))
    rd.render([(bed, None, "bed")] + part, out("sa01_print.png"), cam=(0, -330, 330), focal=(0, 0, 0), zoom=1.2,
              edges=False)
    profile(out("sa01_profile.png"))


def profile(path):
    """Dimensioned half-section of the ring on the flange (mech look): through a hook, or through a rib in
    the variant without hooks."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle

    G, Y, INK, WARN = "#303236", "#FFCC00", "#15171A", "#FF5533"
    fig, ax = plt.subplots(figsize=(10, 7.4), dpi=150)
    fig.patch.set_facecolor("white")
    e, c = sa.EDGE_C, sa.ENTRY_C
    if sa.HOOKS:
        bore = [(sa.R_HOOK, sa.Z_CATCH + sa.HOOK_LAND), (sa.R_HOOK, sa.Z_CATCH), (sa.R_BORE, sa.Z_CATCH),
                (sa.R_BORE, sa.LIP_T)]
    else:
        bore = [(sa.R_TIP, sa.H - sa.LEAD_L), (sa.R_TIP, sa.LIP_T)]
    ring = ([(sa.R_LIP_IN + e, 0), (sa.R_OUT - e, 0), (sa.R_OUT, e), (sa.R_OUT, sa.H - e), (sa.R_OUT - e, sa.H),
             (sa.R_BORE + c, sa.H)] + bore + [(sa.R_LIP_IN, sa.LIP_T), (sa.R_LIP_IN, e)])
    ax.add_patch(Rectangle((89.5, sa.LIP_T), sa.R_RIM - 89.5, FLANGE_T, fc="#C9CCD1", ec="#7A7E85", lw=1, zorder=1))
    ax.add_patch(Polygon(ring, closed=True, fc=G, ec=INK, lw=1.2, zorder=2))
    ax.add_patch(Rectangle((sa.R_LIP_IN + 1.5, 0), 2.2, sa.LIVERY_DEPTH, fc=Y, ec=INK, lw=0.8, zorder=3))
    if sa.HOOKS:
        # the ribs, between the hooks: tips dashed
        ax.plot([sa.R_TIP, sa.R_TIP], [sa.LIP_T, sa.Z_CATCH - 0.05], ls="--", lw=1.0, color=WARN, zorder=3)
        ax.annotate(f"hook: {sa.HOOK_H:g} behind the rim,\n"
                    f"catch {sa.Z_CATCH - sa.LIP_T - sa.FLANGE_T:.1f} above the flange",
                    (sa.R_HOOK + 0.05, sa.Z_CATCH + 0.2), (90.0, 5.55), fontsize=8.5, color=INK, va="center",
                    arrowprops=dict(arrowstyle="->", lw=0.8, color=INK))
    else:
        # section through a rib: the bore between the ribs dashed
        ax.plot([sa.R_BORE, sa.R_BORE], [sa.LIP_T, sa.H - 0.75], ls="--", lw=0.9, color="#9AA0A6", zorder=3)
    # the CFS roller's axis is parallel to the spool's, so in this section it is a band along z
    ax.add_patch(Rectangle((sa.R_OUT, -1.3), 2.4, sa.H + 2.6, fc="#EEF0F2", ec="#9AA0A6", lw=1, ls=":", zorder=1))
    ax.text(sa.R_OUT + 1.2, sa.H + 1.6, "CFS roller\n(schematic)", fontsize=8, color="#7A7E85", ha="center")
    ax.text(90.0, sa.LIP_T + 0.25, f"spool flange: Ø {sa.RIM_D:g}, {sa.FLANGE_T:g} thick (measured)",
            fontsize=8, color="#55595F", va="bottom")
    ax.text(sa.R_LIP_IN + 2.6, -0.95, "logo inlay 0.6 (on the tab)", fontsize=8, ha="center", color=INK)

    def dim_h(x0, x1, y, text, above=True):
        ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", lw=0.8, color=INK))
        ax.text((x0 + x1) / 2, y + (0.18 if above else -0.18), text, ha="center",
                va="bottom" if above else "top", fontsize=8.5, color=INK)

    def dim_v(x, y0, y1, text, left=False):
        ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<->", lw=0.8, color=INK))
        ax.text(x + (-0.15 if left else 0.15), (y0 + y1) / 2, text, ha="right" if left else "left",
                va="center", fontsize=8.5, color=INK)

    for r, label, y, col in ((sa.R_OUT, f"Ø {sa.OD:.1f}  outside (rolls on the CFS)", 9.3, INK),
                             (sa.R_BORE, f"Ø {2 * sa.R_BORE:.2f}  bore " +
                              ("(at the hooks)" if sa.HOOKS else "between ribs"), 8.6, "#55595F"),
                             (sa.R_RIM, f"Ø {sa.RIM_D:.2f}  spool rim (measured)", 7.9, "#55595F"),
                             (sa.R_TIP, f"Ø {2 * sa.R_TIP:.2f}  rib tips ({sa.RIB_N} ribs, {sa.RIB_H} high)", 7.2, WARN)):
        ax.plot([r, r], [sa.H + 0.1, y], lw=0.6, color=col)
        ax.text(r - 0.08, y, label, ha="right", va="center", fontsize=8.5, color=col)
    dim_v(sa.R_OUT + 3.3, 0, sa.LIP_T, f"{sa.LIP_T} lip (adds to width)")
    dim_v(sa.R_OUT + 3.3, sa.LIP_T, sa.H, f"{sa.BAND_L:.1f} band")
    for z in (0, sa.LIP_T, sa.H):
        ax.plot([sa.R_OUT + 0.1, sa.R_OUT + 3.5], [z, z], lw=0.5, color="#9AA0A6", zorder=1)
    dim_h(sa.R_LIP_IN, sa.R_RIM, -1.9, f"{sa.LIP_DEPTH} lip depth", above=False)
    dim_h(sa.R_BORE, sa.R_OUT, -1.9, f"{sa.BAND_T:.2f} wall", above=False)
    if sa.HOOKS:
        ax.text(sa.R_HOOK - 0.35, sa.Z_CATCH + 1.2, "lead-in ramp", fontsize=7.5, ha="right", color="#55595F")
    else:
        ax.text(sa.R_TIP - 0.2, sa.H - 0.2, "lead-in", fontsize=7.5, ha="right", color="#55595F")
    ax.text(89.5, -3.6, f"Interference {sa.INTERFERENCE:.2f} mm on the diameter: the closed ring stretches "
            f"{100 * sa.INTERFERENCE / sa.RIM_D:.2f} % and clamps the rim. Design values; dimensions in mm.",
            fontsize=8, color="#55595F")
    ax.text(89.5, -4.3, f"Fitted sizes. The 3MF is {sa.XY_COMP:g} % larger in X/Y for the printer's shrinkage "
            f"(outside Ø {sa.OD * sa.xy_scale():.2f}, rib tips Ø {2 * sa.R_TIP * sa.xy_scale():.2f} as drawn): "
            f"the first print, without it, was too tight.", fontsize=8, color="#55595F")
    # title band (mech look): unit code knocked out of a yellow band with a 45 deg cut
    ax.add_patch(Polygon([(89.5, 11.0), (92.4, 11.0), (93.0, 11.6), (89.5, 11.6)], closed=True, fc=Y, ec="none",
                         clip_on=False))
    ax.text(89.65, 11.3, "SA-01", fontsize=11, fontweight="bold", color=INK, va="center")
    title = "PROFILE THROUGH A HOOK" if sa.HOOKS else "NO HOOKS  ·  PROFILE THROUGH A RIB"
    ax.text(93.3, 11.3, f"SPOOL ADAPTER  ·  {title}", fontsize=11, fontweight="bold", color=INK, va="center")
    ax.set_xlim(89.3, 107.8)
    ax.set_ylim(-4.8, 11.9)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--no-export", action="store_true")
    ap.add_argument("--rim", type=float, help=f"measured flange diameter of the spool (default {sa.RIM_D})")
    ap.add_argument("--od", type=float, help=f"outside diameter wanted (default {sa.OD}; CFS: 197-202)")
    ap.add_argument("--interference", type=float, help=f"rib tips vs rim, on the diameter (default {sa.INTERFERENCE})")
    ap.add_argument("--flange", type=float, help=f"measured flange thickness at the rim (default {sa.FLANGE_T})")
    ap.add_argument("--comp", type=float,
                    help=f"%% larger in X/Y in the 3MF, for print shrinkage (default {sa.XY_COMP}; looser = more)")
    ap.add_argument("--variant", choices=[*VARIANTS, "both"], default="both",
                    help="with the snap hooks, without them, or both (default)")
    args = ap.parse_args()
    custom = any(v is not None for v in (args.rim, args.od, args.interference, args.comp, args.flange))
    sa.configure(args.rim, args.od, args.interference, args.comp, args.flange)

    t0 = time.time()
    names = list(VARIANTS) if args.variant == "both" else [args.variant]
    for name in names:
        if build_variant(VARIANTS[name], args, custom):
            return 1
    log(f"done in {time.time() - t0:.0f} s")
    return 0


def build_variant(hooks, args, custom):
    """Model, checks, 3MF and renders of one variant; returns the number of failed checks."""
    sa.configure(hooks=hooks)
    log(f"SA-01 spool adapter, {'with ' + str(sa.HOOK_N) + ' snap hooks' if sa.HOOKS else 'no hooks'}")
    log(f"   rim {sa.RIM_D} -> outside {sa.OD} mm, interference {sa.INTERFERENCE} mm, {sa.RIB_N} ribs, "
        f"lip {sa.LIP_T} mm, band {sa.BAND_L:.1f} mm (height {sa.H:.1f}), flange {sa.FLANGE_T} mm, "
        f"3MF +{sa.XY_COMP:g} % in X/Y")
    body = sa.ring_body()
    ring, inlay = sa.build()
    results = sa.checks(ring, inlay, body)
    log("checks")
    for name, ok, detail in results:
        log(f"   {'ok  ' if ok else 'FAIL'} {name}: {detail}")
    failed = [n for n, ok, _ in results if not ok]
    log(f"   mass {sa.mass_g(ring) + sa.mass_g(inlay):.1f} g in PETG (ring {sa.mass_g(ring):.1f} g, "
        f"logo {sa.mass_g(inlay):.2f} g); two rings per spool; hoop section {sa.hoop_section(body):.2f} mm2")
    if failed:
        log(f"{len(failed)} check(s) failed: {', '.join(failed)}")
        return len(failed)
    if not args.no_export:
        path = out_3mf()
        n = export3mf.two_colour(path, "SpoolAdapter", ring, inlay, xy_scale=sa.xy_scale())
        log(f"3mf -> {os.path.relpath(path, REPO)} (logo in the first {n} layers)")
    if custom:
        log("renders skipped: they document the default adapter")
    elif not args.no_render:
        log("renders")
        renders(ring, inlay)
    return 0


if __name__ == "__main__":
    sys.exit(main())
