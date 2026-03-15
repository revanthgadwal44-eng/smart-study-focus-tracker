/**
 * Smart Study Focus Tracker - Frontend Application
 * Modular Vanilla JS, Chart.js
 */
const API = '/api';
let subjectChart = null;
let timerInterval = null;
let timerSeconds = 0;
let currentSubject = null;
let sessionDistractions = 0;

// ============ API ============

async function api(path, options = {}) {
  const res = await fetch(API + path, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
    credentials: 'same-origin',
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(json?.error || `Error ${res.status}`);
  return json.data !== undefined ? json.data : json;
}

// ============ Utilities ============

function escapeHtml(s) {
  const div = document.createElement('div');
  div.textContent = String(s ?? '');
  return div.innerHTML;
}

function formatMinutes(m) {
  const n = parseInt(m, 10) || 0;
  const h = Math.floor(n / 60);
  const min = n % 60;
  return h ? `${h}h ${min}m` : `${min}m`;
}

function setLoading(el, loading) {
  if (!el) return;
  el.classList.toggle('loading', !!loading);
}

// ============ Auth ============

function showAuth() {
  document.getElementById('auth-container').classList.remove('hidden');
  document.getElementById('dashboard').classList.add('hidden');
}

function showDashboard() {
  document.getElementById('auth-container').classList.add('hidden');
  document.getElementById('dashboard').classList.remove('hidden');
  document.getElementById('user-display').textContent = `Hi, ${sessionStorage.getItem('username') || 'User'}`;
  initDashboard();
}

function setAuthError(msg) {
  const el = document.getElementById('auth-error');
  if (el) el.textContent = msg || '';
}

// ============ Dashboard Init ============

async function initDashboard() {
  setDashboardLoading(true);
  try {
    await loadSubjects();
    await refreshAll();
    startNotificationCheck();
  } finally {
    setDashboardLoading(false);
  }
}

function setDashboardLoading(loading) {
  const ids = ['weekly-progress', 'chart-container', 'heatmap', 'recent-sessions-list'];
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.toggle('loading-skeleton', loading);
  });
  const rec = document.getElementById('recommendation-text');
  if (rec) rec.textContent = loading ? 'Loading...' : rec.textContent || 'Start your first session!';
}

// ============ Subjects ============

async function loadSubjects() {
  const list = document.getElementById('subjects-list');
  const sel = document.getElementById('subject-select');
  if (!list || !sel) return;

  try {
    const { subjects } = await api('/subjects');
    const safeSubjects = Array.isArray(subjects) ? subjects : [];

    sel.innerHTML = '<option value="">Select subject...</option>' +
      safeSubjects.map(s => {
        const name = String(s?.name ?? s?.subject_name ?? '');
        const id = s?.id ?? '';
        return `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`;
      }).join('');

    if (safeSubjects.length === 0) {
      list.innerHTML = '<p class="text-muted subjects-empty">No subjects yet. Add one above!</p>';
      return;
    }

    list.innerHTML = safeSubjects.map(s => {
      const name = escapeHtml(String(s?.name ?? s?.subject_name ?? ''));
      const id = s?.id ?? '';
      return `
        <div class="subject-item" data-id="${id}">
          <span class="subject-name">${name}</span>
          <div class="subject-actions">
            <button type="button" class="edit-btn" data-edit>Edit</button>
            <button type="button" class="delete-btn" data-delete>Delete</button>
          </div>
        </div>`;
    }).join('');

    list.querySelectorAll('[data-delete]').forEach(btn => {
      btn.addEventListener('click', () => {
        const item = btn.closest('.subject-item');
        if (item) deleteSubject(parseInt(item.dataset.id, 10));
      });
    });
    list.querySelectorAll('[data-edit]').forEach(btn => {
      btn.addEventListener('click', () => {
        const item = btn.closest('.subject-item');
        if (item) {
          const nameEl = item.querySelector('.subject-name');
          const name = nameEl?.textContent ?? '';
          editSubject(parseInt(item.dataset.id, 10), name);
        }
      });
    });
  } catch (err) {
    list.innerHTML = `<p class="text-muted">Could not load subjects: ${escapeHtml(err.message)}</p>`;
  }
}

