/**
 * 错误恢复框架 — 完整测试套件
 * 运行：npx tsx --test error-recovery.test.ts
 */

import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import {
  RetryStrategy,
  CircuitBreaker,
  DeploymentPipeline,
  TimeoutError,
  FastFailError,
  FallbackExhaustedError,
  CircuitOpenError,
  PipelineError,
} from './error-recovery.js';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function failNTimes(n: number, error = 'fail') {
  let calls = 0;
  return async () => {
    calls++;
    if (calls <= n) throw new Error(`${error} #${calls}`);
    return `success after ${n} failures`;
  };
}

// ─── RetryStrategy ───────────────────────────────────────────────────────────

describe('RetryStrategy', () => {
  it('成功操作直接返回', async () => {
    const rs = new RetryStrategy({ maxRetries: 3 });
    const result = await rs.execute(async () => 'ok');
    assert.equal(result, 'ok');
  });

  it('失败后重试成功', async () => {
    const rs = new RetryStrategy({ maxRetries: 3, initialDelay: 10 });
    const fn = failNTimes(2);
    const result = await rs.execute(fn);
    assert.equal(result, 'success after 2 failures');
  });

  it('超过 maxRetries 抛出最后的错误', async () => {
    const rs = new RetryStrategy({ maxRetries: 2, initialDelay: 10 });
    await assert.rejects(
      () => rs.execute(failNTimes(10)),
      (err: Error) => err.message.includes('fail'),
    );
  });

  it('超时抛出 TimeoutError', async () => {
    const rs = new RetryStrategy({ maxRetries: 0, timeout: 50 });
    await assert.rejects(
      () => rs.execute(() => new Promise((r) => setTimeout(() => r('late'), 500))),
      TimeoutError,
    );
  });

  it('fastFail 模式立即抛出 FastFailError', async () => {
    const rs = new RetryStrategy({
      maxRetries: 5,
      initialDelay: 100,
      fastFailPatterns: ['FATAL'],
    });
    const start = Date.now();
    await assert.rejects(
      () => rs.execute(async () => { throw new Error('FATAL: out of memory'); }),
      FastFailError,
    );
    // 应该很快失败，不会等 5 次重试
    assert.ok(Date.now() - start < 200, 'Should fail fast, not wait for retries');
  });

  it('fastFail 支持正则', async () => {
    const rs = new RetryStrategy({
      maxRetries: 5,
      initialDelay: 50,
      fastFailPatterns: [/^AUTH_FAIL/],
    });
    await assert.rejects(
      () => rs.execute(async () => { throw new Error('AUTH_FAIL: invalid token'); }),
      FastFailError,
    );
  });

  it('fallbackChain：主方案失败用备选方案', async () => {
    const rs = new RetryStrategy({ maxRetries: 1, initialDelay: 10 });
    const result = await rs.executeWithFallbacks([
      async () => { throw new Error('primary down'); },
      async () => { throw new Error('fallback-1 down'); },
      async () => 'fallback-2 works!',
    ]);
    assert.equal(result.strategyIndex, 2);
    assert.equal(result.value, 'fallback-2 works!');
  });

  it('fallbackChain：全部失败抛 FallbackExhaustedError', async () => {
    const rs = new RetryStrategy({ maxRetries: 0 });
    await assert.rejects(
      () => rs.executeWithFallbacks([
        async () => { throw new Error('A'); },
        async () => { throw new Error('B'); },
      ]),
      FallbackExhaustedError,
    );
  });
});

// ─── CircuitBreaker ──────────────────────────────────────────────────────────

