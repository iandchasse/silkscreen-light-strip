# Design notes: Silkscreen light strip, rev A

These notes explain why the strip looks the way it does. Primary sources and the working behind each number are in [research/](research/), and the reviews are in [review/](review/). The as-built numbers are regenerated into [reports/design_summary.md](reports/design_summary.md) on every build. The research and review notes are dated records. Where they differ from this document, this document is current.

**Coordinates.** Every dimension is in millimetres in the **main board's KiCad frame**: seen from the screen side, x to the right, y down.

- Everything that lies on the panel is drawn where it actually sits on the reader.
- The tail is drawn *unrolled*. It keeps its x, because every fold is about a line parallel to x, and continues in +y past the 4.26″ panel's bottom glass edge at y = 142.965.
- The enclosure (CAD) frame is X = x − 44.237 (44.24 in the enclosure code) and Y = 148.25 − y, with Z = 0 at the board's rear face and +Z toward the reader.

---

## 1. What the main board fixes

The strip replaces a bonded frontlight, so the main board decides almost everything electrical. None of it changes.

| Item | Value | Source |
|---|---|---|
| Driver | U10 TPS923610, a synchronous boost with constant current. LED_SW feeds both anodes. Q5 (warm, `W−`) and Q6 (cool, `C−`) switch the returns into R37. | silkscreen-pcb HARDWARE.md §7 |
| Current | 200 mV / R37 15 Ω = **13.3 mA** nominal, 13.9 mA worst case (reference and resistor tolerance). One string at a time. | TI SNVSCN8A §6.5 |
| OVP | TPS923610: 24.25 / 25 / 25.5 V (min / typ / max). After 3 trips it latches off, and it resets only through ADIM low for more than 2.5 ms or a VIN UVLO. | TI §6.5, §7.3.6 |
| Off-state floor | A boost cannot go below VIN. The body diode leaves a DC path from VIN (up to 5.5 V on USB) into the string, so a string must hold off **more than about 5.2 V** at µA currents, or it conducts with no regulation, even when the light is off. | TI §7.3.3 |
| Enable and dim | ADIM does both. A first HIGH of more than 40 µs enables the part, PWM at 10–200 kHz sets an analog (flicker-free) current, and LOW for more than 2.5 ms shuts it down. | TI §6.5, §7.3.8 |
| Monitor | `LED_MONIT` = LED_SW × 120 k / 1.12 M (0.1071), 10.7 ms filter | R39 / R41 / C31 |
| Protection | D3 SMAJ26A on LED_SW, and D8 PESD2IVN-UX on C−/W−, both beside J6, 140–170 mm of trace from J3. R49/R50 are 1 MΩ bleeders on C−/W−. | main-board PCB |
| Connector | J3 Hirose FH34SRJ-6S-0.5SH(50): 0.5 mm pitch, top-and-bottom contact, back-flip, for a 0.3 ± 0.03 mm FPC | Hirose FH34 catalogue |
| J3 nets | 1 LED_SW, 2 C−, 3 NC, 4 NC, 5 LED_SW, 6 W−. The fitting nails are GND, but the FPC never touches them. **The tail has no ground.** | main-board PCB |
| Design target | Good Display's -FL01C frontlight: 5 dies per string, 15 V typ, IF ≤ 15 mA | FL01C spec |

