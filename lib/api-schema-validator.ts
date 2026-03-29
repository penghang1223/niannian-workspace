/**
 * API Schema Validator
 * 
 * 解决前后端字段不一致问题 — 开发前先定义 schema 契约
 * 
 * 使用场景：
 * 1. 开发前定义 API schema (JSON Schema 格式)
 * 2. 从 schema 自动生成 TypeScript 类型
 * 3. 验证请求/响应数据是否符合 schema
 * 4. 对比前后端 schema 差异
 */

// === Schema 定义类型 ===
export interface FieldSchema {
  type: 'string' | 'number' | 'boolean' | 'array' | 'object' | 'null';
  required?: boolean;
  description?: string;
  example?: any;
  enum?: any[];
  items?: FieldSchema;
  properties?: Record<string, FieldSchema>;
  minLength?: number;
  maxLength?: number;
  minimum?: number;
  maximum?: number;
  pattern?: string;
}

export interface EndpointSchema {
  name: string;
  method: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  path: string;
  description?: string;
  request?: {
    query?: Record<string, FieldSchema>;
    body?: Record<string, FieldSchema>;
  };
  response: {
    success: Record<string, FieldSchema>;
    error?: Record<string, FieldSchema>;
  };
}

export interface ApiSchema {
  version: string;
  baseUrl: string;
  endpoints: EndpointSchema[];
}

// === 验证结果 ===
export interface ValidationError {
  field: string;
  expected: string;
  actual: string;
  message: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
}

// === Schema Validator ===
export class SchemaValidator {
  private schema: ApiSchema;

  constructor(schema: ApiSchema) {
    this.schema = schema;
  }

  /** 验证请求数据 */
  validateRequest(path: string, method: string, data: Record<string, any>): ValidationResult {
    const endpoint = this.findEndpoint(path, method);
    if (!endpoint) return { valid: false, errors: [{ field: 'endpoint', expected: 'defined', actual: 'not found', message: `Endpoint ${method} ${path} not found in schema` }] };
    if (!endpoint.request?.body) return { valid: true, errors: [] };
    return this.validateFields(data, endpoint.request.body, 'body');
  }

  /** 验证响应数据 */
  validateResponse(path: string, method: string, data: Record<string, any>): ValidationResult {
    const endpoint = this.findEndpoint(path, method);
    if (!endpoint) return { valid: false, errors: [{ field: 'endpoint', expected: 'defined', actual: 'not found', message: `Endpoint ${method} ${path} not found in schema` }] };
    return this.validateFields(data, endpoint.response.success, 'response');
  }

  /** 对比两个 schema 的差异 */
  static compareSchemas(frontend: Record<string, FieldSchema>, backend: Record<string, FieldSchema>): { missing: string[], extra: string[], typeMismatches: { field: string, frontend: string, backend: string }[] } {
    const missing: string[] = [];
    const extra: string[] = [];
    const typeMismatches: { field: string, frontend: string, backend: string }[] = [];

    // 前端期望但后端没有的字段
    for (const key of Object.keys(frontend)) {
      if (!(key in backend)) {
        missing.push(key);
      } else if (frontend[key].type !== backend[key].type) {
        typeMismatches.push({ field: key, frontend: frontend[key].type, backend: backend[key].type });
      }
    }

    // 后端有但前端不需要的字段
    for (const key of Object.keys(backend)) {
      if (!(key in frontend)) {
        extra.push(key);
      }
    }

    return { missing, extra, typeMismatches };
  }

  /** 从 schema 生成 TypeScript 类型定义 */
  static generateTypescript(name: string, fields: Record<string, FieldSchema>): string {
    const lines: string[] = [`export interface ${name} {`];
    for (const [key, field] of Object.entries(fields)) {
      const tsType = this.fieldToTsType(field);
      const optional = field.required ? '' : '?';
      if (field.description) lines.push(`  /** ${field.description} */`);
      lines.push(`  ${key}${optional}: ${tsType};`);
    }
    lines.push('}');
    return lines.join('\n');
  }

  private static fieldToTsType(field: FieldSchema): string {
    switch (field.type) {
      case 'string': return field.enum ? field.enum.map(e => `'${e}'`).join(' | ') : 'string';
      case 'number': return 'number';
      case 'boolean': return 'boolean';
      case 'array': return field.items ? `${this.fieldToTsType(field.items)}[]` : 'any[]';
      case 'object': return field.properties ? `{ ${Object.entries(field.properties).map(([k, v]) => `${k}: ${this.fieldToTsType(v)}`).join('; ')} }` : 'Record<string, any>';
      case 'null': return 'null';
      default: return 'any';
    }
  }

  private findEndpoint(path: string, method: string): EndpointSchema | undefined {
    return this.schema.endpoints.find(e => e.path === path && e.method === method);
  }

  private validateFields(data: Record<string, any>, schema: Record<string, FieldSchema>, prefix: string): ValidationResult {
    const errors: ValidationError[] = [];
    for (const [key, field] of Object.entries(schema)) {
      const value = data[key];
      const fieldPath = `${prefix}.${key}`;

      if (field.required && (value === undefined || value === null)) {
        errors.push({ field: fieldPath, expected: field.type, actual: 'undefined', message: `Required field '${fieldPath}' is missing` });
        continue;
      }

      if (value !== undefined && value !== null) {
        const actualType = Array.isArray(value) ? 'array' : typeof value;
        if (actualType !== field.type && !(field.type === 'null' && value === null)) {
          errors.push({ field: fieldPath, expected: field.type, actual: actualType, message: `Type mismatch at '${fieldPath}': expected ${field.type}, got ${actualType}` });
        }
      }
    }
    return { valid: errors.length === 0, errors };
  }
}

// === 预置 schema 示例 ===
export const AGENT_SCHEMA: Record<string, FieldSchema> = {
  id: { type: 'string', required: true, description: 'Agent 唯一标识' },
  name: { type: 'string', required: true, description: 'Agent 名称' },
  role: { type: 'string', required: true, description: 'Agent 角色' },
  emoji: { type: 'string', description: 'Agent 图标' },
  status: { type: 'string', required: true, enum: ['online', 'busy', 'idle', 'offline', 'error'], description: 'Agent 状态' },
  tasks_completed: { type: 'number', description: '已完成任务数' },
  tasks_in_progress: { type: 'number', description: '进行中任务数' },
  success_rate: { type: 'number', description: '成功率' },
};

export const TASK_SCHEMA: Record<string, FieldSchema> = {
  id: { type: 'string', required: true, description: '任务 ID' },
  title: { type: 'string', required: true, description: '任务标题' },
  description: { type: 'string', description: '任务描述' },
  status: { type: 'string', required: true, enum: ['todo', 'in_progress', 'review', 'done', 'cancelled'], description: '任务状态' },
  priority: { type: 'string', required: true, enum: ['P0', 'P1', 'P2', 'P3'], description: '优先级' },
  assignee_id: { type: 'string', description: '负责人 Agent ID' },
  assignee_name: { type: 'string', description: '负责人名称（冗余）' },
  assignee_emoji: { type: 'string', description: '负责人图标（冗余）' },
  wave: { type: 'number', description: '所属波次' },
};
