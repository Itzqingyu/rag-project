/**
 * vaultApi.ts - 多 Vault 與 DASH OUT / DASH IN 前端 API 模組
 */

const API_BASE_URL = 'http://127.0.0.1:8000';

export interface VaultStats {
  vault_name: string;
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

export interface VaultManifest {
  app: string;
  version: string;
  vault_id: string;
  name: string;
  created_at: string;
  updated_at: string;
  description: string;
}

export interface VaultItem {
  name: string;
  display_name: string;
  vault_id: string;
  path: string;
  created_at: string;
  updated_at: string;
  description: string;
  is_active: boolean;
  stats: VaultStats;
}

export interface InspectZipResponse {
  status: string;
  manifest: VaultManifest;
  suggested_name: string;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options?.body && !(options.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
      ...options?.headers,
    },
  });

  let body: any = null;
  try {
    body = await response.json();
  } catch {
    // 預防空回應或檔案下載
  }

  if (!response.ok) {
    const detail = body?.detail || `API request failed (${response.status})`;
    throw new Error(detail);
  }

  return body as T;
}

export const vaultApi = {
  /** 取得所有 Vault 列表 */
  listVaults: () => request<VaultItem[]>('/vaults'),

  /** 取得當前使用中 Vault 資訊與統計數據 */
  getActiveVault: () => request<{ active_vault: string; stats: VaultStats }>('/vaults/active'),

  /** 熱切換使用中的 Vault */
  switchVault: (vaultName: string) =>
    request<{ status: string; message: string; active_vault: string; stats: VaultStats }>('/vaults/switch', {
      method: 'POST',
      body: JSON.stringify({ vault_name: vaultName }),
    }),

  /** 建立全新空白 Vault 並自動切換 */
  createVault: (vaultName: string, description?: string) =>
    request<{ status: string; message: string; vault: any; stats: VaultStats }>('/vaults/create', {
      method: 'POST',
      body: JSON.stringify({ vault_name: vaultName, description: description || '' }),
    }),

  /** 重新命名 Vault */
  renameVault: (oldName: string, newName: string) =>
    request<{ status: string; message: string; old_name: string; new_name: string }>('/vaults/rename', {
      method: 'POST',
      body: JSON.stringify({ old_name: oldName, new_name: newName }),
    }),

  /** 刪除指定的非使用中 Vault */
  deleteVault: (vaultName: string) =>
    request<{ status: string; message: string; deleted_vault: string }>(`/vaults/${encodeURIComponent(vaultName)}`, {
      method: 'DELETE',
    }),

  /** 取得當前使用中 Vault 之統計數據 */
  getVaultStats: () => request<VaultStats>('/vault/stats'),

  /** DASH OUT 導出下載 URL */
  getExportUrl: () => `${API_BASE_URL}/vault/export`,

  /** 檢驗並解析上傳的 ZIP 描述檔 */
  inspectZip: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request<InspectZipResponse>('/vault/inspect-zip', {
      method: 'POST',
      body: formData,
    });
  },

  /** DASH IN: 匯入 ZIP 並建立為全新獨立 Vault */
  importVault: (file: File, targetName?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    const query = targetName ? `?target_name=${encodeURIComponent(targetName)}` : '';
    return request<{
      status: string;
      message: string;
      vault_name: string;
      manifest: VaultManifest;
      stats: VaultStats;
    }>(`/vault/import${query}`, {
      method: 'POST',
      body: formData,
    });
  },
};
