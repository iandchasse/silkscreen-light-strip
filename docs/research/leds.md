# Side-emitting warm/cool white LEDs from LCSC

Status: DONE (research pass 1). Date: 2026-09-24. Author: LED sourcing research agent.

## Requirements (from the project brief)

- Side-view (right-angle) SMD white LED that emits parallel to the PCB.
- A warm variant (about 2700-3500 K) and a cool variant (about 5000-6500 K) in the SAME package and footprint, ideally from the same series.
- Low profile: the height above the PCB should ideally be 1.0 mm or less, and lower is better.
- Rated for at least 20 mA continuous. We run about 13.3 mA nominal and 13.9 mA worst case (TPS923610, R37 = 15 ohm).

## Recommendation

**Pair 1: XINGLIGHT XL-4008UWC (C2843774, cool) + XL-4008WWC (C5440667, warm).** This is the only pair found that meets every requirement:

- It is truly side-emitting, and both parts have the same 4.0 x 1.4 x 0.8 mm outline, so the part stands 0.8 mm above the PCB.
- The two datasheets have identical drawings and an identical recommended land pattern.
- CCT is 6000-6500 K for the cool part and 3000 K typ (bin 2900-3200 K) for the warm part.
- Both are Vf 2.7-3.3 V at 20 mA with the same Vf bin codes.
- If max is 20 mA and VR is 5 V.
- Both are in stock at LCSC and are JLCPCB Extended parts.

LCSC's own product page for C5440667 lists XL-4008UWC as its "Similar" alternative.

## Method (so this can be re-run)

1. **Catalog sweep.** I ran about 110 keyword queries against the JLCPCB/LCSC catalog mirror at `https://jlcsearch.tscircuit.com/api/search?q=<kw>&limit=100&full=true`. Keywords:
   - package and style terms: side view, side emitting, 020, 3806, 4008, 3010, 3014, 335, 1204, 0802, 0603/0805/1206 side, 2700K/3000K side
   - suffixes and maker prefixes: WWC, XL-, TJ-S, 99-218/216/616, A-SP, MHS, TZ-P2, E6X, LTW, NSSW/NSSL, KT-, HL-

   That gave 2,620 unique parts, which I filtered for "Side View Mount" plus white or a CCT.
2. **LCSC product data.** I pulled the JSON behind each LCSC product page from `https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=Cxxxx`. It gives stock, the price ladder, attributes and the datasheet URL. I cross-checked C5440667 in a browser at https://www.lcsc.com/product-detail/C5440667.html: stock 8,840, same price ladder, "Side View Mount", 3000K, and XL-4008UWC listed as the alternative.
3. **JLCPCB assembly class.** I checked each part with a POST to `https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList` (keyword = C-number). Every candidate below returned `componentLibraryType = "expand"`, which means **Extended**. None is Basic or Preferred.
4. **Datasheets.** I downloaded every datasheet from datasheet.lcsc.com (URLs in the per-part sections) and read it with PyMuPDF. I rendered the outline and land-pattern pages to PNG and read them visually.
5. **EasyEDA footprints.** I pulled the LCSC/EasyEDA footprints from `https://easyeda.com/api/products/Cxxxx/components?version=6.4.19.5` to get where the pads sit relative to the body. The datasheets do not dimension the pad-to-body offset, so every "body front edge vs pad centerline" figure below comes from EasyEDA and is marked **(EasyEDA-derived)**.

Stock and prices are LCSC figures as of 2026-09-24 (the JLC stock is in brackets).

## Comparison table (ranked best first)

