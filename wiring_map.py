"""Draw wiring-map.svg: real key positions (cosmos-41.kls.json) with row/column wires.

Keep MATRIX in sync with wiring.md / boards/shields/cosmos/*.
Run: python3 wiring_map.py
"""
import json
import math
import re
from pathlib import Path

LAYOUT = Path(__file__).parents[2] / "designs/cosmos-keyboard/cosmos-41.kls.json"
OUT = Path(__file__).with_name("wiring-map.svg")
U = 60  # px per key unit

# legend -> (row, col), per half; C0 = outer pinky column.
MATRIX = {
    "q": (0, 0), "w": (0, 1), "e": (0, 2), "r": (0, 3), "t": (0, 4),
    "a": (1, 0), "s": (1, 1), "d": (1, 2), "f": (1, 3), "g": (1, 4),
    "z": (2, 0), "x": (2, 1), "c": (2, 2), "v": (2, 3), "b": (2, 4),
    "Esc": (3, 0), "Tab": (3, 1), "Cmd": (3, 2), "Space": (3, 4), "Lower": (3, 3), "Enter": (3, 5),
    "p": (0, 0), "o": (0, 1), "i": (0, 2), "u": (0, 3), "y": (0, 4),
    "Shift": (1, 0), "l": (1, 1), "k": (1, 2), "j": (1, 3), "h": (1, 4),
    "/": (2, 0), ".": (2, 1), ",": (2, 2), "m": (2, 3), "n": (2, 4),
    "?": (3, 0), "(": (3, 1), "Alt": (3, 2), "Ctrl": (3, 4), "Backspace": (3, 3),
}
ROW_HOLES = ["031", "029", "002", "115"]
COL_HOLES = ["017", "020", "022", "024", "100", "106"]


def load_keys():
    keys = json.loads(LAYOUT.read_text())["keys"]
    out = []
    for k in keys:
        name = k["legend"]["center"]
        w = k.get("width", 1)
        cx, cy = (k["x"] + w / 2) * U + 40, (k["y"] + 0.5) * U + 70
        side = "L" if k["x"] < 7.5 else "R"
        out.append({"name": name, "w": w, "cx": cx, "cy": cy,
                    "rot": k.get("rotation", 0), "side": side, "rc": MATRIX[name]})
    return out


def key_svg(k):
    w, h = k["w"] * U - 6, U - 6
    r, c = k["rc"]
    return (
        f'<g transform="translate({k["cx"]:.1f},{k["cy"]:.1f}) rotate({k["rot"]})">'
        f'<rect x="{-w/2}" y="{-h/2}" width="{w}" height="{h}" rx="6" fill="#f4f4f4" stroke="#555"/>'
        f'<text y="-4" text-anchor="middle" font-size="13" font-weight="bold">{k["name"]}</text>'
        f'<text y="14" text-anchor="middle" font-size="10" fill="#666">R{r} C{c}</text></g>'
    )


def wires(keys, index, colour, width):
    """Polyline through keys sharing the same row (index=0) or column (index=1), per half."""
    lines = []
    for side in "LR":
        groups = {}
        for k in keys:
            if k["side"] == side:
                groups.setdefault(k["rc"][index], []).append(k)
        for group in groups.values():
            other = 1 - index
            group.sort(key=lambda k: k["rc"][other])
            pts = " ".join(f'{k["cx"]:.1f},{k["cy"]:.1f}' for k in group)
            lines.append(f'<polyline points="{pts}" fill="none" stroke="{colour}" '
                         f'stroke-width="{width}" stroke-linecap="round" opacity="0.8"/>')
    return lines


BLUE, YELLOW = "#1e6fd9", "#f2c200"
DETAIL_KEYS = [["q", "w", "e"], ["a", "s", "d"]]  # 2 rows x 3 cols of the left half
GAP = 160  # px between switches in the close-up


def line(x1, y1, x2, y2, colour, width=4):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{colour}" '
            f'stroke-width="{width}" stroke-linecap="round"/>')


def dot(x, y):
    """Solder joint."""
    return f'<circle cx="{x}" cy="{y}" r="6" fill="#bbb" stroke="#333" stroke-width="1.5"/>'


def label(x, y, text, size=12, colour="#333", anchor="start"):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{colour}" text-anchor="{anchor}">{text}</text>'


def switch_detail(cx, cy, name, row_y):
    """One switch seen from below: column pin (left), diode pin (right), diode down to the row wire."""
    col_pin, diode_pin = (cx - 22, cy - 20), (cx + 22, cy - 20)
    dx = diode_pin[0]
    return [
        f'<rect x="{cx-45}" y="{cy-45}" width="90" height="90" rx="8" fill="#efe6fb" stroke="#7a5aa6" stroke-width="2"/>',
        label(cx, cy + 32, name, 18, "#4b3470", "middle"),
        f'<rect x="{col_pin[0]-3}" y="{col_pin[1]-8}" width="6" height="16" fill="#b87333"/>',
        f'<rect x="{dx-3}" y="{diode_pin[1]-8}" width="6" height="16" fill="#b87333"/>',
        # diode: leg from pin, glass body with black band at the ROW end, leg to the row wire
        line(dx, diode_pin[1], dx + 40, diode_pin[1] + 10, "#999", 2),
        line(dx + 40, diode_pin[1] + 10, dx + 40, row_y, "#999", 2),
        f'<rect x="{dx+32}" y="{cy+5}" width="16" height="34" rx="5" fill="#e9a46a" stroke="#8a5a2b"/>',
        f'<rect x="{dx+32}" y="{cy+31}" width="16" height="7" fill="#111"/>',
    ], [dot(dx, diode_pin[1]), dot(dx + 40, row_y), dot(*col_pin)], col_pin


def detail_panel(top):
    """Close-up: switches, diodes, row/column wires and the controller holes they end in."""
    x0, y0 = 120, top + 130
    parts = [
        f'<line x1="20" y1="{top}" x2="1030" y2="{top}" stroke="#ccc" stroke-width="2"/>',
        label(40, top + 35, "Close-up: how one key connects (q w e / a s d, seen from below)", 20, "#000"),
        label(40, top + 58, "switch pin → diode → band end → BLUE row wire · other switch pin → YELLOW column wire", 13),
    ]
    board_x, board_top = x0 + 3 * GAP + 120, top + 70
    board, holes = controller(board_x, board_top, "L")
    bottom_y = y0 + len(DETAIL_KEYS) * GAP + 10  # column wires run along here to the board
    col_pins = [[] for _ in DETAIL_KEYS[0]]
    wires_svg, joints = [], []
    for r, row in enumerate(DETAIL_KEYS):
        cy = y0 + r * GAP
        row_y = cy + 62
        for c, name in enumerate(row):
            sw, sw_joints, pin = switch_detail(x0 + c * GAP, cy, name, row_y)
            parts += sw
            joints += sw_joints
            col_pins[c].append(pin)
        # Row wire approaches the physical 031 edge, on the right in this chip-up view.
        hole_x, hole_y = holes[ROW_HOLES[r]]
        route_x = board_x + 170 + r * 18
        wires_svg += [line(x0 - 30, row_y, route_x, row_y, BLUE),
                      line(route_x, row_y, route_x, hole_y, BLUE),
                      line(route_x, hole_y, hole_x, hole_y, BLUE),
                      label(x0 - 40, row_y + 4, f"R{r}", 14, BLUE, "end")]
    for c, pins in enumerate(col_pins):
        x = pins[0][0]
        hole_x, hole_y = holes[COL_HOLES[c]]
        route_x = board_x - 60 - c * 18
        wires_svg += [line(x, pins[0][1], x, bottom_y + c * 14, YELLOW, 6),
                      line(x, bottom_y + c * 14, route_x, bottom_y + c * 14, YELLOW, 6),
                      line(route_x, bottom_y + c * 14, route_x, hole_y, YELLOW, 6),
                      line(route_x, hole_y, hole_x, hole_y, YELLOW, 6),
                      label(x, pins[0][1] - 32, f"C{c}", 14, "#a07c00", "middle")]
    # Reuse the full controller drawing so labelled holes and cable endpoints cannot swap sides.
    ny = bottom_y + 80
    notes = [label(40, ny, "● grey dots = solder joints · black band always on the row side · "
                   "one row wire can touch many band legs", 13),
             label(40, ny + 20, "Rows and columns never touch metal-to-metal; crossing over insulated wire is fine.", 13)]
    height = ny + 50 - top
    # switches under the wires, solder joints on top, so you see each wire meet its pin
    return parts + wires_svg + board + joints + notes, height


