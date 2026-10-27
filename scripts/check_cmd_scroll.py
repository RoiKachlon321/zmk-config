"""Refuse firmware whose Cmd-mask listener runs after the HID key handler."""
import subprocess
import sys


# check_order - validates the actual linked subscription addresses, not source order.
def check_order(nm, elf):
    symbols = {}
    for line in subprocess.check_output([nm, elf], text=True).splitlines():
        fields = line.split()
        if len(fields) == 3:
            symbols[fields[2]] = int(fields[0], 16)
    first = symbols["zmk_event_sub_cmd_scrollzmk_keycode_state_changed"]
    hid = symbols["zmk_event_sub_hid_listenerzmk_keycode_state_changed"]
    if first >= hid:
        raise SystemExit("Unsafe listener order: Cmd restoration must run BEFORE HID")
    print("Verified: Cmd-scroll key listener runs before HID")


if __name__ == "__main__":
    check_order(*sys.argv[1:])
