"""Self-contained chart HTML for one patient (print to PDF).

This module deliberately depends only on the *canonical* shapes from
``labflow/docs/MC-EHR-SPEC.md`` — a patient dict from ``PatientStore`` and a
list of observations — so exporting a chart never requires the live app, a
template engine, a CDN, or any external asset.  The output is one HTML file
with inline CSS and, when a metric has at least two numeric points, an inline
SVG trend line.

Two rules are enforced here rather than left to the UI:

* **The disclaimer is always present** (header and footer):
  "Lab record for research and operations. Not a certified EHR; not a medical
  device; clinical decisions are physician-led."
* **Every number carries its provenance.**  A value is rendered with its
  source session id plus the provenance fields the source app supplied
  (app, device, file, protocol, firmware, processing_version).  A number with
  no provenance renders as "provenance missing" rather than looking
  authoritative.

Nothing in this module reads patient data from disk or the network; the caller
passes everything in, and the caller owns access control (LabFlow binds
127.0.0.1).
"""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

__all__ = ["DISCLAIMER", "render_chart_html", "export_filename"]

#: Mandatory on every MC screen and every export (see the build contract).
DISCLAIMER = (
    "Lab record for research and operations. Not a certified EHR; "
    "not a medical device; clinical decisions are physician-led."
)

#: Provenance fields worth showing, in display order.
_PROVENANCE_FIELDS = (
    ("app", "app"),
    ("device", "device"),
    ("file", "file"),
    ("endpoint", "endpoint"),
    ("protocol", "protocol"),
    ("firmware", "firmware"),
    ("processing_version", "processing"),
    ("simulated", "simulated"),
)

#: Fixed metric namespaces — used for grouping and for the source badge.
_NAMESPACES = ("bertec", "runtrack", "eeg", "body", "vitals", "intake")

_SOURCE_LABELS = {
    "bertec": "Bertec",
    "runtrack": "RunTrack",
    "neurosync": "NeuroSync",
    "inbody": "InBody",
    "intake": "Intake",
    "manual": "Manual",
}

_QUALITY_CLASS = {
    "verified": "q-verified",
    "unverified": "q-unverified",
    "flagged": "q-flagged",
    "incomplete": "q-incomplete",
}

_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


# --------------------------------------------------------------------------- #
# small formatting helpers
# --------------------------------------------------------------------------- #
def _text(value: Any) -> str:
    """HTML-escaped text for any scalar; empty string for None."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def _attr(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _num(value: Any) -> float | None:
    """A finite float, or None (bools are not numbers here)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            parsed = float(value.strip())
        except (TypeError, ValueError):
            return None
        if parsed != parsed or parsed in (float("inf"), float("-inf")):
            return None
        return parsed
    return None


def _fmt_value(value: Any) -> str:
    """Human-readable value: numbers get up to 3 decimals, units appended later."""
    if value is None:
        return "—"
    number = _num(value)
    if number is not None and not isinstance(value, bool):
        if number == int(number) and abs(number) < 1e15:
            return str(int(number))
        return f"{number:.3f}".rstrip("0").rstrip(".")
    return str(value)


def _fmt_ts(value: Any) -> str:
    """ISO timestamp -> ``YYYY-MM-DD HH:MM`` when parseable, else verbatim."""
    text = "" if value is None else str(value)
    if not text:
        return "—"
    candidate = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return text
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc)
        return parsed.strftime("%Y-%m-%d %H:%M UTC")
    return parsed.strftime("%Y-%m-%d %H:%M")


def _source_of(observation: Mapping[str, Any]) -> str:
    source = str(observation.get("source") or "").strip().lower()
    if source:
        return source
    metric = str(observation.get("metric") or "")
    return metric.split(".", 1)[0] if "." in metric else "manual"


def _source_label(source: str) -> str:
    return _SOURCE_LABELS.get(source, source.title() or "Unknown")


