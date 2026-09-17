import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Bot, User, MessageSquare, Sparkles, ChevronDown, ChevronUp, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import SessionSidebar, { SessionItem } from './SessionSidebar';
import DocumentDrawer, { DocumentItem } from './DocumentDrawer';

/**
 * 訊息氣泡介面定義
 */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  mode?: 'chat' | 'rag';
  createdAt: string;
  // 檢索切片引用來源 (可選)
  retrievedChunks?: Array<{
    content: string;
    source?: string;
  }>;
}

/**
 * LLM 聊天面板主組件 (Chat Panel)
 * 整合：
 * 1. 雙欄佈局 (會話清單邊欄 + 聊天串流主區)
 * 2. 模式切換 Toggle Pill (💬 普通對話 vs 📚 知識庫問答)
 * 3. 極簡空狀態 (無訊息時顯示簡潔圖示與提示)
 * 4. 浮動知識庫文檔抽屜 (Document Drawer)
 * 5. 本機狀態發送互動與自動捲動
 */
export const ChatPanel: React.FC = () => {
  // 會話列表狀態 (初始為空列表，無假資料)
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  // 當前選中的會話 ID
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  // 當前對話模式：'chat' (普通對話) 或 'rag' (知識庫問答)
  const [currentMode, setCurrentMode] = useState<'chat' | 'rag'>('chat');

  // 訊息串流狀態 (對應各會話的訊息對應表，初始皆為空)
  const [sessionMessages, setSessionMessages] = useState<Record<string, ChatMessage[]>>({});

  // 輸入框文字狀態
  const [input, setInput] = useState('');
  // 訊息發送中的 Loading 狀態 (供互動模擬)
  const [loading, setLoading] = useState(false);

  // 知識庫文檔抽屜開啟狀態
  const [isDocDrawerOpen, setIsDocDrawerOpen] = useState(false);
  // 知識庫文件清單狀態 (初始為空列表，無假資料)
  const [documents, setDocuments] = useState<DocumentItem[]>([]);

  // 參考切片折疊狀態 (key: messageId, value: boolean)
  const [expandedChunks, setExpandedChunks] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 訊息更新時自動向下滾動至最新訊息
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const currentMessages = activeSessionId ? sessionMessages[activeSessionId] || [] : [];

  useEffect(() => {
    scrollToBottom();
  }, [currentMessages, loading]);

  /**
   * 新增對話會話 (本機狀態)
   */
  const handleCreateSession = () => {
    const newId = `session-${Date.now()}`;
    const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const newSession: SessionItem = {
      id: newId,
      title: '新對話',
      createdAt: nowStr,
    };

    setSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(newId);
    setSessionMessages((prev) => ({
      ...prev,
      [newId]: [],
    }));
  };

  /**
   * 刪除指定會話 (本機狀態)
   */
  const handleDeleteSession = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSessions((prev) => prev.filter((s) => s.id !== id));
    setSessionMessages((prev) => {
      const updated = { ...prev };
      delete updated[id];
      return updated;
    });

    if (activeSessionId === id) {
      // 若刪除的是當前會話，自動切換至剩餘的第一個會話或 null
      const remaining = sessions.filter((s) => s.id !== id);
      setActiveSessionId(remaining.length > 0 ? remaining[0].id : null);
    }
  };

  /**
   * 發送訊息處理函式 (第一階段：本機狀態互動)
   */
  const handleSendMessage = () => {
    if (!input.trim() || loading) return;

    // 若當前尚未有選中的會話，自動為使用者建立一個
    let targetSessionId = activeSessionId;
    if (!targetSessionId) {
      const newId = `session-${Date.now()}`;
      const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const newSession: SessionItem = {
        id: newId,
        title: input.trim().slice(0, 15),
        createdAt: nowStr,
      };
      setSessions((prev) => [newSession, ...prev]);
      targetSessionId = newId;
      setActiveSessionId(newId);
    }

    const userText = input.trim();
    const nowTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // 建立使用者自身訊息氣泡
    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: userText,
      mode: currentMode,
      createdAt: nowTime,
    };

    // 更新當前會話的訊息紀錄
    setSessionMessages((prev) => ({
      ...prev,
      [targetSessionId as string]: [...(prev[targetSessionId as string] || []), userMsg],
    }));

    // 若會話標題仍為「新對話」，自動更新為提問文字
    setSessions((prev) =>
      prev.map((s) => {
        if (s.id === targetSessionId && s.title === '新對話') {
          return { ...s, title: userText.slice(0, 16) };
        }
        return s;
      })
    );

    setInput('');
    setLoading(true);

    // 模擬助手回傳預留提示訊息 (供驗證氣泡與滾動樣式)
    setTimeout(() => {
      const assistantReply: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content:
          currentMode === 'rag'
            ? `（UI 框架展示階段）您在「**知識庫問答**」模式下提問：\n\n> ${userText}\n\n目前尚未連接後端 API，後續將自動檢索入庫文檔並提供結構化解答與引用來源。`
            : `（UI 框架展示階段）您在「**普通對話**」模式下提問：\n\n> ${userText}\n\n目前尚未連接後端 API，後續將由大語言模型直接生成回覆。`,
        mode: currentMode,
        createdAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        // 若為 RAG 模式，展示預留的切片來源卡片骨架
        retrievedChunks:
          currentMode === 'rag'
            ? [
              {
                source: '活動籌備規劃指引.md',
                content: '活動籌備期間應定期召開籌備協調會議，各組工作進度與突發狀況應詳實記錄...',
              },
            ]
            : undefined,
      };

      setSessionMessages((prev) => ({
        ...prev,
        [targetSessionId as string]: [...(prev[targetSessionId as string] || []), assistantReply],
      }));
      setLoading(false);
    }, 600);
  };

  /**
   * 鍵盤 Enter 鍵發送處理 (Shift+Enter 為換行)
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  /**
   * 切換切片折疊展開狀態
   */
  const toggleChunkExpand = (messageId: string) => {
    setExpandedChunks((prev) => ({
      ...prev,
      [messageId]: !prev[messageId],
    }));
  };

  // 本機上傳文件模擬
  const handleUploadFileLocal = (file: File) => {
    const newDoc: DocumentItem = {
      id: `doc-${Date.now()}`,
      name: file.name,
      size: `${(file.size / 1024).toFixed(1)} KB`,
      uploadedAt: '剛才',
      chunkCount: 3,
    };
    setDocuments((prev) => [newDoc, ...prev]);
  };

  // 本機刪除文件模擬
  const handleDeleteDocumentLocal = (id: string) => {
    setDocuments((prev) => prev.filter((d) => d.id !== id));
  };

  const activeSessionTitle =
    sessions.find((s) => s.id === activeSessionId)?.title || '未選擇對話';

  return (
    <div className="chat-panel-layout">
      {/* 1. 左側：會話歷史側邊欄 */}
      <SessionSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={setActiveSessionId}
        onCreateSession={handleCreateSession}
        onDeleteSession={handleDeleteSession}
        onOpenDocDrawer={() => setIsDocDrawerOpen(true)}
        docCount={documents.length}
      />

      {/* 2. 右側：聊天主區域 */}
      <section className="chat-main-area">
        {/* 頂部資訊列 */}
        <header className="chat-top-header">
          <div className="chat-header-title">
            <Sparkles size={18} className="sparkle-icon" />
            <h2>{activeSessionId ? activeSessionTitle : 'AI 智庫對話'}</h2>
          </div>
          <div className="chat-header-actions">
            <button
              type="button"
              className="button secondary sm-btn"
              onClick={() => setIsDocDrawerOpen(true)}
            >
              <FileText size={15} />
              <span>知識庫 ({documents.length})</span>
            </button>
          </div>
        </header>

        {/* 聊天串流訊息滾動區 */}
        <div className="chat-stream-container">
          {currentMessages.length === 0 ? (
            // 極簡空狀態 (符合用戶偏好：簡約圖示與提示字樣)
            <div className="chat-empty-state">
              <div className="empty-icon-wrapper">
                <Bot size={40} />
              </div>
              <h3>尚無訊息</h3>
              <p>在下方輸入開始對話，或切換模式詢問知識庫</p>
            </div>
          ) : (
            // 渲染訊息氣泡列表
            <div className="chat-messages-flow">
              {currentMessages.map((msg) => {
                const isUser = msg.role === 'user';
                const hasChunks = msg.retrievedChunks && msg.retrievedChunks.length > 0;
                const isExpanded = !!expandedChunks[msg.id];

                return (
                  <div
                    key={msg.id}
                    className={`chat-bubble-row ${isUser ? 'user-row' : 'assistant-row'}`}
                  >
                    {/* 頭像 */}
                    <div className={`chat-avatar ${isUser ? 'user-avatar' : 'assistant-avatar'}`}>
                      {isUser ? <User size={18} /> : <Bot size={18} />}
                    </div>

                    {/* 氣泡內容 */}
                    <div className="chat-bubble-wrapper">
                      <div className="chat-bubble-meta">
                        <span className="bubble-author">{isUser ? '你' : 'AI 助手'}</span>
                        <span className="bubble-time">{msg.createdAt}</span>
                        {msg.mode && (
                          <span className={`bubble-mode-tag ${msg.mode}`}>
                            {msg.mode === 'rag' ? '知識庫問答' : '普通對話'}
                          </span>
                        )}
                      </div>

                      <div className={`chat-bubble-body ${isUser ? 'user-body' : 'assistant-body'}`}>
                        <ReactMarkdown>{msg.content}</ReactMarkdown>

                        {/* RAG 參考來源折疊卡片 */}
                        {hasChunks && (
                          <div className="rag-chunk-card">
                            <button
                              type="button"
                              className="rag-chunk-header"
                              onClick={() => toggleChunkExpand(msg.id)}
                            >
                              <div className="rag-chunk-title">
                                <span>📎</span>
                                <strong>參考來源 ({msg.retrievedChunks!.length} 筆切片)</strong>
                              </div>
                              {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                            </button>

                            {isExpanded && (
                              <div className="rag-chunk-content-list">
                                {msg.retrievedChunks!.map((chunk, idx) => (
                                  <div key={idx} className="rag-chunk-item">
                                    <div className="rag-chunk-source">
                                      <span>來源：</span>
                                      <em>{chunk.source || '上傳文件'}</em>
                                    </div>
                                    <p className="rag-chunk-text">{chunk.content}</p>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* 發送中的 Loading 骨架 */}
              {loading && (
                <div className="chat-bubble-row assistant-row">
                  <div className="chat-avatar assistant-avatar">
                    <Bot size={18} />
                  </div>
                  <div className="chat-bubble-wrapper">
                    <div className="chat-bubble-body assistant-body loading-bubble">
                      <span className="loading-dot"></span>
                      <span className="loading-dot"></span>
                      <span className="loading-dot"></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* 底部輸入區域 */}
        <div className="chat-bottom-dock">
          {/* 模式切換 Toggle Pill */}
          <div className="mode-toggle-bar">
            <div className="mode-toggle-pill">
              <button
                type="button"
                className={`mode-toggle-option ${currentMode === 'chat' ? 'active' : ''}`}
                onClick={() => setCurrentMode('chat')}
              >
                <span>💬</span>
                <strong>普通對話</strong>
              </button>
              <button
                type="button"
                className={`mode-toggle-option ${currentMode === 'rag' ? 'active' : ''}`}
                onClick={() => setCurrentMode('rag')}
              >
                <span>📚</span>
                <strong>知識庫問答</strong>
              </button>
            </div>
            <span className="mode-tip-text">
              {currentMode === 'rag'
                ? '將檢索已導入之文件切片輔助回答'
                : '無需檢索文件，由 AI 自由發揮與上下文記憶對話'}
            </span>
          </div>

          {/* 輸入框與發送按鈕組 */}
          <div className="chat-input-wrapper">
            <button
              type="button"
              className="chat-input-btn doc-attach-btn"
              title="管理知識庫文件"
              onClick={() => setIsDocDrawerOpen(true)}
            >
              <Paperclip size={18} />
            </button>

            <textarea
              className="chat-textarea"
              placeholder={
                currentMode === 'rag'
                  ? '輸入想從知識庫查詢的問題… (Enter 發送，Shift+Enter 換行)'
                  : '與 AI 助手開始對話… (Enter 發送，Shift+Enter 換行)'
              }
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
            />

            <button
              type="button"
              className="chat-input-btn send-btn"
              disabled={!input.trim() || loading}
              onClick={handleSendMessage}
              title="發送訊息"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </section>

      {/* 3. 浮動/抽屜式知識庫文檔管理 */}
      <DocumentDrawer
        isOpen={isDocDrawerOpen}
        onClose={() => setIsDocDrawerOpen(false)}
        documents={documents}
        onUploadFile={handleUploadFileLocal}
        onDeleteDocument={handleDeleteDocumentLocal}
      />
    </div>
  );
};

export default ChatPanel;
