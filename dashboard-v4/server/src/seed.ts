import { initDatabase } from './db.js';

const db = initDatabase();

// 清空旧数据（先删有外键引用的表）
db.exec('DELETE FROM metrics');
db.exec('DELETE FROM events');
db.exec('DELETE FROM tasks');
db.exec('DELETE FROM agents');

// 插入 13 个 Agent
const insertAgent = db.prepare(`
  INSERT INTO agents (id, name, role, emoji, status, tasks_completed, success_rate)
  VALUES (?, ?, ?, ?, ?, ?, ?)
`);

const agents = [
  ['main', '年年', '团队领导/协调员', '🎀', 'online', 15, 100],
  ['product_manager', '娜尔', '产品经理', '📋', 'online', 8, 100],
  ['qa_engineer', '本尔', '测试工程师', '🛡️', 'online', 5, 100],
  ['dev_engineer', '开发工程师', '后端开发', '💻', 'online', 6, 100],
  ['frontend_dev', '夕尔', '前端开发', '🎨', 'online', 3, 100],
  ['taiyi', '太一', '架构师', '🏗️', 'online', 4, 100],
  ['chief_cute_officer', '岁岁', '首席可爱官', '🎉', 'idle', 2, 100],
  ['lingxi', '灵犀', '策略顾问', '💡', 'idle', 1, 100],
  ['jinghong', '惊鸿', '翰林/文案', '📝', 'idle', 1, 100],
  ['tiangong', '天工', '首席架构师', '⚙️', 'idle', 1, 100],
  ['zhiming', '执明', '协调员', '🔄', 'idle', 0, 100],
  ['yueying', '月影', '数据分析', '📊', 'idle', 0, 100],
  ['shichen', '司辰', '时间管理', '⏰', 'idle', 0, 100],
];

for (const [id, name, role, emoji, status, tasksCompleted, successRate] of agents) {
  insertAgent.run(id, name, role, emoji, status, tasksCompleted, successRate);
}

// 插入示例任务
const insertTask = db.prepare(`
  INSERT INTO tasks (id, title, description, status, priority, assignee_id, wave)
  VALUES (?, ?, ?, ?, ?, ?, ?)
`);

const tasks = [
  ['DASH-001', 'PRD 需求文档', 'Dashboard v4.0 产品需求文档', 'done', 'P0', 'product_manager', 1],
  ['DASH-002', '技术架构方案', 'Dashboard v4.0 技术架构设计', 'done', 'P0', 'taiyi', 1],
  ['DASH-003', '后端 API 开发', 'Fastify + SQLite 后端服务', 'in_progress', 'P0', 'dev_engineer', 2],
  ['DASH-004', '前端 UI 实现', 'React + Vite 前端页面', 'in_progress', 'P0', 'frontend_dev', 2],
  ['DASH-005', '前后端联调', 'API 对接 + WebSocket 调试', 'todo', 'P0', 'dev_engineer', 3],
  ['DASH-006', '测试验收', '全面功能测试 + 性能测试', 'todo', 'P0', 'qa_engineer', 4],
  ['DASH-007', '部署上线', 'pm2 守护进程 + 启动脚本', 'todo', 'P1', 'dev_engineer', 4],
];

for (const [id, title, desc, status, priority, assignee, wave] of tasks) {
  insertTask.run(id, title, desc, status, priority, assignee, wave);
}

// 插入示例事件
const insertEvent = db.prepare(`
  INSERT INTO events (type, source, target, data)
  VALUES (?, ?, ?, ?)
`);

insertEvent.run('project_start', 'main', null, '{"project": "Dashboard v4.0"}');
insertEvent.run('task_completed', 'product_manager', 'DASH-001', '{}');
insertEvent.run('task_completed', 'taiyi', 'DASH-002', '{}');

console.log('✅ Seed data inserted successfully');
console.log(`   - ${agents.length} agents`);
console.log(`   - ${tasks.length} tasks`);
console.log(`   - 3 events`);

db.close();
