import React from 'react';

export default function BeforePanel({ currentActivity, currentView, setCurrentView }: any) {
  // 自動幫我們算好「未完成的待辦」有幾筆
  const pendingTasksCount = currentActivity.tasks ? currentActivity.tasks.filter((t:any) => t.status !== 'done').length : 0;
  // 自動幫我們算好「待確認的決策」有幾筆
  const pendingDecisionsCount = currentActivity.decisions ? currentActivity.decisions.filter((d:any) => d.state === '待確認').length : 0;

  return (
    <section className={`view-panel ${currentView === 'before' ? 'active' : ''}`} data-panel="before">
      <div className="section-heading">
        <div><p className="eyebrow">BEFORE EVENT</p><h2>活動前</h2><p>集中查看籌備進度與尚未確認的事項。</p></div>
      </div>
      
      {/* 📊 頂部數據區 */}
      <div className="prep-overview">
        <article className="prep-score">
          <span>準備完成度</span>
          <strong>{currentActivity.progress}%</strong>
          <div className="bar"><i style={{ width: `${currentActivity.progress}%` }}></i></div>
          <small>{currentActivity.prepNote}</small>
        </article>
        <article>
          <span>下一場會議</span>
          <strong>{currentActivity.nextMeeting || '無'}</strong>
          <small>{currentActivity.nextMeetingDate}</small>
        </article>
        <article>
          <span>未完成待辦</span>
          <strong>{pendingTasksCount}</strong>
          <small>請至任務追蹤查看</small>
        </article>
        <article>
          <span>待確認決策</span>
          <strong>{pendingDecisionsCount}</strong>
          <small>請盡快確認</small>
        </article>
      </div>

      {/* 🎛️ 四大模組入口 */}
      <div className="module-grid">
        <button className="module-card featured" type="button" onClick={() => setCurrentView('meeting')}>
          <span className="module-number">01</span>
          <div>
            <p>下一場會議・{currentActivity.nextMeetingDate || '無'}</p>
            <h3>{currentActivity.nextMeeting || '暫無會議'}</h3>
          </div>
          <b>開啟 ›</b>
        </button>
        <button className="module-card" type="button" onClick={() => setCurrentView('tasks')}>
          <span className="module-number">02</span>
          <div>
            <p>任務追蹤</p>
            <h3>待辦事項</h3>
            <small>{currentActivity.taskTotals?.total || 0} 筆待辦・完成 {currentActivity.taskTotals?.done || 0} 筆</small>
          </div>
          <b>查看 ›</b>
        </button>
        <button className="module-card" type="button" onClick={() => setCurrentView('decisions')}>
          <span className="module-number">03</span>
          <div>
            <p>保存選擇原因</p>
            <h3>決策紀錄</h3>
            <small>{currentActivity.decisions?.length || 0} 筆決策・{pendingDecisionsCount} 筆待確認</small>
          </div>
          <b>查看 ›</b>
        </button>
        <button className="module-card" type="button" onClick={() => setCurrentView('schedule')}>
          <span className="module-number">04</span>
          <div><p>兩天活動</p><h3>流程規劃</h3><small>查看詳細時程</small></div>
          <b>查看 ›</b>
        </button>
      </div>

      {/* 🚨 警報面板 (如果有資料才顯示) */}
      {currentActivity.alert && currentActivity.alert.length > 0 && (
        <div className="alert-panel">
          <span>!</span>
          <div>
            <strong>{currentActivity.alert[0]}</strong>
            <p>{currentActivity.alert[1]}</p>
          </div>
          <button className="button secondary" type="button">加入會議</button>
        </div>
      )}
    </section>
  );
}