def big_diode(x, y1, y2):
    """Vertical diode from y1 (no-band leg) to y2 (band leg). Glass body + black band near y2."""
    mid = (y1 + y2) / 2
    return [line(x, y1, x, y2, "#999", 3),
            f'<rect x="{x-14}" y="{mid-30}" width="28" height="60" rx="9" fill="#e9a46a" stroke="#8a5a2b" stroke-width="2"/>',
            f'<rect x="{x-14}" y="{mid+16}" width="28" height="11" fill="#111"/>']


def single_key_panel(top):
    """One key, big: both pins, diode body + band, yellow and blue wires; plus the diode-legs-as-row trick."""
    cx, cy = 230, top + 190
    pin1, pin2 = (cx - 40, cy - 40), (cx + 40, cy - 40)
    row_y, diode_x = cy + 200, cx + 130
    p = [
        f'<line x1="20" y1="{top}" x2="1030" y2="{top}" stroke="#ccc" stroke-width="2"/>',
        label(40, top + 35, "One key, close up (seen from below)", 20, "#000"),
        f'<rect x="{cx-90}" y="{cy-90}" width="180" height="180" rx="14" fill="#efe6fb" stroke="#7a5aa6" stroke-width="3"/>',
        label(cx, cy + 60, "switch", 18, "#4b3470", "middle"),
        f'<rect x="{pin1[0]-5}" y="{pin1[1]-14}" width="10" height="28" fill="#b87333"/>',
        f'<rect x="{pin2[0]-5}" y="{pin2[1]-14}" width="10" height="28" fill="#b87333"/>',
        label(pin1[0], pin1[1] + 36, "pin 1", 13, "#333", "middle"),
        label(pin2[0], pin2[1] + 36, "pin 2", 13, "#333", "middle"),
        # yellow: pin 1 straight to the column
        line(pin1[0], pin1[1], pin1[0] - 130, pin1[1], YELLOW, 7),
        line(pin1[0] - 130, pin1[1], pin1[0] - 130, row_y + 60, YELLOW, 7),
        label(pin1[0] - 140, pin1[1] - 62, "YELLOW column wire", 13, "#a07c00"),
        # diode: pin 2 -> no-band leg ... band leg -> blue
        line(pin2[0], pin2[1], diode_x, pin2[1], "#999", 3),
        *big_diode(diode_x, pin2[1], row_y),
        line(cx - 200, row_y, cx + 300, row_y, BLUE, 6),
        label(cx + 305, row_y + 5, "BLUE row wire", 13, BLUE),
        dot(*pin1), dot(*pin2), dot(diode_x, row_y),
        label(diode_x + 24, pin2[1] + 4, "no-band leg (solder to pin 2)", 13),
        label(diode_x + 24, (pin2[1] + row_y) / 2 - 10, "diode body: glass, don't heat", 13),
        label(diode_x + 24, (pin2[1] + row_y) / 2 + 26, "black band = row side", 13),
        label(diode_x + 24, row_y - 12, "band leg (solder to blue)", 13),
        label(40, row_y + 95, "Yellow and blue never touch each other directly: the switch connects them only while the key is pressed.", 13),
    ]
    # trick: diode band legs joined leg-to-leg form the row
    tx, ty = 640, top + 110
    p += [label(tx, ty - 30, "Trick: diode legs as the row wire", 16, "#000"),
          label(tx, ty - 10, "band legs bent sideways and soldered to each other", 12)]
    for i in range(3):
        kx = tx + 20 + i * 120
        p += [f'<rect x="{kx-40}" y="{ty+10}" width="80" height="80" rx="8" fill="#efe6fb" stroke="#7a5aa6" stroke-width="2"/>',
              f'<rect x="{kx+16}" y="{ty+22}" width="6" height="14" fill="#b87333"/>',
              *big_diode(kx + 50, ty + 29, ty + 150),
              line(kx + 50, ty + 150, kx + 170, ty + 150, "#999", 3) if i < 2 else "",
              line(kx + 19, ty + 29, kx + 50, ty + 29, "#999", 3),
              dot(kx + 19, ty + 29), dot(kx + 50, ty + 150)]
    p += [line(tx + 310, ty + 150, tx + 370, ty + 150, BLUE, 6),
          label(tx, ty + 180, "bent band legs = the row → blue wire only to the controller", 12),
          label(tx, ty + 198, "(use blue between keys where the legs can't reach)", 12, "#666")]
    return p, row_y + 130 - top


# Pro Micro edges, USB at the top, chip side up (top to bottom).
LEFT_EDGE = ["006", "008", "GND", "GND", "017", "020", "022", "024", "100", "011", "104", "106"]
RIGHT_EDGE = ["RAW", "GND", "RST", "VCC", "031", "029", "002", "115", "113", "111", "010", "009"]
TRACKBALL = {"008", "011", "104", "006"}  # SCLK, SDIO, NCS, MOTION (cosmos_right.overlay)
S = 68  # px per key unit in the full wiring panel


def rotate(x, y, deg):
    a = math.radians(deg)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def controller(bx, by, side, back=False):
    """Pro Micro outline with every hole labelled; back=True = seen from its back (edges swap)."""
    parts = [f'<rect x="{bx}" y="{by}" width="130" height="290" rx="8" fill="#2b4fa8"/>',
             f'<rect x="{bx+47}" y="{by-12}" width="36" height="22" rx="4" fill="#c9c9c9"/>',
             label(bx + 65, by + 275, f"{side} board ({'back side' if back else 'chip up'})", 12, "#fff", "middle")]
    holes = {}
    edges = (RIGHT_EDGE, LEFT_EDGE) if back else (LEFT_EDGE, RIGHT_EDGE)
    for i, (lh, rh) in enumerate(zip(*edges)):
        y = by + 30 + i * 20
        holes[lh], holes[rh] = (bx + 12, y), (bx + 118, y)
        for name, x, anchor, dx in ((lh, bx + 12, "start", 10), (rh, bx + 118, "end", -10)):
            used = name in ROW_HOLES or name in COL_HOLES
            fill = "#40e0d0" if side == "R" and name in TRACKBALL else ("#fff" if used else "#8fa6d8")
            parts += [f'<circle cx="{x}" cy="{y}" r="5" fill="{fill}" stroke="#111"/>',
                      label(x + dx, y + 4, name, 10, "#fff" if used else "#aab8dd", anchor)]
    return parts, holes