async function addSubject() {
  const input = document.getElementById('new-subject');
  const subject = input?.value?.trim() ?? '';
  if (!subject) {
    alert('Enter subject name');
    return;
  }
  try {
    await api('/subjects', { method: 'POST', body: JSON.stringify({ subject }) });
    input.value = '';
    await loadSubjects();
  } catch (err) {
    alert(err.message);
  }
}

async function editSubject(id, currentName) {
  const newName = prompt('Edit subject name:', currentName);
  if (newName === null || !newName.trim()) return;
  try {
    await api(`/subjects/${id}`, { method: 'PUT', body: JSON.stringify({ subject: newName.trim() }) });
    await loadSubjects();
  } catch (err) {
    alert(err.message);
  }
}

async function deleteSubject(id) {
  if (!confirm('Delete this subject? Sessions are kept.')) return;
  try {
    await api(`/subjects/${id}`, { method: 'DELETE' });
    await loadSubjects();
  } catch (err) {
    alert(err.message);
  }
}

// ============ Analytics (batched + individual) ============

async function refreshAll() {
  try {
    const dashboard = await api('/analytics/dashboard');
    if (dashboard) {
      applyDashboardData(dashboard);
    } else {
      await refreshAllIndividual();
    }
  } catch {
    await refreshAllIndividual();
  }

  await Promise.all([refreshGamification(), refreshRecommendation()]);
}

async function applyDashboardData(d) {
  if (d.daily) {
    document.getElementById('today-hours').textContent = formatMinutes(d.daily.total_minutes);
  }
  if (d.weekly) {
    document.getElementById('week-hours').textContent = formatMinutes(d.weekly.total_minutes);
  }
  if (typeof d.streak === 'number') {
    const el = document.getElementById('streak-value');
    if (el) el.textContent = `${d.streak} day${d.streak !== 1 ? 's' : ''}`;
  }
  if (d.weekly_progress?.days) {
    renderWeeklyProgress(d.weekly_progress.days);
  }
  if (d.subject_breakdown?.data) {
    renderSubjectChart(d.subject_breakdown.data);
  }
  if (d.focus_score) {
    const el = document.getElementById('focus-score');
    if (el) el.textContent = Math.round(d.focus_score.focus_score ?? 0);
  }
  if (d.heatmap?.data) {
    renderHeatmap(d.heatmap.data);
  }
  if (d.prediction?.predicted_minutes !== undefined) {
    const el = document.getElementById('predicted-minutes');
    if (el) el.textContent = d.prediction.predicted_minutes;
  }
  refreshDailyGoalAndGrade(d.daily?.total_minutes);
  if (d.recent_sessions?.sessions) {
    refreshRecentSessionsFromCache(d.recent_sessions.sessions);
  } else {
    await refreshRecentSessions();
  }
}

async function refreshAllIndividual() {
  const [daily, weekly, streak, focusScore, weeklyProgress, subjectBreakdown, heatmap, prediction] = await Promise.all([
    api('/analytics/daily').catch(() => ({})),
    api('/analytics/weekly').catch(() => ({})),
    api('/analytics/streak').catch(() => ({})),
    api('/analytics/focus-score').catch(() => ({})),
    api('/analytics/weekly-progress').catch(() => ({})),
    api('/analytics/subject-breakdown').catch(() => ({})),
    api('/analytics/heatmap').catch(() => ({})),
    api('/analytics/prediction').catch(() => ({})),
  ]);

  document.getElementById('today-hours').textContent = formatMinutes(daily.total_minutes);
  document.getElementById('week-hours').textContent = formatMinutes(weekly.total_minutes);
  document.getElementById('streak-value').textContent = `${streak.streak ?? 0} day${(streak.streak ?? 0) !== 1 ? 's' : ''}`;
  document.getElementById('focus-score').textContent = Math.round(focusScore.focus_score ?? 0);
  document.getElementById('predicted-minutes').textContent = prediction.predicted_minutes ?? 0;

  renderWeeklyProgress(weeklyProgress.days ?? []);
  renderSubjectChart(subjectBreakdown.data ?? []);
  renderHeatmap(heatmap.data ?? []);
  refreshDailyGoalAndGrade(daily.total_minutes);
  await refreshRecentSessions();
}