**The 3.68″ build uses a trimmed board** (cut at KiCad y 62, see the x3 case's `hardware/reference/board-trim.md`).

- Every frontlight part survives the trim: U10, L2, C9, R37, Q5/Q6, U12, R39/R41, R49/R50 and J3. The FPC slot is unchanged.
- **The trim removes D3 and D8.** On that build nothing clamps the strip's nets, so handle the strip ESD-safe and plug it in with the board unpowered.
- **On a board made before silkscreen-pcb Rev 1.01, the trim also cuts 3V3 to Q2/R81 and splits the ground.** The charger's enable stays low, so the x3 board will not charge, and the power section's ground (U3, U2, Q1) reaches the rest of the board only through one shell tab of the microSD socket. This is a board issue, not a strip issue. Two wires fix a built board, including the 2026-09-21 order: R40 pad 2 to R81 pad 2 (or bridge the two cut 3V3 stubs at the edge), and C6 pad 2 to C21 pad 2. Rev 1.01 (2026-09-30) has a 3V3 link and GND stitching vias below the cut and needs neither (silkscreen-pcb README, "Cutting the board down for a smaller display").

## 2. Electrical

### 2.1 Six LEDs per string

The string has to stay under OVP when cold and on a high Vf bin. It also has to stay above the 5.2 V off-state floor when hot, deeply dimmed and on a low bin. Rev A's first layout used five per string, the stock load; the dual-panel layout needs six pairs.

The budget below is at 13.9 mA. LED Vf is taken at the XL-4008's 20 mA bin limits, conservatively; BAV70W figures are Nexperia's; the method is the electrical review's ([review/electrical.md](review/electrical.md)).

| Case | LED_SW | LED_MONIT |
|---|---|---|
| Max: −10 °C, top bin N12-1 (datasheet 3.3 V at 20 mA) | **21.66 V**, 0.34 V under the 22 V ceiling and 2.59 V under OVP min | 2.32 V |
| Max, LCSC's "3.4 V" listing for the UWC | 22.29 V, 0.29 V over the ceiling, 1.96 V under OVP min | 2.39 V |
| Stress: 3.6 V per LED cold | 22.86 V, 1.39 V under OVP min | 2.45 V |
| Typ: 25 °C | **18.41 V** | 1.97 V |
| Min: 60 °C, bottom bin N11-8 | **15.87 V** | 1.70 V |
| Open, flipped or no strip | 23.25–25.5 V while tripping OVP (first ~0.1–0.8 s), then latched and decaying toward VIN − ~0.4 V | 2.49–2.73 V, then decaying to 0.27–0.56 V |

- **Six fits the datasheet bins.** Taking the 20 mA bin limit at 13.9 mA overstates Vf by about 0.1 V per LED, so the real worst case is nearer 21.1 V.
- **Seven would not fit:** 25.1 V worst case, over OVP, so a cold top-bin strip would latch dark.
- **The low end is fine.** Deep dim sits at about 12.8 V; one shorted LED still leaves at least 13.4 V; the off state needs only 0.87 V per LED at VIN 5.5 V.
- **Per-LED stress is unchanged:** 13.96 mA × 3.4 V = 47 mW, 67 % of Pd, allowed to about 60 °C ambient.
- **The boost** runs at duty 0.86 (0.89 with losses) at 21.7 V from a 3.0 V cell, peak inductor current about 0.24 A. That is the corner already accepted for the 22 V ceiling. Full-brightness output rises about 18 %.
- **ADC range.** The ESP32-S3 SAR ADC is specified to 2900 mV at 12 dB (ATTEN3, datasheet Table 5-6), so every reading above is in range. On a TPS923611 board the open band saturates the ADC but still clears the thresholds below.
- The strip also works unchanged with the TPS923611 alternate (OVP 29.6–31.4 V).

### 2.2 Firmware thresholds

The first layout's 2.2 V "open" threshold would call a cold six-LED strip open, because it can read 2.32 V. The replacements:

- **Open, flipped or missing:** the peak of `LED_MONIT` over the first ~1 s after enabling is **≥ 2.49 V**.
  - A lit strip reads at most 2.39 V; the OVP peak is at least 2.60 V.
  - With a ± 1.8 % divider error, that leaves about 0.06 V each side in the worst (parametric) case.
  - Once the driver latches, it stops switching and C9 drains through the divider, so record the fault when first seen. A reading that keeps falling while enabled is also a latched open.
- **Short or bridge:** below **1.30 V** at full duty, at least 50 ms after enabling. That flags two shorted LEDs and never a healthy string.
- **Colour change:** only at PWM duty 0, and for under about 1 ms. ADIM LOW for more than 2.5 ms shuts the driver down, and a low-duty carrier won't re-enable it; after a longer pause, send the ≥ 100 µs enable pulse again.

### 2.3 Why the flex carries two diodes

J3 contacts both faces of the tail, so a tail inserted face-down still makes contact, mirrored: flex contact *k* lands on J3 pin 7 − *k*.

- With one string per colour and no steering diodes, the pin map 1 C+, 2 C−, 5 W+, 6 W− cannot be wired to be flip-invariant. Anti-parallel string pairs or eight steering diodes could manage it, at the cost of 24 LEDs or about 1.5 V ([research/electrical-limits.md §7](research/electrical-limits.md)).
- A mirrored plain strip reverse-biases both strings:
  - **LEDs without an ESD Zener** see about 5 V reverse each until OVP latches.
  - **LEDs with an ESD Zener** give a string that conducts backwards with no regulation. Q6 is on by default, so that path is live even with the light off.

**Fix:** each string gets a BAV70W,115, a 100 V common-cathode pair in SOT-323:

```
LED_SW ──A1▶|──┬── K = string anode (W_A / C_A) ──[6 LEDs]── string return (W− / C−)
               └──|◀A2── string return          (A2: clamp across the LEDs)
```

| Situation | What happens |
|---|---|
| Normal | A1 conducts (+0.65–0.95 V, included in the budget above). A2 is reverse-biased at the string voltage, leaking nA. |
| Tail flipped | A1 blocks up to 25.5 V (31.4 V on the TPS923611) against a 100 V rating. A2 clamps the LEDs to within one diode drop of 0 V. No current flows in any state: the strip stays dark, the driver trips OVP three times and latches. Nothing is stressed. |
| No strip / open string | Same as flipped. This is the ordinary "light never comes on" symptom. |

Everything else on the tail follows from this:

- **Pins 1 and 5 are tied** on the flex. Both are LED_SW, so tying them halves the contact current. When the tail is flipped, the tie shorts the board's C− to W−. Both sit near GND, so this is harmless.
- **Pins 3 and 4** are isolated fingers with no trace. They are there so every contact sees the same finger.
- **No TVS on the flex.** There is no ground to clamp to. On the 4.26″ build, D3 and D8 clamp all three nets from beside J6; the trimmed 3.68″ board has neither. Treat the loose strip, and inserting it, as ESD-sensitive.

### 2.4 Behaviour inherited from the main board

- **Faint glow of the unselected string.** The deselected string sits between LED_SW and its 1 MΩ bleeder: about 3.7 µA with six LEDs. You may see a faint tint in a dark room. The stock panel does the same.
- **Colour-switch pulse.** Switching to the lower-Vf string discharges C9 through it. In the worst bin pairing (JLC cannot select bins) the peak is about 53 mA for τ ≈ 0.18 ms, under the 80 mA IFP rating. Blending is still a bench item.
- **Hot-plug.** Only plug or unplug the strip with the board unpowered, or with the light disabled for more than 30 s.

## 3. LEDs

### 3.1 Choice

About 110 catalogue queries across LCSC and JLC turned up four side-view warm/cool pairs that share a package ([research/leds.md](research/leds.md)). Only one meets every requirement:

| | XINGLIGHT XL-4008WWC / XL-4008UWC |
|---|---|
| LCSC | C5440667 (warm) / C2843774 (cool). Both are JLC Extended parts, in stock 2026-09-25 (8,840 / 6,850). |
| Size | 4.0 × 1.4 mm footprint, **0.8 mm tall**, 120° beam, emitting parallel to the board |
| CCT | 3000 K typ (bin 2900–3200 K) / 6000–6500 K |
| Vf | 2.7–3.3 V at 20 mA (bins N11-8, N11-9, N12-1), about 2.9–3.0 V at 13 mA |
| Ratings | IF 20 mA, IFP 80 mA (≤ 0.1 ms, 1/10 duty), VR 5 V, Pd 70 mW |
| Output | Cool 2600–3500 mcd, warm 5–10 lm, both at 20 mA. At 13.3 mA, about 0.72–0.75 of that. |

### 3.2 Polarity: corrected once, still worth a diode test

The datasheet's outline drawing is ambiguous about which terminal is the anode. The first layout had the LEDs reversed; the review caught it (E1 in [review/electrical.md](review/electrical.md), DFM-1 in [review/dfm.md](review/dfm.md)). A side-view LED can't be fixed by rotating it, because turning it 180° also points the light the other way. Three independent readings now agree:

1. **Datasheet p.7, third view, read as a top view.** Lens band up, pin 2 (+) on the left, and pin 1 on the right, carrying the notch mark.
2. **Datasheet p.8, the reel note and the tape cross-section.** The tape's sprocket-hole side is the part's negative. The cross-section shows the part's rear face, so the lens faces away from it.
3. **Both LCSC/EasyEDA library footprints** (C5440667, C2843774). The anode is at −x, the lens toward −y, and "−" on the right.

So, looking down on the part with the lens pointing up the page, the **anode (pin 2) is on the left and the cathode (pin 1) on the right**. On the strip each LED is rotated 270° so its light goes +x across the screen. That puts the anode toward the top of the reader and the cathode toward the bottom, so current runs down the bar through each string. A silkscreen bar marks the cathode side of every LED.

Two things remain assumptions. **Polarity:** datasheets do get this wrong, which is why [ASSEMBLY.md](ASSEMBLY.md) starts with a 30-second diode test on one loose LED. **Face position:** the footprint assumes the face is 1.0 mm ahead of the pad centreline, from the EasyEDA outline.

### 3.3 Footprint

- **Pads:** the datasheet's 1.6 × 1.1 mm pads at ±1.85 mm, with 0.1 mm trimmed off the rear edge. The trim keeps the coverlay opening 0.15 mm from the copper lane behind the pads (JLC's minimum).
- **Model:** a VRML model for renders, plus a STEP body so a plain STEP export shows the LEDs.