def chain(group, point):
    """Order keys as the shortest-hop chain from the first one (wire order doesn't matter electrically).
    ponytail: greedy nearest-neighbour, fine for <= 6 keys per wire."""
    rest, path = group[1:], [group[0]]
    while rest:
        last = path[-1][point]
        nxt = min(rest, key=lambda k: (k[point][0] - last[0]) ** 2 + (k[point][1] - last[1]) ** 2)
        rest.remove(nxt)
        path.append(nxt)
    return path


# Two band legs (~25 mm each, ~5 mm used at the body) can bridge about one key pitch (19 mm).
# ponytail: straight-line estimate on the flat layout; the curved case may need blue on a few more gaps.
LEG_REACH = 1.3  # key units


def full_panel(top, mirror=False, legs=False):
    """Whole keyboard: every key with pins + diode, every wire to its exact hole.
    mirror=True = each half flipped over left<->right, as seen while soldering upside down."""
    raw = json.loads(LAYOUT.read_text())["keys"]
    keys = []
    for k in raw:
        w = k.get("width", 1)
        name = k["legend"]["center"]
        keys.append({"name": name, "w": w, "kx": k["x"] + w / 2, "ky": k["y"] + 0.5,
                     "rot": k.get("rotation", 0), "side": "L" if k["x"] < 7.5 else "R", "rc": MATRIX[name]})
    if mirror:  # flip each half in place: x mirrored inside its own half, rotations reversed
        for side in "LR":
            half = [k for k in keys if k["side"] == side]
            lo, hi = min(k["kx"] for k in half), max(k["kx"] for k in half)
            for k in half:
                k["kx"], k["rot"] = lo + hi - k["kx"], -k["rot"]
    sx = -1 if mirror else 1  # local left/right of the pins and diode flip too
    for k in keys:
        k["cx"], k["cy"] = 40 + k["kx"] * S, top + 110 + k["ky"] * S

        def g(lx, ly, k=k):
            rx, ry = rotate(sx * lx, ly, k["rot"])
            return k["cx"] + rx, k["cy"] + ry
        k["pin1"], k["pin2"] = g(-0.22 * S, -0.25 * S), g(0.22 * S, -0.25 * S)

    parts = [f'<line x1="20" y1="{top}" x2="1100" y2="{top}" stroke="#ccc" stroke-width="2"/>',
             label(40, top + 35, "SOLDERING VIEW + DIODE-LEG ROWS: each colour = one diode; colour changes where it's soldered to the next"
                   if legs else "SOLDERING VIEW: each half flipped over (what you see with the case upside down)"
                   if mirror else "Full wiring: every key, diode and wire (top view, as if the case were see-through)", 20, "#000"),
             label(40, top + 58, "Left↔right mirrored vs. the top view; labels kept readable. Outer pinky column is now on the inside edge."
                   if mirror else "Each diode lies sideways from pin 2 toward the next key in its row (blue = row wire).", 13),
             label(40, top + 76, "Board drawn from its back (hole rows swap sides). If you see the chip, read the holes from the top view. "
                   "Turquoise = trackball sensor wires (right board)."
                   if mirror else "Case upside down for soldering = the next picture (mirrored). "
                   "Grey dots = solder joints. Turquoise holes = trackball (right board).", 13)]
    key_svg_parts, joints, wire_svg = [], [], []
    for k in keys:
        w, h = k["w"] * S - 8, S - 8
        r, c = k["rc"]
        key_svg_parts.append(
            f'<g transform="translate({k["cx"]:.1f},{k["cy"]:.1f}) rotate({k["rot"]})">'
            f'<rect x="{-w/2}" y="{-h/2}" width="{w}" height="{h}" rx="6" fill="#efe6fb" stroke="#7a5aa6"/>'
            f'<text y="4" x="{-6*sx}" text-anchor="middle" font-size="13" font-weight="bold" fill="#4b3470">{k["name"]}</text>'
            f'<text y="20" x="{-6*sx}" text-anchor="middle" font-size="9" fill="#666">R{r} C{c}</text>'
            f'<g transform="scale({sx},1)">'
            f'<rect x="{-0.22*S-3}" y="{-0.25*S-7}" width="6" height="14" fill="#b87333"/>'
            f'<rect x="{0.22*S-3}" y="{-0.25*S-7}" width="6" height="14" fill="#b87333"/></g></g>')
        joints += [dot(*k["pin1"]), dot(*k["pin2"])]

    bottom = max(k["cy"] for k in keys) + 70
    holes, diodes = {}, []
    for side in "LR":
        half = [k for k in keys if k["side"] == side]
        mid = sum(k["cx"] for k in half) / len(half)
        board, holes[side] = controller(mid - 65, bottom, side, back=mirror)
        parts += board
        wire_svg += column_wires(half, holes[side])
        for n in range(len(ROW_HOLES)):
            row = sorted((k for k in half if k["rc"][0] == n), key=lambda k: k["rc"][1])
            if row:
                w_svg, d_svg, j_svg = row_wires(chain(row, "pin2"), holes[side][ROW_HOLES[n]], n, legs)
                wire_svg += w_svg
                diodes += d_svg
                joints += j_svg
    parts.append(label(40, bottom + 330, "Dashed line = the wire from the end of that row/column to its hole. "
                       "Controller position is schematic: route to wherever the holder sits, with ~3 cm slack.", 13))
    # wires over keys, then joints on top, then controllers on top of the dashed ends
    return [parts[0], parts[1], parts[2]] + key_svg_parts + wire_svg + diodes + joints + parts[3:], bottom + 360 - top


def column_wires(half, holes, dashed=True):
    """Yellow: chain each column through pin 1 of its keys, dashed to its hole (or just an end label)."""
    out = []
    for n in range(len(COL_HOLES)):
        col = sorted((k for k in half if k["rc"][1] == n), key=lambda k: k["rc"][0])
        if not col:
            continue
        pts = [k["pin1"] for k in chain(col, "pin1")]
        hx, hy = holes[COL_HOLES[n]]
        end = min(pts, key=lambda p: (p[0] - hx) ** 2 + (p[1] - hy) ** 2)
        out.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" stroke="{YELLOW}" '
                   f'stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')
        if dashed:
            out += [f'<line x1="{end[0]:.1f}" y1="{end[1]:.1f}" x2="{hx}" y2="{hy}" stroke="{YELLOW}" '
                    f'stroke-width="4.5" stroke-dasharray="8 5" opacity="0.9"/>',
                    label(end[0] - 8, end[1] - 8, f"C{n}", 11, "#a07c00", "end")]
        else:
            out.append(f'<text x="{end[0]:.1f}" y="{end[1] - 14:.1f}" font-size="15" font-weight="bold" fill="#8a6a00" '
                       f'text-anchor="middle" stroke="white" stroke-width="4" paint-order="stroke">C{n} → {COL_HOLES[n]}</text>')
    return out


