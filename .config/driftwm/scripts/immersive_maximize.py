#!/usr/bin/env python3
"""Immersive maximize — promote a maximized window to real fullscreen.

`fit-window` (mod+m) resizes a window to the usable area minus snap gap,
centers it, and resets zoom to 1. This daemon watches the IPC event stream for a
fit window sitting centered at zoom 1 and turns it into actual fullscreen, so a
maximize loses the gap, the decorations and the wallpaper behind them.

The trigger is the state, not the action, so anything that lands a window there
fires it: fit-window, the titlebar maximize button, or centering onto an already
fit window with center-nearest / center-window at zoom 1. Those centering actions
raise and focus their target, so watching the focused window is enough.

Needs a compositor that reports `WindowInfo.mode` — without it every window reads
as Normal and nothing is ever promoted. `mode` is also what separates fit from
fill: `fill-window` on a lone window grows it to the same box fit produces, so
the two are indistinguishable by geometry alone.

mod+m still works from fullscreen: the dispatch exits fullscreen for any action
outside its allowlist, so fit-window then unfits and the window goes back to its
pre-fit size. mod+f is the awkward one — it drops the window out while it is
still fit, which the next event would grab again. A window we fullscreened is
held back once dropped out, so mod+f lands on a plain windowed maximize;
navigating away and centering onto it again is a fresh trigger.
"""

import fcntl
import json
import os
import signal
import subprocess
import sys
import time

ZOOM_EPS = 0.01
CENTER_TOL = 2.0   # promote only when precisely centered
AWAY_TOL = 100.0   # release a hold only on an unambiguous move away
CONFIRM_TIMEOUT = 2.0
RECONNECT_DELAY = 1.0


def center_offset(win, out):
    """How far the window's frame center sits from the viewport center."""
    cam_x, cam_y = out["camera"]
    win_x, win_y = win["position"]
    return max(abs(win_x - cam_x), abs(win_y - cam_y))


def is_fit(win, out):
    return (
        win.get("mode") == "Fit"
        and abs(out["zoom"] - 1.0) <= ZOOM_EPS
        and center_offset(win, out) <= CENTER_TOL
    )


def go_fullscreen():
    subprocess.run(
        ["driftwm", "msg", "action", "toggle-fullscreen"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=2,
        check=False,
    )


class Tracker:
    def __init__(self):
        self.pending = {}   # id -> deadline; toggle sent, fullscreen not seen yet
        self.ours = set()   # windows we put fullscreen
        self.held = set()   # dropped out of fullscreen by hand, still fit
        self.warned = False

    def on_state(self, state):
        windows = state.get("windows", ())
        fullscreen_list = state.get("fullscreen", ())
        fullscreen = {w["id"] for w in fullscreen_list}
        now = time.monotonic()

        if self.pending:
            if fullscreen:
                # Adopt whatever the toggle actually hit: it targets the window
                # focused at dispatch, which focus_follows_mouse may have moved
                # since the snapshot we decided on.
                self.ours |= fullscreen
                self.pending.clear()
            else:
                # A toggle that never lands expires, so a window that cannot go
                # fullscreen retries instead of wedging the daemon.
                for wid, deadline in list(self.pending.items()):
                    if deadline < now:
                        del self.pending[wid]

        self.held |= self.ours - fullscreen
        self.ours &= fullscreen
        self.held &= (
            {w["id"] for w in windows}
            | fullscreen
            | {w["id"] for w in state.get("pinned", ())}
        )

        # A second toggle while one is in flight would land on an output that is
        # already fullscreen and undo the first.
        if self.pending:
            return

        out = next((o for o in state.get("outputs", ()) if o["active"]), None)
        if out is None:
            return
        # Fullscreen on another monitor is no reason to skip this one.
        if any(w["output"] == out["name"] for w in fullscreen_list):
            return
        win = next((w for w in windows if w["is_focused"]), None)
        if win is None or win["is_widget"] or win["suspended"]:
            return

        if "mode" not in win and not self.warned:
            self.warned = True
            print(
                "immersive_maximize: compositor reports no window mode — "
                "restart driftwm to pick up a build that does",
                file=sys.stderr,
            )

        if is_fit(win, out):
            if win["id"] not in self.held:
                self.pending[win["id"]] = now + CONFIRM_TIMEOUT
                go_fullscreen()
        elif win.get("mode") != "Fit" or center_offset(win, out) > AWAY_TOL:
            # Anything nearer than that is the window's own configure settling —
            # one leaving fullscreen reports its old size until the client acks,
            # which shifts the reported center by half the delta. That must not
            # read as the user having navigated away.
            self.held.discard(win["id"])


def main():
    # Default SIGTERM death skips the finally below, orphaning the subscriber,
    # which then holds a connection the compositor keeps broadcasting to.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    runtime = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
    # Two daemons would each answer the same fit, toggling fullscreen twice.
    lock = open(os.path.join(runtime, "drift-immersive-maximize.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return

    while True:
        # Window ids do not survive a compositor restart, so state starts fresh.
        tracker = Tracker()
        try:
            proc = subprocess.Popen(
                ["driftwm", "msg", "subscribe", "--json"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
        except OSError:
            time.sleep(RECONNECT_DELAY)
            continue
        # readline, not iteration: iterating a pipe reads ahead and would sit on
        # events until the buffer fills.
        try:
            for line in iter(proc.stdout.readline, ""):
                try:
                    event = json.loads(line)
                    if isinstance(event, dict) and "State" in event:
                        tracker.on_state(event["State"])
                except Exception:
                    # One malformed or unexpected snapshot must not end the
                    # session — stderr is inherited, so it is still visible.
                    continue
        finally:
            proc.stdout.close()
            proc.terminate()
            proc.wait()
        time.sleep(RECONNECT_DELAY)


if __name__ == "__main__":
    main()
