# @steered SNARE-1 2026-09-12
"""
xbox_detect.py - layered probe for Xbox controller input.

Run this FIRST when the Xbox pad does not work. It walks up the stack and
prints what it finds at each layer, so the failure point is obvious:

    1. Environment  - python, pygame version, 'input' group membership
    2. OS devices   - /dev/input/js*, event*, by-id symlinks
    3. Bluetooth    - paired / connected pads via bluetoothctl
    4. pygame       - how many pads SDL sees, names, axis/button/hat counts
    5. Live dump    - press buttons and watch indices appear

Every stage is independent and non-fatal: a stage that fails prints why and
the probe keeps going, so one run tells you everything.

Usage:
    python3 components/sensors/xbox_detect.py              # all stages, 20s dump
    python3 components/sensors/xbox_detect.py --seconds 60 # longer dump
    python3 components/sensors/xbox_detect.py --no-dump    # stages 1-4 only

Nothing here writes to the robot or moves a servo - it is read-only.
"""

import argparse
import glob
import os
import platform
import subprocess
import sys
import time

# Headless robot: SDL must not try to open a window. Must be set before pygame
# is imported. Same as components/sensors/xbox_control.py.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

XBOX_NAME_HINTS = ("xbox", "x-box", "xinput", "microsoft")

# Reference layout xbox_control.py assumes, printed so you can compare against
# what the live dump actually reports.
EXPECTED_BUTTONS = {
    0: "A", 1: "B", 2: "X", 3: "Y",
    4: "LB", 5: "RB", 6: "Back", 7: "Start", 8: "Guide",
    9: "LStick click", 10: "RStick click",
}
EXPECTED_AXES = {
    0: "Left stick X", 1: "Left stick Y", 2: "LT",
    3: "Right stick X", 4: "Right stick Y", 5: "RT",
}


def hr(title):
    print("\n" + "=" * 68)
    print(title)
    print("=" * 68)


def ok(msg):
    print(f"  [OK]   {msg}")


def bad(msg):
    print(f"  [FAIL] {msg}")


def warn(msg):
    print(f"  [WARN] {msg}")


def info(msg):
    print(f"         {msg}")


