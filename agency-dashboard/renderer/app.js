/* ============================================================
   Agency Dashboard — local CRM + outreach toolkit
   All data lives in this computer's localStorage (private to you).
   ============================================================ */

const STORE_KEY = 'agencyData_v1';

/* Show any load-time error on screen instead of failing silently. */
window.addEventListener('error', function (e) {
  var b = document.getElementById('fatalBanner');
  if (!b) {
    b = document.createElement('div');
    b.id = 'fatalBanner';
    b.style.cssText = 'position:fixed;top:0;left:0;right:0;background:#dc2626;color:#fff;padding:10px 16px;font:13px -apple-system,sans-serif;z-index:9999';
    (document.body || document.documentElement).appendChild(b);
  }
  b.textContent = 'App error: ' + (e.message || e.error || 'unknown') + '  —  copy this and tell Claude.';
});

/* ---------- Safe storage (keeps working even if localStorage is blocked,
   which Safari does when you open a file directly) ---------- */
var memStore = {};
var storageWorks = true;
function safeGet(k) { try { return localStorage.getItem(k); } catch (e) { storageWorks = false; return (k in memStore) ? memStore[k] : null; } }
function safeSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { storageWorks = false; memStore[k] = v; } }
function safeRemove(k) { try { localStorage.removeItem(k); } catch (e) { delete memStore[k]; } }

/* ---------- Seed leads (your Newton, MA starter list) ---------- */
function seedLeads() {
  const raw = [
    ['Salvi\'s Barber Shop', 'Barbershop', '', '140 Adams St, Newton 02458', 'Likely none (Booksy only)'],
    ['Neighborhood Barbers', 'Barbershop', '', '286 Centre St, Newton 02458', 'Likely none (Squire only)'],
    ['Centre Barbershop Hairstyling', 'Barbershop', '', '212 Sumner St, Newton 02459', 'Likely none (Fresha only)'],
    ['Nail It', 'Nail Salon', '', '325 Walnut St, Newton 02460', 'Likely none (Fresha only)'],
    ['Joe\'s Barber Shop', 'Barbershop', '', 'Newton (verify)', 'Check on Maps'],
    ['Mike\'s Classic Barber Shop', 'Barbershop', '', 'Newton (verify)', 'Check on Maps'],
    ['Plush Nail & Spa', 'Nail Salon', '', 'Newton (verify)', 'Check on Maps'],
    ['Unique Nails', 'Nail Salon', '', 'Newton (verify)', 'Check on Maps'],
    ['David Sauro Landscaping', 'Landscaping', '', 'Newton (verify)', 'Check on Maps'],
    ['Lynch Landscape & Tree Service', 'Landscaping', '', 'Newton (verify)', 'Check on Maps'],
    ['LAC Landscaping & Construction', 'Landscaping', '', 'Newton (verify)', 'Check on Maps'],
    ['Triple E Paving & Landscaping', 'Landscaping', '', 'Newton (verify)', 'Check on Maps']
  ];
  return raw.map((r) => ({
    id: uid(),
    business: r[0], niche: r[1], phone: r[2], address: r[3],
    website: 'No', status: 'New', lastTouch: '', notes: r[4]
  }));
}

function defaultSettings() {
  return { yourName: '', company: '', defaultBuild: 250, defaultMonthly: 50 };
}

/* ---------- Data load / save ---------- */
let data = load();

function load() {
  const raw = safeGet(STORE_KEY);
  if (raw) {
    try {
      const p = JSON.parse(raw);
      p.clients = p.clients || [];
      p.leads = p.leads || [];
      p.settings = Object.assign(defaultSettings(), p.settings || {});
      return p;
    } catch (e) { /* fall through to fresh */ }
  }
  const fresh = { clients: [], leads: seedLeads(), settings: defaultSettings() };
  safeSet(STORE_KEY, JSON.stringify(fresh));
  return fresh;
}

function save() {
  safeSet(STORE_KEY, JSON.stringify(data));
  renderSideStats();
}

/* ---------- Utilities ---------- */
function uid() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 7); }
function todayISO() { return new Date().toISOString().slice(0, 10); }
function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
function daysSince(dateStr) {
  if (!dateStr) return null;
  const then = new Date(dateStr + 'T00:00:00');
  const now = new Date(todayISO() + 'T00:00:00');
  return Math.round((now - then) / 86400000);
}
function money(n) { return '$' + (Number(n) || 0).toLocaleString(); }

function toast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toast._t);
  toast._t = setTimeout(() => t.classList.remove('show'), 1900);
}

function copy(text) {
  navigator.clipboard.writeText(text).then(
    () => toast('Copied to clipboard'),
    () => toast('Copy failed — select and copy manually')
  );
}