| # | Pair (cool / warm) | Maker | Package (L x D x H above PCB) | CCT cool / warm | Vf (min-max @ test I) | If max | VR | Output | View | Land pattern | LCSC stock cool / warm | Price 10-20+ cool / warm | JLC class |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | XL-4008UWC C2843774 / XL-4008WWC C5440667 | XINGLIGHT | 4.0 x 1.4 x **0.8** mm | 6000-6500 K / 3000 K typ (bin WW3-6 2900-3200 K) | 2.7-3.3 V / 2.7-3.3 V @20 mA | 20 mA | 5 V | 2600-3500 mcd / 5-10 lm @20 mA | 120° | 2 pads 1.6 x 1.1, gap 2.1 (identical) | 6,850 / 8,840 (JLC 6,855 / 9,125) | $0.0724 / $0.0648 (10+) | Extended |
| 2 | XL-2810UWC C3646946 / XL-2810WWC C5440675 | XINGLIGHT | 3.5 x 1.4 x **1.2** mm | 5500-7500 K / 2800-3200 K | 2.7-3.3 V / 2.8-3.4 V @20 mA | 20 mA | 5 V | 5-13 lm / 5-13 lm @20 mA | 120° | 2 pads 1.4 x 1.0, gap 1.4 (identical) | 9,640 / 2,480 (JLC 9,644 / 2,485) | $0.0787 / $0.0786 (10+) | Extended |
| 3 | XL-3806UWC C2843778 / XL-3806WWC C5440671 | XINGLIGHT | 3.8 x 1.0 x **0.6** mm | 6000-8000 K / **1800-2000 K** (off-spec warm) | 2.8-3.4 V / 2.8-3.4 V @20 mA | 20 mA | 5 V | 2000-2600 mcd / 2000-2600 mcd @20 mA | 120° | 2 pads 1.3 x 0.85, gap 2.2 (identical) | 63,840 / 4,300 (JLC 63,850 / 4,308) | $0.0291 / $0.0280 (20+) | Extended |
| 4 | MHS110WDT-C1 C397051 / MHS110WDT-C3 C3028827 (clone: Amicc A-SP110W1D-C01-2C C5355422 / -C03-2C C5355471) | MEIHUA (Amicc) | 3.0 x 1.5 x **1.0** mm, "1204" side view | about 8000 K (CIE 0.30/0.29; off-spec cool) / 2700-3000 K | 2.7-3.2 V / 2.4-3.0 V **@5 mA** | 25 mA | 5 V | 112-228 / 90-180 mcd @5 mA | 130° | 3 pads 0.7 x 0.7 at 0.7 mm spacing (identical) | 55,340 / 11,740 (Amicc 1,950 / 1,380) | $0.0547 / $0.0566 (10+) | Extended |

### Why this ranking

1. **XL-4008 pair.** It meets every requirement (CCT, height, footprint, 20 mA rating), both datasheets are identical, the land pattern is given, the Vf bins match, and both parts are in stock.
2. **XL-2810 pair.** Both CCTs are in spec and it is a different package, so it is the fallback. It stands 1.2 mm tall, which is over the 1.0 mm target. Warm stock is only 2,480.
3. **XL-3806 pair.** This is the lowest profile (0.6 mm), and the cool part is abundant. But the "warm" XL-3806WWC is 1800-2000 K (candle/amber) according to its datasheet, not 2700-3500 K. Use it only if an amber night light is acceptable.
4. **MEIHUA/Amicc 1204 pair.** It stands 1.0 mm tall and the warm part is 2700-3000 K. The drawbacks:
   - The "cool" C1 part is generic cold white, CIE x/y typ 0.30/0.29, which is about 8000 K by McCamy's approximation (my calculation, **UNVERIFIED**). Its bins span roughly 6500 K to over 15000 K.
   - Vf is only specified at 5 mA.
   - The footprint has 3 pads.
   - MHS110WDT-C1 is only ESD 150 V HBM.

## String-voltage sanity check (for the strip designer)

- With TPS923610, OVP is 24.25 V min. With the XL-4008 (Vf max 3.3 V at 20 mA, a little lower at 13.3 mA):
  - 5 LEDs per string = 16.5 V worst case. This is close to the stock frontlight's ~15 V, so it is recommended.
  - 6 LEDs = 19.8 V, still OK.
  - 7 LEDs = 23.1 V, too close to OVP. Don't use 7.
  - XL-3806 and XL-2810WWC (3.4 V max): 5 = 17.0 V, 6 = 20.4 V.
- The minimum string length is set by the boost topology: Vout must stay above the maximum VIN (5 V USB), so use at least 3 LEDs. 5 is the natural choice.
- Power at 13.9 mA x ~3.1 V is about 43 mW per LED, under the 70 mW Pd.
- The XL-4008WWC derating curve (datasheet p.5) keeps 20 mA flat to ~27 °C, then falls linearly to 10 mA at 85 °C. That means 13.9 mA is allowed up to roughly 60 °C ambient (read from the graph).
- At 13.3 mA, relative intensity is about 0.72-0.75 of the 20 mA value (read from the graph).
- The V-I curve shows Vf of about 2.9-3.0 V at ~13 mA (read from the graph, **approximate**).

## Per-part detail

### Pair 1: XINGLIGHT XL-4008UWC (cool) / XL-4008WWC (warm), RECOMMENDED

