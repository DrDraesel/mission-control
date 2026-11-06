/* ============================================================
   Mission Control — shared UI logic.
   Plain browser JS, no build step, no external libraries.
   Every page is a static shell; this file fills it from the
   /api/mc/* endpoints and keeps an honest empty/error state when
   an endpoint is missing or a source has no data yet.
   ============================================================ */
(function () {
  "use strict";

  var API = "/api/mc";
  var SOURCES = ["bertec", "runtrack", "neurosync", "inbody", "intake"];
  var SOURCE_LABEL = {
    bertec: "Bertec",
    runtrack: "RunTrack",
    neurosync: "NeuroSync",
    inbody: "InBody",
    intake: "Intake",
    manual: "Manual"
  };
  var QUALITY_CLASS = {
    verified: "ok",
    unverified: "warn",
    flagged: "bad",
    incomplete: "bad"
  };
  var METRIC_LABEL = {
    asi: "ASI",
    quality: "Session quality",
    kept_trials: "Kept trials",
    form_index: "Form index",
    symmetry_mean_pct: "Symmetry mean",
    trunk_lean_deg: "Trunk lean",
    head_sway_norm: "Head sway (norm.)",
    external_power_est_watts: "External power (est.)",
    tbr: "Theta / beta ratio",
    jump_height: "Jump height",
    peak_force: "Peak force",
    resting_hr: "Resting HR",
    systolic: "Systolic BP",
    training_days_week: "Training days / week",
    weight_kg: "Weight",
    skeletal_muscle_kg: "Skeletal muscle mass",
    body_fat_kg: "Body fat mass",
    body_fat_pct: "Body fat",
    visceral_fat: "Visceral fat",
    lean_mass_kg: "Lean mass",
    bmi: "BMI"
  };
  var UNREACHABLE_HINT = {
    bertec: "Open Bertec Jump and finish a protocol, then check that bertec-jump/data/protocols exists on this PC.",
    runtrack: "Start RunTrack and complete a session; its data/runtrack.db must exist and be readable.",
    neurosync: "Open NeuroSync and record a session. An empty recordings/ folder returns nothing — that is not an error.",
    inbody: "No device API. Enter the printout by hand on the InBody page, or import the CSV.",
    intake: "Intake comes from LabFlow's own patient store; create or edit the patient in LabFlow."
  };

  /* -------------------------------------------------- basics */
  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function asArray(value) {
    if (Array.isArray(value)) return value;
    if (value && typeof value === "object") return Object.keys(value).map(function (k) { return value[k]; });
    return [];
  }
  function esc(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function shortId(value) {
    var text = String(value == null ? "" : value);
    return text.length > 32 ? text.slice(0, 31) + "…" : text;
  }
  function titleCase(text) {
    return String(text || "")
      .replace(/[._-]+/g, " ")
      .replace(/\b\w/g, function (m) { return m.toUpperCase(); });
  }
  function has(obj, key) {
    return obj != null && Object.prototype.hasOwnProperty.call(obj, key);
  }
  function numberOrNull(value) {
    if (value === null || value === undefined || value === "") return null;
    var n = typeof value === "number" ? value : Number(value);
    return isFinite(n) ? n : null;
  }
  function parseDate(value) {
    if (!value) return null;
    var text = String(value);
    // A bare YYYY-MM-DD is a calendar date, not UTC midnight: parse it locally
    // so a DOB never shifts a day in a negative-offset timezone.
    var d = new Date(/^\d{4}-\d{2}-\d{2}$/.test(text) ? text + "T00:00:00" : text);
    return isNaN(d.getTime()) ? null : d;
  }
  function fmtDate(value) {
    var d = parseDate(value);
    if (!d) return value ? String(value) : "—";
    return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
  }
  function fmtTime(value) {
    var d = parseDate(value);
    if (!d) return "";
    return d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
  }
  function fmtWhen(value) {
    var d = parseDate(value);
    if (!d) return value ? String(value) : "—";
    var days = Math.floor((Date.now() - d.getTime()) / 86400000);
    if (days === 0) return "today, " + fmtTime(d);
    if (days === 1) return "yesterday";
    if (days > 1 && days < 30) return days + " days ago";
    return fmtDate(d);
  }
  function fmtValue(value) {
    if (value === null || value === undefined || value === "") return "—";
    var n = typeof value === "number" ? value : null;
    if (n !== null) {
      if (!isFinite(n)) return "—";
      return new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(n);
    }
    return String(value);
  }
  function ageFromDob(dob) {
    if (!dob) return null;
    var text = String(dob);
    var d = parseDate(/^\d{4}-\d{2}-\d{2}$/.test(text) ? text + "T00:00:00" : text);
    if (!d) return null;
    var now = new Date();
    var age = now.getFullYear() - d.getFullYear();
    var m = now.getMonth() - d.getMonth();
    if (m < 0 || (m === 0 && now.getDate() < d.getDate())) age -= 1;
    return age >= 0 && age < 130 ? age : null;
  }
  function metricLabel(key) {
    var raw = String(key || "");
    var parts = raw.split(".");
    var tail = parts.length > 1 ? parts.slice(1).join(".") : raw;
    if (parts[0] === "runtrack" && parts[1] === "joint" && parts.length >= 4) {
      return "Joint " + parts[2] + " " + parts[3];
    }
    if (METRIC_LABEL[tail]) return METRIC_LABEL[tail];
    var suffix = "";
    if (/_rel$/.test(tail) || /_abs$/.test(tail)) {
      suffix = tail.slice(-3) === "rel" ? " relative" : " absolute";
      tail = tail.slice(0, -4);
    }
    var units = ["_mm_s", "_mmhg", "_uv2", "_pct", "_bpm", "_watts", "_cm", "_kg", "_deg", "_hz", "_ms", "_n", "_w", "_s"];
    for (var i = 0; i < units.length; i += 1) {
      if (tail.length > units[i].length && tail.slice(-units[i].length) === units[i]) {
        tail = tail.slice(0, -units[i].length);
        break;
      }
    }
    return (METRIC_LABEL[tail] || titleCase(tail)) + suffix;
  }
  function srcTag(source) {
    var key = String(source || "").toLowerCase();
    return '<span class="src-tag"><i class="dot src-' + esc(key) + '" aria-hidden="true"></i>' +
      esc(SOURCE_LABEL[key] || titleCase(key) || "Unknown") + "</span>";
  }
  function qualityBadge(quality) {
    var key = String(quality || "").toLowerCase();
    if (!key) return '<span class="badge plain">no data</span>';
    return '<span class="badge q-' + esc(key) + (QUALITY_CLASS[key] ? "" : " plain") + '">' + esc(key) + "</span>";
  }
  function provTitle(prov) {
    if (!prov || typeof prov !== "object") return "";
    return Object.keys(prov).filter(function (k) {
      return prov[k] !== null && prov[k] !== undefined && String(prov[k]) !== "";
    }).map(function (k) {
      return k.replace(/_/g, " ") + ": " + prov[k];
    }).join(" · ");
  }
  function worstQuality(list) {
    var trust = { verified: 3, unverified: 2, incomplete: 1, flagged: 1 };
    var worst = null;
    var worstRank = 99;
    (list || []).forEach(function (metric) {
      var key = String(metric.quality || "").toLowerCase();
      if (!key) return;
      var rank = trust[key] != null ? trust[key] : 1;
      if (rank < worstRank) { worstRank = rank; worst = key; }
    });
    return worst;
  }
  function metricTitle(metric) {
    var parts = [];
    if (metric.session_id) parts.push("session: " + metric.session_id);
    var provenance = provTitle(metric.provenance);
    if (provenance) parts.push(provenance);
    return parts.join(" · ");
  }
  function metricValueHtml(metric) {
    var text = fmtValue(metric.value);
    var unit = metric.unit ? '<span class="unit">' + esc(metric.unit) + "</span>" : "";
    var body = esc(text) + unit;
    var title = metricTitle(metric);
    if (title) {
      return '<span class="prov" tabindex="0" title="' + esc(title) + '" aria-label="' +
        esc(text + " " + (metric.unit || "") + " — " + title) + '">' + body + "</span>";
    }
    return '<span class="prov prov-missing" tabindex="0" title="provenance missing" ' +
      'aria-label="' + esc(text + " " + (metric.unit || "") + " — provenance missing") + '">' + body + "</span>";
  }

  /* -------------------------------------------------- http */
  function apiErrorText(response, payload) {
    if (payload && typeof payload === "object") {
      if (payload.detail) return String(payload.detail);
      if (payload.error) return String(payload.error);
    }
    return "HTTP " + response.status + " from " + response.url;
  }
  function request(path, options) {
    var opts = options || {};
    return fetch(path, {
      method: opts.method || "GET",
      headers: opts.body ? { "Content-Type": "application/json" } : undefined,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
      cache: "no-store"
    }).then(function (response) {
      return response.text().then(function (text) {
        var payload = null;
        if (text) {
          try { payload = JSON.parse(text); } catch (err) { payload = null; }
        }
        if (!response.ok) {
          var message = apiErrorText(response, payload);
          var error = new Error(message);
          error.status = response.status;
          throw error;
        }
        if (payload === null && text) {
          throw new Error("The API returned a non-JSON response (" + response.status + ").");
        }
        return payload || {};
      });
    });
  }
  function get(path) { return request(path); }
  function post(path, body) { return request(path, { method: "POST", body: body }); }

  function pageNotice(kind, message, target) {
    var host = target || $("#page-notice");
    if (!host) return;
    host.innerHTML = '<div class="banner ' + esc(kind) + '" role="' + (kind === "bad" ? "alert" : "status") + '">' +
      esc(message) + "</div>";
  }
  function clearNotice(target) {
    var host = target || $("#page-notice");
    if (host) host.innerHTML = "";
  }

  /* -------------------------------------------------- payload readers
     The API contract fixes the resources, not every inner key. These
     readers accept the documented shape first and a couple of sane
     aliases, so a naming drift shows real data instead of a blank page. */
  function patientList(payload) {
    if (Array.isArray(payload)) return payload;
    return asArray(payload.patients || payload.items || payload.rows || []);
  }
  function sourceCounts(raw) {
    var counts = {};
    if (Array.isArray(raw)) {
      raw.forEach(function (item) {
        var key = String((item && (item.source || item.name || item.id)) || "").toLowerCase();
        if (!key) return;
        var n = item.count != null ? item.count : (item.sessions != null ? item.sessions : item.observations);
        counts[key] = numberOrNull(n);
      });
      return counts;
    }
    if (raw && typeof raw === "object") {
      Object.keys(raw).forEach(function (key) {
        var value = raw[key];
        if (value && typeof value === "object") {
          var n = value.count != null ? value.count : (value.sessions != null ? value.sessions : value.observations);
          counts[key.toLowerCase()] = numberOrNull(n);
        } else {
          counts[key.toLowerCase()] = numberOrNull(value);
        }
      });
    }
    return counts;
  }
  function integrationsList(payload) {
    var raw = payload.integrations || payload.sources || payload.items || payload;
    return asArray(raw).map(function (item) {
      var key = String((item && (item.source || item.name || item.id)) || "").toLowerCase();
      return {
        source: key,
        path: item.path || item.endpoint || item.location || "",
        reachable: item.reachable != null ? item.reachable : item.ok,
        sessions: item.sessions != null ? item.sessions : (item.sessions_found != null ? item.sessions_found : item.count),
        last_checked: item.last_checked || item.checked_at || item.last_seen || null,
        hint: item.hint || item.action || item.next_step || ""
      };
    }).filter(function (item) { return item.source; });
  }
  function unlinkedCount(overview) {
    var counts = overview.counts && typeof overview.counts === "object" ? overview.counts : {};
    var raw = overview.unlinked_sessions != null ? overview.unlinked_sessions
      : (counts.unlinked_sessions != null ? counts.unlinked_sessions
        : (overview.unlinked != null ? overview.unlinked : overview.unlinked_count));
    if (Array.isArray(raw)) return raw.length;
    if (raw && typeof raw === "object") {
      var total = numberOrNull(raw.count);
      if (total != null) return total;
      return asArray(raw).length;
    }
    return numberOrNull(raw);
  }
  function kpiNumber(value) {
    var n = numberOrNull(value);
    return n == null ? "—" : new Intl.NumberFormat().format(n);
  }
  /* -------------------------------------------------- rail */
  function markRail() {
    var here = location.pathname.replace(/\/+$/, "") || "/mc";
    $$(".rail a[data-nav]").forEach(function (link) {
      var target = link.getAttribute("href");
      var active = (target === "/mc" && here === "/mc") ||
        (target !== "/mc" && here.indexOf(target) === 0);
      if (active) link.classList.add("active");
      else link.classList.remove("active");
      if (active) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
  }

  /* ================================================================
     Overview — master admin panel
     ================================================================ */
  function renderHealthStrip(items) {
    var host = $("#health-strip");
    if (!host) return;
    if (!items.length) {
      host.innerHTML = '<span class="muted small">No integration status reported yet.</span>';
      return;
    }
    var html = items.map(function (item) {
      var down = item.reachable === false || String(item.reachable).toLowerCase() === "false";
      var unknown = item.reachable === null || item.reachable === undefined;
      var sessions = numberOrNull(item.sessions);
      var count = sessions == null ? "—" : String(sessions);
      var label = SOURCE_LABEL[item.source] || titleCase(item.source);
      return '<a class="health-item' + (down ? " down" : "") + '" href="/mc/integrations" title="' +
        esc(item.path || label) + '">' +
        '<i class="dot ' + (down ? "bad" : unknown ? "idle" : "ok") + '" aria-hidden="true"></i>' +
        "<span>" + esc(label) + "</span>" +
        '<span class="count" title="sessions found">' + esc(count) + "</span>" +
        "</a>";
    }).join("");
    host.innerHTML = html;
  }

  function renderPatientsTable(patients) {
    var tbody = $("#patients-body");
    var empty = $("#patients-empty");
    var wrap = $("#patients-wrap");
    var loading = $("#patients-loading");
    if (loading) loading.hidden = true;
    if (!tbody) return;
    if (!patients.length) {
      tbody.innerHTML = "";
      if (empty) empty.hidden = false;
      if (wrap) wrap.hidden = true;
      return;
    }
    if (empty) empty.hidden = true;
    if (wrap) wrap.hidden = false;
    tbody.innerHTML = patients.map(function (patient) {
      var id = patient.id || patient.patient_id || patient.subject_id || "";
      var name = patient.name || patient.display_name || "Unnamed patient";
      var intake = patient.intake && typeof patient.intake === "object" ? patient.intake : {};
      var age = patient.age != null ? patient.age : ageFromDob(patient.dob || patient.date_of_birth || intake.dob);
      var counts = sourceCounts(patient.sessions || patient.sources || patient.counts || patient.source_counts || {});
      var chips = SOURCES.filter(function (source) {
        return counts[source] != null && counts[source] > 0;
      }).map(function (source) {
        return '<span class="src-tag" title="' + esc(SOURCE_LABEL[source] + ": " + counts[source] + " sessions") + '">' +
          '<i class="dot src-' + source + '" aria-hidden="true"></i>' + esc(SOURCE_LABEL[source]) +
          " · " + esc(counts[source]) + "</span>";
      }).join("");
      var last = patient.last_activity || patient.last_seen || patient.last_measured_at || patient.updated_at;
      var status = patient.status ? '<span class="badge plain">' + esc(patient.status) + "</span>" : "";
      return '<tr data-patient-id="' + esc(id) + '">' +
        '<td class="name"><a href="/mc/patient/' + encodeURIComponent(id) + '">' + esc(name) + "</a>" +
        '<span class="sub">' + esc(id || "no id") + "</span></td>" +
        '<td class="age">' + (age == null ? "—" : esc(age)) + "</td>" +
        '<td class="when">' + (last ? esc(fmtWhen(last)) : '<span class="muted">no activity</span>') + "</td>" +
        '<td class="sources-cell"><div class="sources">' + (chips || '<span class="none">no linked sessions</span>') + "</div></td>" +
        '<td class="status">' + status + "</td>" +
        "</tr>";
    }).join("");
  }

  function overviewPage() {
    markRail();
    var syncButton = $("#sync-all");

    function loadKpis() {
      return get(API + "/overview").then(function (overview) {
        var counts = overview.counts || overview;
        var patients = counts.patients != null ? counts.patients : counts.patient_count;
        var observations = counts.observations != null ? counts.observations : counts.observation_count;
        var sessions = counts.sessions != null ? counts.sessions : counts.linked_sessions;
        if (sessions && typeof sessions === "object") {
          var map = sourceCounts(sessions);
          sessions = Object.keys(map).reduce(function (sum, key) { return sum + (map[key] || 0); }, 0);
        }
        $("#kpi-patients").textContent = kpiNumber(patients);
        $("#kpi-observations").textContent = kpiNumber(observations);
        $("#kpi-sessions").textContent = kpiNumber(sessions);
        var unlinked = unlinkedCount(overview);
        $("#kpi-unlinked").textContent = unlinked == null ? "—" : kpiNumber(unlinked);
        $("#kpi-unlinked-card").classList.toggle("warn", unlinked > 0);
        var last = overview.last_ingest || overview.last_ingest_at || overview.ingested_at;
        var reportsLast = has(overview, "last_ingest") || has(overview, "last_ingest_at") || has(overview, "ingested_at");
        $("#kpi-last-ingest").textContent = last ? fmtWhen(last) : (reportsLast ? "never" : "not reported");
        $("#health-stamp").textContent = last ? "Last ingest " + fmtDate(last) + " · " + fmtTime(last) : "No ingest has run yet";
        renderHealthStrip(integrationsList(overview));
        if (syncButton) syncButton.disabled = false;
        return overview;
      }).catch(function (error) {
        pageNotice("bad", "Could not read the Mission Control overview: " + error.message + ". The pages stay usable; nothing is shown as zero by default.");
        $("#health-strip").innerHTML = '<span class="muted small">Integration status unavailable.</span>';
        if (syncButton) syncButton.disabled = true;
        throw error;
      });
    }

    function loadPatients() {
      return get(API + "/patients").then(function (payload) {
        renderPatientsTable(patientList(payload));
      }).catch(function (error) {
        var tbody = $("#patients-body");
        if (tbody) tbody.innerHTML = "";
        var loading = $("#patients-loading");
        if (loading) loading.hidden = true;
        var empty = $("#patients-empty");
        if (empty) {
          empty.hidden = false;
          empty.textContent = "Patient list unavailable — " + error.message;
        }
      });
    }

    function syncAll() {
      if (!syncButton) return;
      syncButton.disabled = true;
      syncButton.textContent = "Syncing…";
      clearNotice();
      get(API + "/patients").then(function (payload) {
        var patients = patientList(payload);
        if (!patients.length) {
          pageNotice("warn", "Nothing to sync — there are no patients yet. Start with New patient / intake.");
          return null;
        }
        var added = 0;
        var failed = [];
        return patients.reduce(function (chain, patient) {
          var id = patient.id || patient.patient_id || patient.subject_id;
          return chain.then(function () {
            return post(API + "/patients/" + encodeURIComponent(id) + "/sync", {})
              .then(function (result) {
                var n = result.added != null ? result.added
                  : (result.added_count != null ? result.added_count : (Array.isArray(result.observations) ? result.observations.length : 0));
                added += numberOrNull(n) || 0;
              })
              .catch(function (error) {
                failed.push((patient.name || id) + " (" + error.message + ")");
              });
          });
        }, Promise.resolve()).then(function () {
          if (failed.length) {
            pageNotice("warn", "Sync finished with " + added + " new observation(s). Could not sync " + failed.length + " patient(s): " + failed.join("; "));
          } else {
            pageNotice("ok", "Sync finished — " + added + " new observation(s) across " + patients.length + " patient(s).");
          }
        });
      }).catch(function (error) {
        pageNotice("bad", "Sync could not start: " + error.message);
      }).then(function () {
        syncButton.disabled = false;
        syncButton.textContent = "Sync all";
        loadKpis().catch(function () {});
        loadPatients();
      });
    }

    if (syncButton) {
      syncButton.disabled = true;
      syncButton.addEventListener("click", syncAll);
    }
    loadKpis().catch(function () {});
    loadPatients();
  }

  /* ================================================================
     Patient chart
     ================================================================ */
  function currentPatientId() {
    var match = location.pathname.match(/\/mc\/patient\/([^/]+)/);
    if (match) return decodeURIComponent(match[1]);
    return new URLSearchParams(location.search).get("patient") || "";
  }

  function normalizeMetric(item, fallbackSource) {
    if (item == null) return null;
    if (typeof item === "number" || typeof item === "string") {
      return { metric: "", value: item, unit: "", source: fallbackSource };
    }
    var key = item.metric || item.key || item.name || "";
    if (!key && item.label) key = item.label;
    return {
      source: String(item.source || fallbackSource || "").toLowerCase(),
      metric: String(key),
      value: item.value1 != null ? item.value1 : item.value,
      unit: item.unit || "",
      measured_at: item.measured_at || item.timestamp || item.created_at || null,
      quality: item.quality || null,
      provenance: item.provenance || null,
      session_id: item.session_id || item.session || null,
      analysis: item.analysis || "",
      ai_text: item.ai_text || item.ai || "",
      ai_model: item.ai_model || item.model || "",
      _order: 0
    };
  }
  function metricArray(raw, source) {
    var list = [];
    if (Array.isArray(raw)) {
      raw.forEach(function (item) { var m = normalizeMetric(item, source); if (m) list.push(m); });
    } else if (raw && typeof raw === "object") {
      Object.keys(raw).forEach(function (key) {
        var item = raw[key];
        if (item && typeof item === "object") {
          var m = normalizeMetric(item, source);
          if (m) { m.metric = m.metric || key; list.push(m); }
        } else {
          list.push({
            source: source, metric: key, value: item, unit: "",
            measured_at: null, quality: null, provenance: null, session_id: null,
            analysis: "", ai_text: "", ai_model: "", _order: 0
          });
        }
      });
    }
    return list;
  }
  function sortMetrics(list) {
    return list.map(function (m, i) { m._order = i; return m; }).sort(function (a, b) {
      var da = parseDate(a.measured_at), db = parseDate(b.measured_at);
      if (da && db && da.getTime() !== db.getTime()) return db.getTime() - da.getTime();
      if (da && !db) return -1;
      if (!da && db) return 1;
      return a._order - b._order;
    });
  }

  function cardModels(chart, timeline) {
    var models = {};
    var rawCards = chart.cards || chart.sources || chart.source_cards || null;
    if (rawCards && typeof rawCards === "object" && !Array.isArray(rawCards)) {
      Object.keys(rawCards).forEach(function (key) {
        var entry = rawCards[key] || {};
        if (Array.isArray(entry) || (entry && entry.metric != null)) {
          models[key.toLowerCase()] = { metrics: metricArray(entry, key) };
          return;
        }
        var metrics = entry.metrics || entry.observations || entry.latest || entry.values || entry.measurements || entry.data || [];
        models[key.toLowerCase()] = {
          metrics: metricArray(metrics, key),
          quality: entry.quality,
          analysis: entry.analysis || "",
          ai_text: entry.ai_text || "",
          ai_model: entry.ai_model || "",
          measured_at: entry.measured_at || entry.latest_at || null,
          session_id: entry.session_id || null
        };
      });
    } else if (Array.isArray(rawCards)) {
      rawCards.forEach(function (entry) {
        var key = String(entry.source || entry.name || entry.id || "").toLowerCase();
        if (!key) return;
        models[key] = {
          metrics: metricArray(entry.metrics || entry.observations || entry.latest || entry.values || entry.data || [], key),
          quality: entry.quality,
          analysis: entry.analysis || "",
          ai_text: entry.ai_text || "",
          ai_model: entry.ai_model || "",
          measured_at: entry.measured_at || entry.last_activity || entry.latest_at || null,
          session_id: entry.session_id || null,
          sessions: entry.sessions
        };
      });
    }

    // Fallback 1: a flat latest-measurements list/object.
    if (!Object.keys(models).length) {
      var latest = chart.latest || chart.latest_measurements || chart.latest_metrics || chart.measurements || [];
      metricArray(latest, "").forEach(function (m) {
        var key = m.source || (m.metric ? m.metric.split(".")[0] : "");
        if (!key) return;
        models[key] = models[key] || { metrics: [] };
        models[key].metrics.push(m);
      });
    }

    // Fallback 2: derive per-source cards from timeline entries.
    timeline.forEach(function (entry) {
      var key = String(entry.source || "").toLowerCase();
      if (!key) return;
      models[key] = models[key] || { metrics: [] };
      var metrics = metricArray(entry.metrics || entry.observations || entry.values || entry.metric_values || [], key);
      metrics.forEach(function (m) {
        m.measured_at = m.measured_at || entry.measured_at;
        m.quality = m.quality || entry.quality;
        m.session_id = m.session_id || entry.session_id;
        m.analysis = m.analysis || entry.analysis || "";
        models[key].metrics.push(m);
      });
      if (!models[key].analysis) models[key].analysis = entry.analysis || "";
      if (!models[key].ai_text) {
        models[key].ai_text = entry.ai_text || "";
        models[key].ai_model = entry.ai_model || "";
      }
      if (!models[key].measured_at) models[key].measured_at = entry.measured_at || entry.last_activity;
      if (!models[key].quality) models[key].quality = entry.quality;
      if (!models[key].session_id) models[key].session_id = entry.session_id;
    });

    // The chart's per-source `latest` rows intentionally stay small and do not
    // repeat provenance for every metric. The session in the timeline carries
    // it, so attach that session-level provenance to the values it produced.
    timeline.forEach(function (entry) {
      var key = String(entry.source || "").toLowerCase();
      var model = models[key];
      if (!model) return;
      model.metrics.forEach(function (metric) {
        if (!metric.provenance && entry.provenance) metric.provenance = entry.provenance;
        if (!metric.session_id && entry.session_id) metric.session_id = entry.session_id;
        if (!metric.measured_at && entry.measured_at) metric.measured_at = entry.measured_at;
      });
    });

    // Dedupe metrics by namespaced key, newest first.
    Object.keys(models).forEach(function (key) {
      var seen = {};
      var list = sortMetrics(models[key].metrics).filter(function (m) {
        var dedupe = m.metric || ("value-" + m._order);
        if (seen[dedupe]) return false;
        seen[dedupe] = true;
        return true;
      });
      // Put the instrument's headline values first, then alphabetical.
      list.sort(function (a, b) {
        var da = parseDate(a.measured_at), db = parseDate(b.measured_at);
        if (da && db && da.getTime() !== db.getTime()) return db.getTime() - da.getTime();
        return a._order - b._order;
      });
      models[key].metrics = list;
    });
    return models;
  }

  function renderSourceCards(models, chart) {
    SOURCES.forEach(function (source) {
      var card = $('[data-source-card="' + source + '"]');
      if (!card) return;
      var model = models[source];
      var body = $('[data-role="metrics"]', card);
      var quality = $('[data-role="quality"]', card);
      var analysis = $('[data-role="analysis"]', card);
      var foot = $('[data-role="foot"]', card);
      if (!model || !model.metrics.length) {
        if (quality) quality.innerHTML = qualityBadge("");
        if (body) body.innerHTML = '<p class="muted small">No ' + esc(SOURCE_LABEL[source]) + " data yet.</p>";
        if (analysis) { analysis.textContent = ""; analysis.hidden = true; }
        if (foot) foot.innerHTML = "";
        return;
      }
      var latestQuality = model.quality || worstQuality(model.metrics) || "unverified";
      if (quality) quality.innerHTML = qualityBadge(latestQuality);
      if (body) {
        var visible = 6;
        var rows = model.metrics.map(function (metric, index) {
          var label = metricLabel(metric.metric);
          var when = metric.measured_at ? "<span>" + esc(fmtDate(metric.measured_at)) + "</span>" : "";
          return '<div class="metric-row' + (index >= visible ? " extra" : "") + '"' +
            (index >= visible ? ' hidden data-extra="1"' : "") + ">" +
            '<div class="metric-label">' + esc(label) +
            (metric.metric && metric.metric !== label ? '<span class="key">' + esc(metric.metric) + "</span>" : "") +
            "</div>" +
            '<div class="metric-value">' + metricValueHtml(metric) + "</div>" +
            '<div class="metric-sub">' + when + "</div>" +
            "</div>";
        }).join("");
        var more = model.metrics.length > visible
          ? '<button class="btn ghost sm" type="button" data-role="more">Show ' + (model.metrics.length - visible) + " more</button>"
          : "";
        body.innerHTML = rows + more;
        var moreBtn = $('[data-role="more"]', body);
        if (moreBtn) {
          moreBtn.addEventListener("click", function () {
            var expanded = moreBtn.getAttribute("data-expanded") === "1";
            $$(".metric-row.extra", body).forEach(function (row) { row.hidden = expanded; });
            moreBtn.setAttribute("data-expanded", expanded ? "0" : "1");
            moreBtn.textContent = expanded ? "Show " + (model.metrics.length - visible) + " more" : "Show fewer";
          });
        }
      }
      if (analysis) {
        var text = model.analysis || (chart.analysis_by_source && chart.analysis_by_source[source]) || "";
        analysis.textContent = text;
        analysis.hidden = !text;
      }
      var aiHost = $('[data-role="ai"]', card);
      if (aiHost) {
        if (model.ai_text) {
          var aiWhen = model.measured_at || (model.metrics[0] && model.metrics[0].measured_at);
          aiHost.hidden = false;
          aiHost.innerHTML = '<div class="ai-label"><span>AI text</span>' +
            (model.ai_model ? '<span class="model">' + esc(model.ai_model) + "</span>" : "") +
            (aiWhen ? "<span>" + esc(fmtDate(aiWhen)) + " " + esc(fmtTime(aiWhen)) + "</span>" : "") +
            "</div><p>" + esc(model.ai_text) + "</p>";
        } else {
          aiHost.hidden = true;
          aiHost.innerHTML = "";
        }
      }
      if (foot) {
        var when = model.measured_at || (model.metrics[0] && model.metrics[0].measured_at);
        var sessionId = model.session_id || (model.metrics[0] && model.metrics[0].session_id);
        var bits = [];
        if (when) bits.push("Latest " + fmtDate(when));
        if (model.sessions) bits.push(model.sessions + (model.sessions === 1 ? " session" : " sessions"));
        else if (sessionId) bits.push('<span title="' + esc(sessionId) + '">session ' + esc(shortId(sessionId)) + "</span>");
        foot.innerHTML = bits.join(" · ");
      }
    });
  }

  function timelineEntries(chart) {
    var raw = chart.timeline || chart.sessions || chart.events || [];
    var list = asArray(raw).map(function (entry) {
      if (!entry || typeof entry !== "object") return null;
      return {
        source: String(entry.source || "").toLowerCase(),
        session_id: entry.session_id || entry.session || entry.id || "",
        measured_at: entry.measured_at || entry.started_at || entry.timestamp || entry.completed_at || null,
        quality: entry.quality || entry.status || null,
        analysis: entry.analysis || entry.summary || "",
        ai_text: entry.ai_text || entry.ai || "",
        ai_model: entry.ai_model || entry.model || "",
        provenance: entry.provenance || null,
        metrics: metricArray(entry.metrics || entry.observations || entry.values || entry.metric_values || [], entry.source)
      };
    }).filter(Boolean);
    list.sort(function (a, b) {
      var da = parseDate(a.measured_at), db = parseDate(b.measured_at);
      if (da && db) return db.getTime() - da.getTime();
      if (da) return -1;
      if (db) return 1;
      return 0;
    });
    return list;
  }

  function renderTimeline(entries) {
    var host = $("#timeline");
    var empty = $("#timeline-empty");
    if (!host) return;
    if (!entries.length) {
      host.innerHTML = "";
      if (empty) empty.hidden = false;
      return;
    }
    if (empty) empty.hidden = true;
    host.innerHTML = entries.map(function (entry) {
      var values = entry.metrics.filter(function (m) { return m.value != null; }).slice(0, 5).map(function (m) {
        return "<span>" + esc(metricLabel(m.metric)) + " <b>" + fmtValue(m.value) + "</b>" +
          (m.unit ? " " + esc(m.unit) : "") + "</span>";
      }).join("");
      var more = entry.metrics.length > 5 ? '<span class="muted">+' + (entry.metrics.length - 5) + " more</span>" : "";
      var ai = entry.ai_text
        ? '<div class="ai-note"><div class="ai-label"><span>AI text</span>' +
          (entry.ai_model ? '<span class="model">' + esc(entry.ai_model) + "</span>" : "") +
          "<span>" + esc(fmtDate(entry.measured_at)) + " " + esc(fmtTime(entry.measured_at)) + "</span></div>" +
          "<p>" + esc(entry.ai_text) + "</p></div>"
        : "";
      var analysis = entry.analysis ? '<p class="analysis">' + esc(entry.analysis) + "</p>" : "";
      var date = parseDate(entry.measured_at);
      var q = String(entry.quality || "").toLowerCase();
      return '<li class="' + (q ? "is-" + q : "") + '">' +
        '<div class="when">' + (date ? esc(fmtDate(date)) : "<span class=\"muted\">date unknown</span>") +
        '<span class="time">' + (date ? esc(fmtTime(date)) : "") + "</span></div>" +
        '<div class="entry">' +
        '<div class="entry-head">' + srcTag(entry.source) + qualityBadge(entry.quality) +
        (entry.session_id ? '<span class="sid" title="' + esc(entry.session_id) + '">session ' + esc(shortId(entry.session_id)) + "</span>" : "") +
        "</div>" + analysis +
        (values ? '<div class="metrics-inline">' + values + more + "</div>" : "") + ai +
        "</div></li>";
    }).join("");
  }

  function renderChartHeader(patient, chart) {
    var name = patient.name || patient.display_name || "Unnamed patient";
    document.title = name + " — Mission Control";
    $("#chart-name").textContent = name;
    var intake = patient.intake && typeof patient.intake === "object" ? patient.intake : {};
    var dob = patient.dob || patient.date_of_birth || intake.dob;
    var age = patient.age != null ? patient.age : ageFromDob(dob);
    var meta = [];
    meta.push("<span><strong>DOB</strong> " + (dob ? esc(fmtDate(dob)) : "not recorded") + (age != null ? " · " + esc(age) + " y" : "") + "</span>");
    var sex = patient.sex || intake.sex || intake.gender;
    if (sex) meta.push("<span><strong>Sex</strong> " + esc(sex) + "</span>");
    meta.push("<span><strong>Status</strong> " + (patient.status ? '<span class="badge plain">' + esc(patient.status) + "</span>" : "—") + "</span>");
    meta.push("<span><strong>Patient id</strong> " + esc(patient.id || patient.patient_id || currentPatientId()) + "</span>");
    $("#chart-meta").innerHTML = meta.join("");
  }

  function patientPage() {
    markRail();
    var pid = currentPatientId();
    var refresh = $("#refresh-chart");
    var sync = $("#sync-patient");
    var exportLink = $("#export-chart");
    if (exportLink && pid) {
      exportLink.href = API + "/patients/" + encodeURIComponent(pid) + "/export.html";
    }

    function load() {
      clearNotice();
      return get(API + "/patients/" + encodeURIComponent(pid) + "/chart")
        .then(function (payload) {
          var chart = payload.chart || payload;
          var patient = chart.patient || payload.patient || {};
          var timeline = timelineEntries(chart);
          renderChartHeader(patient, chart);
          renderTimeline(timeline);
          renderSourceCards(cardModels(chart, timeline), chart);
          var stamp = $("#chart-stamp");
          if (stamp) stamp.textContent = "Loaded " + new Date().toLocaleTimeString() + " · " + timeline.length + " session" + (timeline.length === 1 ? "" : "s");
          if (sync) sync.disabled = false;
          return chart;
        })
        .catch(function (error) {
          if (error.status === 404) {
            pageNotice("bad", "Patient " + pid + " was not found in the LabFlow patient store.");
            $("#chart-name").textContent = "Unknown patient";
            $("#chart-meta").innerHTML = "";
            if (exportLink) {
              exportLink.removeAttribute("href");
              exportLink.classList.add("is-disabled");
              exportLink.setAttribute("aria-disabled", "true");
            }
          } else {
            pageNotice("bad", "Could not load this chart: " + error.message + ". The cards below are empty rather than guessed.");
          }
          var stamp = $("#chart-stamp");
          if (stamp) stamp.textContent = "Chart not loaded.";
          renderTimeline([]);
          renderSourceCards({}, {});
          if (sync) sync.disabled = true;
          throw error;
        });
    }

    if (refresh) {
      refresh.addEventListener("click", function () {
        refresh.disabled = true;
        load().catch(function () {}).then(function () { refresh.disabled = false; });
      });
    }
    if (sync) {
      sync.addEventListener("click", function () {
        sync.disabled = true;
        sync.textContent = "Syncing…";
        post(API + "/patients/" + encodeURIComponent(pid) + "/sync", {})
          .then(function (result) {
            var added = result.added != null ? result.added : (Array.isArray(result.observations) ? result.observations.length : 0);
            pageNotice("ok", "Sync added " + (numberOrNull(added) || 0) + " observation(s) for this patient.");
            return load();
          })
          .catch(function (error) {
            pageNotice("bad", "Sync failed: " + error.message);
          })
          .then(function () {
            sync.disabled = false;
            sync.textContent = "Sync now";
          });
      });
    }
    load().catch(function () {});
  }

  /* ================================================================
     Integrations
     ================================================================ */
  function integrationHint(item) {
    if (item.hint) return item.hint;
    if (item.reachable === false) return UNREACHABLE_HINT[item.source] || "Check that the app is installed and its data folder is readable.";
    return "Read-only adapter — Mission Control never writes into the source app.";
  }

  function renderIntegrations(items) {
    var tbody = $("#integrations-body");
    var empty = $("#integrations-empty");
    if (!tbody) return;
    if (!items.length) {
      tbody.innerHTML = "";
      if (empty) empty.hidden = false;
      return;
    }
    if (empty) empty.hidden = true;
    tbody.innerHTML = items.map(function (item) {
      var reachable = item.reachable;
      var known = reachable !== null && reachable !== undefined;
      var yes = reachable === true || String(reachable).toLowerCase() === "true";
      var reachClass = !known ? "unknown" : (yes ? "yes" : "no");
      var reachText = !known ? "not reported" : (yes ? "yes" : "no");
      var sessions = numberOrNull(item.sessions);
      return "<tr>" +
        '<td class="source">' + srcTag(item.source) + "</td>" +
        '<td class="path">' + (item.path ? "<code>" + esc(item.path) + "</code>" : '<span class="muted">not configured</span>') + "</td>" +
        '<td class="num"><span class="reach ' + reachClass + '"><i class="dot ' + (reachClass === "yes" ? "ok" : reachClass === "no" ? "bad" : "idle") + '" aria-hidden="true"></i>' + reachText + "</span></td>" +
        '<td class="num">' + (sessions == null ? "—" : esc(sessions)) + "</td>" +
        '<td class="when">' + (item.last_checked
          ? '<span title="' + esc(fmtWhen(item.last_checked)) + '">' + esc(fmtDate(item.last_checked)) + ", " + esc(fmtTime(item.last_checked)) + "</span>"
          : '<span class="muted">not checked yet</span>') + "</td>" +
        '<td><span class="hint">' + esc(integrationHint(item)) + "</span></td>" +
        "</tr>";
    }).join("");
  }

  function integrationsPage() {
    markRail();
    function load() {
      clearNotice();
      return get(API + "/integrations").then(function (payload) {
        renderIntegrations(integrationsList(payload));
        var stamp = $("#integrations-stamp");
        if (stamp) stamp.textContent = "Checked " + new Date().toLocaleTimeString();
      }).catch(function (error) {
        pageNotice("bad", "Could not read integration status: " + error.message + ". No source is shown as connected without a fresh check.");
        var stamp = $("#integrations-stamp");
        if (stamp) stamp.textContent = "not checked";
        renderIntegrations([]);
        var empty = $("#integrations-empty");
        if (empty) { empty.hidden = false; empty.textContent = "Integration status unavailable."; }
      });
    }
    var again = $("#refresh-integrations");
    if (again) again.addEventListener("click", function () { load(); });
    load();
  }

  /* ================================================================
     InBody — manual body composition
     ================================================================ */
  var INBODY_FIELDS = [
    "weight_kg", "skeletal_muscle_kg", "body_fat_kg",
    "body_fat_pct", "visceral_fat", "lean_mass_kg", "bmi"
  ];

  function inbodyPage() {
    markRail();
    var form = $("#inbody-form");
    var select = $("#patient-select");
    var status = $("#inbody-status");
    var submit = $("#inbody-submit");
    var params = new URLSearchParams(location.search);
    var wanted = params.get("patient") || "";

    get(API + "/patients").then(function (payload) {
      var patients = patientList(payload);
      if (!patients.length) {
        select.innerHTML = '<option value="">No patients — create one in LabFlow first</option>';
        select.disabled = true;
        if (submit) submit.disabled = true;
        $("#inbody-empty").hidden = false;
        return;
      }
      $("#inbody-empty").hidden = true;
      select.disabled = false;
      if (submit) submit.disabled = false;
      select.innerHTML = patients.map(function (p) {
        var id = p.id || p.patient_id || p.subject_id || "";
        var label = (p.name || "Unnamed patient") + (p.dob ? " · " + p.dob : "");
        return '<option value="' + esc(id) + '"' + (String(id) === wanted ? " selected" : "") + ">" + esc(label) + "</option>";
      }).join("");
    }).catch(function (error) {
      select.innerHTML = '<option value="">Patient list unavailable</option>';
      select.disabled = true;
      if (submit) submit.disabled = true;
      pageNotice("bad", "Could not load patients: " + error.message + ". Manual entry needs a patient from LabFlow.");
    });

    if (!form) return;
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var pid = select.value;
      if (!pid) {
        status.textContent = "Choose a patient first.";
        status.className = "form-status bad";
        return;
      }
      var measuredAt = $("#measured_at").value;
      if (!measuredAt) {
        status.textContent = "Date and time of the measurement is required.";
        status.className = "form-status bad";
        return;
      }
      var parsedWhen = new Date(measuredAt);
      var body = { measured_at: isNaN(parsedWhen.getTime()) ? measuredAt : parsedWhen.toISOString() };
      var filled = 0;
      INBODY_FIELDS.forEach(function (field) {
        var input = $("#" + field);
        var value = input && input.value !== "" ? numberOrNull(input.value) : null;
        if (value != null) { body[field] = value; filled += 1; }
      });
      if (!filled) {
        status.textContent = "Enter at least one body-composition value.";
        status.className = "form-status bad";
        return;
      }
      submit.disabled = true;
      status.textContent = "Saving…";
      status.className = "form-status";
      post(API + "/patients/" + encodeURIComponent(pid) + "/inbody", body).then(function (result) {
        var n = result.added != null ? result.added : filled;
        var received = result.received != null ? result.received : filled;
        if (n === 0 && received > 0) {
          status.innerHTML = "No new values — this entry is already in the record (" + esc(received) + " received, 0 added). " +
            '<a href="/mc/patient/' + encodeURIComponent(pid) + '">Open the chart</a>.';
        } else {
          status.innerHTML = "Saved " + esc(n) + " value(s) as manual entry. " +
            '<a href="/mc/patient/' + encodeURIComponent(pid) + '">Open the chart</a> to check them against the printout.';
        }
        status.className = "form-status ok";
      }).catch(function (error) {
        status.textContent = "Not saved: " + error.message;
        status.className = "form-status bad";
      }).then(function () {
        submit.disabled = false;
      });
    });
  }

  /* -------------------------------------------------- boot */
  document.addEventListener("DOMContentLoaded", function () {
    var page = document.body.getAttribute("data-page");
    if (page === "overview") overviewPage();
    else if (page === "patient") patientPage();
    else if (page === "integrations") integrationsPage();
    else if (page === "inbody") inbodyPage();
  });
})();
