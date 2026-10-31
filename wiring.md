# Cosmos wiring map

New controller pin map: **same holes on both halves**. Matches `boards/shields/cosmos/` (col2row). Old-pin-map firmware must be replaced before using this wiring.

Four rows stay four rows. Firmware keeps six column slots per half: five letter columns, plus **C5 for Enter on the left only**. Right C5 has no wire. Only the controller ends change; keep the diode chains and physical key groups unchanged.

- Switches: metal pins toward the top, all the same way.
- Diode: no-band leg on the switch pin, **band leg → row wire**.
- Other switch pin → column wire.
- **Blue = rows, yellow = columns.**

## Controller holes (silk label)

| Wire | Hole | Wire | Hole |
|---|---|---|---|
| R0 | `031` | C0 | `017` |
| R1 | `029` | C1 | `020` |
| R2 | `002` | C2 | `022` |
| R3 | `115` | C3 | `024` |
| | | C4 | `100` |
| | | C5 (left Enter only) | `106` |

Rows use the `031` edge. The five main columns are consecutive on the `017` edge: **`017`, `020`, `022`, `024`, `100`**. Left Enter alone uses `106`, skipping `011` and `104` (right trackball). Read the printed pin labels rather than assuming all six column holes are consecutive. No right-hand column wire goes to `106`.

## Trackball sensor → R controller (right half only, 6 wires)

| Sensor pin | Controller hole |
|---|---|
| SCLK | `008` |
| SDIO | `011` |
| NCS | `104` |
| MOTION | `006` |
| VDD | `VCC` |
| GND | `GND` |

**Leave VDDIO and NRESET unconnected; do not bridge VDD and VDDIO.** This follows the exact-module [sensor guide](sensor-wiring.html), correcting the older generic bridge caption. Trackball NCS moves from `100` to `104`; SCLK, SDIO and MOTION stay unchanged. Still free on the right: `113`, `111`, `009`, `010`. Pin `106` is scanned as C5 even though the right has no key there; do not reuse it for another function without changing the firmware.

## Left half (C0 = outer pinky column)

|    | C0  | C1  | C2  | C3    | C4    | C5    |
|----|-----|-----|-----|-------|-------|-------|
| R0 | q   | w   | e   | r     | t     |       |
| R1 | a   | s   | d   | f     | g     |       |
| R2 | z   | x   | c   | v     | b     |       |
| R3 | Esc | Tab | Cmd | Lower | Space | Enter |

## Right half (C0 = outer pinky column)

Use the same new C0–C4 pins as the left: **`017`, `020`, `022`, `024`, `100`**. The previous mirrored controller-pin assignment is retired; physical key positions and the matrix transform are unchanged.

|    | C0    | C1  | C2  | C3   | C4        | C5 |
|----|-------|-----|-----|------|-----------|----|
| R0 | p     | o   | i   | u    | y         |    |
| R1 | Shift | l   | k   | j    | h         |    |
| R2 | /     | .   | ,   | m    | n         |    |
| R3 | ?     | (   | Alt | Backspace | Ctrl |    |
