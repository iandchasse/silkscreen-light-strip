# Assembly and fitting

This guide takes a bare rev A flex through to a working light in a Silkscreen reader. It assumes:

- a plain **GDEY0426T82** panel, with no bonded frontlight;
- the P03 enclosure;
- a main board with the frontlight driver populated (U10 and friends).

The reasons behind each step are in [DESIGN.md](DESIGN.md).

> **The P03 enclosure does not take this strip unmodified.** The strip's fold around the bottom glass edge needs about 0.8–2 mm of room. P03 leaves 0.535 mm there, before its bottom button bridge and rocker 1's forward pad. You can wire and test the strip on a bare board and panel today. Closing it inside P03 needs the case change in [§8](#8-enclosure-p03).

**You need:**

- **Soldering:** a fine-tip iron, or hot air with paste. Flux, tweezers and isopropyl alcohol.
- **Testing:** a CR2032 coin cell, a multimeter, and a bench supply that can current-limit at 5–10 mA and reach 18 V.
- **Fitting:** Kapton tape, and 0.8 mm black foam tape for the visor.
- **Parts:** 5 × XL-4008WWC (warm), 5 × XL-4008UWC (cool), 2 × BAV70W,115. Buy a few spares. The LEDs are 4 mm long and easy to lose.

Handle the loose strip as ESD-sensitive. It has no ground and no on-board clamp.

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

- **Warm/cool placement.** In every pair, the **warm XL-4008WWC goes in the lower spot**: D1–D5, nearer the foot. The **cool XL-4008UWC goes in the upper spot**: D6–D10. The two parts look identical, so keep the reels apart.
- **LED orientation.** The window faces the bar's inner edge, toward the screen. The **cathode** is the lower pad of each footprint, marked by a short white bar on the outer edge beside it. The anode is the upper pad.
- **LED position.** Seat each LED flat and square. Its window should sit just behind the flex's inner edge, not overhanging it: the design puts the face 0.1 mm behind the edge.
- **Diodes.** D11 and D12 (BAV70W) sit side by side on the tail. On each, the single pin (pin 3) points back toward the LEDs.
- **Solder.**
  - Keep each hand joint short: 2–3 s at the lowest temperature that wets.
  - The bar and the tail end are stiffened, so the joints don't flex.
  - Use very little solder. The LED sits only 0.8 mm tall, and a big fillet can wick up to the window.
- **Clean** off the flux with isopropyl alcohol.

## 3. Bench test on the pads

Test before the strip goes anywhere near the panel. Three pads on the tail each have a letter **directly below** them:

- **S** = LED_SW, the anode supply. It is the lower-left pad, with a via in its centre.
- **C** = C−, the cool return.
- **W** = W−, the warm return.

1. **Coin-cell every LED first.** A CR2032 across any single LED's two pads, "+" on the upper pad, lights just that LED. One that won't light is reversed, badly soldered or open. Fix it now: the supply test below can over-stress a reversed LED.
2. **Check for shorts.** With a meter on the diode range, **S–C and S–W must read open (OL) in both directions.** A reading means a solder bridge, usually at D11/D12 or a test pad. Don't fit a strip that fails this. On the reader, that short puts the battery or USB across the main board's 15 Ω R37 with no regulation, about 0.3 A, even with the light off.
3. **Set the supply.** Set a **5–10 mA current limit** and 0 V.
4. **Test the cool string.** Connect **+ to S** and **− to C**, and raise the voltage slowly. The five cool LEDs should light together at about 13–16 V, depending on bin and temperature.
5. **Test the warm string.** Move **− to W**. The five warm LEDs should light.
6. **Stop at 18 V.**
   - If nothing lights by 18 V, a string is open or has an LED in backwards. Go back to step 1. A single backwards LED already sees more than its 5 V reverse rating from about 14 V up, so don't dwell there.
   - If the supply sits in current limit with the voltage stuck near 0 V, S is shorted to C or W. See step 2.

## 4. Prepare the panel

1. Peel the panel's thin shipping film and pull tape.
2. Clean the left and bottom borders with isopropyl alcohol. Keep it off the active area.
3. Leave the panel's own protective sheet on. The strip is designed to sit on it.
4. Look at the bare-glass ledge along the bottom edge. The strip's neck crosses it 9.4–15 mm in from the left glass edge. Check for a raised COG chip or silicone bead there. The fold path has room for up to about 1 mm, but it's worth knowing before you fold.

## 5. Lay the bar and foot

1. Peel the liner off the 3M 9077 tape on the back of the bar and foot.
2. Align the strip to the panel:
   - **Bar:** its straight outer edge sits flush with the panel's **left** glass edge. The drawing puts it 0.05 mm outside, which is within the outline tolerance.
   - **Top end:** the rounded top sits about 1.3 mm below the top glass edge.
   - **Foot:** it lies along the bottom border on the flat protective sheet.
   - **Fold ticks:** the first pair of white ticks on the neck edges sits **0.8 mm above the bottom glass edge**.
3. Tack it at one end, check the alignment along the whole length, then press the rest down with a soft tool. **Press on the flex between the LEDs, not on the LEDs.**
4. **Check** that every window faces the screen and sits just outside the image area (about 1.2 mm outside it). Nothing should visibly overhang a glass edge.

## 6. Fold the tail

The tail wraps 180° around the **bottom glass edge**, runs back under the panel, and goes through the main board's FPC slot next to the panel's own FPC. It then turns onto the back of the board and runs to J3. This is the same route the stock frontlight tail takes.

1. **Protect the path first.** Put Kapton on both edges of the main board's FPC slot. Also cover the **SW9 pad-4 leg** on the front of the board, near the bottom-left corner of the slot. The neck passes over that cut lead.
2. **Tack the neck.** A small dot of Kapton holds the neck to the ledge 1–2 mm before the glass edge. Put it on bare glass, clear of any chip or silicone.
3. **Wrap the U.** Wrap it snugly, with an inside radius of about 0.7–1.0 mm; a 1.5–2 mm drill shank is a good former. **Never crease it**: the glass edge is bare and sharp. The neck has no vias or pads in the bend zone, and copper only on the outside of the U, so a smooth wrap is safe.
   - Keep the wrap square to the glass edge.
   - The neck's right edge is only 0.2–0.8 mm from the panel's own FPC. The U must not ride onto, press on or pull that FPC's bond or bend area.
4. **Thread the tail.** Feed it through the slot and turn it onto the back of the board. From the second pair of white ticks onward, the tail is stiffened, and it should lie flat on the board's back all the way to J3.
5. **Know where the slack goes.** The tail is cut about 2 mm long on purpose, so it is never short. With the tip fully in J3, the spare makes the U stand about 1 mm further past the glass edge.
   - **Keep the U's radius tight.** Let the legs lengthen instead of letting the loop balloon toward the SW9 lead.
   - **The enclosure has to make room.** With the spare, the U's outer surface ends up about 2 mm past the glass edge, and even a tight U needs about 0.8 mm. See [§8](#8-enclosure-p03).

## 7. Plug into J3

J3 is on the back of the main board. It is a back-flip ZIF: the lever is on the side away from the opening.

1. Flip the lever open.
2. Insert the contact tab. **Its gold contacts face away from the board**, which also means the diodes and the S/C/W labels face you.
3. Push the tab in **fully**, about 2.9 mm. The full 3.5 mm width runs only about 3.8 mm from the tip before the tail starts to widen, so about 1 mm of it stays visible outside the mouth.
4. The white **triangle** marks contact 1. The fold keeps the pin order, so if the strip is folded as above, it lands on J3 pin 1 by itself.
5. Close the lever.
6. Tape the stiffened back run flat to the board with Kapton. J3 holds with only about 3 N, so the tape, not the connector, should take any pull.
   - The right edge of the back run lies over the main board's **TP5** (W−, about 10 mm below J3).
   - TP5 must stay unpopulated and flush, with no pin, wire or solder blob, or the run won't lie flat.

A tail inserted upside down is harmless: the strip stays dark and the driver latches off. Turn it over and re-seat it.

## 8. Enclosure (P03)

- **Required: room for the U.** P03 leaves the panel tails 0.535 mm past the bottom glass edge. Behind that line sit two parts:
  - the bottom bearing bridge's crossbar (enclosure X 5.5–54.5, Y 4.30–4.75, Z 2.8–4.4);
  - rocker 1's forward pad (X 9.2–13.8, Y 3.15–4.75, Z 4.4–4.9), which the bottom return foam presses.

  The strip's U needs about 0.8 mm at its tightest and about 2 mm with the spare tail. Over enclosure X 8.0–14.1, the crossbar and rocker 1's forward pad and axle boss must be cut back to about Y 2.75. After that, re-check rocker 1's return and stop, because both use that pad and the bridge. This is a change to the case design (`silkscreen-case`), not something to carve by hand. Until it's made, the strip can only be tested outside the case.
- **Panel-stack parameters.** Keep P03's 1.98 mm settings. The plain panel is 0.926 mm thick, and the spare height is what the LEDs use: LED tops are at Z ≈ 6.11 under a bezel ceiling of Z 6.5.
- **Left border visor.**
  - Remove the P03 upper gasket pad from the left border.
  - Stick a strip of **0.8 mm black foam** along the top of the LED row, from just above the top LED to just below the bottom one.
  - It may overhang the window edge by up to about 0.4 mm, but no further, or it shades the light.
  - It compresses to about 0.4 mm, hides the LEDs from glancing views, and holds the bar down.
- **Other borders.** The thin panel is loose in P03. Use 1.8–2.0 mm silicone foam on the top, right and bottom borders, or shim the existing pads by about 1 mm.
- **Look straight on** with the bezel fitted. No flex or LED should be visible. At steep side angles, a dark sliver of the black coverlay may show.
- **Antenna.** The bar passes 5–8 mm from the ESP32-S3 antenna. Compare the Wi-Fi RSSI with and without the strip on the first build.

## 9. Firmware bring-up

The strip is electrically a stock frontlight ([silkscreen-pcb HARDWARE.md §7](https://github.com/iandchasse/silkscreen-pcb/blob/master/docs/HARDWARE.md#7-frontlight-driver)).

1. **Choose a colour.** With the light off, set `COLOR_SEL` (IO40): LOW selects cool, HIGH selects warm. R75 holds it LOW at boot.
2. **Enable.** Drive `PWM_LED` (IO42, ADIM) **HIGH for at least 100 µs**. A bare PWM carrier may never enable the driver.
3. **Dim.** Start PWM at 10–200 kHz from a low duty and ramp up. Dimming is analog inside the driver, so it doesn't flicker.
4. **Check `LED_MONIT`** (IO2, ADC1_CH1) about 50–200 ms after enabling. Take a few reads and use the highest:

   | Reading | Meaning |
   |---|---|
   | 0.27–0.56 V | Off (tracks the battery or USB) |
   | **1.4–2.0 V** | **Lit** at full duty |
   | above ~2.2 V (about 2.5–2.7 V) | Strip open, flipped or unplugged. The driver trips its over-voltage limit and latches off after 3 trips, within about 0.1–0.8 s. It then stops switching, and `LED_MONIT` sinks back to the off band over several seconds. **Record the fault when you first see it**, because a later read looks like "off". |

5. **Recover from a latch.** Hold `PWM_LED` **LOW for at least 3 ms**, fix the cause, then enable again. PWM alone won't restart it.
6. **Change colour** only with the duty at 0: ramp down, switch `COLOR_SEL`, ramp back up.
   - Keep the time at duty 0 under about 1 ms. `ADIM` LOW for more than 2.5 ms shuts the driver down, and a low-duty carrier won't re-enable it.
   - If the pause may be longer, send the ≥ 100 µs HIGH enable pulse again before ramping up.
   - Mixing warm and cool by switching fast is possible, but not yet validated on the bench.

A faint glow from the unselected string in a dark room is normal: about 1–3 µA leak through the main board's 1 MΩ bleeder. The stock panel does the same.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Nothing lights; `LED_MONIT` 2.5–2.7 V when read within ~0.2 s of enabling, then falling to the off band | Tail flipped or not fully seated, or an LED reversed or open. Bench-test on S/C/W. |
| Nothing lights; `LED_MONIT` in the off band (0.27–0.56 V) with PWM running | The driver never enabled (check the ≥ 100 µs HIGH pulse), or it latched open earlier and C9 has drained since. Hold `PWM_LED` LOW for ≥ 3 ms, re-enable, and read again within 0.2 s. |
| `LED_MONIT` about 0.45 V at boot and the board warm near R37 | S shorted to C or W on the strip. Unplug it and do the step 2 meter check in §3. |
| One colour works, the other doesn't | Open joint or reversed LED in that string, or a BAV70W joint. Coin-cell each LED. |
| Light flickers when the reader is tapped | J3 not latched, or the tail pulling on J3. Re-seat it and tape the back run. |
| `LED_MONIT` below about 1.2 V in the first second at full duty, with the LEDs lit | Shorted LEDs or a solder bridge across part of a string. One shorted LED alone may still read about 1.2–1.6 V. Power off: a string shorted out entirely draws current with no regulation. |
| Bright band right at the left edge, dim right side | Expected with grazing light. See [DESIGN.md §6](DESIGN.md#6-optics). |
