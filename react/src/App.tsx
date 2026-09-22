import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Paperclip,
  Loader2,
  Bot,
  User,
  LayoutGrid,
  Menu,
  ArrowLeft,
  X,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  FileScan,
  MessageSquare,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { activityList, activities } from './mockData';
import OverviewPanel from './components/OverviewPanel';
import BeforePanel from './components/BeforePanel';
import TasksPanel from './components/TasksPanel';
import DecisionsPanel from './components/DecisionsPanel';
import SchedulePanel from './components/SchedulePanel';
import MeetingPanel from './components/MeetingPanel';
import DuringPanel from './components/DuringPanel';
import AfterPanel from './components/AfterPanel';
import SourceRecordPanel from './components/SourceRecordPanel';
// 引入 LLM 聊天面板組件
import ChatPanel from './components/ChatPanel';
// 引入 AI 會議紀錄整理面板組件
import MeetingExtractPanel from './components/MeetingExtractPanel';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

export default function App() {
  // ==========================================
  // 1. 保留原本的 AI 對話與上傳狀態邏輯
  // ==========================================
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', role: 'assistant', content: 'Hello! Please upload a markdown document to start asking questions.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  // 🌟 新增這個狀態：記住目前點擊的是哪個活動（預設為 camp）
  const [currentActivityId, setCurrentActivityId] = useState('camp');
  // 🌟 加上這行：根據目前的 ID，抓出那一包活動資料
  const currentActivity = activities[currentActivityId as keyof typeof activities];
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // ... (保留你原本的 messages, input, loading 等對話狀態) ...

  // ==========================================
  // 新增：畫面切換與側邊欄狀態
  // ==========================================
  // 控制目前顯示的畫面，預設為 'activities' (活動列表)
  const [currentView, setCurrentView] = useState('activities');

  // 控制左側主選單是否開啟 (預設為開啟；收合時完全隱藏並由三線按鈕控制)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // 控制右側 AI 歷史參考抽屜是否開啟
  const [isAiDrawerOpen, setIsAiDrawerOpen] = useState(false);

  // 控制左側邊欄「AI 功能」下拉選單展開/收合 (預設展開)
  const [isAiNavOpen, setIsAiNavOpen] = useState(true);

  // 封裝一個切換畫面的小函式：點擊切換頁面時自動收起側邊欄
  const handleSetView = (view: string) => {
    setCurrentView(view);
    setIsSidebarOpen(false);
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleUpload = () => {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.md,.txt';

    fileInput.onchange = async (e: Event) => {
      const target = e.target as HTMLInputElement;
      if (!target.files || target.files.length === 0) return;

      const file = target.files[0];
      const formData = new FormData();
      formData.append('file', file);

      setUploading(true);
      try {
        const response = await fetch('http://127.0.0.1:8000/upload', {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();

        if (response.ok) {
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            role: 'assistant',
            content: `✅ Successfully uploaded **${file.name}**. ${data.message} (Added ${data.chunks_added} chunks)`
          }]);
        } else {
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            role: 'assistant',
            content: `❌ Failed to upload document: ${data.detail || 'Unknown error'}`
          }]);
        }
      } catch (error: any) {
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'assistant',
          content: `⚠️ Connection error: Make sure the FastAPI backend is running. (${error.message})`
        }]);
      } finally {
        setUploading(false);
      }
    };
    fileInput.click();
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = { id: Date.now().toString(), role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      setTimeout(() => {
        setMessages(prev => [...prev, {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `Echo: You asked "${userMessage.content}". (Query API pending connection)`
        }]);
        setLoading(false);
      }, 1000);
    } catch (error: any) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `❌ Query failed: ${error.message}`
      }]);
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // ==========================================
  // 2. 原型 UI 結構 (已轉換 className、閉合標籤與 inline style)
  // ==========================================
  return (
    <>
      <div className={`app-shell ${!isSidebarOpen ? 'sidebar-closed' : ''}`}>
        <aside className="sidebar" id="primary-sidebar" aria-label="主選單">
          <a className="brand" href="#activities" data-route="activities" aria-label="回到活動首頁" onClick={(e) => { e.preventDefault(); handleSetView('activities'); }}>
            <span className="brand-mark" aria-hidden="true">A</span>
            <span><strong>Archive</strong><small>組織記憶工作台</small></span>
          </a>
          {/* 側邊欄邊緣小半圓箭頭收合/展開按鈕 */}
          <button
            className="sidebar-tab-toggle"
            id="sidebar-toggle"
            type="button"
            aria-label={isSidebarOpen ? "收合側邊欄" : "展開側邊欄"}
            title={isSidebarOpen ? "收合側邊欄" : "展開側邊欄"}
            onClick={() => setIsSidebarOpen(prev => !prev)}
          >
            {isSidebarOpen ? <ChevronLeft size={14} /> : <ChevronRight size={14} />}
          </button>

          <nav className="main-nav">
            <a
              className={`nav-item ${currentView === 'activities' ? 'active' : ''}`}
              href="#activities"
              data-route="activities"
              aria-current={currentView === 'activities' ? 'page' : undefined}
              onClick={(e) => {
                e.preventDefault();
                handleSetView('activities');
              }}
            >
              <span className="nav-icon" aria-hidden="true"><LayoutGrid size={16} /></span>
              <span>活動</span>
            </a>

            {/* AI 功能下拉折疊分組選單 */}
            <div className="nav-group">
              <button
                type="button"
                className={`nav-group-toggle ${['chat', 'extract'].includes(currentView) ? 'active' : ''}`}
                onClick={() => setIsAiNavOpen((prev) => !prev)}
                aria-expanded={isAiNavOpen}
              >
                <div className="nav-group-left">
                  <span className="nav-icon" aria-hidden="true"><Bot size={16} /></span>
                  <span>AI 功能</span>
                </div>
                <span className="nav-group-arrow">
                  {isAiNavOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </span>
              </button>

              {isAiNavOpen && (
                <div className="nav-sub-list">
                  {/* 子選項 1：AI 對話 */}
                  <button
                    type="button"
                    className={`nav-sub-item ${currentView === 'chat' ? 'active' : ''}`}
                    onClick={() => handleSetView('chat')}
                  >
                    <MessageSquare size={14} />
                    <span>AI 對話</span>
                  </button>

                  {/* 子選項 2：會議紀錄整理 */}
                  <button
                    type="button"
                    className={`nav-sub-item ${currentView === 'extract' ? 'active' : ''}`}
                    onClick={() => handleSetView('extract')}
                  >
                    <FileScan size={14} />
                    <span>會議紀錄整理</span>
                  </button>
                </div>
              )}
            </div>
          </nav>

          <div className="sidebar-note">
            <span className="eyebrow">2026 屆</span>
            <strong>資管系學會</strong>
            <span>4 個活動・2 個正在處理</span>
          </div>
          <div className="profile">
            <span className="avatar">林</span>
            <span><strong>林同學</strong><small>活動組</small></span>
          </div>
        </aside>
        <button className="nav-backdrop" id="nav-backdrop" type="button" aria-label="關閉選單" tabIndex={-1} hidden={!isSidebarOpen} onClick={() => setIsSidebarOpen(false)}></button>

        <main className={`main ${['chat', 'extract'].includes(currentView) ? 'chat-mode' : ''}`} id="main-content">
          <section className="page" id="activity-list-view" hidden={currentView !== 'activities'}>
            <div className="page-heading">
              <div>
                <p className="eyebrow">ACTIVITY HUB</p>
                <h1>活動工作台</h1>
                <p>從籌備、執行到檢討，把每一屆的經驗留下來。</p>
              </div>
              <div className="heading-actions">
                <button className="button secondary open-record" type="button">＋ 新增紀錄</button>
                <button className="button primary" id="open-new-activity" type="button">＋ 新增活動</button>
              </div>
            </div>

            <div className="summary-strip" aria-label="活動摘要">
              <article><span>今年活動</span><strong>4</strong><small>四種狀態各 1 個</small></article>
              <article><span>正在處理</span><strong>2</strong><small>1 個準備中・1 個進行中</small></article>
              <article><span>已完成</span><strong>1</strong><small>資管週已進入交接整理</small></article>
              <article className="accent-card"><span>目前執行中</span><strong>制服趴</strong><small>晚間 18:30 結束</small></article>
            </div>

            <div className="surface">
              <div className="toolbar">
                <div className="year-switch" aria-label="選擇年度">
                  <button className="icon-button" type="button" aria-label="上一年">‹</button>
                  <strong>2026 年度</strong>
                  <button className="icon-button" type="button" aria-label="下一年">›</button>
                </div>
                <label className="search-field">
                  <span aria-hidden="true">⌕</span>
                  <input type="search" placeholder="搜尋活動" aria-label="搜尋活動" />
                </label>
              </div>

              <div className="table-wrap">
                <table className="activity-table">
                  <thead><tr><th>活動</th><th>日期</th><th>狀態</th><th>下一步行動</th><th>負責人</th><th><span className="sr-only">操作</span></th></tr></thead>
                  <tbody>
                    {activityList.map((activity) => (
                      <tr
                        key={activity.id}
                        className="activity-row"
                        tabIndex={0}
                        // 🌟 魔法在這裡：點擊時，設定選擇的活動 ID，並切換到工作台畫面！
                        onClick={() => {
                          setCurrentActivityId(activity.id);
                          handleSetView('overview');
                        }}
                      >
                        <td>
                          <span className={`activity-glyph ${activity.glyphColor}`}>{activity.glyph}</span>
                          <span><strong>{activity.name}</strong><small>{activity.type}・{activity.people}</small></span>
                        </td>
                        <td>{activity.date}</td>
                        <td><span className={`status ${activity.statusClass}`}>{activity.status}</span></td>
                        <td><strong>{activity.nextAction}</strong><small>{activity.nextMeetingDate}</small></td>
                        <td><span className="person">{activity.lead.charAt(0)}</span>{activity.lead}</td>
                        <td>›</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          <section className="page activity-workspace" id="activity-workspace" hidden={['activities', 'chat', 'extract'].includes(currentView)}>
            <div className="activity-heading">
              <div className="title-lockup">
                {/* 1. 動態顏色與圖示 */}
                <span className={`activity-glyph ${currentActivity.glyphColor}`}>
                  {currentActivity.glyph}
                </span>
                <div>
                  <p className="eyebrow">2026 年度</p>
                  {/* 2. 動態標題 (加上 color: 'var(--ink)' 確保不會變隱形白字) */}
                  <h1 style={{ color: 'var(--ink)', margin: '0' }}>{currentActivity.name}</h1>
                  {/* 3. 動態狀態、日期與地點 */}
                  <div className="activity-meta">
                    <span className={`status ${currentActivity.statusClass}`}>
                      {currentActivity.status}
                    </span>
                    <span>{currentActivity.fullDate}</span>
                    <span>{currentActivity.location}</span>
                  </div>
                </div>
              </div>
              <button className="button secondary open-record" type="button">＋ 新增紀錄</button>
            </div>

            <nav className="stage-tabs" aria-label="活動階段">
              <button
                className={`stage-tab ${currentView === 'overview' ? 'active' : ''}`}
                type="button"
                onClick={() => setCurrentView('overview')}
              >
                <span>01</span>總覽
              </button>
              <button
                className={`stage-tab ${currentView === 'before' ? 'active' : ''}`}
                type="button"
                onClick={() => setCurrentView('before')}
              >
                <span>02</span>活動前
              </button>
              <button
                className={`stage-tab ${currentView === 'during' ? 'active' : ''}`}
                type="button"
                onClick={() => setCurrentView('during')}
              >
                <span>03</span>活動中
              </button>
              <button
                className={`stage-tab ${currentView === 'after' ? 'active' : ''}`}
                type="button"
                onClick={() => setCurrentView('after')}
              >
                <span>04</span>活動後
              </button>
            </nav>
            <div className="workspace-main">
              <div className="workspace-content">
                <OverviewPanel currentActivity={currentActivity} currentView={currentView} setCurrentView={setCurrentView} />

                {/* --- 這裡略過部分靜態結構，確保你原本的活動前/中/後等區塊不受影響 --- */}
                {/* 所有的 section 保持原樣，因為它們的顯示邏輯在之後掛上 mockData 後會由狀態驅動 */}

                <BeforePanel currentActivity={currentActivity} currentView={currentView} setCurrentView={setCurrentView} />

                <MeetingPanel currentActivity={currentActivity} currentView={currentView} setCurrentView={setCurrentView} />

                <TasksPanel currentActivity={currentActivity} currentView={currentView} />

                <DecisionsPanel currentActivity={currentActivity} currentView={currentView} />

                <SchedulePanel currentActivity={currentActivity} currentView={currentView} />

                <DuringPanel currentView={currentView} setCurrentView={setCurrentView} />

                <AfterPanel currentView={currentView} />

                <SourceRecordPanel currentView={currentView} setCurrentView={setCurrentView} />
              </div>

              <aside className="module-nav" id="activity-module-nav">
                <div className="module-nav-head">
                  <p>活動內容</p>
                  <button className="module-nav-toggle" id="module-nav-toggle" type="button">›</button>
                </div>
                <button className={`module-link ${currentView === 'overview' ? 'active' : ''}`} type="button" onClick={() => setCurrentView('overview')}>
                  <span>⌂</span><em>總覽</em>
                </button>
                <button className={`module-link ${['before', 'meeting', 'tasks', 'decisions', 'schedule'].includes(currentView) ? 'active' : ''}`} type="button" onClick={() => setCurrentView('before')}>
                  <span>◫</span><em>活動前</em>
                </button>
                <div className="module-subnav" hidden={!['before', 'meeting', 'tasks', 'decisions', 'schedule'].includes(currentView)}>
                  <button className={currentView === 'meeting' ? 'active' : ''} type="button" onClick={() => setCurrentView('meeting')}>籌備會議</button>
                  <button className={currentView === 'tasks' ? 'active' : ''} type="button" onClick={() => setCurrentView('tasks')}>待辦事項 <b>5</b></button>
                  <button className={currentView === 'decisions' ? 'active' : ''} type="button" onClick={() => setCurrentView('decisions')}>決策 <b>2</b></button>
                  <button className={currentView === 'schedule' ? 'active' : ''} type="button" onClick={() => setCurrentView('schedule')}>流程規劃</button>
                </div>
                <button className={`module-link ${currentView === 'during' ? 'active' : ''}`} type="button" onClick={() => setCurrentView('during')}>
                  <span>▶</span><em>活動中</em>
                </button>
                <button className={`module-link ${currentView === 'after' ? 'active' : ''}`} type="button" onClick={() => setCurrentView('after')}>
                  <span>◎</span><em>活動後</em>
                </button>
              </aside>
            </div>
          </section>

          {/* 9. LLM 聊天大面板視圖 */}
          {currentView === 'chat' && <ChatPanel />}

          {/* 10. AI 會議紀錄整理視圖 */}
          {currentView === 'extract' && <MeetingExtractPanel />}
        </main>
      </div>

      {/* 7. 綁定 Drawer 半透明背景關閉事件 */}
      <div className="drawer-backdrop" id="drawer-backdrop" hidden={!isAiDrawerOpen} onClick={() => setIsAiDrawerOpen(false)}></div>

      {/* 8. AI 抽屜狀態綁定 */}
      <aside className={`ai-drawer ${isAiDrawerOpen ? 'open' : ''}`} id="ai-drawer" aria-label="AI 歷史參考" aria-hidden={!isAiDrawerOpen}>
        <div className="drawer-head"><div><p className="eyebrow">HISTORY MEMORY</p><h2>歷史參考</h2></div>
          <button className="close-button" type="button" id="close-ai" aria-label="關閉歷史參考" onClick={() => setIsAiDrawerOpen(false)}>×</button></div>

        {/* 對話訊息顯示區 */}
        <div className="messages-container" style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {messages.map(msg => (
            <div key={msg.id} className={`message-wrapper ${msg.role}`} style={{ display: 'flex', gap: '12px' }}>
              <div className="avatar">
                {msg.role === 'assistant' ? <Bot size={20} /> : <User size={20} />}
              </div>
              <div className="message-content" style={{ background: msg.role === 'user' ? '#e3f2fd' : '#f5f5f5', padding: '12px', borderRadius: '8px', flex: 1 }}>
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
            </div>
          ))}
          {loading && (
            <div className="message-wrapper assistant" style={{ display: 'flex', gap: '12px' }}>
              <div className="avatar"><Bot size={20} /></div>
              <div className="message-content loading" style={{ background: '#f5f5f5', padding: '12px', borderRadius: '8px', flex: 1, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Loader2 className="spinner" size={20} />
                <span>Searching documents...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 底部輸入框與上傳按鈕 */}
        <div className="input-area" style={{ padding: '16px', borderTop: '1px solid var(--border)', background: 'white' }}>
          <div className="input-box" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <button
              className="action-btn upload-btn"
              onClick={handleUpload}
              disabled={uploading}
              title="Upload Markdown File"
              style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '8px' }}
            >
              {uploading ? <Loader2 className="spinner" size={20} /> : <Paperclip size={20} />}
            </button>

            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="詢問歷史活動資料…"
              rows={1}
              disabled={loading}
              style={{ flex: 1, padding: '8px', borderRadius: '4px', border: '1px solid var(--border)' }}
            />

            <button
              className="action-btn send-btn"
              onClick={handleSend}
              disabled={!input.trim() || loading}
              style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '8px' }}
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </aside>

      {/* ========================================== */}
      {/* 4. 保留所有原型的 Dialog Modal */}
      {/* ========================================== */}
      <dialog className="modal" id="record-modal">
        <form method="dialog"><div className="modal-head"><div><p className="eyebrow">QUICK ADD</p><h2>新增紀錄</h2></div><button className="close-button" value="cancel" aria-label="關閉">×</button></div>
          <label className="field"><span>選擇所屬活動</span><select id="record-activity-select"><option value="camp">迎新宿營</option><option value="uniform">制服趴</option><option value="bbq">系烤</option><option value="week">資管週</option></select></label>
          <p className="modal-copy">要把哪一種紀錄加入此活動？</p>
          <div className="record-options"><button type="button" data-record="meeting"><span>◫</span><strong>會議</strong><small>建立籌備會議紀錄</small></button><button type="button" data-record="decision"><span>◇</span><strong>決策</strong><small>記錄問題、選項與原因</small></button><button type="button" data-record="task"><span>✓</span><strong>待辦</strong><small>加入負責人與期限</small></button><button type="button" data-record="incident"><span>!</span><strong>臨時紀錄</strong><small>記下活動當天狀況</small></button></div>
        </form>
      </dialog>

      <dialog className="modal small-modal" id="incident-modal">
        <form method="dialog"><div className="modal-head"><div><p className="eyebrow">QUICK NOTE</p><h2>新增臨時紀錄</h2></div><button className="close-button" value="cancel" aria-label="關閉">×</button></div>
          <div className="two-fields"><label className="field"><span>發生時間</span><input id="incident-time" type="time" defaultValue="16:15" /></label><label className="field"><span>處理狀態</span><select id="incident-status"><option>處理中</option><option>已處理</option><option>待追蹤</option></select></label></div>
          <label className="field"><span>發生什麼狀況？</span><textarea rows={4} placeholder="例如：大地遊戲延遲 20 分鐘"></textarea></label>
          <label className="field"><span>對應流程</span><select id="incident-flow"><option>團康活動・10:30</option><option>午餐・12:00</option><option>大地遊戲・13:30</option></select></label>
          <div className="two-fields"><label className="field"><span>處理人</span><input id="incident-handler" type="text" placeholder="例如：陳怡安" /></label><label className="field"><span>處理方式</span><input id="incident-action" type="text" placeholder="例如：調整下一段開始時間" /></label></div>
          <div className="modal-actions"><button className="button secondary" value="cancel">取消</button><button className="button primary" id="save-incident" value="default">儲存紀錄</button></div>
        </form>
      </dialog>

      <dialog className="modal small-modal" id="activity-modal">
        <form method="dialog"><div className="modal-head"><div><p className="eyebrow">NEW ACTIVITY</p><h2>新增活動</h2></div><button className="close-button" value="cancel" aria-label="關閉">×</button></div>
          <label className="field"><span>活動名稱</span><input type="text" placeholder="例如：新生茶會" /></label>
          <div className="two-fields"><label className="field"><span>年度</span><select><option>2026</option><option>2027</option></select></label><label className="field"><span>活動類型</span><select><option>大型活動</option><option>校內活動</option><option>聯誼活動</option><option>其他</option></select></label></div>
          <div className="two-fields"><label className="field"><span>活動日期</span><input type="date" defaultValue="2026-11-01" /></label><label className="field"><span>主要負責人</span><input type="text" placeholder="輸入姓名" /></label></div>
          <div className="modal-actions"><button className="button secondary" value="cancel">取消</button><button className="button primary" id="save-activity" value="default">建立活動</button></div>
        </form>
      </dialog>

      <dialog className="modal small-modal" id="meeting-upload-modal">
        <form method="dialog" id="meeting-upload-form"><div className="modal-head"><div><p className="eyebrow">MEETING FILE</p><h2>上傳會議紀錄</h2></div><button className="close-button" type="button" aria-label="關閉">×</button></div>
          <p className="modal-copy">選擇這份紀錄所屬的會議；prototype 只顯示操作結果，不會保存檔案。</p>
          <label className="field"><span>所屬會議</span><select id="meeting-upload-target"></select></label>
          <label className="upload-field"><input id="meeting-upload-file" type="file" accept=".txt,.md,.doc,.docx,.pdf" /><span>選擇會議紀錄檔案</span><small>支援 TXT、Markdown、Word、PDF</small></label>
          <div className="modal-actions"><button className="button secondary" type="button" value="cancel">取消</button><button className="button primary" type="submit">使用此檔案</button></div>
        </form>
      </dialog>

      <dialog className="modal small-modal" id="action-modal">
        <form method="dialog" id="action-form"><div className="modal-head"><div><p className="eyebrow" id="action-eyebrow">EDIT</p><h2 id="action-title">編輯資料</h2></div><button className="close-button" value="cancel" aria-label="關閉">×</button></div>
          <div id="action-fields"></div>
          <div className="modal-actions"><button className="button secondary" value="cancel">取消</button><button className="button primary" id="action-submit" value="default">完成</button></div>
        </form>
      </dialog>

      <dialog className="modal" id="handover-modal">
        <form method="dialog"><div className="modal-head"><div><p className="eyebrow">AI HANDOVER</p><h2>交接摘要預覽</h2></div><button className="close-button" value="cancel" aria-label="關閉">×</button></div>
          <div className="handover-content" style={{ maxHeight: '60vh', overflowY: 'auto', paddingRight: '12px', marginTop: '16px' }}>
            <h3 style={{ marginBottom: '8px', fontSize: '16px' }}>今年做得好的地方</h3>
            <p style={{ marginBottom: '16px', lineHeight: '1.6' }}>1. 單向環形動線有效改善了中午尖峰時段的回堵。<br />2. 熱門攤位使用兌換券顯著減少了找零錯誤。</p>
            <hr style={{ margin: '16px 0', border: '0', borderTop: '1px solid var(--border)' }} />
            <h3 style={{ marginBottom: '8px', fontSize: '16px' }}>發生的重要問題</h3>
            <p style={{ marginBottom: '16px', lineHeight: '1.6' }}>第一天中午入口處因飲料攤與兌換券櫃台過近，導致回堵約 8 分鐘。</p>
            <hr style={{ margin: '16px 0', border: '0', borderTop: '1px solid var(--border)' }} />
            <h3 style={{ marginBottom: '8px', fontSize: '16px' }}>關鍵決策與執行結果</h3>
            <ul style={{ marginBottom: '16px', paddingLeft: '20px', lineHeight: '1.6' }}>
              <li><strong>攤位改採單向環形動線</strong>：成效良好，值得沿用。</li>
              <li><strong>部分攤位改用兌換券</strong>：縮短了結帳時間，值得沿用。</li>
            </ul>
            <hr style={{ margin: '16px 0', border: '0', borderTop: '1px solid var(--border)' }} />
            <h3 style={{ marginBottom: '8px', fontSize: '16px' }}>下次建議</h3>
            <p style={{ marginBottom: '16px', lineHeight: '1.6' }}>明年建議保留環形動線與兌換券制度，但務必將兌換券櫃台移至入口外側，避免與熱門攤位人潮交叉。</p>
          </div>
          <div className="modal-actions"><button className="button secondary" value="cancel">關閉預覽</button><button className="button primary" type="button" data-toast="交接摘要已匯出">匯出為 PDF</button></div>
        </form>
      </dialog>

      <div className="toast" id="toast" role="status" aria-live="polite"></div>
    </>
  );
}