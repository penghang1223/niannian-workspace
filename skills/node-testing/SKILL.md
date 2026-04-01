---
name: node-testing
description: "Write and run tests using Node.js 25's built-in test runner (node:test). Zero dependencies — includes describe/it, mocking, coverage, expectFailure, rerun-failures, and TypeScript type stripping. Use when: writing unit/integration tests, running test suites, checking coverage, mocking functions, or testing .ts files directly."
metadata:
  {
    "openclaw":
      {
        "emoji": "🧪",
        "requires": { "bins": ["node"] },
        "compat": "Node.js >= 25.x (24.x partially supported; expectFailure requires 25.5+)",
      },
  }
---

# Node.js 25 Built-In Test Runner

Zero-dependency testing with `node:test`. No Jest, no Mocha, no Vitest — everything is built in.

## When to Use

✅ **USE this skill when:**

- Writing unit tests or integration tests for Node.js projects
- Running test suites for CLI tools, APIs, libraries
- Checking code coverage on a project
- Mocking functions, methods, or timers in tests
- Testing TypeScript files directly (type stripping)
- User says: "run the tests", "write tests for X", "test coverage", "mock something"

❌ **DON'T use this skill when:**

- Browser/frontend testing (use Playwright, Vitest browser mode)
- React component testing (use Vitest + Testing Library)
- Projects locked to Jest/Vitest (respect existing config)

## Quick Start

```bash
# Run all tests (auto-discovers *.test.js, *_test.js, etc.)
node --test

# Run specific file
node --test src/math.test.js

# Run with coverage
node --test --experimental-test-coverage
```

## Core APIs

### describe / it (BDD-style)

```js
import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert';

describe('Calculator', () => {
  let calc;

  beforeEach(() => {
    calc = { add: (a, b) => a + b };
  });

  it('should add two numbers', () => {
    assert.strictEqual(calc.add(2, 3), 5);
  });

  it('should handle negatives', () => {
    assert.strictEqual(calc.add(-1, 1), 0);
  });

  describe('nested suite', () => {
    it('works inside describe', () => {
      assert.ok(true);
    });
  });
});
```

**Aliases:** `describe` = `suite`, `it` = `test`. Use whichever you prefer.

### test() (functional style)

```js
import test from 'node:test';
import assert from 'node:assert';

test('synchronous', () => {
  assert.strictEqual(1, 1);
});

test('async', async () => {
  const result = await fetch('https://example.com');
  assert.ok(result.ok);
});

test('callback', (t, done) => {
  setTimeout(done, 100);
});
```

### Subtests

```js
test('parent', async (t) => {
  await t.test('child 1', () => { /* ... */ });
  await t.test('child 2', () => { /* ... */ });
});
```

## Built-In Mocking

No `jest.fn()` needed. Mocking is built into `node:test`.

### Mock Functions (Spy)

```js
import { mock, test } from 'node:test';
import assert from 'node:assert';

test('spy on a function', () => {
  const fn = mock.fn((a, b) => a + b);

  assert.strictEqual(fn(3, 4), 7);
  assert.strictEqual(fn.mock.callCount(), 1);

  const call = fn.mock.calls[0];
  assert.deepStrictEqual(call.arguments, [3, 4]);
  assert.strictEqual(call.result, 7);

  mock.reset(); // Reset all globally tracked mocks
});
```

### Mock Methods (auto-restore via test context)

```js
test('mock object method', (t) => {
  const obj = {
    value: 5,
    add(a) { return this.value + a; }
  };

  t.mock.method(obj, 'add');
  obj.add(3);

  assert.strictEqual(obj.add.mock.callCount(), 1);
  assert.deepStrictEqual(obj.add.mock.calls[0].arguments, [3]);

  // Auto-restored when test finishes — no manual cleanup needed
});
```

### Mock Timers

```js
import { mock, test } from 'node:test';
import assert from 'node:assert';

test('mock setTimeout', () => {
  const fn = mock.fn();

  mock.timers.enable({ apis: ['setTimeout'] });
  setTimeout(fn, 9999);
  assert.strictEqual(fn.mock.callCount(), 0);

  mock.timers.tick(9999); // Fast-forward time
  assert.strictEqual(fn.mock.callCount(), 1);

  mock.timers.reset();
  mock.reset();
});
```

Supported timer APIs: `setTimeout`, `setInterval`, `Date.now()`, `Date` constructor, `setImmediate`.

### Mock Modules (getters/setters)

```js
test('mock getter', (t) => {
  const obj = { get val() { return 'real'; } };
  t.mock.getter(obj, 'val', () => 'mocked');

  assert.strictEqual(obj.val, 'mocked');
});
```

## Test Options

### Skipping Tests

```js
// Skip via option
it('skipped', { skip: true }, () => { /* never runs */ });
it('skipped with reason', { skip: 'bug #123' }, () => {});

// Skip via method
it('also skipped', (t) => {
  t.skip();           // no message
  t.skip('reason');   // with message
});

// Skip entire suite
describe.skip('skipped suite', () => { /* ... */ });
```

### TODO Tests (expected failures, v25.5+)

TODO tests execute but **don't fail the suite**. Use for pending work.

```js
it('not yet implemented', { todo: true }, () => {
  throw new Error('this does NOT fail the test');
});

it('with message', { todo: 'needs refactoring' }, () => {});
```

### `expectFailure` — Mark Known Bugs (v25.5+)

**🔄 Reversed logic:** The test **must throw** to pass. If it doesn't throw (i.e., it runs clean), it **fails**.

Perfect for tracking known bugs: when the bug is fixed, the test starts failing — alerting you to remove the flag.

