import React, { useState } from 'react';

export default function MeetingPanel({ currentActivity, currentView, setCurrentView }: any) {
  // 🌟 魔法狀態：用來記錄「原文」是否為展開狀態 (預設為 false 隱藏)
  const [isTranscriptOpen, setIsTranscriptOpen] = useState(false);

  return (
    <section className={`view-panel ${currentView === 'meeting' ? 'active' : ''}`} data-panel="meeting">
      
      {/* 🔙 頂部工具列 */}
      <div className="detail-toolbar">
        <button className="back-link" type="button" onClick={() => setCurrentView('before')}>
          ← 回到活動前
        </button>
        <div>
          <button className="button secondary" type="button">↑ 上傳會議紀錄</button>
          <button className="button secondary" type="button" style={{ margin: '0 8px' }}>編輯會議</button>
          <button className="button primary" type="button">儲存</button>
        </div>
      </div>
      
      {/* 📅 會議標題區 */}
      <div className="section-heading" style={{ marginTop: '24px' }}>
        <div>
          <p className="eyebrow">MEETING</p>
          <h2>{currentActivity.nextMeeting || '三籌會議'}</h2>
          <p>{currentActivity.nextMeetingDate ? `2026 年 ${currentActivity.nextMeetingDate}` : '日期未定'}・19:00–21:00・系辦會議室</p>
        </div>
        <span className="status preparing">即將進行</span>
      </div>
      
      <div className="attendees">
        <span>參與人員</span>
        <div className="avatar-stack">
          <i>陳</i><i>黃</i><i>吳</i><i>許</i><i>＋8</i>
        </div>
      </div>
      
      {/* 🤖 AI 整理摘要區 */}
      <article className="ai-summary-block">
        <div className="card-title">
          <div>
            <p className="eyebrow">AI 整理結果・假資料</p>
            <h3>會議紀錄已整理為 4 種資料</h3>
          </div>
          <span className="source-chip">來源：三籌紀錄.md</span>
        </div>
        <div className="extraction-stats">
          <button type="button" onClick={() => setCurrentView('decisions')}><b>3</b><span>決策</span></button>
          <button type="button" onClick={() => setCurrentView('tasks')}><b>7</b><span>待辦</span></button>
          <button type="button"><b>5</b><span>工作分配</span></button>
          <button type="button" onClick={() => setCurrentView('schedule')}><b>2</b><span>流程變更</span></button>
        </div>
      </article>
      
      <div className="meeting-grid">
        {/* 待確認決策卡片 */}
        <article className="info-card">
          <div className="card-title">
            <h3>待確認決策</h3>
            <div>
              <span className="count-badge">2</span>
              <button className="text-button" style={{ marginLeft: '8px' }} type="button">＋ 新增</button>
            </div>
          </div>
          <div className="proposal-card">
            <p>問題</p>
            <strong>遊覽車發車時間是否提前？</strong>
            <p>AI 建議更新</p>
            <div className="change-row">
              <span>07:30</span><b>→</b><span className="new-value">07:00</span>
            </div>
            <small>原因：避開週末上山車潮</small>
            <div className="proposal-actions">
              <button type="button">忽略</button>
              <button type="button">確認</button>
            </div>
          </div>
        </article>

        {/* 本次待辦卡片 */}
        <article className="info-card">
          <div className="card-title">
            <h3>本次待辦</h3>
            <div>
              <button className="text-button" type="button" style={{ marginRight: '8px' }}>＋ 新增</button>
              <button className="text-button" type="button" onClick={() => setCurrentView('tasks')}>查看全部</button>
            </div>
          </div>
          <ul className="simple-list">
            <li><span>確認遊覽車發車時間</span><small>陳怡安・9/16</small></li>
            <li><span>向場地方確認室內音響</span><small>黃冠宇・9/20</small></li>
            <li><span>更新家長通知單</span><small>吳品妤・9/22</small></li>
          </ul>
        </article>
      </div>
      
      {/* 📄 會議紀錄原文 (展開/收起功能) */}
      <article className="transcript">
        <div className="card-title">
          <h3>會議紀錄原文</h3>
          {/* 🌟 點擊按鈕切換 isTranscriptOpen 的狀態 */}
          <button 
            className="text-button transcript-toggle" 
            type="button"
            onClick={() => setIsTranscriptOpen(!isTranscriptOpen)}
          >
            {isTranscriptOpen ? '收起原文' : '展開原文'}
          </button>
        </div>
        {/* 🌟 根據狀態決定要不要加上 hidden 屬性 */}
        <div className="transcript-body" hidden={!isTranscriptOpen}>
          <p>交通組回報週末上山車流量較大，建議發車時間由 07:30 提前至 07:00。總召請交通組在 9/16 前向遊覽車公司確認……</p>
          <mark>晚會若遇雨，改至室內禮堂；音響組需提前一天完成測試。</mark>
          <p>保險資料目前尚未確認，請於下次會議前補齊。</p>
        </div>
      </article>

    </section>
  );
}