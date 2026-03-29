/**
 * ProactiveAdvisor - 主动建议引擎
 * 
 * 设计目标：基于使用模式、时间上下文和主人作息，
 * 在合适的时机主动提出有价值的建议，而不是被动等待提问。
 * 
 * @author 灵犀 (Lingxi) 💡
 * @version 1.0.0
 */

// ─── 类型定义 ───────────────────────────────────────────────

/** 话题分类 */
export type TopicCategory =
  | 'ai_tools'        // AI 工具
  | 'coding'          // 编程开发
  | 'photography'     // 摄影
  | 'crawling'        // 爬虫
  | 'ai_video'        // AI 视频
  | 'ai_comic'        // AI 漫剧
  | 'productivity'    // 效率工具
  | 'daily_life'      // 日常生活
  | 'other';          // 其他

/** 时间段 */
export type TimeSlot = 'early_morning' | 'morning' | 'afternoon' | 'evening' | 'night' | 'late_night';

/** 建议类型 */
export type SuggestionType =
  | 'greeting'        // 问候
  | 'task_reminder'   // 任务提醒
  | 'content_recommend' // 内容推荐
  | 'habit_tip'       // 习惯建议
  | 'knowledge_gap'   // 知识盲区补充
  | 'rest_reminder'   // 休息提醒
  | 'weekly_review'   // 周回顾
  | 'learning_followup'; // 学习跟进

/** 建议优先级 */
export type SuggestionPriority = 'high' | 'medium' | 'low';

/** 一条历史记录 */
export interface HistoryEntry {
  /** 时间戳（ISO 8601） */
  timestamp: string;
  /** 对话话题分类 */
  topic: TopicCategory;
  /** 关键词列表 */
  keywords: string[];
  /** 是否已完成/解决 */
  resolved: boolean;
  /** 对话摘要 */
  summary?: string;
}

/** 使用模式分析结果 */
export interface PatternAnalysis {
  /** 高频话题及出现次数 */
  topTopics: Array<{ topic: TopicCategory; count: number; percentage: number }>;
  /** 时间段 → 话题分布 */
  timePatterns: Record<TimeSlot, Array<{ topic: TopicCategory; count: number }>>;
  /** 未完成的任务/话题 */
  unresolvedItems: HistoryEntry[];
  /** 知识盲区（频繁提问但未深入的话题） */
  knowledgeGaps: Array<{ topic: TopicCategory; questionCount: number; depth: 'shallow' | 'medium' }>;
  /** 分析时间范围 */
  analysisRange: { start: string; end: string };
  /** 总记录数 */
  totalEntries: number;
}

/** 建议上下文 */
export interface SuggestionContext {
  /** 当前时间 */
  now: Date;
  /** 最近 24 小时的话题 */
  recentTopics: TopicCategory[];
  /** 最近使用的关键词 */
  recentKeywords: string[];
  /** 未完成任务列表 */
  pendingTasks: Array<{ id: string; title: string; deadline?: string }>;
  /** 上次交互时间（ISO 8601） */
  lastInteractionTime?: string;
  /** 是否正在忙碌（如刚发了长消息 / 正在执行任务） */
  isBusy?: boolean;
}

/** 生成的建议 */
export interface Suggestion {
  /** 建议类型 */
  type: SuggestionType;
  /** 优先级 */
  priority: SuggestionPriority;
  /** 建议内容（Markdown） */
  message: string;
  /** 附加数据 */
  metadata?: Record<string, unknown>;
}

/** 主人作息配置 */
export interface ScheduleConfig {
  /** 起床时间（小时，24h） */
  wakeHour: number;
  /** 起床分钟 */
  wakeMinute: number;
  /** 休息时间（小时，24h） */
  sleepHour: number;
  /** 休息分钟 */
  sleepMinute: number;
}

/** 引擎配置 */
export interface AdvisorConfig {
  /** 作息 */
  schedule: ScheduleConfig;
  /** 每小时最大建议数 */
  maxSuggestionsPerHour: number;
  /** 深夜安静开始时间（小时） */
  quietHourStart: number;
  /** 深夜安静结束时间（小时） */
  quietHourEnd: number;
  /** 最小建议间隔（毫秒） */
  minIntervalMs: number;
}

// ─── 常量 ───────────────────────────────────────────────────

/** 默认作息：07:30 起床，24:00 休息 */
const DEFAULT_SCHEDULE: ScheduleConfig = {
  wakeHour: 7,
  wakeMinute: 30,
  sleepHour: 0,
  sleepMinute: 0,
};

