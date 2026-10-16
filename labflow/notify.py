"""LabFlow notifiers — Console / Telegram / Null plus the config factory.

Every flow mutation goes out as a notification describing what is done and
what is next.  Telegram is the only outbound call LabFlow makes, and it carries
**no clinical values**: only step/launch/capture *labels* (station names,
descriptions, probe names, field labels) — never intake answers, measurements,
results or any patient data.  All clinical data stays local.

Frozen API
----------
``Notifier`` base interface with

* ``step_started(patient, station, next_station)``
* ``step_completed(patient, station, next_station)``
* ``flow_completed(patient)``
* ``reminder(patient, current_station)``

Implementations: ``ConsoleNotifier`` (default), ``TelegramNotifier``,
``NullNotifier``; factory ``make_notifier(config)``.

Telegram message format (frozen)::

    LabFlow · <patient first name or "Patient"> — <Step Name> DONE

    Next: <name> — <instruction>

Notifier methods never raise: failures are logged to stderr and reported as
``False``.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

__all__ = [
    "Notifier",
    "ConsoleNotifier",
    "TelegramNotifier",
    "NullNotifier",
    "make_notifier",
    "read_token_from_file",
    "patient_label",
    "station_name",
    "station_instruction",
    "format_step_started",
    "format_step_completed",
    "format_flow_completed",
    "format_reminder",
]

_TOKEN_RE = re.compile(
    r"^\s*(?:export\s+)?TELEGRAM_BOT_TOKEN\s*=\s*(.+?)\s*$", re.MULTILINE
)


def _log(message: str) -> None:
    """Best-effort stderr log (notifiers never raise)."""
    try:
        print(f"LABFLOW: {message}", file=sys.stderr, flush=True)
    except Exception:
        pass


def _one_line(text, limit: int = 200) -> str:
    return " ".join(str(text or "").split())[:limit]


def _field(obj, key, default=None):
    """Read ``key`` from a dict-like or attribute-like station/patient."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


# -- message building (pure functions, unit-testable without a network) ----
def patient_label(patient, include_name: bool = True) -> str:
    """First name of the patient, or ``'Patient'`` when unavailable/hidden."""
    if include_name and isinstance(patient, dict):
        name = str(patient.get("name") or "").strip()
        if name:
            return name.split()[0]
    return "Patient"


def station_name(station) -> str:
    """Human name of a station (falls back to id, then 'Step')."""
    return str(_field(station, "name") or _field(station, "id") or "Step")


def launch_hint(station) -> str:
    """Launch hint for a single-line instruction ('' for manual steps)."""
    launch = _field(station, "launch") or {}
    if not isinstance(launch, dict):
        launch = {}
    ltype = str(launch.get("type") or "")
    value = _one_line(launch.get("value") or "", 120)
    if ltype == "url" and value:
        return f"open {value}"
    if ltype == "command" and value:
        return f"run `{value}`"
    return ""


def capture_hint(station) -> str:
    """Capture hint for a single-line instruction."""
    capture = _field(station, "capture") or {}
    if not isinstance(capture, dict):
        capture = {}
    ctype = str(capture.get("type") or "")
    if ctype == "auto":
        probe = _one_line(capture.get("probe") or "", 80)
        return f"auto-capture from '{probe}'" if probe else "auto-capture"
    if ctype == "ref":
        return "external reference"
    if ctype == "manual":
        return "manual entry"
    return ""


def station_instruction(station) -> str:
    """One-line instruction: description + launch hint (+ capture for auto)."""
    parts = []
    description = _one_line(_field(station, "description"))
    if description:
        parts.append(description)
    hint = launch_hint(station)
    if hint:
        parts.append(hint)
    capture = capture_hint(station)
    if capture:
        capture_type = (_field(station, "capture") or {})
        capture_type = capture_type.get("type") if isinstance(capture_type, dict) else None
        if not description or capture_type == "auto":
            parts.append(capture)
    return _one_line(" ".join(parts) or capture or station_name(station), 200)


