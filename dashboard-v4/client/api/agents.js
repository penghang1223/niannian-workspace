const agents = [
  { id: 'main', name: '年年', role: '团队领导/协调员', emoji: '🎀', status: 'online', tasks_completed: 15, tasks_in_progress: 1, success_rate: 100 },
  { id: 'product_manager', name: '娜尔', role: '产品经理', emoji: '📋', status: 'online', tasks_completed: 8, tasks_in_progress: 0, success_rate: 100 },
  { id: 'qa_engineer', name: '本尔', role: '测试工程师', emoji: '🛡️', status: 'online', tasks_completed: 5, tasks_in_progress: 0, success_rate: 100 },
  { id: 'dev_engineer', name: '开发工程师', role: '后端开发', emoji: '💻', status: 'online', tasks_completed: 6, tasks_in_progress: 2, success_rate: 100 },
  { id: 'frontend_dev', name: '夕尔', role: '前端开发', emoji: '🎨', status: 'online', tasks_completed: 3, tasks_in_progress: 0, success_rate: 100 },
  { id: 'taiyi', name: '太一', role: '架构师', emoji: '🏗️', status: 'online', tasks_completed: 4, tasks_in_progress: 0, success_rate: 100 },
  { id: 'chief_cute_officer', name: '岁岁', role: '首席可爱官', emoji: '🎉', status: 'idle', tasks_completed: 2, tasks_in_progress: 0, success_rate: 100 },
  { id: 'lingxi', name: '灵犀', role: '策略顾问', emoji: '💡', status: 'idle', tasks_completed: 1, tasks_in_progress: 0, success_rate: 100 },
  { id: 'jinghong', name: '惊鸿', role: '翰林/文案', emoji: '📝', status: 'idle', tasks_completed: 1, tasks_in_progress: 0, success_rate: 100 },
  { id: 'tiangong', name: '天工', role: '首席架构师', emoji: '⚙️', status: 'idle', tasks_completed: 1, tasks_in_progress: 0, success_rate: 100 },
  { id: 'zhiming', name: '执明', role: '协调员', emoji: '🔄', status: 'idle', tasks_completed: 0, tasks_in_progress: 0, success_rate: 100 },
  { id: 'yueying', name: '月影', role: '数据分析', emoji: '📊', status: 'idle', tasks_completed: 0, tasks_in_progress: 0, success_rate: 100 },
  { id: 'shichen', name: '司辰', role: '时间管理', emoji: '⏰', status: 'idle', tasks_completed: 0, tasks_in_progress: 0, success_rate: 100 },
];
module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.json({ data: agents });
};