const DEFAULT_CONFIG: AdvisorConfig = {
  schedule: DEFAULT_SCHEDULE,
  maxSuggestionsPerHour: 1,
  quietHourStart: 23,
  quietHourEnd: 7,
  minIntervalMs: 3_600_000, // 1 小时
};

// ─── 工具函数 ───────────────────────────────────────────────

/** 判断时间段 */
function getTimeSlot(hour: number): TimeSlot {
  if (hour >= 5 && hour < 7) return 'early_morning';
  if (hour >= 7 && hour < 12) return 'morning';
  if (hour >= 12 && hour < 17) return 'afternoon';
  if (hour >= 17 && hour < 21) return 'evening';
  if (hour >= 21 && hour < 23) return 'night';
  return 'late_night';
}

/** 获取星期几（0=周日） */
function getDayOfWeek(date: Date): number {
  return date.getDay();
}

/** 判断是否工作日 */
function isWeekday(date: Date): boolean {
  const dow = getDayOfWeek(date);
  return dow >= 1 && dow <= 5;
}

// ─── 核心类 ─────────────────────────────────────────────────

export class ProactiveAdvisor {
  private config: AdvisorConfig;
  private lastSuggestionTime: number = 0;
  private suggestionHistory: Array<{ time: number; type: SuggestionType }> = [];

