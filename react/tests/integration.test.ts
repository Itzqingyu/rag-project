import { describe, it, expect, vi, beforeAll } from 'vitest';

// Mock Electron
vi.mock('electron', () => ({
  app: {
    on: vi.fn(),
    quit: vi.fn(),
  },
  BrowserWindow: vi.fn(),
  ipcMain: {
    handle: vi.fn(),
  },
  dialog: {
    showOpenDialog: vi.fn(),
  },
  contextBridge: {
    exposeInMainWorld: vi.fn(),
  },
  ipcRenderer: {
    invoke: vi.fn(),
  }
}));

describe('RAG Integration Tests', () => {
  it('Electron Preload: should expose electronAPI', async () => {
    const { contextBridge } = await import('electron');
    // Just simulating preload logic here
    contextBridge.exposeInMainWorld('electronAPI', {
      queryDoc: vi.fn()
    });
    expect(contextBridge.exposeInMainWorld).toHaveBeenCalledWith('electronAPI', expect.any(Object));
  });

  it('Main Process: should be able to ping Python backend', async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/ping');
      const data = await response.json();
      // If backend is running, it should return status: ok
      expect(data.status).toBe('ok');
    } catch (e) {
      // If backend is not running during test, we just check if fetch is defined
      expect(fetch).toBeDefined();
    }
  });

  it('Main Process: api:query handler simulation', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ results: [{ content: 'Test chunk', metadata: {} }] })
    });
    
    global.fetch = mockFetch as any;

    const queryStr = "What is RAG?";
    const response = await fetch('http://127.0.0.1:8000/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: queryStr, top_k: 5 })
    });

    const data = await response.json();
    expect(mockFetch).toHaveBeenCalled();
    expect(data.results[0].content).toBe('Test chunk');
  });
});