def format_step_started(patient, station, next_station=None, include_patient_name=True) -> str:
    """Message for ``step_started``."""
    label = patient_label(patient, include_patient_name)
    name = station_name(station)
    title = f"LabFlow · {label} — {name} STARTED"
    body = [f"Now: {name} — {station_instruction(station)}"]
    if next_station is not None:
        body.append(f"Next: {station_name(next_station)} — {station_instruction(next_station)}")
    return title + "\n\n" + "\n".join(body)


def format_step_completed(patient, station, next_station=None, include_patient_name=True) -> str:
    """Message for ``step_completed`` — frozen two-line format."""
    label = patient_label(patient, include_patient_name)
    title = f"LabFlow · {label} — {station_name(station)} DONE"
    if next_station is not None:
        body = f"Next: {station_name(next_station)} — {station_instruction(next_station)}"
    else:
        body = "Next: — all stations complete."
    return f"{title}\n\n{body}"


def format_flow_completed(patient, include_patient_name=True) -> str:
    """Message for ``flow_completed``."""
    label = patient_label(patient, include_patient_name)
    return f"LabFlow · {label} — Flow DONE\n\nAll stations complete."


def format_reminder(patient, station, include_patient_name=True) -> str:
    """Message for ``reminder``."""
    label = patient_label(patient, include_patient_name)
    name = station_name(station)
    return f"LabFlow · {label} — Reminder\n\nCurrent step: {name} — {station_instruction(station)}"


# -- notifier implementations ---------------------------------------------
class Notifier:
    """Notification interface for the flow engine.

    Called on every mutation: ``step_started`` when a station begins,
    ``step_completed`` when it is closed (done *or* skipped) with the next
    station (or None on the last one), ``flow_completed`` when nothing is left,
    ``reminder`` for nudges/redos.  Implementations must never raise.
    """

    kind = "base"

    def step_started(self, patient, station, next_station=None) -> bool:
        """A station just began; ``next_station`` is the one after it."""
        raise NotImplementedError

    def step_completed(self, patient, station, next_station=None) -> bool:
        """A station was closed; ``next_station`` is None when the flow ended."""
        raise NotImplementedError

    def flow_completed(self, patient) -> bool:
        """Every station is closed."""
        raise NotImplementedError

    def reminder(self, patient, current_station=None) -> bool:
        """Nudge about (or re-queue) ``current_station``."""
        raise NotImplementedError


class NullNotifier(Notifier):
    """Silent no-op notifier (engine default when none is supplied)."""

    kind = "null"

    def step_started(self, patient, station, next_station=None) -> bool:
        return True

    def step_completed(self, patient, station, next_station=None) -> bool:
        return True

    def flow_completed(self, patient) -> bool:
        return True

    def reminder(self, patient, current_station=None) -> bool:
        return True


class ConsoleNotifier(Notifier):
    """Prints notifications to a stream (stdout by default) with a prefix."""

    kind = "console"

    def __init__(self, prefix: str = "LABFLOW:", stream=None):
        self.prefix = prefix
        self.stream = stream

    def _emit(self, text) -> bool:
        try:
            stream = self.stream if self.stream is not None else sys.stdout
            print(f"{self.prefix} {_one_line(text, 400)}", file=stream, flush=True)
            return True
        except Exception as exc:  # pragma: no cover - defensive
            _log(f"console notify failed: {exc}")
            return False

    def step_started(self, patient, station, next_station=None) -> bool:
        return self._emit(format_step_started(patient, station, next_station))

    def step_completed(self, patient, station, next_station=None) -> bool:
        return self._emit(format_step_completed(patient, station, next_station))

    def flow_completed(self, patient) -> bool:
        return self._emit(format_flow_completed(patient))

    def reminder(self, patient, current_station=None) -> bool:
        if current_station is None:
            return False
        return self._emit(format_reminder(patient, current_station))