- **LCSC pages:**
  - https://www.lcsc.com/product-detail/C2843774.html
  - https://www.lcsc.com/product-detail/C5440667.html
- **Datasheets:**
  - UWC: https://datasheet.lcsc.com/datasheet/pdf/e6aed946d22bf266730bba05a11330f0.pdf?productCode=C2843774
  - WWC: https://datasheet.lcsc.com/datasheet/pdf/98f3d1f702a22a454447380c669f5ab6.pdf?productCode=C5440667
- **Outline** (datasheet p.1 and p.7, identical for both): "L/W/H 4.0*0.8*1.4 mm".
  - The emitting face is 4.0 mm long x 0.8 mm high, with a 1.8 mm-wide emitting window.
  - Depth (along the light) is 1.4 mm: a 0.6 mm lens region at the front plus the terminal region at the back.
  - The back view shows a 2.86 mm body between the terminals.
  - The part stands **0.8 mm above the PCB**.
  - Tolerance is ±0.25 mm unless noted.
- **Emitting face:** the 4.0 x 0.8 face on the side away from the terminals.
  - In the EasyEDA footprint (EasyEDA-derived), the body spans y = -1.0 … +0.4 mm (UWC) or -0.925 … +0.475 mm (WWC) from the pad centerline.
  - So the **front (emitting) edge sits ~1.0 mm ahead of the pad centerline** on the -Y side. The rear is ~0.4 mm behind it, and the pads overhang the rear by ~0.15 mm.
  - The EasyEDA silkscreen line is on the -Y (emitting) edge.
- **Polarity:** pin 1 = cathode (−) and pin 2 = anode (+). A "mark" notch on the pin-1 terminal (bottom view) identifies pin 1.
  - EasyEDA numbers the pads mirrored between the WWC and UWC footprints. Build one KiCad footprint from the datasheet.
- **Recommended land pattern (datasheet p.7):** two rectangular pads, **1.6 mm (along the length) x 1.1 mm (along the depth)**.
  - The inner gap is **2.1 mm**, so the pad centers are at **x = ±1.85 mm** and the outer span is 5.3 mm.
  - The EasyEDA footprint matches: pads 1.6 x 1.1 at (±1.85, 0).
- **Electrical/optical** (Ta = 25 °C, datasheet p.3-4):

  | Parameter | UWC (cool) | WWC (warm) |
  |---|---|---|
  | If max | 20 mA | 20 mA |
  | IFP (0.1 ms, 1/10 duty) | 80 mA | 80 mA |
  | VR | 5 V | 5 V |
  | IR | 5 µA max @5 V | 5 µA max @5 V |
  | Pd | 70 mW | 70 mW |
  | ESD | 2000 V | 2000 V |
  | Vf @20 mA | 2.7 / - / 3.3 V | 2.7 / - / 3.3 V |
  | Vf bins | N11-8 2.7-2.9, N11-9 2.9-3.1, N12-1 3.1-3.3 | same bins |
  | CCT | 6000-6500 K (bin UW9-10) | 3000 K typ (bin WW3-6 2900-3200 K) |
  | Output @20 mA | Iv 2600-3500 mcd (G1-G3) | Φ 5-10 lm (H4-H6) |
  | CRI | Ra 70 typ | not stated (**UNVERIFIED**) |
  | Viewing angle | 120° | 120° |
  | Topr | -40 … +85 °C | -20 … +85 °C |
  | MSL | 3 | 3 |

- **LCSC** (2026-09-24):
  - UWC: stock 6,850; 10+ $0.0724, 100+ $0.0568, 300+ $0.0491.
  - WWC: stock 8,840; 10+ $0.0648, 100+ $0.0514, 300+ $0.0447; 4000/reel.
  - JLCPCB: Extended (JLC stock 6,855 / 9,125).
- **LCSC attribute quirks:** the LCSC listing gives UWC Topr as -20 … +85 °C, while the datasheet says -40 … +85 °C. The warm WWC's own datasheet says -20 … +85 °C.

### Pair 2: XINGLIGHT XL-2810UWC (cool) / XL-2810WWC (warm), fallback in a different package

- **LCSC pages:**
  - https://www.lcsc.com/product-detail/C3646946.html
  - https://www.lcsc.com/product-detail/C5440675.html
- **Datasheets:**
  - UWC: https://datasheet.lcsc.com/datasheet/pdf/11098fa7b2cfa588dfb0c3cae21d3e29.pdf?productCode=C3646946
  - WWC: https://datasheet.lcsc.com/datasheet/pdf/3c7dcddfe80cd223b7a955301a75ae2f.pdf?productCode=C5440675
