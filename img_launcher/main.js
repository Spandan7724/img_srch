// main.js

const {
  app,
  BrowserWindow,
  globalShortcut,
  ipcMain,
  dialog,       // ← make sure dialog is included here
  screen
} = require('electron');
const path = require('path');

let win;

function createWindow() {
  const { width: screenWidth } = screen.getPrimaryDisplay().workAreaSize;
  const windowWidth     = 600;
  const collapsedHeight = 80;
  const expandedHeight  = 300;
  const xPos            = Math.round((screenWidth - windowWidth) / 2);
  const yPos            = 200;  // shift down 20px

  win = new BrowserWindow({
    x: xPos,
    y: yPos,
    width: windowWidth,
    height: collapsedHeight,
    frame: false,
    transparent: false,
    backgroundColor: '#000000', 
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: true,
    hasShadow: false,
    show: false,
    title: '',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js')
    }
  });

  win.loadFile('renderer/index.html');
  // win.webContents.openDevTools({ mode: 'detach' });
  win.hide();

  globalShortcut.register('Alt+S', () => {
    if (win.isVisible()) {
      win.hide();
    } else {
      win.setPosition(xPos, yPos);
      win.setContentSize(windowWidth, collapsedHeight);
      win.webContents.send('clear-all');
      win.show();
      win.focus();
    }
  });
}

app.whenReady().then(createWindow);

ipcMain.on('expand-window', () => {
  // console.log('▶ expand-window received');
  if (win) win.setContentSize(600, 300);
});

ipcMain.on('collapse-window', () => {
  // console.log('◀ collapse-window received');
  if (win) win.setContentSize(600, 80);
});

ipcMain.handle('show-open-dialog', async () => {
  // now 'dialog' is defined
  const result = await dialog.showOpenDialog(win, {
    properties: ['openDirectory']
  });
  return result;  // { canceled: bool, filePaths: [...] }
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
});