def _quality(observation: Mapping[str, Any]) -> str:
    quality = str(observation.get("quality") or "unverified").strip().lower()
    return quality if quality in _QUALITY_CLASS else "unverified"


def _namespace_options(metric: str) -> str:
    """Group key for a metric: its fixed namespace, else the raw prefix."""
    prefix = metric.split(".", 1)[0]
    return prefix if prefix in _NAMESPACES else prefix


def _provenance_lines(observation: Mapping[str, Any]) -> list[str]:
    """Human-readable provenance fragments for one observation."""
    lines: list[str] = []
    session_id = observation.get("session_id")
    if session_id not in (None, ""):
        lines.append(f"session {session_id}")
    provenance = observation.get("provenance")
    if not isinstance(provenance, Mapping) or not provenance:
        lines.append("provenance missing")
        return lines
    for key, label in _PROVENANCE_FIELDS:
        value = provenance.get(key)
        if value in (None, "", False):
            continue
        if key == "simulated":
            lines.append("simulated")
        else:
            lines.append(f"{label} {value}")
    return lines


def _provenance_html(observation: Mapping[str, Any]) -> str:
    fragments = [_text(part) for part in _provenance_lines(observation)]
    if not fragments:
        return '<span class="prov prov-missing">provenance missing</span>'
    return '<span class="prov">' + " · ".join(fragments) + "</span>"


def _quality_badge(observation: Mapping[str, Any]) -> str:
    quality = _quality(observation)
    return f'<span class="badge {_QUALITY_CLASS[quality]}">{_text(quality)}</span>'


def _source_badge(source: str) -> str:
    return f'<span class="badge src src-{_attr(source)}">{_text(_source_label(source))}</span>'


def _sparkline(points: Sequence[float], width: int = 132, height: int = 30) -> str:
    """Inline SVG polyline for >= 2 finite points (no external JS)."""
    if len(points) < 2:
        return ""
    low, high = min(points), max(points)
    span = high - low or 1.0
    step = (width - 4) / (len(points) - 1)
    coords = []
    for index, value in enumerate(points):
        x = 2 + index * step
        y = height - 3 - ((value - low) / span) * (height - 8)
        coords.append(f"{x:.1f},{y:.1f}")
    return (
        f'<svg class="spark" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="trend">'
        f'<polyline fill="none" stroke="currentColor" stroke-width="1.6" '
        f'points="{" ".join(coords)}"/></svg>'
    )


# --------------------------------------------------------------------------- #
# data shaping
# --------------------------------------------------------------------------- #
def _ordered_observations(observations: Iterable[Mapping[str, Any]]) -> list[dict]:
    """Valid-ish dicts only, newest first (ISO strings sort correctly)."""
    rows = [dict(item) for item in observations if isinstance(item, Mapping)]
    rows.sort(
        key=lambda row: (str(row.get("measured_at") or ""), str(row.get("metric") or "")),
        reverse=True,
    )
    return rows


def _latest_by_metric(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict]:
    """Latest observation per metric key (newest measured_at wins)."""
    latest: dict[str, dict] = {}
    for row in rows:  # already newest-first
        metric = str(row.get("metric") or "").strip()
        if not metric:
            continue
        latest.setdefault(metric, dict(row))
    return latest


def _series_by_metric(rows: Sequence[Mapping[str, Any]]) -> dict[str, list[float]]:
    """Numeric series per metric, oldest -> newest."""
    series: dict[str, list[tuple[str, float]]] = {}
    for row in rows:
        metric = str(row.get("metric") or "").strip()
        number = _num(row.get("value"))
        if not metric or number is None:
            continue
        series.setdefault(metric, []).append((str(row.get("measured_at") or ""), number))
    result: dict[str, list[float]] = {}
    for metric, points in series.items():
        points.sort(key=lambda pair: pair[0])
        result[metric] = [value for _, value in points]
    return result


