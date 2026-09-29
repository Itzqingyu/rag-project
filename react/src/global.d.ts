/// <reference types="@electron-forge/plugin-vite/forge-vite-env" />

export interface ElectronAPI {
  openFile: () => Promise<string | null>;
  uploadFile: (filePath: string) => Promise<{ status: string; chunks_added: number }>;
  queryDoc: (query: string) => Promise<{ results: Array<{ content: string; metadata: any }> }>;
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
  const MAIN_WINDOW_VITE_DEV_SERVER_URL: string;
  const MAIN_WINDOW_VITE_NAME: string;
}

declare module '*.css';