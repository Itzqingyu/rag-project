import React, { useState } from 'react';

export default function TasksPanel({ currentActivity, currentView }: any) {
  // 🌟 新魔法：用來記住現在點擊了哪個篩選按鈕（預設顯示 'all' 全部）
  const [filter, setFilter] = useState('all');

  // 防呆機制：如果這個活動還沒有 tasks，就給它一個空陣列
  const tasks = currentActivity.tasks || [];
  
  // 計算上方按鈕的數字
  const totalCount = tasks.length;
  const pendingCount = tasks.filter((t:any) => t.status !== 'done').length;
  const doneCount = tasks.filter((t:any) => t.status === 'done').length;

  // 幫任務分門別類，對應到看板的三個直排
  const todoTasks = tasks.filter((t:any) => t.status === 'todo');
  const doingTasks = tasks.filter((t:any) => t.status === 'doing');
  const doneTasks = tasks.filter((t:any) => t.status === 'done');

  // 把中文的優先度轉換成 CSS 認得的 class
  const getPriorityClass = (priority: string) => {
    if (priority === '高') return 'high';
    if (priority === '中') return 'medium';
    return 'low';
  };

  return (
    <section className={`view-panel ${currentView === 'tasks' ? 'active' : ''}`} data-panel="tasks">
      <div className="section-heading">
        <div>
          <p className="eyebrow">TASKS</p>
          <h2>待辦事項</h2>
          <p>同一筆待辦保留原始會議來源。</p>
        </div>
        <button className="button primary" type="button">＋ 新增待辦</button>
      </div>
      
      {/* 🔘 篩選按鈕列 */}
      <div className="filter-row">
        <button className={`filter ${filter === 'all' ? 'active' : ''}`} type="button" onClick={() => setFilter('all')}>
          全部 {totalCount}
        </button>
        <button className={`filter ${filter === 'pending' ? 'active' : ''}`} type="button" onClick={() => setFilter('pending')}>
          未完成 {pendingCount}
        </button>
        <button className={`filter ${filter === 'done' ? 'active' : ''}`} type="button" onClick={() => setFilter('done')}>
          已完成 {doneCount}
        </button>
      </div>
      
      <div className="task-board">
        {/* 📋 第一行：待處理 */}
        {(filter === 'all' || filter === 'pending') && (
          <article className="task-column">
            <div className="column-title"><span>待處理</span><b>{todoTasks.length}</b></div>
            {todoTasks.map((task:any) => (
              <div className="task-card" data-status="pending" key={task.id}>
                <div>
                  <span className={`priority ${getPriorityClass(task.priority)}`}>{task.priority}</span>
                  <button className="task-check" aria-label="標記完成"></button>
                </div>
                <h3>{task.title}</h3>
                <p>{task.owner}・期限 {task.due}</p>
                <small>來源：{task.source}</small>
              </div>
            ))}
          </article>
        )}

        {/* 🏃‍♂️ 第二行：進行中 */}
        {(filter === 'all' || filter === 'pending') && (
          <article className="task-column">
            <div className="column-title"><span>進行中</span><b>{doingTasks.length}</b></div>
            {doingTasks.map((task:any) => (
              <div className="task-card" data-status="pending" key={task.id}>
                <div>
                  <span className={`priority ${getPriorityClass(task.priority)}`}>{task.priority}</span>
                  <button className="task-check" aria-label="標記完成"></button>
                </div>
                <h3>{task.title}</h3>
                <p>{task.owner}・期限 {task.due}</p>
                <small>來源：{task.source}</small>
              </div>
            ))}
          </article>
        )}

        {/* ✅ 第三行：已完成 */}
        {(filter === 'all' || filter === 'done') && (
          <article className="task-column">
            <div className="column-title"><span>已完成</span><b>{doneTasks.length}</b></div>
            {doneTasks.map((task:any) => (
              <div className="task-card completed" data-status="done" key={task.id}>
                <div>
                  <span className={`priority ${getPriorityClass(task.priority)}`}>{task.priority}</span>
                  <button className="task-check checked" aria-label="取消完成"></button>
                </div>
                <h3>{task.title}</h3>
                <p>{task.owner}・{task.due} 完成</p>
                <small>來源：{task.source}</small>
              </div>
            ))}
          </article>
        )}
      </div>
    </section>
  );
}