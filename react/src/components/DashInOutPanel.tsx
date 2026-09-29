import React, { useState, useEffect, useRef } from 'react';
import {
  ArrowLeftRight,
  Download,
  Upload,
  RotateCw,
  RotateCcw,
  FileArchive,
  Database,
  Calendar,
  FileText,
  Clock,
  Layers,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import {
  VaultStats,
  BackupItem,
  fetchVaultStats,
  downloadExportVault,
  importVault,
  fetchBackups,
  restoreBackup,
} from '../api/vaultService';
import ConfirmModal from './ConfirmModal';
import './DashInOutPanel.css';

interface DashInOutPanelProps {
  onDataReloaded?: () => void;
}

export default function DashInOutPanel({ onDataReloaded }: DashInOutPanelProps) {
  const [stats, setStats] = useState<VaultStats | null>(null);
  const [backups, setBackups] = useState<BackupItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [isImporting, setIsImporting] = useState<boolean>(false);
  const [isRestoring, setIsRestoring] = useState<boolean>(false);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [confirmImportOpen, setConfirmImportOpen] = useState<boolean>(false);
  const [confirmRestoreOpen, setConfirmRestoreOpen] = useState<boolean>(false);
  const [restoreTarget, setRestoreTarget] = useState<string | null>(null);

  const [banner, setBanner] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 格式化檔案大小
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 格式化日期時間
  const formatDateTime = (isoString?: string): string => {
    if (!isoString) return '-';
    try {
      const d = new Date(isoString);
      return d.toLocaleString('zh-TW', { hour12: false });
    } catch {
      return isoString;
    }
  };

  // 載入統計與備份列表
  const loadData = async () => {
    setIsLoading(true);
    try {
      const [statsData, backupsData] = await Promise.all([
        fetchVaultStats(),
        fetchBackups(),
      ]);
      setStats(statsData);
      setBackups(backupsData);
    } catch (err: any) {
      setBanner({ type: 'error', text: `載入概況失敗: ${err.message || '無法連線後端'}` });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // 導出資料包
  const handleExport = async () => {
    setIsExporting(true);
    setBanner(null);
    try {
      await downloadExportVault();
      setBanner({ type: 'success', text: '資料包已成功打包並開始下載！' });
    } catch (err: any) {
      setBanner({ type: 'error', text: `導出失敗: ${err.message || '未知錯誤'}` });
    } finally {
      setIsExporting(false);
    }
  };

  // 選取檔案
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!file.name.toLowerCase().endsWith('.zip')) {
        setBanner({ type: 'error', text: '請選擇 .zip 格式的資料包檔案。' });
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
      setBanner(null);
    }
  };

  // 觸發導入確認
  const handleStartImport = () => {
    if (!selectedFile) return;
    setConfirmImportOpen(true);
  };

  // 確認並執行導入
  const handleConfirmImport = async () => {
    if (!selectedFile) return;
    setConfirmImportOpen(false);
    setIsImporting(true);
    setBanner(null);
    try {
      const result = await importVault(selectedFile);
      setBanner({
        type: 'success',
        text: `全量導入成功！${result.backup_created ? `已自動建立快照備份「${result.backup_created}」。` : ''}`,
      });
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      await loadData();
      onDataReloaded?.();
    } catch (err: any) {
      setBanner({ type: 'error', text: `導入失敗: ${err.message || '資料包驗證失敗'}` });
    } finally {
      setIsImporting(false);
    }
  };

  // 觸發還原確認
  const handleStartRestore = (filename: string) => {
    setRestoreTarget(filename);
    setConfirmRestoreOpen(true);
  };

  // 確認並執行還原
  const handleConfirmRestore = async () => {
    if (!restoreTarget) return;
    setConfirmRestoreOpen(false);
    setIsRestoring(true);
    setBanner(null);
    try {
      await restoreBackup(restoreTarget);
      setBanner({ type: 'success', text: `已成功將系統還原至快照「${restoreTarget}」！` });
      setRestoreTarget(null);
      await loadData();
      onDataReloaded?.();
    } catch (err: any) {
      setBanner({ type: 'error', text: `還原失敗: ${err.message || '未知錯誤'}` });
    } finally {
      setIsRestoring(false);
    }
  };

  return (
    <div className="dash-inout-page">
      {/* 頂部標題 */}
      <div className="dash-inout-header">
        <div>
          <p className="eyebrow">DATA MIGRATION & BACKUP</p>
          <h1>DASH IN & OUT</h1>
          <p>本地資料全量交接、整包備份與安全匯入工作台。</p>
        </div>
        <button
          className="button secondary"
          type="button"
          onClick={loadData}
          disabled={isLoading}
          title="重新整理概況"
        >
          <RotateCw size={14} className={isLoading ? 'spin-icon' : ''} />
          <span>重新整理</span>
        </button>
      </div>

      {/* 訊息反饋橫幅 */}
      {banner && (
        <div className={`dash-inout-banner ${banner.type}`}>
          <span>{banner.text}</span>
          <button
            type="button"
            className="close-button"
            onClick={() => setBanner(null)}
            aria-label="關閉提示"
          >
            ×
          </button>
        </div>
      )}

      {/* 卡片 1: 本地資料庫規模概況 */}
      <section className="dash-inout-card">
        <div className="dash-inout-card-head">
          <h2>
            <Database size={18} />
            <span>目前本機資料庫概況</span>
          </h2>
          <small style={{ color: 'var(--muted)', fontSize: '0.78rem' }}>
            最後統計時間：{formatDateTime(stats?.last_updated)}
          </small>
        </div>
        <div className="dash-stats-grid">
          <div className="dash-stat-item">
            <span className="dash-stat-label">活動總數</span>
            <span className="dash-stat-value">{stats?.activities_count ?? 0}</span>
          </div>
          <div className="dash-stat-item">
            <span className="dash-stat-label">會議紀錄</span>
            <span className="dash-stat-value">{stats?.meetings_count ?? 0}</span>
          </div>
          <div className="dash-stat-item">
            <span className="dash-stat-label">待辦事項</span>
            <span className="dash-stat-value">{stats?.tasks_count ?? 0}</span>
          </div>
          <div className="dash-stat-item">
            <span className="dash-stat-label">決策紀錄</span>
            <span className="dash-stat-value">{stats?.decisions_count ?? 0}</span>
          </div>
          <div className="dash-stat-item">
            <span className="dash-stat-label">流程日程</span>
            <span className="dash-stat-value">{stats?.schedules_count ?? 0}</span>
          </div>
          <div className="dash-stat-item">
            <span className="dash-stat-label">突發事件</span>
            <span className="dash-stat-value">{stats?.incidents_count ?? 0}</span>
          </div>
          <div className="dash-stat-item">
            <span className="dash-stat-label">託管文檔 (RAG)</span>
            <span className="dash-stat-value">{stats?.documents_count ?? 0}</span>
          </div>
          <div className="dash-stat-item">
            <span className="dash-stat-label">對話會話</span>
            <span className="dash-stat-value">{stats?.chat_sessions_count ?? 0}</span>
          </div>
          <div className="dash-stat-item" style={{ gridColumn: 'span 2' }}>
            <span className="dash-stat-label">資料庫總佔用空間</span>
            <span className="dash-stat-value" style={{ color: 'var(--cyan)' }}>
              {formatBytes(stats?.data_size_bytes ?? 0)}
            </span>
          </div>
        </div>
      </section>

      {/* 卡片 2 & 3: 導出與導入操作區 */}
      <div className="dash-actions-row">
        {/* 全量導出卡片 */}
        <section className="dash-inout-card">
          <div className="dash-inout-card-head">
            <h2>
              <Download size={18} />
              <span>整包導出 (Export)</span>
            </h2>
          </div>
          <p className="dash-inout-card-desc">
            將目前的 SQLite 資料庫、Chroma 向量索引庫與 Markdown 託管文本完整打包為標準 ZIP 檔案，內嵌專屬防偽簽名，可用於無損交接給下一屆負責人或搬移至新電腦。
          </p>
          <button
            className="button primary"
            type="button"
            onClick={handleExport}
            disabled={isExporting}
            style={{ width: '100%', justifyContent: 'center' }}
          >
            <Download size={16} />
            <span>{isExporting ? '正在封裝打包中...' : '導出全量資料包 (.zip)'}</span>
          </button>
        </section>

        {/* 安全導入卡片 */}
        <section className="dash-inout-card">
          <div className="dash-inout-card-head">
            <h2>
              <Upload size={18} />
              <span>安全導入 (Import)</span>
            </h2>
          </div>
          <p className="dash-inout-card-desc">
            導入由 DASH 導出之 ZIP 資料包。系統在覆蓋前會<strong>自動建立安全快照備份</strong>，並嚴格檢驗簽名合法性以防導入無關檔案。
          </p>

          <input
            type="file"
            ref={fileInputRef}
            accept=".zip"
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />

          {!selectedFile ? (
            <div
              className="dash-dropzone"
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="dash-dropzone-inner">
                <FileArchive size={28} color="var(--muted)" />
                <span>點擊選取 DASH 導出之 .zip 資料包</span>
                <span className="dash-dropzone-hint">只接受包含 dash_manifest.json 簽名之合法壓縮檔</span>
              </div>
            </div>
          ) : (
            <div className="dash-selected-file-info">
              <div>
                <strong>{selectedFile.name}</strong> ({formatBytes(selectedFile.size)})
              </div>
              <button
                type="button"
                className="button secondary"
                style={{ padding: '4px 8px', fontSize: '0.78rem' }}
                onClick={() => {
                  setSelectedFile(null);
                  if (fileInputRef.current) fileInputRef.current.value = '';
                }}
              >
                重選
              </button>
            </div>
          )}

          <button
            className="button secondary"
            type="button"
            onClick={handleStartImport}
            disabled={!selectedFile || isImporting}
            style={{ width: '100%', justifyContent: 'center' }}
          >
            <Upload size={16} />
            <span>{isImporting ? '正在校驗並導入中...' : '開始驗證並導入'}</span>
          </button>
        </section>
      </div>

      {/* 卡片 4: 本地自動快照備份歷史 */}
      <section className="dash-inout-card">
        <div className="dash-inout-card-head">
          <h2>
            <Clock size={18} />
            <span>本地快照備份歷史 (Automatic Snapshots)</span>
          </h2>
        </div>
        <p className="dash-inout-card-desc">
          系統在每次執行全量導入覆蓋前，均會自動將本機當前狀態留存為快照備份。若有需要，可隨時從下方列表一鍵還原回指定的歷史快照。
        </p>

        {backups.length === 0 ? (
          <div className="dash-empty-backups">
            目前尚無自動備份快照紀錄。
          </div>
        ) : (
          <table className="dash-backups-table">
            <thead>
              <tr>
                <th>備份檔案名稱</th>
                <th>建立時間</th>
                <th>檔案容量</th>
                <th style={{ textAlign: 'right' }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {backups.map((b) => (
                <tr key={b.filename}>
                  <td style={{ fontWeight: 600, color: 'var(--ink)' }}>{b.filename}</td>
                  <td>{formatDateTime(b.created_at)}</td>
                  <td>{formatBytes(b.size_bytes)}</td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      type="button"
                      className="button secondary"
                      style={{ padding: '4px 10px', fontSize: '0.78rem' }}
                      onClick={() => handleStartRestore(b.filename)}
                      disabled={isRestoring}
                    >
                      <RotateCcw size={12} />
                      <span>還原此快照</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {/* 導入確認彈窗 */}
      <ConfirmModal
        isOpen={confirmImportOpen}
        title="確認全量覆蓋導入資料包？"
        message={`確定將「${selectedFile?.name}」導入系統？目前本機的所有活動、紀錄與向量庫資料將被完整替換。系統將在覆蓋前自動為你現存資料建立快照備份，以供隨時復原。`}
        confirmText="確認覆蓋導入"
        cancelText="取消"
        isDanger={true}
        onConfirm={handleConfirmImport}
        onCancel={() => setConfirmImportOpen(false)}
      />

      {/* 還原確認彈窗 */}
      <ConfirmModal
        isOpen={confirmRestoreOpen}
        title="確認還原歷史快照？"
        message={`確定將系統還原至快照「${restoreTarget}」？目前的資料將會被該快照內容覆蓋。在執行還原前系統也會再次為當前狀態建立最新快照備份。`}
        confirmText="確認還原"
        cancelText="取消"
        isDanger={true}
        onConfirm={handleConfirmRestore}
        onCancel={() => setConfirmRestoreOpen(false)}
      />
    </div>
  );
}