describe('CircuitBreaker', () => {
  let cb: CircuitBreaker;

  beforeEach(() => {
    cb = new CircuitBreaker({
      failureThreshold: 3,
      resetTimeout: 100,
      halfOpenSuccessThreshold: 1,
    });
  });

  it('初始状态为 closed', () => {
    assert.equal(cb.getState(), 'closed');
  });

  it('连续失败 threshold 次后打开熔断器', async () => {
    for (let i = 0; i < 3; i++) {
      try {
        await cb.execute(async () => { throw new Error('boom'); });
      } catch { /* expected */ }
    }
    assert.equal(cb.getState(), 'open');
  });

  it('熔断器打开时走 fallback', async () => {
    for (let i = 0; i < 3; i++) {
      try { await cb.execute(async () => { throw new Error('boom'); }); } catch {}
    }
    const result = await cb.execute(
      async () => 'should not run',
      async () => 'fallback value',
    );
    assert.equal(result, 'fallback value');
  });

  it('熔断器打开时无 fallback 抛 CircuitOpenError', async () => {
    for (let i = 0; i < 3; i++) {
      try { await cb.execute(async () => { throw new Error('boom'); }); } catch {}
    }
    await assert.rejects(
      () => cb.execute(async () => 'nope'),
      CircuitOpenError,
    );
  });

  it('半开状态探测恢复', async () => {
    // 打开熔断器
    for (let i = 0; i < 3; i++) {
      try { await cb.execute(async () => { throw new Error('boom'); }); } catch {}
    }
    assert.equal(cb.getState(), 'open');

    // 等 resetTimeout
    await new Promise((r) => setTimeout(r, 120));
    assert.equal(cb.getState(), 'half-open');

    // 半开状态成功 → 恢复为 closed
    const result = await cb.execute(async () => 'recovered');
    assert.equal(result, 'recovered');
    assert.equal(cb.getState(), 'closed');
  });

  it('半开状态失败 → 重新打开', async () => {
    for (let i = 0; i < 3; i++) {
      try { await cb.execute(async () => { throw new Error('boom'); }); } catch {}
    }
    await new Promise((r) => setTimeout(r, 120));
    assert.equal(cb.getState(), 'half-open');

    try {
      await cb.execute(async () => { throw new Error('still broken'); });
    } catch {}

    assert.equal(cb.getState(), 'open');
  });

  it('成功操作重置失败计数', async () => {
    for (let i = 0; i < 2; i++) {
      try { await cb.execute(async () => { throw new Error('boom'); }); } catch {}
    }
    await cb.execute(async () => 'success');
    // 再失败 2 次不应该打开（因为计数已重置）
    for (let i = 0; i < 2; i++) {
      try { await cb.execute(async () => { throw new Error('boom'); }); } catch {}
    }
    assert.equal(cb.getState(), 'closed');
  });

  it('reset() 手动恢复', async () => {
    for (let i = 0; i < 3; i++) {
      try { await cb.execute(async () => { throw new Error('boom'); }); } catch {}
    }
    assert.equal(cb.getState(), 'open');
    cb.reset();
    assert.equal(cb.getState(), 'closed');
  });
});

// ─── DeploymentPipeline ──────────────────────────────────────────────────────