### 3.4 Pairs and the hinge

The LEDs sit in **six warm/cool pairs**, as professional warm/cool strips do: each cool LED sits right above its warm partner, 6.6 mm centre to centre, so both colours light the same patch of page.

The layout is chosen so one strip serves both panels:

| | Pair centres (KiCad y) | 4.26″ (active y 40.35–133.15) | 3.68″ (active y 56.86–134.62) |
|---|---|---|---|
| Top pair (D7 / D1) | 47.15 | lit; 6.8 mm from the top of the image | folded back under the bar |
| Pairs 2–6 | 64.15, 79.70, 95.25, 110.80, 126.35 (15.55 apart) | lit; 6.8 mm from the bottom | lit; 7.3 mm from the top, 8.3 mm from the bottom |

- **15.55 mm** is the 3.68″ active height (77.76 mm) divided by five, so the bottom five pairs spread evenly over the smaller screen.
- **The top pair sits 17.0 mm above the next.** That leaves room for the hinge. On the 4.26″ the six pairs then cover the 92.8 mm edge with 6.8 mm margins at both ends.
- **The hinge** is 3.6 mm of bare flex between the top pair's own stiffener piece and the bar's (y 54.275–57.900): no stiffener, no tape, no vias or pads. Its four conductors (the cool anode feed and warm anode feed on B.Cu, the warm link on B.Cu, the cool link on F.Cu) run straight across. The nearest via, the top pair's warm link, is 0.58 mm above it.
- **The fold.** On the 3.68″ the top piece folds 180° backward, tape to tape, into a teardrop that uses the whole hinge. The case agent modelled inside radii 0.35–0.63 mm; with copper on both faces a fold here is a one-time bend, so it is never creased and never re-flexed.
- **Colour mismatch.** With both strings lit equally, the worst warm-share error along the edge 10 mm into the page is 0.087 on the 4.26″ (the first five-pair layout: 0.104) and 0.097 on the 3.68″.