- **Outline** (identical p.7): 3.5 x 1.2 x 1.4 mm.
  - The emitting face is 3.5 mm long x **1.2 mm high**, and the depth is 1.4 mm.
  - The rear view shows a 2.0 mm body and 0.5 mm terminals.
- **Emitting face:** the 3.5 x 1.2 face. In EasyEDA (EasyEDA-derived), the body spans y = -1.1 … +0.3 mm from the pad centerline, so the emitting edge is ~1.1 mm ahead on -Y.
- **Polarity:** pin 1 = cathode (−), marked by a chamfer ("mark") on the pin-1 corner of the front face. Pin 2 = anode.
- **Land pattern (datasheet):** two pads **1.4 x 1.0 mm** with a **1.4 mm gap**, so the centers are at **x = ±1.4 mm** and the outer span is 4.2 mm.
  - **Discrepancy:** the EasyEDA footprint puts its pads at x = ±1.7 mm, 0.85 x 1.3 mm. Use the datasheet.
- **Electrical/optical:**

  | Parameter | UWC (cool) | WWC (warm) |
  |---|---|---|
  | If max | 20 mA | 20 mA |
  | IFP | 80 mA | 80 mA |
  | VR | 5 V | 5 V |
  | Pd | 70 mW | 70 mW |
  | ESD | 2000 V | 2000 V |
  | Vf @20 mA | 2.7-3.3 V | 2.8-3.4 V |
  | CCT | 5500-7500 K (bins 5500-6000 / 6000-6500 / 6500-7000 / 7000-7500) | 2800-3200 K (bins 2800-3000 / 3000-3200) |
  | CIE typ | x 0.32, y 0.34 | not stated |
  | Flux @20 mA | 5-13 lm | 5-13 lm |
  | Viewing angle | 120° | 120° |
  | CRI | not stated (**UNVERIFIED**) | not stated (**UNVERIFIED**) |

  - LCSC lists UWC as 5000-7500 K; the datasheet says 5500-7500 K.
- **LCSC:**
  - UWC: 9,640 in stock, 10+ $0.0787.
  - WWC: 2,480 in stock, 10+ $0.0786.
  - Both Extended.

### Pair 3: XINGLIGHT XL-3806UWC (cool) / XL-3806WWC (very warm, 1800-2000 K)

- **LCSC pages:**
  - https://www.lcsc.com/product-detail/C2843778.html
  - https://www.lcsc.com/product-detail/C5440671.html
- **Datasheets:**
  - UWC: https://datasheet.lcsc.com/datasheet/pdf/3427bc4b59e1c7d6fee2984035162910.pdf?productCode=C2843778
  - WWC: https://datasheet.lcsc.com/datasheet/pdf/13cd288c37170c4802cdf3858dfc5ed2.pdf?productCode=C5440671
- **Outline** (identical p.7): 3.8 x 0.6 x 1.0 mm.
  - The emitting face is 3.8 mm long x **0.6 mm high**, and the depth is 1.00 mm.
  - From the bottom view: a 0.28 mm lens region, a 2.10 mm window widening to 3.45/3.70 mm, and 0.7 x 0.4 mm terminals at the rear corners.
  - The part stands **0.6 mm above the PCB**.
- **Emitting face:** the 3.8 x 0.6 face. In EasyEDA (EasyEDA-derived), the body spans y = -0.35 … +0.65 mm from the pad centerline. The emitting edge is on **+Y**, ~0.62-0.65 mm ahead.
- **Polarity:** pin 1 = cathode (−), marked by a chamfered corner ("mark") at the pin-1 end of the front face. Pin 2 = anode.
- **Land pattern (datasheet):** two pads **1.3 x 0.85 mm** with a **2.2 mm gap**, so the centers are at **x = ±1.75 mm** and the outer span is 4.8 mm. EasyEDA matches.
- **Electrical/optical:**

  | Parameter | UWC (cool) | WWC (warm) |
  |---|---|---|
  | If max | 20 mA | 20 mA |
  | IFP | 80 mA | 80 mA |
  | VR | 5 V | 5 V |
  | Pd | 70 mW | 70 mW |
  | ESD | 2000 V | 2000 V |
  | Vf @20 mA | 2.8-3.4 V (bins N13-3/4/5) | 2.8-3.4 V (bins N13-3/4/5) |
  | Iv @20 mA | 2000-2600 mcd | 2000-2600 mcd |
  | CCT | 6000-8000 K (bin UW9-21) | **1800-2000 K** (bin YW7-4) |
  | Viewing angle | 120° | 120° |

  - LCSC lists UWC as 6000-7000 K.
  - LCSC's WWC listing is wrong in places: it says "Top-mount" and illumination "Yellow", with 1800-2200 K. The datasheet outline is the same side-view package as the UWC.