describe('DeploymentPipeline', () => {
  it('所有步骤成功执行', async () => {
    const log: string[] = [];
    const pipeline = new DeploymentPipeline()
      .addStep('build', async () => { log.push('build'); })
      .addStep('deploy', async () => { log.push('deploy'); })
      .addStep('verify', async () => { log.push('verify'); });

    const results = await pipeline.execute();
    assert.deepEqual(log, ['build', 'deploy', 'verify']);
    assert.equal(results.length, 3);
    assert.ok(results.every((r) => r.success));
  });

  it('步骤失败自动尝试 fallback', async () => {
    const log: string[] = [];
    const pipeline = new DeploymentPipeline()
      .addStep(
        'build',
        async () => { throw new Error('build failed'); },
        async () => { log.push('build-fallback'); },
      )
      .addStep('deploy', async () => { log.push('deploy'); });

    const results = await pipeline.execute();
    assert.deepEqual(log, ['build-fallback', 'deploy']);
    assert.equal(results[0].usedFallback, true);
    assert.equal(results[0].success, true);
  });

  it('步骤主方案和 fallback 都失败 → 回滚', async () => {
    const log: string[] = [];
    const pipeline = new DeploymentPipeline()
      .addStepWithRollback(
        'provision',
        async () => log.push('provision'),
        async () => log.push('rollback-provision'),
      )
      .addStepWithRollback(
        'deploy',
        async () => { throw new Error('deploy down'); },
        async () => log.push('rollback-deploy'),
        async () => { throw new Error('fallback also down'); },
      );

    await assert.rejects(
      () => pipeline.execute(),
      PipelineError,
    );
    // provision 应该被回滚
    assert.ok(log.includes('rollback-provision'));
  });

  it('回滚步骤本身失败不中断流水线', async () => {
    const log: string[] = [];
    const pipeline = new DeploymentPipeline()
      .addStepWithRollback(
        'step1',
        async () => log.push('step1'),
        async () => { throw new Error('rollback exploded'); log.push('never'); },
      )
      .addStep(
        'step2',
        async () => { throw new Error('step2 failed'); },
        async () => { throw new Error('fallback also failed'); },
      );

    await assert.rejects(
      () => pipeline.execute(),
      PipelineError,
    );
    // rollback 失败不会阻止错误抛出
    assert.ok(!log.includes('never'));
  });

  it('getStepNames 返回步骤名', () => {
    const pipeline = new DeploymentPipeline()
      .addStep('a', async () => {})
      .addStep('b', async () => {})
      .addStep('c', async () => {});
    assert.deepEqual(pipeline.getStepNames(), ['a', 'b', 'c']);
  });

  it('空管道直接成功', async () => {
    const results = await new DeploymentPipeline().execute();
    assert.deepEqual(results, []);
  });
});

// ─── Vercel 部署场景集成测试 ─────────────────────────────────────────────────

describe('Vercel 部署场景', () => {
  it('完整部署流程：build → deploy → verify → 全部成功', async () => {
    const log: string[] = [];
    const pipeline = new DeploymentPipeline()
      .addStep(
        'npm-build',
        async () => { log.push('build: next build'); },
      )
      .addStep(
        'vercel-deploy',
        async () => { log.push('deploy: vercel --prod'); },
      )
      .addStep(
        'health-check',
        async () => { log.push('verify: curl /api/health'); },
      );

    const results = await pipeline.execute();
    assert.equal(results.length, 3);
    assert.ok(results.every((r) => r.success && !r.usedFallback));
  });

  it('Vercel 部署失败 → fallback 到 Netlify', async () => {
    const log: string[] = [];

    const pipeline = new DeploymentPipeline()
      .addStepWithRollback(
        'npm-build',
        async () => { log.push('build'); },
        async () => { log.push('clean-build-artifacts'); },
      )
      .addStepWithRollback(
        'deploy',
        async () => { throw new Error('Vercel 502: deployment failed'); },
        async () => { log.push('rollback-vercel'); },
        async () => { log.push('fallback: netlify deploy --prod'); },
      )
      .addStep(
        'verify',
        async () => { log.push('verify: check URL responds 200'); },
      );

    const results = await pipeline.execute();
    assert.equal(results[1].usedFallback, true);
    assert.deepEqual(log, [
      'build',
      'fallback: netlify deploy --prod',
      'verify: check URL responds 200',
    ]);
  });

  it('部署 + 验证全失败 → 自动回滚', async () => {
    const log: string[] = [];

    const pipeline = new DeploymentPipeline()
      .addStepWithRollback(
        'provision-db',
        async () => { log.push('db: create migration'); },
        async () => { log.push('db: rollback migration'); },
      )
      .addStepWithRollback(
        'deploy-app',
        async () => { log.push('app: deploy'); },
        async () => { log.push('app: scale down'); },
      )
      .addStep(
        'verify',
        async () => { throw new Error('healthcheck timeout'); },
        async () => { throw new Error('retry also timed out'); },
      );

    await assert.rejects(() => pipeline.execute(), PipelineError);
    // 逆序回滚
    assert.deepEqual(log, [
      'db: create migration',
      'app: deploy',
      'app: scale down',
      'db: rollback migration',
    ]);
  });
});