  constructor(config: Partial<AdvisorConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  // ── 模式分析 ────────────────────────────────────────────

  /**
   * 分析使用模式
   * @param history 历史对话记录
   * @returns 模式分析结果
   */
  analyzePatterns(history: HistoryEntry[]): PatternAnalysis {
    if (history.length === 0) {
      return {
        topTopics: [],
        timePatterns: this.emptyTimePatterns(),
        unresolvedItems: [],
        knowledgeGaps: [],
        analysisRange: { start: new Date().toISOString(), end: new Date().toISOString() },
        totalEntries: 0,
      };
    }

    // 高频话题
    const topicCounts = new Map<TopicCategory, number>();
    for (const entry of history) {
      topicCounts.set(entry.topic, (topicCounts.get(entry.topic) ?? 0) + 1);
    }
    const total = history.length;
    const topTopics = [...topicCounts.entries()]
      .map(([topic, count]) => ({ topic, count, percentage: Math.round((count / total) * 100) }))
      .sort((a, b) => b.count - a.count);

    // 时间模式
    const timePatterns = this.emptyTimePatterns();
    for (const entry of history) {
      const hour = new Date(entry.timestamp).getHours();
      const slot = getTimeSlot(hour);
      const existing = timePatterns[slot].find(t => t.topic === entry.topic);
      if (existing) {
        existing.count++;
      } else {
        timePatterns[slot].push({ topic: entry.topic, count: 1 });
      }
    }
    // 排序每个时间段
    for (const slot of Object.keys(timePatterns) as TimeSlot[]) {
      timePatterns[slot].sort((a, b) => b.count - a.count);
    }

    // 未完成项
    const unresolvedItems = history.filter(e => !e.resolved);

    // 知识盲区：同一话题多次提问但问题分散（关键词重叠度低）
    const topicKeywords = new Map<TopicCategory, Set<string>>();
    for (const entry of history) {
      if (!topicKeywords.has(entry.topic)) {
        topicKeywords.set(entry.topic, new Set());
      }
      const kwSet = topicKeywords.get(entry.topic)!;
      for (const kw of entry.keywords) {
        kwSet.add(kw.toLowerCase());
      }
    }
    const knowledgeGaps: PatternAnalysis['knowledgeGaps'] = [];
    for (const [topic, count] of topicCounts) {
      const kwSet = topicKeywords.get(topic)!;
      if (count >= 3 && kwSet.size > count * 0.8) {
        // 问题多、关键词分散 → 浅层探索
        knowledgeGaps.push({
          topic,
          questionCount: count,
          depth: count >= 6 ? 'medium' : 'shallow',
        });
      }
    }

    // 时间范围
    const timestamps = history.map(e => new Date(e.timestamp).getTime()).sort((a, b) => a - b);

    return {
      topTopics,
      timePatterns,
      unresolvedItems,
      knowledgeGaps,
      analysisRange: {
        start: new Date(timestamps[0]).toISOString(),
        end: new Date(timestamps[timestamps.length - 1]).toISOString(),
      },
      totalEntries: total,
    };
  }

  // ── 建议生成 ──────────────────────────────────────────────

  /**
   * 生成主动建议
   * @param context 当前上下文
   * @returns 建议列表（按优先级排序）
   */
  generateSuggestions(context: SuggestionContext): Suggestion[] {
    const suggestions: Suggestion[] = [];
    const { now } = context;
    const hour = now.getHours();
    const minute = now.getMinutes();
    const slot = getTimeSlot(hour);
    const weekday = isWeekday(now);

    // 1. 早安问候 + 任务提醒（7:30 - 9:00）
    if (hour >= 7 && hour < 9 && minute >= (hour === 7 ? 30 : 0)) {
      const taskCount = context.pendingTasks.length;
      if (taskCount > 0) {
        const taskList = context.pendingTasks
          .slice(0, 5)
          .map(t => {
            const deadlineStr = t.deadline ? `（截止: ${this.formatRelativeDate(t.deadline)}）` : '';
            return `  - ${t.title}${deadlineStr}`;
          })
          .join('\n');
        suggestions.push({
          type: 'greeting',
          priority: 'high',
          message: `君上早安！☀️ 今天有 **${taskCount}** 个待处理事项：\n${taskList}\n\n臣随时待命，需要先处理哪个？`,
          metadata: { taskCount, weekday },
        });
      } else {
        suggestions.push({
          type: 'greeting',
          priority: 'medium',
          message: weekday
            ? '君上早安！☀️ 今天事项清空，臣建议利用空闲时间学习新技能～'
            : '君上早安！☀️ 周末愉快！今天有什么计划吗？',
          metadata: { weekday },
        });
      }
    }

    // 2. 学习跟进 / 内容推荐（下午 14:00 - 16:00）
    if (hour >= 14 && hour < 16 && context.recentTopics.length > 0) {
      const aiRelated = context.recentTopics.filter(t =>
        ['ai_tools', 'ai_video', 'ai_comic', 'coding', 'crawling'].includes(t)
      );
      if (aiRelated.length > 0) {
        const topicName = this.topicDisplayName(aiRelated[0]);
        suggestions.push({
          type: 'content_recommend',
          priority: 'medium',
          message: `检测到你最近在钻研 **${topicName}**，臣精选了一些资源：\n\n` +
            `📚 推荐深入阅读相关文档\n` +
            `💡 可以尝试用刚学到的知识做一个小项目练手\n\n` +
            `需要臣帮你整理学习笔记吗？`,
          metadata: { recentTopic: aiRelated[0] },
        });
      }
    }

    // 3. 未完成任务跟进（下午 16:00 - 18:00）
    if (hour >= 16 && hour < 18 && context.pendingTasks.length > 0) {
      const urgentTasks = context.pendingTasks.filter(t => {
        if (!t.deadline) return false;
        const dl = new Date(t.deadline).getTime();
        const nowMs = now.getTime();
        return dl - nowMs < 24 * 60 * 60 * 1000; // 24 小时内到期
      });
      if (urgentTasks.length > 0) {
        suggestions.push({
          type: 'task_reminder',
          priority: 'high',
          message: `⚠️ 君上，有 **${urgentTasks.length}** 个任务即将到期：\n` +
            urgentTasks.map(t => `  🔴 ${t.title}`).join('\n') +
            `\n\n需要臣帮你拆解任务步骤吗？`,
          metadata: { urgentCount: urgentTasks.length },
        });
      }
    }

    // 4. 晚间休息提醒（22:30 - 23:30）
    if ((hour === 22 && minute >= 30) || (hour === 23 && minute <= 30)) {
      suggestions.push({
        type: 'rest_reminder',
        priority: 'high',
        message: '🌙 君上，夜深了～明天还有战斗要打，早点休息为妙！\n\n' +
          '臣已经帮君上整理好了今日进展，明早继续不迟。晚安 💤',
        metadata: { hour },
      });
    }

    // 5. 周回顾（周五 17:00 - 19:00）
    if (weekday && getDayOfWeek(now) === 5 && hour >= 17 && hour < 19) {
      suggestions.push({
        type: 'weekly_review',
        priority: 'medium',
        message: '📋 君上，本周即将收官！臣建议花 10 分钟做个周回顾：\n\n' +
          '1. 本周完成了哪些目标？\n' +
          '2. 有哪些未完成的事项需下周跟进？\n' +
          '3. 有什么经验教训值得记录？\n\n' +
          '需要臣帮你生成周报草稿吗？',
        metadata: { weekday: 'friday' },
      });
    }

    // 6. 知识盲区提醒（任意时间，低优先级填充）
    if (suggestions.length === 0 && slot === 'morning' && context.recentKeywords.length > 0) {
      suggestions.push({
        type: 'knowledge_gap',
        priority: 'low',
        message: `💡 君上，臣注意到你最近关注了「${context.recentKeywords.slice(0, 3).join('、')}」，` +
          `要不要臣帮你做一份系统化的学习路线？`,
        metadata: { keywords: context.recentKeywords.slice(0, 3) },
      });
    }

    // 按优先级排序
    const priorityOrder: Record<SuggestionPriority, number> = { high: 0, medium: 1, low: 2 };
    suggestions.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);

    return suggestions;
  }

