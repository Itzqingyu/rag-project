import React from 'react';

export default function AfterPanel({ currentView }: any) {
  return (
    <section className={`view-panel ${currentView === 'after' ? 'active' : ''}`} data-panel="after">
      <div className="section-heading">
        <div><p className="eyebrow">AFTER EVENT</p><h2>成果與檢討</h2><p>沿用活動流程補上實際結果，形成下一屆可用的經驗。</p></div>
        <span className="status finished">已完成</span>
      </div>
      <div className="after-summary">
        <article><span>流程檢討</span><strong>12 / 18</strong><small>已完成填寫</small></article>
        <article><span>決策結果</span><strong>7 / 12</strong><small>還有 5 筆待補</small></article>
        <article><span>臨時紀錄</span><strong>4</strong><small>已帶入相關流程</small></article>
      </div>
      <div className="section-heading compact subsection-heading">
        <div><p className="eyebrow">FLOW RESULTS</p><h3>流程結果</h3><p>在原本流程上補充實際時間、問題、原因與下次建議。</p></div>
      </div>
      <div className="flow-result-list"></div>
      <div className="section-heading compact subsection-heading">
        <div><p className="eyebrow">DECISION RESULTS</p><h3>決策執行結果</h3><p>確認每筆決策是否有效，補齊下一屆需要知道的結果。</p></div>
      </div>
      <div className="decision-result-list"></div>
      <article className="handover-card enriched-handover">
        <div>
          <p className="eyebrow">AI 年度交接摘要・假資料</p>
          <h3>2026 迎新宿營交接重點</h3>
          <p>已根據目前填寫內容整理重大決策、問題與下次建議。</p>
          <div className="handover-metrics">
            <span><b>5</b>重大決策</span><span><b>8</b>主要問題</span><span><b>3</b>值得沿用</span><span><b>6</b>需要改善</span>
          </div>
        </div>
        <button className="button primary" type="button">預覽摘要</button>
      </article>
    </section>
  );
}