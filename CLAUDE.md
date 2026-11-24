# CLAUDE.md — SpoolAdapter (SA-01)

A small 3DTesla accessory, not a kit: a printed press-fit ring that brings a 195.5 mm filament spool up to
199 mm for the Creality CFS. **Public** repository (`icefoxj/SpoolAdapter`): nothing private goes in it.
The family rules in `E:\GitHub\CLAUDE.md` apply (English in the repo, Brazilian Portuguese with the user, design
values labelled, mech look, grey never white).

## User requirements (2026-11-24)

> "Vamos criar um projeto simples de um adaptador de rolo de filamento. Comprei alguns rolos de filamento da
> Filamentor e eles são um pouco menores que os que normalmente uso e ficam soltos quando uso o CFS da Creality.
> O rolo que funciona com a Creality tem 199 mm de diâmetro e o rolo da Filamentor tem 195,5 mm. Precisamos criar
> um STL para adaptar o rolo da Filamentor para funcionar na Creality. Ele precisa ficar bem preso para não
> escorregar. Pode criar o README.md, CLAUDE.md e colocar no GitHub no repositório SpoolAdapter. Pode deixar
> público. Coloque uma pequena aba no adaptador com o logo da 3DTesla. Pode usar 2 cores nesse caso e gerar um
> .3mf. Esqueça o STL."

- Rim 195.5 mm (measured) → outside 199.0 mm (measured on the Creality spool that works).
- Must hold firmly and not slip on the spool.
- Small tab with the 3DTesla logo, **two colours, 3MF only — no STL** (and no STEP unless asked).
- Public GitHub repo `SpoolAdapter`, README.md and CLAUDE.md.
- "Projeto simples": no firmware, app, theory course, manual PDFs, website page or cost workbook unless the user
  asks (the full kit structure of the family CLAUDE.md does not apply).

## Phase

v0.1.0 (2026-11-24): designed, CAD checks pass, 3MF and renders generated. **Not printed yet**: the check items
are in `docs/design.md` §10. When the user prints and measures, record the real fit and update the status lines
(README, design.md, CHANGELOG).

## Design in one paragraph

Closed ring with an L section (decisions and alternatives in `docs/design.md` §2): band Ø 199.0 outside / Ø 196.0
bore, 1.5 mm wall, 5.2 mm long; 60 axial crush ribs, tips on Ø 195.3 (0.20 mm interference on the diameter, the
ring stretches 0.10 %); lead-in cone; lip 1.2 mm thick (the only width added per side), 3.0 mm inside the rim on
the flange's outer face; logo tab 45 mm wide on the lip; logo 40 × 13 mm inlaid 0.6 mm in the bed face (= outer
face), mirrored in the model. Prints lip down; two rings per spool.

## Commands

```bash
# CadQuery venv shared by the family (or make one from cad/requirements.txt)
E:\GitHub\FilamentRecycler\.venv\Scripts\python.exe cad\build.py              # checks + 3MF + renders
E:\GitHub\FilamentRecycler\.venv\Scripts\python.exe cad\build.py --no-render  # what CI runs
E:\GitHub\FilamentRecycler\.venv\Scripts\python.exe cad\build.py --rim 194.8 --od 199 --interference 0.2
```

CI (`.github/workflows/cad.yml`) runs the checks and uploads the 3MF.

## Conventions

- Design frame = print pose: axis Z, lip on the bed (z = 0 … 1.2), band up to z = 5.2. The bed face is the outer
  face when mounted; anything drawn on it is mirrored in X so it reads from outside.
- Two-colour 3MF in the house format (core 3MF, one object, parts `SpoolAdapter` + `SpoolAdapter_logo`), the logo
  a 0.6 mm slab on the bed (3 layers of 0.2 mm), checked by `export3mf.two_colour`.
- Meshes use an **absolute** chordal tolerance (`export3mf.mesh`): cadquery's `tessellate()` alone is relative and
  made the 199 mm rolling surface an 84-gon.
- Logo geometry only from the brand master `E:\GitHub\3DTeslaWebSite\brand\logo-horizontal-dark.svg`; strokes and
  gaps ≥ 0.8 mm; at least 1 mm inside the flat bed face (both checked).
- Colours: ring graphite #303236, logo yellow #FFCC00 (never orange). If a light printed colour is ever used it is
  grey #A7ABB1, never white.
- The spool in the renders is an illustration (only its diameter is measured); say so where it matters.

## Keep in sync

When a parameter changes in `cad/spool_adapter.py`:

1. `docs/design.md` — §3 geometry, §4 parameter table, §5 retention numbers, §8 scale table.
2. `README.md` — "How it holds", print and fit sections, the scale table.
3. `CLAUDE.md` — "Design in one paragraph".
4. Rebuild (`cad/build.py`): the 3MF and `docs/img/sa01_*.png` (the profile drawing is generated from the
   parameters).
5. `CHANGELOG.md`.

## Mech look

Graphite ring, yellow logo; the profile drawing has the unit code SA-01 knocked out of a yellow title band with a
45° cut; the tab has 45° cut corners; red-orange #FF5533 marks the critical dimension (rib tips) in the drawing.
