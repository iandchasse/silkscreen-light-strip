# Review lens: KiCad project integrity, reproducibility and tooling

Reviewer: adversarial review agent, 2026-09-25. KiCad 9.0.6 (kicad-cli + pcbnew python), KiCAD MCP server (mixelpixx, stdio).

Everything that writes ran in scratch copies only: `a scratch copy` (checks, old-generator test,
re-enabled-rules DRC), `a scratch regeneration copy` (regeneration diff), `a scratch MCP copy` (MCP + gerber
re-export). Nothing in the repo's .kicad_* / lib / tools files was written. No KiCad process and no `*.lck` file was
present during the review.

**Verdict:** the project opens, checks clean and regenerates exactly (geometry and schematic), and the production
gerbers match the board. Nothing here stops the board working or being built. What's left is tooling and hygiene:
44 ERC exclusions copied over from the main board, a generator that only worked inside the parent folder (fixed
in the working tree during the review), a hard-to-read schematic around J1 (the contact tail), D11/D12 (the diodes) and TP1-3 (the test pads), no silkscreen
polarity marks on the LEDs, and a repo with no commits and no .gitignore, README or LICENSE.

---

## Findings

### K1 (MINOR) 44 ERC exclusions carried over from the main-board project
- Evidence: `silkscreen-light-strip.kicad_pro` -> `erc.erc_exclusions` has 44 entries (18 pin_to_pin,
  12 multiple_net_names, 9 lib_symbol_mismatch, 3 four_way_junction, 1 footprint_link_issues, 1 single_global_label).
  Their UUIDs and sheet path (`/2fbd4c8f-...`) come from the main board's schematic. This root sheet is `ad90a496-...`.
- `kicad-cli sch erc --severity-all` prints **"Found 44 violations"** on stdout, while the .rpt/.json it writes
  list 0. In the scratch copy I set `erc_exclusions = []` and the stdout count dropped to "Found 0 violations".
  So all 44 are exclusions that match nothing in this schematic. The GUI will restore them as excluded markers.
- Cause: `tools/generate.py write_project_files()` resets `drc_exclusions` (line ~551) but not `erc_exclusions`.
  The new `tools/template.kicad_pro` (added 00:04 during this review) is byte-identical to the generated
  project, so it keeps the 44 entries.
- Fix: add `pro["erc"]["erc_exclusions"] = []` in `write_project_files()`, and remove the entries from
  `tools/template.kicad_pro`.

### K2 (MINOR, fixed in the working tree during the review) Generator only ran next to `../silkscreen-pcb`, and a failed run leaves a half-regenerated project
- Evidence: the copy taken at 00:03 had `TEMPLATE_PRO = os.path.join(os.path.dirname(ROOT), "silkscreen-pcb",
  "silkscreen_pcb.kicad_pro")`. Run from `a scratch copy` it stopped with
  `FileNotFoundError: ...\silkscreen-pcb\silkscreen_pcb.kicad_pro`.
- Before the crash it had already rewritten `lib/*.pretty`, `lib/*.kicad_sym` and `.kicad_sch` (mtime 00:05:53),
  but not `.kicad_pro` or `.kicad_pcb`. The order in `__main__` is footprints -> symbols -> schematic -> project
  files -> netlist -> PCB, and nothing is written atomically.
- At 00:04:03 the repo's `generate.py` line 48 was changed to `os.path.join(HERE, "template.kicad_pro")` and
  `tools/template.kicad_pro` was added. I checked that version from `a scratch regeneration copy` and it
  regenerates successfully (see "Verified OK").
- Remaining fix:
  - Clean the template (K1, K4).
  - Check that every input exists (template, stock SOT-323 footprint and symbol, kicad-cli) before writing
    anything, or write to a temp dir and move the files in at the end.
  - Commit the template.

