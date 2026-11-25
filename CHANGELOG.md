# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/) (0.x until the adapter is printed and measured).

## [0.2.0] - 2026-11-25

### Changed

- **Looser fit after the first print.** The v0.1.1 ring, printed by the user, was much too tight ("muito
  apertado"): the printer's shrinkage and the usual undersize of printed holes ate the 0.20 mm interference
  budget. The model stays the fitted ring; the 3MF is now written **0.25 % larger in X and Y** (`XY_COMP`, Z
  untouched so the logo stays 0.6 mm): outside Ø 199.50 and rib tips Ø 195.79 as drawn, the tips 0.49 mm looser on
  the diameter. Design estimate, to be confirmed by the next print.

### Added

- `--comp <%>` in `cad/build.py` (a file named `_comp<value>` when it differs from the default), a "print
  compensation" check (drawn outside diameter inside the CFS's 197–202 mm), the compensation noted on the profile
  drawing, and the scale table in the README and `docs/design.md` §8 restated for the new file.

## [0.1.1] - 2026-11-24

### Fixed

- **Two teeth on the rolling surface at the logo tab** (reported by the user): the tab's straight sides ran up to
  y = 97.75 mm, so its two top corners (x = ±22.5 mm) reached r = 100.3 mm and stood 0.8 mm proud of the Ø 199 mm
  rolling surface (2.5 mm³). The tab is now clipped to the bore; nothing reaches beyond r = 99.50 mm. The
  outside-diameter check only looked at the bounding box, which misses features off the X/Y axes; a new check,
  "nothing outside the rolling surface", measures the volume beyond Ø 199 mm.

## [0.1.0] - 2026-11-24

First release: designed and checked in CAD. **Not printed yet**: every number except the two spool diameters is a
design value or an estimate.

### Added

- **SA-01 spool adapter**: a closed press-fit ring that brings a 195.5 mm spool (Filamentor) up to 199 mm for the
  Creality CFS. Band Ø 199.0 / Ø 196.0 (1.5 mm wall), 60 axial crush ribs with 0.20 mm interference on the
  diameter, lead-in, 1.2 mm lip on the flange's outer face (the only width added per side), grips flanges up to
  4 mm thick.
- **3DTesla logo tab**: the horizontal logo, 40 × 13 mm, from the brand SVG, inlaid 0.6 mm in the outer face.
- **Two-colour 3MF** (`3mf/SpoolAdapter_195.5-to-199mm_2color.3mf`): ring + logo as one object with two parts,
  print pose, logo in the first 3 layers.
- **Parametric CadQuery model** (`cad/`) with checks (diameters, fit, wall, ribs, bed fit, logo strokes and
  margins, inlay slab, overlaps, solids, meshes) and `--rim / --od / --interference` for other spools.
- **Renders and a dimensioned profile drawing** (`docs/img/`), **design document** (`docs/design.md`: requirements,
  concept and alternatives, parameters, retention estimates, fit adjustment, check items), CI that runs the checks
  and builds the 3MF.
