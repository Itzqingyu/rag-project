/**
 * 本地資料庫交接與全量管理服務模組 (vaultService.ts)
 * 負責串接 Python FastAPI 之 /vault 相關端點 (統計資訊、全量匯出、安全匯入、備份快照與還原)
 */

import { apiClient } from './apiClient';

export interface VaultStats {
  activities_count: number;
  meetings_count: number;
  tasks_count: number;
  decisions_count: number;
  schedules_count: number;
  incidents_count: number;
  documents_count: number;
  chat_sessions_count: number;
  data_size_bytes: number;
  db_size_bytes: number;
  chroma_size_bytes: number;
  markdown_size_bytes: number;
  last_updated: string;
}

export interface BackupItem {
  filename: string;
  size_bytes: number;
  created_at: string;
}

export interface ImportResult {
  status: string;
  message: string;
  backup_created?: string;
  manifest?: Record<string, any>;
  stats?: VaultStats;
}

/**
 * 取得當前本機資料庫與儲存庫統計資訊
 */
export async function fetchVaultStats(): Promise<VaultStats> {
  return await apiClient.get<VaultStats>('/vault/stats');
}

/**
 * 取得全量導出下載 URL
 */
export function getExportUrl(): string {
  return 'http://127.0.0.1:8000/vault/export';
}

/**
 * 觸發瀏覽器下載全量資料包 ZIP
 */
export async function downloadExportVault(): Promise<void> {
  const response = await fetch(getExportUrl());
  if (!response.ok) {
    throw new Error('導出資料包失敗');
  }
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  
  // 嘗試從 header 解析檔名，若無則以時間戳命名
  const disposition = response.headers.get('content-disposition');
  let filename = 'dash_backup.zip';
  if (disposition && disposition.includes('filename=')) {
    const match = disposition.match(/filename=["']?([^"';]+)["']?/);
    if (match && match[1]) filename = match[1];
  } else {
    const now = new Date();
    const ts = now.toISOString().replace(/[-:T.]/g, '').slice(0, 14);
    filename = `dash_backup_${ts}.zip`;
  }

  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

/**
 * 上傳並安全全量導入 ZIP 資料包
 */
export async function importVault(file: File): Promise<ImportResult> {
  const formData = new FormData();
  formData.append('file', file);
  return await apiClient.upload<ImportResult>('/vault/import', formData);
}

/**
 * 取得本機所有的自動快照備份歷史
 */
export async function fetchBackups(): Promise<BackupItem[]> {
  return await apiClient.get<BackupItem[]>('/vault/backups');
}

/**
 * 指定快照檔名執行還原
 */
export async function restoreBackup(backupFilename: string): Promise<ImportResult> {
  return await apiClient.post<ImportResult>('/vault/restore', {
    backup_filename: backupFilename,
  });
}