def run(cmd, timeout=5):
    """Run a command, returning (ok, output). Never raises."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout or r.stderr).strip()
    except FileNotFoundError:
        return False, f"{cmd[0]}: not installed"
    except subprocess.TimeoutExpired:
        return False, f"{cmd[0]}: timed out"
    except Exception as e:
        return False, f"{cmd[0]}: {e}"


# ---------------------------------------------------------------- stage 1

def stage_environment():
    hr("STAGE 1: Environment")
    info(f"python   : {sys.version.split()[0]}")
    info(f"platform : {platform.system()} {platform.release()} ({platform.machine()})")
    info(f"user     : {os.environ.get('USER', '?')} (uid {os.getuid()})")
    info(f"SDL_VIDEODRIVER: {os.environ.get('SDL_VIDEODRIVER')}")

    # Reading joysticks on Linux needs membership of the 'input' group (or root).
    # Irrelevant off Linux, so do not raise a false alarm when testing on a Mac.
    if platform.system() == "Linux":
        try:
            import grp
            groups = [grp.getgrgid(g).gr_name for g in os.getgroups()]
            info(f"groups   : {', '.join(sorted(groups))}")
            if os.getuid() == 0:
                ok("running as root, device permissions not an issue")
            elif "input" in groups:
                ok("user is in the 'input' group")
            else:
                bad("user is NOT in the 'input' group - SDL may not read the pad")
                info("fix: sudo usermod -aG input $USER   (then log out and back in)")
        except Exception as e:
            warn(f"could not read groups: {e}")
    else:
        info("(not Linux - skipping 'input' group and /dev/input checks)")

    try:
        import pygame
        ver = pygame.version.ver
        info(f"pygame   : {ver} (SDL {getattr(pygame.version, 'SDL', '?')})")
        if int(str(ver).split(".")[0]) < 2:
            bad(f"pygame {ver} is too old - xbox_control.py needs pygame 2.x")
            info("pygame 1.x has no JOYDEVICEREMOVED event and poor Xbox support.")
            info("fix: pip3 install --upgrade 'pygame>=2.0'")
        else:
            ok("pygame 2.x present")
        return pygame
    except ImportError as e:
        bad(f"pygame not importable: {e}")
        info("fix: pip3 install pygame")
        return None


# ---------------------------------------------------------------- stage 2

def stage_devices():
    hr("STAGE 2: OS input devices")

    if platform.system() != "Linux":
        info(f"skipped - {platform.system()} has no /dev/input (Linux/Pi only)")
        return

    js = sorted(glob.glob("/dev/input/js*"))
    ev = sorted(glob.glob("/dev/input/event*"))

    if js:
        ok(f"joystick devices: {', '.join(js)}")
        for d in js:
            readable = os.access(d, os.R_OK)
            (ok if readable else bad)(f"{d} readable: {readable}")
    else:
        bad("no /dev/input/js* devices - the kernel does not see a pad")
        info("wired Xbox pads need the 'xpad' driver; Xbox One/Series")
        info("Bluetooth pads often need 'xone' or 'xpadneo' installed.")

    info(f"event devices: {len(ev)} found")

    by_id = sorted(glob.glob("/dev/input/by-id/*"))
    if by_id:
        info("by-id symlinks:")
        for d in by_id:
            info(f"  {os.path.basename(d)}")

    # Kernel's own view of the device names.
    try:
        with open("/proc/bus/input/devices") as f:
            text = f.read()
        names = [ln.split('"')[1] for ln in text.splitlines()
                 if ln.startswith("N: Name=") and '"' in ln]
        if names:
            info("kernel input device names:")
            for n in names:
                marker = " <-- looks like an Xbox pad" if any(
                    h in n.lower() for h in XBOX_NAME_HINTS) else ""
                info(f"  {n}{marker}")
    except Exception as e:
        info(f"(could not read /proc/bus/input/devices: {e})")

    # jstest is the ground truth for whether the kernel is delivering events.
    found, out = run(["which", "jstest"])
    if found:
        info(f"jstest available at {out} - try: jstest --normal /dev/input/js0")
    else:
        info("jstest not installed (optional): sudo apt-get install joystick")


# ---------------------------------------------------------------- stage 3

def stage_bluetooth():
    hr("STAGE 3: Bluetooth")

    found, out = run(["bluetoothctl", "devices"])
    if not found:
        warn(f"bluetoothctl unavailable: {out}")
        info("(fine if the pad is plugged in over USB)")
        return

    lines = [ln for ln in out.splitlines() if ln.strip()]
    if not lines:
        warn("no paired Bluetooth devices at all")
        return

    info("paired devices:")
    candidates = []
    for ln in lines:
        info(f"  {ln}")
        parts = ln.split(None, 2)
        name = parts[2] if len(parts) > 2 else ""
        if any(h in name.lower() for h in XBOX_NAME_HINTS):
            candidates.append((parts[1], name))

    if not candidates:
        bad("no paired device looks like an Xbox pad")
        info("pair it: bluetoothctl -> scan on -> pair <MAC> -> trust <MAC> -> connect <MAC>")
        return

    for mac, name in candidates:
        found, detail = run(["bluetoothctl", "info", mac])
        connected = "Connected: yes" in detail
        (ok if connected else bad)(f"{name} ({mac}) connected: {connected}")
        if not connected:
            info(f"fix: bluetoothctl connect {mac}")


# ---------------------------------------------------------------- stage 4

def stage_pygame(pygame):
    hr("STAGE 4: pygame / SDL enumeration")

    if pygame is None:
        bad("skipped - pygame not importable")
        return None

    try:
        pygame.init()
        pygame.joystick.init()
    except Exception as e:
        bad(f"pygame init failed: {e}")
        return None

    count = pygame.joystick.get_count()
    if count == 0:
        bad("SDL sees 0 joysticks")
        info("If stage 2 found /dev/input/js0, this is a permissions or SDL")
        info("problem rather than a driver one - check the 'input' group above.")
        return None

    ok(f"SDL sees {count} joystick(s)")

    chosen = None
    for i in range(count):
        joy = pygame.joystick.Joystick(i)
        joy.init()
        name = joy.get_name()
        looks_xbox = any(h in name.lower() for h in XBOX_NAME_HINTS)
        print(f"\n  [{i}] {name}{'  <-- Xbox-style' if looks_xbox else ''}")
        info(f"axes={joy.get_numaxes()} buttons={joy.get_numbuttons()} "
             f"hats={joy.get_numhats()}")
        try:
            info(f"guid={joy.get_guid()}")
        except Exception:
            pass

        if joy.get_numaxes() < 6:
            warn(f"only {joy.get_numaxes()} axes - xbox_control.py expects 6 "
                 "(triggers are axes 2 and 5)")
        if joy.get_numbuttons() < 9:
            warn(f"only {joy.get_numbuttons()} buttons - Guide button (index 8) "
                 "will not work as quit")
        if joy.get_numhats() == 0:
            warn("no hat - the D-pad may be reported as axes or buttons instead, "
                 "so movement will not work")

        if chosen is None and looks_xbox:
            chosen = joy

    if chosen is None:
        if count == 1:
            warn("no pad matched the Xbox name hints; xbox_control.py would fall "
                 "back to index 0 anyway")
            chosen = pygame.joystick.Joystick(0)
            chosen.init()
        else:
            bad("multiple pads and none look like an Xbox - xbox_control.py will "
                "refuse to pick one")
            info(f"name hints it looks for: {XBOX_NAME_HINTS}")

    return chosen


# ---------------------------------------------------------------- stage 5

def stage_live_dump(pygame, joy, seconds):
    hr(f"STAGE 5: Live input dump ({seconds}s)")

    if joy is None:
        bad("skipped - no usable joystick")
        return

    print("  Press every button and move both sticks and triggers.")
    print("  Nothing printed = the pad is connected but sending no events.\n")
    print("  Layout xbox_control.py assumes:")
    for i, n in sorted(EXPECTED_BUTTONS.items()):
        info(f"  button {i:>2} = {n}")
    for i, n in sorted(EXPECTED_AXES.items()):
        info(f"  axis   {i:>2} = {n}")
    print()

    n_axes, n_btns, n_hats = joy.get_numaxes(), joy.get_numbuttons(), joy.get_numhats()

    # Baseline so resting triggers (which sit at -1.0) do not spam.
    pygame.event.pump()
    last_axes = [joy.get_axis(i) for i in range(n_axes)]
    last_btns = [joy.get_button(i) for i in range(n_btns)]
    last_hats = [joy.get_hat(i) for i in range(n_hats)]

    events = 0
    started = time.time()
    try:
        while time.time() - started < seconds:
            pygame.event.pump()
            for e in pygame.event.get():
                if e.type == getattr(pygame, "JOYDEVICEREMOVED", -1):
                    bad("JOYDEVICEREMOVED - the pad disconnected mid-run")
                    return

            for i in range(n_btns):
                v = joy.get_button(i)
                if v != last_btns[i]:
                    last_btns[i] = v
                    if v:
                        label = EXPECTED_BUTTONS.get(i, "unmapped")
                        print(f"  button {i:>2} PRESSED   (expected: {label})")
                        events += 1

            for i in range(n_hats):
                v = joy.get_hat(i)
                if v != last_hats[i]:
                    last_hats[i] = v
                    print(f"  hat    {i:>2} = {v}   (D-pad)")
                    events += 1

            for i in range(n_axes):
                v = joy.get_axis(i)
                if abs(v - last_axes[i]) > 0.15:
                    last_axes[i] = v
                    label = EXPECTED_AXES.get(i, "unmapped")
                    print(f"  axis   {i:>2} = {v:+.3f}   (expected: {label})")
                    events += 1

            time.sleep(0.02)
    except KeyboardInterrupt:
        print("\n  (interrupted)")

    print()
    if events:
        ok(f"{events} input event(s) seen - the pad works at the pygame layer")
        info("If keyboard_control.py still does nothing, the problem is the")
        info("mapping in xbox_control.py, not detection. Compare the indices")
        info("above against the expected layout and edit BUTTONS / AXES.")
    else:
        bad("no input events seen")
        info("The pad is enumerated but silent. Usual causes: it went to sleep")
        info("(press the Guide button), it is paired but not connected, or the")
        info("driver is bound but not delivering (try jstest to confirm).")


def main():
    p = argparse.ArgumentParser(
        description="Layered probe for Xbox controller detection on PiCrawler")
    p.add_argument("--seconds", type=int, default=20,
                   help="how long to watch for live input (default 20)")
    p.add_argument("--no-dump", action="store_true",
                   help="run stages 1-4 only, skip the live input dump")
    args = p.parse_args()

    hr("PiCrawler Xbox controller probe")
    print("Read-only: nothing is written and no servo moves.")

    pygame = stage_environment()
    stage_devices()
    stage_bluetooth()
    joy = stage_pygame(pygame)

    if args.no_dump:
        hr("Skipping live dump (--no-dump)")
    else:
        stage_live_dump(pygame, joy, args.seconds)

    hr("Probe complete")
    print("Paste this whole output when reporting what happened.")

    if pygame is not None:
        try:
            pygame.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
