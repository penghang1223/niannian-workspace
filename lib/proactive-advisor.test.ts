/**
 * ProactiveAdvisor 测试套件
 *
 * @author 灵犀 (Lingxi) 💡
 */

import { ProactiveAdvisor, type HistoryEntry, type SuggestionContext, type TopicCategory } from './proactive-advisor';

// ─── 测试工具 ───────────────────────────────────────────────

function makeDate(hour: number, minute: number = 0, dayOffset: number = 0): Date {
  const d = new Date(2026, 2, 27, hour, minute, 0); // 2026-03-27 是周五
  if (dayOffset) d.setDate(d.getDate() + dayOffset);
  return d;
}

function makeHistory(entries: Partial<HistoryEntry>[]): HistoryEntry[] {
  return entries.map((e, i) => ({
    timestamp: e.timestamp ?? `2026-03-${String(20 + i).padStart(2, '0')}T10:00:00+08:00`,
    topic: e.topic ?? 'ai_tools',
    keywords: e.keywords ?? ['test'],
    resolved: e.resolved ?? true,
    summary: e.summary,
  }));
}

function makeContext(overrides: Partial<SuggestionContext> = {}): SuggestionContext {
  return {
    now: makeDate(8, 0),
    recentTopics: [],
    recentKeywords: [],
    pendingTasks: [],
    ...overrides,
  };
}

// ─── 测试 ───────────────────────────────────────────────────

let passed = 0;
let failed = 0;

function assert(condition: boolean, name: string) {
  if (condition) {
    passed++;
    console.log(`  ✅ ${name}`);
  } else {
    failed++;
    console.error(`  ❌ ${name}`);
  }
}

function assertIncludes(text: string, substring: string, name: string) {
  assert(text.includes(substring), name);
}

// ─── analyzePatterns 测试 ──────────────────────────────────

console.log('\n📊 analyzePatterns 测试');

{
  const advisor = new ProactiveAdvisor();

  // 空历史
  const empty = advisor.analyzePatterns([]);
  assert(empty.totalEntries === 0, '空历史 → totalEntries = 0');
  assert(empty.topTopics.length === 0, '空历史 → 无高频话题');
  assert(empty.unresolvedItems.length === 0, '空历史 → 无未完成项');
}

{
  const advisor = new ProactiveAdvisor();
  const history = makeHistory([
    { topic: 'ai_tools', keywords: ['claude', 'gpt'] },
    { topic: 'ai_tools', keywords: ['gemini'] },
    { topic: 'coding', keywords: ['typescript'] },
    { topic: 'photography', keywords: ['镜头'] },
    { topic: 'ai_tools', keywords: ['prompt'] },
  ]);
  const result = advisor.analyzePatterns(history);

  assert(result.totalEntries === 5, '总记录数 = 5');
  assert(result.topTopics[0].topic === 'ai_tools', '最高频话题 = ai_tools');
  assert(result.topTopics[0].count === 3, 'ai_tools 出现 3 次');
  assert(result.topTopics[0].percentage === 60, 'ai_tools 占比 60%');
}

{
  const advisor = new ProactiveAdvisor();
  const history = makeHistory([
    { timestamp: '2026-03-20T08:00:00+08:00', topic: 'coding', keywords: ['typescript'] },
    { timestamp: '2026-03-21T15:00:00+08:00', topic: 'ai_video', keywords: ['runway'] },
    { timestamp: '2026-03-22T20:00:00+08:00', topic: 'photography', keywords: ['修图'] },
  ]);
  const result = advisor.analyzePatterns(history);

  assert(result.timePatterns.morning.length > 0, '早上有话题记录');
  assert(result.timePatterns.afternoon.length > 0, '下午有话题记录');
  assert(result.timePatterns.evening.length > 0, '晚上有话题记录');
  assert(result.timePatterns.morning[0].topic === 'coding', '早上时段最高频 = coding');
}

{
  const advisor = new ProactiveAdvisor();
  const history = makeHistory([
    { topic: 'ai_tools', resolved: false, keywords: ['claude'] },
    { topic: 'coding', resolved: true, keywords: ['ts'] },
    { topic: 'crawling', resolved: false, keywords: ['scrapy'] },
  ]);
  const result = advisor.analyzePatterns(history);
  assert(result.unresolvedItems.length === 2, '有 2 个未完成项');
  assert(result.unresolvedItems[0].topic === 'ai_tools', '第一个未完成 = ai_tools');
}

{
  const advisor = new ProactiveAdvisor();
  // 3 次以上提问 + 关键词高度分散 → 知识盲区
  const history = makeHistory([
    { topic: 'crawling', keywords: ['scrapy'] },
    { topic: 'crawling', keywords: ['selenium'] },
    { topic: 'crawling', keywords: ['代理'] },
    { topic: 'crawling', keywords: ['反爬'] },
  ]);
  const result = advisor.analyzePatterns(history);
  assert(result.knowledgeGaps.length > 0, '识别出知识盲区');
  if (result.knowledgeGaps.length > 0) {
    assert(result.knowledgeGaps[0].topic === 'crawling', '盲区话题 = crawling');
    assert(result.knowledgeGaps[0].depth === 'shallow', '深度 = shallow');
  }
}

// ─── generateSuggestions 测试 ──────────────────────────────

console.log('\n💡 generateSuggestions 测试');

