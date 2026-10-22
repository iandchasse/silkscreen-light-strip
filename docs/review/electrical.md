# Electrical and polarity review: silkscreen-light-strip rev A

Reviewer lens: LED polarity, net correctness, voltage and current budget, and flip and fault behaviour.
Date 2026-09-25. Everything was read-only: no `.kicad_*`, lib or tools file was touched. Scratch work was not kept.

## Verdict

**Do not order assembly yet.** The nets, the diode pinout, the map of J1 (the contact tail) and the voltage budget all check out.
The LED polarity does not. I re-derived it three independent ways (the tape cross-section, the manufacturer's
reel note, and both EasyEDA/JLC library footprints). All three put the **cathode on the RIGHT** in top view with
the light going up (-y), which is the **opposite** of the footprint (`pad 1 = K at x = -1.85`, on the left).
The datasheet drawing is ambiguous, so this is a **medium-confidence (~65 %) "reversed"**, not a certainty.
Either way, the polarity is unverified.

A side-view LED can't be fixed by rotating it, because a 180-degree turn also reverses the light. A reversed
assembly would therefore be dead flex. A $1 sample and a multimeter diode test settle the question before the order.

| ID | Severity | Title |
|---|---|---|
| E1 | BLOCKER | XL-4008 polarity is unverified, and independent evidence says the footprint is reversed |
| E2 | MINOR | D11/D12 CPL rotation is 180 deg off from JLC's BAV70W (C28064) library footprint |
| E3 | NOTE | If E1 is real, the BAV70W clamp does not protect: each string sits at about -24 V (~4.7-5 V per LED, at the 5 V VR rating) until OVP latches |
| E4 | NOTE | Colour-switch transient with worst-case Vf-bin mismatch: ~50 mA peak, still under IFP 80 mA |
| E5 | NOTE | LCSC parametrics disagree with the datasheets on Vf (UWC "3.4 V"); the budget still holds at 3.6 V |
| E6 | NOTE | The unselected string glows at ~1-3 uA through the main board's bleeders R49/R50. This is a main-board behaviour, slightly reduced by the BAV70W |

---

## E1 (BLOCKER): LED polarity is unverified and probably reversed

**Design as built.** `lib/.../LED_SideView_XINGLIGHT_XL-4008.kicad_mod`:

- Pad 1 is at (-1.85, 0), F.Fab "K". Pad 2 is at (+1.85, 0), "A".
- The body F.Fab rect runs from y = -1.0 to +0.4, and the light goes toward -y. So the emitting face sits 1.0 mm
  ahead of the pad centreline, on the side away from the terminals.
- The placement is rot -90, with pad 1 at -y (design_summary: D1 pad 1 @ 44.200,126.660 on `/W1_2`).

The `generate.py` docstring (lines 148-151) gives the rationale: "tape drawing (a top view: face to the right,
cathode bar at the top)" plus "outline drawing's bottom view".

**What I checked independently.**

1. **Which face emits (agrees with the design).** I pulled the LCSC 3D model for C5440667 from
   `modules.easyeda.com/3dmodel/8474eeb1...`:
   - The yellow lens material has its outer face at model y = -0.498.
   - The metal terminals sit only at model y = +0.08...+0.82, the side away from the lens.
   - Mapped through the footprint's SVGNODE (c_rotation 0,0,180), the lens lands at screen -y (up) and the
     terminals at +y.
   - The LCSC photo on a black background (`..._C2843774_blank.jpg`) shows the same thing: terminals on the rear
     half, lens on the front face.

   So the lens is on the narrow 2.86 mm body portion, away from the terminal ("wide 4.0") portion. The design's
   "light toward -y, pads 0.4 mm from the rear edge" matches.
