# Notes for coding agents

Ian (idc LLC) owns this project: the Silkscreen light strip, a 2-layer flex PCB (rev A, untested) that plugs into
the main board's frontlight connector (`J3`). The cases it goes in are a separate repo, silkscreen-enclosures. Machine-specific notes, if
any, are in `CLAUDE.local.md` (not in git).

## Ground rules

- **Commits:** plain messages, with no `Co-Authored-By` or other attribution trailer (public repo).
- **The KiCad project is generated.** Change `tools/params.py` / `tools/build_pcb.py`, then run `tools/generate.py`
  and `tools/make_outputs.py` with KiCad 9's Python. GUI edits to the `.kicad_pcb` get overwritten. Close KiCad
  first: the generator refuses to run while a lock file exists.
- **Verify with `tools/make_outputs.py`:** it fails on any ERC or DRC finding and rewrites everything in `docs/`
  (PDFs, reports, renders) and `production/` (Gerbers, zip, BOM, CPL). Commit those outputs with the change.
- **The cases depend on this strip's geometry.** After any outline or fold change, copy `build/geometry.json` to
  silkscreen-enclosures' `enclosures/case-426/hardware/reference/light-strip/strip-geometry.json` and
  `enclosures/case-368/...` (the same file), and say that the cases need a rebuild. If the optics heatmap changes,
  copy `docs/images/optics_heatmaps.png` there too.
- **The paste stencil (`tools/stencil/`) is built from the pads and the outline.** After a footprint, paste or outline change, rerun `tools/stencil/extract_paste.py` (KiCad Python), then `stencil.py`, `slice_check.py`, `squeegee.py --slice` and `render.py` (a Python with CadQuery, shapely and trimesh), and commit `production/stencil/` (including `squeegee*`), `docs/reports/stencil_slice_check.md`, `docs/reports/stencil_squeegee_check.md` and `docs/images/stencil_*.png` (including `stencil_squeegee*.png`). `squeegee.py` reads the card from `stencil.py`'s geometry, so rerun it after any stencil change. `make_outputs.py` does not touch `production/stencil/`. The stencil and its squeegee are untested: say what the slicer read-back shows, never that they work. The squeegee's forces and angles are beam estimates; say so.
- **Rev A is untested.** Don't describe anything as proven on hardware. `docs/review/` and `docs/research/` are
  dated records; `docs/DESIGN.md` is current where they differ.
