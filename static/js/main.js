// Theme toggle
function toggleTheme() {
  const html = document.documentElement;
  const current = html.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  document.getElementById('theme-icon').className = next === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
}

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
  let overlay = document.getElementById('sidebar-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    overlay.id = 'sidebar-overlay';
    overlay.onclick = () => {
      document.getElementById('sidebar').classList.remove('open');
      overlay.classList.remove('show');
    };
    document.body.appendChild(overlay);
  }
  overlay.classList.toggle('show');
}

// Apply saved theme
(function() {
  const saved = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
  window.addEventListener('DOMContentLoaded', () => {
    const icon = document.getElementById('theme-icon');
    if (icon) icon.className = saved === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
  });
})();

// Chart defaults
function applyChartDefaults() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  Chart.defaults.color = isDark ? '#9b9890' : '#6b6860';
  Chart.defaults.borderColor = isDark ? '#2e2c28' : '#e8e6df';
  Chart.defaults.font.family = "'DM Sans', sans-serif";
  Chart.defaults.font.size = 12;
}

function getCSSVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

// Create a sparkline chart
function createSparkline(canvasId, data, color) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map((_, i) => i),
      datasets: [{
        data: data,
        borderColor: color || '#1a7a5e',
        borderWidth: 2,
        fill: true,
        backgroundColor: (color || '#1a7a5e') + '18',
        tension: 0.4,
        pointRadius: 0,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      scales: { x: { display: false }, y: { display: false } },
      animation: false,
    }
  });
}

// Format currency PKR
function formatPKR(val) {
  if (val >= 1000) return 'PKR ' + (val / 1000).toFixed(1) + 'k';
  return 'PKR ' + Math.round(val).toLocaleString();
}

// Get AI badge HTML
function aiBadge(rec) {
  const map = {
    buy: ['fa-solid fa-fire', '🔥 Buy Now'],
    wait: ['fa-solid fa-clock', '⏳ Wait'],
    buy_soon: ['fa-solid fa-bolt', '⚡ Buy Soon'],
    neutral: ['fa-solid fa-minus', 'Hold'],
  };
  const [icon, label] = map[rec] || map.neutral;
  return `<span class="ai-badge ai-${rec}"><i class="${icon}"></i> ${label}</span>`;
}

// Get change badge
function changeBadge(pct) {
  if (pct < 0) return `<span class="badge badge-success"><i class="fa-solid fa-arrow-down"></i> ${Math.abs(pct).toFixed(1)}%</span>`;
  if (pct > 0) return `<span class="badge badge-danger"><i class="fa-solid fa-arrow-up"></i> ${pct.toFixed(1)}%</span>`;
  return `<span class="badge badge-neutral">0%</span>`;
}

// Deal score color
function scoreColor(s) {
  if (s >= 70) return '#1a7a5e';
  if (s >= 40) return '#c97a1a';
  return '#c0392b';
}
