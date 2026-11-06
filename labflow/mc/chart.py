"""Per-patient chart aggregation.

One patient, one payload: header data, a newest-first timeline of sessions,
one card per source, and the latest value per metric.  Pure read of the
append-only store — no adapter runs here (that is ``Ingest.sync``).

Shape (stable; the API returns it verbatim and the UI renders it)::

    {
      "patient":   {id, name, dob, status, created_at, linked_sessions},
      "generated_at": iso,
      "timeline":  [{source, source_label, session_id, measured_at, quality,
                     analysis, ai_text, ai_model, provenance, metric_count,
                     metrics: [{metric, value, unit}]}],      # newest first
      "sources":   [{source, label, available, sessions, last_activity,
                     latest: [...], analysis, ai_text, ai_model}],
      "latest":    [{metric, value, unit, quality, measured_at, source, session_id}],
      "totals":    {observations, sessions, sources},
      "disclaimer": str,
    }
"""

from __future__ import annotations

from datetime import datetime, timezone

from .ingest import DISCLAIMER, Ingest
from .schema import QUALITY_TRUST, SOURCE_LABELS, SOURCE_ORDER

__all__ = ["build_chart", "latest_by_metric", "group_sessions"]


def _dt(value) -> datetime:
    try:
        stamp = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return datetime.min.replace(tzinfo=timezone.utc)
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)


def _worst_quality(rows: list[dict]) -> str:
    return min(
        (str(row.get("quality") or "unverified") for row in rows),
        key=lambda word: QUALITY_TRUST.get(word, 0),
    )


def group_sessions(rows: list[dict]) -> list[dict]:
    """Group observations into session records, newest first."""
    groups: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        groups.setdefault((str(row.get("source")), str(row.get("session_id"))), []).append(row)

    sessions: list[dict] = []
    for (source, session_id), items in groups.items():
        items = sorted(items, key=lambda row: str(row.get("metric")))
        first = items[0]
        analysis = next((str(row.get("analysis")) for row in items if row.get("analysis")), "")
        ai_text = next((str(row.get("ai_text")) for row in items if row.get("ai_text")), "")
        ai_model = next((str(row.get("ai_model")) for row in items if row.get("ai_model")), "")
        sessions.append(
            {
                "source": source,
                "source_label": SOURCE_LABELS.get(source, source.title()),
                "session_id": session_id,
                "measured_at": first.get("measured_at"),
                "quality": _worst_quality(items),
                "analysis": analysis,
                "ai_text": ai_text,
                "ai_model": ai_model,
                "provenance": first.get("provenance") or {},
                "metric_count": len(items),
                "metrics": [
                    {"metric": row.get("metric"), "value": row.get("value"), "unit": row.get("unit")}
                    for row in items
                ],
            }
        )
    sessions.sort(key=lambda item: (_dt(item.get("measured_at")), item["session_id"]), reverse=True)
    return sessions


def latest_by_metric(rows: list[dict]) -> list[dict]:
    """One row per metric: newest ``measured_at`` wins; higher trust breaks ties."""
    best: dict[str, dict] = {}
    for row in rows:
        metric = str(row.get("metric"))
        candidate = dict(row)
        candidate["_when"] = _dt(row.get("measured_at"))
        candidate["_trust"] = QUALITY_TRUST.get(str(row.get("quality")), 0)
        current = best.get(metric)
        if current is None or (candidate["_when"], candidate["_trust"]) > (
            current["_when"],
            current["_trust"],
        ):
            best[metric] = candidate

    latest = []
    for metric in sorted(best):
        row = best[metric]
        latest.append(
            {
                "metric": metric,
                "value": row.get("value"),
                "unit": row.get("unit") or "",
                "quality": row.get("quality"),
                "measured_at": row.get("measured_at"),
                "source": row.get("source"),
                "session_id": row.get("session_id"),
            }
        )
    return latest


def build_chart(store, patient_id, data_dir=None, ingest: Ingest | None = None) -> dict:
    """The chart payload for one patient.

    Raises :class:`KeyError` for an unknown patient (the API turns that into a
    404); everything else is data-dependent, never an error.
    """
    ingest = ingest or Ingest(store=store, data_dir=data_dir)
    patient = ingest.store.get(patient_id)
    if patient is None:
        raise KeyError(f"unknown patient: {patient_id!r}")

    rows = ingest.read(subject_id=str(patient.get("id")))
    timeline = group_sessions(rows)

    by_source: dict[str, list[dict]] = {}
    for row in rows:
        by_source.setdefault(str(row.get("source")), []).append(row)

    cards = []
    for source in SOURCE_ORDER:
        source_rows = by_source.get(source, [])
        sessions = [item for item in timeline if item["source"] == source]
        latest = latest_by_metric(source_rows) if source_rows else []
        cards.append(
            {
                "source": source,
                "label": SOURCE_LABELS.get(source, source.title()),
                "available": bool(source_rows),
                "sessions": len(sessions),
                "last_activity": sessions[0]["measured_at"] if sessions else None,
                "latest": latest,
                "analysis": sessions[0]["analysis"] if sessions else "",
                "ai_text": sessions[0]["ai_text"] if sessions else "",
                "ai_model": sessions[0]["ai_model"] if sessions else "",
            }
        )

    return {
        "patient": {
            "id": patient.get("id"),
            "name": patient.get("name"),
            "dob": patient.get("dob"),
            "status": patient.get("status"),
            "created_at": patient.get("created_at"),
            "linked_sessions": patient.get("linked_sessions") or {},
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "timeline": timeline,
        "sources": cards,
        "latest": latest_by_metric(rows) if rows else [],
        "totals": {
            "observations": len(rows),
            "sessions": len(timeline),
            "sources": len([card for card in cards if card["available"]]),
        },
        "disclaimer": DISCLAIMER,
    }
