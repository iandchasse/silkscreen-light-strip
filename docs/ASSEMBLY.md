# Assembly and fitting

This guide takes a bare rev A flex through to a working light in a Silkscreen reader: either the **4.26″** reader with a plain `GDEY0426T82` panel, or the **3.68″** x3 reader. Each needs its light-strip case from the [silkscreen-enclosures](https://github.com/iandchasse/silkscreen-enclosures) repo (the `print/` and `enclosures/` paths below are in that repo). You also need a main board with the frontlight driver populated (U10 and friends; the trimmed x3 board keeps all of it).

**The light-strip cases are in development and not released:** the website offers only the standard cases, and no case has been printed around a strip yet.

The reasons behind each step are in [DESIGN.md](DESIGN.md). The showcase source in silkscreen-enclosures (`showcase/`) builds a page that folds the strip into either reader step by step and shows every piece of tape.

**You need:**

- **Soldering:** a fine-tip iron, or hot air with paste. Flux, tweezers and isopropyl alcohol.
- **Testing:** a CR2032 coin cell, a multimeter, and a bench supply that can current-limit at 5–10 mA and reach 22 V.
- **Fitting:** Kapton tape, a craft knife, flush cutters.
- **Parts:** 6 × XL-4008WWC (warm), 6 × XL-4008UWC (cool), 2 × BAV70W,115. Buy a few spares. The LEDs are 4 mm long and easy to lose.

Handle the loose strip as ESD-sensitive. It has no ground and no on-board clamp, and the trimmed x3 board has none on these nets either.

---

## 1. Check LED polarity before anything else

A side-view LED can't be rotated to fix a polarity mistake, because rotating it also points the light the other way. The footprint's polarity was worked out from the datasheet, JLC's tape note and LCSC's library parts, but it has not been measured ([DESIGN.md §3.2](DESIGN.md#32-polarity-corrected-once-still-worth-a-diode-test)). Thirty seconds with a coin cell settles it:

1. **Find the window.** It is the clear, yellow-phosphor strip on one long 4.0 × 0.8 mm face.
2. **Hold the LED as it will sit on the strip.** Put it window-side facing right, as if it were lying on the bar with its light going across the screen.
3. **Touch the CR2032's "+" side to the upper terminal and the "−" side to the lower terminal.** "Upper" means the end that points toward the rounded top of the strip.
4. **It should light.** Reverse the cell and it should stay dark.

If it lights only the other way round, **stop and don't solder.** The footprint and routing would then need mirroring. Please open an issue with a photo.

## 2. Solder the parts

Tape the flex flat, LED side (white silkscreen) up.

- **Warm/cool placement.** In every pair, the **warm XL-4008WWC goes in the lower spot**: D1–D6, nearer the foot. The **cool XL-4008UWC goes in the upper spot**: D7–D12. The two parts look identical, so keep the reels apart.
- **LED orientation.** The window faces the bar's inner edge, toward the screen. The **cathode** is the lower pad of each footprint, marked by a short white bar on the outer edge beside it. The anode is the upper pad.
- **LED position.** Seat each LED flat and square, its window just behind the flex's inner edge, not overhanging it.
- **Diodes.** D13 and D14 (BAV70W) sit side by side on the tail. On each, the single pin (pin 3) points back toward the LEDs.
- **Solder.**
  - Keep each hand joint short: 2–3 s at the lowest temperature that wets.
  - Use very little solder. The LED sits only 0.8 mm tall, and a big fillet can wick up to the window.
  - Nothing is soldered on the **hinge**, the bare 3.6 mm gap between the top pair and the next (white ticks mark its ends). Keep it clean and don't let flux or solder stiffen it.
- **Clean** off the flux with isopropyl alcohol.

## 3. Bench test on the pads

Test before the strip goes anywhere near a panel. Three pads on the tail each have a letter **directly below** them:

- **S** = LED_SW, the anode supply. It is the lower-left pad, with a via in its centre.
- **C** = C−, the cool return.
- **W** = W−, the warm return.

1. **Coin-cell every LED first.** A CR2032 across any single LED's two pads, "+" on the upper pad, lights just that LED. One that won't light is reversed, badly soldered or open. Fix it now: the supply test below can over-stress a reversed LED.
2. **Check for shorts.** With a meter on the diode range, **S–C and S–W must read open (OL) in both directions.** A reading means a solder bridge, usually at D13/D14 or a test pad. Don't fit a strip that fails this: on the reader, that short puts the battery or USB across the main board's 15 Ω R37 with no regulation, about 0.3 A, even with the light off.
3. **Set the supply** to a **5–10 mA current limit** and 0 V.
4. **Cool string.** Connect **+ to S** and **− to C**, and raise the voltage slowly. The six cool LEDs should light together at about 16–20 V, depending on bin and temperature.
5. **Warm string.** Move **− to W**. The six warm LEDs should light.
6. **Stop at 21 V.**
   - If nothing lights by 21 V, a string is open or has an LED in backwards. Go back to step 1. A single backwards LED already sees more than its 5 V reverse rating from about 16.5 V up, so don't dwell there.
   - If the supply sits in current limit with the voltage stuck near 0 V, S is shorted to C or W. See step 2.
   - If a string needs **more than about 20.5 V** at room temperature to reach 10 mA, note it: that batch's LEDs are on the high side, and a cold reader could pass the 22 V design ceiling (still under the driver's 24.25 V shutoff; [DESIGN.md §2.1](DESIGN.md#21-six-leds-per-string)).

## 4. Which reader, which case

| | 4.26″ | 3.68″ |
|---|---|---|
| Panel | Plain **GDEY0426T82** (no touch, no frontlight). The FT01C does not fit the light-strip case. | The x3's 3.68″ 528 × 792 panel |
| Case (in development) | Plate 2 of `print/silkscreen-426-plates.3mf` (or `print/4.26/`: the shared parts plus **`tub-light-strip`**) | Plate 2 of `print/silkscreen-368-plates.3mf` (or `print/3.68/`: the shared parts plus **`tub-light-strip`** and four **`key-x3ls`**) |
| Where the strip goes | **On** the panel's left border | **Beside** the panel, in a channel in the tub; the top pair folds back under the bar |
| Order | Strip onto the panel, then the whole stack into the tub | Strip into the tub first, then the panel |
| Read | [§5](#5-426-strip-on-the-panel) | [§6](#6-368-fold-back-and-fit-beside-the-panel) |

Both case READMEs have a "Light-strip variant" section with the measured numbers behind these steps.

## 5. 4.26″: strip on the panel

1. **Trim SW9's left mounting-lug lead.** It stands on the board's front just left of the slot, next to where the strip's neck passes (KiCad about x 52.2, y 143.9). As it comes, its tip is 0.71 mm proud of the board and 0.10 mm from the neck. Cut it flush (at most 0.1 mm proud) and cover it with Kapton.
2. **Kapton on the slot edges.** Put Kapton on both edges of the board's FPC slot where the neck passes (the left end of the slot).
3. **Prepare the panel.** Peel its thin shipping film (0.065 mm) at least where the case's stops and the strip land, and its pull tape. Clean the left and bottom borders with isopropyl alcohol, not the active area. Leave the panel's own protective sheet on.
4. **Lay the strip.**
   1. **Measure it first.** With a micrometer, measure the bar (flex + stiffener + tape) at 2–3 points between LED pairs, with the liner on, and subtract the liner. It should be **0.37–0.40 mm**: the case's hold-down pads sit only 0.015 mm over a nominal strip, and JLC holds the stiffener to ±0.1. If it is thinner, stick 0.05 mm Kapton on each hold-down pad face in the tub (two layers below 0.32). If it is more than 0.03 mm thicker, scrape the pad faces back.
   2. Peel the liners off the two taped pieces: the short top-pair piece and the long bar + foot.
   3. Lay the bar with its straight outer edge **0.1 mm inside the panel's left glass edge** (0 to 0.2 mm). It must never overhang the glass, or it scrapes the case wall when the stack goes in. Much further in, the neck moves onto the panel's own FPC.
   4. The rounded top sits about 1.3 mm below the top glass edge. The foot lies along the bottom border on the flat protective sheet.
   5. The hinge between the top two pairs lies flat and untaped on this reader.
   6. Tack one end, check the alignment along the whole length, then press the rest down with a soft tool. **Press on the flex between the LEDs, not on the LEDs.**
   7. Check that every window faces the screen and sits just outside the image area (about 1.2 mm outside it).
5. **Wrap the U.** Wrap the neck 180° around the bottom glass edge, inside radius about 0.7–0.9 mm (a 1.5–1.8 mm drill shank is a good former). **Never crease it**: the glass edge is bare and sharp.
   - Keep the wrap square to the glass edge. The neck's right edge is only 0.2–0.8 mm from the panel's own FPC; the U must not ride onto, press on or pull that FPC's bond or bend area.
   - The spare 0.5–2.2 mm of tail stays in the U; don't let the loop balloon toward the board.
6. **Board.** Take the tail through the board's slot and into J3 ([§7](#7-plug-into-j3)).
7. **Into the case.** Stack the panel and strip, then the midplate, then the board, as in the case README (section 6). **Push the stack into the tub with the glass kept toward the right-hand wall** (held there, not pressed hard), so the bar stays clear of the left wall on the way in. The case's hold-down pads land between the LED pairs, off their solder joints.

## 6. 3.68″: fold back and fit beside the panel

On this reader the strip goes into the tub **before** the panel.

1. **Fold the top pair back.**
   1. The long bar + foot piece has one liner. With a craft knife, lightly score that liner (not the tape) across the bar about 16 mm below the hinge, and again where the bar meets the foot.
   2. Peel the top-pair piece's liner and the bar's liner above the first score.
   3. Fold the top pair **180° backward** at the hinge, under the bar, tape to tape. The bare hinge forms an open loop at the bar's end. **Do not crease it**, and keep the folded piece's edges in line with the bar's. Its LEDs now face the back.
2. **Leave the rest of the bar's liner on.** It can't be pressed onto the seat inside the tub. The bar is held anyway: it is trapped between the seat and the skin, the ribs place it sideways, and the foot places it along its length.
3. **Put the strip in the tub.** Tub face down:
   1. Lay the bar in about 0.5 mm right of its place, LEDs down toward the skin. It drops past the seat's edge.
   2. Slide it left, under the seat, **against the six small ribs** on the channel's side wall. The foot comes with it into its pocket.
   3. The folded pair and its loop drop straight into the fold zone, which is open from the back.
   4. Let the neck and tail hang out past the pocket's bottom edge.
4. **Peel the foot's liner.** Then fit the panel as in the x3 README: glass to the lip, its own FPC at the bottom, its left edge against the two corner stops. The midplate springs press the panel's film onto the foot's tape.
5. **Midplate, then the board.**
   - Kapton on the slot's edges where the neck passes, and on SW9's pin just below the slot.
   - Fold the neck over the glass edge and through the board's slot, 6.5 mm left of the panel's FPC.
   - Plug the tail into J3 ([§7](#7-plug-into-j3)).
   - This reader leaves **4–5.6 mm of spare tail**. Leave it as a loop between the slot and the stiffened end on the board's back (it stands about 2–3 mm off the board; the lid clears it). Part of it can sit in the chin instead, where the case's neck gap takes a small loop.

## 7. Plug into J3

J3 is on the back of the main board. It is a back-flip ZIF: the lever is on the side away from the opening.

1. Flip the lever open.
2. Insert the contact tab. **Its gold contacts face away from the board**, which also means the diodes and the S/C/W labels face you.
3. Push the tab in **fully**, about 2.9 mm. The full 3.5 mm width runs only about 3.8 mm from the tip before the tail starts to widen, so about 1 mm of it stays visible outside the mouth.
4. The white **triangle** marks contact 1. The fold keeps the pin order, so it lands on J3 pin 1 by itself.
5. Close the lever.
6. **Strap the stiffened end** to the board's back with Kapton, between the test pads and the J3 mouth. J3 holds with only about 3 N, so the tape should take any pull.
   - The strap goes over the **stiffened** part only; the loop of spare tail (3.68″) stays free.
   - The back run passes over the main board's TP5 (W−). Leave TP5 unpopulated and flush.

A tail inserted upside down is harmless: the strip stays dark and the driver latches off. Turn it over and re-seat it.

## 8. The case

The light-strip cases are in development and not released; this section records what they need.

- **4.26″ (`enclosures/case-426`):**
  - Print the light-strip tub in a **dark or opaque** filament. Over the LEDs the skin is 0.6 mm, and a light colour may glow. Or line the raised ceiling with black tape before fitting.
  - The springs push the plain panel a little less than the FT01C: 6.5 N in all at nominal, against 8.2 N.
  - The left window edge has a 0.2 mm bevel instead of 0.6, so it looks slightly different from the other three.
- **3.68″ (`enclosures/case-368`):**
  - Print plate 2 of `print/silkscreen-368-plates.3mf`, or from `print/3.68/` the shared parts with `tub-light-strip` and four `key-x3ls`. The shell is 13.7 mm deep (the standard build: 12.9). Since 2026-10-12 the lid has 1.0 mm more air behind the board so that it closes over a Rev 1.0 board's charging wires, and since 2026-10-19 another 0.2 for a 6.02 mm cell with its tape (13.5 and 12.7 before; 12.5 and 11.7 before 2026-10-12; 11.3 before the standard build's screen bevel).
  - The bottom keys (`key-x3ls`) stand 1.5 mm proud of the raised face, 0.8 mm taller than the standard build's (`key-x3std`); the cranks, rod and gate are the same in both builds.
  - On the first print, check that the seat's underside is flat and that the light looks even past the hold-down pads.
- **Both:** look straight on with the case closed. No flex or LED should be visible. At steep side angles a dark sliver of the black coverlay may show.
- **Antenna.** The bar passes 5–8 mm from the ESP32-S3 antenna. Compare the Wi-Fi RSSI with and without the strip on the first build.

## 9. Firmware bring-up

The strip is electrically a stock frontlight ([silkscreen-pcb HARDWARE.md §7](https://github.com/iandchasse/silkscreen-pcb/blob/master/docs/HARDWARE.md#7-frontlight-driver)).

1. **Choose a colour.** With the light off, set `COLOR_SEL` (IO40): LOW selects cool, HIGH selects warm. R75 holds it LOW at boot.
2. **Enable.** Drive `PWM_LED` (IO42, ADIM) **HIGH for at least 100 µs**. A bare PWM carrier may never enable the driver.
3. **Dim.** Start PWM at 10–200 kHz from a low duty and ramp up. Dimming is analog inside the driver, so it doesn't flicker.
4. **Check `LED_MONIT`** (IO2, ADC1_CH1) over the first second after enabling, keeping the peak:

   | Reading | Meaning |
   |---|---|
   | 0.27–0.56 V | Off (tracks the battery or USB) |
   | **1.4–2.4 V** | **Lit** at full duty |
   | peak **≥ 2.49 V** (about 2.5–2.7 V) | Strip open, flipped or unplugged. The driver trips its over-voltage limit and latches off after 3 trips, then stops switching, and `LED_MONIT` sinks back to the off band over several seconds. **Record the fault when you first see it.** |
   | below 1.30 V at full duty, 50 ms or more after enabling | Shorted LEDs or a solder bridge |

   The first layout's 2.2 V "open" threshold is too low for six LEDs: a cold strip can read 2.32 V.
5. **Recover from a latch.** Hold `PWM_LED` **LOW for at least 3 ms**, fix the cause, then enable again. PWM alone won't restart it.
6. **Change colour** only with the duty at 0: ramp down, switch `COLOR_SEL`, ramp back up.
   - Keep the time at duty 0 under about 1 ms. `ADIM` LOW for more than 2.5 ms shuts the driver down, and a low-duty carrier won't re-enable it.
   - If the pause may be longer, send the ≥ 100 µs HIGH enable pulse again before ramping up.

A faint glow from the unselected string in a dark room is normal: a few µA leak through the main board's 1 MΩ bleeder. The stock panel does the same.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Nothing lights; `LED_MONIT` 2.5–2.7 V within the first second, then falling to the off band | Tail flipped or not fully seated, or an LED reversed or open. Bench-test on S/C/W. |
| Nothing lights; `LED_MONIT` in the off band with PWM running | The driver never enabled (check the ≥ 100 µs HIGH pulse), or it latched open earlier and C9 has drained since. Hold `PWM_LED` LOW for ≥ 3 ms, re-enable, and read again. |
| `LED_MONIT` about 0.45 V at boot and the board warm near R37 | S shorted to C or W on the strip. Unplug it and do the meter check in §3. |
| One colour works, the other doesn't | Open joint or reversed LED in that string, or a BAV70W joint. Coin-cell each LED. |
| Only the 3.68″'s top pair seems dark | Normal: it is folded under the bar and faces the back. |
| Light flickers when the reader is tapped | J3 not latched, or the tail pulling on J3. Re-seat it and strap the back run. |
| `LED_MONIT` below 1.30 V at full duty, with the LEDs lit | Shorted LEDs or a solder bridge across part of a string. Power off: a string shorted out entirely draws current with no regulation. |
| Bright band right at the left edge, dim right side | Expected with grazing light. See [DESIGN.md §6](DESIGN.md#6-optics). |