  // ── 时机判断 ──────────────────────────────────────────────

  /**
   * 判断当前是否适合主动建议
   * @param now 当前时间
   * @param isBusy 是否忙碌中
   * @returns 是否应该提供建议
   */
  shouldSuggest(now: Date, isBusy: boolean = false): { ok: boolean; reason: string } {
    const hour = now.getHours();
    const { quietHourStart, quietHourEnd, maxSuggestionsPerHour } = this.config;

    // 深夜静默
    if (hour >= quietHourStart || hour < quietHourEnd) {
      // 例外：休息提醒在 22:30 - 23:30 仍可触发
      const minute = now.getMinutes();
      const isRestTime = (hour === 22 && minute >= 30) || (hour === 23 && minute <= 30);
      if (!isRestTime) {
        return { ok: false, reason: `深夜静默时段 (${quietHourStart}:00 - ${quietHourEnd}:00)` };
      }
    }

    // 忙碌时不打断
    if (isBusy) {
      return { ok: false, reason: '主人正在忙碌中，不宜打扰' };
    }

    // 频率控制
    const nowMs = now.getTime();
    if (nowMs - this.lastSuggestionTime < this.config.minIntervalMs) {
      const remainingMin = Math.ceil((this.config.minIntervalMs - (nowMs - this.lastSuggestionTime)) / 60_000);
      return { ok: false, reason: `距离上次建议不足 ${remainingMin} 分钟，频率控制中` };
    }

    // 每小时上限
    const oneHourAgo = nowMs - 3_600_000;
    const recentCount = this.suggestionHistory.filter(s => s.time > oneHourAgo).length;
    if (recentCount >= maxSuggestionsPerHour) {
      return { ok: false, reason: `本小时已发出 ${recentCount} 条建议，已达上限` };
    }

    return { ok: true, reason: '适合提供建议' };
  }

  /** 记录一条建议已发出 */
  recordSuggestion(type: SuggestionType): void {
    const now = Date.now();
    this.lastSuggestionTime = now;
    this.suggestionHistory.push({ time: now, type });
    // 清理 1 小时前的记录
    const oneHourAgo = now - 3_600_000;
    this.suggestionHistory = this.suggestionHistory.filter(s => s.time > oneHourAgo);
  }

  /** 更新配置 */
  updateConfig(config: Partial<AdvisorConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /** 获取当前配置 */
  getConfig(): AdvisorConfig {
    return { ...this.config };
  }

  // ── 内部工具 ──────────────────────────────────────────────

  private emptyTimePatterns(): Record<TimeSlot, Array<{ topic: TopicCategory; count: number }>> {
    return {
      early_morning: [],
      morning: [],
      afternoon: [],
      evening: [],
      night: [],
      late_night: [],
    };
  }

  private topicDisplayName(topic: TopicCategory): string {
    const names: Record<TopicCategory, string> = {
      ai_tools: 'AI 工具',
      coding: '编程开发',
      photography: '摄影',
      crawling: '爬虫',
      ai_video: 'AI 视频',
      ai_comic: 'AI 漫剧',
      productivity: '效率工具',
      daily_life: '日常生活',
      other: '其他',
    };
    return names[topic] ?? topic;
  }

  private formatRelativeDate(isoDate: string): string {
    const date = new Date(isoDate);
    const now = new Date();
    const diffMs = date.getTime() - now.getTime();
    const diffHours = Math.round(diffMs / 3_600_000);

    if (diffHours < 0) return '已过期';
    if (diffHours < 24) return `${diffHours} 小时后`;
    const diffDays = Math.round(diffHours / 24);
    return `${diffDays} 天后`;
  }
}

export default ProactiveAdvisor;
