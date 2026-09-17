import React, { useState, useEffect, useCallback } from 'react';
import {
  Sparkles,
  FileText,
  CheckCircle2,
  Calendar,
  Clock,
  MapPin,
  Users,
  ListTodo,
  AlertCircle,
  ArrowRight,
  RefreshCw,
  Check,
  Layers,
} from 'lucide-react';
import { fetchDocuments } from '../services/documentService';
import { BackendDocument } from '../services/apiTypes';
import {
  fetchActivities,
  extractMeetingSummary,
  commitMeetingSummary,
  BackendActivity,
  MeetingPreviewData,
  ExtractedMeeting,
  ExtractedDecision,
  ExtractedTask,
} from '../services/meetingExtractService';
import './MeetingExtractPanel.css';

interface MeetingExtractPanelProps {
  // 可選：完成提交後若欲切換至該活動頁面
  onNavigateToActivity?: (activityId: number) => void;
}

/**
 * AI 會議紀錄結構化整理主面板 (Meeting Extract Panel)
 * 整合後端 Preview-Commit 雙階段工作流程：
 * 1. 選擇文件與目標活動
 * 2. 呼叫 LLM 進行 1-shot 會議資訊、決策與待辦結構化萃取 (Extract)
 * 3. 預覽與微調編輯 (Preview)
 * 4. 寫入活動 SQLite 資料庫 (Commit)
 */
