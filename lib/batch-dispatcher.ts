/**
 * BatchDispatcher - 批量 Agent 调度框架
 * 
 * 设计目标：减少串行 spawn 多个 Agent 的等待时间，
 * 通过波次（Wave）机制实现并行调度，提升整体效率。
 * 
 * @author Karl (Dev Engineer) 🛠️
 * @version 1.0.0
 */

// ─── 类型定义 ───────────────────────────────────────────────

/** 任务状态枚举 */
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'timeout' | 'retrying';

/** 任务配置选项 */
export interface TaskOptions {
  /** 超时时间（毫秒），默认 300000（5 分钟） */
  timeout?: number;
  /** 最大重试次数，默认 0 */
  maxRetries?: number;
  /** 重试间隔（毫秒），默认 2000 */
  retryDelay?: number;
  /** 依赖的任务标签列表（自动推断波次） */
  dependsOn?: string[];
  /** 附加元数据 */
  metadata?: Record<string, unknown>;
}

/** 单个任务定义 */
export interface TaskDefinition {
  /** 任务唯一标识 */
  label: string;
  /** 目标 Agent ID */
  agentId: string;
  /** 任务内容 */
  task: string;
  /** 任务选项 */
  options: Required<Pick<TaskOptions, 'timeout' | 'maxRetries' | 'retryDelay'>> & Omit<TaskOptions, 'timeout' | 'maxRetries' | 'retryDelay'>;
  /** 当前状态 */
  status: TaskStatus;
  /** 当前重试次数 */
  retryCount: number;
  /** 执行结果 */
  result?: unknown;
  /** 错误信息 */
  error?: Error;
  /** 开始时间 */
  startTime?: number;
  /** 结束时间 */
  endTime?: number;
  /** 所属波次索引 */
  waveIndex?: number;
}

/** 波次定义 */
export interface Wave {
  /** 波次内的任务标签列表 */
  taskLabels: string[];
}

/** 任务结果 */
export interface TaskResult {
  label: string;
  status: TaskStatus;
  result?: unknown;
  error?: Error;
  duration: number;
  retryCount: number;
}

/** 波次结果 */
export interface WaveResult {
  waveIndex: number;
  tasks: TaskResult[];
  duration: number;
  success: boolean;
}

/** 调度器进度 */
export interface DispatcherProgress {
  /** 总任务数 */
  total: number;
  /** 已完成数 */
  completed: number;
  /** 失败数 */
  failed: number;
  /** 运行中数 */
  running: number;
  /** 当前波次索引 */
  currentWave: number;
  /** 总波次数 */
  totalWaves: number;
  /** 完成百分比 */
  percentage: number;
}

/** 调度器配置 */
export interface DispatcherConfig {
  /** 全局默认超时（毫秒） */
  defaultTimeout?: number;
  /** 全局默认最大重试次数 */
  defaultMaxRetries?: number;
  /** 全局默认重试间隔（毫秒） */
  defaultRetryDelay?: number;
  /** 是否在任一波次全部失败时停止后续波次 */
  stopOnWaveFailure?: boolean;
  /** 用于实际 spawn Agent 的函数（方便测试 mock） */
  spawnFn?: SpawnFunction;
}

/** Spawn 函数签名 */
export type SpawnFunction = (config: {
  agentId: string;
  task: string;
  label?: string;
  timeout?: number;
  metadata?: Record<string, unknown>;
}) => Promise<{ result: unknown }>;

/** 回调函数类型 */
export type CompleteCallback = (results: WaveResult[]) => void;
export type WaveCompleteCallback = (result: WaveResult, waveIndex: number) => void;
export type ProgressCallback = (progress: DispatcherProgress) => void;
export type TaskStatusCallback = (task: TaskDefinition, status: TaskStatus) => void;

// ─── 常量 ─────────────────────────────────────────────────

const DEFAULT_TIMEOUT = 300_000;      // 5 分钟
const DEFAULT_MAX_RETRIES = 0;
const DEFAULT_RETRY_DELAY = 2_000;    // 2 秒