2. **Which end is the cathode (disagrees with the design).**
   - **Reel note (p.8, rendered).** The note reads "载带链条孔一侧为元件负极方向": the sprocket-hole side of the carrier
     tape is the component's negative side. The diode symbol beside the pockets has its bar toward the sprocket
     holes. The designer reads it the same way.
   - **Tape cross-section (p.8, right of the pocket strip; native raster upscaled, `xsec_native.png`).**
     - The part drawn in the pocket is the **rear** view of p.7 (the round ejector mark, the rear chamfers, and
       the terminal feet toward the pocket floor). It is not the lens view, which shows the window and die square.
     - The cover-tape side is drawn adjacent to the top view and the pocket protrudes away from it, which is
       third-angle.
     - So the face turned toward +x (right) in the tape top view is the **rear**, and the lens faces **left**.
     - The ")" notch that the designer took for the lens sits on the right, rear edge. That matches the p.7 outline
       view, where the trapezoid recess is also on the rear (terminal-side) edge.
     - The pocket parts are a generic template, about 3.0 x 0.94 mm scaled off the 4.0 mm pitch, not this
       4.0 x 1.4 part. Their outline alone should not be trusted for the lens direction.
   - **Putting it together.** Tape top view: lens left, cathode toward the sprocket holes (up). Rotate 90 deg so
     the lens points up: the cathode ends up on the **RIGHT**.
   - **p.7 outline view read as a TOP view** (it is unlabeled): lens (narrow portion) at top, "1" (cathode, "mark"
     notch) on the **right**. This is the same answer. The designer's reading needs this view to be a *bottom* view.
   - **Both EasyEDA/JLC library footprints** (`easyeda.com/api/products/<C>/components`):
     - C5440667 (author LCSC) has pads 1/2 at x = 4033.3/4047.9, silkscreen "+" beside the LEFT pad and "-" beside
       the right pad. Its symbol says pad 1 = A, pad 2 = K.
     - C2843774 (a different author) has pad 1 (symbol "C", cathode) on the RIGHT, "-" on the right and "+" on the
       left.
     - Both have the lens toward -y (the terminal lead shapes are on +y).
     - So both say anode LEFT, cathode RIGHT with the lens up, the mirror of the design. They may simply be copies
       of the p.7 view read as a top view, so they count as weak corroboration rather than proof.
3. **What supports the designer.** The p.7 outline view sits below the lens view with the lens edge adjacent to it,
   which is the third-angle *bottom* view convention. But the rear view sits between them, and the side view is
   only consistent if it was projected from the rear view. The page layout follows no single projection convention,
   so it can't settle the question. I found no labelled "TOP VIEW" or "BOTTOM VIEW" anywhere in the datasheet.
   The LCSC photos are too low-resolution to show the pin-1 notch relative to the lens with confidence.

**Consequences if reversed.**

- Both strings block, so no light.
- The boost ramps to OVP (24.25-25.5 V) and latches after 3 trips.
- Each string carries about 23.3-24.8 V reverse, see E3.
- JLC will place the parts with the lens toward +x whatever their polarity. The LEDs have **no silkscreen at all**
  (reference hidden, no polarity mark; checked with pcbnew), so JLC's DFM can't catch the error.
- There's no in-place rework. Rotating 180 deg makes the LED shine into the bezel, and a flipped tail doesn't help
  because the BAV70W A1 diodes block that path too.

**Fix.**

1. Before ordering, buy about 5 of each LED from LCSC (under $1). Put a DMM in diode mode across the terminals:
   the LED glows faintly when the red probe is on the anode. Note which end is the anode with the lens facing away
   from you and the part standing on its feet.
2. If the result confirms a reversal, swap the pad numbers in `write_led_fp()` (pad 1 at +1.85, pad 2 at -1.85),
   keep the body and light direction, and regenerate.
3. Add a small silkscreen polarity mark ("+" beside the anode pad, clear of the light path) so JLC's DFM checks the
   physical part against the board.
4. Alternatively, order the flex with the LEDs unpopulated and hand-place them after the diode test.

## E2 (MINOR): D11/D12 rotation in the CPL does not match JLC's footprint

- JLC's C28064 (BAV70W,115) footprint puts pads 1 and 2 at x = 402 (right side, pad 1 lower) and pad 3 at x = 394
  (left side).
- The KiCad `SOT-323_SC-70` puts pad 1 at (-1, -0.65), pad 2 at (-1, +0.65) and pad 3 at (+1, 0).
- So the EasyEDA footprint at 0 deg equals the KiCad footprint at 180 deg.
- D11/D12 are placed at 180 deg in KiCad, and `production/jlc_cpl.csv` passes `180.0` through unchanged
  (`make_outputs.py` line 132: `Rot % 360`, with no per-package correction). JLC's footprint at 180 deg equals
  KiCad at 0 deg, which is 180 deg off the copper: the single cathode pin would land between pads 1 and 2.