def row_wires(row, hole, n, legs):
    """One row: each diode lies from pin 2 toward the next key (the last one toward its hole).
    Its band leg runs on to the next key's joint (just past that diode's band). In the legs view each
    diode has its own colour; blue where keys are too far apart for the legs to reach."""
    for i, k in enumerate(row):
        tx, ty = row[i + 1]["pin2"] if i + 1 < len(row) else hole
        px, py = k["pin2"]
        d = math.hypot(tx - px, ty - py) or 1
        k["u"] = ((tx - px) / d, (ty - py) / d)
        k["joint"] = (px + k["u"][0] * 0.55 * S, py + k["u"][1] * 0.55 * S)
    wires_out, diodes_out, joints_out = [], [], []
    for i, k in enumerate(row):
        colour = DIODE_COLOURS[i % len(DIODE_COLOURS)] if legs else "#999"
        (px, py), (jx, jy), (ux, uy) = k["pin2"], k["joint"], k["u"]
        wires_out.append(line(round(px, 1), round(py, 1), round(jx, 1), round(jy, 1), colour, 3))
        if i + 1 < len(row):  # band leg on to the next key's joint
            nx, ny = row[i + 1]["joint"]
            too_far = math.hypot(nx - jx, ny - jy) > LEG_REACH * S
            seg = BLUE if (too_far or not legs) else colour
            wires_out.append(line(round(jx, 1), round(jy, 1), round(nx, 1), round(ny, 1), seg, 5 if seg == BLUE else 3))
        else:  # last key: blue to the controller
            wires_out += [f'<line x1="{jx:.1f}" y1="{jy:.1f}" x2="{hole[0]}" y2="{hole[1]}" stroke="{BLUE}" '
                          f'stroke-width="2.5" stroke-dasharray="8 5" opacity="0.9"/>',
                          label(jx - 8, jy - 8, f"R{n}", 11, BLUE, "end")]
        bx, by = px + ux * 0.3 * S, py + uy * 0.3 * S
        angle = math.degrees(math.atan2(uy, ux))
        diodes_out.append(f'<g transform="translate({bx:.1f},{by:.1f}) rotate({angle:.1f})">'
                          f'<rect x="-11" y="-6" width="22" height="12" rx="4" fill="#e9a46a" stroke="#8a5a2b"/>'
                          f'<rect x="6" y="-6" width="5" height="12" fill="#111"/></g>')
        joints_out.append(dot(jx, jy))
    return wires_out, diodes_out, joints_out


CHAIN_OUT = Path(__file__).with_name("diode-chain.svg")


DIODE_COLOURS = ["#2a9d8f", "#e63946", "#8338ec"]  # one colour per diode in the RIGHT row


def side_diode(px, py, kink_x, row_y, colour="#999"):
    """Diode lying sideways from a pin: no-band leg -> body -> band (right) -> leg, short kink down to the row."""
    return [line(px, py, kink_x, py, colour, 3),
            line(kink_x, py, kink_x, row_y, colour, 3),
            f'<rect x="{px+22}" y="{py-11}" width="52" height="22" rx="8" fill="#e9a46a" stroke="#8a5a2b" stroke-width="2"/>',
            f'<rect x="{px+62}" y="{py-11}" width="9" height="22" fill="#111"/>']


def chain_row(y, wrong=False):
    """Three keys whose diodes form the row: band leg -> next band leg (or, if wrong, -> next switch pin)."""
    parts, overlay, xs = [], [], [170, 450, 730]
    band_y = y + 52  # row line: just below the diodes, so it passes under the next key's diode
    for i, cx in enumerate(xs):
        pin1, pin2 = (cx - 35, y + 20), (cx + 35, y + 20)
        parts += [f'<rect x="{cx-70}" y="{y-40}" width="140" height="120" rx="12" fill="#efe6fb" stroke="#7a5aa6" stroke-width="2"/>',
                  label(cx, y + 65, f"key {i+1}", 15, "#4b3470", "middle"),
                  line(pin1[0], pin1[1], pin1[0], y - 70, YELLOW, 6),
                  label(pin1[0] - 8, y - 75, "yellow column", 11, "#a07c00", "end"),
                  f'<rect x="{pin1[0]-4}" y="{pin1[1]-10}" width="8" height="20" fill="#b87333"/>',
                  f'<rect x="{pin2[0]-4}" y="{pin2[1]-10}" width="8" height="20" fill="#b87333"/>',
                  label(pin2[0] + 10, pin2[1] - 12, "pin 2", 11)]
        bypassed = wrong and i == 1
        # diode lies sideways toward the next key; band leg kinks down a few mm onto the row line
        kink_x = pin2[0] + 90
        leg = "#999" if wrong else DIODE_COLOURS[i]
        parts += side_diode(pin2[0], pin2[1], kink_x, band_y, leg)
        if not wrong:
            parts += [label(pin2[0] - 4, pin2[1] - 30, f"diode {i+1} starts", 11, leg, "middle"),
                      line(pin2[0], pin2[1] - 26, pin2[0], pin2[1] - 10, leg, 1.5)]
        if bypassed:
            parts.append(label(pin2[0] + 20, pin2[1] - 18, "this diode is skipped!", 12, "#d00"))
        last = i == len(xs) - 1
        if not last:
            nxt_pin2 = (xs[i + 1] + 35, y + 20)
            if wrong and i == 0:  # band leg goes to key 2's switch pin instead of key 2's band leg
                overlay += [line(kink_x, band_y, nxt_pin2[0] - 20, band_y, "#d00", 3),
                          line(nxt_pin2[0] - 20, band_y, nxt_pin2[0], nxt_pin2[1] + 6, "#d00", 3),
                          dot(*nxt_pin2),
                          f'<text x="{nxt_pin2[0]+12}" y="{nxt_pin2[1]+30}" font-size="34" fill="#d00" font-weight="bold">✕</text>',
                          label(nxt_pin2[0] + 50, nxt_pin2[1] + 20, "band leg soldered onto key 2's pin 2", 12, "#d00")]
            else:
                end_x = nxt_pin2[0] + 90
                parts += [line(kink_x, band_y, end_x, band_y, leg, 3),
                          label(end_x, band_y + 34, f"diode {i+1} ends here", 11, leg, "middle"),
                          label(end_x, band_y + 48, f"(soldered to diode {i+2})", 10, "#666", "middle"),
                          line(end_x, band_y + 8, end_x, band_y + 22, leg, 1.5)]
        else:
            blue_x = kink_x + 60  # last diode's leg runs a little further, then blue takes over
            parts += [line(kink_x, band_y, blue_x, band_y, leg, 3),
                      line(blue_x, band_y, blue_x + 80, band_y, BLUE, 6),
                      label(blue_x + 85, band_y + 5, "blue → controller", 12, BLUE)]
            if not wrong:
                parts += [label(blue_x + 30, band_y + 34, f"diode {i+1} ends here", 11, leg, "middle"),
                          label(blue_x + 30, band_y + 48, "(blue starts)", 10, "#666", "middle"),
                          line(blue_x, band_y + 8, blue_x, band_y + 22, leg, 1.5), dot(blue_x, band_y)]
        parts += [dot(*pin2), dot(kink_x, band_y), dot(*pin1)]
    return parts + overlay