function renderWeeklyProgress(days) {
  const container = document.getElementById('weekly-progress');
  if (!container) return;
  container.classList.remove('loading-skeleton');
  if (!days?.length) {
    container.innerHTML = '<span class="text-muted">No data this week</span>';
    return;
  }
  const maxM = Math.max(1, ...days.map(d => d.minutes ?? 0));
  container.innerHTML = days.map(d => `
    <div class="weekly-day ${d.is_today ? 'today' : ''}">
      <div class="day-name">${escapeHtml(d.day)}</div>
      <div class="day-bar">
        <div class="fill" style="height: ${Math.max(4, ((d.minutes ?? 0) / maxM) * 100)}%"></div>
      </div>
      <div class="day-minutes">${d.minutes ?? 0}m</div>
    </div>`).join('');
}

function renderSubjectChart(data) {
  const canvas = document.getElementById('subject-chart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const container = document.getElementById('chart-container');
  if (container) container.classList.remove('loading-skeleton', 'chart-loading');

  if (subjectChart) subjectChart.destroy();

  if (!data?.length) {
    subjectChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['No data'],
        datasets: [{ data: [1], backgroundColor: ['#334155'] }],
      },
      options: { responsive: true, maintainAspectRatio: false },
    });
    return;
  }

  const colors = ['#2563eb', '#06b6d4', '#7c3aed', '#22c55e', '#f59e0b', '#ef4444', '#ec4899'];
  subjectChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.map(d => d.subject),
      datasets: [{
        data: data.map(d => d.minutes),
        backgroundColor: data.map((_, i) => colors[i % colors.length]),
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'right' } },
    },
  });
}

function renderHeatmap(data) {
  const container = document.getElementById('heatmap');
  if (!container) return;
  container.classList.remove('heatmap-loading');
  if (!data?.length) {
    container.innerHTML = '<span class="text-muted">No activity yet</span>';
    return;
  }
  container.innerHTML = data.map(d => {
    const m = d.minutes ?? 0;
    const level = m > 120 ? 4 : m > 60 ? 3 : m > 30 ? 2 : m > 0 ? 1 : 0;
    return `<div class="heat-${level}" title="${escapeHtml(d.date)} - ${m} min"></div>`;
  }).join('');
}

async function refreshRecentSessions() {
  const container = document.getElementById('recent-sessions-list');
  if (!container) return;
  container.classList.remove('loading-skeleton');
  try {
    const { sessions } = await api('/sessions');
    refreshRecentSessionsFromCache(sessions);
  } catch {
    container.innerHTML = '<span class="text-muted">Could not load</span>';
  }
}

function refreshRecentSessionsFromCache(sessions) {
  const container = document.getElementById('recent-sessions-list');
  if (!container) return;
  container.classList.remove('loading-skeleton');
  if (!sessions?.length) {
    container.innerHTML = '<span class="text-muted">No sessions yet. Start studying!</span>';
    return;
  }
  container.innerHTML = sessions.slice(0, 5).map(s =>
    `<div class="recent-session-item">${escapeHtml(s.subject)} — ${s.minutes}m</div>`
  ).join('');
}

