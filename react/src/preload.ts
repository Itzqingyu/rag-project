import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  openFile: () => ipcRenderer.invoke('dialog:openFile'),
  uploadFile: (filePath: string) => ipcRenderer.invoke('api:upload', filePath),
  queryDoc: (queryStr: string) => ipcRenderer.invoke('api:query', queryStr)
});