{
  const advisor = new ProactiveAdvisor();
  const suggestions = advisor.generateSuggestions(makeContext({
    now: makeDate(8, 0),
    pendingTasks: [
      { id: '1', title: '完成爬虫脚本' },
      { id: '2', title: '学习 LangChain' },
      { id: '3', title: '整理照片' },
    ],
  }));
  assert(suggestions.length > 0, '早上 8:00 有待办时有建议');
  if (suggestions.length > 0) {
    assert(suggestions[0].type === 'greeting', '类型 = greeting');
    assertIncludes(suggestions[0].message, '3', '提到 3 个任务');
    assertIncludes(suggestions[0].message, '早安', '包含早安');
  }
}

{
  const advisor = new ProactiveAdvisor();
  const suggestions = advisor.generateSuggestions(makeContext({
    now: makeDate(8, 0),
    pendingTasks: [],
  }));
  // 无待办时可能是问候或其他建议
  if (suggestions.length > 0) {
    assertIncludes(suggestions[0].message, '早安', '无待办时也有早安问候');
  }
}

{
  const advisor = new ProactiveAdvisor();
  const suggestions = advisor.generateSuggestions(makeContext({
    now: makeDate(15, 0),
    recentTopics: ['ai_video', 'coding'],
  }));
  assert(suggestions.length > 0, '下午 3:00 有建议');
  if (suggestions.length > 0) {
    assert(suggestions[0].type === 'content_recommend', '类型 = content_recommend');
    assertIncludes(suggestions[0].message, 'AI 视频', '推荐最近关注话题');
  }
}

{
  const advisor = new ProactiveAdvisor();
  const suggestions = advisor.generateSuggestions(makeContext({
    now: makeDate(23, 0),
    pendingTasks: [],
  }));
  assert(suggestions.length > 0, '晚上 11:00 有建议');
  if (suggestions.length > 0) {
    assert(suggestions[0].type === 'rest_reminder', '类型 = rest_reminder');
    assertIncludes(suggestions[0].message, '休息', '包含休息提醒');
  }
}

{
  const advisor = new ProactiveAdvisor();
  const suggestions = advisor.generateSuggestions(makeContext({
    now: makeDate(17, 30, 0), // 周五
    pendingTasks: [
      { id: '1', title: '项目部署', deadline: '2026-03-28T18:00:00+08:00' },
    ],
  }));
  const hasReview = suggestions.some(s => s.type === 'weekly_review');
  assert(hasReview, '周五下午有周回顾建议');
}

{
  const advisor = new ProactiveAdvisor();
  const suggestions = advisor.generateSuggestions(makeContext({
    now: makeDate(16, 30),
    pendingTasks: [
      { id: '1', title: '紧急修复', deadline: '2026-03-28T10:00:00+08:00' },
    ],
  }));
  const hasReminder = suggestions.some(s => s.type === 'task_reminder');
  assert(hasReminder, '下午 4:30 有紧急任务提醒');
}

// ─── shouldSuggest 测试 ────────────────────────────────────

console.log('\n🚦 shouldSuggest 测试');

{
  const advisor = new ProactiveAdvisor();
  const result = advisor.shouldSuggest(makeDate(10, 0));
  assert(result.ok, '上午 10:00 可以建议');
}

{
  const advisor = new ProactiveAdvisor();
  const result = advisor.shouldSuggest(makeDate(2, 0));
  assert(!result.ok, '凌晨 2:00 不应建议');
  assertIncludes(result.reason, '深夜', '原因包含深夜');
}

{
  const advisor = new ProactiveAdvisor();
  const result = advisor.shouldSuggest(makeDate(10, 0), true);
  assert(!result.ok, '忙碌时不应建议');
  assertIncludes(result.reason, '忙碌', '原因包含忙碌');
}

{
  const advisor = new ProactiveAdvisor();
  advisor.recordSuggestion('greeting');
  const result = advisor.shouldSuggest(new Date());
  assert(!result.ok, '刚发过建议 → 频率控制拦截');
  assertIncludes(result.reason, '频率', '原因包含频率');
}

{
  const advisor = new ProactiveAdvisor();
  // 22:30 - 23:30 是休息提醒例外
  const result = advisor.shouldSuggest(makeDate(23, 0));
  assert(result.ok, '23:00 可以发休息提醒（例外时段）');
}

// ─── 配置测试 ──────────────────────────────────────────────

console.log('\n⚙️ 配置测试');

{
  const advisor = new ProactiveAdvisor({
    schedule: { wakeHour: 6, wakeMinute: 0, sleepHour: 23, sleepMinute: 0 },
    quietHourStart: 22,
    quietHourEnd: 6,
  });
  const config = advisor.getConfig();
  assert(config.schedule.wakeHour === 6, '自定义起床时间 = 6');
  assert(config.quietHourStart === 22, '自定义静默开始 = 22');
}

{
  const advisor = new ProactiveAdvisor();
  advisor.updateConfig({ maxSuggestionsPerHour: 3 });
  assert(advisor.getConfig().maxSuggestionsPerHour === 3, '更新后每小时上限 = 3');
}

// ─── 汇总 ──────────────────────────────────────────────────

console.log(`\n${'═'.repeat(40)}`);
console.log(`  测试结果: ✅ ${passed} passed, ❌ ${failed} failed`);
console.log(`${'═'.repeat(40)}\n`);

if (failed > 0) {
  process.exit(1);
}
