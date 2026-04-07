/**
 * DevBrain Dashboard — JavaScript
 * Handles auth, API calls, and dynamic UI rendering
 */

// ─── Config ────────────────────────────────────────────────────────────────
const API_BASE = 'http://127.0.0.1:8001/api';

// ─── State ─────────────────────────────────────────────────────────────────
let authToken = localStorage.getItem('devbrain_token') || null;
let currentUser = null;

// ─── Init ──────────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  if (authToken) {
    showDashboard();
    loadAllData();
  } else {
    showAuth();
  }
  buildQuickAddGrid();
});

// ─── Auth ──────────────────────────────────────────────────────────────────
function showAuth() {
  document.getElementById('auth-screen').classList.remove('hidden');
  document.getElementById('dashboard').classList.remove('active');
  document.getElementById('dashboard').classList.add('hidden');
}

function showDashboard() {
  document.getElementById('auth-screen').classList.add('hidden');
  document.getElementById('dashboard').classList.remove('hidden');
  document.getElementById('dashboard').classList.add('active');
}

function switchTab(tab) {
  document.getElementById('tab-login').classList.toggle('active', tab === 'login');
  document.getElementById('tab-register').classList.toggle('active', tab === 'register');
  document.getElementById('login-form').classList.toggle('hidden', tab !== 'login');
  document.getElementById('register-form').classList.toggle('hidden', tab !== 'register');
}

async function handleLogin(e) {
  e.preventDefault();
  const btn = document.getElementById('login-btn');
  const errEl = document.getElementById('login-error');
  errEl.classList.add('hidden');
  btn.disabled = true;
  btn.innerHTML = '<span>Signing in…</span>';

  try {
    const formData = new URLSearchParams();
    formData.append('username', document.getElementById('login-email').value);
    formData.append('password', document.getElementById('login-password').value);

    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Login failed');

    authToken = data.access_token;
    localStorage.setItem('devbrain_token', authToken);
    showDashboard();
    await loadAllData();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.classList.remove('hidden');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span>Sign In</span><span class="btn-arrow">→</span>';
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const btn = document.getElementById('reg-btn');
  const errEl = document.getElementById('reg-error');
  errEl.classList.add('hidden');
  btn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: document.getElementById('reg-email').value,
        username: document.getElementById('reg-username').value,
        password: document.getElementById('reg-password').value,
        full_name: document.getElementById('reg-fullname').value || null,
      }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Registration failed');

    authToken = data.access_token;
    localStorage.setItem('devbrain_token', authToken);
    showDashboard();
    await loadAllData();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.classList.remove('hidden');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span>Create Account</span><span class="btn-arrow">→</span>';
  }
}

function logout() {
  authToken = null;
  currentUser = null;
  localStorage.removeItem('devbrain_token');
  showAuth();
}

// ─── API Helper ─────────────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });

  if (res.status === 401) {
    logout();
    throw new Error('Session expired. Please log in again.');
  }

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'API error');
  return data;
}

// ─── Load All Data ──────────────────────────────────────────────────────────
async function loadAllData() {
  try {
    await Promise.all([
      loadProfile(),
      loadDashboard(),
      loadTodayIntelligence(),
    ]);
    // Load section-specific data lazily
    loadSkills();
    loadRecommendations();
    loadEvents();
    loadSnowflakeAnalytics();
  } catch (err) {
    console.error('Load error:', err);
  }
}

