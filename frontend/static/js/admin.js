/**
 * NEXUS 2026 - Admin Dashboard & Analytics Manager
 */

let currentSearch = '';
let currentCategoryFilter = 'all';
let currentStatusFilter = 'all';
let searchDebounceTimer = null;

document.addEventListener('DOMContentLoaded', () => {
  loadDbStatus();
  loadAdminStats();
  loadRegistrations();
  initAdminEventListeners();
});

function loadDbStatus() {
  const textEl = document.getElementById('db-status-text');
  const dotEl = document.getElementById('db-status-dot');
  if (!textEl) return;

  fetch('/api/db-status')
    .then(r => r.json())
    .then(data => {
      if (data.connected) {
        if (dotEl) dotEl.style.background = '#10b981';
        const latency = data.latency_ms ? ` • ${data.latency_ms}ms` : '';
        textEl.textContent = `${data.engine}${latency}`;
      } else {
        if (dotEl) dotEl.style.background = '#f59e0b';
        textEl.textContent = 'Database: Degraded';
      }
    })
    .catch(() => {
      if (dotEl) dotEl.style.background = '#ef4444';
      textEl.textContent = 'Database: Offline';
    });
}

function initAdminEventListeners() {
  // Search input with debounce
  const searchInput = document.getElementById('admin-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      clearTimeout(searchDebounceTimer);
      searchDebounceTimer = setTimeout(() => {
        currentSearch = e.target.value.trim();
        loadRegistrations();
      }, 300);
    });
  }

  // Category filter
  const catFilter = document.getElementById('admin-cat-filter');
  if (catFilter) {
    catFilter.addEventListener('change', (e) => {
      currentCategoryFilter = e.target.value;
      loadRegistrations();
    });
  }

  // Status filter
  const statusFilter = document.getElementById('admin-status-filter');
  if (statusFilter) {
    statusFilter.addEventListener('change', (e) => {
      currentStatusFilter = e.target.value;
      loadRegistrations();
    });
  }

  // Refresh button
  const refreshBtn = document.getElementById('btn-admin-refresh');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      loadDbStatus();
      loadAdminStats();
      loadRegistrations();
    });
  }

  // Clear all records tool
  const clearBtn = document.getElementById('btn-admin-clear');
  if (clearBtn) {
    clearBtn.addEventListener('click', clearAllRecords);
  }

  // Broadcast emails to all attendees
  const broadcastBtn = document.getElementById('btn-admin-broadcast-emails');
  if (broadcastBtn) {
    broadcastBtn.addEventListener('click', broadcastEmailsToAll);
  }

  // Edit form submit
  const editForm = document.getElementById('edit-attendee-form');
  if (editForm) {
    editForm.addEventListener('submit', handleEditSubmit);
  }

  // Backdrop click to close modals
  const editModal = document.getElementById('edit-modal');
  if (editModal) {
    editModal.addEventListener('click', (e) => {
      if (e.target === editModal) closeEditModal();
    });
  }

  const emailModal = document.getElementById('email-viewer-modal');
  if (emailModal) {
    emailModal.addEventListener('click', (e) => {
      if (e.target === emailModal) closeEmailModal();
    });
  }

  // Escape key to close modals
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeEditModal();
      closeEmailModal();
    }
  });
}

