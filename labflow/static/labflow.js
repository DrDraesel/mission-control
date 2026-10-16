/* LabFlow web UI — plain JS, textContent only (no innerHTML with data). */
'use strict';

(function () {
  var state = { patients: [], currentId: null, view: null, probes: null };

  /* ------------------------------------------------------------ tiny DOM helpers */
  function $(sel) { return document.querySelector(sel); }
  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text !== undefined && text !== null) { node.textContent = String(text); }
    return node;
  }
  function clear(node) { while (node.firstChild) { node.removeChild(node.firstChild); } }
  function show(node, visible) {
    if (!node) { return; }
    node.classList[visible ? 'remove' : 'add']('hidden');
  }
  var toastTimer = null;
  function toast(message, isError) {
    var box = $('#toast');
    box.textContent = message;
    box.classList[isError ? 'add' : 'remove']('error');
    show(box, true);
    if (toastTimer) { clearTimeout(toastTimer); }
    toastTimer = setTimeout(function () { show(box, false); }, 3600);
  }
  function setConn(ok, detail) {
    var pill = $('#conn-pill');
    pill.textContent = ok ? 'local · connected' : ('offline' + (detail ? ' — ' + detail : ''));
    pill.classList[ok ? 'add' : 'remove']('ok');
    pill.classList[ok ? 'remove' : 'add']('bad');
  }

  /* ------------------------------------------------------------ API */
  function api(path, options) {
    var opts = options || {};
    var init = { method: opts.method || 'GET', headers: { 'Accept': 'application/json' } };
    if (opts.body !== undefined) {
      init.headers['Content-Type'] = 'application/json';
      init.body = JSON.stringify(opts.body);
    }
    return fetch(path, init).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (doc) {
        if (!response.ok || doc.ok === false) {
          var message = doc.error || doc.detail || ('HTTP ' + response.status);
          var err = new Error(typeof message === 'string' ? message : JSON.stringify(message));
          err.status = response.status;
          throw err;
        }
        setConn(true, '');
        return doc;
      });
    }).catch(function (err) {
      if (!err.status) { setConn(false, err.message); }
      throw err;
    });
  }

  function run(action, okMessage) {
    return action.then(function (result) {
      if (okMessage) { toast(okMessage, false); }
      return result;
    }).catch(function (err) {
      toast(err.message || 'request failed', true);
    });
  }

  /* ------------------------------------------------------------ patients list */
  function loadPatients(selectId) {
    return run(api('/api/patients').then(function (doc) {
      state.patients = doc.patients || [];
      renderPatients();
      var wanted = selectId !== undefined ? selectId : state.currentId;
      if (wanted !== null && wanted !== undefined) {
        var exists = state.patients.some(function (p) { return String(p.id) === String(wanted); });
        if (exists) { return selectPatient(wanted); }
      }
      return null;
    }));
  }

  function renderPatients() {
    var list = $('#patients-list');
    clear(list);
    show($('#patients-empty'), state.patients.length === 0);
    state.patients.forEach(function (p) {
      var li = el('li');
      var btn = el('button', 'patient-btn');
      if (state.currentId !== null && String(p.id) === String(state.currentId)) { btn.classList.add('active'); }
      btn.type = 'button';
      btn.dataset.patientId = String(p.id);
      btn.appendChild(el('span', 'name', p.name || ('Patient ' + p.id)));
      var bits = [];
      if (p.created_at) { bits.push('created ' + p.created_at); }
      if (p.progress && p.progress.total) {
        bits.push('progress ' + (p.progress.done || 0) + '/' + p.progress.total);
      }
      if (bits.length) { btn.appendChild(el('span', 'sub', bits.join(' · '))); }
      btn.addEventListener('click', function () { selectPatient(p.id); });
      li.appendChild(btn);
      list.appendChild(li);
    });
  }

  function selectPatient(id) {
    state.currentId = id;
    state.probes = null;
    renderPatients();
    return loadPatient();
  }

  /* ------------------------------------------------------------ patient view */
  function loadPatient() {
    if (state.currentId === null || state.currentId === undefined) {
      show($('#patient-view'), false);
      show($('#patient-empty'), true);
      return Promise.resolve();
    }
    return run(api('/api/patients/' + encodeURIComponent(state.currentId)).then(function (doc) {
      state.view = doc;
      renderPatient();
    }));
  }

  function stationFields(station) {
    var capture = station && station.capture ? station.capture : {};
    var fields = capture.fields || [];
    return fields.map(function (f) {
      return (typeof f === 'string') ? { name: f } : (f || {});
    }).filter(function (f) { return f.name; });
  }

  function renderPatient() {
    var view = state.view;
    if (!view || !view.patient) { return; }
    show($('#patient-empty'), false);
    show($('#patient-view'), true);

    var patient = view.patient;
    $('#pv-name').textContent = patient.name || ('Patient ' + patient.id);
    var meta = [];
    if (patient.id !== undefined) { meta.push('id ' + patient.id); }
    var intake = patient.intake || {};
    if (intake.dob) { meta.push('dob ' + intake.dob); }
    if (intake.contact) { meta.push('contact ' + intake.contact); }
    if (intake.medical_flags) { meta.push('flags: ' + intake.medical_flags); }
    $('#pv-meta').textContent = meta.join(' · ') || 'no intake details';

    var progress = view.progress || {};
    var total = progress.total || (view.steps ? view.steps.length : 0);
    var done = progress.done || 0;
    var percent = progress.percent;
    if (percent === undefined || percent === null) {
      percent = total ? Math.round((done / total) * 100) : 0;
    }
    $('#progress-fill').style.width = Math.max(0, Math.min(100, percent)) + '%';
    $('#progress-text').textContent = done + ' / ' + total + ' stations complete';

    renderNext(view);
    renderStations(view);
    renderCapture(view);
    renderMeasurements(patient);
    renderProbes();
    refreshListEntry();
  }

  // keep the sidebar progress line in sync after actions (no extra request)
  function refreshListEntry() {
    if (!state.view || !state.view.patient) { return; }
    var pid = String(state.view.patient.id);
    var buttons = document.querySelectorAll('.patient-btn');
    Array.prototype.forEach.call(buttons, function (btn) {
      if (String(btn.dataset.patientId) !== pid) { return; }
      var sub = btn.querySelector('.sub');
      if (!sub) { return; }
      var progress = state.view.progress || {};
      var bits = [];
      if (state.view.patient.created_at) { bits.push('created ' + state.view.patient.created_at); }
      if (progress.total) { bits.push('progress ' + (progress.done || 0) + '/' + progress.total); }
      sub.textContent = bits.join(' · ');
    });
  }

  function renderNext(view) {
    var next = view.next;
    var banner = $('#next-banner');
    var launch = $('#next-launch');
    clear(launch);
    show(launch, false);
    if (!next) {
      $('#next-name').textContent = 'Flow complete';
      $('#next-desc').textContent = '';
      $('#next-instruction').textContent = view.next_instruction || '';
      show($('#next-flow-done'), true);
      return;
    }
    show($('#next-flow-done'), false);
    $('#next-name').textContent = next.name || next.station_id || 'Next step';
    $('#next-desc').textContent = next.description || '';
    $('#next-instruction').textContent = view.next_instruction || next.instruction || '';
    renderLaunch(next.launch, launch);
  }

  function renderLaunch(launchInfo, container) {
    // core Station.launch shape: {type: 'url'|'command'|'manual', value: str}
    if (!launchInfo || !launchInfo.type || launchInfo.type === 'manual') { return; }
    var value = launchInfo.value || launchInfo.url || launchInfo.command || '';
    show(container, true);
    if (launchInfo.type === 'url' && value) {
      var open = el('button', 'btn primary', 'Open instrument app');
      open.type = 'button';
      open.addEventListener('click', function () { window.open(value, '_blank', 'noopener'); });
      container.appendChild(open);
      container.appendChild(el('span', 'url', value));
    } else if (launchInfo.type === 'command' && value) {
      container.appendChild(el('span', 'url', 'Run this command:'));
      container.appendChild(el('code', null, value));
      var copy = el('button', 'btn small', 'Copy command');
      copy.type = 'button';
      copy.addEventListener('click', function () {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(value).then(
            function () { toast('command copied', false); },
            function () { toast('copy failed — select the text manually', true); });
        } else {
          toast('clipboard unavailable — select the text manually', true);
        }
      });
      container.appendChild(copy);
    }
  }

  function stateLabel(value) {
    return String(value || 'pending').replace(/_/g, ' ');
  }

  function renderStations(view) {
    var list = $('#station-list');
    clear(list);
    var steps = view.steps || [];
    steps.forEach(function (step, index) {
      var li = el('li');
      if (view.current && String(view.current.station_id) === String(step.station_id)) {
        li.classList.add('current');
      }
      li.appendChild(el('span', 'station-num', (index + 1) + '.'));

      var body = el('div', 'station-body');
      var nameLine = el('div', 'name');
      nameLine.appendChild(document.createTextNode(step.name || step.station_id || 'station'));
      nameLine.appendChild(el('span', 'state-chip ' + (step.state || 'pending'), stateLabel(step.state)));
      body.appendChild(nameLine);
      if (step.description) { body.appendChild(el('div', 'desc', step.description)); }
      if (step.notes) { body.appendChild(el('div', 'note', 'note: ' + step.notes)); }
      if (step.step_notes) { body.appendChild(el('div', 'note', 'step notes: ' + step.step_notes)); }
      li.appendChild(body);

      var actions = el('div', 'station-actions');
      var stateValue = step.state || 'pending';
      var stationId = step.station_id;

      if (stateValue === 'pending') {
        actions.appendChild(stepButton('Begin', 'small', function () {
          return run(api(patientPath('/begin'), { method: 'POST', body: { station_id: stationId } }), 'station started')
            .then(loadPatient);
        }));
      }
      if (stateValue === 'pending' || stateValue === 'in_progress') {
        actions.appendChild(stepButton('Done', 'small ok', function () {
          return doneForStation(stationId, stateValue);
        }));
        actions.appendChild(stepButton('Skip', 'small warn', function () {
          return skipStep(stationId);
        }));
      }
      if (stateValue === 'done' || stateValue === 'skipped') {
        actions.appendChild(stepButton('Redo', 'small', function () {
          return run(api(patientPath('/redo'), { method: 'POST', body: { station_id: stationId } }), 'station reopened')
            .then(loadPatient);
        }));
      }
      li.appendChild(actions);
      list.appendChild(li);
    });
  }

  function stepButton(label, className, handler) {
    var btn = el('button', 'btn ' + className, label);
    btn.type = 'button';
    btn.addEventListener('click', handler);
    return btn;
  }

  function patientPath(suffix) {
    return '/api/patients/' + encodeURIComponent(state.currentId) + suffix;
  }

  function currentStation() {
    if (!state.view) { return null; }
    if (state.view.current) { return state.view.current; }
    if (state.view.next) { return state.view.next; }
    return null;
  }

  function captureValues() {
    var values = {};
    var inputs = document.querySelectorAll('#capture-fields [data-field]');
    Array.prototype.forEach.call(inputs, function (input) {
      var raw = input.value;
      if (raw === '') { return; }
      var value = raw;
      if (input.dataset.numeric === '1') {
        var num = Number(raw);
        if (!isNaN(num)) { value = num; }
      }
      values[input.dataset.field] = value;
    });
    return values;
  }

  function doneForStation(stationId, stateValue) {
    var body = { notes: $('#capture-notes').value || '' };
    var station = currentStation();
    var isCurrent = station && String(station.station_id) === String(stationId);
    if (isCurrent && stateValue !== 'done') {
      body.results = captureValues();
      body.station_id = stationId;
    } else if (stateValue === 'pending') {
      body.station_id = stationId;
    }
    return run(api(patientPath('/complete'), { method: 'POST', body: body }), 'step completed')
      .then(function () { $('#capture-notes').value = ''; })
      .then(loadPatient);
  }

  function skipStep(stationId) {
    var reason = window.prompt('Reason for skipping this station?', '');
    if (reason === null) { return Promise.resolve(); }
    return run(api(patientPath('/skip'), { method: 'POST', body: { reason: reason, station_id: stationId } }),
      'station skipped').then(loadPatient);
  }

  function renderCapture(view) {
    var station = view.current || view.next;
    var fieldsBox = $('#capture-fields');
    clear(fieldsBox);
    $('#capture-for').textContent = station ? ('current: ' + (station.name || station.station_id)) : 'no active station';
    if (!station) {
      fieldsBox.appendChild(el('p', 'muted', 'No active station — begin the next step first.'));
      return;
    }
    var fields = stationFields(station);
    if (!fields.length) {
      fieldsBox.appendChild(el('p', 'muted', 'This station has no manual capture fields.'));
      return;
    }
    fields.forEach(function (field) {
      var wrap = el('div');
      var label = el('label', null, field.label || field.name);
      label.setAttribute('for', 'cf-' + field.name);
      wrap.appendChild(label);
      var input = document.createElement('input');
      input.id = 'cf-' + field.name;
      input.type = 'text';
      input.dataset.field = field.name;
      if (field.unit) { input.placeholder = 'unit: ' + field.unit; }
      var kind = String(field.type || '').toLowerCase();
      if (kind === 'number' || kind === 'numeric' || kind === 'float' || kind === 'int') {
        input.dataset.numeric = '1';
      }
      wrap.appendChild(input);
      fieldsBox.appendChild(wrap);
    });
  }

  function renderMeasurements(patient) {
    var body = $('#measure-body');
    clear(body);
    var rows = (patient && patient.measurements) || [];
    show($('#measure-empty'), rows.length === 0);
    rows.slice().reverse().forEach(function (m) {
      var tr = el('tr');
      tr.appendChild(el('td', null, m.metric || ''));
      tr.appendChild(el('td', null, m.value === undefined ? '' : m.value));
      tr.appendChild(el('td', null, m.unit || ''));
      tr.appendChild(el('td', null, m.source || ''));
      tr.appendChild(el('td', null, m.at || m.recorded_at || m.ts || ''));
      body.appendChild(tr);
    });
  }

  /* ------------------------------------------------------------ probes */
  function renderProbes() {
    var list = $('#probe-list');
    clear(list);
    if (!state.probes) { return; }
    var apps = (state.probes.apps) || {};
    var order = ['bertec', 'runtrack', 'neurosync'];
    order.forEach(function (app) {
      var summary = apps[app];
      if (!summary) { return; }
      var li = el('li');
      li.appendChild(el('span', 'probe-app', summary.app || app));
      li.appendChild(el('span', 'pill ' + (summary.available ? 'ok' : 'bad'),
        summary.available ? 'online' : 'offline'));
      var detail = el('div');
      if (summary.available) {
        var bits = [];
        if (summary.count !== undefined && summary.count !== null) { bits.push(summary.count + ' session(s)'); }
        if (summary.note) { bits.push(summary.note); }
        detail.appendChild(el('div', 'probe-latest', bits.join(' · ') || 'available'));
        if (summary.latest) {
          detail.appendChild(el('div', 'probe-latest', 'latest: ' + JSON.stringify(summary.latest)));
        }
      } else {
        detail.appendChild(el('div', 'probe-err', summary.error || 'unavailable'));
      }
      li.appendChild(detail);
      var actions = el('div', 'station-actions');
      if (summary.available && summary.latest && summary.latest.id !== undefined && summary.latest.id !== null) {
        actions.appendChild(stepButton('Link latest', 'small primary', function () {
          return run(api(patientPath('/link'), {
            method: 'POST',
            body: { app: summary.app || app, session_id: summary.latest.id }
          }), 'session linked to this patient').then(loadPatient);
        }));
      }
      li.appendChild(actions);
      list.appendChild(li);
    });
    if (!Object.keys(apps).length) {
      list.appendChild(el('li', 'muted', 'No probe results yet — press “Check results”.'));
    }
  }

  /* ------------------------------------------------------------ wiring */
  function submitNewPatient(event) {
    event.preventDefault();
    var nameInput = $('#np-name');
    var name = nameInput.value.trim();
    if (!name) { return; }
    var intake = {
      dob: $('#np-dob').value.trim(),
      contact: $('#np-contact').value.trim(),
      training_history: $('#np-history').value.trim(),
      medical_flags: $('#np-flags').value.trim(),
      medications: $('#np-meds').value.trim(),
      goals: $('#np-goals').value.trim()
    };
    Object.keys(intake).forEach(function (key) { if (!intake[key]) { delete intake[key]; } });
    api('/api/patients', { method: 'POST', body: { name: name, intake: intake } })
      .then(function (doc) {
        show($('#np-error'), false);
        $('#new-patient-form').reset();
        show($('#new-patient-form'), false);
        toast('patient created', false);
        return loadPatients(doc.patient ? doc.patient.id : undefined);
      })
      .catch(function (err) {
        var box = $('#np-error');
        box.textContent = err.message || 'could not create patient';
        show(box, true);
      });
  }

  function wire() {
    $('#new-patient-btn').addEventListener('click', function () {
      var form = $('#new-patient-form');
      show(form, form.classList.contains('hidden'));
    });
    $('#np-cancel').addEventListener('click', function () {
      show($('#new-patient-form'), false);
    });
    $('#new-patient-form').addEventListener('submit', submitNewPatient);
    $('#refresh-btn').addEventListener('click', function () { loadPatient(); });

    $('#capture-form').addEventListener('submit', function (event) {
      event.preventDefault();
      var station = currentStation();
      if (!station) { toast('no active station', true); return; }
      doneForStation(station.station_id, station.state || 'pending');
    });
    $('#capture-skip').addEventListener('click', function () {
      var station = currentStation();
      if (station) { skipStep(station.station_id); }
    });
    $('#capture-redo').addEventListener('click', function () {
      var station = currentStation();
      if (!station) { toast('no active station', true); return; }
      run(api(patientPath('/redo'), { method: 'POST', body: { station_id: station.station_id } }),
        'station reopened').then(loadPatient);
    });

    $('#probe-btn').addEventListener('click', function () {
      if (state.currentId === null) { return; }
      var btn = $('#probe-btn');
      btn.disabled = true;
      api(patientPath('/probes')).then(function (doc) {
        state.probes = doc.probes || doc;
        renderProbes();
        toast('lab results checked', false);
      }).catch(function (err) {
        toast(err.message || 'probe failed', true);
      }).then(function () { btn.disabled = false; });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    wire();
    loadPatients();
  });
})();