function download(filename, content, mime) {
  const blob = new Blob([content], { type: mime || 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/* ---------- Navigation ---------- */
const RENDERERS = {
  dashboard: renderDashboard,
  clients: renderClients,
  leads: renderLeads,
  scripts: renderScripts,
  messages: renderMessages,
  demo: renderDemo,
  settings: renderSettings
};

function showTab(id) {
  document.querySelectorAll('.nav-item').forEach((b) => b.classList.toggle('active', b.dataset.tab === id));
  document.querySelectorAll('.tab').forEach((s) => s.classList.toggle('active', s.id === 'tab-' + id));
  if (RENDERERS[id]) RENDERERS[id]();
}

document.querySelectorAll('.nav-item').forEach((b) => {
  b.addEventListener('click', () => showTab(b.dataset.tab));
});

/* ---------- Client recommendation logic ---------- */
function clientRec(c) {
  const cad = Number(c.cadence) || 30;
  const d = daysSince(c.lastContact);
  if (d === null) return { level: 'warn', text: 'No contact logged yet' };
  if (d >= cad) return { level: 'urgent', text: `Reach out now — ${d} days since last contact` };
  if (d >= cad - 7) return { level: 'warn', text: `Reach out soon — ${d} days` };
  return { level: 'good', text: `On track — ${d} days ago` };
}

/* ============================================================
   MODAL (generic form builder)
   ============================================================ */
function openModal(title, fields, values, onSubmit) {
  const root = document.getElementById('modalRoot');
  const inputs = fields.map((f) => {
    const v = values && values[f.key] != null ? values[f.key] : (f.default != null ? f.default : '');
    const cls = f.full ? 'field full' : 'field';
    if (f.type === 'select') {
      const opts = f.options.map((o) => `<option value="${esc(o)}" ${String(o) === String(v) ? 'selected' : ''}>${esc(o)}</option>`).join('');
      return `<div class="${cls}"><label>${esc(f.label)}</label><select data-key="${f.key}">${opts}</select></div>`;
    }
    if (f.type === 'textarea') {
      return `<div class="${cls}"><label>${esc(f.label)}</label><textarea data-key="${f.key}" placeholder="${esc(f.placeholder || '')}">${esc(v)}</textarea>${f.hint ? `<div class="hint">${esc(f.hint)}</div>` : ''}</div>`;
    }
    const type = f.type || 'text';
    return `<div class="${cls}"><label>${esc(f.label)}</label><input data-key="${f.key}" type="${type}" value="${esc(v)}" placeholder="${esc(f.placeholder || '')}" />${f.hint ? `<div class="hint">${esc(f.hint)}</div>` : ''}</div>`;
  }).join('');

  root.innerHTML = `
    <div class="modal">
      <h3>${esc(title)}</h3>
      <div class="form-grid">${inputs}</div>
      <div class="modal-foot">
        <button class="btn" id="mCancel">Cancel</button>
        <button class="btn primary" id="mSave">Save</button>
      </div>
    </div>`;
  root.classList.add('open');

  function close() { root.classList.remove('open'); root.innerHTML = ''; }
  document.getElementById('mCancel').onclick = close;
  root.onclick = (e) => { if (e.target === root) close(); };
  document.getElementById('mSave').onclick = () => {
    const obj = {};
    root.querySelectorAll('[data-key]').forEach((el) => { obj[el.dataset.key] = el.value.trim(); });
    onSubmit(obj);
    close();
  };
}

/* ============================================================
   DASHBOARD
   ============================================================ */
function renderDashboard() {
  const clients = data.clients;
  const leads = data.leads;
  const mrr = clients.reduce((s, c) => s + (Number(c.monthlyFee) || 0), 0);
  const toCall = leads.filter((l) => ['New', 'Researching', 'Called - no answer'].includes(l.status));
  const dueFollowups = clients.filter((c) => {
    const r = clientRec(c);
    return r.level === 'urgent' || r.level === 'warn';
  });

  const followupRows = dueFollowups.length
    ? dueFollowups.map((c) => {
        const r = clientRec(c);
        return `<tr>
          <td><span class="biz">${esc(c.business)}</span><div class="muted">${esc(c.contact || '')} ${c.phone ? '· ' + esc(c.phone) : ''}</div></td>
          <td><span class="badge ${r.level}">${esc(r.text)}</span></td>
          <td style="text-align:right">
            <button class="btn sm" onclick="logContact('${c.id}')">Log contact today</button>
            <button class="btn sm primary" onclick="goMessageForClient('${c.id}')">Message</button>
          </td></tr>`;
      }).join('')
    : `<tr><td colspan="3" class="empty">No follow-ups due. Nice and tidy.</td></tr>`;

  const callRows = toCall.length
    ? toCall.slice(0, 8).map((l) => `<tr>
        <td><span class="biz">${esc(l.business)}</span><div class="muted">${esc(l.niche)} · ${esc(l.address || '')}</div></td>
        <td>${esc(l.phone || '—')}</td>
        <td style="text-align:right">
          <button class="btn sm" onclick="goScriptForLead('${l.id}')">Make script</button>
          <button class="btn sm primary" onclick="showTab('leads')">Open</button>
        </td></tr>`).join('')
    : `<tr><td colspan="3" class="empty">No leads queued. Add some in the Leads tab.</td></tr>`;

  document.getElementById('tab-dashboard').innerHTML = `
    <div class="page-head">
      <div><h1>Dashboard</h1><p>Everything you need for the agency, in one place.</p></div>
      <div class="btn-row">
        <button class="btn" onclick="showTab('leads')">+ Add lead</button>
        <button class="btn primary" onclick="showTab('clients')">+ Add client</button>
      </div>
    </div>

    <div class="grid cards-3" style="margin-bottom:18px">
      <div class="stat"><div class="label">Active clients</div><div class="value">${clients.length}</div><div class="sub">paying customers</div></div>
      <div class="stat"><div class="label">Monthly recurring</div><div class="value">${money(mrr)}</div><div class="sub">from retainers</div></div>
      <div class="stat"><div class="label">Leads to call</div><div class="value">${toCall.length}</div><div class="sub">in your pipeline</div></div>
      <div class="stat"><div class="label">Follow-ups due</div><div class="value">${dueFollowups.length}</div><div class="sub">clients to check on</div></div>
    </div>

    <div class="panel">
      <h2>Add leads from a Google Maps CSV <span class="count">— keeps only the ones with no website</span></h2>
      <p style="color:var(--muted);font-size:13px;margin-bottom:12px">Export a Google Maps search (e.g. “landscapers near Newton”) as a CSV, then upload it here. The app keeps only businesses <b>without a website</b> and adds them to your Leads — skipping any duplicates and your existing list.</p>
      <div class="btn-row">
        <button class="btn primary" onclick="document.getElementById('csvFile').click()">Upload CSV</button>
        <input id="csvFile" type="file" accept=".csv,text/csv" style="display:none" onchange="importLeadsCSV(this)">
      </div>
      <div id="csvResult" style="margin-top:10px;font-size:13px;color:var(--muted)"></div>
    </div>

    <div class="panel">
      <h2>Follow-ups due <span class="count">— who to reach out to</span></h2>
      <table><thead><tr><th>Client</th><th>Recommendation</th><th></th></tr></thead><tbody>${followupRows}</tbody></table>
    </div>

    <div class="panel">
      <h2>Next leads to call <span class="count">— ${toCall.length} queued</span></h2>
      <table><thead><tr><th>Business</th><th>Phone</th><th></th></tr></thead><tbody>${callRows}</tbody></table>
    </div>`;
}

/* ============================================================
   CLIENTS
   ============================================================ */
function clientFields() {
  return [
    { key: 'business', label: 'Business name', placeholder: 'e.g. Centre Barbershop' },
    { key: 'niche', label: 'Type of business', placeholder: 'Barbershop' },
    { key: 'contact', label: 'Contact name', placeholder: 'Owner / manager' },
    { key: 'phone', label: 'Phone', placeholder: '(617) 555-0123' },
    { key: 'email', label: 'Email', type: 'email' },
    { key: 'address', label: 'Address' },
    { key: 'buildFee', label: 'Build fee ($)', type: 'number', default: data.settings.defaultBuild },
    { key: 'monthlyFee', label: 'Monthly fee ($)', type: 'number', default: data.settings.defaultMonthly },
    { key: 'startDate', label: 'Client since', type: 'date', default: todayISO() },
    { key: 'lastContact', label: 'Last contacted', type: 'date', default: todayISO() },
    { key: 'cadence', label: 'Check in every (days)', type: 'number', default: 30, hint: 'How often you want to reach out' },
    { key: 'status', label: 'Status', type: 'select', options: ['Active', 'Building site', 'Paused', 'Churned'], default: 'Active' },
    { key: 'notes', label: 'Notes', type: 'textarea', full: true, placeholder: 'What they care about, what you built, etc.' }
  ];
}

function renderClients() {
  const list = data.clients.length
    ? data.clients.map((c) => {
        const r = clientRec(c);
        return `<div class="client-card">
          <div class="ci-main">
            <div class="ci-title">${esc(c.business)} <span class="badge neutral">${esc(c.niche || '')}</span></div>
            <div class="ci-meta">${esc(c.contact || 'No contact')} ${c.phone ? '· ' + esc(c.phone) : ''} ${c.email ? '· ' + esc(c.email) : ''}</div>
            <div class="ci-meta">${money(c.monthlyFee)}/mo · build ${money(c.buildFee)} · ${esc(c.status || 'Active')}</div>
            <div style="margin-top:8px"><span class="badge ${r.level}">${esc(r.text)}</span></div>
            ${c.notes ? `<div class="ci-meta" style="margin-top:8px">${esc(c.notes)}</div>` : ''}
          </div>
          <div class="ci-actions">
            <button class="btn sm" onclick="logContact('${c.id}')">Log contact</button>
            <button class="btn sm" onclick="goMessageForClient('${c.id}')">Message</button>
            <button class="btn sm" onclick="editClient('${c.id}')">Edit</button>
            <button class="btn sm danger" onclick="deleteClient('${c.id}')">Delete</button>
          </div>
        </div>`;
      }).join('')
    : `<div class="empty">No clients yet. When you close a deal, add them here and the app will remind you to follow up.</div>`;

  document.getElementById('tab-clients').innerHTML = `
    <div class="page-head">
      <div><h1>Clients</h1><p>Your paying customers, with reminders on when to reach out.</p></div>
      <button class="btn primary" onclick="addClient()">+ Add client</button>
    </div>
    <div class="panel">${list}</div>`;
}

function addClient(prefill) {
  openModal('Add client', clientFields(), prefill || {}, (obj) => {
    obj.id = uid();
    data.clients.push(obj);
    save(); renderClients(); toast('Client added');
  });
}

function editClient(id) {
  const c = data.clients.find((x) => x.id === id);
  if (!c) return;
  openModal('Edit client', clientFields(), c, (obj) => {
    Object.assign(c, obj);
    save(); renderClients(); toast('Saved');
  });
}

function deleteClient(id) {
  const c = data.clients.find((x) => x.id === id);
  if (!c) return;
  if (!confirm(`Delete ${c.business}? This cannot be undone.`)) return;
  data.clients = data.clients.filter((x) => x.id !== id);
  save(); renderClients(); toast('Deleted');
}

function logContact(id) {
  const c = data.clients.find((x) => x.id === id);
  if (!c) return;
  c.lastContact = todayISO();
  save();
  // re-render whichever tab is active
  const active = document.querySelector('.nav-item.active');
  if (active) RENDERERS[active.dataset.tab]();
  toast('Logged contact for today');
}

/* ============================================================
   LEADS
   ============================================================ */
const LEAD_STATUSES = ['New', 'Researching', 'Called - no answer', 'Called - interested', 'Demo booked', 'Demo sent', 'Closed - WON', 'Closed - lost', 'Not interested'];

function leadFields() {
  return [
    { key: 'business', label: 'Business name' },
    { key: 'niche', label: 'Type of business', placeholder: 'Barbershop, Handyman, ...' },
    { key: 'phone', label: 'Phone' },
    { key: 'address', label: 'Address' },
    { key: 'website', label: 'Has website?', type: 'select', options: ['No', 'Unknown', 'Yes (skip)'], default: 'No' },
    { key: 'status', label: 'Status', type: 'select', options: LEAD_STATUSES, default: 'New' },
    { key: 'notes', label: 'Notes', type: 'textarea', full: true }
  ];
}

let leadFilter = 'All';

function renderLeads() {
  const filtered = leadFilter === 'All' ? data.leads : data.leads.filter((l) => l.status === leadFilter);
  const pills = ['All'].concat(LEAD_STATUSES).map((s) => {
    const n = s === 'All' ? data.leads.length : data.leads.filter((l) => l.status === s).length;
    return `<button class="pill ${leadFilter === s ? 'active' : ''}" onclick="setLeadFilter('${esc(s)}')">${esc(s)} (${n})</button>`;
  }).join('');

  const rows = filtered.length
    ? filtered.map((l) => {
        const opts = LEAD_STATUSES.map((s) => `<option ${s === l.status ? 'selected' : ''}>${esc(s)}</option>`).join('');
        return `<tr>
          <td><span class="biz">${esc(l.business)}</span><div class="muted">${esc(l.niche || '')} ${l.address ? '· ' + esc(l.address) : ''}</div>${l.notes ? `<div class="muted">${esc(l.notes)}</div>` : ''}</td>
          <td>${esc(l.phone || '—')}</td>
          <td><span class="badge ${l.website === 'Yes (skip)' ? 'neutral' : 'good'}">${esc(l.website)}</span></td>
          <td><select class="status-select" onchange="setLeadStatus('${l.id}', this.value)">${opts}</select></td>
          <td style="text-align:right; white-space:nowrap">
            <button class="btn sm" onclick="goScriptForLead('${l.id}')">Script</button>
            <button class="btn sm" onclick="convertLead('${l.id}')">Won → Client</button>
            <button class="btn sm" onclick="editLead('${l.id}')">Edit</button>
            <button class="btn sm danger" onclick="deleteLead('${l.id}')">×</button>
          </td></tr>`;
      }).join('')
    : `<tr><td colspan="5" class="empty">No leads in this view.</td></tr>`;

  document.getElementById('tab-leads').innerHTML = `
    <div class="page-head">
      <div><h1>Leads to Call</h1><p>Businesses with no website — your prospects. Update status as you work them.</p></div>
      <button class="btn primary" onclick="addLead()">+ Add lead</button>
    </div>
    <div class="pill-row">${pills}</div>
    <div class="panel">
      <table><thead><tr><th>Business</th><th>Phone</th><th>Website</th><th>Status</th><th></th></tr></thead><tbody>${rows}</tbody></table>
    </div>`;
}

function setLeadFilter(s) { leadFilter = s; renderLeads(); }
function setLeadStatus(id, status) {
  const l = data.leads.find((x) => x.id === id);
  if (!l) return;
  l.status = status; l.lastTouch = todayISO();
  save(); renderLeads();
}
function addLead(prefill) {
  openModal('Add lead', leadFields(), prefill || {}, (obj) => {
    obj.id = uid();
    data.leads.push(obj);
    save(); renderLeads(); toast('Lead added');
  });
}
function editLead(id) {
  const l = data.leads.find((x) => x.id === id);
  if (!l) return;
  openModal('Edit lead', leadFields(), l, (obj) => { Object.assign(l, obj); save(); renderLeads(); toast('Saved'); });
}
function deleteLead(id) {
  const l = data.leads.find((x) => x.id === id);
  if (!l) return;
  if (!confirm(`Delete ${l.business}?`)) return;
  data.leads = data.leads.filter((x) => x.id !== id);
  save(); renderLeads();
}
function convertLead(id) {
  const l = data.leads.find((x) => x.id === id);
  if (!l) return;
  const prefill = { business: l.business, niche: l.niche, phone: l.phone, address: l.address, notes: l.notes };
  openModal('Convert lead → client', clientFields(), prefill, (obj) => {
    obj.id = uid();
    data.clients.push(obj);
    data.leads = data.leads.filter((x) => x.id !== id);
    save(); toast('Converted to client!'); showTab('clients');
  });
}

/* ---------- CSV lead import (Google Maps export or generic CSV) ---------- */
function parseCSVText(text) {
  const rows = []; let row = []; let cur = ''; let q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) {
      if (c === '"') { if (text[i + 1] === '"') { cur += '"'; i++; } else q = false; }
      else cur += c;
    } else {
      if (c === '"') q = true;
      else if (c === ',') { row.push(cur); cur = ''; }
      else if (c === '\n') { row.push(cur); rows.push(row); row = []; cur = ''; }
      else if (c === '\r') { /* skip */ }
      else cur += c;
    }
  }
  if (cur.length || row.length) { row.push(cur); rows.push(row); }
  return rows;
}

function detectCols(header) {
  const h = header.map((x) => (x || '').trim().toLowerCase());
  function find(pred, fallback) {
    for (let i = 0; i < h.length; i++) { if (pred(h[i])) return i; }
    return fallback;
  }
  return {
    name: find((s) => s === 'qbf1pd' || s.indexOf('name') >= 0 || s.indexOf('business') >= 0 || s.indexOf('title') >= 0, 1),
    website: find((s) => s === 'lcr4fd href' || s === 'website' || (s.indexOf('website') >= 0 && s.indexOf('href') >= 0) || s === 'site' || s === 'url', 11),
    phone: find((s) => s === 'usdlk' || s.indexOf('phone') >= 0 || s.indexOf('tel') >= 0, 10),
    niche: find((s) => s === 'w4efsd' || s.indexOf('category') >= 0 || s.indexOf('type') >= 0 || s.indexOf('niche') >= 0, 4),
    address: find((s) => s === 'w4efsd 3' || s.indexOf('address') >= 0 || s.indexOf('street') >= 0, 6),
    rating: find((s) => s === 'mw4etd' || s.indexOf('rating') >= 0 || s.indexOf('stars') >= 0, 2),
    reviews: find((s) => s === 'uy7f9' || s.indexOf('review') >= 0, 3)
  };
}

function extractLeadsFromCSV(text) {
  const rows = parseCSVText(text);
  if (rows.length < 2) return { leads: [], hadWebsite: 0, total: 0 };
  const cols = detectCols(rows[0]);
  const out = []; let hadWebsite = 0; let total = 0;
  for (let i = 1; i < rows.length; i++) {
    const r = rows[i];
    const name = (r[cols.name] || '').trim();
    if (!name) continue;
    total++;
    const website = (r[cols.website] || '').trim();
    if (website) { hadWebsite++; continue; }
    const rating = (r[cols.rating] || '').trim();
    const reviews = (r[cols.reviews] || '').trim();
    out.push({
      id: uid(),
      business: name,
      niche: (r[cols.niche] || '').trim(),
      phone: (r[cols.phone] || '').trim(),
      address: (r[cols.address] || '').trim(),
      website: 'No',
      status: 'New',
      lastTouch: '',
      notes: (rating ? rating + '★ ' + reviews : '').trim()
    });
  }
  return { leads: out, hadWebsite: hadWebsite, total: total };
}

function importLeadsCSV(input) {
  const file = input.files && input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function () {
    let res;
    try { res = extractLeadsFromCSV(String(reader.result)); }
    catch (e) { alert('Could not read that CSV file.'); return; }
    if (!res.total) { alert('No businesses found in that CSV. Make sure it has a header row and a business-name column.'); return; }
    const seen = {};
    data.leads.forEach((l) => { seen[(l.business || '').trim().toLowerCase()] = true; });
    let added = 0, dupes = 0;
    res.leads.forEach((l) => {
      const key = l.business.trim().toLowerCase();
      if (seen[key]) { dupes++; return; }
      seen[key] = true;
      data.leads.push(l); added++;
    });
    save();
    renderDashboard();
    const msg = 'Added ' + added + ' new lead' + (added === 1 ? '' : 's') +
      (dupes ? ', skipped ' + dupes + ' already in your list' : '') +
      '. (' + res.hadWebsite + ' had websites and were skipped.)';
    const el = document.getElementById('csvResult');
    if (el) { el.textContent = msg; el.style.color = '#16a34a'; }
    toast(added + ' leads added');
  };
  reader.readAsText(file);
}

/* ============================================================
   CALL SCRIPT GENERATOR
   ============================================================ */
function buildCallScript(v) {
  const biz = v.business || '[business name]';
  const niche = (v.niche || 'business').toLowerCase();
  const contact = v.contact || '';
  const build = v.buildFee || data.settings.defaultBuild;
  const monthly = v.monthlyFee || data.settings.defaultMonthly;

  const homework = [];
  if (v.years) homework.push(`you've been doing this since ${v.years}`);
  if (v.rating) homework.push(`you've got a ${v.rating} rating`);
  const hw = homework.length ? ` — I saw ${homework.join(' and ')}, which is genuinely impressive —` : '';

  return `COLD CALL SCRIPT — ${biz}
(Best time to call: Tue–Thu, 10–11:30am or 2–3:30pm)

1) CONFIRM THEY'RE OPEN + HONEST OPENER
"Hey, is this ${biz}? — Are you guys still taking on new ${niche} work right now?
... Good. I'll be honest with you, this is a cold call — can I grab 20 seconds
to tell you why, and you decide if it's worth it?"

2) THE REASON + WHAT YOU ALREADY BUILT
"Appreciate it. The reason I'm calling — I came across ${biz} online${hw}
but when I went to find your website, there wasn't one. So I actually went
ahead and built you a quick demo of what one could look like."

3) THEIR PROBLEM (then STOP and listen)
"Here's why it matters: when someone needs a ${niche} around here, they Google
it — and right now you either don't show up, or you're buried next to ten other
businesses. All the good reputation you've earned isn't working for you online.
... How are most of your customers finding you these days?"

4) IF THEY SAY "I'M BUSY / ALREADY BOOKED"
"Totally — and honestly that's the best position to be in. This isn't about more
random calls, it's about letting you cherry-pick the BETTER jobs. Looking
professional online attracts the bigger projects instead of small odd jobs. Fair?"

5) BOOK THE WALKTHROUGH (don't email it — present it live)
"It's way easier to just show you than describe it — takes 10 minutes on a quick
video call. Are you free later today around 2, or would tomorrow morning be
better? ... Perfect, I'll text you a link to hop on. And what's the best name for you?"

6) IF THEY ASK PRICE NOW
"Great question — let me show you the demo first so you can actually see what
you'd be getting. It's genuinely affordable, I promise. Can we do [time]?"
   → Your pricing when you do reveal it: ${money(build)} one-time build + ${money(monthly)}/month
     ("${money(monthly)}/mo covers hosting, updates, your Google listing, and any edits —
      so you never have to touch it.")

7) CLOSE
"Awesome — talk to you at [time]${contact ? ', ' + contact : ''}. Thanks for the 20 seconds, have a good one."

— REMINDERS —
• Let them talk ~60% of the time. Ask, then listen.
• Never say "is this a bad time?" (it tanks your meeting rate).
• If the business turns out not to be active, thank them warmly and hang up. No pitch.`;
}

function renderScripts(prefill) {
  const s = prefill || {};
  document.getElementById('tab-scripts').innerHTML = `
    <div class="page-head">
      <div><h1>Call Script Generator</h1><p>Fill in the details, get a ready-to-read cold-call script.</p></div>
    </div>
    <div class="split">
      <div class="panel">
        <div class="field"><label>Business name</label><input id="sc_business" value="${esc(s.business || '')}" placeholder="Centre Barbershop"></div>
        <div class="field"><label>Type of business</label><input id="sc_niche" value="${esc(s.niche || '')}" placeholder="Barbershop"></div>
        <div class="field"><label>Contact name (optional)</label><input id="sc_contact" value="${esc(s.contact || '')}"></div>
        <div class="field"><label>Years in business (optional)</label><input id="sc_years" value="${esc(s.years || '')}" placeholder="1998"></div>
        <div class="field"><label>Rating (optional)</label><input id="sc_rating" value="${esc(s.rating || '')}" placeholder="4.9-star"></div>
        <div class="form-grid">
          <div class="field"><label>Build fee ($)</label><input id="sc_build" type="number" value="${esc(s.buildFee || data.settings.defaultBuild)}"></div>
          <div class="field"><label>Monthly ($)</label><input id="sc_monthly" type="number" value="${esc(s.monthlyFee || data.settings.defaultMonthly)}"></div>
        </div>
        <div class="btn-row">
          <button class="btn primary" onclick="genScript()">Generate script</button>
        </div>
      </div>
      <div class="panel">
        <div class="btn-row" style="justify-content:flex-end; margin-bottom:10px">
          <button class="btn sm" onclick="copy(document.getElementById('scriptOut').textContent)">Copy script</button>
        </div>
        <div class="output" id="scriptOut">Fill in the details on the left and hit “Generate script.”</div>
      </div>
    </div>`;
  if (prefill && prefill.business) genScript();
}

function genScript() {
  const v = {
    business: val('sc_business'), niche: val('sc_niche'), contact: val('sc_contact'),
    years: val('sc_years'), rating: val('sc_rating'),
    buildFee: val('sc_build'), monthlyFee: val('sc_monthly')
  };
  document.getElementById('scriptOut').textContent = buildCallScript(v);
}

function goScriptForLead(id) {
  const l = data.leads.find((x) => x.id === id);
  if (!l) return;
  showTab('scripts');
  renderScripts({ business: l.business, niche: l.niche });
}

/* ============================================================
   EMAIL & TEXT GENERATOR
   ============================================================ */
const MSG_TYPES = [
  { id: 'demo-text', label: 'Send demo (text)' },
  { id: 'demo-email', label: 'Send demo (email)' },
  { id: 'after-demo', label: 'Follow-up after walkthrough' },
  { id: 'checkin', label: 'Check-in (haven\'t talked in a while)' },
  { id: 'referral', label: 'Thank you + ask for referral' },
  { id: 'reschedule', label: 'No-show / reschedule' }
];

function buildMessage(type, v) {
  const you = v.yourName || data.settings.yourName || '[your name]';
  const co = v.company || data.settings.company || '[your company]';
  const biz = v.business || '[business]';
  const name = v.contact ? v.contact : 'there';
  const link = v.link || '[demo link]';
  const time = v.time || '[day/time]';

  switch (type) {
    case 'demo-text':
      return `Hey ${name}, this is ${you} with ${co} — great talking with you! Here's the demo site I built for ${biz}: ${link}\n\nSent it to your email too. Talk ${time}!`;
    case 'demo-email':
      return `Subject: Quick website demo for ${biz}\n\nHi ${name},\n\nGreat talking with you! As promised, here's a quick demo of what a website for ${biz} could look like:\n${link}\n\nThis is just a starting point — the photos, services, colors and booking all get customized to exactly how you want it.\n\nA few things it'd do for you:\n• Show up on Google when locals search for your services\n• Show your services, prices, hours and reviews in one place\n• Let customers call or book you in one tap\n\nI'll give you a quick call ${time} to walk through it. Looking forward to it!\n\n${you}\n${co}`;
    case 'after-demo':
      return `Subject: Your ${biz} website — next steps\n\nHi ${name},\n\nThanks for taking the time today! Here's the demo again so you can show anyone who needs to see it: ${link}\n\nTo recap — it's ${money(v.buildFee || data.settings.defaultBuild)} to build it out and get you live on Google, then ${money(v.monthlyFee || data.settings.defaultMonthly)}/month for hosting, updates, your Google listing, and any edits you need.\n\nWant me to get started? Just reply “let's do it” and I'll send over the quick details I need.\n\n${you}\n${co}`;
    case 'checkin':
      return `Hi ${name}, ${you} here from ${co} — just checking in on ${biz}! Everything running smoothly with the site? If there's anything you'd like added or updated this month, just send it over and I'll take care of it. 👍`;
    case 'referral':
      return `Hi ${name}, thanks again for trusting me with ${biz}'s website — it's been great working with you! Quick favor: if you know any other local business owners who could use a site, I'd really appreciate an intro. Happy to take great care of them like I did for you.\n\n— ${you}, ${co}`;
    case 'reschedule':
      return `Hey ${name}, ${you} with ${co} — looks like we missed each other for the website walkthrough, no worries at all! It only takes 10 minutes and I think you'll really like what I put together for ${biz}. When works better for you — later today or tomorrow?`;
    default:
      return '';
  }
}

let curMsgType = 'demo-text';

function renderMessages(prefill) {
  const s = prefill || {};
  const pills = MSG_TYPES.map((m) => `<button class="pill ${curMsgType === m.id ? 'active' : ''}" onclick="setMsgType('${m.id}')">${esc(m.label)}</button>`).join('');
  document.getElementById('tab-messages').innerHTML = `
    <div class="page-head">
      <div><h1>Email &amp; Text Generator</h1><p>Pick a message type, fill the blanks, copy &amp; send.</p></div>
    </div>
    <div class="pill-row">${pills}</div>
    <div class="split">
      <div class="panel">
        <div class="field"><label>Business</label><input id="m_business" value="${esc(s.business || '')}"></div>
        <div class="field"><label>Contact name</label><input id="m_contact" value="${esc(s.contact || '')}"></div>
        <div class="field"><label>Demo link</label><input id="m_link" value="${esc(s.link || '')}" placeholder="https://..."></div>
        <div class="field"><label>Day/time for call</label><input id="m_time" value="${esc(s.time || '')}" placeholder="Monday at 1pm"></div>
        <div class="form-grid">
          <div class="field"><label>Build ($)</label><input id="m_build" type="number" value="${data.settings.defaultBuild}"></div>
          <div class="field"><label>Monthly ($)</label><input id="m_monthly" type="number" value="${data.settings.defaultMonthly}"></div>
        </div>
        <button class="btn primary" onclick="genMessage()">Generate message</button>
      </div>
      <div class="panel">
        <div class="btn-row" style="justify-content:flex-end; margin-bottom:10px">
          <button class="btn sm" onclick="copy(document.getElementById('msgOut').textContent)">Copy</button>
        </div>
        <div class="output" id="msgOut">Pick a type and hit “Generate message.”</div>
      </div>
    </div>`;
  genMessage();
}

function setMsgType(id) { curMsgType = id; renderMessages(currentMsgValues()); }
function currentMsgValues() {
  return {
    business: val('m_business'), contact: val('m_contact'),
    link: val('m_link'), time: val('m_time')
  };
}
function genMessage() {
  const v = {
    business: val('m_business'), contact: val('m_contact'),
    link: val('m_link'), time: val('m_time'),
    buildFee: val('m_build'), monthlyFee: val('m_monthly')
  };
  document.getElementById('msgOut').textContent = buildMessage(curMsgType, v);
}
function goMessageForClient(id) {
  const c = data.clients.find((x) => x.id === id);
  if (!c) return;
  curMsgType = 'checkin';
  showTab('messages');
  renderMessages({ business: c.business, contact: c.contact });
}

/* ============================================================
   WEBSITE DEMO BUILDER (design mockup, no real features)
   ============================================================ */
function demoDefaults() {
  return {
    business: 'Centre Barbershop', niche: 'Barbershop',
    tagline: 'Classic cuts. Newton\'s neighborhood barbershop since 1998.',
    services: 'Haircut — $35\nBeard Trim — $20\nHot Towel Shave — $40\nKids Cut — $25',
    phone: '(617) 555-0123', hours: 'Tue–Sat: 9am–6pm', address: '212 Sumner St, Newton, MA',
    color: '#1f2937', accent: '#c0892f', hero: ''
  };
}

function renderDemo() {
  const d = demoDefaults();
  document.getElementById('tab-demo').innerHTML = `
    <div class="page-head">
      <div><h1>Website Demo Builder</h1><p>Generate a clean one-page design to show a prospect. (Design only — no live booking/payments.)</p></div>
    </div>
    <div class="split">
      <div class="panel">
        <div class="field"><label>Business name</label><input id="d_business" value="${esc(d.business)}"></div>
        <div class="field"><label>Type</label><input id="d_niche" value="${esc(d.niche)}"></div>
        <div class="field"><label>Tagline</label><input id="d_tagline" value="${esc(d.tagline)}"></div>
        <div class="field"><label>Services (one per line)</label><textarea id="d_services" rows="5">${esc(d.services)}</textarea></div>
        <div class="form-grid">
          <div class="field"><label>Phone</label><input id="d_phone" value="${esc(d.phone)}"></div>
          <div class="field"><label>Hours</label><input id="d_hours" value="${esc(d.hours)}"></div>
        </div>
        <div class="field"><label>Address</label><input id="d_address" value="${esc(d.address)}"></div>
        <div class="form-grid">
          <div class="field"><label>Main color</label><input id="d_color" type="color" value="${esc(d.color)}"></div>
          <div class="field"><label>Accent color</label><input id="d_accent" type="color" value="${esc(d.accent)}"></div>
        </div>
        <div class="field"><label>Hero image URL (optional)</label><input id="d_hero" value="" placeholder="https://... (leave blank for gradient)"></div>
        <div class="btn-row">
          <button class="btn primary" onclick="buildDemo()">Build / refresh preview</button>
          <button class="btn" onclick="openDemoWindow()">Open full screen</button>
          <button class="btn" onclick="downloadDemo()">Download .html</button>
        </div>
        <div class="hint" style="margin-top:8px; color:var(--muted); font-size:12px">Tip: “Download .html” gives you a file you can show on your phone or send as the demo link.</div>
      </div>
      <div class="demo-frame-wrap">
        <div class="bar"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>
        <iframe id="demoFrame"></iframe>
      </div>
    </div>`;
  buildDemo();
}

function collectDemo() {
  return {
    business: val('d_business') || 'Your Business',
    niche: val('d_niche') || 'Local Business',
    tagline: val('d_tagline') || '',
    services: (val('d_services') || '').split('\n').map((s) => s.trim()).filter(Boolean),
    phone: val('d_phone') || '',
    hours: val('d_hours') || '',
    address: val('d_address') || '',
    color: val('d_color') || '#1f2937',
    accent: val('d_accent') || '#c0892f',
    hero: val('d_hero') || ''
  };
}

function demoSiteHTML(v) {
  const heroBg = v.hero
    ? `linear-gradient(rgba(0,0,0,.55),rgba(0,0,0,.55)), url('${esc(v.hero)}') center/cover`
    : `linear-gradient(135deg, ${esc(v.color)}, ${esc(v.accent)})`;
  const services = v.services.map((s) => {
    const parts = s.split(/\s[—-]\s/);
    const name = esc(parts[0] || s);
    const price = parts[1] ? esc(parts[1]) : '';
    return `<div class="svc"><span>${name}</span>${price ? `<span class="price">${price}</span>` : ''}</div>`;
  }).join('');

  return `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(v.business)}</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#111827;line-height:1.55}
  .wrap{max-width:1000px;margin:0 auto;padding:0 22px}
  header{position:sticky;top:0;background:#fff;border-bottom:1px solid #eee;z-index:5}
  .nav{display:flex;align-items:center;justify-content:space-between;padding:16px 0}
  .logo{font-weight:800;font-size:19px;color:${esc(v.color)}}
  .nav a{margin-left:18px;text-decoration:none;color:#374151;font-size:14px}
  .cta{background:${esc(v.accent)};color:#fff !important;padding:9px 16px;border-radius:8px;font-weight:700}
  .hero{background:${heroBg};color:#fff;text-align:center;padding:96px 22px}
  .hero h1{font-size:42px;font-weight:800;letter-spacing:-.5px;margin-bottom:14px}
  .hero p{font-size:18px;opacity:.95;max-width:620px;margin:0 auto 26px}
  .hero .btns a{display:inline-block;margin:6px;padding:13px 24px;border-radius:9px;font-weight:700;text-decoration:none}
  .b1{background:${esc(v.accent)};color:#fff}
  .b2{background:rgba(255,255,255,.15);color:#fff;border:1px solid rgba(255,255,255,.5)}
  section{padding:64px 0}
  h2{font-size:28px;margin-bottom:24px;color:${esc(v.color)}}
  .svc{display:flex;justify-content:space-between;padding:15px 0;border-bottom:1px solid #eee;font-size:17px}
  .svc .price{font-weight:700;color:${esc(v.accent)}}
  .reviews{background:#f9fafb}
  .rgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px}
  .review{background:#fff;border:1px solid #eee;border-radius:12px;padding:20px}
  .stars{color:${esc(v.accent)};font-size:16px;margin-bottom:8px}
  .info{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:22px}
  .info .box{background:#fff;border:1px solid #eee;border-radius:12px;padding:20px}
  .info .box b{display:block;color:${esc(v.color)};margin-bottom:6px}
  footer{background:${esc(v.color)};color:#fff;text-align:center;padding:40px 22px;font-size:14px}
  @media(max-width:640px){.hero h1{font-size:32px}.nav a:not(.cta){display:none}}
</style></head>
<body>
  <header><div class="wrap nav">
    <div class="logo">${esc(v.business)}</div>
    <nav><a href="#services">Services</a><a href="#reviews">Reviews</a><a href="#contact">Contact</a><a href="#contact" class="cta">Book Now</a></nav>
  </div></header>

  <div class="hero">
    <h1>${esc(v.business)}</h1>
    <p>${esc(v.tagline)}</p>
    <div class="btns">
      <a class="b1" href="#contact">Book an Appointment</a>
      ${v.phone ? `<a class="b2" href="tel:${esc(v.phone)}">Call ${esc(v.phone)}</a>` : ''}
    </div>
  </div>

  <section id="services"><div class="wrap">
    <h2>Services</h2>
    ${services || '<p>Your services will appear here.</p>'}
  </div></section>

  <section id="reviews" class="reviews"><div class="wrap">
    <h2>What customers say</h2>
    <div class="rgrid">
      <div class="review"><div class="stars">★★★★★</div>“Best in town — friendly, professional, and always great work.”<br><b style="margin-top:8px;display:block">— Local customer</b></div>
      <div class="review"><div class="stars">★★★★★</div>“Highly recommend. Quick to respond and fairly priced.”<br><b style="margin-top:8px;display:block">— Local customer</b></div>
      <div class="review"><div class="stars">★★★★★</div>“Been coming here for years. Wouldn't go anywhere else.”<br><b style="margin-top:8px;display:block">— Local customer</b></div>
    </div>
  </div></section>

  <section id="contact"><div class="wrap">
    <h2>Visit us</h2>
    <div class="info">
      ${v.phone ? `<div class="box"><b>Call</b><a href="tel:${esc(v.phone)}" style="color:${esc(v.accent)};text-decoration:none">${esc(v.phone)}</a></div>` : ''}
      ${v.hours ? `<div class="box"><b>Hours</b>${esc(v.hours)}</div>` : ''}
      ${v.address ? `<div class="box"><b>Location</b>${esc(v.address)}</div>` : ''}
    </div>
  </div></section>

  <footer>© ${new Date().getFullYear()} ${esc(v.business)} · ${esc(v.niche)} · Newton, MA</footer>
</body></html>`;
}

function buildDemo() {
  const html = demoSiteHTML(collectDemo());
  document.getElementById('demoFrame').srcdoc = html;
}
function openDemoWindow() {
  const html = demoSiteHTML(collectDemo());
  const w = window.open('', '_blank');
  if (w) { w.document.open(); w.document.write(html); w.document.close(); }
}
function downloadDemo() {
  const v = collectDemo();
  const name = (v.business || 'demo').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  download(name + '-demo.html', demoSiteHTML(v), 'text/html');
  toast('Demo downloaded');
}

/* ============================================================
   SETTINGS & BACKUP
   ============================================================ */
function renderSettings() {
  const s = data.settings;
  document.getElementById('tab-settings').innerHTML = `
    <div class="page-head">
      <div><h1>Settings &amp; Backup</h1><p>Your defaults, and saving/restoring your data.</p></div>
    </div>
    <div class="panel">
      <h2>Your info (used in scripts &amp; messages)</h2>
      <div class="form-grid">
        <div class="field"><label>Your name</label><input id="set_name" value="${esc(s.yourName)}"></div>
        <div class="field"><label>Company name</label><input id="set_co" value="${esc(s.company)}"></div>
        <div class="field"><label>Default build fee ($)</label><input id="set_build" type="number" value="${esc(s.defaultBuild)}"></div>
        <div class="field"><label>Default monthly ($)</label><input id="set_monthly" type="number" value="${esc(s.defaultMonthly)}"></div>
      </div>
      <button class="btn primary" onclick="saveSettings()">Save settings</button>
    </div>
    <div class="panel">
      <h2>Backup &amp; restore</h2>
      <p style="color:var(--muted);font-size:13px;margin-bottom:14px">Your data is stored only on this computer. Export a backup file regularly so you never lose your clients and leads.</p>
      <div class="btn-row">
        <button class="btn primary" onclick="exportData()">Export backup (.json)</button>
        <button class="btn" onclick="document.getElementById('importFile').click()">Import backup</button>
        <input id="importFile" type="file" accept="application/json" style="display:none" onchange="importData(this)">
        <button class="btn danger" onclick="resetData()">Erase all data</button>
      </div>
    </div>`;
}

function saveSettings() {
  data.settings.yourName = val('set_name');
  data.settings.company = val('set_co');
  data.settings.defaultBuild = Number(val('set_build')) || 250;
  data.settings.defaultMonthly = Number(val('set_monthly')) || 50;
  save(); toast('Settings saved');
}
function exportData() {
  download('agency-dashboard-backup-' + todayISO() + '.json', JSON.stringify(data, null, 2), 'application/json');
  toast('Backup exported');
}
function importData(input) {
  const file = input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const obj = JSON.parse(reader.result);
      if (!obj.clients || !obj.leads) throw new Error('bad file');
      data = { clients: obj.clients, leads: obj.leads, settings: Object.assign(defaultSettings(), obj.settings || {}) };
      save(); toast('Backup restored'); showTab('dashboard');
    } catch (e) { alert('That file does not look like a valid backup.'); }
  };
  reader.readAsText(file);
}
function resetData() {
  if (!confirm('Erase ALL clients, leads and settings? Export a backup first if unsure.')) return;
  safeRemove(STORE_KEY);
  data = load(); save(); toast('Data reset'); showTab('dashboard');
}