// ─── BatchDispatcher 类 ────────────────────────────────────

export class BatchDispatcher {
  private tasks: Map<string, TaskDefinition> = new Map();
  private waves: Wave[] = [];
  private waveCompleteCallbacks: Map<number | '*', WaveCompleteCallback[]> = new Map();
  private completeCallbacks: CompleteCallback[] = [];
  private progressCallbacks: ProgressCallback[] = [];
  private taskStatusCallbacks: TaskStatusCallback[] = [];
  private config: Required<DispatcherConfig>;
  private isExecuting = false;
  private waveResults: WaveResult[] = [];

  constructor(config: DispatcherConfig = {}) {
    this.config = {
      defaultTimeout: config.defaultTimeout ?? DEFAULT_TIMEOUT,
      defaultMaxRetries: config.defaultMaxRetries ?? DEFAULT_MAX_RETRIES,
      defaultRetryDelay: config.defaultRetryDelay ?? DEFAULT_RETRY_DELAY,
      stopOnWaveFailure: config.stopOnWaveFailure ?? false,
      spawnFn: config.spawnFn ?? defaultSpawnFunction,
    };
  }

  // ─── 公共 API ───────────────────────────────────────────

  /**
   * 添加单个任务
   */
  addTask(
    label: string,
    agentId: string,
    task: string,
    options: TaskOptions = {}
  ): this {
    this.assertNotExecuting('addTask');
    this.assertNotDuplicate(label);

    const taskDef: TaskDefinition = {
      label,
      agentId,
      task,
      options: {
        timeout: options.timeout ?? this.config.defaultTimeout,
        maxRetries: options.maxRetries ?? this.config.defaultMaxRetries,
        retryDelay: options.retryDelay ?? this.config.defaultRetryDelay,
        dependsOn: options.dependsOn,
        metadata: options.metadata,
      },
      status: 'pending',
      retryCount: 0,
    };

    this.tasks.set(label, taskDef);
    this.invalidateWaves(); // 任务变更，需要重新计算波次
    return this;
  }

  /**
   * 添加一波并行任务
   */
  addWave(taskDefs: Array<{
    label: string;
    agentId: string;
    task: string;
    options?: TaskOptions;
  }>): this {
    this.assertNotExecuting('addWave');

    for (const def of taskDefs) {
      this.addTask(def.label, def.agentId, def.task, def.options);
    }

    // 如果这些任务没有依赖关系，将它们放在同一波次
    const labels = taskDefs.map(d => d.label);
    this.waves.push({ taskLabels: labels });
    return this;
  }

  /**
   * 注册完成回调
   */
  onComplete(callback: CompleteCallback): this {
    this.completeCallbacks.push(callback);
    return this;
  }

  /**
   * 注册波次完成回调
   */
  onWaveComplete(callback: WaveCompleteCallback, waveIndex?: number): this {
    if (waveIndex !== undefined) {
      const existing = this.waveCompleteCallbacks.get(waveIndex) ?? [];
      existing.push(callback);
      this.waveCompleteCallbacks.set(waveIndex, existing);
    } else {
      // 使用 '*' 标记为所有波次的回调（执行时动态应用）
      const existing = this.waveCompleteCallbacks.get('*') ?? [];
      existing.push(callback);
      this.waveCompleteCallbacks.set('*', existing);
    }
    return this;
  }

  /**
   * 注册进度回调
   */
  onProgress(callback: ProgressCallback): this {
    this.progressCallbacks.push(callback);
    return this;
  }

  /**
   * 注册任务状态变更回调
   */
  onTaskStatus(callback: TaskStatusCallback): this {
    this.taskStatusCallbacks.push(callback);
    return this;
  }

