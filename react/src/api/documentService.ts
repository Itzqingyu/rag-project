/**
 * 歷史紀錄文件管理服務模組 (documentService.ts)
 * 負責串接 Python FastAPI 之 RAG Document 相關端點 (文檔列表、檔案上傳與檔案刪除)
 */

import { apiClient } from './apiClient';
import { BackendDocument, UploadDocumentResponse } from './apiTypes';

/**
 * 取得已入庫的歷史紀錄文件列表
 */
export async function fetchDocuments(): Promise<BackendDocument[]> {
  return await apiClient.get<BackendDocument[]>('/documents');
}

/**
 * 上傳文件並觸發後端轉檔與向量化切片入庫
 * 支援格式：.md, .txt, .pdf, .docx
 */
export async function uploadDocument(
  file: File
): Promise<UploadDocumentResponse> {
  const formData = new FormData();
  formData.append('file', file);
  return await apiClient.upload<UploadDocumentResponse>('/upload', formData);
}

/**
 * 刪除指定文件及其在向量資料庫中的所有切片
 * @param identifier 文件 ID (number) 或 檔案相對路徑 (string)
 */
export async function deleteDocumentByIdentifier(
  identifier: string | number
): Promise<void> {
  // 將路徑或 ID 進行編碼以傳遞給路徑參數
  const encoded = encodeURIComponent(String(identifier));
  await apiClient.delete(`/documents/${encoded}`);
}
