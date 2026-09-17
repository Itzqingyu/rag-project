import React from 'react';
import './OverviewPanel.css';

// 定義這個元件需要接收的資料
export default function OverviewPanel({ currentActivity, currentView, setCurrentView }: any) {
  return (
    <section className={`view-panel ${currentView === 'overview' ? 'active' : ''}`} data-panel="overview">
      <div className="section-heading compact">
        <div><p className="eyebrow">OVERVIEW</p><h2>活動總覽</h2></div>
        <span className="updated">最後更新：今天 14:20</span>
      </div>

      {/* 活動進度 */}
      <div className="lifecycle-card">
        <div className="lifecycle-head">
          <strong>活動進度</strong>
          <span>準備完成度 {currentActivity.progress}%</span>
        </div>
        <div className="lifecycle-track" aria-label={`活動進度：${currentActivity.status}`}>
          <div className={`life-step ${currentActivity.status !== '未開始' ? 'done' : 'current'}`}>
            <i>{currentActivity.status !== '未開始' ? '✓' : '1'}</i><span>建立活動</span>
          </div>
          <div className={`life-line ${currentActivity.status !== '未開始' ? 'done' : ''}`}></div>
          <div className={`life-step ${['進行中', '已完成'].includes(currentActivity.status) ? 'done' : currentActivity.status === '準備中' ? 'current' : ''}`}>
            <i>{['進行中', '已完成'].includes(currentActivity.status) ? '✓' : '2'}</i><span>準備中</span>
          </div>
          <div className={`life-line ${['進行中', '已完成'].includes(currentActivity.status) ? 'done' : ''}`}></div>
          <div className={`life-step ${currentActivity.status === '已完成' ? 'done' : currentActivity.status === '進行中' ? 'current' : ''}`}>
            <i>{currentActivity.status === '已完成' ? '✓' : '3'}</i><span>活動執行</span>
          </div>
          <div className={`life-line ${currentActivity.status === '已完成' ? 'done' : ''}`}></div>
          <div className={`life-step ${currentActivity.status === '已完成' ? 'current' : ''}`}>
            <i>4</i><span>成果檢討</span>
          </div>
        </div>
      </div>

      <div className="info-grid">
        {/* 基本資訊 */}
        <article className="info-card wide">
          <div className="card-title">
            <h3>基本資訊</h3>
            <button className="text-button" type="button">編輯</button>
          </div>
          <dl className="facts">
            <div><dt>活動日期</dt><dd>{currentActivity.fullDate}</dd></div>
            <div><dt>地點</dt><dd>{currentActivity.location}</dd></div>
            <div><dt>總召</dt><dd>{currentActivity.lead}</dd></div>
            <div><dt>預計人數</dt><dd>{currentActivity.people}</dd></div>
            <div><dt>目前預算</dt><dd>{currentActivity.budget}</dd></div>
            <div>
              <dt>下一場會議</dt>
              <dd>
                <button className="inline-link" type="button" onClick={() => setCurrentView('meeting')}>
                  {currentActivity.nextMeetingDate || '無'}
                </button>
              </dd>
            </div>
            <div><dt>下一步行動</dt><dd>{currentActivity.nextAction}</dd></div>
          </dl>
        </article>

        {/* 待辦狀況圓環 */}
        <article className="info-card progress-card">
          <div className="card-title">
            <h3>待辦狀況</h3>
            <button className="text-button" type="button" onClick={() => setCurrentView('tasks')}>查看全部</button>
          </div>
          <div className="ring" style={{ "--progress": currentActivity.taskTotals?.total ? Math.round((currentActivity.taskTotals.done / currentActivity.taskTotals.total) * 100) : 0 } as React.CSSProperties}>
            <span>
              <b>{currentActivity.taskTotals?.done || 0}</b>
              <small>/ {currentActivity.taskTotals?.total || 0} 完成</small>
            </span>
          </div>
          <div className="mini-legend">
            <span><i className="dot done"></i>已完成 {currentActivity.taskTotals?.done || 0}</span>
            <span><i className="dot pending"></i>未完成 {(currentActivity.taskTotals?.total || 0) - (currentActivity.taskTotals?.done || 0)}</span>
          </div>
        </article>
      </div>

      <div className="info-grid equal">
        {/* 最近待辦 */}
        <article className="info-card">
          <div className="card-title">
            <h3>最近待辦</h3>
            <button className="text-button" type="button" onClick={() => setCurrentView('tasks')}>
              {currentActivity.tasks ? currentActivity.tasks.filter((t:any) => t.status !== 'done').length : 0} 筆未完成
            </button>
          </div>
          <ul className="task-preview">
            {currentActivity.tasks && currentActivity.tasks.filter((t:any) => t.status !== 'done').length > 0 ? (
              currentActivity.tasks.filter((t:any) => t.status !== 'done').slice(0, 3).map((task:any) => (
                <li key={task.id}>
                  <button className="check" type="button"></button>
                  <span>
                    <strong>{task.title}</strong>
                    <small>{task.owner}・{task.due} 到期</small>
                  </span>
                  {task.priority === '高' && <em className="urgent">優先處理</em>}
                </li>
              ))
            ) : (
              <li className="empty-inline">
                <span><strong>目前沒有未完成待辦</strong><small>太棒了！所有事情都在軌道上</small></span>
              </li>
            )}
          </ul>
        </article>

        {/* 重要決策 */}
        <article className="info-card">
          <div className="card-title">
            <h3>重要決策</h3>
            <button className="text-button" type="button" onClick={() => setCurrentView('decisions')}>查看全部</button>
          </div>
          <ul className="decision-preview">
            {currentActivity.decisions && currentActivity.decisions.length > 0 ? (
              currentActivity.decisions.slice(0, 3).map((decision:any) => (
                <li key={decision.id}>
                  <span className={`decision-state ${decision.state === '已確認' ? 'confirmed' : 'review'}`}>
                    {decision.state}
                  </span>
                  <div>
                    <strong>{decision.title}</strong>
                    <small>來源：{decision.source}</small>
                  </div>
                </li>
              ))
            ) : (
              <li className="empty-inline">
                <span><strong>目前沒有重要決策</strong><small>會議中的重大決議將會整理在這裡</small></span>
              </li>
            )}
          </ul>
        </article>
      </div>

      <article className="memory-banner">
        <div className="memory-icon">✦</div>
        <div>
          <p className="eyebrow">AI 歷史提醒・假資料</p>
          <h3>過去三年最常發生的問題是交通延誤</h3>
          <p>2025 年遊覽車晚到 25 分鐘；2024 年因集合資訊不清，延後 15 分鐘出發。</p>
        </div>
        <button className="button memory-open" type="button">查看歷史案例</button>
      </article>
    </section>
  );
}