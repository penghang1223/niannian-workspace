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

let tasks = [
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

const events = [
  { id: 1, type: 'project_start', source: 'main', target: null, data: '{"project":"Dashboard v4.0"}', created_at: new Date().toISOString() },
  { id: 2, type: 'test_pass', source: 'qa_engineer', target: null, data: '{"passed":7,"total":7}', created_at: new Date().toISOString() },
  { id: 3, type: 'deploy', source: 'dev_engineer', target: null, data: '{"platform":"vercel"}', created_at: new Date().toISOString() },
];

module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,PATCH,DELETE,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const url = new URL(req.url, 'http://localhost');
  const path = url.pathname.replace('/api', '');
  const method = req.method;

  try {
    if (path === '/health' || path === '/') return res.json({ status: 'ok', version: '1.0.0', timestamp: new Date().toISOString() });
    if (path === '/agents') return res.json({ data: agents });
    if (path === '/agents/stats') return res.json({ data: { total: 13, online: 6, busy: 0, idle: 7, offline: 0 } });

    const am = path.match(/^\/agents\/([^/]+)$/);
    if (am) { const a = agents.find(x => x.id === am[1]); return a ? res.json({ data: a }) : res.status(404).json({ error: 'Not found' }); }

    const atm = path.match(/^\/agents\/([^/]+)\/tasks$/);
    if (atm) return res.json({ data: tasks.filter(t => t.assignee_id === atm[1]) });

    if (path === '/tasks' && method === 'GET') {
      const st = url.searchParams.get('status');
      return res.json({ data: st ? tasks.filter(t => t.status === st) : tasks });
    }
    if (path === '/tasks/stats') return res.json({ data: { total: tasks.length, todo: tasks.filter(t=>t.status==='todo').length, in_progress: tasks.filter(t=>t.status==='in_progress').length, done: tasks.filter(t=>t.status==='done').length } });

    if (path === '/tasks' && method === 'POST') {
      let body = ''; req.on('data', c => body += c); req.on('end', () => {
        const b = JSON.parse(body || '{}');
        const ag = agents.find(a => a.id === b.assignee_id);
        const nt = { id: 'TASK-' + Date.now(), title: b.title, description: b.description || '', status: b.status || 'todo', priority: b.priority || 'P2', assignee_id: b.assignee_id, assignee_name: ag?.name || '', assignee_emoji: ag?.emoji || '', wave: b.wave || 1 };
        tasks.push(nt); return res.json({ data: nt });
      }); return;
    }

    const tm = path.match(/^\/tasks\/([^/]+)$/);
    if (tm && method === 'PATCH') {
      let body = ''; req.on('data', c => body += c); req.on('end', () => {
        const b = JSON.parse(body || '{}');
        const idx = tasks.findIndex(t => t.id === tm[1]);
        if (idx === -1) return res.status(404).json({ error: 'Not found' });
        if (b.status) tasks[idx].status = b.status;
        if (b.title) tasks[idx].title = b.title;
        return res.json({ data: tasks[idx] });
      }); return;
    }
    if (tm && method === 'DELETE') { tasks = tasks.filter(t => t.id !== tm[1]); return res.json({ success: true }); }

    if (path === '/metrics/overview') return res.json({ data: { agents: { total: 13, online: 6 }, tasks: { total: tasks.length, done: tasks.filter(t=>t.status==='done').length }, uptime: 999, memoryMB: 42 } });
    if (path === '/metrics/system') return res.json({ data: { memoryMB: 42, uptime: 999 } });
    if (path === '/metrics') return res.json({ data: [] });

    if (path === '/events' && method === 'GET') return res.json({ data: events });
    if (path === '/config') return res.json({ data: { name: 'Dashboard v4.0', version: '1.0.0', agents: 13 } });

    return res.status(404).json({ error: 'Not found', path });
  } catch (err) { return res.status(500).json({ error: err.message }); }
};