async function loadTodayIntelligence() {
  try {
    const [summaryRes, topicsRes, recsRes] = await Promise.all([
      apiFetch('/dashboard/daily-summary'),
      apiFetch('/dashboard/top-topics'),
      apiFetch('/recommendations/')
    ]);

    // Health Score
    document.getElementById('ui-health-score').textContent = summaryRes.learning_health ?? '--';
    
    // Daily Summary
    document.getElementById('ui-coding-time').textContent = (summaryRes.coding_time || 0) + ' hrs';
    document.getElementById('ui-learning-time').textContent = (summaryRes.learning_time || 0) + ' hrs';
    document.getElementById('ui-focus-time').textContent = (summaryRes.focus_time || 0) + ' hrs';
    
    // Top Topics
    const topicsList = document.getElementById('ui-top-topics');
    if (topicsRes.topics && topicsRes.topics.length > 0) {
      topicsList.innerHTML = topicsRes.topics.map(t => `<li>${t.topic} <span style="color:var(--text-secondary)">(${t.score.toFixed(1)})</span></li>`).join('');
    } else {
      topicsList.innerHTML = `<li style="color:var(--text-secondary)">No topics today</li>`;
    }

    // Insights
    const insightsList = document.getElementById('ui-behavioral-insights');
    if (recsRes.behavioral_insights && recsRes.behavioral_insights.length > 0) {
      insightsList.innerHTML = recsRes.behavioral_insights.map(i => `<li>${i}</li>`).join('');
    } else {
      insightsList.innerHTML = `<li style="color:var(--text-secondary); list-style:none; margin-left:-1.2rem">No insights yet.</li>`;
    }
  } catch (err) {
    console.error('Intelligence load error:', err);
  }
}

async function loadProfile() {
  try {
    currentUser = await apiFetch('/auth/me');
    const initials = (currentUser.full_name || currentUser.username)
      .split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);

    document.getElementById('sidebar-username').textContent = currentUser.username;
    document.getElementById('sidebar-avatar').textContent = initials;
  } catch (err) {
    console.error('Profile load error:', err);
  }
}

async function loadDashboard() {
  try {
    const data = await apiFetch('/dashboard/');

    // Stats
    const s = data.stats;
    document.getElementById('stat-events').textContent = s.total_events;
    document.getElementById('stat-week').textContent = `+${s.events_this_week} this week`;
    document.getElementById('stat-active-domains').textContent = s.active_domains;
    document.getElementById('stat-top-tech').textContent = s.top_technology ? `Top: ${s.top_technology}` : '—';
    document.getElementById('stat-overall-score').textContent = `${s.overall_skill_score}`;
    document.getElementById('stat-level').textContent = scoreToLevel(s.overall_skill_score);
    document.getElementById('stat-sources').textContent = s.connected_sources.length;
    document.getElementById('stat-sources-list').textContent = s.connected_sources.length
      ? s.connected_sources.join(', ')
      : 'No sources yet';

    document.getElementById('streak-count').textContent = s.learning_streak_days;
    document.getElementById('overall-score-header').textContent = s.overall_skill_score;

    // Activity chart
    renderActivityChart(data.activity_last_30_days);

    // Top skills
    renderTopSkills(data.top_skills);

    // Recent events
    renderRecentEvents(data.recent_events);

  } catch (err) {
    console.error('Dashboard load error:', err);
  }
}

async function loadSkills() {
  try {
    const [graphData, gapsData] = await Promise.all([
      apiFetch('/skills/'),
      apiFetch('/skills/gaps'),
    ]);
    renderSkillGraph(graphData);
    renderGaps(gapsData);
  } catch (err) {
    console.error('Skills load error:', err);
  }
}

async function loadRecommendations() {
  try {
    const data = await apiFetch('/recommendations/');
    renderRecommendations(data);
  } catch (err) {
    console.error('Recs load error:', err);
  }
}

async function loadSnowflakeAnalytics() {
  try {
    // We fetch these without blocking the main dashboard
    const [activityRes, trendingRes] = await Promise.all([
      apiFetch('/analytics/learning-activity').catch(() => null),
      apiFetch('/analytics/trending-technologies').catch(() => null),
    ]);

    if (activityRes && activityRes.activity) {
      renderActivityChart(activityRes.activity.map(a => ({
        date: a.DAY,
        event_count: a.LEARNING_EVENTS
      })));
    }

    if (trendingRes && trendingRes.trending) {
      renderTopSkills(trendingRes.trending.map(t => ({
        technology: t.TECHNOLOGY,
        score: Math.min(100, t.HITS * 10), // Mock score calculation based on hits for visual
        level: 'Trending'
      })));

      const headerTitle = document.querySelector('#section-overview .two-col-grid .glass-card:nth-child(2) .card-header .card-title');
      if (headerTitle) headerTitle.textContent = "Trending Technologies (Snowflake)";
    }

    const activityHeader = document.querySelector('#section-overview .two-col-grid .glass-card:nth-child(1) .card-header .card-title');
    if (activityHeader) activityHeader.textContent = "Learning Activity (Snowflake)";

  } catch (e) {
    console.error('Snowflake analytics error:', e);
  }
}

