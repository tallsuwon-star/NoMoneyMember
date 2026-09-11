const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  // 설정 (electron-store)
  getSettings: () => ipcRenderer.invoke('settings:get'),
  setSettings: (partial) => ipcRenderer.invoke('settings:set', partial),

  // Selenium 설치 확인/설치
  checkSelenium: () => ipcRenderer.invoke('setup:checkSelenium'),
  installSelenium: () => ipcRenderer.invoke('setup:installSelenium'),
  onInstallLog: (callback) => {
    ipcRenderer.removeAllListeners('setup:installLog');
    ipcRenderer.on('setup:installLog', (_event, line) => callback(line));
  },

  // 작업(Job) 실행 제어
  startJob: (payload) => ipcRenderer.invoke('job:start', payload),
  pauseJob: () => ipcRenderer.invoke('job:pause'),
  resumeJob: () => ipcRenderer.invoke('job:resume'),
  stopJob: () => ipcRenderer.invoke('job:stop'),
  onJobPeriod: (callback) => {
    ipcRenderer.removeAllListeners('job:period');
    ipcRenderer.on('job:period', (_event, data) => callback(data));
  },
  onJobLog: (callback) => {
    ipcRenderer.removeAllListeners('job:log');
    ipcRenderer.on('job:log', (_event, data) => callback(data));
  },
  onJobDone: (callback) => {
    ipcRenderer.removeAllListeners('job:done');
    ipcRenderer.on('job:done', (_event, data) => callback(data));
  },

  // 결과 요약 클립보드 복사 (pyperclip)
  copySummary: (text) => ipcRenderer.invoke('clipboard:copy', text),
});
