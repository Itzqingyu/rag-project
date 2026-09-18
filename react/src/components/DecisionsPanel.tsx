import React, { useState, useEffect } from 'react';
import './DecisionsPanel.css';

export default function DecisionsPanel({ currentActivity, currentView }: any) {
  // 取得這個活動的所有決策 (如果沒有就給空陣列)
  const decisions = currentActivity.decisions || [];
  
  // 🌟 魔法狀態：記住目前選中的是哪一筆決策的 ID (預設選中第一筆)
  const [selectedId, setSelectedId] = useState(decisions.length > 0 ? decisions[0].id : null);

  // 當切換活動時，如果新活動有決策，自動選中它的第一筆
  useEffect(() => {
    if (decisions.length > 0) {
      setSelectedId(decisions[0].id);
    } else {
      setSelectedId(null);
    }
  }, [currentActivity]);

  // 找出目前選中的那筆決策完整資料，準備給右邊的畫面用
  const activeDecision = decisions.find((d: any) => d.id === selectedId);

  return (
    <section className={`view-panel ${currentView === 'decisions' ? 'active' : ''}`} data-panel="decisions">
      <div className="section-heading">
        <div>
          <p className="eyebrow">DECISIONS</p>
          <h2>決策紀錄</h2>
          <p>記下做了什麼，也記下當時為什麼這樣做。</p>
        </div>
        <button className="button primary" type="button">＋ 新增決策</button>
      </div>

      {/* 判斷：如果有決策資料才顯示左右版面，否則顯示空狀態 */}
      {decisions.length > 0 ? (
        <div className="decision-layout">
          
          {/* 👈 左側：決策列表 */}
          <div className="decision-list" role="listbox" aria-label="決策列表">
            {decisions.map((decision: any) => (
              <button
                key={decision.id}
                // 如果這顆按鈕的 id 剛好是我們選中的 id，就加上 active class 讓它反白！
                className={`decision-list-item ${selectedId === decision.id ? 'active' : ''}`}
                type="button"
                onClick={() => setSelectedId(decision.id)}
              >
                <span className={`decision-state ${decision.state === '已確認' ? 'confirmed' : 'review'}`}>
                  {decision.state}
                </span>
                <strong>{decision.title}</strong>
                <small>{decision.date}</small>
              </button>
            ))}
          </div>

          {/* 👉 右側：決策詳細內容 */}
          {activeDecision && (
            <article className="decision-detail" id="decision-detail">
              <div className="decision-detail-head">
                <div>
                  <span className={`decision-state ${activeDecision.state === '已確認' ? 'confirmed' : 'review'}`}>
                    {activeDecision.state}
                  </span>
                  <h3>{activeDecision.title}</h3>
                </div>
                <button className="text-button" type="button">編輯</button>
              </div>
              
              <div className="decision-section">
                <span>當時考慮的選項</span>
                <ol>
                  {/* 動態列出所有選項 */}
                  {activeDecision.options.map((opt: string, index: number) => (
                    <li key={index}>{opt}</li>
                  ))}
                </ol>
              </div>
              
              <div className="decision-answer">
                <span>最終決定</span>
                <strong>{activeDecision.answer}</strong>
                <p>{activeDecision.description}</p>
              </div>
              
              <div className="decision-meta">
                <div><span>決定原因</span><strong>{activeDecision.reason}</strong></div>
                <div><span>執行狀況</span><strong>{activeDecision.execution}</strong></div>
              </div>
              
              <button className="source-link" type="button">
                <span>⌕</span>
                <div><strong>來源：{activeDecision.source}</strong><small>查看原文</small></div>
                <b>›</b>
              </button>
              
              {/* 如果有歷史相似案例，才把它顯示出來 */}
              {activeDecision.history && (
                <div className="historical-match">
                  <p className="eyebrow">✦ 歷史相似案例・假資料</p>
                  <strong>{activeDecision.history}</strong>
                  <button className="text-button memory-open" type="button">查看完整案例</button>
                </div>
              )}
            </article>
          )}
        </div>
      ) : (
        // 🈳 當完全沒有決策資料時，顯示這個畫面
        <div style={{ textAlign: 'center', padding: '64px 24px', backgroundColor: 'var(--surface)', borderRadius: '12px' }}>
          <h3>目前沒有決策紀錄</h3>
          <p style={{ color: 'var(--ink-light)', marginTop: '8px' }}>籌備過程中的重要選擇，都會保存在這裡供日後參考。</p>
        </div>
      )}
    </section>
  );
}