- JLC's preview usually catches and fixes an error this obvious (SOT-323 fits in only one orientation), but expect
  a DFM query.
- **Fix:** add a +180 correction for `SOT-323*` in `cpl()` so D11/D12 go out as 0.0, and check the JLC placement
  preview.
- The LEDs need no correction: both the JLC footprint and the KiCad footprint have the lens toward -y at 0 deg, so
  270 puts the light toward +x.

## E3 (NOTE): Reverse stress if E1 is real

In the normal insertion with reversed LEDs:

- A1 conducts, and the string blocks.
- A2 (anode on the string return, cathode on the string anode) is reverse-biased, because W_A is high and W- is
  low. It does not clamp.
- The string therefore carries V_OVP - V_A1 ≈ 23.3-24.8 V reverse. That is about 4.7-5.0 V per LED on average,
  and uneven sharing can put one LED above the datasheet VR of 5 V (Ir ≤ 5 uA @ 5 V).
- The exposure is short: 3 OVP trips, then the part latches. InGaN parts usually survive this.
- It is no hazard to the main board: its clamp D3 SMAJ26A (VBR ≥ 28.9 V) stays off, and the clamp D8 sees only the returns near 0 V.

## E4 (NOTE): Colour-switch pulse

- JLC can't choose bins. The worst case is warm N12-1 (3.1-3.3 V) against cool N11-8 (2.7-2.9 V), which gives
  ΔV up to 0.6 V per LED, or 3.0 V per string.
- When the colour switches to the lower-Vf string, the driver's output capacitor C9 (~2 uF effective) discharges through it: 5 LEDs at about
  12 ohm dynamic each, plus the BAV70W, the current-set resistor R37 15 ohm and the BSS138, about 80 ohm in total.
- Result: about +37 mA on top of 13.9 mA, so **~50 mA peak** with τ ≈ 0.16 ms, once per switch.
- That is below the IFP of 80 mA (≤ 0.1 ms, 1/10 duty, datasheet p.3). It is acceptable, but it is worse than
  the 1 V estimate in `electrical-limits.md` §5.

## E5 (NOTE): Vf data disagree

- The LCSC parametric says UWC "Vf 3.4 V" and WWC "2.9-3.3 V".
- Both datasheets (p.3/p.4) say 2.7-3.3 V at 20 mA, in bins N11-8, N11-9 and N12-1.
- With 3.6 V per LED cold, the worst string is 5 x 3.6 + 0.95 + 0.1 + 0.206 = 19.3 V. That is still under the
  22 V ceiling. No action needed.

## E6 (NOTE): Unselected-string glow

- The deselected string runs from LED_SW (~15.5 V) through its BAV70W and 5 LEDs to R49/R50 (1 Mohm to GND).
- At µA currents the drop is about 5 x 2.4 V + 0.35 V ≈ 12.4 V, which leaves roughly 1-3 µA.
- This may show as a faint tint in a dark room. It is the stock-panel behaviour and not new; the series diode
  slightly reduces it.

---

## Verified OK (with evidence)

- **LED chains** (design_summary pad nets, confirmed by pcbnew load):
  - Warm: W_A → D1.2(A); D1.1(K) = W1_2 = D2.2 → ... → D5.1(K) = W-.
  - Cool: C_A → D6.2(A) → ... → D10.1(K) = C-.
  - Symbol pin 1 = K, pin 2 = A (`Sim.Pins 1=K 2=A`), consistent with the footprint K/A labels. The chains are
    right *given* the footprint's pad-1 = K assumption (E1).
- **BAV70W pinout.** Nexperia BAV70_SER Rev. 8, Table 3: BAV70W pin 1 = anode (diode 1), pin 2 = anode (diode 2),
  pin 3 = common cathode. On the board:
  - D11: pad 1 LED_SW (A1, series), pad 2 W- (A2, clamp), pad 3 W_A (K).
  - D12: pad 1 LED_SW, pad 2 C-, pad 3 C_A.
  - Both are correct.