```js
// Basic: any failure = pass
it.expectFailure('known bug: fails intermittently', () => {
  assert.strictEqual(buggyFunction(), expected);
});

// With options object
it('known bug', { expectFailure: true }, () => {
  assert.strictEqual(buggyFunction(), expected);
});

// With reason string
it('known bug', { expectFailure: 'feature not implemented' }, () => {
  assert.strictEqual(buggyFunction(), expected);
});

// Match specific error (regex)
it('fails with specific error', { expectFailure: /timeout/i }, () => {
  throw new Error('Connection timeout');
});

// Match specific error (object shape)
it('error code match', { expectFailure: { code: 'ERR_EXPECTED' } }, () => {
  const err = new Error('boom');
  err.code = 'ERR_EXPECTED';
  throw err; // matches → test passes
});

// Both reason AND specific error
it('specific failure', {
  expectFailure: { label: 'known bug', match: /error msg/ }
}, () => {
  throw new Error('error msg here');
});
```

**Priority:** `skip` > `todo` > `expectFailure`. If a test has both `skip` and `expectFailure`, it's skipped.

### Only Tests (focused runs)

```bash
# Must pass --test-only flag
node --test --test-only
```

```js
it.only('only this runs', () => { /* ... */ });
describe.only('only this suite', () => { /* ... */ });
```

### Filtering by Name Pattern

```bash
# Run tests matching regex
node --test --test-name-pattern="should add"
node --test --test-name-pattern="/should add/i"

# Skip tests matching regex
node --test --test-skip-pattern="slow"
```

## Code Coverage

```bash
# Basic coverage (spec reporter shows summary)
node --test --experimental-test-coverage

# Generate lcov report
node --test --experimental-test-coverage \
  --test-reporter=lcov \
  --test-reporter-destination=coverage.info

# Include node_modules in coverage
node --test --experimental-test-coverage \
  --test-coverage-include="**/*.js"

# Exclude specific paths
node --test --experimental-test-coverage \
  --test-coverage-exclude="**/migrations/**"
```

### Inline Coverage Control

```js
/* node:coverage disable */
// Lines here are ignored for coverage
/* node:coverage enable */

/* node:coverage ignore next */
if (neverReached) { console.log('nope'); }

/* node:coverage ignore next 3 */
if (neverReached) {
  console.log('line 1');
  console.log('line 2');
}
```

## `--test-rerun-failures` — Only Rerun Failed Tests

Instead of re-running the entire suite, persist state and only re-run what failed:

```bash
# First run: saves state to a file
node --test --test-rerun-failures ./test-state.json

# Second run: only re-runs tests that failed
node --test --test-rerun-failures ./test-state.json

# Third run: keeps narrowing down
node --test --test-rerun-failures ./test-state.json
```

The state file is JSON tracking which tests passed on which attempt. Each subsequent run skips passing tests and only re-executes failures. Great for CI flaky-test retry loops.

## TypeScript — Type Stripping (Zero Config)

Node.js 25 has **built-in type stripping**. No `ts-node`, no `tsx`, no transpile step.

```bash
# Run .ts test files directly (type stripping is ON by default in Node 25)
node --test src/utils.test.ts

# Explicitly disable type stripping
node --test --no-strip-types src/utils.test.ts
```

**Auto-discovery of `.ts` test files** (when type stripping is enabled):
- `*.test.{cts,mts,ts}`
- `*-test.{cts,mts,ts}`
- `*_test.{cts,mts,ts}`
- `test-*.{cts,mts,ts}`
- `test.{cts,mts,ts}`
- `test/**/*.{cts,mts,ts}`

**Limitations:** Type stripping removes types but does NOT check them. Run `tsc --noEmit` separately for type checking.

```ts
// math.test.ts — runs directly with node --test
import { describe, it } from 'node:test';
import assert from 'node:assert';

function add(a: number, b: number): number {
  return a + b;
}

describe('add', () => {
  it('sums correctly', () => {
    assert.strictEqual(add(2, 3), 5);
  });
});
```

## Watch Mode

```bash
node --test --watch
```

Automatically re-runs tests when files change. Good for TDD workflow.

## Global Setup / Teardown (v24+)

```js
// setup.js
export async function globalSetup() {
  console.log('Starting DB...');
  // await startDatabase();
}

export async function globalTeardown() {
  console.log('Stopping DB...');
  // await stopDatabase();
}
```

```bash
node --test --test-global-setup=./setup.js
```

## Reporters

```bash
# Spec (default, human-readable)
node --test --test-reporter=spec

# TAP (machine-readable)
node --test --test-reporter=tap

# LCOV (for coverage tools)
node --test --experimental-test-coverage --test-reporter=lcov --test-reporter-destination=lcov.info

# Dot (minimal)
node --test --test-reporter=dot
```

## Key Flags Reference

| Flag | Description |
|------|-------------|
| `--test` | Enable test runner, auto-discover test files |
| `--test-concurrency=N` | Max parallel child processes (default: CPU count) |
| `--test-name-pattern=REGEX` | Run only tests matching pattern |
| `--test-skip-pattern=REGEX` | Skip tests matching pattern |
| `--test-only` | Only run tests with `{ only: true }` |
| `--test-rerun-failures=FILE` | Persist state, only rerun failed tests |
| `--test-reporter=TYPE` | Output format: spec, tap, dot, lcov |
| `--test-reporter-destination=FILE` | Reporter output destination |
| `--test-global-setup=FILE` | Global setup/teardown module |
| `--experimental-test-coverage` | Enable code coverage collection |
| `--test-coverage-include=GLOB` | Coverage include pattern |
| `--test-coverage-exclude=GLOB` | Coverage exclude pattern |
| `--watch` | Re-run tests on file changes |
| `--test-force-exit` | Force exit after tests complete |
| `--experimental-strip-types` | Enable TS type stripping (default in Node 25) |
| `--no-strip-types` | Disable type stripping |