## 4. Geometry and fold

### 4.1 The flat pattern

| Region | Extent (flat pattern, KiCad) | Width | Stiffened |
|---|---|---|---|
| **Top piece** | x 43.00–45.30, y 39.10–54.275 | 2.3 | PI 0.225 + 3M 9077 |
| **Hinge** | y 54.275–57.900 | 2.3 | **bare** |
| **Bar** | x 43.00–45.30, y 57.90–135.50 | 2.3 | PI 0.225 + 3M 9077 |
| **Foot** | y 135.50–139.00, x 43.00–58.00 | 3.5 | PI 0.225 + 3M 9077 (one piece with the bar) |
| **Neck** | x 52.487–58.00, y 139.0 → 152.6 | 5.5 | No; bend zone y 140.7–152.3 has no vias, pads or B.Cu |
| **Back run** | y 152.615–164.85 | 5.5, tapering to 3.5 over y 160.4–164.85 | PI 0.225 (the last 14 mm); carries D13/D14 and TP1–3 |
| **Contact tab** | x 52.487–55.987, y 164.85–166.615 plus the tip | **3.50** | (same stiffener); fingers over the last 1.5 mm |

- **LED faces** are at x 45.20. The flex stops 0.1 mm in front of them, at x 45.30.
- **The foot's top edge (y 135.5)** is 0.38 mm outside the 3.68″ window (135.12) and 1.75 mm outside the 4.26″ one. Its bottom edge (139.0) sits on or just over the flat protective sheet of either panel.
- **The contact face.** Every fold is about an x-parallel axis, so x is preserved: finger 1 at x 52.987 lands on J3 pad 1. After the folds the F side faces away from the board on the back run, where J3's top contact touches it.

### 4.2 On the 4.26″ (`enclosures/case-426`, light-strip front shell)

**Placement.** The bar lies **on** the plain GDEY0426T82's left border ("above the screen"). Its outer edge is laid **0.1 mm inside** the glass edge (0 to 0.2 mm), never over it. The foot lies along the bottom border.

**Z.** The case was drawn for the 1.98 mm FT01C panel; this front shell holds the 0.926 mm plain panel instead. The FT01C no longer fits it.