### K3 (MINOR) Schematic readability: text overlaps at J1, TP1-TP3 and D11/D12
Evidence: `docs/silkscreen-light-strip_schematic.pdf` rendered to PNG with pymupdf at 300 dpi.
- **J1** is placed mirrored (`mirror="y"`), so its pin names `LED_SW(C+)`, `C-`, `NC`, `LED_SW(W+)`, `W-` sit
  outside the body on the left. They overprint the reference "J1" and the value "FPC tail to J3" (J3 being the main board's frontlight connector), which can't be
  read.
- **TP1-TP3**: each value ("LED_SW pad", "C- pad", "W- pad") is drawn on top of the net label below it, and the
  wire runs through both. The render reads "LED_SWED_SW" and "C- Cad".
- **D11/D12**: the pin-3 wire runs down through the value text "BAV70W".
- The whole drawing sits in the top-left third of an A3 sheet.
- Fix in `build_schematic()`:
  - Don't mirror J1: place it at 180° or put pin names inside the body, and move the ref/value above it.
  - Move each TP value above the symbol, or drop the "pad" values.
  - Offset the BAV70W value to the right of pin 3.

### K4 (NOTE) Seven DRC checks are ignored because of the template
- Evidence: `board.design_settings.rule_severities` sets these to "ignore": footprint_filters_mismatch,
  footprint_type_mismatch, missing_courtyard, npth_inside_courtyard, pth_inside_courtyard, silk_over_copper,
  solder_mask_bridge. They come from the main board's settings.
- So "0 DRC violations" does not mean these checks ran.
- I switched all seven to "error" in a scratch copy. DRC then found **8 solder_mask_bridge, all from J1's
  gang coverlay opening** (`Rectangle of J1 on F.Mask` bridging the finger traces). That is expected for gold
  fingers. Nothing else fired, so the ignored checks are not hiding a real problem today.
- Fix: put KiCad's default severities back, and handle J1 locally by adding the footprint attribute
  `allow_soldermask_bridges` to `FPC_Tail_...TopContact` instead of ignoring the check for the whole board.

### K5 (MINOR) Repo has no commits and no .gitignore, README or LICENSE; cache and backup files would be committed
- Evidence: `git log` reports "your current branch 'main' does not have any commits yet". `git status` shows
  every file untracked.
- These would all be committed: `fp-info-cache`, `silkscreen-light-strip.kicad_prl` (per-user UI state),
  `silkscreen-light-strip-backups/*.zip` (a KiCad autosave from 00:01:33), `tools/__pycache__/`, and `build/`
  (which holds stale duplicate drc/erc reports).
- The title blocks say "Licensed under CERN-OHL-S-2.0", but there is no LICENSE file.
- Fix: add a KiCad .gitignore (`*-backups/`, `fp-info-cache`, `*.kicad_prl`, `~*.lck`, `__pycache__/`,
  `build/`), a LICENSE, and a README covering how to regenerate. Then make the first commit.

### K6 (MINOR) No silkscreen polarity or reference marks on the LEDs (hand rework on a DIY flex)
- Evidence (pcbnew read of the repo board):
  - All 16 footprints have their Reference hidden.
  - `LED_SideView_XINGLIGHT_XL-4008` has **0 silkscreen items**. The K/A letters are on F.Fab only.
  - Board-level F.Silkscreen has only the tail bend marks plus "LIGHT STRIP" / "rev A".
- A single LED fitted backwards leaves its whole 5-LED string dark, and the board gives no way to spot which
  one.
- Fix: add a small cathode tick on F.Silkscreen at each LED (outside the pads and the light path), or at least
  one "K" legend per string near the foot.

### K7 (NOTE) Footprint fab graphics outside the courtyard (the cause of the MCP courtyard false positives)
- LED footprint: the F.Fab light-direction arrow reaches 0.9 mm in front of the emitting face, but the
  courtyard stops 0.15 mm in front of it. pcbnew bounding boxes, e.g. D1: arrow x 45.26..46.14 against a
  courtyard edge at about 45.35.
- TestPad_1.1mm_Wire: the F.Fab circle has r = 0.75 mm, but the courtyard is ±0.70 mm.
- The MCP `check_courtyard_overlaps` uses footprint bounding boxes, so it reports TP1/TP2 and TP2/TP3 as
  overlapping by 0.05 mm. KiCad DRC (real courtyards, 0.1 mm gap at 1.5 mm pitch) correctly finds none.
- Fix: shrink the TP fab circle to r ≤ 0.65. Moving the arrow is optional; it is only an annotation.

### K8 (NOTE) The repo PCB is slightly behind `params.py` (stackup colour only)
- Evidence: the regenerated board writes the F.Mask/B.Mask stackup colour as `"#C8800FE0"`. That matches
  `params.py` line 48 (`coverlay_color`), which was modified at 00:00:46.
- The repo `.kicad_pcb` (23:59:18) still says `"Yellow"`. Geometry is identical (see Verified OK).
- The docs renders use `--use-board-stackup-colors`, so they show the old colour.
- Fix: regenerate once the GUI is closed, then re-run `make_outputs.py`.

### K9 (NOTE) Board UUIDs are not deterministic, so every regeneration produces a large diff
- Evidence: after regeneration, `diff` of `.kicad_pcb` shows 3,704 changed lines (2,744 even after replacing
  every UUID with a placeholder). The footprint block order changes (the repo file starts with D4, the
  regenerated one with TP2), because the footprint and track KIIDs are random and KiCad sorts by them.
- Semantically the two boards are identical (next section).
- Fix (optional): post-process the saved file, replacing each UUID with `uid(ref/item hash)` in a stable order.
  Or accept the churn and only commit a regenerated board together with its source change.

### K10 (NOTE) LED 3D model is referenced as .wrl only, so a plain STEP export has no LED bodies
- Evidence: in the scratch copy, `kicad-cli pcb export step` without `--subst-models` prints
  "Cannot load any VRML model for this export". The LEDs are missing from that STEP.
- With `--subst-models` (which `make_outputs.py` uses) the LEDs are included (176 kB vs 161 kB file).
- A GUI or MCP STEP export without substitution, which is what enclosure CAD would use, has a strip with no
  LED bodies.
- Fix: point the footprint `(model ...)` at the `.step`. The 3D viewer and the VRML export both read STEP.

### K11 (NOTE) MCP server vs kicad-cli: where they disagree
- **Courtyard overlaps:** MCP `check_courtyard_overlaps` reports TP1/TP2 and TP2/TP3 overlaps (false; see K7).
  It also reports J1 exceeding the outline by 0.25 mm at the bottom. That is the tail footprint's courtyard
  running 0.25 mm past the finger tip on purpose; KiCad has no such check.
- **Ratsnest:** MCP `get_ratsnest` gives 20 "segments" totalling 440 mm. It estimates pad-to-pad airwires and
  ignores the routed copper. kicad-cli reports 0 unconnected items, so this is not a design problem.
- **run_drc side effect:** MCP `run_drc` writes `silkscreen-light-strip_drc_violations.json` next to the board.
  Never point it at the repo.
- **Backend selection:** the client script defaults to `KICAD_BACKEND=auto`. With the GUI open, that could
  pick IPC and query the GUI's board, which is the repo board, not the scratch copy. I forced
  `KICAD_BACKEND=swig` in my copy of `mcp_call.mjs`, and every call reported `"_backend":"swig"`.

### K12 (NOTE) Hard-coded Windows KiCad paths
`generate.py:44`, `make_outputs.py:29` and `make_step_model.py:17` hard-code `C:\Program Files\KiCad\9.0`.
- Fix: honour an env var (e.g. `KICAD_CLI`) and fall back to `shutil.which("kicad-cli")`.

---

## Verified OK (checked myself)

**Checks**
- kicad-cli 9.0.6:
  - ERC: 0 errors, 0 warnings. The 44 on stdout are K1.
  - `pcb drc --schematic-parity --severity-all`: 0 violations, 0 unconnected, 0 parity issues. Same as
    `docs/reports`.

**Libraries and 3D models**
- `fp-lib-table` / `sym-lib-table` resolve through `${KIPRJMOD}`.
- `kicad-cli fp export svg` plots all 4 footprints. `sym export svg` plots all 4 symbols (BAV70W, FPC_Tail_J3,
  LED_SideView, TestPoint).
- 3D paths:
  - 10 LEDs point at `${KIPRJMOD}/lib/silkscreen-light-strip.3dshapes/LED_SideView_XINGLIGHT_XL-4008.wrl`,
    which exists; the `.step` is beside it.
  - D11/D12 point at `${KICAD9_3DMODEL_DIR}/Package_TO_SOT_SMD.3dshapes/SOT-323_SC-70.step`, which exists in
    the KiCad 9 install.

**Reproducibility**
- The current `generate.py`, run from a scratch copy, reproduces these byte-for-byte:
  - `.kicad_sch`, `.kicad_pro`, `.kicad_dru`
  - both lib tables and `lib/*.kicad_sym`
  - all 4 `.kicad_mod` files and the `.wrl`
- The `.step` differs only in its FILE_NAME timestamp.
- The `.kicad_pcb` is semantically identical: 522/522 canonical items match. That covers footprints (ref,
  value, lib id, position, rotation, layer, sheet path), every field, every pad's net/position/size, footprint
  graphics, all tracks, vias, zones (including filled area), board drawings, thickness, layer count and the
  title block. The only text differences are the stackup colour (K8) and UUID order (K9).

**Production outputs**
- Gerbers and drill: I re-exported the 11 layers `make_outputs.py` uses (F/B.Cu, F.Paste, F/B.Silkscreen,
  F/B.Mask, Edge.Cuts, User.1 = Stiffener.PI0.225, User.2 = Adhesive.3M9077, User.3 = Bend.Zones) plus the
  Excellon drill from the repo board.
- All 13 files (including the job file) match `production/gerbers` except for creation-date lines. The zip
  has the same 13 files.

**MCP server** (swig backend, scratch copy)
- `open_project` succeeds.
- `get_board_info`: 17.1 x 130.315 mm, the same as the design summary's outline bbox.
- `get_component_list`: 16 parts.
- `get_nets_list`: 15 nets plus net 0.
- `run_drc`: 0 violations, which agrees with kicad-cli.
- `get_board_2d_view` PNG saved as `a scratch copy (silkscreen-light-strip_2d_view.png)`; it renders
  the outline, copper and tail correctly.

**Field convention**
- The main board uses Value = short name, MPN = full orderable part number, plus Manufacturer and LCSC
  (e.g. U12 74LVC1G04 / 74LVC1G04GV,125 / Nexperia).
- D11/D12 follow that: Value BAV70W, MPN "BAV70W,115", Manufacturer Nexperia, LCSC C28064. The LCSC product
  page confirms C28064 = Nexperia BAV70W,115, SOT-323-3.
- The LEDs have Value = MPN = XL-4008WWC / XL-4008UWC, XINGLIGHT, LCSC C5440667 / C2843774. They are
  LCSC-only by the owner's request.
- J1 and TP1-3 are excluded from the BOM and the position file, as intended.

**Pin maps**
- LED symbol: 1 = K, 2 = A. The footprint's pad 1 is the cathode.
- BAV70W symbol: 1 = A1, 2 = A2, 3 = K, which matches the Nexperia SOT-323 pinout.
- The netlist matches `design_summary.md`.

**Title blocks**
- Schematic and PCB both carry title, date 2026-09-24, rev A, idc LLC, and licence/description comments.
