import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient, BackendApiError } from '../src/services/apiClient';
import {
  fetchSessions,
  fetchSessionDetail,
  createNewSession,
  deleteSessionById,
  sendChatMessage,
} from '../src/services/chatService';
import {
  fetchDocuments,
  uploadDocument,
  deleteDocumentByIdentifier,
} from '../src/services/documentService';

describe('API Services & Error Handling', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('should throw BackendApiError with clear message when backend is unreachable', async () => {
    // 模擬 fetch 拋出網路異常 (如後端伺服器未開啟)
    global.fetch = vi.fn().mockRejectedValue(new Error('Failed to fetch'));

    await expect(fetchSessions()).rejects.toThrow(BackendApiError);
    await expect(fetchSessions()).rejects.toThrow(
      /無法連線至後端服務.*請確認後端 Python 服務已啟動/
    );
  });

  it('should throw BackendApiError with backend detail on non-200 status', async () => {
    // 模擬後端回傳 HTTP 404 與 detail
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: '找不到指定的對話會話' }),
    } as Response);

    await expect(fetchSessionDetail(999)).rejects.toThrow(BackendApiError);
    await expect(fetchSessionDetail(999)).rejects.toThrow('找不到指定的對話會話');
  });

  it('should correctly format and call POST /sessions/1/messages', async () => {
    const mockResponse = {
      status: 'success',
      session_id: 1,
      mode: 'rag',
      user_message: {
        id: 10,
        session_id: 1,
        role: 'user',
        content: '活動何時開始？',
        mode: 'rag',
        created_at: '2026-09-17T16:00:00Z',
      },
      assistant_message: {
        id: 11,
        session_id: 1,
        role: 'assistant',
        content: '活動預計於早上 9 點開始。',
        mode: 'rag',
        created_at: '2026-09-17T16:00:01Z',
      },
      retrieved_chunks: [
        {
          content: '活動開始時間：09:00',
          metadata: { source: '行程規劃.md' },
        },
      ],
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockResponse,
    } as Response);

    const result = await sendChatMessage(1, '活動何時開始？', 'rag', 5);
    expect(result.status).toBe('success');
    expect(result.assistant_message.content).toBe('活動預計於早上 9 點開始。');
    expect(result.retrieved_chunks).toHaveLength(1);

    expect(global.fetch).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/sessions/1/messages',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          content: '活動何時開始？',
          mode: 'rag',
          top_k: 5,
        }),
      })
    );
  });

  it('should call POST /upload with FormData for document upload', async () => {
    const mockUploadRes = {
      status: 'success',
      message: '成功轉檔並向量化 test.md！',
      doc_id: 1,
      file_path: 'python/data/markdown/test.md',
      chunks_added: 3,
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockUploadRes,
    } as Response);

    const dummyFile = new File(['# test content'], 'test.md', { type: 'text/markdown' });
    const res = await uploadDocument(dummyFile);
    expect(res.status).toBe('success');
    expect(res.chunks_added).toBe(3);

    expect(global.fetch).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/upload',
      expect.objectContaining({
        method: 'POST',
      })
    );
  });

  it('should call DELETE /documents/:id to remove a document', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: 'success', message: '已刪除文件' }),
    } as Response);

    await deleteDocumentByIdentifier(1);
    expect(global.fetch).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/documents/1',
      expect.objectContaining({
        method: 'DELETE',
      })
    );
  });
});