/* ---------- small helper ---------- */
function val(id) { const el = document.getElementById(id); return el ? el.value.trim() : ''; }

function renderSideStats() {
  const mrr = data.clients.reduce((s, c) => s + (Number(c.monthlyFee) || 0), 0);
  const toCall = data.leads.filter((l) => ['New', 'Researching', 'Called - no answer'].includes(l.status)).length;
  document.getElementById('sideStats').innerHTML =
    `<b>${data.clients.length}</b> clients · <b>${money(mrr)}</b>/mo<br><b>${toCall}</b> leads to call`;
}

/* ---------- boot ---------- */
(function () {
  var v = document.getElementById('verStamp');
  if (v) { v.textContent = 'BUILD 3 · ✓ running'; v.style.color = '#22c55e'; }
})();
renderSideStats();
showTab('dashboard');
if (!storageWorks) {
  setTimeout(function () {
    var n = document.createElement('div');
    n.style.cssText = 'position:fixed;bottom:16px;right:16px;max-width:320px;background:#b45309;color:#fff;padding:12px 14px;border-radius:10px;font:12.5px -apple-system,sans-serif;z-index:9999;box-shadow:0 8px 24px rgba(0,0,0,.2)';
    n.textContent = 'Heads up: this browser is blocking saved storage for opened files, so your data won’t persist after closing. Open this file in Chrome (or use the installed app) for saving. Use Settings → Export to back up.';
    document.body.appendChild(n);
    setTimeout(function () { n.style.transition = 'opacity .4s'; n.style.opacity = '0'; setTimeout(function () { n.remove(); }, 500); }, 9000);
  }, 600);
}