async function refreshGamification() {
  try {
    const g = await api('/gamification');
    document.getElementById('level-number').textContent = g.level ?? 1;
    document.getElementById('xp-current').textContent = g.xp_in_level ?? 0;
    document.getElementById('xp-next').textContent = g.xp_for_next ?? 500;
    const pct = ((g.xp_in_level ?? 0) / (g.xp_for_next || 1)) * 100;
    const fill = document.getElementById('xp-fill');
    if (fill) fill.style.width = `${pct}%`;

    const badgesEl = document.getElementById('badges-list');
    if (badgesEl) {
      if (g.badges?.length) {
        badgesEl.innerHTML = g.badges.map(b =>
          `<span class="badge-item ${b.id}">${escapeHtml(b.name)} (${b.days}d)</span>`
        ).join('');
      } else {
        badgesEl.innerHTML = '<span class="text-muted">No badges yet. Study 3+ days for Bronze!</span>';
      }
    }
  } catch (_) {}
}

async function refreshRecommendation() {
  try {
    const { suggestion } = await api('/recommendations');
    const el = document.getElementById('recommendation-text');
    if (el) el.textContent = suggestion || 'Start your first session!';
  } catch {
    const el = document.getElementById('recommendation-text');
    if (el) el.textContent = 'Start your first session!';
  }
}

function refreshDailyGoalAndGrade(totalMinutes) {
  const DAILY_GOAL = 120;
  const minutes = parseInt(totalMinutes, 10) || 0;
  const pct = Math.min(100, (minutes / DAILY_GOAL) * 100);
  const fill = document.getElementById('daily-goal-fill');
  const text = document.getElementById('daily-goal-text');
  const grade = document.getElementById('productivity-grade');
  if (fill) fill.style.width = `${pct}%`;
  if (text) text.textContent = `${minutes} / ${DAILY_GOAL} min`;
  if (grade) {
    let g = 'C';
    if (minutes > 180) g = 'A+';
    else if (minutes > 120) g = 'A';
    else if (minutes > 60) g = 'B';
    grade.textContent = totalMinutes === undefined ? '—' : g;
  }
}

// ============ Timer ============

const radius = 70;
const circumference = 2 * Math.PI * radius;
const circle = document.querySelector('.progress-ring-circle');
if (circle) {
  circle.style.strokeDasharray = circumference;
  circle.style.strokeDashoffset = circumference;
}

function updateRing(seconds) {
  const progress = seconds % 60;
  const offset = circumference * (1 - progress / 60);
  if (circle) circle.style.strokeDashoffset = offset;
}

function updateTimerDisplay() {
  const el = document.getElementById('timer-display');
  if (!el) return;
  const h = Math.floor(timerSeconds / 3600);
  const m = Math.floor((timerSeconds % 3600) / 60);
  const s = timerSeconds % 60;
  el.textContent = [h, m, s].map(x => String(x).padStart(2, '0')).join(':');
}

// ============ Event Listeners ============

function bindAuthListeners() {
  document.getElementById('auth-tabs')?.addEventListener('click', (e) => {
    const tab = e.target?.dataset?.tab;
    if (!tab) return;
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
    document.getElementById('login-form')?.classList.toggle('hidden', tab !== 'login');
    document.getElementById('signup-form')?.classList.toggle('hidden', tab !== 'signup');
    setAuthError('');
  });

  document.getElementById('login-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    setAuthError('');
    const form = e.target;
    try {
      const res = await api('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email: form.email.value.trim(), password: form.password.value }),
      });
      const user = res?.user ?? res?.data?.user;
      const username = user?.username ?? user?.name;
      if (!username) {
        setAuthError('Login failed - invalid response');
        return;
      }
      sessionStorage.setItem('username', username);
      showDashboard();
    } catch (err) {
      setAuthError(err.message);
    }
  });

  document.getElementById('signup-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    setAuthError('');
    const form = e.target;
    try {
      const res = await api('/auth/signup', {
        method: 'POST',
        body: JSON.stringify({
          username: form.username.value.trim(),
          email: form.email.value.trim(),
          password: form.password.value,
        }),
      });
      const user = res?.user ?? res?.data?.user;
      const username = user?.username ?? user?.name;
      if (!username) {
        setAuthError('Signup failed - invalid response');
        return;
      }
      sessionStorage.setItem('username', username);
      showDashboard();
    } catch (err) {
      setAuthError(err.message);
    }
  });

  document.getElementById('logout-btn')?.addEventListener('click', async () => {
    try {
      await api('/auth/logout', { method: 'POST' });
    } catch (_) {}
    sessionStorage.removeItem('username');
    showAuth();
  });
}

