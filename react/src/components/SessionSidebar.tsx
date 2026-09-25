import React from 'react';
import { Plus, MessageSquare, Trash2 } from 'lucide-react';
import './SessionSidebar.css';

/**
 * 會話項目資料介面 (本機狀態使用)
 */
export interface SessionItem {
  id: string;
  title: string;
  createdAt: string;
}

interface SessionSidebarProps {
  // 目前所有會話清單
  sessions: SessionItem[];
  // 當前選中的會話 ID
  activeSessionId: string | null;
  // 切換會話的回呼函式
  onSelectSession: (id: string) => void;
  // 建立新會話的回呼函式
  onCreateSession: () => void;
  // 刪除會話的回呼函式
  onDeleteSession: (id: string, e: React.MouseEvent) => void;
}

/**
 * 會話側邊欄組件 (Session Sidebar)
 * 負責展示使用者歷史會話、提供新增與切換會話功能
 */
export const SessionSidebar: React.FC<SessionSidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
}) => {
  return (
    <aside className="chat-session-sidebar" aria-label="會話列表">
      {/* 頂部操作區：新增對話按鈕 */}
      <div className="chat-session-header">
        <button
          type="button"
          className="button primary new-chat-btn"
          onClick={onCreateSession}
          aria-label="新增對話"
        >
          <Plus size={16} />
          <span>新對話</span>
        </button>
      </div>

      {/* 會話歷史清單展示區 */}
      <div className="chat-session-list">
        {sessions.length === 0 ? (
          // 極簡空狀態：尚無歷史會話
          <div className="chat-session-empty">
            <MessageSquare size={20} className="empty-icon" />
            <p>尚無歷史對話</p>
            <small>點擊上方按鈕建立新對話</small>
          </div>
        ) : (
          // 渲染會話項目列表
          sessions.map((session) => {
            const isActive = session.id === activeSessionId;
            return (
              <div
                key={session.id}
                className={`chat-session-item ${isActive ? 'active' : ''}`}
                onClick={() => onSelectSession(session.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    onSelectSession(session.id);
                  }
                }}
              >
                <div className="session-item-icon">
                  <MessageSquare size={16} />
                </div>
                <div className="session-item-info">
                  <strong className="session-item-title">{session.title}</strong>
                  <span className="session-item-time">{session.createdAt}</span>
                </div>
                {/* 刪除按鈕 (懸停時顯示) */}
                <button
                  type="button"
                  className="session-delete-btn"
                  title="刪除對話"
                  onClick={(e) => onDeleteSession(session.id, e)}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
};

export default SessionSidebar;
