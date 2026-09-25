import React, { useState, useEffect, useCallback } from 'react';
import {
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
  Plus,
  Trash2,
} from 'lucide-react';
import { fetchDocuments } from '../api/documentService';
import { BackendDocument } from '../api/apiTypes';
import {
  extractMeetingSummary,
  commitMeetingSummary,
  MeetingPreviewData,
} from '../api/meetingExtractService';
import ConfirmModal from './ConfirmModal';
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

  // 全域防手殘確認對話框狀態
  const [confirmDialog, setConfirmDialog] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
  }>({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: () => { },
  });

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
      const selectedDoc = documents.find((d) => d.id === selectedDocId);
      const res = await commitMeetingSummary({
        activity_id: defaultActivityId,
        doc_id: typeof selectedDocId === 'number' ? selectedDocId : undefined,
        source_file: selectedDoc?.filename,
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
   * 編輯會議摘要基本欄位
   */
  const handleUpdateMeetingField = (field: keyof typeof previewData.meeting, value: string) => {
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
   * 編輯關鍵決策欄位
   */
  const handleUpdateDecisionField = (index: number, field: string, value: string) => {
    if (!previewData) return;
    const updatedDecisions = [...previewData.decisions];
    updatedDecisions[index] = {
      ...updatedDecisions[index],
      [field]: value,
    };
    setPreviewData({
      ...previewData,
      decisions: updatedDecisions,
    });
  };

  /**
   * 刪除一筆決策 (先跳出全螢幕模糊確認視窗)
   */
  const handleDeleteDecision = (index: number) => {
    if (!previewData) return;
    const targetDecision = previewData.decisions[index];
    const decisionTopic = targetDecision?.problem ? `「${targetDecision.problem}」` : `第 ${index + 1} 項決策`;

    setConfirmDialog({
      isOpen: true,
      title: '確定要刪除此項決策？',
      message: `確定要從本次會議整理中移除決策 ${decisionTopic} 嗎？`,
      onConfirm: () => {
        setConfirmDialog((prev) => ({ ...prev, isOpen: false }));
        setPreviewData((prev) => {
          if (!prev) return null;
          return {
            ...prev,
            decisions: prev.decisions.filter((_, i) => i !== index),
          };
        });
      },
    });
  };

  /**
   * 新增一筆自訂決策
   */
  const handleAddDecision = () => {
    if (!previewData) return;
    const fallbackFilename = documents.find((d) => d.id === selectedDocId)?.filename || '會議紀錄全文';
    setPreviewData({
      ...previewData,
      decisions: [
        ...previewData.decisions,
        {
          problem: '',
          options: '[]',
          final_decision: '',
          reason: '',
          source: fallbackFilename,
        },
      ],
    });
  };

  /**
   * 編輯待辦清單欄位
   */
  const handleUpdateTaskField = (index: number, field: string, value: string) => {
    if (!previewData) return;
    const updatedTasks = [...previewData.tasks];
    updatedTasks[index] = {
      ...updatedTasks[index],
      [field]: value,
    };
    setPreviewData({
      ...previewData,
      tasks: updatedTasks,
    });
  };

  /**
   * 刪除一筆待辦事項 (先跳出全螢幕模糊確認視窗)
   */
  const handleDeleteTask = (index: number) => {
    if (!previewData) return;
    const targetTask = previewData.tasks[index];
    const taskContent = targetTask?.content ? `「${targetTask.content}」` : `第 ${index + 1} 項待辦事項`;

    setConfirmDialog({
      isOpen: true,
      title: '確定要刪除此項待辦？',
      message: `確定要從本次待辦清單中移除待辦 ${taskContent} 嗎？`,
      onConfirm: () => {
        setConfirmDialog((prev) => ({ ...prev, isOpen: false }));
        setPreviewData((prev) => {
          if (!prev) return null;
          return {
            ...prev,
            tasks: prev.tasks.filter((_, i) => i !== index),
          };
        });
      },
    });
  };

  /**
   * 新增一筆待辦事項
   */
  const handleAddTask = () => {
    if (!previewData) return;
    setPreviewData({
      ...previewData,
      tasks: [
        ...previewData.tasks,
        {
          content: '',
          assignee: '',
          due_date: '',
          priority: '中',
          status: 'pending',
        },
      ],
    });
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
          <h2>DASH 會議紀錄整理</h2>
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

        {/* 2. 呈現 LLM 返回的標準化架構表格 (供檢視、編輯與確認) */}
        {previewData && !isExtracting && (
          <>
            {/* 會議基本資訊表格 */}
            <section className="extract-card">
              <div className="extract-card-head">
                <div className="extract-card-title">
                  <Calendar size={18} />
                  <span>會議基本摘要</span>
                </div>
                <div className="extract-card-actions">
                  <span className="extract-card-hint">可直接點擊欄位進行修改</span>
                  <span className="extract-card-badge">會議概況</span>
                </div>
              </div>

              <div className="standard-table-wrap">
                <table className="standard-meeting-table editable">
                  <tbody>
                    <tr>
                      <th>會議名稱</th>
                      <td colSpan={3}>
                        <input
                          type="text"
                          className="table-input title-input"
                          value={previewData.meeting.name || ''}
                          onChange={(e) => handleUpdateMeetingField('name', e.target.value)}
                          placeholder="例如：迎新宿營第一次籌備會"
                        />
                      </td>
                    </tr>
                    <tr>
                      <th>開會日期</th>
                      <td>
                        <input
                          type="text"
                          className="table-input"
                          value={previewData.meeting.date || ''}
                          onChange={(e) => handleUpdateMeetingField('date', e.target.value)}
                          placeholder="例如：2026-09-20"
                        />
                      </td>
                      <th>時間範圍</th>
                      <td>
                        <div className="table-dual-input">
                          <input
                            type="text"
                            className="table-input"
                            value={previewData.meeting.start_time || ''}
                            onChange={(e) => handleUpdateMeetingField('start_time', e.target.value)}
                            placeholder="開始時間 (如 14:00)"
                          />
                          <span className="input-sep">-</span>
                          <input
                            type="text"
                            className="table-input"
                            value={previewData.meeting.end_time || ''}
                            onChange={(e) => handleUpdateMeetingField('end_time', e.target.value)}
                            placeholder="結束時間 (如 16:30)"
                          />
                        </div>
                      </td>
                    </tr>
                    <tr>
                      <th>會議地點</th>
                      <td>
                        <input
                          type="text"
                          className="table-input"
                          value={previewData.meeting.location || ''}
                          onChange={(e) => handleUpdateMeetingField('location', e.target.value)}
                          placeholder="例如：活動中心 201 會議室"
                        />
                      </td>
                      <th>參與成員</th>
                      <td>
                        <input
                          type="text"
                          className="table-input"
                          value={previewData.meeting.participants || ''}
                          onChange={(e) => handleUpdateMeetingField('participants', e.target.value)}
                          placeholder="例如：王小明, 李大華, 張小芳"
                        />
                      </td>
                    </tr>
                    <tr>
                      <th>討論摘要</th>
                      <td colSpan={3} className="content-cell">
                        <textarea
                          className="table-textarea"
                          rows={3}
                          value={previewData.meeting.content || ''}
                          onChange={(e) => handleUpdateMeetingField('content', e.target.value)}
                          placeholder="輸入或調整會議整體討論概述…"
                        />
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
                <div className="extract-card-actions">
                  <button
                    type="button"
                    className="button secondary sm-btn"
                    onClick={handleAddDecision}
                    title="新增一項決策"
                  >
                    <Plus size={14} />
                    <span>新增決策</span>
                  </button>
                  <span className="extract-card-badge">Decisions</span>
                </div>
              </div>

              {previewData.decisions.length === 0 ? (
                <div className="no-data-action-wrap">
                  <p className="no-data-note">此份會議紀錄中未識別出明確決策項目。</p>
                  <button
                    type="button"
                    className="button secondary sm-btn"
                    onClick={handleAddDecision}
                  >
                    <Plus size={14} />
                    <span>新增第一筆決策</span>
                  </button>
                </div>
              ) : (
                <div className="standard-table-wrap">
                  <table className="standard-data-table editable">
                    <thead>
                      <tr>
                        <th style={{ width: '45px' }}>編號</th>
                        <th style={{ width: '25%' }}>討論議題 / 問題</th>
                        <th style={{ width: '25%' }}>最終決策結論</th>
                        <th style={{ width: '25%' }}>考量理由</th>
                        <th style={{ width: '15%' }}>資料來源</th>
                        <th style={{ width: '50px', textAlign: 'center' }}>操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.decisions.map((dec, idx) => (
                        <tr key={idx}>
                          <td className="index-cell">{idx + 1}</td>
                          <td>
                            <textarea
                              className="table-cell-textarea topic-area"
                              rows={2}
                              value={dec.problem}
                              onChange={(e) =>
                                handleUpdateDecisionField(idx, 'problem', e.target.value)
                              }
                              placeholder="討論的問題或議題…"
                            />
                          </td>
                          <td>
                            <textarea
                              className="table-cell-textarea decision-area"
                              rows={2}
                              value={dec.final_decision}
                              onChange={(e) =>
                                handleUpdateDecisionField(idx, 'final_decision', e.target.value)
                              }
                              placeholder="最終定案結論…"
                            />
                          </td>
                          <td>
                            <textarea
                              className="table-cell-textarea reason-area"
                              rows={2}
                              value={dec.reason || ''}
                              onChange={(e) =>
                                handleUpdateDecisionField(idx, 'reason', e.target.value)
                              }
                              placeholder="決策考量之理由或背景…"
                            />
                          </td>
                          <td>
                            <input
                              type="text"
                              className="table-cell-input source-area"
                              value={
                                dec.source !== undefined
                                  ? dec.source
                                  : documents.find((d) => d.id === selectedDocId)?.filename || ''
                              }
                              onChange={(e) =>
                                handleUpdateDecisionField(idx, 'source', e.target.value)
                              }
                              placeholder="如：檔名或章節"
                            />
                          </td>
                          <td style={{ textAlign: 'center' }}>
                            <button
                              type="button"
                              className="table-row-delete-btn"
                              onClick={() => handleDeleteDecision(idx)}
                              title="刪除此項決策"
                            >
                              <Trash2 size={15} />
                            </button>
                          </td>
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
                <div className="extract-card-actions">
                  <button
                    type="button"
                    className="button secondary sm-btn"
                    onClick={handleAddTask}
                    title="新增一項待辦"
                  >
                    <Plus size={14} />
                    <span>新增待辦</span>
                  </button>
                  <span className="extract-card-badge">Tasks</span>
                </div>
              </div>

              {previewData.tasks.length === 0 ? (
                <div className="no-data-action-wrap">
                  <p className="no-data-note">此份會議紀錄中未識別出待辦執行項目。</p>
                  <button
                    type="button"
                    className="button secondary sm-btn"
                    onClick={handleAddTask}
                  >
                    <Plus size={14} />
                    <span>新增第一筆待辦</span>
                  </button>
                </div>
              ) : (
                <div className="standard-table-wrap">
                  <table className="standard-data-table editable">
                    <thead>
                      <tr>
                        <th style={{ width: '45px' }}>編號</th>
                        <th>待辦執行項目</th>
                        <th style={{ width: '130px' }}>指派人</th>
                        <th style={{ width: '130px' }}>完成期限</th>
                        <th style={{ width: '100px' }}>優先級</th>
                        <th style={{ width: '50px', textAlign: 'center' }}>操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.tasks.map((tsk, idx) => (
                        <tr key={idx}>
                          <td className="index-cell">{idx + 1}</td>
                          <td>
                            <input
                              type="text"
                              className="table-cell-input"
                              value={tsk.content}
                              onChange={(e) =>
                                handleUpdateTaskField(idx, 'content', e.target.value)
                              }
                              placeholder="待辦工作內容…"
                            />
                          </td>
                          <td>
                            <input
                              type="text"
                              className="table-cell-input person-input"
                              value={tsk.assignee || ''}
                              onChange={(e) =>
                                handleUpdateTaskField(idx, 'assignee', e.target.value)
                              }
                              placeholder="負責人"
                            />
                          </td>
                          <td>
                            <input
                              type="text"
                              className="table-cell-input date-input"
                              value={tsk.due_date || ''}
                              onChange={(e) =>
                                handleUpdateTaskField(idx, 'due_date', e.target.value)
                              }
                              placeholder="如：2026-09-30"
                            />
                          </td>
                          <td>
                            <select
                              className={`priority-select ${tsk.priority === '高'
                                  ? 'high'
                                  : tsk.priority === '低'
                                    ? 'low'
                                    : 'mid'
                                }`}
                              value={tsk.priority || '中'}
                              onChange={(e) =>
                                handleUpdateTaskField(idx, 'priority', e.target.value)
                              }
                            >
                              <option value="高">高優先</option>
                              <option value="中">中優先</option>
                              <option value="低">低優先</option>
                            </select>
                          </td>
                          <td style={{ textAlign: 'center' }}>
                            <button
                              type="button"
                              className="table-row-delete-btn"
                              onClick={() => handleDeleteTask(idx)}
                              title="刪除此項待辦"
                            >
                              <Trash2 size={15} />
                            </button>
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

      {/* 全域模糊防手殘確認對話框 */}
      <ConfirmModal
        isOpen={confirmDialog.isOpen}
        title={confirmDialog.title}
        message={confirmDialog.message}
        onConfirm={confirmDialog.onConfirm}
        onCancel={() => setConfirmDialog((prev) => ({ ...prev, isOpen: false }))}
      />
    </div>
  );
};

export default MeetingExtractPanel;
