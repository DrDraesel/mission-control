"""LabFlow → Circolo mirror display driver.

Puts a LabFlow page on the Circolo mirror (Dongmi "w400", 1080x1920 portrait)
through its own exported BrowserActivity, tunnels the lab PC's LabFlow port to
the device with ``adb reverse`` (no Wi-Fi routing needed), and keeps the page in
front if the Circolo kiosk app reclaims the screen.

Usage
  python -m labflow.mirror_display                # watch + keep in front
  python -m labflow.mirror_display --once         # push it once and exit
  python -m labflow.mirror_display --url /mirror  # different LabFlow page
  python -m labflow.mirror_display --no-watch     # push once, then idle

The display is read-only: /mirror only GETs the LabFlow JSON API, so nothing on
the mirror can advance or close a patient's step.
"""

from __future__ import annotations

import argparse
import http.client
import os
import pathlib
import subprocess
import sys
import time

DEFAULT_IP = "192.168.1.110"          # DHCP on lab Wi-Fi "IMW" — verify each run
DEFAULT_PORT = 8790                   # LabFlow
DEFAULT_PAGE = "/mirror"
ADB_APK_ACTIVITY = "ai.dongmi.barbell/.ui.sys.BrowserActivity"
SERIAL_SUFFIX = ":5555"


def _adb_path() -> str:
    """adb from platform-tools (skill install location), else PATH."""
    home = pathlib.Path(os.path.expanduser("~"))
    for name in ("adb.exe", "adb"):
        candidate = home / "platform-tools" / name
        if candidate.exists():
            return str(candidate)
    return "adb"  # rely on PATH


def _run(args: list[str], timeout: float = 20.0) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            args, capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
    except (OSError, subprocess.SubprocessError):
        # adb missing or hung: report as a failed command so the caller's
        # readiness checks fail closed instead of raising a traceback.
        return subprocess.CompletedProcess(args, 1, "", "adb unavailable")


def _labflow_up(host: str, port: int) -> bool:
    conn = None
    try:
        conn = http.client.HTTPConnection(host, port, timeout=3)
        conn.request("GET", "/api/patients")
        response = conn.getresponse()
        response.read(2048)
        return response.status == 200
    except (OSError, http.client.HTTPException):
        return False
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:  # noqa: BLE001 — best effort close
                pass


def connect(adb: str, ip: str) -> bool:
    serial = ip + SERIAL_SUFFIX
    _run([adb, "connect", serial])
    listing = _run([adb, "devices"]).stdout or ""
    for line in listing.splitlines():
        if line.startswith(serial) and "device" in line and "offline" not in line:
            return True
    return False


def is_mirror(adb: str, ip: str) -> bool:
    """Refuse to drive a look-alike Android box (MSI F7R etc.)."""
    out = _run([adb, "-s", ip + SERIAL_SUFFIX, "shell", "getprop ro.product.model"]).stdout
    return out.strip() == "w400"


def push_reverse(adb: str, ip: str, port: int) -> None:
    _run([adb, "-s", ip + SERIAL_SUFFIX, "reverse", f"tcp:{port}", f"tcp:{port}"])


def launch(adb: str, ip: str, url: str) -> None:
    # Unique fragment per launch: the kiosk's BrowserActivity reuses its
    # WebView when the intent data is byte-identical, which would leave a
    # stale page (e.g. an old port) on screen.
    _run([
        adb, "-s", ip + SERIAL_SUFFIX, "shell",
        "am", "start",
        "-a", "android.intent.action.VIEW",
        "-d", f"{url}#{int(time.time())}",
        "-n", ADB_APK_ACTIVITY,
    ])


def foreground_is_browser(adb: str, ip: str) -> bool:
    out = _run([adb, "-s", ip + SERIAL_SUFFIX, "shell",
                "dumpsys activity activities"], timeout=25).stdout or ""
    for line in out.splitlines():
        if "mResumedActivity" in line:
            return "BrowserActivity" in line
    return False


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Show a LabFlow page on the Circolo mirror.")
    parser.add_argument("--ip", default=os.environ.get("CIRCOLO_IP", DEFAULT_IP))
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--page", default=DEFAULT_PAGE, help="LabFlow path, e.g. /mirror")
    parser.add_argument("--patient", default=None, help="pin one patient id")
    parser.add_argument("--interval", type=float, default=20.0, help="keep-alive poll seconds")
    parser.add_argument("--once", action="store_true", help="push once and exit")
    parser.add_argument("--no-watch", action="store_true", help="push once, no exit needed")
    args = parser.parse_args(argv)

    adb = _adb_path()
    url = f"http://127.0.0.1:{args.port}{args.page}"
    if args.patient:
        sep = "&" if "?" in url else "?"
        url += f"{sep}patient={args.patient}"

    if not _labflow_up("127.0.0.1", args.port):
        print(f"[!] LabFlow is not answering on http://127.0.0.1:{args.port} — start it first "
              f"(Start LabFlow.cmd).", file=sys.stderr)
        return 2

    if not connect(adb, args.ip):
        print(f"[!] No adb device at {args.ip}{SERIAL_SUFFIX}. The mirror's IP is DHCP — "
              f"run `adb connect <ip>:5555` and pass --ip.", file=sys.stderr)
        return 3
    if not is_mirror(adb, args.ip):
        print(f"[!] {args.ip} is not the Circolo mirror (ro.product.model != w400).", file=sys.stderr)
        return 4

    push_reverse(adb, args.ip, args.port)
    launch(adb, args.ip, url)
    print(f"[ok] {url} -> {args.ip} ({ADB_APK_ACTIVITY})")

    if args.once or args.no_watch:
        return 0

    print(f"[..] keeping it in front every {args.interval:g}s — Ctrl+C to stop")
    try:
        while True:
            time.sleep(max(5.0, args.interval))
            if not connect(adb, args.ip):
                print("[!] mirror dropped off adb — retrying")
                continue
            push_reverse(adb, args.ip, args.port)
            if not foreground_is_browser(adb, args.ip):
                print("[..] kiosk app took the screen — re-launching the display")
                launch(adb, args.ip, url)
    except KeyboardInterrupt:
        print("\n[ok] stopped (the page stays on the mirror)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
