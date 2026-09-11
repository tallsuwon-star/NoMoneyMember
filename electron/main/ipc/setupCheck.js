const { spawn } = require('child_process');
const path = require('path');

const PYTHON_BIN = process.platform === 'win32' ? 'python' : 'python3';
const PYTHON_DIR = path.join(__dirname, '..', '..', '..', 'python');
const REQUIREMENTS_PATH = path.join(PYTHON_DIR, 'requirements.txt');

function checkSelenium() {
  return new Promise((resolve) => {
    const proc = spawn(PYTHON_BIN, ['-c', 'import selenium; print(selenium.__version__)']);
    let out = '';

    proc.stdout.on('data', (chunk) => {
      out += chunk.toString();
    });

    proc.on('close', (code) => {
      if (code === 0) {
        resolve({ installed: true, version: out.trim() });
      } else {
        resolve({ installed: false, version: null });
      }
    });

    proc.on('error', () => resolve({ installed: false, version: null }));
  });
}

function installSelenium(mainWindow) {
  return new Promise((resolve) => {
    const proc = spawn(PYTHON_BIN, ['-m', 'pip', 'install', '-r', REQUIREMENTS_PATH]);

    proc.stdout.on('data', (chunk) => {
      mainWindow?.webContents.send('setup:installLog', chunk.toString());
    });
    proc.stderr.on('data', (chunk) => {
      mainWindow?.webContents.send('setup:installLog', chunk.toString());
    });

    proc.on('close', (code) => {
      resolve({ success: code === 0, code });
    });
    proc.on('error', (err) => {
      mainWindow?.webContents.send('setup:installLog', `\n${err.message}\n`);
      resolve({ success: false, code: -1 });
    });
  });
}

module.exports = { checkSelenium, installSelenium };
