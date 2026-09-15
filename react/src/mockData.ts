export const activities = {
  camp: {
    id: 'camp', glyphColor: 'cyan',
    name: '迎新宿營', glyph: '宿', type: '大型活動', status: '準備中', statusClass: 'preparing',
    date: '10/03–10/04', fullDate: '2026/10/03–10/04', location: '溪頭青年活動中心',
    lead: '陳怡安', people: '120 人', budget: 'NT$ 186,000', progress: 67,
    nextMeeting: '三籌會議', nextMeetingDate: '9/18', nextAction: '召開三籌並確認交通、保險', prepNote: '距離活動還有 21 天',
    alert: ['尚未找到今年的保險確認資訊', '根據過去三年資料，保險通常會在三籌前完成確認。'],
    tasks: [
      { id: 'c1', title: '確認遊覽車發車時間', owner: '陳怡安', due: '9/16', source: '三籌會議', status: 'todo', priority: '高' },
      { id: 'c2', title: '安排雨備音響測試', owner: '黃冠宇', due: '9/20', source: '二籌會議', status: 'doing', priority: '高' },
      { id: 'c3', title: '更新家長通知單', owner: '吳品妤', due: '9/22', source: '三籌會議', status: 'todo', priority: '中' },
      { id: 'c4', title: '確認工作人員住宿名單', owner: '許庭瑜', due: '9/25', source: '二籌會議', status: 'doing', priority: '低' },
      { id: 'c5', title: '完成場地訂金付款', owner: '陳怡安', due: '9/08', source: '一籌會議', status: 'done', priority: '中' },
      { id: 'c6', title: '確認工作人員名單', owner: '吳品妤', due: '9/10', source: '二籌會議', status: 'done', priority: '低' }
    ],
    taskTotals: { done: 2, total: 6 },
    decisions: [
      { id: 'rain', state: '已確認', title: '晚會下雨如何處理？', date: '二籌・9/05', options: ['改至室內禮堂', '延後晚會時間', '取消晚會'], answer: '改至室內禮堂', description: '室內可避免活動中斷，也能保留完整節目內容；但需提前完成音響測試。', reason: '降低天候造成的中斷風險', execution: '準備中', source: '二籌會議紀錄', history: '2025 迎新宿營也曾啟動室內雨備' },
      { id: 'bus', state: '待確認', title: '遊覽車是否提早發車？', date: '三籌・9/12', options: ['維持 07:30', '提前至 07:00'], answer: '提前至 07:00', description: '週末上山車流較大，提早發車能降低延誤風險。', reason: '避開車潮並保留行程緩衝', execution: '待確認', source: '三籌會議紀錄', history: '2025 曾因週末車潮晚到 25 分鐘' },
      { id: 'vendor', state: '已確認', title: '晚餐廠商選擇', date: '二籌・9/05', options: ['山城餐飲', '校園餐盒'], answer: '沿用山城餐飲', description: '報價符合預算，且能配合過敏原標示與延後送餐。', reason: '供餐穩定且有合作經驗', execution: '已聯絡', source: '二籌會議紀錄', history: '2025 合作準時率良好' }
    ]
  },
  uniform: {
    id: 'uniform', glyphColor: 'violet',
    name: '制服趴', glyph: '服', type: '校內活動', status: '進行中', statusClass: 'ongoing',
    date: '09/12', fullDate: '2026/09/12', location: '學生活動中心 2F',
    lead: '黃冠宇', people: '180 人', budget: 'NT$ 72,000', progress: 100,
    nextMeeting: null, nextMeetingDate: '', nextAction: '持續現場執行並記錄臨時狀況', prepNote: '活動已於今天 14:00 開始',
    alert: ['西側入口排隊時間較長', '建議引導後續參加者改由東側入口進場。'],
    tasks: [
      { id: 'u1', title: '補充東側入口指示牌', owner: '林冠妤', due: '今天 16:30', source: '現場紀錄', status: 'doing', priority: '高' },
      { id: 'u2', title: '確認 DJ 撤場時間', owner: '黃冠宇', due: '今天 18:00', source: '行前工作會', status: 'todo', priority: '中' },
      { id: 'u3', title: '補拍活動主視覺照片', owner: '周子晴', due: '今天 17:00', source: '現場紀錄', status: 'doing', priority: '中' },
      { id: 'u4', title: '完成報到桌架設', owner: '鄭文翔', due: '今天 13:20', source: '行前工作會', status: 'done', priority: '高' },
      { id: 'u5', title: '確認餐點過敏原標示', owner: '林冠妤', due: '今天 13:40', source: '行前工作會', status: 'done', priority: '中' }
    ],
    taskTotals: { done: 2, total: 5 },
    decisions: [
      { id: 'entry', state: '已確認', title: '報到入口如何分流？', date: '行前會・9/10', options: ['維持西側入口', '開放東西雙入口'], answer: '開放東西雙入口', description: '兩側入口各配置一組報到人員，將排隊人潮平均分流。', reason: '縮短進場等待時間', execution: '執行中', source: '行前工作會紀錄', history: '2025 入場尖峰曾排隊 18 分鐘' },
      { id: 'dj', state: '已確認', title: 'DJ 設備撤場時間', date: '行前會・9/10', options: ['18:30 立即撤場', '19:00 後撤場'], answer: '19:00 後撤場', description: '保留活動結束後的自由交流音樂。', reason: '避免活動突然中斷', execution: '待執行', source: '行前工作會紀錄', history: '去年自由交流延長約 20 分鐘' }
    ]
  },
  bbq: {
    id: 'bbq', glyphColor: 'orange',
    name: '系烤', glyph: '烤', type: '聯誼活動', status: '未開始', statusClass: 'not-started',
    date: '12/05', fullDate: '2026/12/05', location: '河濱公園烤肉區',
    lead: '吳品妤', people: '90 人', budget: '尚未編列', progress: 0,
    nextMeeting: null, nextMeetingDate: '', nextAction: '安排第一次籌備會議', prepNote: '尚未開始籌備',
    alert: null,
    tasks: [],
    taskTotals: { done: 0, total: 0 },
    decisions: []
  },
  week: {
    id: 'week', glyphColor: 'pink',
    name: '資管週', glyph: '週', type: '系列活動', status: '已完成', statusClass: 'completed',
    date: '05/12–05/16', fullDate: '2026/05/12–05/16', location: '管理學院中庭',
    lead: '許庭瑜', people: '約 460 人次', budget: 'NT$ 98,400', progress: 100,
    nextMeeting: null, nextMeetingDate: '', nextAction: '查看並確認年度交接摘要', prepNote: '活動與檢討皆已完成',
    alert: null,
    tasks: [
      { id: 'w1', title: '完成廠商核銷', owner: '蔡宜芳', due: '5/28', source: '檢討會', status: 'done', priority: '高' },
      { id: 'w2', title: '整理活動照片', owner: '江昀庭', due: '5/30', source: '檢討會', status: 'done', priority: '中' },
      { id: 'w3', title: '完成年度交接摘要', owner: '許庭瑜', due: '6/02', source: '檢討會', status: 'done', priority: '高' }
    ],
    taskTotals: { done: 3, total: 3 },
    decisions: [
      { id: 'layout', state: '已確認', title: '攤位改採單向環形動線', date: '三籌・4/28', options: ['雙排直線', '單向環形'], answer: '單向環形動線', description: '讓入口與出口分開，避免中庭中央人潮交叉。', reason: '改善尖峰時段回堵', execution: '成效良好', source: '三籌會議紀錄', history: '2025 中午時段曾回堵至電梯口' }
    ]
  }
};

export const activityList = Object.values(activities);