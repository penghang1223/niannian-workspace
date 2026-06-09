import type { FastifyInstance } from 'fastify';
import type { DB } from './db.js';
import { broadcast } from './ws.js';
import { getWorkspaceSummary } from './workspace.js';

export async function registerRoutes(app: FastifyInstance, db: DB) {
  const agentsStmt = {
    all: db.prepare('SELECT * FROM agents ORDER BY name'),
    get: db.prepare('SELECT * FROM agents WHERE id = ?'),
    updateStatus: db.prepare("UPDATE agents SET status = ?, last_active = datetime('now'), updated_at = datetime('now') WHERE id = ?"),
    stats: db.prepare(`
      SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN status = 'online' THEN 1 ELSE 0 END) as online,
        SUM(CASE WHEN status = 'busy' THEN 1 ELSE 0 END) as busy,
        SUM(CASE WHEN status = 'idle' THEN 1 ELSE 0 END) as idle,
        SUM(CASE WHEN status = 'offline' THEN 1 ELSE 0 END) as offline
      FROM agents
    `),
    tasksByAgent: db.prepare('SELECT t.*, a.name as assignee_name, a.emoji as assignee_emoji FROM tasks t LEFT JOIN agents a ON t.assignee_id = a.id WHERE t.assignee_id = ? ORDER BY t.priority, t.created_at'),
    metricsByAgent: db.prepare('SELECT * FROM metrics WHERE agent_id = ? ORDER BY recorded_at DESC LIMIT 50')
  };

  const tasksStmt = {
    all: db.prepare('SELECT t.*, a.name as assignee_name, a.emoji as assignee_emoji FROM tasks t LEFT JOIN agents a ON t.assignee_id = a.id ORDER BY t.priority, t.created_at'),
    byStatus: db.prepare('SELECT t.*, a.name as assignee_name, a.emoji as assignee_emoji FROM tasks t LEFT JOIN agents a ON t.assignee_id = a.id WHERE t.status = ? ORDER BY t.priority, t.created_at'),
    get: db.prepare('SELECT t.*, a.name as assignee_name, a.emoji as assignee_emoji FROM tasks t LEFT JOIN agents a ON t.assignee_id = a.id WHERE t.id = ?'),
    create: db.prepare('INSERT INTO tasks (id, title, description, status, priority, assignee_id, wave, depends_on) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'),
    update: db.prepare("UPDATE tasks SET title = COALESCE(?, title), description = COALESCE(?, description), status = COALESCE(?, status), priority = COALESCE(?, priority), assignee_id = COALESCE(?, assignee_id), updated_at = datetime('now'), completed_at = CASE WHEN ? = 'done' THEN datetime('now') ELSE completed_at END WHERE id = ?"),
    delete: db.prepare('DELETE FROM tasks WHERE id = ?'),
    stats: db.prepare(`
      SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN status = 'todo' THEN 1 ELSE 0 END) as todo,
        SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
        SUM(CASE WHEN status = 'review' THEN 1 ELSE 0 END) as review,
        SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as done,
        SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
      FROM tasks
    `)
  };

  const metricsStmt = {
    latest: db.prepare('SELECT * FROM metrics ORDER BY recorded_at DESC LIMIT 100'),
    byAgent: db.prepare('SELECT * FROM metrics WHERE agent_id = ? ORDER BY recorded_at DESC LIMIT 50'),
    overview: db.prepare(`
      SELECT 
        (SELECT COUNT(*) FROM agents) as total_agents,
        (SELECT COUNT(*) FROM agents WHERE status = 'online') as online_agents,
        (SELECT COUNT(*) FROM tasks) as total_tasks,
        (SELECT COUNT(*) FROM tasks WHERE status = 'done') as completed_tasks,
        (SELECT COUNT(*) FROM tasks WHERE status = 'in_progress') as active_tasks,
        (SELECT AVG(success_rate) FROM agents) as avg_success_rate
    `),
    agentActivity: db.prepare(`
      SELECT agent_id, metric_type, value, recorded_at 
      FROM metrics 
      WHERE metric_type IN ('task_count', 'response_time')
      ORDER BY recorded_at DESC LIMIT 200
    `),
    taskTrends: db.prepare(`
      SELECT date(created_at) as date, status, COUNT(*) as count
      FROM tasks
      GROUP BY date(created_at), status
      ORDER BY date DESC LIMIT 100
    `)
  };

  const eventsStmt = {
    recent: db.prepare('SELECT * FROM events ORDER BY created_at DESC LIMIT 50'),
    create: db.prepare('INSERT INTO events (type, source, target, data) VALUES (?, ?, ?, ?)')
  };

  // ============================================
  // Agent API
  // ============================================

  app.get('/api/agents', async () => {
    return { data: agentsStmt.all.all() };
  });

  app.get('/api/agents/stats', async () => {
    return { data: agentsStmt.stats.get() };
  });

  app.get<{ Params: { id: string } }>('/api/agents/:id', async (req, reply) => {
    const agent = agentsStmt.get.get(req.params.id);
    if (!agent) return reply.status(404).send({ error: 'Agent not found' });
    return { data: agent };
  });

  app.get<{ Params: { id: string } }>('/api/agents/:id/tasks', async (req) => {
    return { data: agentsStmt.tasksByAgent.all(req.params.id) };
  });

  app.get<{ Params: { id: string } }>('/api/agents/:id/metrics', async (req) => {
    return { data: agentsStmt.metricsByAgent.all(req.params.id) };
  });

  app.patch<{ Params: { id: string }; Body: { status: string } }>('/api/agents/:id/status', async (req, reply) => {
    const { status } = req.body;
    if (!status) return reply.status(400).send({ error: 'status is required' });
    agentsStmt.updateStatus.run(status, req.params.id);
    const agent = agentsStmt.get.get(req.params.id);
    if (!agent) return reply.status(404).send({ error: 'Agent not found' });
    broadcast('agent:status-change', { agentId: req.params.id, status, timestamp: new Date().toISOString() });
    return { data: agent };
  });

  // ============================================
  // Tasks API
  // ============================================

  app.get('/api/tasks', async (req) => {
    const query = req.query as { status?: string; priority?: string; assignee_id?: string };
    if (query.status) {
      return { data: tasksStmt.byStatus.all(query.status) };
    }
    return { data: tasksStmt.all.all() };
  });

  app.get('/api/tasks/stats', async () => {
    return { data: tasksStmt.stats.get() };
  });

  app.get<{ Params: { id: string } }>('/api/tasks/:id', async (req, reply) => {
    const task = tasksStmt.get.get(req.params.id);
    if (!task) return reply.status(404).send({ error: 'Task not found' });
    return { data: task };
  });

  app.post('/api/tasks', async (req, reply) => {
    const body = req.body as any;
    if (!body.title) return reply.status(400).send({ error: 'title is required' });
    const id = body.id || `TASK-${Date.now()}`;
    tasksStmt.create.run(id, body.title, body.description || null, body.status || 'todo', body.priority || 'P2', body.assignee_id || null, body.wave || 1, JSON.stringify(body.depends_on || []));
    const task = tasksStmt.get.get(id);
    broadcast('task:created', { task });
    eventsStmt.create.run('task.created', 'api', id, JSON.stringify({ title: body.title }));
    return { data: task };
  });

  app.patch<{ Params: { id: string } }>('/api/tasks/:id', async (req, reply) => {
    const body = req.body as any;
    const existing = tasksStmt.get.get(req.params.id);
    if (!existing) return reply.status(404).send({ error: 'Task not found' });
    tasksStmt.update.run(body.title ?? null, body.description ?? null, body.status ?? null, body.priority ?? null, body.assignee_id ?? null, body.status ?? null, req.params.id);
    const task = tasksStmt.get.get(req.params.id);
    broadcast('task:updated', { task, changes: body });
    return { data: task };
  });

  app.delete<{ Params: { id: string } }>('/api/tasks/:id', async (req, reply) => {
    const existing = tasksStmt.get.get(req.params.id);
    if (!existing) return reply.status(404).send({ error: 'Task not found' });
    tasksStmt.delete.run(req.params.id);
    broadcast('task:deleted', { taskId: req.params.id });
    eventsStmt.create.run('task.deleted', 'api', req.params.id, '{}');
    return { success: true };
  });

  // ============================================
  // Metrics API
  // ============================================

  app.get('/api/metrics', async () => {
    return { data: metricsStmt.latest.all() };
  });

  app.get('/api/metrics/overview', async () => {
    return { data: metricsStmt.overview.get() };
  });

  app.get('/api/metrics/agents', async () => {
    return { data: metricsStmt.agentActivity.all() };
  });

  app.get('/api/metrics/tasks', async () => {
    return { data: metricsStmt.taskTrends.all() };
  });

  app.get('/api/metrics/system', async () => {
    const memUsage = process.memoryUsage();
    return {
      data: {
        memory: {
          rss: Math.round(memUsage.rss / 1024 / 1024),
          heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024),
          heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024),
          external: Math.round(memUsage.external / 1024 / 1024),
          unit: 'MB'
        },
        uptime: Math.round(process.uptime()),
        nodeVersion: process.version,
        platform: process.platform,
        arch: process.arch
      }
    };
  });

  // ============================================
  // Events API
  // ============================================

  app.get('/api/events', async () => {
    return { data: eventsStmt.recent.all() };
  });

  app.post('/api/events', async (req) => {
    const body = req.body as any;
    eventsStmt.create.run(body.type, body.source || null, body.target || null, JSON.stringify(body.data || {}));
    return { success: true };
  });

  // ============================================
  // Workspace API
  // ============================================

  app.get('/api/workspace/summary', async () => {
    return { data: getWorkspaceSummary() };
  });

  // ============================================
  // Config API
  // ============================================

  app.get('/api/config', async () => {
    return {
      data: {
        name: 'Dashboard v4.0',
        version: '1.0.0',
        refreshInterval: 5000,
        wsReconnectInterval: 3000,
        theme: 'dark'
      }
    };
  });

  app.patch('/api/config', async () => {
    // In a real impl, persist to a config table
    return { success: true, message: 'Config updated (in-memory)' };
  });
}
