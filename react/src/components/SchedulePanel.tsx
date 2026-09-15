import React, { useState } from 'react';

export default function SchedulePanel({ currentActivity, currentView }: any) {
  // 🌟 魔法狀態：用來控制目前顯示的是 Day 1 還是 Day 2 (預設為 1)
  const [activeDay, setActiveDay] = useState(1);

  // 為了展示方便，我們直接在元件內準備兩天的流程陣列，讓程式碼更乾淨
  const day1Schedule = [
    { id: 1, time: '08:00', category: 'staff', categoryName: '工作人員', title: '工作人員集合', desc: '大廳・負責人：陳怡安', tags: ['📦 報到物資', '👥 32 位工作人員'] },
    { id: 2, time: '09:00', category: 'checkin', categoryName: '報到', title: '新生報到', desc: '一樓大廳・負責人：吳品妤', tags: ['📄 報到名單', '📍 動線圖'] },
    { id: 3, time: '10:00', category: 'ceremony', categoryName: '開幕', title: '開幕式', desc: '大禮堂・主持人：黃冠宇', tags: ['🎤 音響', '📑 主持稿'] },
    { id: 4, time: '10:30', category: 'activity', categoryName: '活動', title: '團康活動', desc: '大禮堂・關主：活動組', tags: ['📦 遊戲器材', '⏱ 90 分鐘'] },
    { id: 5, time: '12:00', category: 'meal', categoryName: '用餐', title: '午餐', desc: '餐廳・負責人：總務組', tags: ['🍱 126 份餐盒'] }
  ];

  const day2Schedule = [
    { id: 6, time: '07:30', category: 'meal', categoryName: '用餐', title: '早餐', desc: '餐廳', tags: [] },
    { id: 7, time: '09:00', category: 'activity', categoryName: '活動', title: '大地遊戲', desc: '戶外草皮', tags: ['💧 雨備方案確認'] },
    { id: 8, time: '12:00', category: 'ceremony', categoryName: '閉幕', title: '結業式與頒獎', desc: '大禮堂', tags: ['🏆 獎品'] },
  ];

  // 根據選中的天數，決定要丟給畫面哪個陣列
  const currentSchedule = activeDay === 1 ? day1Schedule : day2Schedule;

  return (
    <section className={`view-panel ${currentView === 'schedule' ? 'active' : ''}`} data-panel="schedule">
      <div className="section-heading">
        <div>
          <p className="eyebrow">SCHEDULE</p>
          <h2>活動流程規劃</h2>
          <p>活動前先完成細節，活動當天直接查看。</p>
        </div>
        <button className="button primary" type="button">＋ 新增流程</button>
      </div>
      
      {/* 🔘 天數切換按鈕 */}
      <div className="day-switch">
        <button className={activeDay === 1 ? 'active' : ''} type="button" onClick={() => setActiveDay(1)}>
          Day 1・第一天
        </button>
        <button className={activeDay === 2 ? 'active' : ''} type="button" onClick={() => setActiveDay(2)}>
          Day 2・第二天
        </button>
      </div>
      
      {/* ⏳ 時間軸 */}
      <div className="timeline">
        {currentSchedule.map(item => (
          <article key={item.id}>
            <time>{item.time}</time>
            <i></i>
            <div>
              <span className={`category ${item.category}`}>{item.categoryName}</span>
              <h3>{item.title}</h3>
              <p>{item.desc}</p>
              {/* 如果有 tag 才渲染這個 div */}
              {item.tags.length > 0 && (
                <div className="detail-tags">
                  {item.tags.map((tag, idx) => (
                    <span key={idx}>{tag}</span>
                  ))}
                </div>
              )}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}