  /**
   * 按波次顺序执行，同波次内并行
   */
  async execute(): Promise<WaveResult[]> {
    if (this.isExecuting) {
      throw new Error('Dispatcher is already executing');
    }

    if (this.tasks.size === 0) {
      throw new Error('No tasks to execute. Use addTask() or addWave() first.');
    }

    this.isExecuting = true;
    this.waveResults = [];

    try {
      // 如果没有手动添加波次，自动推断
      if (this.waves.length === 0) {
        this.inferWaves();
      }

      const totalWaves = this.waves.length;
      this.emitProgress();

      for (let waveIdx = 0; waveIdx < totalWaves; waveIdx++) {
        const wave = this.waves[waveIdx];
        this.emitProgress();

        // 并行执行当前波次的所有任务
        const waveResult = await this.executeWave(wave, waveIdx);
        this.waveResults.push(waveResult);

        // 触发波次完成回调
        this.triggerWaveCallbacks(waveResult, waveIdx);

        // 检查是否需要停止
        if (this.config.stopOnWaveFailure && !waveResult.success) {
          console.warn(`[BatchDispatcher] Wave ${waveIdx} failed, stopping subsequent waves.`);
          break;
        }
      }

      // 触发全局完成回调
      this.completeCallbacks.forEach(cb => {
        try {
          cb(this.waveResults);
        } catch (err) {
          console.error('[BatchDispatcher] Complete callback error:', err);
        }
      });

      return this.waveResults;
    } finally {
      this.isExecuting = false;
    }
  }

  /**
   * 获取当前进度
   */
  getProgress(): DispatcherProgress {
    const allTasks = Array.from(this.tasks.values());
    const completed = allTasks.filter(t => t.status === 'completed').length;
    const failed = allTasks.filter(t => t.status === 'failed' || t.status === 'timeout').length;
    const running = allTasks.filter(t => t.status === 'running' || t.status === 'retrying').length;

    return {
      total: this.tasks.size,
      completed,
      failed,
      running,
      currentWave: this.waveResults.length,
      totalWaves: this.getWaveCount(),
      percentage: this.tasks.size > 0
        ? Math.round((completed / this.tasks.size) * 100)
        : 0,
    };
  }

  /**
   * 获取所有任务
   */
  getTasks(): TaskDefinition[] {
    return Array.from(this.tasks.values());
  }

  /**
   * 获取指定任务
   */
  getTask(label: string): TaskDefinition | undefined {
    return this.tasks.get(label);
  }

  /**
   * 获取波次数
   */
  getWaveCount(): number {
    return this.waves.length > 0 ? this.waves.length : this.calculateInferredWaves();
  }

  /**
   * 重置调度器状态
   */
  reset(): this {
    if (this.isExecuting) {
      throw new Error('Cannot reset while executing');
    }
    this.tasks.clear();
    this.waves = [];
    this.waveCompleteCallbacks.clear();
    this.completeCallbacks = [];
    this.progressCallbacks = [];
    this.taskStatusCallbacks = [];
    this.waveResults = [];
    return this;
  }

  /**
   * 移除指定任务
   */
  removeTask(label: string): this {
    this.assertNotExecuting('removeTask');
    this.tasks.delete(label);
    this.invalidateWaves();
    return this;
  }

  // ─── 私有方法 ───────────────────────────────────────────

  /**
   * 执行单个波次（并行）
   */
  private async executeWave(wave: Wave, waveIndex: number): Promise<WaveResult> {
    const startTime = Date.now();

    // 标记波次内任务为 running
    for (const label of wave.taskLabels) {
      const task = this.tasks.get(label);
      if (task) {
        task.status = 'running';
        task.startTime = Date.now();
        task.waveIndex = waveIndex;
        this.emitTaskStatus(task, 'running');
      }
    }

    // 并行执行所有任务
    const taskPromises = wave.taskLabels.map(label =>
      this.executeTaskWithRetry(label)
    );

    const taskResults = await Promise.allSettled(taskPromises);

    const results: TaskResult[] = taskResults.map((result, idx) => {
      const label = wave.taskLabels[idx];
      const task = this.tasks.get(label)!;

      if (result.status === 'fulfilled') {
        task.status = 'completed';
        task.endTime = Date.now();
        task.result = result.value;
        this.emitTaskStatus(task, 'completed');
      } else {
        task.status = task.status === 'timeout' ? 'timeout' : 'failed';
        task.endTime = Date.now();
        task.error = result.reason instanceof Error ? result.reason : new Error(String(result.reason));
        this.emitTaskStatus(task, task.status);
      }

      return {
        label,
        status: task.status,
        result: task.result,
        error: task.error,
        duration: (task.endTime ?? Date.now()) - (task.startTime ?? Date.now()),
        retryCount: task.retryCount,
      };
    });

    const duration = Date.now() - startTime;
    const success = results.every(r => r.status === 'completed');

    return {
      waveIndex,
      tasks: results,
      duration,
      success,
    };
  }

