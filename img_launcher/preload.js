const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('launcherAPI', {
  onClear:       (fn) => ipcRenderer.on('clear-all', fn),
  expandWindow:  ()   => ipcRenderer.send('expand-window'),
  collapseWindow:()   => ipcRenderer.send('collapse-window'),
  selectFolder:  ()   => ipcRenderer.invoke('show-open-dialog')
});
