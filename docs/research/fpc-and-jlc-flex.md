# FPC interface (Hirose FH34SRJ) and JLCPCB flex fabrication notes

Researched 2026-09-24. Every number cites a source. Anything not confirmed from a source is marked UNVERIFIED. Source tags ([H25], [JCAP], ...) are defined at the top of each section.

## 1. Hirose FH34SRJ-6S-0.5SH(50) (main board J3)

Sources:
- [H25] Hirose FH34 series catalog, "Mar. 2025" edition (printed Aug.1.2026), official: https://www.hirose.com/en/product/document?clcode=&productname=&series=FH34SRJ&documenttype=Catalog&lang=en&documentid=en_FH34_CAT (pages 3, 4, 5, 6, 8, 9, 16-19 read; p.6 and p.8 rendered and inspected visually).
- [H24] Same catalog, Mar.1.2024 edition, via Octopart mirror: https://datasheet.octopart.com/FH34SRJ-4S-0.5SH(50)-HIROSE-ELECTRIC-datasheet-178267795.pdf (page 14 "FH34SRJ/FH34D Series Recommended FPC/FFC Construction", rendered and inspected).
- [FP] Local footprint: <workspace>\de-link_pcb\KiCad\9.0\3rdparty\FH34SRJ_6pin\HRS_FH34SRJ-6S-0.5SH_50_.kicad_mod
- [BRD] Main board, read-only via pcbnew: <workspace>\de-link_pcb\silkscreen_pcb.kicad_pcb
- [STEP] <workspace>\de-link_pcb\KiCad\9.0\3rdparty\FH34SRJ_6pin\WFH-2100190.stp (header FILE_NAME 'FH34SRJ-6S_ActuatorOPEN.stp', Creo export 2021-09-15; modelled with the actuator OPEN; solid bounds not parsed).

### 1.1 Connector basics
- 0.5 mm pitch, 1.0 mm height, back-flip ZIF, "Top and Bottom Contact" [H25 p.1-2].
- Suffix "SRJ" = "Incompatible with FPC/FFC Tabs" (no ear/tab lock); "D" variant is the tab version [H25 p.5]. So our tail must have NO ears/notches (plain rectangle) for FH34SRJ.
- Rated current 0.5 A per contact (70 % when all contacts carry current), 50 V AC/DC rated, contact resistance 100 mOhm max incl. FPC conductor, mating durability 20 cycles [H25 p.4]. Our ~14 mA / ~25 V OVP is far inside this.
- 6-position dims: A = 5.0 (body width +-0.15), B = 2.5 (pin 1 to pin 6 centre span), C = 3.53, D = 4.38 (+-0.1) [H25 p.6 table].
- Side-view depth (3.8) overall, (2.9) housing, (0.5) tail stub [H25 p.6 side view, reference dims].

### 1.2 Applicable FPC thickness
- **t = 0.3 +-0.03 mm, gold plated** ("Recommended FPC/FFC Specifications") [H25 p.4]; same 0.3 +-0.03 on the FPC side view of the recommended FPC drawing [H25 p.8].
- Hirose's own recommended builds [H24 p.14] (all sum to ~0.3 mm at the contact area):
  - Single-sided FPC: coverlay PI 1 mil (25) + cover adhesive (25) [not over contacts], surface treatment 0.2 um Au over 1-5 um Ni (3), Cu 1 oz (35), base adhesive (25), base film PI 1 mil (25), reinforcement adhesive (35), reinforcement film PI 7 mil (175). Total 298 um.
  - Double-sided FPC: surface treatment (3), through-hole Cu (15), Cu 1/2 oz (18), base adhesive (18), base PI 1 mil (25), base adhesive (18), Cu 1/2 oz (18), cover adhesive (25), cover lay PI 1 mil (25), reinforcement adhesive (50), reinforcing film PI 4 mil (100). Total 297 um.
  - Note: "The thickness tolerance is approximately +-20 um" [H24 p.14].
- Hirose also recommends, when the FPC carries mounted parts, a glass-epoxy reinforcing plate of 0.3 mm min for handling [H25 p.19 "About Mounting to FPC"] (this refers to the connector-side PCB being an FPC; informative only).