// Broadcast official pass emails to all registered attendees
async function broadcastEmailsToAll() {
  const btn = document.getElementById('btn-admin-broadcast-emails');
  if (!confirm('Broadcast official digital pass emails (with scannable QR code, pass card, and PDF badge attachments) to all registered attendees via Gmail SMTP?')) {
    return;
  }

  const origText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner" style="width:13px;height:13px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:6px;"></span> Dispatching Emails...`;

  try {
    const resp = await fetch('/api/admin/broadcast-emails', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const res = await resp.json();
    if (res.success) {
      alert(`Email Broadcast Complete!\n\n${res.message}\nTotal Attendees: ${res.total}\nDelivered: ${res.sent}\nSkipped/Failed: ${res.failed}`);
    } else {
      alert(`Error broadcasting emails: ${res.error || 'Server error'}`);
    }
  } catch (err) {
    alert(`Network error: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = origText;
  }
}

// Load KPI Stats
async function loadAdminStats() {
  try {
    const resp = await fetch('/api/admin/stats');
    const res = await resp.json();

    if (res.success) {
      const s = res.stats;
      document.getElementById('kpi-total').textContent = s.total.toLocaleString();
      document.getElementById('kpi-checked').textContent = s.checked_in.toLocaleString();
      document.getElementById('kpi-pending').textContent = s.pending.toLocaleString();
      document.getElementById('kpi-rate').textContent = s.attendance_rate + '%';

      // Category breakdown
      const facs = (s.categories && s.categories.faculty !== undefined) ? s.categories.faculty : ((s.categories && s.categories.vip) || 0);
      const dels = (s.categories && s.categories.delegate) || 0;
      const pars = (s.categories && s.categories.participant) || 0;
      const total = s.total || 1;

      const kpiFacEl = document.getElementById('kpi-fac-val') || document.getElementById('kpi-vips-val');
      if (kpiFacEl) kpiFacEl.textContent = facs.toLocaleString();
      const kpiDelsEl = document.getElementById('kpi-dels-val');
      if (kpiDelsEl) kpiDelsEl.textContent = dels.toLocaleString();
      const kpiParsEl = document.getElementById('kpi-pars-val');
      if (kpiParsEl) kpiParsEl.textContent = pars.toLocaleString();

      const segFac = document.getElementById('seg-fac') || document.getElementById('seg-vip');
      const segDel = document.getElementById('seg-del');
      const segPar = document.getElementById('seg-par');

      if (segFac) segFac.style.width = `${(facs / total) * 100}%`;
      if (segDel) segDel.style.width = `${(dels / total) * 100}%`;
      if (segPar) segPar.style.width = `${(pars / total) * 100}%`;
    }
  } catch (err) {
    console.error('Failed to load admin stats:', err);
  }
}

// Load Registrations Table
async function loadRegistrations() {
  const tbody = document.getElementById('registrations-tbody');
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 40px;"><div class="spinner" style="margin: 0 auto 12px;"></div>Loading registrations...</td></tr>`;

  try {
    const params = new URLSearchParams({
      search: currentSearch,
      category: currentCategoryFilter,
      status: currentStatusFilter,
      limit: 150
    });

    const resp = await fetch(`/api/admin/registrations?${params.toString()}`);
    const res = await resp.json();

    if (res.success) {
      renderTableRows(res.data.registrations);
      document.getElementById('table-count-label').textContent = `Showing ${res.data.registrations.length} of ${res.data.total.toLocaleString()} attendees`;
    }
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--danger); padding: 20px;">Failed to load data: ${err.message}</td></tr>`;
  }
}

function renderTableRows(items) {
  const tbody = document.getElementById('registrations-tbody');
  if (!tbody) return;

  if (items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 40px; color: var(--text-dim);">No attendee registrations match your filters.</td></tr>`;
    return;
  }

  tbody.innerHTML = items.map(item => {
    const isChecked = item.status === 'CHECKED_IN';
    const statusPill = isChecked 
      ? `<span class="pill-status pill-status-checked">Checked In</span>` 
      : `<span class="pill-status pill-status-registered">Registered</span>`;

    const checkinMeta = isChecked 
      ? `<div style="font-size: 11px; color: var(--success);">${item.check_in_time}</div>
         <div style="font-size: 10px; color: var(--text-dim);">${item.check_in_station || 'Kiosk'}</div>` 
      : `<span style="color: var(--text-dim); font-size: 11px;">Pending arrival</span>`;

    return `
      <tr>
        <td>
          <span style="font-family: var(--font-mono); font-weight: 700; color: #0284c7;">${item.registration_id}</span>
        </td>
        <td>
          <div style="font-weight: 700; color: #0f172a;">${item.full_name}</div>
          <div style="font-size: 12px; color: var(--text-dim);">${item.email}</div>
        </td>
        <td>
          <span class="pill-cat pill-cat-${item.category}">${item.category}</span>
        </td>
        <td>
          <div style="font-weight: 500;">${item.organization}</div>
          <div style="font-size: 11px; color: var(--text-dim);">${item.designation || 'Attendee'}</div>
        </td>
        <td>${statusPill}</td>
        <td>${checkinMeta}</td>
        <td>
          <div class="row-actions">
            <!-- View / Print ID Card Badge -->
            <button class="action-icon-btn" title="View & Print Badge" onclick='BadgeManager.openModal(${JSON.stringify(item)})'>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="12" cy="10" r="3"/><path d="M7 17a5 5 0 0 1 10 0"/></svg>
            </button>

            <!-- Download PDF Pass -->
            <a class="action-icon-btn" title="Download Official PDF Pass" href="/api/registration/${item.registration_id}/pdf" download="YES2026_Pass_${item.registration_id}.pdf" style="display: inline-flex; align-items: center; justify-content: center; color: #0284c7;">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>
            </a>

            <!-- Toggle Check-in status -->
            <button class="action-icon-btn ${isChecked ? 'btn-danger-hover' : 'btn-success-hover'}" 
              title="${isChecked ? 'Undo Check-in' : 'Manual Check-in'}" 
              onclick="toggleCheckin('${item.registration_id}')">
              ${isChecked 
                ? '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>'
                : '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>'
              }
            </button>

            <!-- Edit Attendee -->
            <button class="action-icon-btn" title="Edit Registration" onclick='openEditModal(${JSON.stringify(item)})'>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            </button>

            <!-- View Sent Confirmation Email -->
            <button class="action-icon-btn" title="View Outbox Email" onclick="viewEmail('${item.registration_id}')">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
            </button>

            <!-- Resend Email -->
            <button class="action-icon-btn" title="Resend Email" onclick="resendEmail('${item.registration_id}')">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
            </button>

            <!-- Delete Attendee -->
            <button class="action-icon-btn btn-danger-hover" title="Delete Registration" onclick="deleteAttendee('${item.registration_id}')">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

// Toggle Check-in
async function toggleCheckin(regId) {
  try {
    const resp = await fetch(`/api/admin/registration/${regId}/toggle-checkin`, { method: 'POST' });
    const res = await resp.json();
    if (res.success) {
      loadAdminStats();
      loadRegistrations();
    }
  } catch (err) {
    alert('Failed to toggle status: ' + err.message);
  }
}

// Resend Email
async function resendEmail(regId) {
  try {
    const resp = await fetch(`/api/admin/registration/${regId}/resend-email`, { method: 'POST' });
    const res = await resp.json();
    if (res.success) {
      alert(res.message);
    }
  } catch (err) {
    alert('Failed to resend: ' + err.message);
  }
}

// View Confirmation Email Modal
function viewEmail(regId) {
  const modal = document.getElementById('email-viewer-modal');
  const iframe = document.getElementById('email-viewer-iframe');
  if (modal && iframe) {
    iframe.src = `/api/emails/latest/${regId}`;
    modal.classList.add('active');
  }
}

function closeEmailModal() {
  const modal = document.getElementById('email-viewer-modal');
  if (modal) modal.classList.remove('active');
}

// Delete Attendee
async function deleteAttendee(regId) {
  if (!confirm(`Are you sure you want to delete registration ${regId}? This cannot be undone.`)) return;

  try {
    const resp = await fetch(`/api/admin/registration/${regId}`, { method: 'DELETE' });
    const res = await resp.json();
    if (res.success) {
      loadAdminStats();
      loadRegistrations();
    }
  } catch (err) {
    alert('Delete failed: ' + err.message);
  }
}

// Edit Modal
function openEditModal(attendee) {
  const modal = document.getElementById('edit-modal');
  if (!modal) return;

  document.getElementById('edit-reg-id').value = attendee.registration_id;
  document.getElementById('edit-full-name').value = attendee.full_name;
  document.getElementById('edit-email').value = attendee.email;
  document.getElementById('edit-phone').value = attendee.phone;
  document.getElementById('edit-org').value = attendee.organization;
  document.getElementById('edit-role').value = attendee.designation || '';
  document.getElementById('edit-track').value = attendee.track_or_industry || '';

  modal.classList.add('active');
}

function closeEditModal() {
  const modal = document.getElementById('edit-modal');
  if (modal) modal.classList.remove('active');
}

async function handleEditSubmit(e) {
  e.preventDefault();
  const regId = document.getElementById('edit-reg-id').value;
  const updates = {
    full_name: document.getElementById('edit-full-name').value.trim(),
    email: document.getElementById('edit-email').value.trim(),
    phone: document.getElementById('edit-phone').value.trim(),
    organization: document.getElementById('edit-org').value.trim(),
    designation: document.getElementById('edit-role').value.trim(),
    track_or_industry: document.getElementById('edit-track').value.trim()
  };

  try {
    const resp = await fetch(`/api/admin/registration/${regId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });
    const res = await resp.json();
    if (res.success) {
      closeEditModal();
      loadRegistrations();
    }
  } catch (err) {
    alert('Edit failed: ' + err.message);
  }
}

// Clear All Registration Records (Clean Slate)
async function clearAllRecords() {
  if (!confirm("Are you sure you want to permanently clear ALL registration and check-in records? This will give you a completely clean, empty database for real-time live testing.")) return;

  try {
    const resp = await fetch('/api/admin/clear-all', { method: 'POST' });
    const res = await resp.json();
    if (res.success) {
      alert(res.message);
      loadAdminStats();
      loadRegistrations();
    }
  } catch (err) {
    alert('Clear error: ' + err.message);
  }
}

window.openEditModal = openEditModal;
window.closeEditModal = closeEditModal;
window.viewEmail = viewEmail;
window.closeEmailModal = closeEmailModal;
window.toggleCheckin = toggleCheckin;
window.resendEmail = resendEmail;
window.deleteAttendee = deleteAttendee;
window.loadAdminStats = loadAdminStats;
window.loadRegistrations = loadRegistrations;

