# Cosmos wiring map

Same holes on both halves. Matches `boards/shields/cosmos/` (col2row).

- Switches: metal pins toward the top, all the same way.
- Diode: no-band leg on the switch pin, **band leg → row wire**.
- Other switch pin → column wire.
- **Blue = rows, yellow = columns.**

## Controller holes (silk label)

| Wire | Hole | Wire | Hole |
|---|---|---|---|
| R0 | `017` | C0 | `031` |
| R1 | `020` | C1 | `029` |
| R2 | `022` | C2 | `002` |
| R3 | `024` | C3 | `115` |
| | | C4 | `113` |
| | | C5 | `111` |

## Trackball sensor → R controller (right half only, 6 wires)

| Sensor pin | Controller hole |
|---|---|
| SCLK | `008` |
| SDIO | `011` |
| NCS | `100` |
| MOTION | `006` |
| VDD + VDDIO (bridge them on the sensor) | `VCC` |
| GND | `GND` |

NRESET: not wired (driver resets over SPI). Still free: `104`, `106`, `009`, `010`.

## Left half (C0 = outer pinky column)

|    | C0  | C1  | C2  | C3    | C4    | C5    |
|----|-----|-----|-----|-------|-------|-------|
| R0 | q   | w   | e   | r     | t     |       |
| R1 | a   | s   | d   | f     | g     |       |
| R2 | z   | x   | c   | v     | b     |       |
| R3 | Esc | Tab | Cmd | Lower | Space | Enter |

## Right half (C0 = outer pinky column)

**As soldered, the right board's column holes are mirrored:** C0 → `113`, C1 → `115`, C2 → `002`, C3 → `029`, C4 → `031` (fixed in `cosmos_right.overlay`).

|    | C0    | C1  | C2  | C3   | C4        | C5 |
|----|-------|-----|-----|------|-----------|----|
| R0 | p     | o   | i   | u    | y         |    |
| R1 | Shift | l   | k   | j    | h         |    |
| R2 | /     | .   | ,   | m    | n         |    |
| R3 | ?     | (   | Alt | Backspace | Ctrl |    |