class TelegramNotifier(Notifier):
    """Telegram alerts via the Bot API (``requests``, imported lazily).

    Message contract (frozen): title line
    ``'LabFlow · <patient first name or "Patient"> — <Step Name> DONE'`` and
    body ``'Next: <name> — <instruction>'``.  Only step information is sent —
    **never clinical values**, intake answers, measurements or results; the lab
    owns all data locally.

    ``sender`` is an optional injection hook for offline tests/embedding: it is
    called as ``sender(url, payload, timeout)`` and must return a
    response-like object exposing ``status_code`` and/or ``ok``.  Without it,
    ``requests.post`` is used.

    Robust by contract: methods never raise — failures are logged to stderr and
    reported as ``False``.
    """

    kind = "telegram"

    def __init__(self, bot_token, chat_id, include_patient_name=True, timeout=10, sender=None):
        self.bot_token = str(bot_token or "")
        self.chat_id = str(chat_id or "")
        self.include_patient_name = bool(include_patient_name)
        self.timeout = timeout
        self.sender = sender

    def send_message(self, text) -> bool:
        """Low-level raw send (subject to the same never-raise contract)."""
        return self._send_text(str(text or ""))

    def _send_text(self, text: str) -> bool:
        try:
            if not self.bot_token or not self.chat_id:
                _log("telegram send skipped: missing bot_token or chat_id")
                return False
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "disable_web_page_preview": True,
            }
            if self.sender is not None:
                response = self.sender(url, payload, self.timeout)
            else:
                import requests  # lazy: stdlib-only environments stay importable

                response = requests.post(url, json=payload, timeout=self.timeout)
            ok = getattr(response, "ok", None)
            status = getattr(response, "status_code", None)
            if ok is None:
                ok = status == 200
            if not ok:
                _log(f"telegram send failed: status={status}")
                return False
            return True
        except Exception as exc:
            _log(f"telegram send error: {exc}")
            return False

    def step_started(self, patient, station, next_station=None) -> bool:
        return self._send_text(
            format_step_started(patient, station, next_station, self.include_patient_name)
        )

    def step_completed(self, patient, station, next_station=None) -> bool:
        return self._send_text(
            format_step_completed(patient, station, next_station, self.include_patient_name)
        )

    def flow_completed(self, patient) -> bool:
        return self._send_text(format_flow_completed(patient, self.include_patient_name))

    def reminder(self, patient, current_station=None) -> bool:
        if current_station is None:
            return False
        return self._send_text(
            format_reminder(patient, current_station, self.include_patient_name)
        )


# -- factory ----------------------------------------------------------------
def read_token_from_file(path):
    """Read ``TELEGRAM_BOT_TOKEN=...`` from an .env-style file (e.g. hermes .env).

    Accepts optional ``export`` prefix and optional quotes.  Returns the token
    string, or None when the file is unreadable or has no token line.
    """
    if not path:
        return None
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    match = _TOKEN_RE.search(text)
    if not match:
        return None
    token = match.group(1).strip().strip('"').strip("'").strip()
    return token or None


def make_notifier(config=None) -> Notifier:
    """Build a notifier from a config dict.

    ``config`` = ``{'type': 'telegram'|'console'|'null', 'bot_token_file': path,
    'bot_token': str, 'chat_id': str, ...}``.

    Telegram falls back to :class:`ConsoleNotifier` when the token (direct or
    from file) or the chat id is missing; unknown/missing types default to
    console too.  Never raises.
    """
    cfg = config if isinstance(config, dict) else {}
    kind = str(cfg.get("type") or "console").strip().lower()

    if kind == "null":
        return NullNotifier()

    if kind == "telegram":
        token = cfg.get("bot_token") or read_token_from_file(cfg.get("bot_token_file"))
        chat_id = cfg.get("chat_id")
        if token and chat_id:
            try:
                timeout = int(cfg.get("timeout", 10))
            except (TypeError, ValueError):
                timeout = 10
            return TelegramNotifier(
                str(token),
                str(chat_id),
                include_patient_name=bool(cfg.get("include_patient_name", True)),
                timeout=timeout,
            )
        _log("telegram notifier unavailable (missing token or chat_id) — using console")
        return ConsoleNotifier()

    if kind != "console":
        _log(f"unknown notifier type {kind!r} — using console")
    return ConsoleNotifier()