async function loadEvents() {
  try {
    const data = await apiFetch('/events/?limit=100');
    renderEventsTable(data.items);
  } catch (err) {
    console.error('Events load error:', err);
  }
}

// ─── Navigation ─────────────────────────────────────────────────────────────
const SECTION_META = {
  overview: { title: 'Overview', subtitle: 'Your learning at a glance' },
  skills: { title: 'Skill Graph', subtitle: 'Domain → Technology → Concept' },
  events: { title: 'Knowledge Events', subtitle: 'Every learning signal captured' },
  recommendations: { title: 'Recommendations', subtitle: 'Personalised next steps' },
  ingest: { title: 'Add Learning', subtitle: 'Log a learning event manually' },
};

function showSection(name, navEl) {
  // Hide all sections
  document.querySelectorAll('.section').forEach(s => {
    s.classList.add('hidden');
    s.classList.remove('active');
  });

  // Deactivate nav
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  // Show target
  const section = document.getElementById(`section-${name}`);
  if (section) {
    section.classList.remove('hidden');
    section.classList.add('active');
  }

  if (navEl) navEl.classList.add('active');

  // Update header
  const meta = SECTION_META[name] || {};
  document.getElementById('page-title').textContent = meta.title || name;
  document.getElementById('page-subtitle').textContent = meta.subtitle || '';

  return false; // Prevent anchor navigation
}

// ─── Render: Activity Chart ──────────────────────────────────────────────────
function renderActivityChart(activity) {
  const container = document.getElementById('activity-chart');
  if (!activity || activity.length === 0) {
    container.innerHTML = '<div class="chart-empty">No activity yet</div>';
    return;
  }

  const maxCount = Math.max(...activity.map(a => a.event_count), 1);
  container.innerHTML = activity.map(day => {
    const pct = Math.max(6, (day.event_count / maxCount) * 100);
    return `<div class="chart-bar" style="height:${pct}%"
      title="${day.date}: ${day.event_count} event${day.event_count !== 1 ? 's' : ''}"></div>`;
  }).join('');
}

// ─── Render: Top Skills ──────────────────────────────────────────────────────
function renderTopSkills(skills) {
  const container = document.getElementById('top-skills-list');
  if (!skills || skills.length === 0) {
    container.innerHTML = '<div class="empty-state">No skills yet</div>';
    return;
  }

  container.innerHTML = skills.map(s => `
    <div class="skill-row">
      <div class="skill-tech" title="${s.technology}">${s.technology}</div>
      <div class="skill-bar-bg">
        <div class="skill-bar-fill" style="width:${s.score}%"></div>
      </div>
      <div class="skill-score">${s.score}</div>
      <span class="skill-level-badge ${levelClass(s.level)}">${s.level}</span>
    </div>
  `).join('');
}

// ─── Render: Recent Events ────────────────────────────────────────────────────
function renderRecentEvents(events) {
  const container = document.getElementById('recent-events-list');
  if (!events || events.length === 0) {
    container.innerHTML = '<div class="empty-state">No events yet</div>';
    return;
  }

  const sourceIcons = { browser: '🌐', github: '⬡', youtube: '▶', notes: '📝', manual: '✎' };

  container.innerHTML = events.slice(0, 5).map(e => `
    <div class="event-row">
      <div class="event-source-icon source-${e.source}">${sourceIcons[e.source] || '◎'}</div>
      <div style="flex:1">
        <div class="event-topic">${escHtml(e.topic)}</div>
        <div class="event-domain">${escHtml(e.domain)}</div>
      </div>
      ${e.technology ? `<span class="event-tech-tag">${escHtml(e.technology)}</span>` : ''}
    </div>
  `).join('');
}

