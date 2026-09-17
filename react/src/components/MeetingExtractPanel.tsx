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
  RefreshCw,
  Check,
  RotateCcw,
} from 'lucide-react';
import { fetchDocuments } from '../services/documentService';
import { BackendDocument } from '../services/apiTypes';
import {
  extractMeetingSummary,
  commitMeetingSummary,
  MeetingPreviewData,
} from '../services/meetingExtractService';
import './MeetingExtractPanel.css';

/**
 * AI 會議紀錄整理面板 (Meeting Extract Panel)
 * 核心功能：
 * 1. 從已上傳的文件挑選一份會議紀錄
 * 2. 呼叫 LLM 依據 System Prompt 提煉成標準化結構（會議摘要、決策、待辦）
 * 3. 呈現結構化標準表格並提供使用者確認
 * 4. 確認後一鍵寫入資料庫
 */
export const MeetingExtractPanel: React.FC = () => {
  // 已入庫文檔清單
  const [documents, setDocuments] = useState<BackendDocument[]>([]);
  // 當前選中的文檔 ID
  const [selectedDocId, setSelectedDocId] = useState<number | ''>('');

  // 後端既有活動 ID (背後連結用，不干擾前端簡潔介面)
  const [defaultActivityId, setDefaultActivityId] = useState<number>(1);

  // 狀態管理
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isCommitting, setIsCommitting] = useState(false);
  const [isCommitted, setIsCommitted] = useState(false);

  // 提示與錯誤訊息
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // LLM 返回之標準化預覽資料
  const [previewData, setPreviewData] = useState<MeetingPreviewData | null>(null);

  /**
   * 載入已上傳文件清單
   */
  const loadDocumentsList = useCallback(async () => {
    setIsLoadingDocs(true);
    setErrorMessage(null);
    try {
      const docs = await fetchDocuments();
      setDocuments(docs);
      if (docs.length > 0 && selectedDocId === '') {
        setSelectedDocId(docs[0].id);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMessage(`無法載入文檔清單：${msg}`);
    } finally {
      setIsLoadingDocs(false);
    }
  }, [selectedDocId]);

  useEffect(() => {
    loadDocumentsList();
  }, [loadDocumentsList]);

  /**
   * 步驟 1：觸發 LLM 根據 system prompt 整理會議紀錄 (POST /extract_summary)
   */
  const handleExtract = async () => {
    if (!selectedDocId) {
      setErrorMessage('請先從下拉選單選擇欲整理的會議文件');
      return;
    }

    setIsExtracting(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    setIsCommitted(false);

    try {
      const res = await extractMeetingSummary(Number(selectedDocId));
      setPreviewData(res.preview_data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMessage(`會議整理失敗：${msg}`);
    } finally {
      setIsExtracting(false);
    }
  };

  /**
   * 步驟 2：使用者確認後，寫入資料庫 (POST /commit_summary)
   */
  const handleCommit = async () => {
    if (!previewData) return;

    setIsCommitting(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const res = await commitMeetingSummary({
        activity_id: defaultActivityId,
        meeting: previewData.meeting,
        decisions: previewData.decisions,
        tasks: previewData.tasks,
      });

      setIsCommitted(true);
      setSuccessMessage(
        `${res.message}（包含 1 筆會議紀錄、${res.decisions.length} 項關鍵決策、${res.tasks.length} 項待辦事項）`
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMessage(`寫入資料庫失敗：${msg}`);
    } finally {
      setIsCommitting(false);
    }
  };

  /**
   * 重新整理或挑選其他文件
   */
  const handleReset = () => {
    setPreviewData(null);
    setIsCommitted(false);
    setSuccessMessage(null);
    setErrorMessage(null);
  };

  return (
    <div className="extract-panel-layout">
      {/* 頂部標題列 */}
      <header className="extract-top-header">
        <div className="extract-header-title">
          <Sparkles size={20} className="extract-sparkle-icon" />
          <h2>AI 會議紀錄整理</h2>
        </div>
        <button
          type="button"
          className="button secondary sm-btn"
          onClick={loadDocumentsList}
          disabled={isLoadingDocs || isExtracting || isCommitting}
          title="重新整理文件清單"
        >
          <RefreshCw size={14} className={isLoadingDocs ? 'spinning' : ''} />
          <span>重新整理</span>
        </button>
      </header>

      {/* 錯誤警示列 */}
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

      {/* 主內容獨立滾動區 */}
      <div className="extract-content-scroll">
        {/* 1. 選擇已上傳文件區塊 */}
        <section className="extract-card">
          <div className="extract-card-head">
            <div className="extract-card-title">
              <FileText size={18} />
              <span>選擇會議紀錄文件</span>
            </div>
            <span className="extract-card-badge">已導入文檔</span>
          </div>

          <div className="doc-pick-row">
            <div className="doc-select-wrap">
              <select
                id="meeting-doc-picker"
                value={selectedDocId}
                onChange={(e) => setSelectedDocId(e.target.value ? Number(e.target.value) : '')}
                disabled={isExtracting || isCommitting}
              >
                {documents.length === 0 ? (
                  <option value="">尚未有已入庫之文件（可於對話面板的文檔抽屜上傳）</option>
                ) : (
                  documents.map((doc) => (
                    <option key={doc.id} value={doc.id}>
                      {doc.filename} ({doc.chunk_count} 個切片)
                    </option>
                  ))
                )}
              </select>
            </div>

            <button
              type="button"
              className="button extract-run-btn"
              onClick={handleExtract}
              disabled={isExtracting || !selectedDocId || documents.length === 0}
            >
              <Sparkles size={16} />
              <span>{isExtracting ? 'LLM 整理分析中…' : '開始整理會議紀錄'}</span>
            </button>
          </div>
        </section>

        {/* 分析處理中狀態 */}
        {isExtracting && (
          <div className="extract-loading-box">
            <div className="extract-loading-spinner" />
            <strong>LLM 正在閱讀全文並整理標準會議架構…</strong>
            <p>依據專業秘書 System Prompt 自動提煉會議摘要、關鍵決策與待辦清單，請稍候。</p>
          </div>
        )}

        {/* 成功寫入提示 */}
        {successMessage && (
          <div className="extract-success-banner" role="status">
            <div className="extract-success-info">
              <CheckCircle2 size={20} />
              <span>{successMessage}</span>
            </div>
            <button
              type="button"
              className="button secondary sm-btn"
              onClick={handleReset}
            >
              <RotateCcw size={14} />
              <span>整理下一份會議</span>
            </button>
          </div>
        )}

        {/* 2. 呈現 LLM 返回的標準化架構表格 (供確認) */}
        {previewData && !isExtracting && (
          <>
            {/* 會議基本資訊表格 */}
            <section className="extract-card">
              <div className="extract-card-head">
                <div className="extract-card-title">
                  <Calendar size={18} />
                  <span>會議基本摘要</span>
                </div>
                <span className="extract-card-badge">會議概況</span>
              </div>

              <div className="standard-table-wrap">
                <table className="standard-meeting-table">
                  <tbody>
                    <tr>
                      <th>會議名稱</th>
                      <td colSpan={3}>
                        <strong>{previewData.meeting.name || '未提及'}</strong>
                      </td>
                    </tr>
                    <tr>
                      <th>開會日期</th>
                      <td>{previewData.meeting.date || '未提及'}</td>
                      <th>時間範圍</th>
                      <td>
                        {previewData.meeting.start_time || ''}
                        {previewData.meeting.end_time ? ` - ${previewData.meeting.end_time}` : ''}
                        {!previewData.meeting.start_time && !previewData.meeting.end_time && '未提及'}
                      </td>
                    </tr>
                    <tr>
                      <th>會議地點</th>
                      <td>{previewData.meeting.location || '未提及'}</td>
                      <th>參與成員</th>
                      <td>{previewData.meeting.participants || '未提及'}</td>
                    </tr>
                    <tr>
                      <th>討論摘要</th>
                      <td colSpan={3} className="content-cell">
                        {previewData.meeting.content || '無詳細摘要'}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            {/* 關鍵決策事項 (Decisions) 表格 */}
            <section className="extract-card">
              <div className="extract-card-head">
                <div className="extract-card-title">
                  <CheckCircle2 size={18} />
                  <span>關鍵決策事項 ({previewData.decisions.length} 項)</span>
                </div>
                <span className="extract-card-badge">Decisions</span>
              </div>

              {previewData.decisions.length === 0 ? (
                <p className="no-data-note">此份會議紀錄中未識別出明確決策項目。</p>
              ) : (
                <div className="standard-table-wrap">
                  <table className="standard-data-table">
                    <thead>
                      <tr>
                        <th style={{ width: '60px' }}>編號</th>
                        <th>討論議題 / 問題</th>
                        <th>最終決策結論</th>
                        <th>考量理由</th>
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.decisions.map((dec, idx) => (
                        <tr key={idx}>
                          <td className="index-cell">{idx + 1}</td>
                          <td className="topic-cell">{dec.problem}</td>
                          <td className="decision-cell">{dec.final_decision}</td>
                          <td className="reason-cell">{dec.reason || '無'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            {/* 行動待辦清單 (Tasks) 表格 */}
            <section className="extract-card">
              <div className="extract-card-head">
                <div className="extract-card-title">
                  <ListTodo size={18} />
                  <span>行動待辦清單 ({previewData.tasks.length} 項)</span>
                </div>
                <span className="extract-card-badge">Tasks</span>
              </div>

              {previewData.tasks.length === 0 ? (
                <p className="no-data-note">此份會議紀錄中未識別出待辦執行項目。</p>
              ) : (
                <div className="standard-table-wrap">
                  <table className="standard-data-table">
                    <thead>
                      <tr>
                        <th style={{ width: '60px' }}>編號</th>
                        <th>待辦執行項目</th>
                        <th style={{ width: '120px' }}>指派人</th>
                        <th style={{ width: '130px' }}>完成期限</th>
                        <th style={{ width: '90px' }}>優先級</th>
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.tasks.map((tsk, idx) => (
                        <tr key={idx}>
                          <td className="index-cell">{idx + 1}</td>
                          <td>{tsk.content}</td>
                          <td>
                            <span className="person-pill">{tsk.assignee || '未指定'}</span>
                          </td>
                          <td>{tsk.due_date || '無期限'}</td>
                          <td>
                            <span
                              className={`priority-tag ${
                                tsk.priority === '高' ? 'high' : tsk.priority === '低' ? 'low' : 'mid'
                              }`}
                            >
                              {tsk.priority || '中'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        )}
      </div>

      {/* 底部確認寫入操作區 */}
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

          <button
            type="button"
            className="button commit-btn"
            onClick={handleCommit}
            disabled={isCommitting || isCommitted}
          >
            <Check size={16} />
            <span>
              {isCommitted
                ? '已成功寫入資料庫'
                : isCommitting
                ? '寫入資料庫中…'
                : '確認寫入資料庫'}
            </span>
          </button>
        </div>
      )}
    </div>
  );
};

export default MeetingExtractPanel;
