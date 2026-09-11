// 신규 작업 추가 시 여기에 jobId -> 렌더 함수를 등록한다.
const VIEW_RENDERERS = {
  delinquent_report: (container) => window.renderDelinquentReportView(container),
};

function renderView(jobId) {
  const container = document.getElementById('main-content');
  const renderFn = VIEW_RENDERERS[jobId];

  if (!renderFn) {
    container.innerHTML = `<div class="empty-view">TODO: '${jobId}' 화면 구현이 필요합니다.</div>`;
    return;
  }

  renderFn(container);
}

window.renderView = renderView;

async function initTheme() {
  const settings = await window.api.getSettings();
  const theme = settings.theme || 'light';
  applyTheme(theme);

  document.getElementById('theme-toggle').addEventListener('click', async () => {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    await window.api.setSettings({ theme: next });
  });
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  document.getElementById('theme-toggle').textContent = theme === 'dark' ? '☀️' : '🌙';
}

async function bootstrap() {
  await initTheme();
  window.sidebar.renderJobNav();
  await window.sidebar.renderInstallNav();
  window.sidebar.wireInstallModal();
  renderView(window.sidebar.JOBS[0].id);
}

document.addEventListener('DOMContentLoaded', bootstrap);
