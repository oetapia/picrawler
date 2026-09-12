# @steered SNARE-1 2026-09-12
"""
Xbox controller input for PiCrawler.

This is a drop-in replacement for components/sensors/ps4_control.py. It speaks
the *same* callback protocol, so manual_control/scripts/keyboard_control.py
(and anything else built on the PS4 path) works unchanged:

    controller = xbox_control.MyController(on_input_change=handle_input)
    controller.listen()

The PS4 path uses pyPS4Controller, which reads /dev/input/js0 and dispatches
named events. Xbox pads (wired or Bluetooth, via xpad/xone) are read here with
pygame's joystick module instead, and the polled state is translated back into
the PS4 action strings that handle_input() already understands.

Button map (Xbox physical -> PS4 action string emitted):
    A                -> 'x_press'          (both are the bottom face button)
    B                -> 'circle_press'     (both are the right face button)
    X                -> 'square_press'     (both are the left face button)
    Y                -> 'triangle_press'   (both are the top face button)
    LB / RB          -> 'L1_press' / 'R1_press'
    LT / RT          -> 'L2_press' / 'R2_press' (with pressure value)
    Left stick click -> 'L3_press'
    Right stick "    -> 'R3_press'
    Xbox (Guide)     -> 'ps_button_press'  (quits, same as the PS button)
    D-pad            -> 'on_up_arrow_press' / 'on_down_arrow_press' /
                        'on_left_arrow_press' / 'on_right_arrow_press'
    Right stick      -> 'R3_updown' / 'R3_leftright' (pose interpolation)
    Left stick       -> 'L3_left' / 'L3_right' / 'L3_up' / 'L3_down'

Axis values are rescaled to the PS4 range (-32767..32767) so the maths in
keyboard_control.py (JOYSTICK_MAX, DEADZONE, adjust_speed) needs no changes.

Standalone test:
    python3 components/sensors/xbox_control.py
"""

import os
import time

# The robot runs headless, so SDL must not try to open a window. Set before
# pygame is imported/initialised.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

# PS4 analog full-scale, used by keyboard_control.py's JOYSTICK_MAX.
PS4_AXIS_MAX = 32767

# Names that identify an Xbox-style pad. xpad reports "Xbox Wireless
# Controller", "Microsoft X-Box One pad", 8BitDo clones report "Xinput", etc.
XBOX_NAME_HINTS = ("xbox", "x-box", "xinput", "microsoft")

# SDL2 button indices for the xpad/xone drivers (same layout picar's
# client/controller.py relies on).
BUTTONS = {
    "a": 0,
    "b": 1,
    "x": 2,
    "y": 3,
    "lb": 4,
    "rb": 5,
    "back": 6,
    "start": 7,
    "guide": 8,
    "ls": 9,
    "rs": 10,
}

# SDL2 axis indices. Triggers rest at -1.0 and read +1.0 fully depressed.
AXES = {
    "lx": 0,
    "ly": 1,
    "lt": 2,
    "rx": 3,
    "ry": 4,
    "rt": 5,
}

# Xbox button -> PS4 action string. Edge triggered (fires once per press).
BUTTON_ACTIONS = {
    "a": "x_press",
    "b": "circle_press",
    "x": "square_press",
    "y": "triangle_press",
    "lb": "L1_press",
    "rb": "R1_press",
    "ls": "L3_press",
    "rs": "R3_press",
    "guide": "ps_button_press",
}

# D-pad hat (x, y) -> PS4 action string. SDL reports y=+1 for up.
HAT_ACTIONS = {
    (0, 1): "on_up_arrow_press",
    (0, -1): "on_down_arrow_press",
    (-1, 0): "on_left_arrow_press",
    (1, 0): "on_right_arrow_press",
}


def _joystick_names():
    """Return the names of every joystick SDL can currently see."""
    pygame.joystick.quit()
    pygame.joystick.init()
    names = []
    for i in range(pygame.joystick.get_count()):
        joy = pygame.joystick.Joystick(i)
        joy.init()
        names.append(joy.get_name())
        joy.quit()
    return names


def find_xbox_joystick():
    """
    Return the index of the first Xbox-style pad, or None if none is attached.

    Falls back to index 0 when exactly one pad is present but its name is not
    recognised - generic USB pads usually expose the same SDL layout.
    """
    if not pygame.get_init():
        pygame.init()
    pygame.joystick.quit()
    pygame.joystick.init()

    count = pygame.joystick.get_count()
    if count == 0:
        return None

    for i in range(count):
        joy = pygame.joystick.Joystick(i)
        joy.init()
        name = joy.get_name().lower()
        joy.quit()
        if any(hint in name for hint in XBOX_NAME_HINTS):
            return i

    if count == 1:
        return 0

    return None


def is_xbox_controller_connected():
    """True when an Xbox-style pad is available to pygame."""
    return find_xbox_joystick() is not None