def _sessions(rows: Sequence[Mapping[str, Any]]) -> list[dict]:
    """Group observations into sessions (source + session_id), newest first."""
    buckets: dict[tuple[str, str], dict] = {}
    order: list[tuple[str, str]] = []
    for row in rows:
        source = _source_of(row)
        session_id = str(row.get("session_id") or "")
        key = (source, session_id)
        bucket = buckets.get(key)
        if bucket is None:
            bucket = {
                "source": source,
                "session_id": session_id,
                "measured_at": str(row.get("measured_at") or ""),
                "quality": _quality(row),
                "observations": [],
            }
            buckets[key] = bucket
            order.append(key)
        bucket["observations"].append(dict(row))
        # keep the newest timestamp / worst-for-display quality of the group
        stamp = str(row.get("measured_at") or "")
        if stamp > bucket["measured_at"]:
            bucket["measured_at"] = stamp
        if bucket["quality"] == "verified" and _quality(row) != "verified":
            bucket["quality"] = _quality(row)
    sessions = [buckets[key] for key in order]
    sessions.sort(key=lambda item: item["measured_at"], reverse=True)
    return sessions


# --------------------------------------------------------------------------- #
# HTML sections
# --------------------------------------------------------------------------- #
_STYLE = """
:root{--bg:#0d1117;--panel:#151b23;--line:#26303b;--ink:#e6edf3;--muted:#9aa7b4;
--accent:#5cc8ff;--ok:#3fb950;--warn:#d29922;--bad:#f85149;--dim:#8b949e}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.5 "Segoe UI",system-ui,-apple-system,sans-serif}
.wrap{max-width:1000px;margin:0 auto;padding:28px 24px 48px}
header.chart-head{display:flex;flex-wrap:wrap;gap:16px;align-items:flex-end;
justify-content:space-between;border-bottom:1px solid var(--line);padding-bottom:16px}
h1{font-size:26px;margin:0 0 4px}
h2{font-size:15px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);
margin:32px 0 12px}
.sub{color:var(--muted);font-size:13px}
.disclaimer{border:1px solid var(--warn);background:rgba(210,153,34,.10);
color:#f0d38a;padding:10px 14px;border-radius:8px;font-size:12.5px;margin:18px 0}
.badge{display:inline-block;padding:1px 8px;border-radius:999px;font-size:11px;
letter-spacing:.04em;text-transform:uppercase;border:1px solid var(--line);
white-space:nowrap}
.src{background:rgba(92,200,255,.10);border-color:rgba(92,200,255,.35);color:var(--accent)}
.q-verified{background:rgba(63,185,80,.12);border-color:rgba(63,185,80,.4);color:var(--ok)}
.q-unverified{background:rgba(210,153,34,.12);border-color:rgba(210,153,34,.4);color:var(--warn)}
.q-flagged{background:rgba(248,81,73,.12);border-color:rgba(248,81,73,.4);color:var(--bad)}
.q-incomplete{background:rgba(139,148,158,.12);border-color:rgba(139,148,158,.4);color:var(--dim)}
.grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px 18px}
.card h3{margin:0 0 2px;font-size:16px}
.card .meta{color:var(--muted);font-size:12px;margin-bottom:10px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);
vertical-align:top}
th{color:var(--muted);font-weight:600;font-size:11.5px;text-transform:uppercase;
letter-spacing:.06em}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.metric{font-family:ui-monospace,Consolas,monospace;font-size:12.5px}
.unit{color:var(--muted);font-size:11.5px;margin-left:3px}
.prov{display:block;color:var(--dim);font-size:11px;margin-top:2px;
word-break:break-word}
.prov-missing{color:var(--warn)}
.analysis{color:#c9d1d9;font-size:13px;margin:10px 0 0;
border-left:3px solid var(--line);padding-left:10px;white-space:pre-wrap}
.ai{color:#c9d1d9;font-size:13px;margin:8px 0 0;padding:8px 10px;
background:rgba(92,200,255,.06);border-radius:6px;white-space:pre-wrap}
.ai-model{display:block;color:var(--muted);font-size:11px;margin-top:4px}
.spark{color:var(--accent);display:block;margin-top:2px}
.empty{color:var(--muted);font-style:italic;font-size:13px}
footer{margin-top:40px;border-top:1px solid var(--line);padding-top:14px;
color:var(--muted);font-size:12px}
@media print{
  :root{--bg:#fff;--panel:#fff;--line:#ccc;--ink:#111;--muted:#555;
  --dim:#555;--accent:#005f8f;--ok:#1a6b2a;--warn:#8a6100;--bad:#a32018}
  body{font-size:11pt}
  .wrap{max-width:none;padding:0}
  .card{break-inside:avoid;page-break-inside:avoid}
  .disclaimer{background:#fff7e0;color:#5a4300;border-color:#8a6100}
  footer{position:static}
  a{color:inherit;text-decoration:none}
}
"""


