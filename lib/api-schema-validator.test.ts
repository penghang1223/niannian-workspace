import { SchemaValidator, AGENT_SCHEMA, TASK_SCHEMA, type ApiSchema, type FieldSchema } from './api-schema-validator';

// === 测试数据 ===
const validAgent = {
  id: 'main',
  name: '年年',
  role: '团队领导',
  emoji: '🎀',
  status: 'online',
  tasks_completed: 15,
  success_rate: 100,
};

const invalidAgent = {
  id: 'main',
  name: '年年',
  status: 'invalid_status', // 不在 enum 中
  tasks_completed: 'fifteen', // 类型错误
  // 缺少 required: role
};

const frontendAgentSchema: Record<string, FieldSchema> = {
  id: { type: 'string', required: true },
  name: { type: 'string', required: true },
  model: { type: 'string', required: true }, // 前端期望但后端没有
  last_heartbeat: { type: 'string' }, // 前端期望但后端没有
  capabilities: { type: 'array' }, // 前端期望但后端没有
};

const backendAgentSchema: Record<string, FieldSchema> = {
  id: { type: 'string', required: true },
  name: { type: 'string', required: true },
  emoji: { type: 'string' }, // 后端有但前端没期望
  tasks_completed: { type: 'number' }, // 后端有但前端没期望
  last_active: { type: 'string' }, // 后端有但前端没期望
};

// === 测试套件 ===
describe('SchemaValidator', () => {
  describe('validateRequest', () => {
    const schema: ApiSchema = {
      version: '1.0.0',
      baseUrl: '/api',
      endpoints: [{
        name: 'Create Agent',
        method: 'POST',
        path: '/agents',
        request: { body: AGENT_SCHEMA },
        response: { success: AGENT_SCHEMA },
      }],
    };
    const validator = new SchemaValidator(schema);

    test('valid data passes', () => {
      const result = validator.validateRequest('/agents', 'POST', validAgent);
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    test('missing required field fails', () => {
      const { role, ...partial } = validAgent;
      const result = validator.validateRequest('/agents', 'POST', partial);
      expect(result.valid).toBe(false);
      expect(result.errors.some(e => e.field === 'body.role')).toBe(true);
    });

    test('unknown endpoint returns error', () => {
      const result = validator.validateRequest('/unknown', 'GET', {});
      expect(result.valid).toBe(false);
    });
  });

  describe('compareSchemas', () => {
    test('detects missing fields (frontend expects, backend lacks)', () => {
      const result = SchemaValidator.compareSchemas(frontendAgentSchema, backendAgentSchema);
      expect(result.missing).toContain('model');
      expect(result.missing).toContain('last_heartbeat');
      expect(result.missing).toContain('capabilities');
    });

    test('detects extra fields (backend has, frontend ignores)', () => {
      const result = SchemaValidator.compareSchemas(frontendAgentSchema, backendAgentSchema);
      expect(result.extra).toContain('emoji');
      expect(result.extra).toContain('tasks_completed');
      expect(result.extra).toContain('last_active');
    });

    test('detects type mismatches', () => {
      const front = { count: { type: 'string' as const, required: true } };
      const back = { count: { type: 'number' as const, required: true } };
      const result = SchemaValidator.compareSchemas(front, back);
      expect(result.typeMismatches).toHaveLength(1);
      expect(result.typeMismatches[0].field).toBe('count');
    });

    test('identical schemas have no differences', () => {
      const result = SchemaValidator.compareSchemas(AGENT_SCHEMA, AGENT_SCHEMA);
      expect(result.missing).toHaveLength(0);
      expect(result.extra).toHaveLength(0);
      expect(result.typeMismatches).toHaveLength(0);
    });
  });

  describe('generateTypescript', () => {
    test('generates correct interface', () => {
      const ts = SchemaValidator.generateTypescript('Agent', {
        id: { type: 'string', required: true, description: '唯一标识' },
        name: { type: 'string', required: true },
        status: { type: 'string', enum: ['online', 'offline'] },
        count: { type: 'number' },
      });
      expect(ts).toContain('export interface Agent');
      expect(ts).toContain("id: string");
      expect(ts).toContain("status?: 'online' | 'offline'");
      expect(ts).toContain("count?: number");
    });
  });
});

// === 简单运行器 ===
function runTests() {
  let passed = 0;
  let failed = 0;

  function assert(condition: boolean, name: string) {
    if (condition) { passed++; console.log(`  ✅ ${name}`); }
    else { failed++; console.log(`  ❌ ${name}`); }
  }

  const schema: ApiSchema = {
    version: '1.0.0',
    baseUrl: '/api',
    endpoints: [{ name: 'Create Agent', method: 'POST', path: '/agents', request: { body: AGENT_SCHEMA }, response: { success: AGENT_SCHEMA } }],
  };
  const validator = new SchemaValidator(schema);

  console.log('\n📋 Schema Validator Tests\n');

  // Validate request
  const r1 = validator.validateRequest('/agents', 'POST', validAgent);
  assert(r1.valid, 'Valid agent passes validation');

  const { role, ...noRole } = validAgent;
  const r2 = validator.validateRequest('/agents', 'POST', noRole);
  assert(!r2.valid, 'Missing required field fails');

  // Compare schemas
  const cmp = SchemaValidator.compareSchemas(frontendAgentSchema, backendAgentSchema);
  assert(cmp.missing.includes('model'), 'Detects missing: model');
  assert(cmp.missing.includes('last_heartbeat'), 'Detects missing: last_heartbeat');
  assert(cmp.extra.includes('emoji'), 'Detects extra: emoji');
  assert(cmp.extra.includes('tasks_completed'), 'Detects extra: tasks_completed');

  const cmp2 = SchemaValidator.compareSchemas(AGENT_SCHEMA, AGENT_SCHEMA);
  assert(cmp2.missing.length === 0 && cmp2.extra.length === 0, 'Identical schemas have no diff');

  // Generate TypeScript
  const ts = SchemaValidator.generateTypescript('Agent', AGENT_SCHEMA);
  assert(ts.includes('export interface Agent'), 'Generates interface');
  assert(ts.includes("status"), 'Contains status field');

  console.log(`\n📊 Results: ${passed} passed, ${failed} failed\n`);
  return failed === 0;
}

runTests();
