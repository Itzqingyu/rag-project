export interface ElectronAPI {
  openFile: () => Promise<string | null>;
  uploadFile: (filePath: string) => Promise<{ status: string; chunks_added: number }>;
  queryDoc: (query: string) => Promise<{ results: Array<{ content: string; metadata: any }> }>;
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}