- **LCSC:**
  - UWC: 63,840 in stock, 20+ $0.0291.
  - WWC: 4,300 in stock, 20+ $0.0280.
  - Both Extended.

### Pair 4: MEIHUA MHS110WDT-C1 (cool) / MHS110WDT-C3 (warm), with Amicc A-SP110W1D-C01-2C / -C03-2C as a second source

- **LCSC pages:**
  - https://www.lcsc.com/product-detail/C397051.html
  - https://www.lcsc.com/product-detail/C3028827.html
  - https://www.lcsc.com/product-detail/C5355422.html
  - https://www.lcsc.com/product-detail/C5355471.html
- **Datasheets:**
  - MHS110WDT-C1: https://datasheet.lcsc.com/datasheet/pdf/15a0145db0535e8ca09c02381c9ec893.pdf?productCode=C397051
  - MHS110WDT-C3: https://datasheet.lcsc.com/datasheet/pdf/76f3d687e4185278855419d2b56bd4e2.pdf?productCode=C3028827
  - A-SP110W1D-C01-2C: https://datasheet.lcsc.com/datasheet/pdf/e540fdd457cc74f4fa13a5d37c60328b.pdf?productCode=C5355422
  - A-SP110W1D-C03-2C: https://datasheet.lcsc.com/datasheet/pdf/006ec80922d5ed4c3212a75a3ff0822f.pdf?productCode=C5355471
- **Outline** ("1204 side view", identical in all four datasheets): the emitting face is 3.0 mm long x **1.0 mm high**.
  - The side view shows a cylindrical dome lens, R1.0 and 2.0 mm wide, on a 0.50 mm base, 1.50 mm deep in total.
  - The EasyEDA 3D model name "LED-SMD_3P-L3.0-W1.5-H1.0" confirms the part is **1.0 mm high**.
- **Emitting face:** the dome side. In EasyEDA (EasyEDA-derived), the body spans y = -1.41 … +0.10 mm, so the emitting edge is ~1.3 mm ahead of the outer-pad centers on -Y.
- **Polarity:** pin 1 = **anode (+)** and pin 2 = cathode (−), marked by a cathode triangle on the bottom view. This is the opposite pin-1 convention from XINGLIGHT.
  - The datasheet does not state what pin 3 (the center terminal) does. Treat it as a mechanical/NC pad (**UNVERIFIED**).
- **Land pattern (datasheet "Recommended Solder Pad"):** five 0.7 mm columns, so the pad edges are at x = ±0.35 / ±1.05 / ±1.75 mm.
  - Pads 1 and 2 are 0.7 x 0.7 mm at x = ±1.4 mm.
  - Pad 3 is 0.7 mm wide at x = 0, offset 0.25 mm toward the rear. Its height reads 0.65 mm on the drawing (ambiguous, **UNVERIFIED**).
  - EasyEDA uses 0.7 x 0.7 pads at (±1.4, -0.125) and (0, +0.125).
- **Electrical/optical** (only specified at 5 mA):

  | Parameter | MHS110WDT-C1 (cool) | MHS110WDT-C3 (warm) |
  |---|---|---|
  | If | 25 mA | 25 mA |
  | IFP | 95 mA | 60 mA |
  | Pd | 60 mW | 95 mW |
  | VR | 5 V | 5 V |
  | ESD | **150 V** HBM | 1000 V |
  | Vf @5 mA | 2.7-3.2 V | 2.4-3.0 V |
  | CCT | CIE typ x 0.30 / y 0.29, about 8000 K (**UNVERIFIED** conversion); bins x 0.254-0.314 | 2700-3000 K |
  | Iv @5 mA | 112-228 mcd | 90-180 mcd |
  | Viewing angle | 130° | 130° |

  - The Amicc clones have the same numbers, except that A-SP110W1D-C01 has ESD 1000 V, If 25 mA and Iv 112-225 mcd.
  - Vf at 13.3 mA is not given (**UNVERIFIED**; expect roughly +0.2-0.3 V).