### 1.3 Recommended FPC tail dimensions, 6 positions [H25 p.8 drawing + p.9 table]
| Item | Value | Source |
|---|---|---|
| Overall tail width G | **3.5 +-0.05 mm** (6 pos; G = B + 1.0) | [H25 p.9 table: 6 pos B 2.5, E 4.1, F 4.9, G 3.5] |
| Conductor pitch | 0.5 mm (basic), positional tol. 0.03 to datum Z | [H25 p.8] |
| Conductor width | **0.3 +-0.03 mm** | [H25 p.8] |
| Outer conductor centre to tail edge | **0.5 +-0.07 mm** each side | [H25 p.8] |
| Pin 1 to pin 6 span B | 2.5 mm | [H25 p.9] |
| Exposed (uncovered, coverlay-free) length from tip | **1.5 +-0.3 mm** | [H25 p.8 "(Uncovered Area)"] |
| Reinforcing film (stiffener) length from tip | **2.5 +-0.3 mm** | [H25 p.8 "(Reinforcing Film)"] |
| Overlap P of stiffener past coverlay edge | **P >= 0.5 mm** ("P dimension must be at least 0.5mm") | [H25 p.8 note] |
| Tip corner radius | **R0.2 +-0.1** on the leading corners | [H25 p.8] |
| Thickness at contact area | 0.3 +-0.03 mm | [H25 p.8] |
| Notch / ear / tab | **None** for SRJ (tabs only on FH34D) | [H25 p.5] |
- Drawing note: "The FPC recommended above is for FH34SRJ series only." [H25 p.8]
- The conductors in Hirose's drawing run the full 1.5 mm uncovered length out to the tip (they end at the tip edge in the drawing) [H25 p.8, visual]; exact conductor setback from tip is not dimensioned (UNVERIFIED; JLC's own gold-finger rule in section 2 governs the fab side).

### 1.4 Contact side
- The FH34SRJ contacts **both faces**: "Since it can be used in both top contact and bottom contact" [H25 p.2]. The FPC may present its conductors either up (top contact = facing away from the PCB the connector is soldered to, toward the actuator/lid side) or down (bottom contact = facing that PCB).
- **Pin numbering mirrors with contact side.** The recommended-FPC drawing (viewed from the conductor face, tip pointing into the connector) labels "Contact No.1 (Top Contact)" on the right-hand conductor and "Contact No.1 (Bottom Contact)" on the left-hand conductor [H25 p.8]. So whichever face we expose, the finger that lands on J3 pin 1 must be chosen for that face; getting it wrong swaps 1<->6, 2<->5, 3<->4.
  - Consequence for this project (J3 map 1 C+/LED_SW, 2 C-, 5 W+/LED_SW, 6 W-): a mirrored tail puts LED_SW on our C- and W- conductors and our anodes on the FET drains, i.e. both strings reverse-biased while the boost climbs toward OVP (~25 V). Design must pick one contact side deliberately and label it on silkscreen (e.g. "CONTACTS FACE BOARD" / arrow + pin-1 mark).
- Insertion check "When Used in Top Contact": the FPC pattern boundary line should line up with the housing opening end line; oblique/shallow insertion is visible this way [H25 p.17].

