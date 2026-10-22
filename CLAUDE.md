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
- **Rev A is untested.** Don't describe anything as proven on hardware. `docs/review/` and `docs/research/` are
  dated records; `docs/DESIGN.md` is current where they differ.