  /**
   * 执行单个任务（含重试逻辑）
   */
  private async executeTaskWithRetry(label: string): Promise<unknown> {
    const task = this.tasks.get(label)!;

    while (task.retryCount <= task.options.maxRetries) {
      try {
        if (task.retryCount > 0) {
          task.status = 'retrying';
          this.emitTaskStatus(task, 'retrying');
          await this.sleep(task.options.retryDelay * task.retryCount);
        }

        const result = await this.executeWithTimeout(task);
        return result;
      } catch (err) {
        task.retryCount++;

        if (err instanceof TimeoutError) {
          task.status = 'timeout';
          this.emitTaskStatus(task, 'timeout');
          if (task.retryCount > task.options.maxRetries) {
            throw err;
          }
        } else {
          if (task.retryCount > task.options.maxRetries) {
            throw err;
          }
        }

        // 还有重试机会，继续循环
      }
    }

    throw new Error(`Task "${label}" exhausted all retries`);
  }

  /**
   * 带超时的执行
   */
  private async executeWithTimeout(task: TaskDefinition): Promise<unknown> {
    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        reject(new TimeoutError(`Task "${task.label}" timed out after ${task.options.timeout}ms`));
      }, task.options.timeout);

      this.config.spawnFn!({
        agentId: task.agentId,
        task: task.task,
        label: task.label,
        timeout: task.options.timeout,
        metadata: task.metadata,
      })
        .then(result => {
          clearTimeout(timeoutId);
          resolve(result);
        })
        .catch(err => {
          clearTimeout(timeoutId);
          reject(err);
        });
    });
  }

  /**
   * 基于依赖关系自动推断波次
   */
  private inferWaves(): void {
    const assigned = new Set<string>();
    const waves: Wave[] = [];

    while (assigned.size < this.tasks.size) {
      const currentWave: string[] = [];

      for (const [label, task] of this.tasks) {
        if (assigned.has(label)) continue;

        const deps = task.options.dependsOn ?? [];
        const allDepsMet = deps.every(dep => assigned.has(dep));

        if (allDepsMet) {
          currentWave.push(label);
        }
      }

      if (currentWave.length === 0) {
        // 存在循环依赖，将剩余任务放入最后一波
        for (const [label] of this.tasks) {
          if (!assigned.has(label)) {
            currentWave.push(label);
          }
        }
      }

      for (const label of currentWave) {
        assigned.add(label);
      }

      waves.push({ taskLabels: currentWave });
    }

    this.waves = waves;
  }

  /**
   * 计算推断后的波次数（不实际修改 waves）
   */
  private calculateInferredWaves(): number {
    const assigned = new Set<string>();
    let count = 0;

    while (assigned.size < this.tasks.size) {
      let found = false;
      for (const [label, task] of this.tasks) {
        if (assigned.has(label)) continue;
        const deps = task.options.dependsOn ?? [];
        if (deps.every(dep => assigned.has(dep))) {
          assigned.add(label);
          found = true;
        }
      }
      if (!found) {
        // 循环依赖，剩余全部算一波
        assigned.clear();
        return count + 1;
      }
      count++;
    }

    return count;
  }

  /**
   * 使波次缓存失效
   */
  private invalidateWaves(): void {
    // 仅在手动添加的波次下清理
    // 如果是自动推断则在 execute 时重建
  }

  /**
   * 触发波次回调
   */
  private triggerWaveCallbacks(result: WaveResult, waveIndex: number): void {
    // 特定波次的回调
    const callbacks = this.waveCompleteCallbacks.get(waveIndex) ?? [];
    for (const cb of callbacks) {
      try {
        cb(result, waveIndex);
      } catch (err) {
        console.error(`[BatchDispatcher] Wave ${waveIndex} callback error:`, err);
      }
    }
    // 所有波次的回调（'*' 标记）
    const allCallbacks = this.waveCompleteCallbacks.get('*') ?? [];
    for (const cb of allCallbacks) {
      try {
        cb(result, waveIndex);
      } catch (err) {
        console.error(`[BatchDispatcher] Wave ${waveIndex} callback error:`, err);
      }
    }
    this.emitProgress();
  }

  /**
   * 发送进度更新
   */
  private emitProgress(): void {
    const progress = this.getProgress();
    for (const cb of this.progressCallbacks) {
      try {
        cb(progress);
      } catch (err) {
        console.error('[BatchDispatcher] Progress callback error:', err);
      }
    }
  }

  /**
   * 发送任务状态变更
   */
  private emitTaskStatus(task: TaskDefinition, status: TaskStatus): void {
    for (const cb of this.taskStatusCallbacks) {
      try {
        cb(task, status);
      } catch (err) {
        console.error('[BatchDispatcher] Task status callback error:', err);
      }
    }
    this.emitProgress();
  }

  /**
   * 断言未在执行中
   */
  private assertNotExecuting(method: string): void {
    if (this.isExecuting) {
      throw new Error(`Cannot call ${method}() while executing`);
    }
  }

  /**
   * 断言标签不重复
   */
  private assertNotDuplicate(label: string): void {
    if (this.tasks.has(label)) {
      throw new Error(`Task with label "${label}" already exists`);
    }
  }

  /**
   * 睡眠
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// ─── 自定义错误 ───────────────────────────────────────────

export class TimeoutError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'TimeoutError';
  }
}

// ─── 默认 Spawn 函数 ──────────────────────────────────────

/**
 * 默认的 spawn 函数 - 使用 OpenClaw sessions_spawn API 格式
 * 
 * 在生产环境中，应注入实际的 sessions_spawn 实现。
 * 此默认实现仅用于测试和开发。
 */
