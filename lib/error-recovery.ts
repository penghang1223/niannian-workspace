/**
 * 错误恢复框架 — Error Recovery Framework
 * 解决部署踩坑问题：重试、熔断、管道化回滚
 */

// ─── Types ───────────────────────────────────────────────────────────────────

export interface RetryOptions {
  maxRetries: number;
  /** 初始退避毫秒数，默认 1000 */
  initialDelay?: number;
  /** 退避乘数，默认 2（指数退避） */
  backoffMultiplier?: number;
  /** 单次操作超时毫秒数 */
  timeout?: number;
  /** 快速失败：匹配到这些错误模式时立即切换 fallback，不等重试 */
  fastFailPatterns?: (string | RegExp)[];
}

export interface FallbackChainResult<T> {
  value: T;
  /** 成功执行的方案索引（0 = 主方案） */
  strategyIndex: number;
  attempts: number;
}

// ─── RetryStrategy ───────────────────────────────────────────────────────────

export class RetryStrategy {
  private readonly opts: Required<RetryOptions>;

  constructor(options: RetryOptions) {
    this.opts = {
      maxRetries: options.maxRetries,
      initialDelay: options.initialDelay ?? 1000,
      backoffMultiplier: options.backoffMultiplier ?? 2,
      timeout: options.timeout ?? 30_000,
      fastFailPatterns: options.fastFailPatterns ?? [],
    };
  }

  /** 带重试 + 指数退避的单操作执行 */
  async execute<T>(action: () => Promise<T>): Promise<T> {
    let lastError: unknown;
    for (let attempt = 0; attempt <= this.opts.maxRetries; attempt++) {
      try {
        return await this.withTimeout(action(), this.opts.timeout);
      } catch (err) {
        lastError = err;
        // fastFail：匹配到明确失败模式直接抛出
        if (this.isFastFail(err)) {
          throw new FastFailError(err, attempt);
        }
        if (attempt < this.opts.maxRetries) {
          const delay = this.opts.initialDelay * this.opts.backoffMultiplier ** attempt;
          await sleep(delay);
        }
      }
    }
    throw lastError;
  }

  /**
   * fallbackChain — 一串备选方案，主方案失败自动切换下一个。
   * 每个策略内部仍走 retry 逻辑。
   */
  async executeWithFallbacks<T>(
    strategies: Array<() => Promise<T>>,
  ): Promise<FallbackChainResult<T>> {
    let totalAttempts = 0;
    for (let i = 0; i < strategies.length; i++) {
      try {
        const value = await this.execute(async () => {
          totalAttempts++;
          return strategies[i]();
        });
        return { value, strategyIndex: i, attempts: totalAttempts };
      } catch (err) {
        // 最后一个策略也失败了
        if (i === strategies.length - 1) {
          throw new FallbackExhaustedError(err, strategies.length, totalAttempts);
        }
        // 非最后一个策略失败，继续下一个
      }
    }
    // unreachable
    throw new Error('Unreachable');
  }

  // ── private ──

  private isFastFail(err: unknown): boolean {
    const msg = err instanceof Error ? err.message : String(err);
    return this.opts.fastFailPatterns.some((p) =>
      typeof p === 'string' ? msg.includes(p) : p.test(msg),
    );
  }

  private withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
    return Promise.race([
      promise,
      new Promise<never>((_, reject) =>
        setTimeout(() => reject(new TimeoutError(ms)), ms),
      ),
    ]);
  }
}

// ─── CircuitBreaker ──────────────────────────────────────────────────────────

export type CircuitState = 'closed' | 'open' | 'half-open';

export interface CircuitBreakerOptions {
  /** 连续失败 N 次后打开熔断器 */
  failureThreshold: number;
  /** 熔断器打开后，等待多少毫秒进入半开状态 */
  resetTimeout?: number;
  /** 半开状态下，探测成功几次后恢复为 closed */
  halfOpenSuccessThreshold?: number;
}

export class CircuitBreaker {
  private state: CircuitState = 'closed';
  private failureCount = 0;
  private successCount = 0;
  private lastFailureTime = 0;

  private readonly failureThreshold: number;
  private readonly resetTimeout: number;
  private readonly halfOpenSuccessThreshold: number;

  constructor(options: CircuitBreakerOptions) {
    this.failureThreshold = options.failureThreshold;
    this.resetTimeout = options.resetTimeout ?? 30_000;
    this.halfOpenSuccessThreshold = options.halfOpenSuccessThreshold ?? 1;
  }

  getState(): CircuitState {
    // 自动从 open → half-open
    if (this.state === 'open' && Date.now() - this.lastFailureTime >= this.resetTimeout) {
      this.state = 'half-open';
    }
    return this.state;
  }

  /**
   * 执行操作。熔断器打开时直接走 fallback（如果提供），否则抛出 CircuitOpenError。
   */
  async execute<T>(
    action: () => Promise<T>,
    fallback?: () => Promise<T>,
  ): Promise<T> {
    const currentState = this.getState();

    if (currentState === 'open') {
      if (fallback) return fallback();
      throw new CircuitOpenError(this.failureCount);
    }

    try {
      const result = await action();
      this.onSuccess();
      return result;
    } catch (err) {
      this.onFailure();
      // 半开状态失败 → 重新打开
      if (fallback && (this.state === 'open' || this.state === 'half-open')) {
        return fallback();
      }
      throw err;
    }
  }