function bindSubjectListeners() {
  document.getElementById('add-subject-btn')?.addEventListener('click', addSubject);
}

function bindTimerListeners() {
  document.getElementById('start-timer')?.addEventListener('click', () => {
    const subject = document.getElementById('subject-select')?.value ?? '';
    if (!subject) {
      alert('Please select a subject first.');
      return;
    }
    currentSubject = subject;
    sessionDistractions = 0;
    timerSeconds = 0;
    updateTimerDisplay();
    updateRing(0);
    document.getElementById('start-timer').disabled = true;
    document.getElementById('stop-timer').disabled = false;
    timerInterval = setInterval(() => {
      timerSeconds++;
      updateTimerDisplay();
      updateRing(timerSeconds);
    }, 1000);
  });

  document.getElementById('stop-timer')?.addEventListener('click', async () => {
    if (!timerInterval) return;
    clearInterval(timerInterval);
    timerInterval = null;
    document.getElementById('start-timer').disabled = false;
    document.getElementById('stop-timer').disabled = true;
    const notes = document.getElementById('session-notes')?.value?.trim() ?? '';
    const savedSeconds = timerSeconds;
    try {
      await api('/sessions', {
        method: 'POST',
        body: JSON.stringify({
          subject: currentSubject,
          duration_seconds: timerSeconds,
          notes: notes || undefined,
          distractions: sessionDistractions,
        }),
      });
      if (savedSeconds >= 1800) alert('🏆 30+ minute focus session completed!');
      document.getElementById('session-notes').value = '';
      timerSeconds = 0;
      updateRing(0);
      updateTimerDisplay();
      await refreshAll();
      await loadSubjects();
    } catch (err) {
      alert('Failed to save session: ' + err.message);
    }
  });

  document.getElementById('distraction-btn')?.addEventListener('click', () => {
    if (!timerInterval) return;
    sessionDistractions++;
    const btn = document.getElementById('distraction-btn');
    if (btn) btn.title = `Distractions: ${sessionDistractions}`;
    if (sessionDistractions >= 3) alert('Too many distractions! Refocus 🔥');
  });
}

function bindReportListeners() {
  document.getElementById('download-pdf')?.addEventListener('click', async () => {
    try {
      const res = await fetch(API + '/reports/weekly-pdf', { credentials: 'same-origin' });
      if (!res.ok) throw new Error('Failed to generate report');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `weekly-report-${new Date().toISOString().slice(0, 10)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to download report: ' + err.message);
    }
  });
}

// ============ Notifications ============

let notificationCheckInterval = null;
function startNotificationCheck() {
  if (notificationCheckInterval) clearInterval(notificationCheckInterval);
  notificationCheckInterval = setInterval(checkNotification, 60 * 60 * 1000);
  checkNotification();
}

async function checkNotification() {
  try {
    const { studied_today, should_remind } = await api('/notifications/check');
    if (should_remind && !studied_today && 'Notification' in window) {
      if (Notification.permission === 'granted') {
        new Notification('Smart Study Focus Tracker', {
          body: "You haven't studied today. Start a session to keep your streak!",
        });
      } else if (Notification.permission === 'default') {
        Notification.requestPermission();
      }
    }
  } catch (_) {}
}

// ============ Init ============

async function checkAuth() {
  try {
    const res = await api('/auth/me');
    const user = res?.user ?? res?.data?.user;
    const username = user?.username ?? user?.name ?? 'User';
    sessionStorage.setItem('username', username);
    showDashboard();
    return true;
  } catch {
    showAuth();
    return false;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
  bindAuthListeners();
  bindSubjectListeners();
  bindTimerListeners();
  bindReportListeners();
  checkAuth();
});
