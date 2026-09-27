/**
 * 後端 API 資料型別定義模組 (apiTypes.ts)
 * 對齊 Python FastAPI 後端端點回傳與請求資料結構
 */

/**
 * 向量切片檢索引用資料結構
 */
export interface RetrievedChunk {
  content: string;
  metadata?: {
    source?: string;
    [key: string]: unknown;
  };
}

/**
 * 後端 SQLite 會話紀錄型別
 */
export interface BackendSession {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

/**
 * 後端歷史訊息紀錄型別
 */
export interface BackendMessage {
  id: number;
  session_id: number;
  role: 'user' | 'assistant';
  content: string;
  mode: 'chat' | 'rag';
  retrieved_chunks?: RetrievedChunk[] | string | null;
  created_at: string;
}

/**
 * 取得會話詳情與歷史訊息回應
 */
export interface SessionDetailResponse {
  status: string;
  session: BackendSession;
  messages: BackendMessage[];
}

/**
 * 建立會話請求參數
 */
export interface CreateSessionRequest {
  title?: string;
}

/**
 * 建立會話回應
 */
export interface CreateSessionResponse {
  status: string;
  session: BackendSession;
}

/**
 * 發送訊息請求參數
 */
export interface SendMessageRequest {
  content: string;
  mode: 'chat' | 'rag';
  top_k?: number;
}

/**
 * 發送訊息回應
 */
export interface SendMessageResponse {
  status: string;
  session_id: number;
  mode: 'chat' | 'rag';
  user_message: BackendMessage;
  assistant_message: BackendMessage;
  retrieved_chunks: RetrievedChunk[];
}

/**
 * 後端文件管理紀錄型別
 */
export interface BackendDocument {
  id: number;
  filename: string;
  file_path: string;
  file_hash?: string;
  upload_date: string;
  chunk_count: number;
}

/**
 * 文件上傳回應
 */
export interface UploadDocumentResponse {
  status: string;
  message: string;
  doc_id?: number | null;
  file_path?: string;
  chunks_added?: number;
}

/**
 * API 統一錯誤介面
 */
export interface ApiError {
  status: number;
  message: string;
  detail?: string;
}
