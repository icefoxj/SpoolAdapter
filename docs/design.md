# SA-01 design

The contract for the spool adapter: what it must do, why it looks the way it does, every number and where it
comes from. The CAD (`cad/spool_adapter.py`) implements this page; when one changes, the other changes with it.

**Status (2026-11-24): designed and checked in CAD, not printed yet.** Only two numbers are measured (the two
spool diameters, by the user). Everything else is a design value or an estimate, and says so.

## 1. Problem and requirements

The Creality Filament System (CFS) holds each spool on rollers that touch the rims of its two flanges. Creality
lists spools of **197–202 mm** diameter and **42–68 mm** width for the CFS
([CFS filament compatibility](https://wiki.creality.com/en/cfs/cfs-filament-compatibility)) and warns that a
spool that is too small can slip and turn unsteadily, which breaks retraction
([CFS 2 precautions](https://wiki.creality.com/en/cfs-2/supported-filaments-precautions)).

User requirements (2026-11-24):

| # | Requirement | Source |
|---|---|---|
| R1 | Filamentor spools measure **195.5 mm** and run loose in the CFS; the Creality spools that work measure **199 mm**. Adapt the Filamentor spool to 199 mm. | user, measured |
| R2 | The adapter must hold firmly and **must not slip** on the spool. | user |
| R3 | A small **tab with the 3DTesla logo**, in **two colours**, delivered as a **3MF** (no STL). | user |
| R4 | Public GitHub repository `SpoolAdapter` with README and CLAUDE.md. | user |

Derived requirements:

| # | Requirement | Why |
|---|---|---|
| D1 | The rolling surface is a smooth, continuous cylinder, Ø 199.0 mm, with no joint or step. | the CFS rollers run on it every rewind |
| D2 | Add as little width as possible: **1.2 mm per side** (2.4 mm per spool). | the CFS accepts at most 68 mm |
| D3 | Nothing may reach inside the rim on the filament side. | a full spool's filament comes close to the rim |
| D4 | Printed only, no hardware, no glue. One part, printed twice (one per flange). | simple to make and to fit |
| D5 | Fits the Creality Hi plate (260 × 260 mm) and the logo prints in the first layers (CFS colour change). | house printer |

## 2. Concept

**A closed ring with an L section, pressed onto the rim.** The band wraps the rim and is the new rolling surface;
the lip sits on the flange's outer face and sets the ring's axial position; 60 axial crush ribs on the bore are
0.20 mm (on the diameter) tighter than the rim, so the closed ring stretches 0.10 % and clamps the rim all round.

![Profile](img/sa01_profile.png)

Why this and not the alternatives:

| Concept | Verdict |
|---|---|
| **Closed press-fit ring (chosen)** | No joint on the rolling surface (D1). The hoop stress of a closed ring clamps the rim evenly: a small interference gives a large grip (§5). One part, no hardware. Fit depends on print accuracy: handled by ribs, a small nominal interference and an XY-scale adjustment (§8). |
| Split C-ring (expand and snap on) | A gap on the rolling surface, and the open ring is so flexible that it clamps almost nothing: it would slip (R2). |
| U-channel ring gripping both faces | Cannot go onto a solid flange in one piece; in segments it has joints on the rolling surface; its inner lip reaches inside the rim on the filament side (D3); it needs the flange thickness, which is not measured. |
| Clip-on segments | Joints and steps on the rolling surface (D1), several parts to align. |
| Ring with a clamping screw | Grips well, but needs hardware and leaves a bump at the clamp (D1, D4). |
| Plain ring held by glue or tape | Not removable, messy, and tape adds thickness unevenly. |

The band stays outside the rim, so its length does not depend on the flange thickness: any flange up to 4.0 mm
thick is gripped over its full thickness, and on a thinner flange the band simply runs past the inner face (it
stays outside the rim's diameter, clear of the filament).

## 3. Geometry

Design frame = print pose: the ring's axis is Z, the lip lies on the bed (z = 0 … 1.2 mm), the band rises to
z = 5.2 mm. Mounted, the bed face is the outer face of the spool and carries the logo.

- **Band**: Ø 199.0 outside, Ø 196.00 bore, 1.50 mm wall, 5.2 mm long including the lip. Outside edges chamfered
  0.4 mm.
- **Crush ribs**: 60, axial, one every 6°, 0.35 mm high, 0.6 mm flat tip, 1.6 mm base; tips on Ø 195.30. They are
  centred between the 6° marks so that none falls on the tab's centre line.
- **Lead-in**: one cone through the rib tips 1.4 mm below the entry edge and 0.4 mm outside the bore at the edge:
  the ribs ramp up and the bore gets its entry chamfer in the same cut.
- **Lip**: 1.2 mm thick, reaches 3.0 mm inside the rim (to Ø 189.5) on the flange's outer face. Its inner edge and
  the tab outline are chamfered 0.4 mm on the bed face.
- **Logo tab**: 45 mm wide, reaching 14.25 mm beyond the lip (inner edge 17.25 mm inside the rim), 45° cut corners, same 1.2 mm
  thickness, centred on +Y. It carries the logo and gives a place to push or pull when fitting or removing.
- **Logo**: 40.0 × 13.0 mm, inlaid 0.6 mm into the bed face, mirrored in the model so that it reads correctly from
  outside, letter tops towards the rim.

## 4. Parameters

All in `cad/spool_adapter.py`. `M` = measured, `D` = design value, `E` = estimate.

| Name | Value | | Meaning |
|---|---|---|---|
| `RIM_D` | 195.5 mm | M | Filamentor flange outside diameter (user) |
| `OD` | 199.0 mm | M | target outside diameter: the Creality spool that works (user); CFS range 197–202 |
| `INTERFERENCE` | 0.20 mm | D | rib tips vs rim, on the diameter |
| `RIB_N`, `RIB_H` | 60, 0.35 mm | D | crush ribs |
| `RIB_TIP_W`, `RIB_BASE_W` | 0.6, 1.6 mm | D | rib tip (above one 0.4 mm line) and base |
| `LIP_T` | 1.2 mm | D | lip and tab thickness = width added per side |
| `LIP_DEPTH` | 3.0 mm | D | lip reach inside the rim |
| `BAND_L` | 4.0 mm | D | band length past the lip = thickest flange gripped fully |
| `LEAD_L`, `ENTRY_C` | 1.4, 0.4 mm | D | lead-in |
| `EDGE_C` | 0.4 mm | D | chamfers |
| `LOGO_H` | 13.0 mm | D | logo height (thinnest stroke 0.84 mm) |
| `LIVERY_DEPTH` | 0.6 mm | D | logo inlay depth = 3 layers of 0.2 mm (house standard) |
| `MIN_STROKE` | 0.8 mm | D | thinnest stroke allowed on the bed face |
| `FACE_MARGIN` | 1.0 mm | D | logo kept this far from every edge and chamfer |
| derived bore | Ø 196.00 mm | D | rib tips + 2 × rib height |
| derived wall | 1.50 mm | D | (OD − bore) / 2 |
| mass | 9.8 g per ring | E | PETG 1.27 g/cm³, from the CAD volume; two rings per spool |

## 5. Retention (estimates)

Design values: the ring's hoop section is about 11.3 mm² (band 1.5 × 5.2 mm plus lip 3.25 × 1.2 mm, less
chamfers); printed PETG E ≈ 2.0 GPa; friction PETG on a plastic spool μ ≈ 0.3 (estimate).

| Quantity | Value | How |
|---|---|---|
| hoop strain when fitted | 0.10 % | 0.20 / 195.5 |
| hoop stress | 2.0 MPa | E·ε (PETG yields around 50 MPa) |
| hoop force T | 23 N | σ × 11.3 mm² |
| total clamping force on the rim | 146 N | 2π·T |
| torque before the ring turns on the rim | ≈ 4.3 N·m | μ × 146 N × 97.75 mm |
| torque the CFS needs to turn the spool | ≲ 0.3 N·m | filament tension of a few newtons × ≤ 86 mm radius (estimate) |
| force to press the ring on | ≈ 44 N (4.5 kgf) | μ × 146 N |

So the grip has a margin of more than ten against the torque it must carry, at a stress far below anything that
would creep noticeably at room temperature. In PLA (E ≈ 3.5 GPa) every force is 1.75 times larger.

Print accuracy matters more than the material: large FDM parts often come out 0.1–0.3 % small. At 0.2 % small
the interference becomes about 0.59 mm: the press-on force rises to roughly 130 N (13 kgf, still possible by
pressing the spool onto the ring on a table) and the strain to 0.3 %, still elastic. That is why the nominal
interference is small; §8 says how to adjust it.

The ribs make the fit tolerant: the bore between them never touches the rim (0.5 mm clearance on the
diameter), a seam blob or a slightly oval rim only meets a few ribs, and the ribs press into the rim along their
length, which also resists turning.

## 6. Printing

- **One object, two parts** in `3mf/SpoolAdapter_195.5-to-199mm_2color.3mf`: `SpoolAdapter` (the ring, hint
  graphite #303236) and `SpoolAdapter_logo` (hint yellow #FFCC00). Core 3MF (2015/02) without slicer extensions,
  the house format (OutageAlarm, LineFollowerRobot): Creality Print, OrcaSlicer, Bambu Studio and PrusaSlicer load
  it as one object whose parts each take a filament; the colours are base materials, a hint the slicer may
  ignore.
- **Pose**: as modelled, lip down. No supports: the lead-in and chamfers are 45° or steeper, the ribs are vertical.
- **Colours**: the logo occupies only the first 3 layers (0.6 mm), so the CFS changes colour on 3 layers and the
  rest of the ring is one colour.
- **Settings** (design values): 0.4 mm nozzle, **0.2 mm layers including the first** (the logo depth lands on a
  layer boundary), 4 walls (the band is then solid), no brim (it would sit on the rolling surface's chamfer).
  Print two.
- **Material**: PETG preferred (a little give when pressing on), PLA works.

## 7. Logo

From the brand master `3DTeslaWebSite/brand/logo-horizontal-dark.svg`: emblem (a square with its top-left and
bottom-right corners cut at 45°), the "3D" stroked inside it, "TESLA" beside it; square caps and mitred joins as in
the SVG (`cad/logo.py`). With two colours the dark variant's white "TESLA" becomes yellow: yellow = emblem − "3D" +
"TESLA", and the graphite ring shows through the "3D". At 13 mm high the strokes are 1.05 mm ("3D") and 0.84 mm
("TESLA"), the gaps at least 0.84 mm.

## 8. Fit adjustment and other spools

Without CAD, in the slicer: **scale X and Y only** (Z stays 100 %). 0.1 % changes every diameter by about 0.2 mm,
and the outside diameter stays well inside the CFS range:

| Fit after printing | Scale X/Y | Bore change | Outside diameter |
|---|---|---|---|
| loose, turns by hand | 99.8 % | −0.39 mm | 198.6 mm |
| right | 100 % | — | 199.0 mm |
| too hard to press on | 100.2 % | +0.39 mm | 199.4 mm |

With CAD: `python build.py --rim <measured> --od <wanted> --interference <mm>` builds the checks and a 3MF named
after the values (the renders always show the default adapter).

## 9. Automatic checks (`python build.py`)

Outside diameter; rib tips < rim < bore; wall ≥ 1.4 mm; ribs printable; hoop strain < 0.4 %; bed fit; height; logo
strokes ≥ 0.8 mm; the logo at least 1 mm inside the flat bed face (clear of every chamfer and edge); the inlay is
exactly a 0.6 mm slab on the bed; ring and logo do not overlap; valid solids. The 3MF writer then checks both meshes
(closed, consistently oriented, positive volume, on the bed, the inlay only on its two faces). The rolling surface
is meshed with an absolute tolerance of 0.01 mm (about 314 facets around).

## 10. Check items (not verified)

- [ ] Rim roundness: measure the Filamentor flange at three angles; the design assumes 195.5 mm everywhere.
- [ ] Flange thickness at the rim ≤ 4.0 mm (gripped over its full thickness).
- [ ] Spool width over the flanges + 2.4 mm ≤ 68 mm (CFS limit).
- [ ] The flange's outer face is flat where the lip and tab sit (17 mm in from the rim); if there are ribs or
      windows, turn the ring so the tab lands on a flat area.
- [ ] Press-on force and grip of the first print (depends on the printer's accuracy); adjust with §8.
- [ ] Rewind behaviour in the CFS with the adapters, with a full and a nearly empty spool.