- **BAV70W part.** C28064 is "BAV70W,115, Nexperia, SOT-323, 1 pair common cathode, 100 V", with 21,660 in stock.
- **J1 vs J3.** Read-only on `silkscreen-pcb/silkscreen_pcb.kicad_pcb`:
  - J3 (the main board's frontlight connector; B.Cu, rot 180) pads: 1 LED_SW @ x 52.987, 2 C- @ 53.487, 3/4 unconnected @ 53.987/54.487,
    5 LED_SW @ 54.987, 6 W- @ 55.487.
  - J1 fingers carry the identical nets at the identical x. All folds are about lines parallel to x, so x is
    preserved.
  - J3 is dual-contact, so the contact face doesn't matter.
  - Pins 3/4 are isolated pads. The pin 1/5 tie matches the board.
- **Test pads.** TP1 = LED_SW, TP2 = C-, TP3 = W-.
- **Main-board context** (pcbnew; U10 is the frontlight driver, J6 the expansion header, Q5/Q6 the warm/cool string switches, R39 the top of the monitor divider):
  - LED_SW connects to U10.5, C9, D3 SMAJ26A, R39 1M, J3.1/5, J6.5 and TP3.
  - W- connects to Q5.3, R50 1M, D8, J3.6 and J6.6. C- connects to Q6.3, R49 1M, D8, J3.2 and J6.11.
  - The Q5/Q6 sources go to U10.3 and R37 (15 ohm), so the FB current is 0.2 V / 15 ohm = 13.3 mA.
- **Voltage budget at 13.9 mA** (LED datasheet p.3/p.5; Nexperia BAV70_SER characteristics table: VF ≤ 855 mV @ 10 mA, ≤ 1 V @ 50 mA; BSS138 drop assumes R_on ≤ 7 ohm at VGS 3.3 V (not verified); LED Vf at 13.9 mA taken conservatively as the 20 mA bin limit, cold +3 mV/K, hot -3 mV/K):

  | Case | LEDs (5x) | BAV70W | BSS138 | FB | LED_SW | LED_MONIT (x0.1071) |
  |---|---|---|---|---|---|---|
  | Max: -10 C, N12-1 bin | 5 x 3.40 = 17.0 | 0.95 | ≤0.10 | 0.206 | **18.3 V** (22 V ceiling −3.7 V; OVP min −6.0 V) | 1.96 V |
  | Typ: 25 C | 5 x 2.90 = 14.5 | 0.78 | 0.03 | 0.200 | 15.5 V | 1.66 V |
  | Min: 60 C, N11-8 bin | 5 x 2.50 = 12.5 | 0.65 | 0.02 | 0.195 | 13.4 V | 1.43 V |
  | Open or flipped (OVP) | — | — | — | — | 24.25-25.5 V | 2.60-2.73 V |

  - Deep dim and the off state (µA) stay at ≥ ~11 V, far above the 5.2 V off-state and ~6.5 V regulation bounds.
  - The normal maximum (1.96 V) and the open/flipped reading (2.60 V) are 0.64 V apart, so the firmware threshold
    of ~2.2 V separates them cleanly.
- **LED current rating.** 13.9 mA is 70 % of IF 20 mA. PD is about 13.9 mA x 3.4 V = 47 mW, 67 % of 70 mW. The
  derating curve (UWC datasheet p.5) is flat to ~28 C and then linear to 10 mA at 85 C, so 13.9 mA is allowed up to ≈ 63 C
  ambient. That is above the panel's 0-50 C operating range.
- **Flipped tail** (finger k lands on J3 pin 7-k):
  - Board LED_SW drives the flex W- and C-.
  - A2 forward-biases toward W_A/C_A, but that node has no sink, because A1 is reverse-biased (K high, A at the
    board W-/C-, near 0 V).
  - The LEDs sit at -0.2...-0.5 V (one A2 drop at nA).
  - A1 blocks ≤ 25.5 V, against a 100 V rating.
  - The result is an open load: 3 OVP trips, then the latch. No current path, no main-board stress (D3 stays off;
    D8 and the board W-/C- sit near 0 V).
  - The strip's pin 1-5 tie shorts the board's W- and C- drains together, which is harmless.
- **BAV70W leakage and capacitance.** IR ≤ 30 nA @ 25 V (25 C). Even ×20 hot, it is < 1 µA, under 5 % of the
  0.1 % ADIM current (≈ 20 µA) and negligible at full current. Cd ≤ 1.5 pF, and trr 4 ns: irrelevant at the
  1.1 MHz switching and 10-200 kHz ADIM.
- **Trace IR drop.** The longest return (C-, ~144 mm of 0.2-0.45 mm copper) drops under 20 mV at 14 mA. The
  driver is constant-current, so this doesn't matter.
