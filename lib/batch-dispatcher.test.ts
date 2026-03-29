/**
 * BatchDispatcher 测试套件
 * 
 * 使用 Node.js 内置 test runner (node:test) + assert
 * 运行: node --test lib/batch-dispatcher.test.ts
 * 
 * @author Karl (Dev Engineer) 🛠️
 */

import { describe, it, beforeEach, mock } from 'node:test';
import assert from 'node:assert/strict';
import {
  BatchDispatcher,
  TimeoutError,
  quickDispatch,
  type SpawnFunction,
  type TaskResult,
  type WaveResult,
} from './batch-dispatcher.js';

// ─── 测试工具 ─────────────────────────────────────────────

/** 创建一个 mock spawn 函数 */
function createMockSpawn(
  behavior: 'success' | 'fail' | 'delay' | 'mixed' = 'success',
  delayMs = 50
): SpawnFunction {
  return async ({ agentId, label }) => {
    if (behavior === 'delay') {
      await new Promise(r => setTimeout(r, delayMs));
    }

    if (behavior === 'fail') {
      throw new Error(`Agent ${agentId} failed`);
    }

    if (behavior === 'mixed' && label?.includes('fail')) {
      throw new Error(`Agent ${agentId} failed`);
    }

    return { result: { agentId, label, status: 'done' } };
  };
}

/** 创建一个超时的 mock spawn */
function createTimeoutSpawn(timeoutMs = 100): SpawnFunction {
  return async () => {
    await new Promise(r => setTimeout(r, timeoutMs + 50));
    return { result: 'should not reach' };
  };
}

// ─── 测试套件 ─────────────────────────────────────────────

