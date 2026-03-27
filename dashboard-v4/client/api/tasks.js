const tasks = [
  { id: 'DASH-001', title: 'PRD 需求文档', description: 'Dashboard v4.0 产品需求文档', status: 'done', priority: 'P0', assignee_id: 'product_manager', assignee_name: '娜尔', assignee_emoji: '📋', wave: 1 },
  { id: 'DASH-002', title: '技术架构方案', description: 'Dashboard v4.0 技术架构设计', status: 'done', priority: 'P0', assignee_id: 'taiyi', assignee_name: '太一', assignee_emoji: '🏗️', wave: 1 },
  { id: 'DASH-003', title: '后端 API 开发', description: 'Fastify + SQLite 后端服务', status: 'done', priority: 'P0', assignee_id: 'dev_engineer', assignee_name: '开发工程师', assignee_emoji: '💻', wave: 2 },
  { id: 'DASH-004', title: '前端 UI 实现', description: 'React + Vite 前端页面', status: 'done', priority: 'P0', assignee_id: 'frontend_dev', assignee_name: '夕尔', assignee_emoji: '🎨', wave: 2 },
  { id: 'DASH-005', title: '前后端联调', description: 'API 对接 + WebSocket 调试', status: 'in_progress', priority: 'P0', assignee_id: 'dev_engineer', assignee_name: '开发工程师', assignee_emoji: '💻', wave: 3 },
  { id: 'DASH-006', title: '测试验收', description: '全面功能测试 + 性能测试', status: 'done', priority: 'P0', assignee_id: 'qa_engineer', assignee_name: '本尔', assignee_emoji: '🛡️', wave: 4 },
  { id: 'DASH-007', title: 'Vercel 部署', description: '前后端部署到 Vercel', status: 'in_progress', priority: 'P1', assignee_id: 'dev_engineer', assignee_name: '开发工程师', assignee_emoji: '💻', wave: 4 },
  { id: 'DASH-008', title: '性能优化', description: '代码分割 + 缓存优化', status: 'todo', priority: 'P2', assignee_id: 'frontend_dev', assignee_name: '夕尔', assignee_emoji: '🎨', wave: 5 },
  { id: 'DASH-009', title: '文档编写', description: '使用文档 + API 文档', status: 'todo', priority: 'P2', assignee_id: 'jinghong', assignee_name: '惊鸿', assignee_emoji: '📝', wave: 5 },
  { id: 'DASH-010', title: 'CI/CD 流水线', description: 'GitHub Actions 自动化', status: 'todo', priority: 'P2', assignee_id: 'dev_engineer', assignee_name: '开发工程师', assignee_emoji: '💻', wave: 5 },
];
module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.json({ data: tasks });
};