- **Stops.** Three rails hang from the lip onto the panel's protective sheet and hold its front at **Z 4.00**. Every new face sits on a 0.2 mm print layer, so the model is what prints.
- **Springs.** The midplate springs deflect 0.276 mm (0.176–0.376 over the panel's ± 0.1 mm), 6.5 N in all against 8.2 N with the FT01C.
- **Ceiling.** The stack is tape 0.05 + PI 0.225 + flex 0.11 + LED 0.8, so the LED tops are at 5.185. The skin's underside over the left border rises to **5.40** (0.215 mm clearance) up to the window edge, so the light passes under it. That leaves 0.6 mm of skin, so print the tub dark or line the ceiling.
- **Window edge.** The left window edge has a 0.2 mm bevel instead of 0.6, so there is no knife edge in front of the LEDs.
- **Hold-down pads.** They bear on the bar's bare flex between the pairs, bottoms at 4.40 (0.015 mm clear). They are sized from the LEDs' **solder pads**, at least 0.6 mm clear nominally and 0.10 mm at the worst placement. They reach X 0.90, just inside the edge of the panel's e-ink film with the glass centred, so they press where it backs the protective sheet (§4.5). Because their gap is only 0.015 mm and the stiffener is held to ±0.1, the delivered strip's thickness is measured before fitting and the pads shimmed or scraped to match (ASSEMBLY §5).
- **Wall relief.** A 0.3 mm relief in the pocket's left wall, with a 43° roof, keeps the bar from ever being the panel's left stop.
- **Insertion.** The stack goes in with the glass kept toward the right wall. With the bar 0.1 mm inside the glass edge it then clears the left wall by at least 0.275 mm over the whole stroke.

**Hidden.** At the 0.1 mm-inside placement the LED faces sit 0.45 mm behind the window edge and about 1.0 mm outside the active area. The coverlay is black.

**Fold path.** The neck crosses the bare-glass ledge and wraps a U around the bottom glass edge. The inside radius is 0.7–0.9 mm: the tub has room to about 0.93, and 0.66 is the 6 × thickness minimum for single-layer copper. It then runs back under the glass, drops 90° through the board's FPC slot (y 141.2–142.5), and turns 90° onto the back to J3. The front shell's ribbon gap is widened to X 7.7, which leaves the neck 0.55 mm of clearance, and the U reaches about 1.7–2.1 mm past the glass edge.

- **SW9's left lug lead** stands to Z 2.31, 0.10 mm (0.26 mm as placed) beside the U's lower leg. At the far-left extreme they overlap, so trim it flush and cover it with Kapton (ASSEMBLY §5 step 1).
- **The EPD FPC.** The neck's right edge is about 0.35 mm from the panel's own FPC at the 0.1 mm-inside placement. The U must not ride onto it.

### 4.3 On the 3.68″ (`enclosures/case-368`: light-strip front shell, midplate, its own bottom keys, one lid latch arm)

**Placement.** The 3.68″ glass starts at x 45.367, just right of the bar (x 43.00–45.30), so the bar lies **beside** the panel ("next to the screen"), 0.07 mm from the glass. It rests on a shelf in the front shell at the panel-front plane (Z 3.47), so the LEDs still sit above the page and graze it. The foot lies on the 3.68″ panel's bottom border.

**Z.** The x3 front skin was only 0.6 mm over the panel, and the strip stands 1.185 mm tall.

- The light-strip front shell raises the whole front by **1.2 mm** (Z 4.07 → 5.27), keeping one flat face so it still prints face down. The case goes from 11.3 to 12.5 mm deep, and the LED tops (4.655) clear the skin by 0.215.
- A channel runs along the left edge for the bar, with the light path under 0.4 mm of skin to the window. The window has a 0.6 land and a 1.2 mm 45° bevel, so the thicker border skin doesn't shade the edge.
- **Six stop ribs** (0.18 mm) on the channel's wall set the bar's left edge at X −1.24. They sit between the lid's latch arms; the two on the fold zone also stop the folded piece.
- **Seat.** The bar's tape side rests on a strip of the old frame at the panel-front plane, over Y 14.5–73.4. It starts at 14.5 so a bar sliding in with a thick stack and a 0.9 mm LED clears its edge; the G-code puts its first line at Y 14.72.
- **The foot is the panel's stop** at the bottom-left corner. The lip there is gone, and the foot pocket's roof (Z 3.87) sits 0.015 over the foot. The midplate spring under that corner deflects 0.04–0.33 mm (0.2–1.8 N).
- **Corner stops** at the panel's two left corners locate its left edge, now that no wall is beside it. They face the glass edge's full thickness (Z 2.47–3.27) at every panel tolerance, with through-notches in the midplate under them.
- The left lip is gone (it was in the light path), so small hold-down pads between the pairs hold the panel's left border. Pads 1–4 each hang from a 2 mm rib under the channel ceiling, which keeps the border within about 0.03 mm of the other three. Pads and ribs shade about 4.8 % of the light, all of it steep rays.
- **Bottom keys.** Since Rev L (2026-09-26) the keys are straight sliding keys on bell cranks (the case README's "Bottom keys"). Each stands 1.5 mm over its own tub's face, so the light-strip build has its own four keys (`key-x3ls`), 1.2 mm taller than the standard build's; the cranks, the rod and the gate are shared. (Until then the rocker caps were 0.155 mm taller and flush in wells.)

**The fold-back.** The top piece folds 180° backward at the hinge and lies under the bar, its LEDs facing the back. The front shell's frame is removed there (Y 73.4–92.7), and the **midplate is notched through** under it, on into SW7's two front lead holes so no web narrower than a printed line is left. Nothing else in the midplate changes except one detent, moved from Y 86 to 58, clear of the fold.

- **Lid latch arm.** The folded pair's D1 lies over the lid's left latch arm at Y 83. That arm gets a 0.5 × 0.5 mm chamfer on its inner top corner, so D1 clears it in every case: strip at the ribs or against the wall, 0.8 or 0.9 mm LED, nominal or thick stack, at rest and while the lid snaps on. The worst case clears it by 0.10 mm as modelled and 0.066 mm in the sliced G-code. The barb, catch and lead-in are untouched, so the latch holds as before. This is the lid's only change.

**Fold path.** The x3 panel's bottom glass edge is the board slot's top edge (y 141.2), so the neck folds 90° over it straight down the slot. That path needs 19.8–21.3 mm, against the 25.4 mm the strip has from that edge, so the 3.68″ build has **4–5.6 mm of spare tail**. It goes into a small loop into the chin (a new neck gap in the front shell makes room) and a hairpin loop on the board's back that stands about 2–3 mm off the board. The lid clears it by about 2.9 mm.

### 4.4 Tail length

`tools/foldpath.py` sweeps each reader's path (bend radii, overhang, drop position, J3 insertion ± 0.3):

| | Needed, glass edge to tip | The strip has | Spare |
|---|---|---|---|
| 4.26″ (U) | 21.5–23.2 mm (22.5 nominal) | 23.65 mm | 0.5–2.2 mm, into the U |
| 3.68″ (90° fold) | 19.8–21.3 mm (20.5 nominal) | 25.4 mm (the glass edge is 1.77 mm higher) | 4.1–5.6 mm, into the chin loop and the back loop |

On the 4.26″ the bends end by flat y 150.5, and on the 3.68″ by about 146 plus its loops. The back stiffener starts at 152.6, so it never sits in a bend.

### 4.5 How the panel is held

A review compared each light-strip case with its original, measuring the models and modelling the glass as a plate on its springs and stops (2026-09-25/26). An independent check confirmed each figure. Neither case lets the panel rattle: every border has a front stop and the springs keep it clamped at every tolerance.

| | 4.26″ | 3.68″ |
|---|---|---|
| Spring preload | 6.5 N (8.2 N on the FT01C); lift-off 34 g against 27 g, since the plain panel is half the mass | 7.5 N, unchanged (3.7–11.2 N over tolerance) |
| Front stops | Rails on the right, top and bottom (the original lip was a closed frame); the left border only through the strip, under 7 pads | The original lip on three sides; the left border on 4 ribbed pads; the bottom-left corner on the strip's foot |
| Left border against the rest | Within ±0.1 mm, set by the strip's thickness, hence the fitting check | About 0.03 mm proud (0.07 in a 200 g knock); it was 0.07–0.10 before the ribs |
| In-plane location | The original pocket, 0.35–0.55 mm play | 0.28 mm play; two full-depth corner stops on the left |
| Glass bending | About twice the original's, 8–14 MPa | 30–50 % higher at one spot, about 12 MPa; the same as the original in a drop |

The original 4.26″ tub cannot hold the plain panel at all: it would sit 0.7 mm loose with no preload. On the first print, look for marks on the protective sheet under the pads and rails, and check the left border's height against the other three.

## 5. Robustness

The brief called for a ribbon that is "wide, not fragile, and has no sharp corners", and for an intermediate section that resists tearing and broken series connections:

- **Outline.**
  - The bar ends in a full round.
  - The bar → foot and foot → neck outer turns are **R3.5 and R4.0**, the full height of the foot, so they barely read as corners.
  - The neck → tab taper uses two R3.0 sweeps; the concave neck corner is R1.6.
  - Only the two R0.2 tip corners (Hirose) and one R1.0 inside corner on the stiffener are small.
- **Neck.**
  - It is **5.5 mm wide**, while J3 only needs 3.5 mm at the tab.
  - It carries **four 0.4 mm conductors at 0.8 mm pitch**, 1.15–1.55 mm in from the edges.
  - Through the folds the conductors run straight and cross the fold lines at right angles.
- **Single-layer copper in the bends.** There is no B.Cu between y 139.85 and the LED_SW tie on the back run. Two rule areas cover the bend zone: no vias or pads on either layer, no B.Cu tracks.
- **Tear-stop rails.** An unconnected 0.3 mm F.Cu rail runs 0.3 mm in from each neck edge; a B.Cu arc reinforces the concave neck corner.
- **The hinge.** It has no vias, pads, stiffener or tape, and straight tracks. It is bent once, on the 3.68″ only, into a teardrop, never creased. On the 4.26″ it lies flat.
- **Teardrops.** There are 42 net-assigned teardrop polygons wherever a narrow track meets a pad or via.
- **Stiffeners.** The bar and foot are one PI piece and the top pair has its own, so no LED joint ever flexes. The back-run stiffener covers the diodes, test pads, taper and tab.
- **Why this matters.** Each colour is one series string, so any broken conductor darkens that colour.

## 6. Optics

`tools/optics_sim.py` treats each LED as a point source 0.785 mm above the page: tape, stiffener, flex, plus half the LED. On the 3.68″ the bar sits on a shelf at the panel-front plane, so the height is the same. The beam is 120° (cos¹), aimed parallel to the surface. Irradiance on a flat matte page is E = I·cos(incidence)/r².

| | 4.26″, 6 pairs | 3.68″, 5 pairs lit | 4.26″, first layout (5 pairs) |
|---|---|---|---|
| LED face to image | 1.20 mm | 2.37 mm | 1.20 mm |
| 2 mm / far edge | 233 | 176 | 179 |
| 10 mm / far edge | 37 | 28 | 37 |
| 20 mm / far edge | 9.9 | 8.2 | 9.9 |
| Ripple along the edge, 3 mm in | 13.5 | 5.0 | 18.0 |
| Ripple, 6 mm in | 3.1 | 1.9 | 3.7 |
| Ripple, 10 mm in | 1.5 | 1.3 | 1.6 |
| Colour mix error, 10 mm in | 0.087 | 0.097 | 0.104 |

- **Grazing light is steep.** No placement fixes that without a light guide, which was out of scope. A real e-paper front film scatters, so the far side looks brighter than this geometry predicts. The shape of the gradient still holds.
- **The 3.68″ edge is softer** because its LED faces sit 2.37 mm from the image, beside the glass, instead of 1.2 mm.
- **Why the long edge.** From the top short edge the same six pairs would have to throw light 92.8 mm instead of 55.7 mm: 2017:1 at 2 mm and 47:1 at 20 mm, 5–10 times worse.

## 7. Flex build and DFM (JLCPCB)

| | Rev A | JLC limit / Hirose requirement |
|---|---|---|
| Stack | 2 layers, finished 0.11 mm, 25 µm adhesiveless PI core, 1/3 oz (12 µm) Cu, 12.5 µm PI + 15 µm adhesive coverlay | — |
| Coverlay / silk / finish | Black / white / ENIG | Yellow is the default; ENIG is the only flex finish |
| Track / space | 0.20 minimum used (0.15 in the rules) / 0.15 | 3/3 mil on 1/3 oz |
| Vias | 16, 0.30 / 0.55, all tented except the same-net LED_SW via inside TP1; none in the bends or the hinge | Regular 0.3 / 0.55 |
| Copper to edge | ≥ 0.30 (DRC) | 0.3 |
| Gold fingers | 0.30 wide at 0.50 pitch; ends 0.20 from the tip; gang coverlay opening over the last 1.5 mm | Finger-to-edge 0.2; Hirose: exposed 1.5 ± 0.3, conductors 0.3 ± 0.03 |
| Contact thickness | 0.11 − 0.0275 − 0.012 + 0.225 = **0.2955** nominal (no back copper behind the fingers) | Hirose 0.30 ± 0.03, JLC ± 0.03 |
| Tab width | 3.50 | Hirose 3.5 ± 0.05 (ask for ± 0.05 in the remark) |
| Stiffener | PI 0.225, B side, **three pieces** (79 % of the board area) | Choose it on the form and name the file in the remark |
| Tape | 3M 9077 on the two front pieces, over the stiffener ("stacked stiffener") | Extra fee |
| Coverlay webs / openings | Every web ≥ 0.5 (0.55 between D14 and D13, 0.50 from each diode to its same-net test pad). Every opening ≥ 0.15 from other-net copper and ≥ 0.225 from via rings, except the deliberate via in TP1. | Web ≥ 0.5; opening-to-trace ≥ 0.15; via ≥ 0.2 from openings |
| Silkscreen | 1.0 mm text, 0.15 mm lines, clipped off every opening, kept off the creases; ticks mark the hinge ends | ≥ 1.0 / 0.15 |

The ordering steps are in [ORDERING.md](ORDERING.md).

## 8. Verification

Every build (`tools/make_outputs.py`) re-runs the following and fails if any count is not zero:

- **ERC and DRC.** ERC checks all severities; DRC also checks schematic parity and unconnected items. The result is **0 / 0 / 0 / 0**, with nothing excluded.
- **Outputs.** Gerbers, drill, BOMs, CPL, PDFs, flat STEP/VRML and renders.
- **Coverlay clearance and webs.** DRC can't see them, so they are measured separately with pcbnew shape collisions (§7).

The strip has had four review rounds:

1. **Independent review before rev A.** Four lenses: electrical, mechanical, DFM, KiCad ([review/](review/)).
2. **Final check of the docs and board.** 42 confirmed findings, including the P03 case clash that led to this dual-panel design.
3. **Dual-panel survey.** Both cases, the 3.68″ panel and the six-LED budget.
4. **Each case variant built, then fixed and adversarially re-measured in rounds:** three on the 4.26″ case, four on the 3.68″. The last 3.68″ round applied Ian's decisions (flush rocker caps, since replaced by the Rev L keys; the lid latch-arm chamfer) and was checked by two independent verifiers. Each case README's "Light-strip variant" section has the numbers; the remaining items are in §9.

| Finding | Resolution |
|---|---|
| E1 / DFM-1: LED polarity reversed | Re-derived three ways (§3.2); footprint and string topology corrected; cathode silk marks; diode test is step 1 |
| E2 / DFM-2: BAV70W CPL 180° off | Per-footprint rotation offset in `make_outputs.py` |
| M1–M6: visibility, diode height, SW9 lead, instructions, bend zone, glass overhang | Foot moved under the lip, diodes on the back run, Kapton on SW9, these docs, bend zone and ticks, `outer_x` 43.00 |
| DFM-3 – DFM-10: coverlay clearances and webs, test pads, bend-zone layer, stiffener corners | All measured and fixed (§7) |
| K1 – K12: project hygiene | Exclusions cleared, own template, env paths, schematic and silk fixes, STEP body |
| Final check: title block, BOM, job file, PDF path, LED_MONIT decay, colour-change dwell, S-to-C/W short check | Fixed in the generator, the output script and the docs |
| P03 case clash | Superseded: the strip now targets the two enclosures in `enclosures/`, where the fold fits |
| Dual-panel: 5 → 6 pairs, hinge, lower foot, shorter tail, new LED_MONIT threshold | §2–§4 |
| Case variants: see each case README's "Light-strip variant" section for the per-case findings and fixes | — |

## 9. Open items

1. **LED polarity and face position** are derived from documents, not measured. Diode-test one part (ASSEMBLY step 1). If the anode turns out to be on the other side, the footprint and routing must be mirrored.
2. **Six LEDs per string** assumes the XL-4008 bins as published. If a batch reads above about 3.4 V per LED at 13 mA, the string can pass the 22 V ceiling in the cold (still under OVP). Check one string on the bench (ASSEMBLY step 3).
3. **The hinge fold** has not been bent on a real board. Fold one bare board before trusting it.
4. **The bottom keys (Rev L, both cases).** The 4.26″ case has been printed twice. In the first print the keys bound in their openings; the 2026-09-29 refit gave them 0.40 on the chin side and 0.35 per side across. In the second (2026-09-30) the keys tilted, sat low, stuck or fell out: their drag leaf held each key wherever it was left. The keys are now **hook keys**: two rigid hooks per key run in two slots in the tub's chin wall and stop 1.0 mm out, and nothing on the key flexes or rubs. They are not printed yet: reprint the tub and the 4 keys, and keep the tub face down from the keys until the board is in (`print/README.md`). The chin coupon on plate 3, with one key, is an optional fit check; print the gate coupon first, and check a real TS365ZJ against its drawing before printing crank-T.
5. **Board issues on the x3 build** (§1): no D3/D8, which is accepted and not being changed, so handle the strip ESD-safe. On boards made before silkscreen-pcb Rev 1.01 the trim also cuts 3V3 to the charger enable and splits the power-section ground; those boards need the two wires in §1. Rev 1.01 fixes both on the board.
6. **Cost.** No instant quote has been run.
7. **Antenna.** The bar passes 5–8 mm from the ESP32-S3 antenna. Compare RSSI with and without the strip.
