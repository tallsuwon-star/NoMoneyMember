const { BrowserWindow } = require('electron');
const path = require('path');
const store = require('./store');

function createMainWindow() {
  const bounds = store.get('windowBounds');

  const win = new BrowserWindow({
    ...bounds,
    minWidth: 1024,
    minHeight: 680,
    title: 'LMS 미납자 관리 자동화',
    backgroundColor: '#f5f6fa',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  win.loadFile(path.join(__dirname, '..', 'renderer', 'index.html'));

  win.on('resize', () => store.set('windowBounds', win.getBounds()));
  win.on('move', () => store.set('windowBounds', win.getBounds()));

  return win;
}

module.exports = { createMainWindow };