def diode_chain_svg():
    """Separate picture: diode legs as the row (right) vs. band leg on the next switch pin (wrong)."""
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1140" height="900" font-family="Helvetica">',
             '<rect width="100%" height="100%" fill="white"/>',
             label(40, 40, "Skip the blue: join the diodes directly (one row, seen from below)", 22, "#000"),
             label(40, 66, "Each diode lies sideways from pin 2 toward the next key. After the band, its leg kinks down a few mm", 14),
             label(40, 86, "and runs on to the NEXT key's kink. The kink keeps the row under the next diode instead of touching it.", 14),
             label(40, 130, "✅ RIGHT: band leg → next key's band leg", 18, "#080")]
    parts += chain_row(220)
    parts += [label(40, 410, "Each colour = one diode, from its switch pin to where it's soldered onto the next diode's leg.", 14),
              label(40, 430, "The bent band legs ARE the row. No blue between keys; blue only from the last key to the controller.", 14),
              f'<line x1="20" y1="470" x2="1040" y2="470" stroke="#ccc" stroke-width="2"/>',
              label(40, 520, "❌ WRONG: band leg → next key's switch pin", 18, "#d00")]
    parts += chain_row(610, wrong=True)
    parts += [label(40, 820, "Key 2 still types, but the row now touches key 2's switch directly, so key 2's diode does nothing.", 14),
              label(40, 842, "Pressing several keys at once can then produce wrong letters (ghosting). Band legs only touch band legs or blue.", 14),
              "</svg>"]
    CHAIN_OUT.write_text("\n".join(parts))
    print(f"wrote {CHAIN_OUT}")


SOLDER_OUT = Path(__file__).with_name("soldering-view.svg")
S2 = 125  # px per key unit in the big soldering view
# Controller centre in layout key units (x, y), from the Microcontroller mesh in cosmotylleft/right.glb
# (keyyboard-full/), mapped onto cosmos-41.kls.json via the outer-column keys. USB points to the back edge.
CTRL_POS = {"L": (2.79, 0.69), "R": (13.2, 0.69)}
BOARD_UNITS = (0.95, 1.74)  # SuperMini 18 x 33 mm in key units (19 mm)


def controller_real(cx, cy, side="L"):
    """SuperMini at real size, seen from its back (case upside down), USB toward the back edge (up)."""
    w, h = BOARD_UNITS[0] * S2 * 1.4, BOARD_UNITS[1] * S2 * 1.4  # drawn 1.4x so the hole labels are readable
    x0, y0 = cx - w / 2, cy - h / 2
    parts = [f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" rx="6" fill="#2b4fa8" opacity="0.88"/>',
             f'<rect x="{cx-16:.1f}" y="{y0-12:.1f}" width="32" height="18" rx="4" fill="#c9c9c9"/>',
             label(cx, y0 - 18, "USB (back edge)", 12, "#333", "middle"),
             label(cx, y0 + h - 8, "controller (back side)", 11, "#fff", "middle")]
    holes = {}
    for i, (lh, rh) in enumerate(zip(RIGHT_EDGE, LEFT_EDGE)):  # back view: edges swap
        y = y0 + 22 + i * (h - 44) / 11
        holes[lh], holes[rh] = (x0 + 9, y), (x0 + w - 9, y)
        for name, x, anchor, dx in ((lh, x0 + 9, "start", 8), (rh, x0 + w - 9, "end", -8)):
            used = name in ROW_HOLES or name in COL_HOLES
            sensor = side == "R" and (name in TRACKBALL or name == "VCC" or name == "GND" and i == 1)
            fill = "#40e0d0" if sensor else ("#fff" if used else "#8fa6d8")
            parts += [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{fill}" stroke="#111"/>',
                      label(round(x + dx, 1), round(y + 4, 1), name, 10, "#fff" if used else "#aab8dd", anchor)]
    return parts, holes


# Row chain order Roi actually solders (overrides the nearest-neighbour guess). Order doesn't matter electrically.
ROW_ORDER = {("L", 3): ["Esc", "Tab", "Cmd", "Lower", "Enter", "Space"]}


def soldering_half(top, side):
    """One half, big, as seen with the case upside down (mirrored). Diodes drawn like the real build:
    pin 2 -> across its own switch -> band in the gap below; the next key's band leg runs along the gap
    and crosses it (= solder joint)."""
    keys = []
    for k in json.loads(LAYOUT.read_text())["keys"]:
        if ("L" if k["x"] < 7.5 else "R") != side:
            continue
        w, name = k.get("width", 1), k["legend"]["center"]
        keys.append({"name": name, "w": w, "kx": k["x"] + w / 2, "ky": k["y"] + 0.5,
                     "rot": k.get("rotation", 0), "rc": MATRIX[name]})
    lo, hi = min(k["kx"] for k in keys), max(k["kx"] for k in keys)
    for k in keys:  # flip over: mirror x inside the half, reverse rotation
        k["kx"], k["rot"] = lo + hi - k["kx"], -k["rot"]
        k["cx"], k["cy"] = 60 + (k["kx"] - lo + 0.8) * S2, top + 470 + k["ky"] * S2

        def g(lx, ly, k=k):
            rx, ry = rotate(-lx, ly, k["rot"])
            return k["cx"] + rx, k["cy"] + ry
        k["pin1"], k["pin2"], k["drop"] = g(-0.22 * S2, -0.25 * S2), g(0.22 * S2, -0.25 * S2), g(0.15 * S2, 0.5 * S2)

    ccx = lo + hi - CTRL_POS[side][0]  # mirrored like the keys
    # drawn ABOVE the keys (same left/right spot, USB to the back) so it doesn't cover them
    board_cy = min(k["cy"] for k in keys) - 0.5 * S2 - 40 - BOARD_UNITS[1] * S2 * 0.7
    board, holes = controller_real(60 + (ccx - lo + 0.8) * S2, board_cy, side)
    name = "LEFT" if side == "L" else "RIGHT"
    parts = [label(40, top + 10, f"{name} HALF — case upside down (what you see while soldering)", 24, "#000")]
    for k in keys:
        w, h = k["w"] * S2 - 12, S2 - 12
        r, c = k["rc"]
        parts.append(
            f'<g transform="translate({k["cx"]:.1f},{k["cy"]:.1f}) rotate({k["rot"]})">'
            f'<rect x="{-w/2}" y="{-h/2}" width="{w}" height="{h}" rx="10" fill="#efe6fb" stroke="#7a5aa6" stroke-width="2"/>'
            f'<text x="{0.14*S2}" y="8" text-anchor="middle" font-size="20" font-weight="bold" fill="#4b3470">{k["name"]}</text>'
            f'<text x="{0.14*S2}" y="28" text-anchor="middle" font-size="12" fill="#666">R{r} C{c}</text>'
            f'<rect x="{0.22*S2-4}" y="{-0.25*S2-10}" width="8" height="20" fill="#b87333"/>'
            f'<rect x="{-0.22*S2-4}" y="{-0.25*S2-10}" width="8" height="20" fill="#b87333"/></g>')
    parts += column_wires(keys, holes, dashed=False)
    ends = []  # (x, y, hole, colour): where each row/column wire leaves for the controller
    for n in range(len(COL_HOLES)):
        col = [k["pin1"] for k in keys if k["rc"][1] == n]
        if col:
            hx, hy = holes[COL_HOLES[n]]
            ends.append((*min(col, key=lambda p: (p[0] - hx) ** 2 + (p[1] - hy) ** 2), COL_HOLES[n], YELLOW))
    legs, bodies, joints = [], [], []
    for n in range(len(ROW_HOLES)):
        row = sorted((k for k in keys if k["rc"][0] == n), key=lambda k: k["rc"][1])
        order = ROW_ORDER.get((side, n))
        row = sorted(row, key=lambda k: order.index(k["name"])) if order else chain(row, "drop")
        for i, k in enumerate(row):
            colour = DIODE_COLOURS[i % len(DIODE_COLOURS)]
            (px, py), (dx, dy) = k["pin2"], k["drop"]
            legs.append(line(round(px, 1), round(py, 1), round(dx, 1), round(dy, 1), colour, 4))
            ux, uy = dx - px, dy - py
            bx_, by_ = px + ux * 0.62, py + uy * 0.62
            angle = math.degrees(math.atan2(uy, ux))
            bodies.append(f'<g transform="translate({bx_:.1f},{by_:.1f}) rotate({angle:.1f})">'
                          f'<rect x="-17" y="-8" width="34" height="16" rx="6" fill="#e9a46a" stroke="#8a5a2b" stroke-width="1.5"/>'
                          f'<rect x="9" y="-8" width="7" height="16" fill="#111"/></g>')
            if i + 1 < len(row):  # band leg along the gap to the next key's drop, crossing it a little
                nx, ny = row[i + 1]["drop"]
                d = math.hypot(nx - dx, ny - dy) or 1
                far = d > LEG_REACH * S2
                ex, ey = nx + (nx - dx) / d * 14, ny + (ny - dy) / d * 14
                legs.append(line(round(dx, 1), round(dy, 1), round(ex, 1), round(ey, 1), BLUE if far else colour, 6 if far else 4))
            else:
                ends.append((dx, dy, ROW_HOLES[n], BLUE))
                legs.append(f'<text x="{dx:.1f}" y="{dy + 26:.1f}" font-size="15" font-weight="bold" fill="{BLUE}" '
                            f'text-anchor="middle" stroke="white" stroke-width="4" paint-order="stroke">R{n} → {ROW_HOLES[n]}</text>')
            joints += [dot(px, py), dot(dx, dy)]
    joints += [dot(*k["pin1"]) for k in keys]
    # the board sits above the switch bottoms when the case is upside down: draw it over them, cables on top
    cables = [f'<line x1="{ex:.1f}" y1="{ey:.1f}" x2="{holes[h][0]:.1f}" y2="{holes[h][1]:.1f}" stroke="{colour}" '
              f'stroke-width="4" stroke-dasharray="1 7" stroke-linecap="round"/>' for ex, ey, h, colour in ends]
    height = max(k["cy"] for k in keys) + 1.2 * S2 - top
    return parts + legs + bodies + joints + board + cables, max(height, 480)


