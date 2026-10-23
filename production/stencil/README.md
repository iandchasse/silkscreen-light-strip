# Paste stencil for the LED pads (experimental, untested)

A 3D-printable stencil for the 24 LED pads of the light strip, for use with paste and a reflow oven instead of hand soldering. **It has not been printed or tried.** The slicer read-back ([`docs/reports/stencil_slice_check.md`](../../docs/reports/stencil_slice_check.md)) shows the toolpath leaves every opening clear; whether the printed holes stay open, and how good the joints are, are estimates. The full process (paste, tape, carrier, oven) is in [`docs/ASSEMBLY.md`](../../docs/ASSEMBLY.md#option-3d-printed-paste-stencil-and-oven-reflow-experimental-untested).

| File | What |
|---|---|
| `light-strip-stencil_D0.3_print.stl` | The card with a 0.3 mm deep pocket (0.5 mm thick). For a bar that measures 0.32-0.41 mm with the liner on. |
| `light-strip-stencil_D0.4_print.stl` | Pocket 0.4 mm (0.6 mm thick). For 0.42-0.51 mm. The likely one: nominal stack 0.385 mm plus the 0.09 mm liner = 0.475 mm. |
| `light-strip-stencil_D0.5_print.stl` | Pocket 0.5 mm (0.7 mm thick). For 0.52-0.61 mm. |
| `light-strip-stencil_D0.4_use.step` | The 0.4 file in the use frame (KiCad x, y; z up from the FR4), for CAD. |
| `aperture-coupon_print.stl` | Optional 1 g test coupon: holes from 0.4 to 1.0 mm in the same 0.2 mm membrane, to find where your printer stops opening them. |
| `stencil_params.json` | Every parameter, the derived numbers (aperture sizes, paste per pad, area ratio) and the slice-check time and filament per file. |
| `stencil_input.json` | The pads, outline and stiffener polygons read from the board by `tools/stencil/extract_paste.py`. |

**Pick the file** by measuring the bar (flex + stiffener + tape + liner, liner on) at 2-3 points: the largest multiple of 0.1 mm at least 0.02 mm below your reading is the depth. The liner is about 0.09 mm (3M's data sheet), so a nominal bar reads about 0.475 mm; a reading under about 0.37 mm means the liner is off or the reading is wrong. The files are already in print orientation (squeegee face on the bed, pocket facing up): load them as they are.

**Registration.** The pocket is 0.12 mm bigger than the strip all round. Pushing the card onto the strip's straight outer edge and the foot's top edge moves it 0.12 mm toward +x and 0.12 mm toward +y, so the 24 openings are cut 0.12 mm toward -x and -y of the pad centres (the stencil script checks every one) and land on the pad centres once the card is pushed home. If the card is not pushed onto both edges, every opening sits up to 0.12 mm off its pad.

**Print settings** (OrcaSlicer, Elegoo Centauri Carbon 2, PLA; start from "0.12mm Fine @Elegoo CC2 0.4 nozzle"):

| Setting | Value |
|---|---|
| Layer height, first layer height | 0.10 mm |
| Elephant foot compensation | 0 (the stock 0.1 opens the squeegee-side openings by 0.10 mm per side) |
| Brim, supports, ironing, arc fitting | off |
| Slow layers | 2 |
| First layer speed | 30 mm/s |

Slicer estimates with these settings: D0.3 8m52s and 1.91 g, D0.4 9m43s and 2.27 g, D0.5 10m31s and 2.63 g.

**Before use:** hold the card to a light (all 24 openings clear), and check that the first and last LED openings are 89.50 mm apart (D7's anode to D6's cathode, centre to centre).

**Regenerate** after a footprint, paste or outline change (see [CLAUDE.md](../../CLAUDE.md)):

```powershell
& "C:\Program Files\KiCad\9.0\bin\python.exe" -X utf8 -I tools\stencil\extract_paste.py
& <python with cadquery, shapely, trimesh> -X utf8 -I tools\stencil\stencil.py
& <python with cadquery, shapely, trimesh> -X utf8 -I tools\stencil\slice_check.py
& <python with cadquery, shapely, trimesh> -X utf8 -I tools\stencil\render.py
```

`slice_check.py` needs OrcaSlicer's command line (never its window). `tools/make_outputs.py` does not touch this folder.