### 1.5 Insertion side vs solder tails and actuator
- Back-flip: "the FPC insertion direction and actuator are in different directions. Do not open from the FPC insertion side." [H25 p.18]. Actuator opens to 90 deg max [H25 p.18]; ships open [H25 p.16].
- Connector drawing [H25 p.6]: in the top view the signal solder tails protrude from the TOP edge (Contact No.1 at the right); the side view shows the tails at one end, the (open) actuator standing next to the tail end, and the tapered FPC opening at the opposite end. So **the FPC enters from the side opposite the signal solder tails, i.e. from the retention-tab (fitting nail) side**. Recommended land pattern [H25 p.8]: signal pads at the top, retention-tab pads at the bottom corners, overall 0.8 + gap + 0.8 = 3.3 +-0.05 mm, tab pads E 4.1 / F 4.9 (6 pos).
- Local footprint [FP] agrees with Hirose: signal pads at y = -1.25 (tails side), pin 1 at x = +1.25 (right), nails S1/S2 at y = +1.25, x = +-2.25 (0.4 wide -> inner 4.1 / outer 4.9 = E/F). Fab body y -2.0..+1.8.
- **In footprint coordinates the FPC enters from the +y side (the nail side, body edge y = +1.8) and travels in the -y direction.**
- On the main board [BRD]: J3 on B.Cu at (54.237, 126.0) rot 180; pads 1..6 at y = 124.575 (x 52.987 .. 55.487, pin 1 at the smallest x when viewed from the front), nails S1/S2 at (51.737 / 56.737, 127.5). So on the board the opening faces +y (toward the board's bottom edge y = 148.25) and the tail slides in along -y (upward in front view). Note: the board's embedded footprint has hand-solder-lengthened pads (signal 0.3 x 1.15, nails 0.95 x 1.15; pad centre-to-centre 2.925 vs 2.5 in the library file); body B.Fab y 124.0..127.8 [BRD]. The opening edge is therefore near y ~127.8-128.1 (UNVERIFIED to +-0.3 mm; derived from fab lines, not the STEP solid).
- J3 sits on the BACK of the main board, so "top contact" for J3 = conductors facing rearward (away from the main board, toward the case back); "bottom contact" = conductors facing the main board. (Derived from [H25 p.2/p.8] + [BRD] layer B.Cu.)
- Routing precautions [H25 p.18]: no strain on the connector; stiffener must lie parallel to the PCB; do not let the FPC or stiffener touch the case; observe bend radii; insert horizontally with actuator open [H25 p.16].

## 2. JLCPCB flexible PCB capabilities

Sources:
- [JCAP] https://jlcpcb.com/capabilities/flex-pcb-capabilities (read 2026-09-24 via browser, incl. FAQ).

### 2.1 Capability table [JCAP]
- Layers: 1, 2, 4. Rigid-flex not supported.
- Stack-ups: 1L / 2L with 25 um PI core; 1L / 2L with 50 um PI core ("Tear-resistant"); 1L / 2L transparent (PET 36 um); 4L. FAQ: both adhesive and adhesive-less PI supported; adhesive-less "strongly recommended" for flexibility/bend life.
- Finished thickness (excluding stiffeners): 25 um core 1L 0.07 / 0.11 mm, 2L 0.11 / 0.12 / 0.2 mm; 50 um core 1L 0.12 mm, 2L 0.19 mm; transparent 1L 0.14, 2L 0.24; 4L 0.2..0.45. White coverlay adds 10 um per side.
- Copper: single-sided 18 um (0.5 oz) or 35 um (1 oz); double-sided/4L 12 um (1/3 oz), 18 um, 35 um.
- Process: dry film + LDI exposure.
- Surface finish: ENIG 1u" / 2u" (only finish listed).
- Thickness with stiffener = FPC thickness + stiffener thickness. Thickness tolerance: stiffened area <= 0.3 mm: +-0.05; 0.3-1.0 mm: +-0.1; > 1.0 mm: +-10 %; **gold-finger area +-0.03 mm** (matches Hirose 0.3 +-0.03).
- Max size 234 x 490 mm regular (250 x 600 with rails, ask support). Min size: no limit, but parts smaller than 20 x 20 mm "are best panelised".
- Holes 0.1-6.5 mm, +-0.08 mm; min plated slot 0.5 mm; NPTH to copper >= 0.20 mm; non-plated slot copper clearance >= 0.2 mm.
- Vias: regular 0.3 mm hole / 0.55 mm pad; extreme 2L 0.10/0.3 (extra cost); pad >= hole + 0.2 mm (0.25 better). PTH annular ring >= 0.25 mm recommended, 0.18 absolute.
- Trace/space: 1/3 oz 3/3 mil (2/2 absolute), 0.5 oz 3.5/3.5 mil, 1 oz 4/4 mil. Width tolerance +-20 %.
- Via ring to trace >= 0.1 mm; exposed pad to trace >= 0.15 mm.
- Coverlay colours Yellow / Black / White / Transparent ("Yellow is recommended"). Coverlay opening expansion 0.1 mm per side; coverlay-opening-to-trace >= 0.15 mm. Keep coverlay over vias (recommended). Coverlay thickness (25 um core): PI 12.5 + adhesive 15 um on 1/3 or 0.5 oz Cu; PI 25 + adh 25 um on 1 oz Cu; 50 um core: PI 25 + adh 25. White coverlay 13-18 um thicker per side.
- Minimum coverlay (solder) bridge 0.5 mm; narrower bridges are removed (so 0.5 mm-pitch pads get one gang opening).
- Silkscreen: character height >= 1 mm, line width >= 0.15 mm, >= 0.15 mm to pads (clipped otherwise).
- Outline (laser): copper to board edge >= 0.3 mm; copper to slots >= 0.3 mm; outline tolerance +-0.1 mm (+-0.05 on request). **Gold-finger pad to board edge 0.2 mm; fingers closer are cut back** (castellations exempt).
- Panels: 2 mm spacing (3 mm with metal stiffeners); 5 mm handling edges on all 4 sides with copper pour; fiducial 1 mm, tooling hole 2 mm, fiducial centre 3.85 mm from edge, 4 fiducials with one offset >= 5 mm; support tabs 0.7-1.0 mm; max panel 234 x 490.
- Stiffeners:
  - PI: 0.1, 0.15, 0.20, 0.225, 0.25 mm. "if the connector needs to be 0.3 mm thick on a 0.11 mm FPC, a 0.225 mm stiffener thickness is most suitable."
  - FR4: 0.1, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.6 mm ("prone to chipping. Avoid if possible").
  - Stainless steel: 0.1, 0.2, 0.3 mm (good flatness, support under SMD parts; slightly magnetic).
  - 3M tape: 3M9077 0.05 mm heat-resistant; 3M468 0.13 mm not heat-resistant; tesa8854 0.1 mm heat-resistant "recommended".
  - EMI shielding film 18 um black.
- Bend radius: single layer >= 6x total thickness; multi-layer >= 10x; static 6-10x; dynamic >= 10-15x, 1-2 layers adhesive-less PI; "Avoid placing vias/pads in bend area."
- Impedance: PI er 3.3, coverlay er 2.9; impedance not controlled.
- File prep (other EDA than EasyEDA): "Put annotations on its own layer. Include the outlines of the stiffeners and indicate material and thickness. This information is not automatically parsed so stiffener options need to be set manually when ordering. Make sure that annotation text does not overlap the board area." FAQ: "standard Gerber files (RS-274X) with a separate layer for stiffener outlines (filled polygons)"; complex outlines laser cut; upload for DFM before ordering.

### 2.2 Stiffener file convention (KiCad -> JLC)
- [JGER] https://jlcpcb.com/help/article/gerber-files-preparation (updated Sep 08, 2026): recommended layer names GTO/GTS/GTL/GBL/GBS/GBO/XLN/GKO(or GM1 = outline). "Any other layers in the gerber file, such as sk, stiffener layer ... should be remarked the usage of it when placing orders. Otherwise, it/they may be ignored." Stiffener layer: "For flex boards only, and only show the information of stiffener". For flex: "you may need to set a layer to indicate the position and thickness of the stiffener you need ... when placing orders, please remember to choose the stiffener you need and remark the layer you put stiffener on." Also "put only one GKO layer in the file, and delete other GM layers or outline layers" (stated for FR-4; apply to flex too so a User-layer stiffener gerber is not mistaken for an outline).
- [JCAP] FAQ: stiffener layer = "filled polygons" in its own RS-274X gerber; annotate material + thickness; annotation text must not overlap the board.
- [KJT] kicad-jlcpcb-tools plugin README https://github.com/Bouni/kicad-jlcpcb-tools : "Additional layers can be exported by creating layers with `JLC_` as the prefix of the layer name", explicitly citing the flex stiffener case (layer outlining the stiffener top/bottom, dimensions and material properties). Issue https://github.com/Bouni/kicad-jlcpcb-tools/issues/525 is the origin ("JLC requires a dedicated layer for outlining the Stainless Steel stiffener with the specs included in the zipped gerber").
- => Practical convention for this project: rename a KiCad user layer to e.g. `JLC_Stiffener_Bottom` (works with the plugin and is self-describing if gerbers are plotted by hand), draw each stiffener as a FILLED polygon exactly where it goes, add a text note OUTSIDE the board outline ("PI stiffener 0.225 mm, bottom side, under ZIF fingers"), plot it as its own gerber, and in the JLC order form select the stiffener type/thickness and type the file name into the remark. (Convention synthesized from [JGER] + [JCAP] + [KJT].)
- Stiffener placement guidance, JLC blog/search snippets (not the capability page, lower confidence): extend stiffener 1-2 mm beyond pads; keep >= 0.5 mm from bend lines; metal stiffeners need 0.8 mm slots around them and >= 3 mm board spacing (the 0.8 mm slot / 3 mm spacing is also in [JPAN] below). Source: https://jlcpcb.com/blog/pcb-stiffeners-for-flexible-circuits (via search summary; UNVERIFIED verbatim).

### 2.3 ZIF gold-finger build for the FH34SRJ tail
- [JPI] https://jlcpcb.com/gold-fingers-pi-thickness-calculator : rule "(1) If gold fingers have copper on the back: Subtract one layer of coverlay thickness ... (2) If gold fingers have no copper on the back: Subtract one layer of coverlay thickness and then subtract one layer of copper thickness". Table: 2L 0.11 mm = coverlay 0.0275 (yellow/black) / Cu 0.012; 2L 0.12 mm = 0.0275 / 0.018; 2L 0.2 = 0.05 / 0.035; 2L 0.19 (50 um core) = 0.05 / 0.018. JLC's own example: target 0.3 mm on 0.11 mm FPC without back copper -> 0.3 - (0.11 - 0.0275 - 0.012) = 0.2295 -> "choose a PI thickness of 0.25 mm". The page's default display (1L 0.07, 0.3 mm target) shows theoretical 0.2755 -> recommended 0.25 mm.
- Worked options for our 0.3 +-0.03 target (arithmetic per [JPI] rule; the finished result is still subject to +-0.03 gold-finger tolerance [JCAP]):
  - 2L 0.12 mm (0.5 oz), no copper behind fingers: 0.3 - (0.12 - 0.0275 - 0.018) = 0.2255 -> **PI 0.225 mm** -> nominal 0.2995 mm. Best match.
  - 2L 0.12 mm with copper behind fingers: 0.3 - (0.12 - 0.0275) = 0.2075 -> PI 0.20 -> 0.2925 mm.
  - 2L 0.11 mm (1/3 oz), no back copper: 0.2295 -> JLC says 0.25 -> 0.3205 mm (inside +0.03 but at the high side); 0.225 -> 0.2955 mm.
  - 2L 0.19 mm (50 um core, tear-resistant), no back copper: 0.3 - (0.19 - 0.05 - 0.018) = 0.178 -> PI 0.15 (0.272) or 0.20 (0.322): neither lands well; the 50 um core is a worse fit for the ZIF tail. (Arithmetic; UNVERIFIED against a real quote.)
- Hirose asks for a reinforcing film 2.5 +-0.3 mm long from the tip, overlapping the coverlay by P >= 0.5 mm [H25 p.8]; the stiffener goes on the face OPPOSITE the exposed fingers.
- Gold fingers must stay >= 0.2 mm from the laser-cut edge or JLC cuts them back [JCAP]. Hirose puts conductor centres 0.5 +-0.07 mm from each side edge, i.e. a 0.3 mm wide finger has 0.35 mm to the side edge, OK. At the TIP edge, pull fingers back >= 0.2 mm (fingers still reach well into the 1.5 mm uncovered length).
- Finish: ENIG only [JCAP] (JLC offers no hard gold for flex on the capability page; Hirose recommends 0.2 um Au over 1-5 um Ni [H24 p.14]; ENIG at 1u"/2u" is thinner (~0.025-0.05 um); acceptable for a 20-cycle ZIF but note it). ENIG gold thickness conversion 1u" = 0.0254 um is arithmetic.

### 2.4 PCBA on flex
- [JPCBA] https://jlcpcb.com/capabilities/pcb-assembly-capabilities FAQ: "JLCPCB provides assembly services for FPCs. Dedicated fixtures are typically required"; "an additional fixture (tooling) fee applies ... The fixture cost is $23.57 per fixture, and the required quantity depends on your production volume"; "avoid placing large or heavy components near bending areas". Economic PCBA table lists board thickness 0.8-1.6 mm and single-sided placement only; Standard PCBA thickness "No limit", single & double sided. So a 0.12 mm flex is (by that table) Standard-PCBA territory; whether Economic accepts FPC is UNVERIFIED.
- Standard PCBA single-board size 70 x 70 mm min, panel 70 x 70 .. 250 x 250 mm [JPCBA]. A ~20 x 110 mm strip is below 70 mm in one axis -> needs a panel/rails.
- [JPAN] https://jlcpcb.com/blog/Design-Guidelines-for-Flex-PCB-Panels-on-JLCPCB (updated Jun 22, 2026): board spacing 2 mm (3 mm with metal stiffener); 5 mm process edges all sides, copper-covered except 1 mm around fiducials / 0.5 mm around tooling holes; fiducials 1 mm dia, 3.85 mm from panel edge, "one additional local fiducial next to each individual FPC unit" for SMT; tooling holes 2 mm, one fiducial + one tooling hole per corner with one corner offset >= 5 mm; tabs 0.7-1.0 mm (~1.0 mm and more of them near stiffeners); metal-stiffener 0.8 mm slots; depanel by laser-cut bridge tabs only (no V-cut/mouse bites); panel 70 x 70 min to ~250 x 500 max; customer panelizes, JLC offers a free panelization review.
- Which side / stiffener under parts: JLC recommends FR4 or stainless stiffener as SMT support ("Steel ... good as support under SMD components" [JCAP]); a hard requirement for a stiffener under small side-view LEDs is not stated (UNVERIFIED). For a DIY build the LEDs can be hand-soldered on a bare-flex order (no PCBA), which avoids the fixture fee and the 70 mm panel minimum.

### 2.5 Indicative pricing
- JLC: "Flexible PCBs start from $25 for 5 pieces with a 4 to 5 day build" (https://jlcpcb.com/blog/flex-pcb-cost-pricing-guide, Sep 01, 2026; landing page title "JLCPCB Flex PCB Special Offer from $25 5pcs" https://jlcpcb.com/RGE/FlexPCB). Layer count adds "typically 35 to 40 percent per layer" [same blog]. Lead time 4-5 days (https://jlcpcb.com/pcb-fabrication/flexible-pcb).
- An actual quote for 5 pcs of a ~20 x 110 mm 2-layer flex with a PI stiffener was NOT obtained (the instant-quote form did not render in the headless browser pane): **UNVERIFIED**. Expect more than the $25 floor once size (110 mm), PI stiffener and any coverlay colour other than yellow are added. Run the instant quote with the real gerbers before committing.

## 3. Flex design rules (IPC-2223 and best practice)

IPC-2223 itself is paywalled and was not read. The numbers below are from fabricators who cite it.

### 3.1 Bend radius
| Source | Static / bend-to-install | Dynamic |
|---|---|---|
| [JCAP] JLC capability page | single layer >= 6x total thickness; multi-layer >= 10x; "Static Bending: ... typically 6-10x" | ">= 10-15x thickness recommended"; 1-2 layers, adhesive-less PI; "Avoid placing vias/pads in bend area" |
| [JBR] https://jlcpcb.com/blog/flexible-pcb-bend-radius (May 22, 2026, upd. Sep 09, 2026), table attributed to IPC-2223 | 1 layer 6x; 2+ layers 12x | 1 layer 100x; 2+ layers 100-150x |
| [EPEC] https://blog.epectec.com/flex-circuit-design-a-guide-to-electrical-and-mechanical-integration (Mar 20, 2024) | "6x to 35x circuit thickness" depending on layer count; folded flex "zero-bend radius" with creasing allowed | "up to 100x" single layer; dynamic "typically limited to 1-layer" |
- [JBR] also: add "a 20-30% safety margin to the calculated minimum"; via-to-bend-zone clearance "1.0 mm min" static / "1.5 mm min" dynamic; >= 2.5 mm from any rigid component to the start of the bend; RA copper only needed for dynamic; 0.5-1 oz static, 0.5 oz dynamic; adhesiveless PI.
- Our case is **bend-to-install (static)**, bent once when fitted, plus maybe a few re-fits. Worked numbers (arithmetic on the rules above; JLC thicknesses from [JCAP]):
  - 2L 0.12 mm flex: 10x = 1.2 mm [JCAP] / 12x = 1.44 mm [JBR]; with +30 % margin ~1.9 mm.
  - 1L 0.11 mm: 6x = 0.66 mm; 1L 0.07 mm: 0.42 mm.
  - Wrapping around a ~2 mm thick panel edge gives an inner radius of ~1 mm (half the panel thickness), which is below the 2-layer rule. So: **route copper on ONE layer only through the fold zones** (so the fold behaves as a single-layer bend) or use a 1-layer build for the strip, and/or give the fold a larger radius with a spacer. (Design inference, not from a source.)

### 3.2 Layout best practice (sourced where possible)
- Traces perpendicular to the bend line [JBR].
- Staggered, not stacked: "Alternate the traces such that traces on the top are between the bottom traces" to avoid the I-beam effect [JBR].
- Hatched copper instead of solid pours in flexing areas: "0.38 mm trace-width and 0.63 mm spacing" hatch [JBR].
- No vias/pads in bend areas [JCAP]; via-to-bend >= 1.0 mm static [JBR]; stiffener edge >= 0.5 mm from bend lines (JLC stiffener blog via search summary, UNVERIFIED verbatim); nothing rigid within 2.5 mm of a bend start [JBR].
- Pad retention: "coverlay overlaps connector pads by at least 0.3 mm"; "add copper reinforcement around the pad and connect pad corners to the copper area" (JLC https://jlcpcb.com/blog/essential-flex-pcb-design-guidelines, Apr 28, 2025, upd. Dec 27, 2025). Same article: 0.2 mm pad-to-trace gap, 0.5 mm pad-to-pad spacing, vias >= 0.2 mm from mask openings.
- Keep coverlay over vias [JCAP]; coverlay (not LPI solder mask) is JLC's standard flex dielectric; coverlay openings expand 0.1 mm per side; bridge < 0.5 mm is removed [JCAP].
- Copper >= 0.3 mm from the laser outline and from slots; gold fingers >= 0.2 mm from the edge [JCAP].
- Curved traces (arcs, no 45/90-degree corners), teardrops at every pad/via-trace junction, anchoring spurs ("rabbit ears") on SMD pads captured under coverlay, rounded internal outline corners / tear-stop features (copper or drilled relief at slot ends): standard flex practice, but **no fabricator page read in this session gives numeric values for these: UNVERIFIED**. Suggested working values (engineering judgement, not sourced): trace arc radius >= 3x trace width; outline inner corner radius >= 1 mm (and >= 0.5 mm absolute); teardrops via KiCad 9's built-in teardrop tool.
- Strain relief at stiffener edges: stagger/neck-free traces crossing the stiffener edge and keep them perpendicular (general practice; UNVERIFIED numbers).
- Hirose: FPC routing must not load the connector; the stiffener must lie parallel to the PCB; the FPC/stiffener must not touch the case [H25 p.18].

## 4. Representing the flex in KiCad 9

Verified locally: KiCad 9.0.6 `_pcbnew.dll` contains the dielectric material strings "Polyimide" and "Kapton" (plus "FR4", "PTFE") and "Solder mask" (grep of C:\Program Files\KiCad\9.0\bin\_pcbnew.dll). `kicad-cli pcb export gerbers` supports `--layers` with untranslated names (e.g. `User.1`), `--no-protel-ext` (so Protel extensions are the default), `--no-x2`, `--subtract-soldermask`, `--board-plot-params` (from `kicad-cli pcb export gerbers --help`).

Recommended setup (synthesis of [JCAP]/[JPI]/[JGER] numbers; KiCad UI details not independently re-verified are marked):
- Board Setup > Physical Stackup: 2 copper layers; board thickness 0.12 mm (2L, 0.5 oz, 25 um PI per [JCAP]/[JPI]). Copper 0.018 mm each. Dielectric: material **Polyimide**, 0.025 mm, er 3.3 [JCAP]. F.Mask/B.Mask represent the **coverlay**: thickness 0.0275 mm (12.5 um PI + 15 um adhesive [JCAP]/[JPI]), er 2.9 [JCAP]; colour field "Yellow" (KiCad's mask colour list offering yellow: UNVERIFIED; use a custom colour if absent). Note [JPI] counts coverlay+copper inside the 0.12 mm.
- Board Setup > Solder Mask/Paste: global mask expansion 0.1 mm (coverlay expansion one side [JCAP]); minimum web width 0.5 mm (JLC removes bridges < 0.5 mm [JCAP]) so the 0.5 mm-pitch finger row becomes one gang opening. Fingers: no paste.
- Design rules (JLC 0.5 oz flex [JCAP]): min track/space 3.5 mil (0.089 mm), use >= 0.2 mm anyway; copper-to-edge 0.3 mm (0.2 mm allowed only for the gold fingers); vias 0.3/0.55 mm (keep out of bends); hole-to-copper 0.2 mm; silkscreen text >= 1 mm high, 0.15 mm line.
- Edge.Cuts: laser outline, all corners drawn as arcs (no sharp corners), tip corners R0.2 +-0.1 at the ZIF tail [H25 p.8], outline tol +-0.1 mm [JCAP]. ZIF tail width 3.5 +-0.05 mm [H25 p.9] is tighter than JLC's standard +-0.1 outline tolerance: request +-0.05 ("upon request" [JCAP]) or accept the risk (UNVERIFIED how the connector tolerates 3.6 mm; body A = 5.0 mm [H25 p.6]).
- User layers (KiCad 9 lets you rename user layers in Board Setup > Board Editor Layers): `User.1` -> `JLC_Stiffener_Bot` (filled polygons of PI stiffener, text note outside outline), `User.2` -> `Bend_Lines` (documentation only; do not send, or send with a remark), optionally `User.3` -> `Panel_Assembly`. The `JLC_` prefix is what kicad-jlcpcb-tools exports automatically [KJT]. For kicad-cli, refer to the layer by its canonical name (`User.1`), since `--layers` takes "untranslated layer names" (kicad-cli help); whether a renamed user name is also accepted is UNVERIFIED.
- Gerber job: F.Cu, B.Cu, F.Mask, B.Mask, F.Silkscreen, B.Silkscreen (only the side that has legend), Edge.Cuts, User.1 (stiffener), plus Excellon drill; Protel extensions ON (JLC recommended names GTL/GBL/GTS/GBS/GTO/GBO/GKO [JGER]); only one outline layer in the zip [JGER]; paste layers only if ordering PCBA. The Protel extension KiCad gives a User layer is UNVERIFIED (check the file name after plotting and quote it in the order remark).
- KiCad 9 has no flex-bending in the 3D viewer (rigid-flex/bend support is not in 9.x, to my knowledge: UNVERIFIED). Model folds by splitting into separate flat 3D views or by doing the fold in the enclosure CAD.

## 5. Summary of what the tail must be (for the layout agent)
- Plain rectangular tail, **3.5 +-0.05 mm wide** (6 positions), 6 fingers 0.3 mm wide at 0.5 mm pitch, outer finger centres 0.5 mm from the edges, **coverlay-free 1.5 +-0.3 mm** from the tip, **PI stiffener 2.5 +-0.3 mm** from the tip on the face opposite the fingers, overlapping the coverlay by >= 0.5 mm, tip corners R0.2, **total 0.3 +-0.03 mm** at the fingers (JLC 2L 0.12 mm + PI 0.225 mm = 0.2995 nominal), no ears/notches [H25 p.4, p.5, p.8, p.9; JCAP; JPI].
- Fingers pulled back >= 0.2 mm from the tip edge (JLC) [JCAP].
- Pick the contact side on purpose. Pin 1 is on the right when you view the finger face with the tip pointing away for TOP contact, and on the left for BOTTOM contact [H25 p.8]. Mark pin 1 and "contacts this side" on silkscreen. A mirrored tail reverse-biases both strings under OVP (section 1.4).
- In footprint coordinates the tail enters J3 from +y moving toward -y. On the main board it enters from the bottom-edge side (board +y) moving up (-y), with the J3 opening near board y ~127.8-128.1 [FP, BRD].
- Tail beyond the stiffener: widen it (the parent brief asks for a wide, non-fragile ribbon) with a generous radiused flare starting >= 0.5-1 mm behind the stiffener edge, not at it (general practice; UNVERIFIED numbers). J3 is 5.0 mm wide (A) [H25 p.6], so any flare must clear the connector body and the neighbouring parts.

Status: COMPLETE for this research pass (2026-09-24). Open UNVERIFIED items: real JLC quote; Economic-PCBA acceptance of FPC; numeric values for teardrop/anchor/tear-stop rules; KiCad user-layer Protel extension; exact J3 opening edge from the STEP solid.