def _section_header(label: str, card: Mapping[str, Any]) -> str:
    session_id = card.get("session_id")
    measured_at = _fmt_ts(card.get("measured_at"))
    quality = _quality(card)
    badge = f'<span class="badge {_QUALITY_CLASS[quality]}">{_text(quality)}</span>'
    meta = [measured_at]
    if session_id not in (None, ""):
        meta.insert(0, f"session {_text(session_id)}")
    return (
        f'<div class="card-head"><h3>{_text(label)}</h3></div>'
        f'<div class="meta">{" · ".join(meta)} {badge}</div>'
    )


def _metric_rows(card: Mapping[str, Any], series: Mapping[str, Sequence[float]]) -> str:
    observations = card.get("observations") or []
    if not observations:
        return '<tr><td colspan="4" class="empty">no measurements</td></tr>'
    rows = []
    for observation in observations:
        metric = str(observation.get("metric") or "")
        value = _fmt_value(observation.get("value"))
        unit = str(observation.get("unit") or "")
        spark = _sparkline(series.get(metric, ()))
        rows.append(
            "<tr>"
            f'<td><span class="metric">{_text(metric)}</span>{spark}</td>'
            f'<td class="num">{_text(value)}'
            + (f'<span class="unit">{_text(unit)}</span>' if unit else "")
            + "</td>"
            f"<td>{_quality_badge(observation)}</td>"
            f"<td>{_provenance_html(observation)}</td>"
            "</tr>"
        )
    return "".join(rows)


def _analysis_block(card: Mapping[str, Any]) -> str:
    """The source app's own words, then any verbatim assistant text."""
    parts = []
    analyses = []
    for observation in card.get("observations") or []:
        text = str(observation.get("analysis") or "").strip()
        if text and text not in analyses:
            analyses.append(text)
    if analyses:
        parts.append('<p class="analysis">' + "<br>".join(_text(t) for t in analyses) + "</p>")

    ai_texts = []
    ai_models = []
    for observation in card.get("observations") or []:
        text = str(observation.get("ai_text") or "").strip()
        if text and text not in ai_texts:
            ai_texts.append(text)
            model = str(observation.get("ai_model") or "").strip()
            if model:
                ai_models.append(model)
    if ai_texts:
        model_note = (
            f'<span class="ai-model">model: {_text(", ".join(dict.fromkeys(ai_models)))}</span>'
            if ai_models
            else ""
        )
        parts.append('<div class="ai">' + "<br>".join(_text(t) for t in ai_texts) + model_note + "</div>")
    return "".join(parts)