async function defaultSpawnFunction(config: {
  agentId: string;
  task: string;
  label?: string;
  timeout?: number;
  metadata?: Record<string, unknown>;
}): Promise<{ result: unknown }> {
  // 这是一个 placeholder，实际使用时应通过 config.spawnFn 注入真实实现
  // 真实实现示例：
  //   const session = await sessions_spawn({
  //     agentId: config.agentId,
  //     task: config.task,
  //     label: config.label,
  //     metadata: config.metadata,
  //   });
  //   return { result: session };
  
  console.log(`[BatchDispatcher] Spawning agent "${config.agentId}" with task: ${config.task.substring(0, 50)}...`);
  
  // 模拟延迟（用于开发测试）
  return new Promise(resolve => {
    setTimeout(() => {
      resolve({ result: { status: 'completed', agentId: config.agentId } });
    }, 100);
  });
}

// ─── 工具函数 ─────────────────────────────────────────────

/**
 * 快速创建并执行批量调度
 * 
 * @example
 * ```typescript
 * const results = await quickDispatch([
 *   { label: 'pm', agentId: 'product_manager', task: '分析需求' },
 *   { label: 'dev', agentId: 'dev_engineer', task: '设计方案', options: { dependsOn: ['pm'] } },
 * ]);
 * ```
 */
export async function quickDispatch(
  tasks: Array<{
    label: string;
    agentId: string;
    task: string;
    options?: TaskOptions;
  }>,
  config?: DispatcherConfig
): Promise<WaveResult[]> {
  const dispatcher = new BatchDispatcher(config);

  for (const t of tasks) {
    dispatcher.addTask(t.label, t.agentId, t.task, t.options);
  }

  return dispatcher.execute();
}
