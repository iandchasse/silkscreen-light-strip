# Paste stencil for the LED pads (experimental, untested)

A 3D-printable stencil for the 24 LED pads of the light strip, for use with paste and a reflow oven instead of hand soldering. **It has not been printed or tried.** The slicer read-back ([`docs/reports/stencil_slice_check.md`](../../docs/reports/stencil_slice_check.md)) shows the toolpath leaves every opening clear; whether the printed holes stay open, and how good the joints are, are estimates. A printed squeegee that holds a piece of plastic card at a set angle and pressure wipes the paste on (also untested). **To print everything at once, print `stencil-kit_cc2.3mf` or `stencil-kit_generic.3mf`** (below): one plate with the three cards, the squeegee and its blades, and the coupon. The full process (paste, tape, carrier, oven) is in [`docs/ASSEMBLY.md`](../../docs/ASSEMBLY.md#option-3d-printed-paste-stencil-and-oven-reflow-experimental-untested).

| File | What |
|---|---|
| `stencil-kit_cc2.3mf` | **The kit for the Elegoo Centauri Carbon 2** (0.4 nozzle, Elegoo PLA): an OrcaSlicer project with one plate holding the three stencil cards (D0.3, D0.4, D0.5), the squeegee handle with its two PLA blades and the aperture coupon, with the settings below in the file (see "Check after opening" below). Slicer estimate about 1 h 06 min, 14.1 g. |
| `stencil-kit_generic.3mf` | The same plate for OrcaSlicer's Generic Marlin Printer 0.4 nozzle and Generic PLA; all parts inside 220 x 210 mm. About 2 h with that profile's slow speeds. |
| `light-strip-stencil_D0.3_print.stl` | The card with a 0.3 mm deep pocket (0.5 mm thick). For a bar that measures 0.32-0.41 mm with the liner on. |
| `light-strip-stencil_D0.4_print.stl` | Pocket 0.4 mm (0.6 mm thick). For 0.42-0.51 mm. The likely one: nominal stack 0.385 mm plus the 0.09 mm liner = 0.475 mm. |
| `light-strip-stencil_D0.5_print.stl` | Pocket 0.5 mm (0.7 mm thick). For 0.52-0.61 mm. |
| `light-strip-stencil_D0.4_use.step` | The 0.4 file in the use frame (KiCad x, y; z up from the FR4), for CAD. |
| `aperture-coupon_print.stl` | Optional 1 g test coupon: holes from 0.4 to 1.0 mm in the same 0.2 mm membrane, to find where your printer stops opening them. |
| `squeegee_print.stl` | The squeegee handle and two spare PLA blades on one plate, in print orientation (runners on the bed, blades standing on their working edges). Load it as it is. |
| `squeegee-blade-pla_print.stl` | One more PLA blade (10.0 x 1.0 x 26.2 mm), for spares. |
| `squeegee_params.json` | Every squeegee dimension, the derived numbers, the force and stress estimates (beam formulas, assumed stiffness) and the slice-check result. |
| `stencil_params.json` | Every parameter, the derived numbers (aperture sizes, paste per pad, area ratio) and the slice-check time and filament per file. |
| `stencil_input.json` | The pads, outline and stiffener polygons read from the board by `tools/stencil/extract_paste.py`. |

**The kit files** are written by OrcaSlicer itself (its command line, by `tools/stencil/make_plate.py`), so they carry its full project settings; the script only places the five STLs, asks OrcaSlicer to write the project, and adds the squeegee's own `wall_loops` = 3 and `wall_generator` = Arachne to that one object. The cards and the coupon use the process's classic walls. They are read back from a slice of the finished file ([`docs/reports/stencil_plate_check.md`](../../docs/reports/stencil_plate_check.md)): parts, positions, all 3 x 24 openings clear on layers 1 and 2, membranes, the clamp tongue tied, no support, brim, ironing or arcs, the plate inside its bed. Toolpath only: **nothing has been printed**. **Check after opening** (the files have been through OrcaSlicer's command line only, not yet opened in its window): the process is a project preset named "Stencil kit 0.10mm @Elegoo CC2 0.4 nozzle" (generic: "... @Generic Marlin 0.4 nozzle"), deliberately not a stock name, because OrcaSlicer's window replaces the values of a same-named stock preset when a command-line project is opened; it should show layer height and first layer height 0.10 mm, elephant-foot compensation 0, no brim, 2 slow layers and the classic wall generator. If it shows the stock "0.12mm Fine" values (0.12 / 0.2 mm, elephant-foot 0.1, an auto brim), set them by hand from the table below before slicing; the squeegee object's own 3 walls and Arachne are kept either way. Print all three cards, use the one that matches your bar; the single STLs below are for reprints and for other printers.

**Pick the file** by measuring the bar (flex + stiffener + tape + liner, liner on) at 2-3 points: the largest multiple of 0.1 mm at least 0.02 mm below your reading is the depth. The liner is about 0.09 mm (3M's data sheet), so a nominal bar reads about 0.475 mm; a reading under about 0.37 mm means the liner is off or the reading is wrong. The files are already in print orientation (squeegee face on the bed, pocket facing up): load them as they are.

**Registration.** The pocket is 0.12 mm bigger than the strip all round. Pushing the card onto the strip's straight outer edge and the foot's top edge moves it 0.12 mm toward +x and 0.12 mm toward +y, so the 24 openings are cut 0.12 mm toward -x and -y of the pad centres (the stencil script checks every one) and land on the pad centres once the card is pushed home. If the card is not pushed onto both edges, every opening sits up to 0.12 mm off its pad.

**Print settings** for a single card (OrcaSlicer, Elegoo Centauri Carbon 2, PLA; start from "0.12mm Fine @Elegoo CC2 0.4 nozzle"; the kit files already have them, for the whole plate):

| Setting | Value |
|---|---|
| Layer height, first layer height | 0.10 mm |
| Elephant foot compensation | 0 (the stock 0.1 opens the squeegee-side openings by 0.10 mm per side) |
| Brim, supports, ironing, arc fitting | off |
| Slow layers | 2 |
| First layer speed | 30 mm/s |

Slicer estimates with these settings: D0.3 8m52s and 1.91 g, D0.4 9m43s and 2.27 g, D0.5 10m31s and 2.63 g.

**The squeegee** (`squeegee_print.stl`, or on the kit plate; optional, **untested**) is a printed handle that clamps a 10 x 27 mm piece of plastic card (gift or loyalty card, 0.68-0.84 mm; or the printed PLA blade) in a slot at 50 degrees, with one M3 screw (8-12 mm) pushing a printed tongue onto it. Two 3 x 22 mm runners ride on the stencil card beside the openings and set the angle and the pressure (about 1.4 N for a 0.76 mm card; an estimate). One pass along the bar toward the foot only, about 99 mm, fills all 24 openings. Printed alone, use the stock "0.20mm Standard @Elegoo CC2 0.4 nozzle" with 3 walls, Arachne, no brim; supports off; **the elephant-foot compensation stays at the stock 0.1** (the opposite of the stencil card, which needs 0). On the kit plate it is printed at 0.10 mm layers with the plate's elephant-foot compensation of 0 and its own 3 walls and Arachne (6.7 g, about half of the plate's time); only a slight lip at the bottom edge of the runners and PLA blades is expected from that, which sandpaper takes off. Slicer estimate for its own plate (`squeegee_print.stl`, 0.20 mm layers): about 17 min and 6.4 g (16 min 37 s in the last read-back); the tongue's first layer is held by two one-layer tabs, so nothing prints in mid air and nothing needs supports (snap or cut the tabs before first use: see ASSEMBLY); [`docs/reports/stencil_squeegee_check.md`](../../docs/reports/stencil_squeegee_check.md) is the read-back. Cutting the card, clamping it and using it: [`docs/ASSEMBLY.md`](../../docs/ASSEMBLY.md#option-3d-printed-paste-stencil-and-oven-reflow-experimental-untested).

**Before use:** hold the card to a light (all 24 openings clear), and check that the first and last LED openings are 89.50 mm apart (D7's anode to D6's cathode, centre to centre).

**Regenerate** after a footprint, paste or outline change (see [CLAUDE.md](../../CLAUDE.md)):

```powershell
& "C:\Program Files\KiCad\9.0\bin\python.exe" -X utf8 -I tools\stencil\extract_paste.py
& <python with cadquery, shapely, trimesh> -X utf8 -I tools\stencil\stencil.py
& <python with cadquery, shapely, trimesh> -X utf8 -I tools\stencil\slice_check.py
& <python with cadquery, shapely, trimesh> -X utf8 -I tools\stencil\squeegee.py --slice
& <python with cadquery, shapely, trimesh> -X utf8 -I tools\stencil\make_plate.py
& <python with cadquery, shapely, trimesh> -X utf8 -I tools\stencil\render.py
```

`slice_check.py`, `squeegee.py --slice` and `make_plate.py` need OrcaSlicer's command line (never its window). `tools/make_outputs.py` does not touch this folder.