class MyController:
    """
    Xbox controller reader with the ps4_control.MyController interface.

    Args:
        on_input_change: callable(action, value=0) - same callback the PS4
            controller uses. `value` is only passed for analog events.
        interface: accepted for signature compatibility with the PS4 class and
            ignored (pygame picks the device itself).
        connecting_using_ds4drv: accepted and ignored, PS4-only concept.
        stick_deadzone: raw PS4-scale deadzone for the analog sticks. Defaults
            to 20000 to match ps4_control.MyController.deadzone; lower it for
            finer pose control.
        poll_interval: seconds between polls of the pad state.
    """

    def __init__(self, on_input_change=None, interface=None,
                 connecting_using_ds4drv=False, stick_deadzone=20000,
                 poll_interval=0.02):
        self.on_input_change = on_input_change
        self.deadzone = stick_deadzone
        self.poll_interval = poll_interval

        if not pygame.get_init():
            pygame.init()

        index = find_xbox_joystick()
        if index is None:
            seen = _joystick_names()
            detail = f" Joysticks seen: {seen}." if seen else ""
            raise ConnectionError(
                "No Xbox controller detected. Pair or plug in the pad "
                "(bluetoothctl for wireless) and try again." + detail
            )

        self.joy = pygame.joystick.Joystick(index)
        self.joy.init()
        self.name = self.joy.get_name()
        print(f"Xbox controller found: {self.name}")

        self._prev_buttons = {}
        self._prev_hat = (0, 0)
        self._stick_at_rest = True
        self._stop = False

    # -- helpers ---------------------------------------------------------

    def _emit(self, action, value=None):
        if callable(self.on_input_change):
            if value is None:
                self.on_input_change(action)
            else:
                self.on_input_change(action, value)

    def _button(self, key):
        index = BUTTONS[key]
        if index >= self.joy.get_numbuttons():
            return 0
        return self.joy.get_button(index)

    def _axis(self, key):
        index = AXES[key]
        if index >= self.joy.get_numaxes():
            return 0.0
        return self.joy.get_axis(index)

    def _hat(self):
        if self.joy.get_numhats() == 0:
            return (0, 0)
        return self.joy.get_hat(0)

    def _to_ps4_scale(self, axis_value):
        """Map a -1.0..1.0 pygame axis onto the PS4 -32767..32767 range."""
        return int(max(-1.0, min(1.0, axis_value)) * PS4_AXIS_MAX)

    def _trigger_to_ps4_scale(self, axis_value):
        """
        Map an SDL trigger (-1.0 released .. 1.0 pressed) onto the PS4 L2/R2
        range (-32767 released .. 32767 pressed) that adjust_speed() expects.
        """
        return self._to_ps4_scale(axis_value)

    # -- polling ---------------------------------------------------------

    def _poll_buttons(self):
        for key, action in BUTTON_ACTIONS.items():
            pressed = self._button(key)
            if pressed and not self._prev_buttons.get(key):
                print(f"{key.upper()} pressed -> {action}")
                self._emit(action)
            self._prev_buttons[key] = pressed

    def _poll_hat(self):
        hat = self._hat()
        if hat == self._prev_hat:
            return
        self._prev_hat = hat
        action = HAT_ACTIONS.get(hat)
        if action:
            print(f"D-pad {hat} -> {action}")
            self._emit(action)

    def _poll_triggers(self):
        # Only forward while the trigger is actually held, mirroring the PS4
        # driver which emits L2/R2 events on press rather than at rest.
        lt = self._axis("lt")
        if lt > -0.9:
            self._emit("L2_press", self._trigger_to_ps4_scale(lt))

        rt = self._axis("rt")
        if rt > -0.9:
            self._emit("R2_press", self._trigger_to_ps4_scale(rt))

    def _poll_right_stick(self):
        """
        Feed the pose interpolator from the right stick.

        Both R3 axes drive the same single-value pose interpolator in
        keyboard_control.handle_joystick_input(), so only the dominant axis is
        forwarded each poll - sending both would make them fight each other.
        Sign is left as pygame reports it (up is negative), which matches
        pyPS4Controller and therefore keeps interpolate_pose() behaviour
        identical.
        """
        rx = self._to_ps4_scale(self._axis("rx"))
        ry = self._to_ps4_scale(self._axis("ry"))

        if abs(ry) <= self.deadzone and abs(rx) <= self.deadzone:
            if not self._stick_at_rest:
                self._stick_at_rest = True
                self._emit("R3_rest")
            return

        self._stick_at_rest = False
        if abs(ry) >= abs(rx):
            self._emit("R3_updown", ry)
        else:
            self._emit("R3_leftright", rx)

    def _poll_left_stick(self):
        lx = self._to_ps4_scale(self._axis("lx"))
        ly = self._to_ps4_scale(self._axis("ly"))

        if abs(lx) > self.deadzone:
            self._emit("L3_right" if lx > 0 else "L3_left", lx)
        if abs(ly) > self.deadzone:
            self._emit("L3_down" if ly > 0 else "L3_up", ly)

    # -- public API ------------------------------------------------------

    def stop(self):
        """Ask listen() to return at the end of the current poll."""
        self._stop = True

    def listen(self, timeout=None):
        """
        Block and dispatch controller input until the pad disconnects, stop()
        is called, or `timeout` seconds elapse.

        `timeout` exists for signature compatibility with pyPS4Controller's
        listen(); None means listen forever.
        """
        self._stop = False
        started = time.time()

        while not self._stop:
            if timeout is not None and time.time() - started > timeout:
                break

            for event in pygame.event.get():
                if event.type == pygame.JOYDEVICEREMOVED:
                    raise ConnectionError("Xbox controller disconnected")

            if not self.joy.get_init():
                raise ConnectionError("Xbox controller disconnected")

            self._poll_buttons()
            self._poll_hat()
            self._poll_triggers()
            self._poll_right_stick()
            self._poll_left_stick()

            time.sleep(self.poll_interval)

    def close(self):
        try:
            self.joy.quit()
        except Exception:
            pass
        pygame.joystick.quit()


if __name__ == "__main__":
    def show(action, value=0):
        print(f"action={action} value={value}")

    controller = MyController(on_input_change=show)
    print("Listening. Press the Xbox (Guide) button or Ctrl^C to stop.")
    try:
        controller.listen()
    except KeyboardInterrupt:
        pass
    finally:
        controller.close()