  /** 手动重置 */
  reset(): void {
    this.state = 'closed';
    this.failureCount = 0;
    this.successCount = 0;
  }

  // ── private ──

  private onSuccess(): void {
    if (this.state === 'half-open') {
      this.successCount++;
      if (this.successCount >= this.halfOpenSuccessThreshold) {
        this.state = 'closed';
        this.failureCount = 0;
        this.successCount = 0;
      }
    } else {
      this.failureCount = 0;
    }
  }

  private onFailure(): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();
    this.successCount = 0;

    if (this.state === 'half-open' || this.failureCount >= this.failureThreshold) {
      this.state = 'open';
    }
  }
}

// ─── DeploymentPipeline ──────────────────────────────────────────────────────

export interface PipelineStep<T = unknown> {
  name: string;
  action: () => Promise<T>;
  fallback?: () => Promise<T>;
  rollback?: () => Promise<void>;
}

export interface StepResult<T = unknown> {
  name: string;
  success: boolean;
  usedFallback: boolean;
  value?: T;
  error?: unknown;
}

export class DeploymentPipeline {
  private steps: PipelineStep[] = [];

  /** 添加部署步骤 */
  addStep(name: string, action: () => Promise<unknown>, fallback?: () => Promise<unknown>): this {
    this.steps.push({ name, action, fallback });
    return this;
  }

  /** 添加带回滚的步骤 */
  addStepWithRollback(
    name: string,
    action: () => Promise<unknown>,
    rollback: () => Promise<void>,
    fallback?: () => Promise<unknown>,
  ): this {
    this.steps.push({ name, action, fallback, rollback });
    return this;
  }

  /** 顺序执行所有步骤，失败自动 fallback，全部失败则回滚 */
  async execute(): Promise<StepResult[]> {
    const completed: StepResult[] = [];

    for (const step of this.steps) {
      const result = await this.runStep(step);
      completed.push(result);

      if (!result.success) {
        // 所有方案都失败，回滚已完成的步骤
        await this.rollback(completed);
        throw new PipelineError(step.name, result.error, completed);
      }
    }

    return completed;
  }

  /** 回滚已完成的步骤（逆序） */
  async rollback(completed?: StepResult[]): Promise<void> {
    const stepsToRollback = completed
      ? completed.filter((r) => r.success)
      : [];

    // 逆序回滚
    for (let i = stepsToRollback.length - 1; i >= 0; i--) {
      const stepName = stepsToRollback[i].name;
      const step = this.steps.find((s) => s.name === stepName);
      if (step?.rollback) {
        try {
          await step.rollback();
        } catch {
          // 回滚失败也要继续，不能停
        }
      }
    }
  }

  getStepNames(): string[] {
    return this.steps.map((s) => s.name);
  }

  // ── private ──

  private async runStep(step: PipelineStep): Promise<StepResult> {
    // 尝试主方案
    try {
      const value = await step.action();
      return { name: step.name, success: true, usedFallback: false, value };
    } catch (primaryErr) {
      // 尝试 fallback
      if (step.fallback) {
        try {
          const value = await step.fallback();
          return { name: step.name, success: true, usedFallback: true, value };
        } catch (fallbackErr) {
          return { name: step.name, success: false, usedFallback: true, error: fallbackErr };
        }
      }
      return { name: step.name, success: false, usedFallback: false, error: primaryErr };
    }
  }
}

// ─── Errors ──────────────────────────────────────────────────────────────────

export class TimeoutError extends Error {
  constructor(public readonly timeoutMs: number) {
    super(`Operation timed out after ${timeoutMs}ms`);
    this.name = 'TimeoutError';
  }
}

export class FastFailError extends Error {
  constructor(
    public readonly originalError: unknown,
    public readonly attempt: number,
  ) {
    super(`Fast fail triggered on attempt ${attempt}`);
    this.name = 'FastFailError';
  }
}

export class FallbackExhaustedError extends Error {
  constructor(
    public readonly lastError: unknown,
    public readonly totalStrategies: number,
    public readonly totalAttempts: number,
  ) {
    super(`All ${totalStrategies} fallback strategies exhausted after ${totalAttempts} attempts`);
    this.name = 'FallbackExhaustedError';
  }
}

export class CircuitOpenError extends Error {
  constructor(public readonly failureCount: number) {
    super(`Circuit breaker is open after ${failureCount} consecutive failures`);
    this.name = 'CircuitOpenError';
  }
}

export class PipelineError extends Error {
  constructor(
    public readonly failedStep: string,
    public readonly cause: unknown,
    public readonly completedSteps: StepResult[],
  ) {
    super(`Pipeline failed at step "${failedStep}"`);
    this.name = 'PipelineError';
  }
}

// ─── Utils ───────────────────────────────────────────────────────────────────

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}