def _timeline_table(sessions: Sequence[Mapping[str, Any]]) -> str:
    if not sessions:
        return '<p class="empty">No sessions recorded for this patient yet.</p>'
    rows = []
    for session in sessions:
        values = [
            f"{obs.get('metric')}={_fmt_value(obs.get('value'))}{obs.get('unit') or ''}"
            for obs in session.get("observations") or []
        ]
        summary = ", ".join(values[:4]) + (" …" if len(values) > 4 else "")
        rows.append(
            "<tr>"
            f'<td>{_text(_fmt_ts(session.get("measured_at")))}</td>'
            f'<td>{_source_badge(str(session.get("source") or ""))}</td>'
            f'<td class="metric">{_text(session.get("session_id") or "—")}</td>'
            f'<td><span class="badge {_QUALITY_CLASS[_quality(session)]}">'
            f'{_text(_quality(session))}</span></td>'
            f'<td class="sub">{_text(summary)}</td>'
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Measured</th><th>Source</th><th>Session</th>"
        "<th>Quality</th><th>Values</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


# --------------------------------------------------------------------------- #
# public entry point
# --------------------------------------------------------------------------- #
def export_filename(patient: Mapping[str, Any]) -> str:
    """Safe download name, e.g. ``chart-jane-doe-1a2b.html``."""
    pid = _SAFE_NAME_RE.sub("-", str(patient.get("id") or "patient")).strip("-") or "patient"
    return f"chart-{pid}.html"


def render_chart_html(
    patient: Mapping[str, Any],
    observations: Sequence[Mapping[str, Any]] = (),
    *,
    generated_at: str | None = None,
) -> str:
    """Render one patient's chart as a single self-contained HTML document.

    ``patient`` is a ``PatientStore`` dict; ``observations`` are canonical MC
    observation dicts (already filtered to this subject).  Every number shown
    is accompanied by its session id and provenance fields.
    """
    patient = dict(patient or {})
    rows = _ordered_observations(observations)
    sessions = _sessions(rows)
    series = _series_by_metric(rows)
    generated = generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    name = str(patient.get("name") or "Unknown patient")
    pid = str(patient.get("id") or "")
    dob = patient.get("dob") or (patient.get("intake") or {}).get("dob") or "—"
    status = str(patient.get("status") or "—")

    meta_bits = [f"Patient id <span class=\"metric\">{_text(pid)}</span>"]
    if patient.get("dob") or (patient.get("intake") or {}).get("dob"):
        meta_bits.append(f"DOB {_text(dob)}")
    meta_bits.append(f"Status {_text(status)}")
    meta_bits.append(f"Generated {_text(generated)}")
    meta_bits.append(f"{len(sessions)} session{'s' if len(sessions) != 1 else ''} · "
                     f"{len(rows)} observation{'s' if len(rows) != 1 else ''}")

    cards = []
    for session in sessions:
        source = str(session.get("source") or "")
        cards.append(
            '<section class="card">'
            + _section_header(_source_label(source), session)
            + "<table><thead><tr><th>Metric</th><th>Value</th><th>Quality</th>"
            "<th>Provenance</th></tr></thead><tbody>"
            + _metric_rows(session, series)
            + "</tbody></table>"
            + _analysis_block(session)
            + "</section>"
        )

    body = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>Chart — {_text(name)}</title>"
        f"<style>{_STYLE}</style></head><body><div class=\"wrap\">"
        '<header class="chart-head"><div>'
        f"<h1>{_text(name)}</h1>"
        f'<div class="sub">{" · ".join(meta_bits)}</div>'
        "</div></header>"
        f'<p class="disclaimer">{_text(DISCLAIMER)}</p>'
        "<h2>Timeline</h2>"
        + _timeline_table(sessions)
        + "<h2>By session</h2>"
        + ('<div class="grid">' + "".join(cards) + "</div>" if cards
           else '<p class="empty">No observations recorded for this patient yet.</p>')
        + f'<footer>{_text(DISCLAIMER)}<br>'
        "Every value above carries the source session id and the provenance the "
        "source app reported; values marked <em>unverified</em>, <em>flagged</em> "
        "or <em>incomplete</em> are shown as received and were not upgraded.</footer>"
        "</div></body></html>"
    )
    return body
