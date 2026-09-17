import React from 'react';
import './DuringPanel.css';

export default function DuringPanel({ currentView, setCurrentView }: any) {
  return (
    <section className={`view-panel ${currentView === 'during' ? 'active' : ''}`} data-panel="during">
      <div className="section-heading">
        <div><p className="eyebrow">DURING EVENT</p><h2>活動中紀錄</h2><p>集中記下活動期間發生的狀況，之後可帶入活動檢討。</p></div>
        <button className="button primary" type="button">＋ 新增紀錄</button>
      </div>
      <div className="during-summary">
        <article><span>活動狀態</span><strong className="during-status">進行中</strong></article>
        <article><span>活動中紀錄</span><strong className="during-count">0 筆</strong></article>
        <article><span>原訂流程</span><button className="text-button" type="button" onClick={() => setCurrentView('schedule')}>查看活動流程 ›</button></article>
      </div>
      <div className="section-heading compact subsection-heading">
        <div><p className="eyebrow">PREPARED FLOW</p><h3>活動流程與執行資料</h3><p>直接查看活動前整理好的負責人、器材與相關附件。</p></div>
      </div>
      <div className="execution-flow-list"></div>
      <div className="section-heading compact subsection-heading">
        <div><p className="eyebrow">EVENT NOTES</p><h3>活動中紀錄</h3><p>新增的狀況會保留對應流程，供活動後檢討使用。</p></div>
      </div>
      <article className="info-card execution-log">
        <div className="card-title"><h3>執行紀錄</h3><span className="updated">依時間排序</span></div>
        <div className="record-timeline"></div>
      </article>
    </section>
  );
}