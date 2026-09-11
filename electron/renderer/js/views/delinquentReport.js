const STATUS_LABEL_KO = {
  pending: '대기중',
  processing: '처리중',
  success: '완료',
  failed: '실패',
};

const STATUS_CLASS_MAP = {
  대기중: 'pending',
  처리중: 'processing',
  완료: 'success',
  실패: 'failed',
};

function todayLocalISODate() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function addDaysISODate(isoDate, days) {
  const [y, m, d] = isoDate.split('-').map(Number);
  const date = new Date(y, m - 1, d);
  date.setDate(date.getDate() + days);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str ?? '';
  return div.innerHTML;
}

function renderDelinquentReportView(container) {
  container.innerHTML = `
    <section class="panel">
      <div class="field-label login-test-label">LMS 로그인 테스트 (먼저 확인)</div>
      <div class="inline-row">
        <button id="login-test-btn" class="btn btn-primary">로그인 테스트 시작</button>
        <button id="login-test-stop-btn" class="btn btn-danger" disabled>중단</button>
        <span id="login-test-status" class="status-badge status-pending">대기중</span>
      </div>
    </section>

    <section class="panel">
      <div class="field-label login-test-label">직접 기간 조회 (수동 확인용, 로그인 → 일일정산달력 이동 → 조회까지 한 번에 테스트)</div>
      <div class="inline-row">
        <input type="date" id="manual-sdate" />
        <span>~</span>
        <input type="date" id="manual-edate" />
        <button id="manual-query-btn" class="btn btn-primary">조회</button>
        <button id="manual-query-stop-btn" class="btn btn-danger" disabled>중단</button>
        <span id="manual-query-status" class="status-badge status-pending">대기중</span>
      </div>
      <div class="field-hint" id="manual-query-result"></div>
    </section>

    <div class="view-header">
      <h1>미납자 관리</h1>
      <div class="job-controls">
        <button id="start-btn" class="btn btn-primary">보고서 생성 시작</button>
        <button id="pause-btn" class="btn btn-ghost" disabled>일시정지</button>
        <button id="stop-btn" class="btn btn-danger" disabled>중단</button>
        <button id="copy-btn" class="btn btn-ghost" disabled>결과 클립보드 복사</button>
      </div>
    </div>

    <section class="panel criteria-panel">
      <div class="field">
        <label class="field-label" for="reference-date">기준일 (이 날짜의 전날까지 집계)</label>
        <input type="date" id="reference-date" />
      </div>
      <div class="field-hint">
        2023-01-01부터 기준일의 전날까지를 6개월 단위로 나눠 자동 조회하고(전체 합산),
        기준일의 전날이 속한 달(부분월)과 그 이전 4개월도 함께 조회합니다.
      </div>
    </section>

    <section class="panel">
      <div class="field-label">월별 현황 (최근)</div>
      <table class="dashboard-table" id="months-table">
        <thead><tr><th>기간</th><th>상태</th><th>미납자 수</th></tr></thead>
        <tbody id="months-table-body"><tr><td colspan="3" class="empty">시작 버튼을 눌러주세요.</td></tr></tbody>
      </table>
    </section>

    <section class="panel">
      <div class="field-label">6개월 구간별 현황</div>
      <table class="dashboard-table" id="chunks-table">
        <thead><tr><th>기간</th><th>상태</th><th>미납자 수</th></tr></thead>
        <tbody id="chunks-table-body"><tr><td colspan="3" class="empty">시작 버튼을 눌러주세요.</td></tr></tbody>
      </table>
    </section>

    <section class="panel">
      <div class="field-label login-test-label">보고서 요약 (아래 복사 버튼으로 바로 공유 가능)</div>
      <pre id="report-output" class="log-output">아직 생성된 보고서가 없습니다.</pre>
    </section>

    <section class="panel">
      <div class="field-label login-test-label">실행 로그</div>
      <div class="log-toolbar">
        <input type="text" id="log-search" class="roster-search-input" placeholder="로그 검색... (일치하는 줄만 표시)" />
        <span id="log-search-count" class="tutor-roster-count"></span>
      </div>
      <div id="log-output" class="log-output"></div>
    </section>
  `;

  // ---- 로그 패널 ----
  const logOutput = document.getElementById('log-output');
  const logSearchInput = document.getElementById('log-search');
  const logSearchCount = document.getElementById('log-search-count');
  let logSearchQuery = '';

  function applyLogLineVisibility(line) {
    const matches = !logSearchQuery || line.textContent.toLowerCase().includes(logSearchQuery);
    line.hidden = !matches;
  }

  function updateLogSearchCount() {
    if (!logSearchQuery) {
      logSearchCount.textContent = '';
      return;
    }
    const total = logOutput.children.length;
    const shown = logOutput.querySelectorAll('.log-line:not([hidden])').length;
    logSearchCount.textContent = `${shown} / ${total}줄 일치`;
  }

  logSearchInput.addEventListener('input', () => {
    logSearchQuery = logSearchInput.value.trim().toLowerCase();
    Array.from(logOutput.children).forEach(applyLogLineVisibility);
    updateLogSearchCount();
  });

  function appendLog(level, message) {
    const line = document.createElement('div');
    line.className = `log-line log-line-${level}`;
    line.textContent = message;
    applyLogLineVisibility(line);
    logOutput.appendChild(line);
    if (!line.hidden) {
      logOutput.scrollTop = logOutput.scrollHeight;
    }
    updateLogSearchCount();
  }

  // ---- 월별 / 6개월 구간별 표 ----
  const monthsBody = document.getElementById('months-table-body');
  const chunksBody = document.getElementById('chunks-table-body');

  function resetPeriodTable(tbody) {
    tbody.innerHTML = '<tr><td colspan="3" class="empty">진행 중...</td></tr>';
  }

  function upsertPeriodRow(tbody, data) {
    const emptyRow = tbody.querySelector('.empty');
    if (emptyRow) emptyRow.closest('tr').remove();

    const rowId = `period-row-${data.kind}-${data.label}`;
    let row = document.getElementById(rowId);
    if (!row) {
      row = document.createElement('tr');
      row.id = rowId;
      tbody.appendChild(row);
    }

    const statusLabel = STATUS_LABEL_KO[data.status] || data.status;
    const statusClass = STATUS_CLASS_MAP[statusLabel] || 'pending';
    const countText = typeof data.count === 'number' ? `${data.count}명` : data.reason ? escapeHtml(data.reason) : '-';

    row.className = statusLabel === '실패' ? 'row-failed' : '';
    row.innerHTML = `
      <td>${escapeHtml(data.label)} (${escapeHtml(data.start)} ~ ${escapeHtml(data.end)})</td>
      <td><span class="status-badge status-${statusClass}">${statusLabel}</span></td>
      <td>${countText}</td>
    `;
  }

  // ---- 보고서 요약 / 복사 ----
  const reportOutput = document.getElementById('report-output');
  const copyBtn = document.getElementById('copy-btn');
  let currentReportText = '';

  copyBtn.addEventListener('click', async () => {
    const result = await window.api.copySummary(currentReportText);
    copyBtn.textContent = result.success ? '복사됨!' : '복사 실패';
    setTimeout(() => {
      copyBtn.textContent = '결과 클립보드 복사';
    }, 1500);
  });

  // ---- 기준일 / 시작·일시정지·중단 ----
  const referenceDateInput = document.getElementById('reference-date');
  referenceDateInput.value = todayLocalISODate();

  const startBtn = document.getElementById('start-btn');
  const pauseBtn = document.getElementById('pause-btn');
  const stopBtn = document.getElementById('stop-btn');

  // ---- 로그인 테스트 ----
  const loginTestBtn = document.getElementById('login-test-btn');
  const loginTestStopBtn = document.getElementById('login-test-stop-btn');
  const loginTestStatus = document.getElementById('login-test-status');

  function setLoginTestStatus(label, statusClass) {
    loginTestStatus.textContent = label;
    loginTestStatus.className = `status-badge status-${statusClass}`;
  }

  // ---- 직접 기간 조회 (수동) ----
  const manualSdateInput = document.getElementById('manual-sdate');
  const manualEdateInput = document.getElementById('manual-edate');
  const manualQueryBtn = document.getElementById('manual-query-btn');
  const manualQueryStopBtn = document.getElementById('manual-query-stop-btn');
  const manualQueryStatus = document.getElementById('manual-query-status');
  const manualQueryResult = document.getElementById('manual-query-result');

  const yesterday = addDaysISODate(todayLocalISODate(), -1);
  manualSdateInput.value = yesterday;
  manualEdateInput.value = yesterday;

  function setManualQueryStatus(label, statusClass) {
    manualQueryStatus.textContent = label;
    manualQueryStatus.className = `status-badge status-${statusClass}`;
  }

  // 이 화면의 모든 작업은 python worker 프로세스를 하나만 쓰므로 동시에 실행할 수 없다.
  // 지금 실행 중인 작업이 어느 쪽인지 추적해서 완료 시 해당 UI만 되돌린다.
  let activeJob = null; // 'login_test' | 'delinquent_manual_query' | 'delinquent_report' | null
  let paused = false;

  function setStartButtonsDisabled(disabled) {
    startBtn.disabled = disabled;
    loginTestBtn.disabled = disabled;
    manualQueryBtn.disabled = disabled;
  }

  loginTestBtn.addEventListener('click', async () => {
    const result = await window.api.startJob({ jobId: 'login_test' });
    if (!result.started) {
      alert('이미 실행 중인 작업이 있습니다.');
      return;
    }

    activeJob = 'login_test';
    setLoginTestStatus('로그인 시도 중', 'processing');
    setStartButtonsDisabled(true);
    loginTestStopBtn.disabled = false;
  });

  loginTestStopBtn.addEventListener('click', async () => {
    await window.api.stopJob();
    loginTestStopBtn.disabled = true;
  });

  manualQueryBtn.addEventListener('click', async () => {
    const sdate = manualSdateInput.value;
    const edate = manualEdateInput.value;
    if (!sdate || !edate) {
      alert('조회 기간을 입력해주세요.');
      return;
    }

    const result = await window.api.startJob({ jobId: 'delinquent_manual_query', sdate, edate });
    if (!result.started) {
      alert('이미 실행 중인 작업이 있습니다.');
      return;
    }

    manualQueryResult.textContent = '';
    activeJob = 'delinquent_manual_query';
    setManualQueryStatus('진행 중', 'processing');
    setStartButtonsDisabled(true);
    manualQueryStopBtn.disabled = false;
  });

  manualQueryStopBtn.addEventListener('click', async () => {
    await window.api.stopJob();
    manualQueryStopBtn.disabled = true;
  });

  startBtn.addEventListener('click', async () => {
    const referenceDate = referenceDateInput.value;
    if (!referenceDate) {
      alert('기준일을 선택해주세요.');
      return;
    }

    resetPeriodTable(monthsBody);
    resetPeriodTable(chunksBody);
    reportOutput.textContent = '진행 중... (완료되면 여기에 보고서가 표시됩니다)';
    currentReportText = '';
    copyBtn.disabled = true;
    paused = false;
    pauseBtn.textContent = '일시정지';

    const result = await window.api.startJob({ jobId: 'delinquent_report', referenceDate });
    if (!result.started) {
      alert('이미 실행 중인 작업이 있습니다.');
      return;
    }

    activeJob = 'delinquent_report';
    setStartButtonsDisabled(true);
    pauseBtn.disabled = false;
    stopBtn.disabled = false;
  });

  pauseBtn.addEventListener('click', async () => {
    if (!paused) {
      await window.api.pauseJob();
      paused = true;
      pauseBtn.textContent = '재개';
    } else {
      await window.api.resumeJob();
      paused = false;
      pauseBtn.textContent = '일시정지';
    }
  });

  stopBtn.addEventListener('click', async () => {
    await window.api.stopJob();
    stopBtn.disabled = true;
    pauseBtn.disabled = true;
  });

  // ---- Python worker 이벤트 ----
  window.api.onJobPeriod((data) => {
    if (data.kind === 'month') {
      upsertPeriodRow(monthsBody, data);
    } else if (data.kind === 'chunk') {
      upsertPeriodRow(chunksBody, data);
    } else if (data.kind === 'manual') {
      const statusLabel = STATUS_LABEL_KO[data.status] || data.status;
      setManualQueryStatus(statusLabel, STATUS_CLASS_MAP[statusLabel] || 'pending');
      if (typeof data.count === 'number') {
        manualQueryResult.textContent = `[${data.start} ~ ${data.end}] 미납자: ${data.count}명`;
      } else if (data.reason) {
        manualQueryResult.textContent = `조회 실패: ${data.reason}`;
      }
    }
  });

  window.api.onJobLog((data) => {
    appendLog(data.level || 'info', data.message || '');
  });

  window.api.onJobDone((data) => {
    // python worker의 emit_done(요약 정보, code 없음)과 프로세스 종료(code 있음) 두 번 올 수 있다.
    if (data.summary && activeJob === 'delinquent_report') {
      currentReportText = data.summary.reportText || '';
      reportOutput.textContent = currentReportText || '(보고서 내용 없음)';
    }

    // 실제 성공/실패는 code가 담긴 이벤트가 최종 판단 기준이다.
    if (typeof data.code === 'undefined') return;

    appendLog('info', `작업 프로세스 종료 (종료 코드: ${data.code})`);

    if (activeJob === 'login_test') {
      setLoginTestStatus(
        data.code === 0 ? '완료 (브라우저 창 확인)' : '실패 (로그 확인)',
        data.code === 0 ? 'success' : 'failed'
      );
      loginTestStopBtn.disabled = true;
    } else if (activeJob === 'delinquent_manual_query') {
      setManualQueryStatus(
        data.code === 0 ? '완료 (브라우저 창 확인)' : '실패 (로그 확인)',
        data.code === 0 ? 'success' : 'failed'
      );
      manualQueryStopBtn.disabled = true;
    } else if (activeJob === 'delinquent_report') {
      pauseBtn.disabled = true;
      stopBtn.disabled = true;
      copyBtn.disabled = !currentReportText;
    }

    setStartButtonsDisabled(false);
    activeJob = null;
  });
}

window.renderDelinquentReportView = renderDelinquentReportView;