- **LCSC:**
  - MHS110WDT-C1: 55,340 in stock, 10+ $0.0547.
  - MHS110WDT-C3: 11,740 in stock, 10+ $0.0566.
  - A-SP110W1D-C01: 1,950 in stock, $0.062.
  - A-SP110W1D-C03: 1,380 in stock, $0.0751.
  - All Extended.

## Rejected candidates

- **TOGIALED TJ-S1606EXET5ALCCW-A5 (C48689641) / TJ-S1606EXET5ALC3DW-A5 (C48689640).** These are 1606 side view, 1.6 x 0.6 mm SMT with 1.0 mm thickness. Pads 0.8 x 0.7 mm with a 0.9 mm gap, 2.5 mm span. If 20 mA, Vf 2.8-3.6 V @20 mA.
  - The cool part is **10000-17000 K**, far outside 5000-6500 K.
  - The warm part (2500-3000 K) has **0 stock at LCSC** and 6 at JLC.
  - Datasheets:
    - https://datasheet.lcsc.com/datasheet/pdf/c19548caa201807f5ccef20e65df1741.pdf?productCode=C48689641
    - https://datasheet.lcsc.com/datasheet/pdf/cf8aec84fdd5391a32ed00a2f245ad53.pdf?productCode=C48689640
- **Cool-only side-view parts with no warm sibling found in the LCSC/JLC catalog:**
  - TOGIALED: TJ-S3806SW1TGLCCW-A5 C601692 (8000-15000 K), TJ-S4008SW4TGLCCW-A5 C601698 (6000-8000 K), TJ-S1706CL6T5ALC8CW-A5 C1322341 (8300-17000 K), TJ-S1706SW6TGLCCW-A5, TJ-S2005, TJ-S3210 (10000-15000 K).
  - XINGLIGHT: XL-1606UWC C965866, XL-2106UWC C965873 (7500-12000 K), XL-3210UWC C965880 (8000-12000 K), XL-C3014UWC C2843795 (7000-7500 K). Searches for XL-1606/2106/3210/C3014/020 "WWC" returned nothing.
  - Everlight: the 99-218 / 99-216 / 99-616 / 3003 / 3004 / 12-215 side-view whites (e.g. 99-218GLM2C C605463). LCSC gives no CCT and I found no warm variant.
  - Others: MEIHUA MHS190WDT-C1 C409795 and Amicc A-SP192SW1D (1.6 x 0.6, 5 mA); MHS171WDT-C2 / A-SP170SW1D (0805 side); E6X0602/E6X0802; TZ-P2-0603/0802/1204 (10000-40000 K); Inolux IN-S121ASUW; YONGYUTAI YLED0602WSIDE (2 mA); ZSW1-3210-15-C3; Harvatek XN-0603UWC C48678155 (7000-25000 K, 2 mA, not tagged side view).
- **XL-3806WWC as a "warm" part:** it is 1800-2000 K. I kept it as ranked pair 3 but flagged it off-spec.
- **Top-emitting warm whites** (XL-1608WWC-06, XL-2012WWC, XL-3216WWC, XL-3014WWC-02, XL-3528WWC, TJ-S1608CY6T5ALC3DW-A5): they are not side-emitting. Using them would mean standing the flex on edge.
- **Dual-CCT TOGIALED TJ-S3527UG2W4TLCDWTW-A5 (C440512; 2700-3300 K plus 5500-7000 K in one 3528-4P):** it is top-emitting and much taller.
- **XINGLIGHT XL-5050WYWWC-2812B:** addressable 5050, not relevant.
- **Nichia NSSW/NSSL, Kingbright, NationStar, KENTO, Refond, MLED side-view whites:** none turned up in the LCSC/JLC catalog search (no hits for NSSW, NSSL, KT-3806/4008, HL-3806/4008). Their absence from LCSC is **UNVERIFIED** beyond these keyword searches.
- **Lite-On LTST-S310F3WT (C284951):** it appeared in a web search result. I did not check whether it is white or has a warm variant (**UNVERIFIED**).

## Sources

- The LCSC product pages and datasheet URLs are listed in each part section above. LCSC product JSON: `https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=<C#>`.
- JLCPCB parts API (assembly class): `https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList`.
- Catalog search mirror: https://jlcsearch.tscircuit.com/api/search
- EasyEDA footprints: `https://easyeda.com/api/products/<C#>/components?version=6.4.19.5`
- The local scratch copies of the datasheets, renders and JSON were in `a scratch folder` (not part of the repo).