TRACKBALL_WIRES = [  # sensor pin, hole, what it does (cosmos_right.overlay)
    ("MOTION", "006", "tells the board the ball moved"),
    ("SCLK", "008", "clock"),
    ("NCS", "104", "chip select"),
    ("SDIO", "011", "data"),
    ("VDD", "VCC", "power; VDDIO unconnected (see sensor-wiring.html)"),
    ("GND", "GND", "ground: the GND next to RAW"),
]


def table(x, y, title, head, rows, widths, colour, bold_col):
    """Simple SVG table: title, coloured header row, striped body rows. Returns parts and bottom y."""
    rh = 30
    parts = [label(x, y, title, 20, "#000")]
    y += 12
    for r, cells in enumerate([head] + rows):
        fill = colour if r == 0 else ("#f3f3f3" if r % 2 else "#fff")
        parts.append(f'<rect x="{x}" y="{y}" width="{sum(widths)}" height="{rh}" fill="{fill}" stroke="#ccc"/>')
        cx = x
        for c, (text, w) in enumerate(zip(cells, widths)):
            bold = r == 0 or c == bold_col
            parts.append(f'<text x="{cx + 10}" y="{y + 21}" font-size="16" fill="{"#fff" if r == 0 else "#111"}"'
                         f'{" font-weight=\"bold\"" if bold else ""}>{text}</text>')
            cx += w
        y += rh
    return parts, y


def hole_tables(top):
    """Which wire goes into which controller hole (both halves) + the trackball's extra wires."""
    names = list(MATRIX)
    sides = {"L": names[:21], "R": names[21:]}
    keys_on = lambda side, i, j: " ".join(sorted((k for k in sides[side] if MATRIX[k][i] == j),
                                                  key=lambda k: MATRIX[k][1 - i])) or "—"
    pos = lambda h: (f"017 edge, hole {LEFT_EDGE.index(h) + 1}" if h in LEFT_EDGE
                     else f"031 edge, hole {RIGHT_EDGE.index(h) + 1}")
    rows = [[f"R{j}", keys_on("L", 0, j), keys_on("R", 0, j), h, pos(h)] for j, h in enumerate(ROW_HOLES)]
    cols = [[f"C{j}", keys_on("L", 1, j), keys_on("R", 1, j), h, pos(h)] for j, h in enumerate(COL_HOLES)]
    widths = [130, 330, 300, 90, 330]
    head = ["Wire", "Left half keys", "Right half keys", "Hole", "Where (count from the USB end)"]
    parts, y = table(40, top, "ROWS (blue) → controller holes, same holes on both boards", head, rows, widths, BLUE, 3)
    more, y = table(40, y + 50, "COLUMNS (yellow) → controller holes, same holes on both boards", head, cols, widths,
                    "#c9a000", 3)
    parts += more
    tb = [[p, h, pos(h) if h != "GND" else "031 edge, hole 2", what] for p, h, what in TRACKBALL_WIRES]
    more, y = table(40, y + 50, "Trackball sensor → RIGHT board only (6 extra wires, turquoise holes)",
                    ["Sensor pin", "Hole", "Where (count from the USB end)", "What it does"], tb,
                    [150, 90, 280, 660], "#1a8f86", 1)
    parts += more
    parts.append(label(40, y + 26, "017 edge = side with 017…024. 031 edge = side with RST/VCC. Read the printed label, not just the hole count.", 14, "#666"))
    parts.append(label(40, y + 48, "C5 / 106 = LEFT Enter only (no right wire). First five columns consecutive; skip 011 / 104 for LEFT Enter (106). VDDIO / NRESET: unconnected.", 14, "#666"))
    return parts, y + 70 - top


def soldering_svg():
    """Big two-part picture: hole tables, then left half, then right half, in the real soldering orientation."""
    intro = [label(40, 40, "Soldering view — NEW pin map for BOTH halves · case upside down", 26, "#000"),
             label(40, 72, "Each COLOUR = one diode: starts at its switch's pin 2, crosses its own switch, band in the gap below,", 16),
             label(40, 94, "then its leg runs along the gap and CROSSES the next key's leg = solder joint (grey dot). Colour changes = next diode.", 16),
             label(40, 116, "Blue = wire where legs can't reach. Yellow = column wire on pin 1. DOTTED = cable from that end to its controller hole.", 16),
             label(40, 138, "Controller drawn ABOVE the keys at its real left/right spot (it actually sits under the top keys), seen from its back, "
                   "USB to the back edge. Shown 1.4x size.", 14, "#666"),
             label(40, 160, "Turquoise holes (right board) = trackball sensor wires: 006 MOTION, 008 SCLK, 011 SDIO, 104 NCS, VCC, GND.",
                   14, "#1a8f86"),
             label(40, 184, "Rewire controller ends and flash matching firmware. Keep the existing diode chains and key positions unchanged.", 15, "#9a400e")]
    tables, tables_h = hole_tables(210)
    start = 210 + tables_h
    left, left_h = soldering_half(start, "L")
    right, right_h = soldering_half(start + left_h + 60, "R")
    total = start + left_h + 60 + right_h + 40
    sep = f'<line x1="20" y1="{start + left_h + 20}" x2="1240" y2="{start + left_h + 20}" stroke="#ccc" stroke-width="3"/>'
    SOLDER_OUT.write_text("\n".join([f'<svg xmlns="http://www.w3.org/2000/svg" width="1260" height="{total:.0f}" '
                                      'font-family="Helvetica">', '<rect width="100%" height="100%" fill="white"/>']
                                     + intro + tables + left + [sep] + right + ["</svg>"]))
    print(f"wrote {SOLDER_OUT}")