describe('BatchDispatcher', () => {
  let dispatcher: BatchDispatcher;

  beforeEach(() => {
    dispatcher = new BatchDispatcher({
      spawnFn: createMockSpawn(),
      defaultTimeout: 5000,
    });
  });

  // ─── 基础 API 测试 ─────────────────────────────────────

  describe('基础 API', () => {
    it('应该支持链式调用', () => {
      const result = dispatcher
        .addTask('task1', 'agent1', 'test task 1')
        .addTask('task2', 'agent2', 'test task 2');

      assert.strictEqual(result, dispatcher);
    });

    it('应该拒绝重复标签', () => {
      dispatcher.addTask('task1', 'agent1', 'test task 1');

      assert.throws(
        () => dispatcher.addTask('task1', 'agent2', 'test task 2'),
        { message: /already exists/ }
      );
    });

    it('空任务时执行应该报错', async () => {
      await assert.rejects(
        () => dispatcher.execute(),
        { message: /No tasks to execute/ }
      );
    });

    it('执行中不能添加任务', async () => {
      dispatcher.addTask('task1', 'agent1', 'test');
      const promise = dispatcher.execute();

      assert.throws(
        () => dispatcher.addTask('task2', 'agent2', 'test2'),
        { message: /Cannot call addTask.*while executing/ }
      );

      await promise;
    });

    it('应该返回正确进度', () => {
      dispatcher
        .addTask('task1', 'agent1', 'test 1')
        .addTask('task2', 'agent2', 'test 2')
        .addTask('task3', 'agent3', 'test 3');

      const progress = dispatcher.getProgress();
      assert.strictEqual(progress.total, 3);
      assert.strictEqual(progress.completed, 0);
      assert.strictEqual(progress.percentage, 0);
    });

    it('应该能获取任务列表', () => {
      dispatcher
        .addTask('task1', 'agent1', 'test 1')
        .addTask('task2', 'agent2', 'test 2');

      const tasks = dispatcher.getTasks();
      assert.strictEqual(tasks.length, 2);
      assert.strictEqual(tasks[0].label, 'task1');
      assert.strictEqual(tasks[1].label, 'task2');
    });

    it('应该能移除任务', () => {
      dispatcher
        .addTask('task1', 'agent1', 'test 1')
        .addTask('task2', 'agent2', 'test 2');

      dispatcher.removeTask('task1');
      assert.strictEqual(dispatcher.getTasks().length, 1);
      assert.strictEqual(dispatcher.getTask('task1'), undefined);
    });

    it('reset 应该清空所有状态', () => {
      dispatcher
        .addTask('task1', 'agent1', 'test 1')
        .onComplete(() => {});

      dispatcher.reset();
      assert.strictEqual(dispatcher.getTasks().length, 0);
    });
  });

  // ─── 单波次并行执行 ─────────────────────────────────────

  describe('单波次并行执行', () => {
    it('多个无依赖任务应该并行执行', async () => {
      const executionOrder: string[] = [];

      const trackSpawn: SpawnFunction = async ({ label }) => {
        executionOrder.push(`start:${label}`);
        await new Promise(r => setTimeout(r, 30));
        executionOrder.push(`end:${label}`);
        return { result: label };
      };

      const d = new BatchDispatcher({ spawnFn: trackSpawn });

      d.addTask('A', 'agent1', 'task A');
      d.addTask('B', 'agent2', 'task B');
      d.addTask('C', 'agent3', 'task C');

      const results = await d.execute();

      // 应该只有一个波次
      assert.strictEqual(results.length, 1);
      // 波次内所有任务都完成
      assert.strictEqual(results[0].tasks.length, 3);
      assert.ok(results[0].success);

      // 验证并行：所有 start 应该在所有 end 之前
      const starts = executionOrder.filter(e => e.startsWith('start'));
      const ends = executionOrder.filter(e => e.startsWith('end'));
      assert.strictEqual(starts.length, 3);
      assert.strictEqual(ends.length, 3);
    });

    it('addWave 应该将任务放入同一波次', async () => {
      const d = new BatchDispatcher({ spawnFn: createMockSpawn() });

      d.addWave([
        { label: 'A', agentId: 'agent1', task: 'task A' },
        { label: 'B', agentId: 'agent2', task: 'task B' },
      ]);

      const results = await d.execute();
      assert.strictEqual(results.length, 1);
      assert.strictEqual(results[0].tasks.length, 2);
    });
  });

  // ─── 多波次串行执行 ─────────────────────────────────────

  describe('多波次串行执行', () => {
    it('有依赖的任务应该分波次执行', async () => {
      const executionOrder: string[] = [];

      const trackSpawn: SpawnFunction = async ({ label }) => {
        executionOrder.push(label);
        return { result: label };
      };

      const d = new BatchDispatcher({ spawnFn: trackSpawn });

      d.addTask('A', 'agent1', 'task A');
      d.addTask('B', 'agent2', 'task B', { dependsOn: ['A'] });
      d.addTask('C', 'agent3', 'task C', { dependsOn: ['A'] });
      d.addTask('D', 'agent4', 'task D', { dependsOn: ['B', 'C'] });

      const results = await d.execute();

      // 应该有 3 个波次: [A], [B, C], [D]
      assert.strictEqual(results.length, 3);

      // 波次 0: 只有 A
      assert.deepStrictEqual(
        results[0].tasks.map(t => t.label).sort(),
        ['A']
      );

      // 波次 1: B 和 C
      assert.deepStrictEqual(
        results[1].tasks.map(t => t.label).sort(),
        ['B', 'C']
      );

      // 波次 2: 只有 D
      assert.deepStrictEqual(
        results[2].tasks.map(t => t.label).sort(),
        ['D']
      );
    });

    it('多波次应该串行执行（后一波次等前一波次完成）', async () => {
      const timeline: Array<{ event: string; time: number }> = [];
      const start = Date.now();

      const trackSpawn: SpawnFunction = async ({ label }) => {
        timeline.push({ event: `start:${label}`, time: Date.now() - start });
        await new Promise(r => setTimeout(r, 20));
        timeline.push({ event: `end:${label}`, time: Date.now() - start });
        return { result: label };
      };

      const d = new BatchDispatcher({ spawnFn: trackSpawn });

      d.addTask('A', 'agent1', 'task A');
      d.addTask('B', 'agent2', 'task B', { dependsOn: ['A'] });

      await d.execute();

      // A 的 end 应该在 B 的 start 之前
      const aEnd = timeline.find(t => t.event === 'end:A')!.time;
      const bStart = timeline.find(t => t.event === 'start:B')!.time;
      assert.ok(bStart >= aEnd, `B started (${bStart}) before A ended (${aEnd})`);
    });
  });

  // ─── 依赖关系自动分波 ───────────────────────────────────

  describe('依赖关系自动分波', () => {
    it('简单链式依赖应该正确分波', async () => {
      const d = new BatchDispatcher({ spawnFn: createMockSpawn() });

      d.addTask('step1', 'agent1', '第一步');
      d.addTask('step2', 'agent2', '第二步', { dependsOn: ['step1'] });
      d.addTask('step3', 'agent3', '第三步', { dependsOn: ['step2'] });

      const results = await d.execute();

      assert.strictEqual(results.length, 3);
      assert.deepStrictEqual(results[0].tasks.map(t => t.label), ['step1']);
      assert.deepStrictEqual(results[1].tasks.map(t => t.label), ['step2']);
      assert.deepStrictEqual(results[2].tasks.map(t => t.label), ['step3']);
    });

    it('钻石依赖应该正确分波', async () => {
      //     A
      //    / \
      //   B   C
      //    \ /
      //     D
      const d = new BatchDispatcher({ spawnFn: createMockSpawn() });

      d.addTask('A', 'agent', 'top');
      d.addTask('B', 'agent', 'left', { dependsOn: ['A'] });
      d.addTask('C', 'agent', 'right', { dependsOn: ['A'] });
      d.addTask('D', 'agent', 'bottom', { dependsOn: ['B', 'C'] });

      const results = await d.execute();

      assert.strictEqual(results.length, 3);
      assert.deepStrictEqual(results[0].tasks.map(t => t.label), ['A']);
      assert.deepStrictEqual(results[1].tasks.map(t => t.label).sort(), ['B', 'C']);
      assert.deepStrictEqual(results[2].tasks.map(t => t.label), ['D']);
    });

    it('多个独立链应该并行', async () => {
      //  chain1: A -> B
      //  chain2: C -> D
      const d = new BatchDispatcher({ spawnFn: createMockSpawn() });

      d.addTask('A', 'agent', 'A');
      d.addTask('B', 'agent', 'B', { dependsOn: ['A'] });
      d.addTask('C', 'agent', 'C');
      d.addTask('D', 'agent', 'D', { dependsOn: ['C'] });

      const results = await d.execute();

      assert.strictEqual(results.length, 2);
      // 波次 0: A 和 C
      assert.deepStrictEqual(results[0].tasks.map(t => t.label).sort(), ['A', 'C']);
      // 波次 1: B 和 D
      assert.deepStrictEqual(results[1].tasks.map(t => t.label).sort(), ['B', 'D']);
    });
  });

  // ─── 超时和重试 ─────────────────────────────────────────

  describe('超时和重试', () => {
    it('任务超时应该标记为 timeout', async () => {
      const d = new BatchDispatcher({
        spawnFn: createTimeoutSpawn(200),
        defaultTimeout: 100,
      });

      d.addTask('slow', 'agent', 'slow task');

      const results = await d.execute();

      assert.strictEqual(results[0].tasks[0].status, 'timeout');
      assert.ok(!results[0].success);
    });

    it('超时后应该重试', async () => {
      let attempts = 0;

      const flakySpawn: SpawnFunction = async () => {
        attempts++;
        if (attempts < 3) {
          await new Promise(r => setTimeout(r, 200)); // 超时
        }
        return { result: 'success on attempt ' + attempts };
      };

      const d = new BatchDispatcher({
        spawnFn: flakySpawn,
        defaultTimeout: 50,
        defaultMaxRetries: 3,
        defaultRetryDelay: 10,
      });

      d.addTask('flaky', 'agent', 'flaky task');

      const results = await d.execute();

      assert.strictEqual(attempts, 3);
      assert.strictEqual(results[0].tasks[0].status, 'completed');
      assert.strictEqual(results[0].tasks[0].retryCount, 2);
    });

    it('重试耗尽应该标记为失败', async () => {
      const failSpawn: SpawnFunction = async () => {
        throw new Error('always fail');
      };

      const d = new BatchDispatcher({
        spawnFn: failSpawn,
        defaultMaxRetries: 2,
        defaultRetryDelay: 10,
      });

      d.addTask('failing', 'agent', 'always fail');

      const results = await d.execute();

      // maxRetries=2: 1次初始 + 2次重试 = 3次尝试, retryCount 最终为 3
      assert.strictEqual(results[0].tasks[0].status, 'failed');
      assert.strictEqual(results[0].tasks[0].retryCount, 3);
    });

    it('单个任务选项应该覆盖全局配置', async () => {
      let attempts = 0;

      const countSpawn: SpawnFunction = async () => {
        attempts++;
        throw new Error('fail');
      };

      const d = new BatchDispatcher({
        spawnFn: countSpawn,
        defaultMaxRetries: 0, // 全局不重试
      });

      d.addTask('custom', 'agent', 'task', {
        maxRetries: 3, // 该任务重试 3 次
        retryDelay: 5,
      });

      const results = await d.execute();

      // 应该尝试 1 + 3 = 4 次
      assert.strictEqual(attempts, 4);
      assert.strictEqual(results[0].tasks[0].status, 'failed');
    });
  });

  // ─── 回调测试 ───────────────────────────────────────────

  describe('回调', () => {
    it('onComplete 应该在所有波次完成后触发', async () => {
      let completed = false;
      let waveCount = 0;

      const d = new BatchDispatcher({ spawnFn: createMockSpawn() });

      d.addTask('A', 'agent', 'A');
      d.addTask('B', 'agent', 'B', { dependsOn: ['A'] });

      d.onWaveComplete(() => {
        waveCount++;
      });

      d.onComplete((results) => {
        completed = true;
        assert.strictEqual(results.length, 2);
      });

      await d.execute();

      assert.ok(completed);
      assert.strictEqual(waveCount, 2);
    });

    it('onWaveComplete 应该针对指定波次触发', async () => {
      const triggered: number[] = [];

      const d = new BatchDispatcher({ spawnFn: createMockSpawn() });

      d.addTask('A', 'agent', 'A');
      d.addTask('B', 'agent', 'B', { dependsOn: ['A'] });
      d.addTask('C', 'agent', 'C', { dependsOn: ['B'] });

      d.onWaveComplete((_result, waveIndex) => {
        triggered.push(waveIndex);
      }, 1); // 只监听波次 1

      await d.execute();

      assert.deepStrictEqual(triggered, [1]);
    });

    it('onProgress 应该报告进度', async () => {
      const progressSnapshots: number[] = [];

      const d = new BatchDispatcher({ spawnFn: createMockSpawn() });

      d.addTask('A', 'agent', 'A');
      d.addTask('B', 'agent', 'B');

      d.onProgress((progress) => {
        progressSnapshots.push(progress.percentage);
      });

      await d.execute();

      // 最后一次进度应该显示 100%
      assert.strictEqual(progressSnapshots[progressSnapshots.length - 1], 100);
    });

    it('回调异常不应该中断执行', async () => {
      const d = new BatchDispatcher({ spawnFn: createMockSpawn() });

      d.addTask('A', 'agent', 'A');

      d.onComplete(() => {
        throw new Error('callback error');
      });

      // 不应该抛出异常
      const results = await d.execute();
      assert.strictEqual(results[0].tasks[0].status, 'completed');
    });
  });

  // ─── stopOnWaveFailure ──────────────────────────────────

  describe('stopOnWaveFailure', () => {
    it('波次失败时应该停止后续波次', async () => {
      const executed: string[] = [];

      const trackSpawn: SpawnFunction = async ({ label }) => {
        executed.push(label!);
        if (label === 'fail') throw new Error('fail');
        return { result: label };
      };

      const d = new BatchDispatcher({
        spawnFn: trackSpawn,
        stopOnWaveFailure: true,
      });

      d.addTask('fail', 'agent', 'will fail');
      d.addTask('never', 'agent', 'should not run', { dependsOn: ['fail'] });

      const results = await d.execute();

      assert.strictEqual(results.length, 1);
      assert.ok(!results[0].success);
      assert.deepStrictEqual(executed, ['fail']);
    });
  });

  // ─── quickDispatch 工具函数 ─────────────────────────────

  describe('quickDispatch', () => {
    it('应该快速创建并执行调度', async () => {
      const results = await quickDispatch(
        [
          { label: 'pm', agentId: 'product_manager', task: '分析需求' },
          { label: 'dev', agentId: 'dev_engineer', task: '设计方案', options: { dependsOn: ['pm'] } },
        ],
        { spawnFn: createMockSpawn() }
      );

      assert.strictEqual(results.length, 2);
      assert.deepStrictEqual(results[0].tasks.map(t => t.label), ['pm']);
      assert.deepStrictEqual(results[1].tasks.map(t => t.label), ['dev']);
    });
  });

  // ─── 进度追踪 ───────────────────────────────────────────

  describe('进度追踪', () => {
    it('应该准确追踪完成/失败/运行中', async () => {
      const d = new BatchDispatcher({
        spawnFn: createMockSpawn('mixed'),
        defaultMaxRetries: 0,
      });

      d.addTask('success', 'agent', 'ok');
      d.addTask('fail-task', 'agent', 'will fail');

      const results = await d.execute();
      const progress = d.getProgress();

      assert.strictEqual(progress.total, 2);
      assert.strictEqual(progress.completed, 1);
      assert.strictEqual(progress.failed, 1);
      assert.strictEqual(progress.percentage, 50);
    });

    it('波次信息应该正确', async () => {
      const d = new BatchDispatcher({ spawnFn: createMockSpawn() });

      d.addTask('A', 'agent', 'A');
      d.addTask('B', 'agent', 'B', { dependsOn: ['A'] });

      await d.execute();

      const progress = d.getProgress();
      assert.strictEqual(progress.currentWave, 2);
      assert.strictEqual(progress.totalWaves, 2);
    });
  });
});
