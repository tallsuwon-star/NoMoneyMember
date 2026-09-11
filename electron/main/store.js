const Store = require('electron-store');

const store = new Store({
  name: 'settings',
  defaults: {
    theme: 'light',
    windowBounds: { width: 1280, height: 840 },
  },
});

module.exports = store;