export const MeetingExtractPanel: React.FC<MeetingExtractPanelProps> = ({
  onNavigateToActivity,
}) => {
  // 已入庫文檔清單
  const [documents, setDocuments] = useState<BackendDocument[]>([]);
  // 現有活動清單
  const [activities, setActivities] = useState<BackendActivity[]>([]);

  // 使用者選擇之文件 ID 與目標活動 ID
  const [selectedDocId, setSelectedDocId] = useState<number | ''>('');
  const [selectedActivityId, setSelectedActivityId] = useState<number | ''>('');

  // 狀態旗標
  const [loadingInitial, setLoadingInitial] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isCommitting, setIsCommitting] = useState(false);

  // 提示與錯誤訊息
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // 結構化預覽資料 (若為 null 則代表處於選擇階段)
  const [previewData, setPreviewData] = useState<MeetingPreviewData | null>(null);

  /**
   * 初始化載入文件清單與活動清單
   */
  const loadPrerequisites = useCallback(async () => {
    setLoadingInitial(true);
    setErrorMessage(null);
    try {
      const [docs, acts] = await Promise.all([
        fetchDocuments(),
        fetchActivities(),
      ]);
      setDocuments(docs);
      setActivities(acts);

      if (docs.length > 0 && selectedDocId === '') {
        setSelectedDocId(docs[0].id);
      }
      if (acts.length > 0 && selectedActivityId === '') {
        setSelectedActivityId(acts[0].id);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMessage(`無法載入基礎資料：${msg}`);
    } finally {
      setLoadingInitial(false);
    }
  }, [selectedDocId, selectedActivityId]);

  useEffect(() => {
    loadPrerequisites();
  }, [loadPrerequisites]);

  /**
   * 階段 1：觸發 AI 結構化萃取 (POST /extract_summary)
   */
  const handleStartExtract = async () => {
    if (!selectedDocId) {
      setErrorMessage('請先選擇欲分析的會議紀錄文件');
      return;
    }

    setIsExtracting(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const res = await extractMeetingSummary(Number(selectedDocId));
      setPreviewData(res.preview_data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMessage(`AI 結構化萃取失敗：${msg}`);
    } finally {
      setIsExtracting(false);
    }
  };

  /**
   * 會議基本資訊欄位異動
   */
  const handleMeetingChange = (
    field: keyof ExtractedMeeting,
    value: string
  ) => {
    if (!previewData) return;
    setPreviewData({
      ...previewData,
      meeting: {
        ...previewData.meeting,
        [field]: value,
      },
    });
  };

  /**
   * 決策紀錄欄位異動
   */
  const handleDecisionChange = (
    index: number,
    field: keyof ExtractedDecision,
    value: string
  ) => {
    if (!previewData) return;
    const updated = [...previewData.decisions];
    updated[index] = { ...updated[index], [field]: value };
    setPreviewData({ ...previewData, decisions: updated });
  };

  /**
   * 待辦事項欄位異動
   */
  const handleTaskChange = (
    index: number,
    field: keyof ExtractedTask,
    value: string
  ) => {
    if (!previewData) return;
    const updated = [...previewData.tasks];
    updated[index] = { ...updated[index], [field]: value };
    setPreviewData({ ...previewData, tasks: updated });
  };

  /**
   * 階段 2：確認並寫入活動資料庫 (POST /commit_summary)
   */
  const handleCommit = async () => {
    if (!previewData) return;
    if (!selectedActivityId) {
      setErrorMessage('請指定欲歸屬的活動目標');
      return;
    }

    setIsCommitting(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const res = await commitMeetingSummary({
        activity_id: Number(selectedActivityId),
        meeting: previewData.meeting,
        decisions: previewData.decisions,
        tasks: previewData.tasks,
      });

      setSuccessMessage(
        `${res.message}（包含 1 筆會議、${res.decisions.length} 筆決策與 ${res.tasks.length} 項待辦事項）`
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMessage(`寫入資料庫失敗：${msg}`);
    } finally {
      setIsCommitting(false);
    }
  };

  /**
   * 重設並重新選擇
   */
  const handleReset = () => {
    setPreviewData(null);
    setSuccessMessage(null);
    setErrorMessage(null);
  };

  const selectedActivityName =
    activities.find((a) => a.id === selectedActivityId)?.name || '未選擇活動';

  return (
    <div className="extract-panel-layout">
      {/* 頂部標題列 */}
      <header className="extract-top-header">
        <div className="extract-header-title">
          <Sparkles size={20} className="extract-sparkle-icon" />
          <h2>AI 會議紀錄整理</h2>
          <span className="extract-header-tag">1-Shot 結構化萃取</span>
        </div>
        <div>
          <button
            type="button"
            className="button secondary sm-btn"
            onClick={loadPrerequisites}
            disabled={loadingInitial || isExtracting || isCommitting}
            title="重新讀取文件與活動清單"
          >
            <RefreshCw size={14} className={loadingInitial ? 'spinning' : ''} />
            <span>重新整理</span>
          </button>
        </div>
      </header>

      {/* 異常提示列 */}
      {errorMessage && (
        <div className="extract-api-error-banner" role="alert">
          <div className="extract-api-error-info">
            <AlertCircle size={16} />
            <span>{errorMessage}</span>
          </div>
          <button
            type="button"
            className="extract-api-error-dismiss"
            onClick={() => setErrorMessage(null)}
          >
            關閉
          </button>
        </div>
      )}

      {/* 內容獨立可滾動區 */}
      <div className="extract-content-scroll">
        {/* 成功提交提示 */}
        {successMessage && (
          <div className="extract-success-banner" role="status">
            <div className="extract-success-info">
              <CheckCircle2 size={20} />
              <span>{successMessage}</span>
            </div>
            {onNavigateToActivity && selectedActivityId && (
              <button
                type="button"
                className="button primary sm-btn"
                onClick={() => onNavigateToActivity(Number(selectedActivityId))}
              >
                <span>前往檢視活動</span>
                <ArrowRight size={14} />
              </button>
            )}
          </div>
        )}

        {/* 1. 設定與來源選擇卡片 */}
        <section className="extract-card">
          <div className="extract-card-head">
            <div className="extract-card-title">
              <FileText size={18} />
              <span>步驟一：選擇會議文件與目標活動</span>
            </div>
            <span className="extract-card-badge">來源設定</span>
          </div>

          <div className="extract-selector-grid">
            {/* 選擇文件 */}
            <div className="selector-field">
              <label htmlFor="extract-doc-select">會議紀錄文件</label>
              <select
                id="extract-doc-select"
                value={selectedDocId}
                onChange={(e) => setSelectedDocId(e.target.value ? Number(e.target.value) : '')}
                disabled={isExtracting || isCommitting}
              >
                {documents.length === 0 ? (
                  <option value="">暫無已入庫文件（請先於對話面板上傳）</option>
                ) : (
                  documents.map((doc) => (
                    <option key={doc.id} value={doc.id}>
                      {doc.filename} ({doc.chunk_count} 個切片)
                    </option>
                  ))
                )}
              </select>
              <small>系統將直接讀取該文檔全文進行 1-shot 結構化抽取</small>
            </div>

            {/* 選擇目標活動 */}
            <div className="selector-field">
              <label htmlFor="extract-act-select">關聯活動</label>
              <select
                id="extract-act-select"
                value={selectedActivityId}
                onChange={(e) =>
                  setSelectedActivityId(e.target.value ? Number(e.target.value) : '')
                }
                disabled={isExtracting || isCommitting}
              >
                {activities.length === 0 ? (
                  <option value="">暫無可用活動</option>
                ) : (
                  activities.map((act) => (
                    <option key={act.id} value={act.id}>
                      {act.name} ({act.year} 年・{act.status || '進行中'})
                    </option>
                  ))
                )}
              </select>
              <small>萃取後的會議、決策與待辦將自動綁定至此活動</small>
            </div>
          </div>

          <div className="extract-action-row">
            <button
              type="button"
              className="button extract-run-btn"
              onClick={handleStartExtract}
              disabled={isExtracting || !selectedDocId || documents.length === 0}
            >
              <Sparkles size={16} />
              <span>{isExtracting ? 'AI 深度整理中…' : '開始 AI 結構化整理'}</span>
            </button>
          </div>
        </section>

        {/* 分析中骨架與載入狀態 */}
        {isExtracting && (
          <div className="extract-loading-box">
            <div className="extract-loading-spinner" />
            <strong>大語言模型正在深度分析會議全文…</strong>
            <p>正在自動萃取會議時間、地點、討論摘要、核心決策結論與後續待辦事項，請稍候。</p>
          </div>
        )}

        {/* 2. 結構化預覽卡片 (Preview Phase) */}
        {previewData && !isExtracting && (
          <>
            {/* 會議主體資訊 */}
            <section className="extract-card">
              <div className="extract-card-head">
                <div className="extract-card-title">
                  <Calendar size={18} />
                  <span>步驟二：會議基本資料核對</span>
                </div>
                <span className="extract-card-badge">即時編輯</span>
              </div>

              <div className="preview-form-grid">
                <div className="preview-form-group">
                  <label>會議名稱</label>
                  <input
                    type="text"
                    value={previewData.meeting.name || ''}
                    onChange={(e) => handleMeetingChange('name', e.target.value)}
                    placeholder="例：第一次籌備協調會"
                  />
                </div>

                <div className="preview-form-group">
                  <label>開會日期</label>
                  <input
                    type="text"
                    value={previewData.meeting.date || ''}
                    onChange={(e) => handleMeetingChange('date', e.target.value)}
                    placeholder="例：2026-09-20"
                  />
                </div>

                <div className="preview-form-group">
                  <label>時間範圍</label>
                  <input
                    type="text"
                    value={`${previewData.meeting.start_time || ''}${
                      previewData.meeting.end_time ? ' - ' + previewData.meeting.end_time : ''
                    }`}
                    onChange={(e) => {
                      const parts = e.target.value.split('-');
                      handleMeetingChange('start_time', parts[0]?.trim() || '');
                      handleMeetingChange('end_time', parts[1]?.trim() || '');
                    }}
                    placeholder="例：14:00 - 16:30"
                  />
                </div>

                <div className="preview-form-group">
                  <label>會議地點</label>
                  <input
                    type="text"
                    value={previewData.meeting.location || ''}
                    onChange={(e) => handleMeetingChange('location', e.target.value)}
                    placeholder="例：系辦大樓 201 會議室"
                  />
                </div>

                <div className="preview-form-group full-width">
                  <label>出席成員</label>
                  <input
                    type="text"
                    value={previewData.meeting.participants || ''}
                    onChange={(e) => handleMeetingChange('participants', e.target.value)}
                    placeholder="例：王小明, 李大華, 林同學"
                  />
                </div>

                <div className="preview-form-group full-width">
                  <label>會議討論大綱與內容</label>
                  <textarea
                    rows={3}
                    value={previewData.meeting.content || ''}
                    onChange={(e) => handleMeetingChange('content', e.target.value)}
                    placeholder="會議核心討論議題與記錄"
                  />
                </div>
              </div>
            </section>

            {/* 萃取的關鍵決策 (Decisions) */}
            <section className="extract-card">
              <div className="extract-card-head">
                <div className="extract-card-title">
                  <CheckCircle2 size={18} />
                  <span>已萃取決策紀錄 ({previewData.decisions.length} 項)</span>
                </div>
                <span className="extract-card-badge">Decisions</span>
              </div>

              {previewData.decisions.length === 0 ? (
                <p className="no-items-text">未在此會議中識別出明確決策項目</p>
              ) : (
                <div className="extract-items-stack">
                  {previewData.decisions.map((dec, idx) => (
                    <div key={idx} className="extract-sub-card">
                      <div className="extract-sub-card-header">
                        <span className="extract-sub-card-num">決策 #{idx + 1}</span>
                        <input
                          type="text"
                          className="extract-item-input"
                          style={{ maxWidth: '280px', fontWeight: 700 }}
                          value={dec.problem}
                          onChange={(e) => handleDecisionChange(idx, 'problem', e.target.value)}
                          placeholder="議題/問題"
                        />
                      </div>
                      <div className="preview-form-grid">
                        <div className="preview-form-group full-width">
                          <label>最終決策結論</label>
                          <input
                            type="text"
                            value={dec.final_decision}
                            onChange={(e) =>
                              handleDecisionChange(idx, 'final_decision', e.target.value)
                            }
                          />
                        </div>
                        <div className="preview-form-group">
                          <label>考量理由</label>
                          <input
                            type="text"
                            value={dec.reason}
                            onChange={(e) => handleDecisionChange(idx, 'reason', e.target.value)}
                          />
                        </div>
                        <div className="preview-form-group">
                          <label>來源段落依據</label>
                          <input
                            type="text"
                            value={dec.source}
                            onChange={(e) => handleDecisionChange(idx, 'source', e.target.value)}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* 萃取的待辦事項 (Tasks) */}
            <section className="extract-card">
              <div className="extract-card-head">
                <div className="extract-card-title">
                  <ListTodo size={18} />
                  <span>已萃取待辦事項 ({previewData.tasks.length} 項)</span>
                </div>
                <span className="extract-card-badge">Tasks</span>
              </div>

              {previewData.tasks.length === 0 ? (
                <p className="no-items-text">未在此會議中識別出待辦執行事項</p>
              ) : (
                <div className="extract-items-stack">
                  {previewData.tasks.map((tsk, idx) => (
                    <div key={idx} className="extract-sub-card">
                      <div className="extract-sub-card-header">
                        <span className="extract-sub-card-num">待辦 #{idx + 1}</span>
                        <input
                          type="text"
                          className="extract-item-input"
                          style={{ flex: 1, marginLeft: '10px' }}
                          value={tsk.content}
                          onChange={(e) => handleTaskChange(idx, 'content', e.target.value)}
                          placeholder="待辦事項內容"
                        />
                      </div>
                      <div className="preview-form-grid">
                        <div className="preview-form-group">
                          <label>指派負責人</label>
                          <input
                            type="text"
                            value={tsk.assignee || ''}
                            onChange={(e) => handleTaskChange(idx, 'assignee', e.target.value)}
                            placeholder="例：林同學"
                          />
                        </div>
                        <div className="preview-form-group">
                          <label>預計完成期限</label>
                          <input
                            type="text"
                            value={tsk.due_date || ''}
                            onChange={(e) => handleTaskChange(idx, 'due_date', e.target.value)}
                            placeholder="例：2026-09-25"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>

      {/* 3. 底部確認寫入操作欄 (Commit Phase) */}
      {previewData && !isExtracting && (
        <div className="extract-bottom-dock">
          <button
            type="button"
            className="button secondary"
            onClick={handleReset}
            disabled={isCommitting}
          >
            重新選擇文件
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '.84rem', color: 'var(--muted)' }}>
              目標活動：<strong>{selectedActivityName}</strong>
            </span>
            <button
              type="button"
              className="button commit-btn"
              onClick={handleCommit}
              disabled={isCommitting || !selectedActivityId}
            >
              <Check size={16} />
              <span>{isCommitting ? '寫入資料庫中…' : '確認寫入活動資料庫'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default MeetingExtractPanel;
