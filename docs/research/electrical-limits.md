# Electrical limits for the silkscreen-light-strip LED strings

Research notes, 2026-09-24. Every number is cited. **UNVERIFIED** marks generic engineering values or
things no primary source confirmed; swap in the chosen LED's datasheet curves before layout sign-off.

Source key:

- **[TI]** TPS923610/1/2 datasheet, SNVSCN8A (Sep 2025, rev. Oct 2025), https://www.ti.com/lit/ds/symlink/tps923610.pdf
- **[HW]** `de-link_pcb/docs/HARDWARE.md` §7 "Frontlight driver" (lines 749-861) and the USB note at lines 210-228
- **[DR]** `de-link_pcb/DESIGN_REVIEW.md` §8 "Frontlight" (lines 375-429)
- **[RM]** `de-link_pcb/README.md` lines 216-251 (TPS923611 swap)
- **[PCB]** `de-link_pcb/silkscreen_pcb.kicad_pcb`, pad nets read with pcbnew (read-only) on 2026-09-24
- **[FL]** Good Display GDEQ0426T82-FL01C specification, https://www.good-display.com/companyfile/1946.html
  (PDF: https://v4.cecdn.yun300.cn/100001_1909185148/GDEQ0426T82-FL01c-specification.pdf)
- **[HRS]** Hirose FH34 page, https://info.hirose.com/products/fh34 , and the catalog title at
  https://www.hirose.com/en/product/document?clcode=&productname=&series=FH34SRJ&documenttype=Catalog&lang=en&documentid=en_FH34_CAT

---

## 0. Summary

| Item | Value |
|---|---|
| String current (fixed by main board) | 13.33 mA nominal, 13.87 mA max (ref + 1 % R), 13.96 mA with 60 C drift [DR §8 table] |
| Hard upper limit, V_OUT at the IC | **< 24.25 V** (TPS923610 OVP rising min, TJ <= 85 C) [TI §6.5]; ROC V_OUT max 24.5 V [TI §6.3] |
| Design ceiling, V_OUT worst case (-10 C, max bin, incl. FB/FET/diode drops) | **<= 22.0 V** (2.25 V / ~9 % under OVP min) |
| Hard lower limit, off state | string voltage at ~1 uA, hot, min bin **> 5.2 V** (= VIN max 5.5 V - ~0.3 V body diode) |
| Design lower limit, regulation | V_OUT at 0.1 % ADIM, hot, min bin **>= ~6.5 V** (VIN max + 1 V); ROC V_OUT min 5 V [TI §6.3] |
| **String Vf window at 13.9 mA, 25 C** | **~9 V to ~20 V** (typical-bin string); N = 5 (~14.75 V typ) sits mid-window |
| **Recommended LEDs per string** | **5** (same as the stock FL01C: 5 dies, 15 V typ [FL]); N = 4 or 6 acceptable, 3 marginal, 7 rejected |
| Flex protection | Recommended: 1 common-cathode dual silicon diode per string (series block + clamp), no TVS (the flex has no GND contact) |
| TPS923611 | Compatible unchanged with N = 4-6; OVP 29.6-31.4 V [TI §6.5] |

---

## 1. Main-board driver context (local, verified)

- U10 TPS923610DRLR, synchronous boost, constant current; LED_SW feeds both anodes; Q5 (warm, W-) / Q6 (cool, C-)
  return to the shared sense resistor R37 [HW §7].
- **J3 pad nets [PCB]:** 1 = `LED_SW`, 2 = `C-`, 3 = unconnected, 4 = unconnected, 5 = `LED_SW`, 6 = `W-`,
  S1/S2 (fitting nails) = `GND`. **So the FPC tail has no ground contact.** S1/S2 are soldered to the board, not
  touched by the FPC.
- Q5 gate = `COLOR_SEL`; Q6 gate = `/COLOR_SEL_INV` from U12 74LVC1G04 powered from `3V3`; R75 (100 k) holds
  `COLOR_SEL` low at boot [PCB], [HW §7]. **So whenever 3V3 is up and COLOR_SEL is low, Q6 is on and the cool
  string's return is closed, even with the light off.** One string always has a closed return path.
- R49 (C-) / R50 (W-) = 1 Mohm to GND; R39/R41 = 1 M / 120 k from LED_SW to `LED_MONIT`; D3 SMAJ26A on LED_SW;
  D8 PESD2IVN-UX on C-/W- [PCB].
- C9 = 4.7 uF / 50 V nameplate, ~1-2.5 uF effective at 15-24 V (estimate) [HW §7], [DR §8].
- L2 = 10 uH TDK VLS252012HBX-100M-1 [DR §8].
- LDO_IN comes from the TPS2116 mux (USB or battery) [HW line 134]. **A USB-C source may legally sit at 5.5 V**
  [HW line 214]. Hot-plug ringing may reach 6-7.4 V for tens of microseconds (model) [HW lines 217-220].

## 2. TPS923610 / TPS923611 datasheet extract [TI]

| Parameter | Value | Section |
|---|---|---|
| VIN recommended | 2.5-5.5 V | §6.3, §6.5 |
| VIN abs max | -0.3 to 6 V | §6.1 |
| VIN UVLO | rising 2.3 typ / 2.49 max; falling 2.05 typ / 2.17 max | §6.5 |
| SW abs max | -1 to 32 V (38 V < 10 ns transient) | §6.1 |
| VOUT abs max | -0.3 to 32 V | §6.1 |
| VOUT recommended | TPS923610: 5-24.5 V; TPS923611/2: 5-30 V | §6.3 |
| OVP rising, TPS923610 | 24.25 / 25 / 25.5 V (min/typ/max), TJ <= 85 C | §6.5 |
| OVP rising, TPS923611/2 | 29.6 / 30.5 / 31.4 V, TJ <= 85 C | §6.5 |
| OVP hysteresis | 1 V | §6.5 |
| FB reference, 100 % duty (610/611) | 195 / 200 / 206 mV over TJ -40..125 C; 198 / 200 / 203 mV at 25 C | §6.5 |
| FB at 10 % / 1 % / 0.1 % duty | 14.5-25.5 mV; 1.7-2.7 mV (25 C); 0.3 mV typ | §6.5 |
| Switch peak current limit ILIM (610/611) | 1.6 / 1.8 / 2.1 A | §6.5 |
| Start-up current limit ILIM_START | 0.8 A | §6.5, §7.3.1 |
| RDSON LS / HS (610/611) | 280 mohm (400 max) / 600 mohm (900 max) | §6.5 |
| Switching frequency | 1.1 MHz (DRLR); 0.4 MHz (LS variants) | §6.5 |
| **Max duty / min off-time** | **Not specified in SNVSCN8A. UNVERIFIED.** Off-time is "adaptive" (VIN, VOUT) for quasi-constant frequency | §7.1, §7.3.4 |
| Control | peak current mode, internal comp, FCCM over the whole load range | §7.3.4, §7.4.1 |
| ADIM thresholds | VADIM_H 1.2 V, VADIM_L 0.385 V (TJ <= 85 C); internal pull-down 600 kohm | §6.5 |
| Enable | first ADIM high pulse > **40 us** (tADIM_EN); then soft start | §6.5, §7.3.1 |
| Shutdown | ADIM low > **2.5 ms** (tADIM_SD); ISD 0.13 uA typ | §6.5, §7.3.3 |
| ADIM min PWM on-time | 20 ns; recommended carrier 10-200 kHz | §6.5, §7.3.8 |
| Thermal shutdown | 170 C rising / 150 C falling, auto-restart | §6.5, §7.3.9 |

**Open LED (§7.3.6, §7.4.2, Fig. 8-9):** when VOUT exceeds VOVP_R, switching stops until VOUT falls by the 1 V
hysteresis, then restarts. After **3** detections the part latches into OVP mode (no switching). Reset only by an
ADIM shutdown (> 2.5 ms low) and re-enable, or by VIN UVLO.

**Shorted LED:** the datasheet has **no LED-short protection** beyond the cycle-by-cycle ILIM, the FB
short-to-GND over-current behaviour shown in Fig. 8-10/8-11, and thermal shutdown. A string short (or any load
whose voltage is below VIN) is **not current-controlled** because of the path below.

**Load voltage below VIN (§7.3.3):** a boost can't produce VOUT < VIN. Even in shutdown there is a DC path
VIN -> L2 -> high-side body diode -> VOUT -> string -> Q5/Q6 -> R37. TI says the LEDs stay dark in shutdown only
because string Vf plus the body-diode drop "exceeds the maximum input voltage". If it does not, current is limited
only by R37 (15 ohm) + BSS138 R_on + L2 DCR, whether the driver is on or off. Estimates for a fully shorted string:
(VIN - 0.7 V) / 16.5-18.5 ohm = **0.19-0.21 A at 4.2 V, 0.26-0.29 A at 5.5 V**. That puts **0.5-1.3 W into R37**
(a 0.1 W 0603 [DR §8]) and over-stresses the BSS138 (~0.2 A class, **UNVERIFIED**). A fault with a closed return
(Q6 is closed by default, see §1) is therefore a real hazard, not a dim-light symptom.

**Duty and power at VIN = 3.0 V, I = 13.96 mA** (calc, η = 0.8 assumed, **UNVERIFIED** at this light load):

- At the 22 V design ceiling: P_OUT = 0.31 W, I_IN avg ≈ 0.13 A. Ideal D = 1 - 3.0/22 = 0.864 (≈ 0.89 with
  losses), so the off-time ≈ 124 ns at 1.1 MHz. Inductor ripple with 10 uH ≈ 0.24 A p-p, so peak ≈ 0.25 A,
  far under ILIM min 1.6 A and ILIM_START 0.8 A.
- Evidence TI supports this duty: the reference design (Table 8-1: VIN 2.5-5.5 V, 3 × 6-LED strings, 20 mA each)
  runs ≈ 18.5 V from 2.5 V, so D ≈ 0.865 at 1.1 W. Our worst case is the same duty at about 28 % of that power.
- The ROC corner (24.5 V from 2.5 V, D ≈ 0.90) is listed but not jointly characterized. Staying at or below 22 V
  keeps us inside TI's demonstrated duty envelope.

## 3. Stock frontlight: Good Display FL01C [FL]

- Text, p. 4: "With LED front-light. **5 dies in serial, 15V(Typ.)**".
- Drawing, p. 5 (rendered and read): two strings, "1. COLD 5PCS LEDs" and "2. WARM 5PCS LEDs", each **VF <= 15 V,
  IF <= 15 mA**; technical parameter "Operating Voltage: <= 15V".
- Pin table on the drawing: **1 LED C+, 2 LED C-, 3 NC, 4 NC, 5 LED W+, 6 LED W-**. This matches the board and the
  owner's sample [HW §7]. The conflicting FT01C drawing is discussed in [DR §8].
- Also on p. 5 (useful for mechanics): LGP 0.40 mm, AG film 0.285 mm, OCA 0.175 mm, EPD 0.93 mm, total
  1.8 ± 0.1 mm; operating 0-50 C, storage -25 to 70 C.
- So the stock load is **3.0 V per die typ at <= 15 mA**. The main board's R37, C9 and LED_MONIT were chosen for a
  ~15 V string [HW §7].

## 4. Safe forward-voltage window for one series string

Define V_OUT = V_string + V_FB (0.200 V, 0.206 V max) + V_Q (BSS138 at 14 mA, ~0.05 V, **UNVERIFIED**) + V_Ds
(optional series diode, §8).

### Upper bound

- **Hard:** V_OUT,max < **24.25 V** (TPS923610 OVP min) [TI §6.5], and ROC ≤ 24.5 V [TI §6.3]. Above this the light
  flashes three OVP cycles and latches off, typically only when cold.
- **Design ceiling: 22.0 V** worst case. Worst case means max Vf bin, -10 C, 13.96 mA, V_FB 0.206 V, plus the
  series diode if fitted. The ~2.25 V margin covers loop overshoot on ADIM steps and colour switches, the 1 V OVP
  hysteresis band, and the OVP spec applying only up to TJ 85 C.
- Temperature: InGaN white Vf rises about 1.5-3 mV/K per LED as it cools (**UNVERIFIED** generic; use the part's
  curve). 25 C to -10 C is +0.05 to +0.105 V per LED.
- Stock panel ceiling: VF ≤ 15 V per string [FL]. Anything ≤ ~17 V is the load the board was validated around.

### Lower bound

- **Off state, hard:** V_string(≈1 uA, 50-65 C, min bin) > VIN_max - V_bd(uA) ≈ **5.5 - 0.3 = 5.2 V**. VIN_max is
  5.5 V, from USB-C [HW line 214] and TI ROC [TI §6.3]. The Q6 default-on state (§1) makes this a condition that
  holds at all times the board is powered, not only when the light is on. InGaN white at 1 uA is roughly
  2.1-2.4 V per LED (**UNVERIFIED** generic), so N ≥ 3 is needed (5.2/3 = 1.73 V per LED, nA-level current).
  N = 2 (≈ 4.2 V) would glow and conduct uncontrolled on USB power.
- **Regulation, design:** V_OUT at the lowest dimming current (0.1 % ADIM ≈ 14 uA), hot, min bin ≥ **~6.5 V**
  (VIN_max + 1 V). This keeps the boost switching with real duty. Min on-time is **UNVERIFIED**, since TI gives none.
  Below this the lowest dim steps on USB power may not track ADIM. That limits dimming but is not a hazard as long
  as the off-state bound holds.
- **Single-fault tolerance:** with one shorted LED the string must still satisfy the off-state bound. That needs
  N ≥ 4, because N = 3 minus one LED leaves 2 LEDs (≈ 4.2 V), which conduct when off.

### Resulting window

At 13.9 mA and 25 C, a typical-bin string between **~9 V and ~20 V** meets every bound with margin. The table
below checks each N at the corners.

## 5. LEDs per string: table, N = 3..7

Assumptions (all per LED, **UNVERIFIED** generic for InGaN white; replace with the chosen LCSC part's bins/curves):

- Vf at 13.9 mA, 25 C: min 2.70, typ 2.95, max 3.20 V; "wide bin" max 3.50 V.
- Cold (-10 C): +1.5 / 2.25 / 3 mV/K. Hot: TJ 65 C, -3 mV/K.
- 0.1 % ADIM: -0.45 V per LED (≈ 0.15 V/decade over 3 decades).
- Overheads V_FB 0.206 V + V_Q 0.05 V. Series Si diode 0.95 V cold.

Computed with `docs/research/electrical-limits-calc.py` (run with any Python 3).

| N | String Vf 25 C min / typ / max (V) | V_OUT typ 25 C (V) | V_OUT max -10 C, no diode / with diode (V) | V_OUT max -10 C, 3.5 V bin + diode (V) | Margin to OVP min 24.25 V (worst col.) | V_OUT min at 0.1 % ADIM, 65 C, min bin (V) | Off-state V per LED at VIN 5.5 V | LED_MONIT typ (V) | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 3 | 8.10 / 8.85 / 9.60 | 9.10 | 10.17 / 11.12 | 12.02 | +12.23 | 6.39 | 1.73 | 0.98 | Marginal: deep-dim V_OUT 6.4 V vs 6.5 V target; one shorted LED leaves 2 LEDs that conduct when off |
| 4 | 10.80 / 11.80 / 12.80 | 12.05 | 13.48 / 14.43 | 15.63 | +8.62 | 8.52 | 1.30 | 1.29 | OK |
| **5** | **13.50 / 14.75 / 16.00** | **15.00** | **16.78 / 17.73** | **19.23** | **+5.02** | **10.65** | **1.04** | **1.61** | **Recommended**: equals stock FL01C class; large margins both ways |
| 6 | 16.20 / 17.70 / 19.20 | 17.95 | 20.09 / 21.04 | 22.84 | +1.41 | 12.78 | 0.87 | 1.92 | OK only if the part's max bin ≤ 3.2 V at ~14 mA (then ≤ 21.0 V with diode) |
| 7 | 18.90 / 20.65 / 22.40 | 20.90 | 23.39 / 24.34 | 26.44 | -2.19 | 14.91 | 0.74 | 2.24 | Reject for TPS923610 (can hit OVP when cold); TPS923611 only |

**Recommendation: N = 5 LEDs per string (5 warm + 5 cool = 10 LEDs).**

- It reproduces the stock load the main board was designed around (15 V typ, ≤ 15 mA [FL]).
- It keeps ≥ 5 V under OVP min at the worst corner and ≥ 10 V at deepest dim.
- It tolerates one shorted LED.
- It works unchanged on TPS923611.
- For more light, N = 6 is acceptable only with a tight-bin part (max ≤ 3.2 V at ~14 mA). N = 7 is not.

Related constraints on the LEDs:

- **Keep one series string per colour.** Do not parallel strings: R37 sets the total current, so parallel strings
  share it by Vf mismatch.
- **Rate the LED for ≥ 20 mA continuous.** It carries 13.96 mA worst case continuously [DR §8].
- **Allow for colour-switch pulses.** On a switch to the lower-Vf string, C9 discharges into it [DR §8]. Estimate:
  ΔV 1 V over ~70-90 ohm of dynamic resistance gives +11-14 mA for ~0.1-0.2 ms (**UNVERIFIED**), so a pulse rating
  (IFP) of ≥ 50 mA is preferred.
- **Use matched Vf bins for warm and cool.** This minimizes ΔV_f, which drives both the blend re-slew
  [HW §7, DR §8] and the bleeder glow below.

## 6. LED_MONIT readings

The divider ratio is 120 k / 1.12 M = **0.1071** [PCB: R39 1M, R41 120k]. The filter is C31 100 nF with
τ ≈ 107 k × 100 nF ≈ 10.7 ms [HW §7].

| Condition | LED_SW (V) | LED_MONIT (V) |
|---|---|---|
| Off, battery 3.0-4.2 V (minus 0.3-0.5 V body diode) | 2.5-3.8 | 0.27-0.41 |
| Off, USB 5.0-5.5 V | 4.5-5.2 | 0.48-0.56 |
| N = 5 on, hot / min bin, full current | 13.1 | 1.41 |
| N = 5 on, typ | 15.0 (15.75 with diode) | 1.61 (1.69) |
| N = 5 on, -10 C / max bin | 16.8 (17.7 with diode) | 1.80 (1.90) |
| N = 6 on, typ | 17.95 | 1.92 |
| Open, flipped-and-blocked, or no strip: TPS923610 OVP | 24.25-25.5 | 2.60-2.73 |
| Same for TPS923611 OVP | 29.6-31.4 | 3.17-3.36 (may exceed ADC range) |

- The ESP32-S3 ADC full scale at 12 dB attenuation is roughly 3.1 V (**UNVERIFIED**; check Espressif docs).
- Suggested firmware thresholds for an N = 5 strip: treat > ~2.2 V (≈ 20.5 V) as open, missing, or blocked. Treat
  < ~0.9 V (≈ 8.4 V) while enabled at full duty as a short or a string below spec. These thresholds depend on N,
  so re-derive them for N = 6.
- The divider itself draws VOUT / 1.12 M ≈ 13-20 uA, which R37 does not sense. That is negligible.
- **Unselected-string glow:** the deselected string sits between LED_SW and its 1 M bleeder (R49/R50), so it
  carries ≈ (N × 0.6-0.8 V excess) / 1 M ≈ **3-5 uA** (**UNVERIFIED** estimate). That may be visible as a faint
  tint in a dark room, but it is only ~0.03 % of the selected string's current. The stock panel has the same
  behaviour [HW §7, "off is microamp-leaky"].

## 7. Connector orientation, flip, pins 1/5, pins 3/4

### Can the tail be inserted flipped? Yes

FH34 is a "Both Upper and Lower Contacts" (top-and-bottom contact) back-flip connector for 0.3 mm FPC [HRS]. A
tail turned upside down still makes contact, **mirrored: flex contact k lands on J3 pin 7-k**. The receptacle has no
key, and a 0.3 mm tail fits either way.

### What a mirrored plain two-string flex does

Board pin 1 (LED_SW) meets flex W- (warm cathode), and board pin 2 (C-) meets flex W+. Board pin 5 (LED_SW) meets
flex C-, and board pin 6 (W-) meets flex C+. **Both strings are reverse-biased.** The outcome depends on the LED:

- **LEDs without an internal protection Zener:** no forward path. When enabled, the boost ramps to OVP (24.25-25.5 V)
  3 times and latches [TI §7.3.6]. The reverse voltage is shared unevenly across N LEDs: about 5 V per LED
  average for N = 5, up to 6.3 V with TPS923611. That is at or above the usual 5 V VR test rating
  (**UNVERIFIED**, part-dependent). C9 then holds it for seconds (τ = 1.12 M × 2-4.7 uF ≈ **2.2-5.3 s**).
  Possible LED damage.
- **LEDs with an internal anti-parallel ESD Zener:** the reversed string conducts at ≈ N × 0.7 V. With Q6 on by
  default (§1), current flows even with the light **off**. Estimate for N = 5: (5.5 - 0.4 - 3.5) / 17 ohm ≈
  **94 mA** on USB (0.13 W in R37, over its 0.1 W rating), ~18 mA on a 4.2 V battery, continuously. The boost
  can't regulate it, because the load is below VIN. **This is the worst case. Avoid it.**

### Is a flip-symmetric design possible?

The map is 1 C+, 2 C-, 5 W+, 6 W-, and the mirror pairs (1,6) and (2,5) each hold one + and one return. So no
passive single-polarity wiring is flip-invariant. Two symmetric schemes exist:

1. **Anti-parallel string pairs.** Between flex contacts 1-2, put a cool string 1 -> 2 plus a warm string 2 -> 1.
   Between 5-6, put a warm string 5 -> 6 plus a cool string 6 -> 5. The colour comes out correct in both
   orientations with no diodes. Costs:
   - it needs 4 strings (20 LEDs at N = 5), only half of which are used at a time;
   - each idle string sits at about -3 V per LED reverse, which is acceptable for AC-style LED pairs but part-dependent;
   - it **breaks completely** with Zener-protected LEDs, because the idle string's Zeners shunt the active string.
2. **Diode steering.** Each string gets 2 anode-steering and 2 cathode-steering diodes: anode from flex 1 or 6,
   cathode to flex 2 or 5 for cool, and correspondingly for warm. The colour comes out correct in both orientations.
   Costs: 8 diodes, and 2 diode drops (~1.5 V) added to V_OUT.

**Neither is recommended for a DIY strip.** Instead, make a flip **inert** (next section) and mark the orientation.
Put a pin-1 arrow and "CONTACTS FACE ..." text in silkscreen on the tail stiffener side, and let the fold geometry
make the correct orientation the natural one.

### Tying pins 1 and 5 on the flex

**Harmless and recommended.** Both are `LED_SW` on the board [PCB], so a single anode bus fed from both contacts
halves the contact-current density. When mirrored, the tied bus shorts board C- to W-. Both sit near GND through the
FETs or 1 M bleeders, so that is harmless too, and the strings stay blocked or reversed exactly as analysed above.

### Pins 3/4

These are unconnected on the board [PCB] and NC on the stock panel [FL]. Keep them **unconnected on the flex**:
plain isolated copper pads (for uniform contact/retention) with no trace. A future board revision might use them,
and there is nothing useful on them today (no GND or supply).

## 8. On-flex protection and ESD

### Recommended: one common-cathode dual silicon diode per string

A BAV70-class part, VR ≥ 75 V, low leakage; the part choice and rating are **UNVERIFIED**, so confirm the LCSC
datasheet. Wiring:

- Diode A (series block): flex anode bus -> A-node.
- Diode B (clamp): anode at the string cathode, cathode at the A-node, so it is anti-parallel across the LEDs.
- The shared cathode is the string's anode node.

**Normal orientation:** A conducts. The LEDs see +0.6-0.95 V extra, already included in the §5 table. B is
reverse-biased at the string voltage (≤ 22 V), and its nA leakage is sensed by R37.

**Flipped:** B conducts, clamping the LED reverse voltage to ≈ 0 V. A blocks the whole ≤ 25.5 V (31.4 V with
TPS923611, so VR ≥ 40 V is the minimum and 75-100 V is preferred). The result is **no current in any state**: the
light is dark, the boost latches OVP, and LED_MONIT reads 2.6-2.7 V, which firmware can report. This works whether
or not the LEDs have internal Zeners.

A 30 V Schottky (e.g. a BAT54C class part) is not recommended: too little margin to the TPS923611 OVP (31.4 V) and
to D3's clamp region, and higher leakage.

Place the diodes on a stiffened, non-bending area near the tail.

### No on-flex TVS/ESD part

- The flex **has no GND contact** (J3 S1/S2 are board-side only) [PCB], so a clamp to ground is impossible on the flex.
- D3 (SMAJ26A, LED_SW) and D8 (PESD2IVN-UX, C-/W-) already clamp every flex net at the connector when it is
  installed [PCB], [HW §7].
- Handle the loose strip with ESD precautions. Prefer LEDs with ≥ 2 kV HBM rating (**UNVERIFIED** per part), and keep
  all copper except the tail contacts under coverlay.

### Hot-plug

Insert or remove the strip only with the light disabled for > ~30 s, or the board unpowered. After an OVP latch
with no strip fitted, C9 can sit near 24 V for several seconds (τ 2.2-5.3 s). Plugging a 5-LED string into that
would dump C9 through it: ≈ 9 V over ~70 ohm, about 0.13 A peak for ~0.1-0.2 ms (**UNVERIFIED** estimate).

## 9. TPS923611 compatibility

- Same package, pinout and ILIM; OVP 29.6 / 30.5 / 31.4 V; ROC V_OUT 5-30 V [TI §6.3, §6.5]. The board swaps
  D3 to SMAJ33A with it [RM].
- An N = 4-6 strip designed to the 22 V ceiling works unchanged. N = 7 would work *only* on TPS923611, so don't
  design for it, because stock builds use TPS923610.
- The open or flipped excursion rises to 31.4 V: the diode rating needs VR ≥ 40 V, and LED_MONIT may saturate the ADC.
- Unprotected flipped reverse stress rises to ~6.3 V per LED at N = 5, which strengthens the case for the §8 diodes.

## 10. Open items / UNVERIFIED

- TPS923610 max duty and min on/off time: not in SNVSCN8A.
- The chosen LED's real Vf bins at ~14 mA, its temperature coefficient, the 1 uA and 14 uA Vf, VR, ESD rating, and
  whether it has an internal Zener. The table assumptions must be replaced with these.
- BSS138 R_on at Vgs 3.3 V and 14 mA, and its current rating under a short.
- ESP32-S3 ADC range at 12 dB attenuation.
- BAV70-class VR and leakage, and the LCSC code (left to the parts research).
- Colour-switch and hot-plug pulse magnitudes are estimates; bench-check them with the scope as [DR §8] already asks.