HOLE_OUT = Path(__file__).with_name("through-hole.svg")


def hole_step(x0, title, lines, wire=True, iron=False, solder=False, fillet=False):
    """One side-view step: controller board cut through a plated hole, wire coming from above."""
    cx, by = x0 + 150, 300  # hole centre, board top
    p = [label(x0 + 20, 90, title, 18, "#000")]
    p += [label(x0 + 20, 115 + i * 20, t, 13) for i, t in enumerate(lines)]
    # board (blue) with a hole; copper ring top + bottom and plated barrel
    p += [f'<rect x="{x0+20}" y="{by}" width="{cx-x0-28}" height="30" fill="#2b4fa8"/>',
          f'<rect x="{cx+8}" y="{by}" width="{x0+280-cx-8}" height="30" fill="#2b4fa8"/>',
          f'<rect x="{cx-20}" y="{by-3}" width="12" height="36" fill="#d4a017"/>',
          f'<rect x="{cx+8}" y="{by-3}" width="12" height="36" fill="#d4a017"/>',
          label(x0 + 25, by + 52, "controller board (side cut)", 11, "#2b4fa8"),
          label(cx + 26, by - 8, "copper ring", 11, "#a07c00")]
    if wire:  # insulated blue wire, bare tinned tip pushed through the hole
        p += [f'<rect x="{cx-6}" y="185" width="12" height="{by-185-28}" rx="3" fill="{BLUE}"/>',
              f'<rect x="{cx-3}" y="{by-28}" width="6" height="74" fill="#c0c0c0"/>',
              label(cx - 14, 205, "blue wire", 12, BLUE, "end"),
              label(cx - 14, by - 12, "bare, tinned tip", 11, "#555", "end")]
    if fillet:  # finished joint: shiny cone around the wire, filling the hole
        p += [f'<path d="M{cx-22},{by-3} Q{cx-6},{by-6} {cx-3},{by-24} L{cx+3},{by-24} Q{cx+6},{by-6} {cx+22},{by-3} Z" fill="#d9d9d9" stroke="#888"/>',
              f'<rect x="{cx-8}" y="{by}" width="16" height="30" fill="#d9d9d9"/>',
              label(cx + 30, by - 30, "small shiny cone", 12, "#080")]
    if iron:  # iron tip touching ring AND wire
        p += [f'<path d="M{cx+130},{by-150} L{cx+16},{by-12} L{cx+6},{by-18} L{cx+110},{by-165} Z" fill="#777"/>',
              label(cx + 70, by - 160, "iron: touch ring + wire", 12, "#333")]
    if solder:  # solder wire fed to the joint from the other side
        p += [line(cx - 120, by - 110, cx - 14, by - 10, "#bfbfbf", 6),
              label(cx - 140, by - 118, "solder: feed into the joint", 12, "#333")]
    return p


def through_hole_svg():
    """How a wire is soldered into a controller hole, in three steps (side view)."""
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="430" font-family="Helvetica">',
             '<rect width="100%" height="100%" fill="white"/>',
             label(20, 40, "Soldering a wire into a controller hole (side view)", 22, "#000"),
             label(20, 64, "USB AND battery disconnected while soldering. The plated copper hole lets solder grip the wire.", 14)]
    parts += hole_step(0, "1. Push the wire in", ["Strip ~3 mm, tin it.", "Push the tip through the hole;", "bend it a little so it stays."])
    parts += hole_step(330, "2. Heat + add solder", ["Iron on the ring AND the wire,", "1-2 s. Then touch solder to", "the joint, not to the iron."],
                       iron=True, solder=True)
    parts += hole_step(660, "3. Done", ["Remove solder, then iron.", "Hold still 3 s. Tug to test.", "Trim the tip on the far side."], fillet=True)
    parts.append(label(20, 410, "Check: no solder bridge to the next hole (especially RST next to 031). To undo: heat the joint and pull the wire out.", 13))
    parts.append("</svg>")
    HOLE_OUT.write_text("\n".join(parts))
    print(f"wrote {HOLE_OUT}")


METER_OUT = Path(__file__).with_name("multimeter-test.svg")


def meter_panel(x0, pressed):
    """One key tested with the multimeter: red stick on the clean pin, black on the band leg."""
    p = [label(x0 + 20, 90, "KEY PRESSED → number" if pressed else "KEY RELEASED → nothing", 20,
               "#080" if pressed else "#a00")]
    # multimeter body + screen
    mx, my = x0 + 30, 120
    p += [f'<rect x="{mx}" y="{my}" width="150" height="220" rx="14" fill="#f2c200" stroke="#8a6a00" stroke-width="2"/>',
          f'<rect x="{mx+15}" y="{my+15}" width="120" height="55" rx="4" fill="#cfe3c9" stroke="#333"/>',
          f'<text x="{mx+75}" y="{my+55}" text-anchor="middle" font-size="30" font-family="Courier" font-weight="bold">'
          f'{"0.700" if pressed else "OL"}</text>',
          f'<circle cx="{mx+75}" cy="{my+125}" r="30" fill="#333"/>',
          label(mx + 75, my + 130, "•)))", 14, "#fff", "middle"),
          label(mx + 75, my + 175, "multimeter", 13, "#333", "middle"),
          label(mx + 75, my + 195, "(own battery)", 11, "#333", "middle"),
          f'<circle cx="{mx+45}" cy="{my+212}" r="6" fill="#111"/>', f'<circle cx="{mx+105}" cy="{my+212}" r="6" fill="#d00"/>']
    # the key (seen from below): switch, clean pin, diode pin, diode, band leg
    kx, ky = x0 + 330, 200
    pin1, pin2 = (kx - 35, ky - 20), (kx + 35, ky - 20)
    band = (kx + 35, ky + 120)
    p += [f'<rect x="{kx-80}" y="{ky-70}" width="160" height="130" rx="12" fill="#efe6fb" stroke="#7a5aa6" stroke-width="2"/>',
          label(kx, ky + 45, "key a", 15, "#4b3470", "middle"),
          f'<rect x="{pin1[0]-4}" y="{pin1[1]-10}" width="8" height="20" fill="#b87333"/>',
          f'<rect x="{pin2[0]-4}" y="{pin2[1]-10}" width="8" height="20" fill="#b87333"/>',
          label(pin1[0], pin1[1] - 18, "clean pin", 11, "#333", "middle"),
          label(pin2[0] + 6, pin2[1] - 18, "diode pin", 11, "#333", "middle")]
    # switch contact inside: closed when pressed, open gap when released
    if pressed:
        p.append(line(pin1[0], pin1[1] + 12, pin2[0], pin2[1] + 12, "#333", 3))
    else:
        p += [line(pin1[0], pin1[1] + 12, kx - 8, pin1[1] + 2, "#333", 3),
              line(kx + 8, pin2[1] + 12, pin2[0], pin2[1] + 12, "#333", 3),
              label(kx, pin1[1] + 32, "open", 11, "#a00", "middle")]
    p += big_diode(pin2[0], pin2[1], band[1])
    p += [line(band[0], band[1], band[0] + 140, band[1], "#999", 4),
          label(band[0] + 45, band[1] - 8, "row (bare legs)", 12, "#555")]
    # sticks: red to clean pin, black to the band leg
    p += [f'<path d="M{mx+105},{my+212} C{mx+230},{my+300} {pin1[0]-120},{pin1[1]-60} {pin1[0]},{pin1[1]}" fill="none" stroke="#d00" stroke-width="5"/>',
          f'<path d="M{mx+45},{my+212} C{mx+80},{my+360} {band[0]-60},{band[1]+80} {band[0]+60},{band[1]}" fill="none" stroke="#111" stroke-width="5"/>',
          dot(*pin1), dot(band[0] + 60, band[1]), dot(*pin2), dot(*band),
          label(pin1[0] - 70, pin1[1] - 45, "RED stick", 13, "#d00"),
          label(band[0] + 70, band[1] + 28, "BLACK stick", 13, "#111")]
    if pressed:  # current path
        path = [pin1, (pin1[0], pin1[1] + 12), (pin2[0], pin2[1] + 12), band, (band[0] + 60, band[1])]
        p.append(f'<polyline points="{" ".join(f"{x},{y}" for x, y in path)}" fill="none" stroke="#0a0" '
                 f'stroke-width="6" stroke-dasharray="10 6" opacity="0.8"/>')
        p.append(label(x0 + 20, 400, "Tiny current from the meter: red → clean pin → switch → diode → black. Path complete.", 13, "#080"))
    else:
        p.append(label(x0 + 20, 400, "Switch open: the path is broken, nothing gets through, the screen shows OL / 1.", 13, "#a00"))
    return p


