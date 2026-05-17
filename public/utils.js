// ─── Shared Utilities ──────────────────────────────────────────────────────

const API = '';  // same origin

// Session storage helpers
function saveUser(u) { localStorage.setItem('unicafe_user', JSON.stringify(u)); }
function getUser() { try { return JSON.parse(localStorage.getItem('unicafe_user')); } catch { return null; } }
function clearUser() { localStorage.removeItem('unicafe_user'); }

// Toast notifications
function showToast(msg, type = '') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  container.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

// API fetch helper
async function apiFetch(url, options = {}) {
  const res = await fetch(API + url, {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    ...options
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}

// Status badge
function statusBadge(status) {
  const labels = {
    pending: 'Pending', preparing: 'Preparing', ready: 'Ready',
    out_for_delivery: 'Out for Delivery', delivered: 'Delivered',
    active: 'Active', inactive: 'Inactive', open: 'Open', resolved: 'Resolved'
  };
  return `<span class="badge badge-${status}">${labels[status] || status}</span>`;
}

// Format date
function fmtDate(d) {
  if (!d) return '-';
  return new Date(d).toLocaleString('en-PK', { dateStyle: 'medium', timeStyle: 'short' });
}

// Logout
async function logout() {
  await apiFetch('/api/logout', { method: 'POST' }).catch(() => {});
  clearUser();
  window.location.href = '/';
}

// Role guard
function requireRole(role) {
  const user = getUser();
  if (!user) { window.location.href = '/'; return null; }
  if (user.role !== role) {
    const pages = { student: '/menu.html', owner: '/owner.html', delivery: '/delivery.html' };
    window.location.href = pages[user.role] || '/';
    return null;
  }
  return user;
}

// Stars display
function starsHtml(rating) {
  return '★'.repeat(rating) + '☆'.repeat(5 - rating);
}
