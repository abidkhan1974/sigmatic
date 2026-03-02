// Sigmatic monitoring dashboard - Phase 3 placeholder
(async function () {
  const badge = document.getElementById('status-badge');
  try {
    const res = await fetch('/v1/health');
    const data = await res.json();
    badge.textContent = data.status === 'healthy' ? 'Healthy' : 'Degraded';
    badge.style.background = data.status === 'healthy' ? '#238636' : '#da3633';
  } catch {
    badge.textContent = 'Unreachable';
    badge.style.background = '#da3633';
  }
})();