def multimeter_svg():
    """How the multimeter tests one key without the controller."""
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="440" font-family="Helvetica">',
             '<rect width="100%" height="100%" fill="white"/>',
             label(20, 36, "Testing one key with the multimeter (no USB, no controller needed)", 22, "#000"),
             label(20, 60, "Dial on •))) . The meter's own battery sends a tiny current out of the RED stick and checks if it comes back to BLACK.", 14)]
    parts += meter_panel(0, True) + meter_panel(580, False)
    parts.append(f'<line x1="575" y1="75" x2="575" y2="420" stroke="#ccc" stroke-width="2"/>')
    parts.append("</svg>")
    METER_OUT.write_text("\n".join(parts))
    print(f"wrote {METER_OUT}")


# check_pin_maps - prevents publishing a diagram whose GPIOs disagree with either half's firmware.
def check_pin_maps():
    assert len(ROW_HOLES) == 4 and len(COL_HOLES) == 6
    assert len(set(ROW_HOLES + COL_HOLES)) == 10
    assert not TRACKBALL.intersection(ROW_HOLES + COL_HOLES)
    silk = {21: "031", 20: "029", 19: "002", 18: "115", 2: "017", 3: "020",
            4: "022", 5: "024", 6: "100", 8: "104", 9: "106"}  # nice_nano/arduino_pro_micro_pins.dtsi
    shield = Path(__file__).parent / "boards/shields/cosmos"
    for filename, prop, expected in (("cosmos.dtsi", "row-gpios", ROW_HOLES),
                                     ("cosmos_left.overlay", "col-gpios", COL_HOLES),
                                     ("cosmos_right.overlay", "col-gpios", COL_HOLES)):
        text = (shield / filename).read_text()
        body = re.search(rf"\b{prop}\s*=\s*(.*?);", text, re.S)
        assert body, f"Missing {prop} in {filename}"
        aliases = re.findall(r"<&pro_micro\s+(\d+)\s", body[1])
        assert [silk[int(pin)] for pin in aliases] == expected, f"Diagram/firmware mismatch: {filename}"
    right = (shield / "cosmos_right.overlay").read_text()
    chip_select = re.search(r"\bcs-gpios\s*=\s*<&gpio(\d+)\s+(\d+)\s+GPIO_ACTIVE_LOW>", right)
    assert chip_select, "Missing active-low SPI chip select"
    ncs = f"{chip_select[1]}{int(chip_select[2]):02d}"
    assert ncs == next(h for name, h, _ in TRACKBALL_WIRES if name == "NCS") and ncs in TRACKBALL
    assert 'diode-direction = "col2row";' in (shield / "cosmos.dtsi").read_text()
    keys = load_keys()
    assert len(keys) == len({(key["side"], *key["rc"]) for key in keys}) == 41
    print(f"PASS: both firmware pin maps match the diagram; 4 rows, 6 column slots, 41 keys; trackball NCS={ncs}, no GPIO collisions.")


# main - validates the pin assignments and regenerates the existing wiring pictures.
def main():
    check_pin_maps()
    multimeter_svg()
    through_hole_svg()
    diode_chain_svg()
    soldering_svg()
    keys = load_keys()
    width = math.ceil(max(k["cx"] for k in keys) + 80)
    height = math.ceil(max(k["cy"] for k in keys) + 160)
    single, single_h = single_key_panel(height)
    detail, detail_h = detail_panel(height + single_h)
    full, full_h = full_panel(height + single_h + detail_h)
    flipped, flipped_h = full_panel(height + single_h + detail_h + full_h, mirror=True)
    legs_view, legs_h = full_panel(height + single_h + detail_h + full_h + flipped_h, mirror=True, legs=True)
    detail_h += single_h + full_h + flipped_h + legs_h
    detail = single + detail + full + flipped + legs_view
    width = max(width, math.ceil(40 + 16 * S + 40))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" font-family="Helvetica">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="40" y="35" font-size="20" font-weight="bold">Cosmos wiring map (top view)</text>',
        '<text x="40" y="58" font-size="13"><tspan fill="#1e6fd9">blue = rows</tspan> · '
        '<tspan fill="#c99a00">yellow = columns</tspan> · diode band → row · same holes on both halves</text>',
    ]
    parts += wires(keys, 1, "#f2c200", 9)  # columns under rows
    parts += wires(keys, 0, "#1e6fd9", 4)
    parts += [key_svg(k) for k in keys]
    legend = "   ".join(f"R{i}={h}" for i, h in enumerate(ROW_HOLES)) + "      " + \
        "   ".join(f"C{i}={h}" for i, h in enumerate(COL_HOLES))
    parts.append(f'<text x="40" y="{height - 40}" font-size="14">Controller holes: {legend}</text>')
    parts.append(f'<text x="40" y="{height - 18}" font-size="12" fill="#666">'
                 'Right half trackball: SCLK 008, SDIO 011, NCS 104, MOTION 006, plus VCC + GND. Positions from cosmos-41.kls.json '
                 '(2D layout, not the curved case).</text>')
    parts += detail
    parts.append("</svg>")
    parts[0] = parts[0].replace(f'height="{height}"', f'height="{height + detail_h}"')
    OUT.write_text("\n".join(parts))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