// ─── Render: Skill Graph ─────────────────────────────────────────────────────
function renderSkillGraph(data) {
  const container = document.getElementById('skill-graph-container');
  const subtitle = document.getElementById('skills-subtitle');
  subtitle.textContent = `${data.total_skills} skills across ${data.domains.length} domains · Overall: ${data.overall_score}/100`;

  if (!data.domains || data.domains.length === 0) {
    container.innerHTML = '<div class="empty-state">No skills yet. Log learning events to build your skill graph!</div>';
    return;
  }

  container.innerHTML = data.domains.map(domain => `
    <div class="domain-block">
      <div class="domain-header">
        <span class="domain-name">${escHtml(domain.domain)}</span>
        <span class="domain-score-badge">${domain.domain_score.toFixed(0)}/100</span>
      </div>
      <div class="techs-grid">
        ${domain.technologies.map(tech => `
          <div class="tech-card">
            <div class="tech-card-header">
              <span class="tech-card-name">${escHtml(tech.technology)}</span>
              <span class="tech-card-score">${tech.score.toFixed(0)}</span>
            </div>
            <div class="tech-card-bar">
              <div class="tech-card-bar-fill" style="width:${tech.score}%"></div>
            </div>
            <div class="tech-card-meta">
              <span class="tech-card-level ${levelClass(tech.level)}" style="padding:0.1rem 0.4rem;border-radius:999px;font-size:0.65rem">
                ${tech.level}
              </span>
              <span class="tech-card-events">${tech.event_count} events</span>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `).join('');
}

// ─── Render: Gaps ────────────────────────────────────────────────────────────
function renderGaps(data) {
  const container = document.getElementById('gaps-container');
  if (!data.gaps || data.gaps.length === 0) {
    container.innerHTML = '<div class="empty-state">No gaps identified. Keep logging events!</div>';
    return;
  }

  container.innerHTML = data.gaps.slice(0, 10).map(g => `
    <div class="gap-row">
      <div class="gap-priority ${g.priority}"></div>
      <div class="gap-tech">${escHtml(g.technology)}</div>
      <div class="gap-domain">${escHtml(g.domain)}</div>
      <div class="gap-topics">
        ${g.recommended_topics.slice(0, 3).map(t =>
    `<span class="gap-topic-tag">${escHtml(t)}</span>`
  ).join('')}
      </div>
      <div class="gap-score">${g.current_score.toFixed(0)}</div>
    </div>
  `).join('');
}

// ─── Render: Events Table ────────────────────────────────────────────────────
function renderEventsTable(events) {
  const container = document.getElementById('events-table-container');
  if (!events || events.length === 0) {
    container.innerHTML = '<div class="empty-state">No events yet</div>';
    return;
  }

  const sourceIcons = { browser: '🌐', github: '⬡', youtube: '▶', notes: '📝', manual: '✎' };

  container.innerHTML = `
    <table class="events-table">
      <thead>
        <tr>
          <th>Topic</th>
          <th>Technology</th>
          <th>Domain</th>
          <th>Depth</th>
          <th>Source</th>
          <th>Confidence</th>
          <th>Date</th>
        </tr>
      </thead>
      <tbody>
        ${events.map(e => `
          <tr>
            <td style="font-weight:600">${escHtml(e.topic)}</td>
            <td>${e.technology ? `<span class="event-tech-tag">${escHtml(e.technology)}</span>` : '—'}</td>
            <td style="color:var(--text-secondary)">${escHtml(e.domain)}</td>
            <td><span class="skill-level-badge ${levelClass(depthToLevel(e.depth))}" style="padding:0.1rem 0.5rem">${e.depth}</span></td>
            <td><span class="event-source-icon source-${e.source}" style="display:inline-flex">${sourceIcons[e.source] || '◎'} ${e.source}</span></td>
            <td><span style="color:var(--teal)">${Math.round(e.confidence_score * 100)}%</span></td>
            <td style="color:var(--text-muted);font-size:0.75rem">${new Date(e.created_at).toLocaleDateString()}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

// ─── Render: Recommendations ─────────────────────────────────────────────────
function renderRecommendations(data) {
  const container = document.getElementById('recs-container');
  const sections = [
    { key: 'weekly_focus', label: '🎯 Weekly Focus', items: data.weekly_focus },
    { key: 'explore_next', label: '🚀 Explore Next', items: data.explore_next },
    { key: 'quick_wins', label: '⚡ Quick Wins', items: data.quick_wins },
  ];

  const hasAny = sections.some(s => s.items && s.items.length > 0);
  if (!hasAny) {
    container.innerHTML = '<div class="empty-state">No recommendations yet. Log more learning events to get personalised suggestions!</div>';
    return;
  }

  container.innerHTML = sections
    .filter(s => s.items && s.items.length > 0)
    .map(s => `
      <div>
        <div class="recs-section-title">${s.label}</div>
        <div class="rec-cards">
          ${s.items.map(r => `
            <div class="rec-card priority-${r.priority}">
              <div class="rec-card-header">
                <div class="rec-card-title">${escHtml(r.title)}</div>
                <span class="rec-type-badge type-${r.resource_type}">${r.resource_type}</span>
              </div>
              <div class="rec-card-desc">${escHtml(r.description)}</div>
              <div class="rec-card-reason">${escHtml(r.reason)}</div>
              <div class="rec-card-footer">
                <span class="rec-tech-badge">${escHtml(r.technology)}</span>
                <div style="display:flex;gap:0.75rem;align-items:center">
                  ${r.estimated_hours ? `<span class="rec-hours">~${r.estimated_hours}h</span>` : ''}
                  ${r.resource_url ? `<a href="${r.resource_url}" target="_blank" rel="noopener" class="rec-link">Open →</a>` : ''}
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `).join('');
}

// ─── Ingest Form ─────────────────────────────────────────────────────────────
async function handleIngest(e) {
  e.preventDefault();
  const btn = document.getElementById('ingest-btn');
  const successEl = document.getElementById('ingest-success');
  const errEl = document.getElementById('ingest-error');
  successEl.classList.add('hidden');
  errEl.classList.add('hidden');
  btn.disabled = true;

  const confidence = parseInt(document.getElementById('ingest-confidence').value) / 100;

  try {
    await apiFetch('/events/', {
      method: 'POST',
      body: JSON.stringify({
        topic: document.getElementById('ingest-topic').value,
        technology: document.getElementById('ingest-technology').value || null,
        domain: document.getElementById('ingest-domain').value,
        concept: document.getElementById('ingest-concept').value || null,
        source: document.getElementById('ingest-source').value,
        depth: document.getElementById('ingest-depth').value,
        source_url: document.getElementById('ingest-url').value || null,
        confidence_score: confidence,
      }),
    });

    successEl.classList.remove('hidden');
    document.getElementById('ingest-form').reset();
    document.getElementById('confidence-label').textContent = '50%';

    // Refresh data in background
    setTimeout(() => {
      loadDashboard();
      loadSkills();
      loadEvents();
      loadRecommendations();
    }, 500);
  } catch (err) {
    errEl.textContent = err.message;
    errEl.classList.remove('hidden');
  } finally {
    btn.disabled = false;
  }
}

// ─── Quick Add Grid ────────────────────────────────────────────────────────
const QUICK_TECHS = [
  { name: 'React', domain: 'Frontend', icon: '⚛', depth: 'intermediate' },
  { name: 'TypeScript', domain: 'Frontend', icon: 'TS', depth: 'intermediate' },
  { name: 'Python', domain: 'Backend', icon: '🐍', depth: 'intermediate' },
  { name: 'FastAPI', domain: 'Backend', icon: '⚡', depth: 'beginner' },
  { name: 'Docker', domain: 'DevOps', icon: '🐳', depth: 'beginner' },
  { name: 'SQL', domain: 'Data', icon: '🗄', depth: 'intermediate' },
  { name: 'PyTorch', domain: 'AI/ML', icon: '🔥', depth: 'beginner' },
  { name: 'Next.js', domain: 'Frontend', icon: '▲', depth: 'intermediate' },
  { name: 'PostgreSQL', domain: 'Backend', icon: '🐘', depth: 'beginner' },
  { name: 'Kubernetes', domain: 'DevOps', icon: '⎈', depth: 'beginner' },
];

function buildQuickAddGrid() {
  const grid = document.getElementById('quick-add-grid');
  if (!grid) return;
  grid.innerHTML = QUICK_TECHS.map(t => `
    <button class="quick-add-btn" onclick="quickLog('${t.name}','${t.domain}','${t.depth}')">
      <span class="quick-add-icon">${t.icon}</span>
      <span class="quick-add-name">${t.name}</span>
      <span class="quick-add-domain">${t.domain}</span>
    </button>
  `).join('');
}

async function quickLog(technology, domain, depth) {
  const successEl = document.getElementById('ingest-success');
  const errEl = document.getElementById('ingest-error');
  successEl.classList.add('hidden');
  errEl.classList.add('hidden');

  try {
    await apiFetch('/events/', {
      method: 'POST',
      body: JSON.stringify({
        topic: `${technology} study session`,
        technology,
        domain,
        depth,
        source: 'manual',
        confidence_score: 0.65,
      }),
    });
    successEl.textContent = `✓ Logged ${technology} session! Skill graph updated.`;
    successEl.classList.remove('hidden');
    setTimeout(() => {
      loadDashboard();
      loadSkills();
      loadEvents();
      loadRecommendations();
    }, 400);
  } catch (err) {
    errEl.textContent = err.message;
    errEl.classList.remove('hidden');
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function levelClass(level) {
  return 'level-' + (level || 'novice').toLowerCase().replace(/\s+/g, '');
}

function depthToLevel(depth) {
  const map = { beginner: 'Beginner', intermediate: 'Intermediate', advanced: 'Advanced' };
  return map[depth] || 'Beginner';
}

function scoreToLevel(score) {
  if (score >= 80) return 'Expert';
  if (score >= 60) return 'Advanced';
  if (score >= 40) return 'Intermediate';
  if (score >= 20) return 'Beginner';
  return 'Novice';
}

// ─── Chatbot Logic ──────────────────────────────────────────────────────────────
window.toggleChatbot = toggleChatbot;
window.sendChatMessage = sendChatMessage;
window.handleChatEnter = handleChatEnter;

function toggleChatbot() {
  const widget = document.getElementById('chatbot-widget');
  widget.classList.toggle('collapsed');
}

function handleChatEnter(e) {
  if (e.key === 'Enter') {
    sendChatMessage();
  }
}

async function sendChatMessage() {
  const input = document.getElementById('chat-input');
  const msg = input.value.trim();
  if (!msg) return;

  const messagesDiv = document.getElementById('chatbot-messages');

  // Apppend User Message
  messagesDiv.innerHTML += `<div class="chat-message user-message">${escHtml(msg)}</div>`;
  input.value = '';
  messagesDiv.scrollTop = messagesDiv.scrollHeight;

  // Loading indicator
  const loadingId = 'loading-' + Date.now();
  messagesDiv.innerHTML += `<div id="${loadingId}" class="chat-message ai-message" style="opacity: 0.7">Thinking...</div>`;
  messagesDiv.scrollTop = messagesDiv.scrollHeight;

  try {
    const res = await apiFetch('/chat/', {
      method: 'POST',
      body: JSON.stringify({ message: msg })
    });

    document.getElementById(loadingId).remove();
    // Parse newlines roughly to HTML breaks for basic readability
    const formattedReply = escHtml(res.response).replace(/\n/g, '<br>');
    messagesDiv.innerHTML += `<div class="chat-message ai-message">${formattedReply}</div>`;
  } catch (e) {
    document.getElementById(loadingId).remove();
    messagesDiv.innerHTML += `<div class="chat-message ai-message" style="color:#ff6b6b">Error: ${escHtml(e.message)}</div>`;
  }
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

