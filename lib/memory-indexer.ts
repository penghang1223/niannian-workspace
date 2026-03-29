/**
 * MemoryIndex - 智能记忆检索系统
 *
 * 解决问题：MEMORY.md 每次全量加载浪费 token。
 * 方案：基于 TF-IDF 的关键词搜索 + 结构化分区索引，
 *       仅加载相关片段，大幅降低 token 消耗。
 *
 * @author Karl (Dev Engineer) 🛠️
 * @version 1.0.0
 */

import * as fs from 'fs';
import * as path from 'path';

// ─── 类型定义 ───────────────────────────────────────────────

/** 记忆分类 */
export type MemoryCategory = '技术' | '工作流' | '主人偏好' | '安全' | '日志' | '其他';

/** 索引条目 */
export interface IndexEntry {
  /** 唯一 ID */
  id: string;
  /** 来源文件路径 */
  filePath: string;
  /** 起始行号（1-indexed） */
  startLine: number;
  /** 结束行号（1-indexed） */
  endLine: number;
  /** 标题/摘要 */
  title: string;
  /** 完整文本内容 */
  content: string;
  /** 分类 */
  category: MemoryCategory;
  /** 关联日期（从文件名或内容提取） */
  date?: string;
  /** 词频统计（term -> count） */
  termFreq: Map<string, number>;
  /** 标签（从标题和内容提取） */
  tags: string[];
}

/** 搜索选项 */
export interface SearchOptions {
  /** 返回结果数量上限，默认 5 */
  topK?: number;
  /** 按分类过滤 */
  category?: MemoryCategory;
  /** 日期范围过滤 */
  dateRange?: { from?: string; to?: string };
  /** 最低相关度阈值（0-1），默认 0 */
  minScore?: number;
}

/** 搜索结果 */
export interface SearchResult {
  /** 匹配的索引条目 */
  entry: IndexEntry;
  /** 相关度评分（0-1） */
  score: number;
  /** 匹配的关键词 */
  matchedTerms: string[];
}

/** 索引统计 */
export interface IndexStats {
  /** 总条目数 */
  totalEntries: number;
  /** 索引的文件数 */
  totalFiles: number;
  /** 各分类条目数 */
  categoryCounts: Record<MemoryCategory, number>;
  /** 总词数 */
  totalTerms: number;
  /** 索引构建时间（ISO） */
  builtAt: string;
  /** 索引的文件列表 */
  indexedFiles: string[];
}

/** 索引配置 */
export interface IndexerConfig {
  /** MEMORY.md 路径 */
  memoryPath: string;
  /** memory/ 目录路径 */
  memoryDirPath: string;
  /** 停用词列表 */
  stopWords?: Set<string>;
  /** 文件过滤器（返回 true 则索引该文件） */
  fileFilter?: (fileName: string) => boolean;
}

// ─── 工具函数 ───────────────────────────────────────────────

/** 默认中文 + 英文停用词 */
const DEFAULT_STOP_WORDS = new Set([
  // 中文停用词
  '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
  '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
  '自己', '这', '他', '她', '它', '们', '那', '被', '从', '把', '对', '为', '与',
  '而', '但', '或', '及', '等', '如', '比', '向', '已', '将', '用', '于', '之',
  '其', '又', '所', '以', '可', '能', '还', '更', '最', '因', '此', '些', '种',
  '该', '让', '给', '做', '过', '来', '起', '得', '地', '之', '后', '前', '中',
  '下', '时', '年', '月', '日',
  // 英文停用词
  'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
  'should', 'may', 'might', 'shall', 'can', 'need', 'dare', 'ought',
  'and', 'but', 'or', 'nor', 'not', 'no', 'so', 'if', 'then', 'than',
  'too', 'very', 'just', 'about', 'above', 'after', 'again', 'all',
  'also', 'am', 'any', 'because', 'before', 'between', 'both', 'each',
  'few', 'from', 'further', 'get', 'got', 'here', 'how', 'i', 'in',
  'into', 'it', 'its', 'itself', 'me', 'more', 'most', 'my', 'myself',
  'now', 'of', 'off', 'on', 'once', 'one', 'only', 'other', 'our',
  'out', 'over', 'own', 'same', 'she', 'he', 'some', 'such', 'take',
  'tell', 'that', 'their', 'them', 'there', 'these', 'they', 'this',
  'those', 'through', 'to', 'under', 'until', 'up', 'us', 'want',
  'we', 'what', 'when', 'where', 'which', 'while', 'who', 'whom',
  'why', 'with', 'you', 'your',
]);

/**
 * 中文分词 + 英文 tokenizer
 * 简单实现：中文按字符/词组切分，英文按空格+标点切分
 */
export function tokenize(text: string): string[] {
  const tokens: string[] = [];
  // 先统一转小写
  const lower = text.toLowerCase();

  // 正则：匹配中文词组（连续中文字符）、英文单词、日期、版本号等
  const pattern = /[\u4e00-\u9fff]{1,6}|[a-z][a-z0-9_\-]{1,30}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|v?\d+\.\d+(\.\d+)?/gi;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(lower)) !== null) {
    const token = match[0];
    // 英文：进一步按连字符/下划线拆分
    if (/^[a-z]/.test(token)) {
      const sub = token.split(/[-_]/).filter(s => s.length > 0);
      tokens.push(...sub);
    } else {
      tokens.push(token);
    }
  }

  return tokens;
}

/**
 * 解析 Markdown 标题层级为分区
 * 返回每个分区的 { title, startLine, endLine, level }
 */
function parseSections(lines: string[]): Array<{ title: string; startLine: number; endLine: number; level: number }> {
  const sections: Array<{ title: string; startLine: number; endLine: number; level: number }> = [];
  const headingRegex = /^(#{1,6})\s+(.+)/;

  for (let i = 0; i < lines.length; i++) {
    const match = lines[i].match(headingRegex);
    if (match) {
      const level = match[1].length;
      const title = match[2].trim();
      sections.push({ title, startLine: i + 1, endLine: i + 1, level });
    }
  }

  // 计算每个分区的结束行
  for (let i = 0; i < sections.length; i++) {
    const nextSameOrHigher = sections.findIndex(
      (s, idx) => idx > i && s.level <= sections[i].level
    );
    sections[i].endLine = nextSameOrHigher === -1 ? lines.length : sections[nextSameOrHigher].startLine - 1;
  }

  return sections;
}

/**
 * 从标题和内容推断分类
 */
function inferCategory(title: string, content: string): MemoryCategory {
  const text = `${title} ${content}`.toLowerCase();

  // 安全相关
  if (/安全|密码|密钥|token|权限|授权|oauth|secret|credential|禁止|危险|删除/i.test(text)) {
    return '安全';
  }

  // 工作流相关
  if (/工作流|workflow|流程|步骤|方法论|gsd|superpowers|ecc|协作|调度/i.test(text)) {
    return '工作流';
  }

  // 主人偏好相关
  if (/主人|偏好|教导|教训|原则|记住|喜欢|不喜欢|沟通/i.test(text)) {
    return '主人偏好';
  }

  // 技术相关
  if (/代码|api|bug|fix|部署|docker|git|typescript|javascript|python|react|node|server|数据库|配置|实现|集成/i.test(text)) {
    return '技术';
  }

  // 日志类（按日期的记录）
  if (/^\d{4}-\d{2}-\d{2}/.test(title) || /每日记录|日志|完成|事件/i.test(text)) {
    return '日志';
  }

  return '其他';
}

/**
 * 从文件名或内容提取日期
 */
function extractDate(filePath: string, content: string): string | undefined {
  // 从文件名提取
  const fileName = path.basename(filePath);
  const dateFromFile = fileName.match(/(\d{4}-\d{2}-\d{2})/);
  if (dateFromFile) return dateFromFile[1];

  // 从内容提取（取最早的日期）
  const dates: string[] = [];
  const dateRegex = /(\d{4}-\d{2}-\d{2})/g;
  let match;
  while ((match = dateRegex.exec(content)) !== null) {
    dates.push(match[1]);
  }

  return dates.length > 0 ? dates.sort()[0] : undefined;
}

/**
 * 从标题和内容提取标签
 */
function extractTags(title: string, content: string): string[] {
  const tags = new Set<string>();

  // 提取 emoji 标签
  const emojiMap: Record<string, string> = {
    '✅': '完成', '⚠️': '警告', '❌': '错误', '📋': '待办',
    '🔧': '技术', '🧠': '方法论', '📌': '重要', '📚': '知识',
    '🤖': 'agent', '🎯': '目标', '💡': '想法', '🔍': '搜索',
  };
  for (const [emoji, tag] of Object.entries(emojiMap)) {
    if (title.includes(emoji) || content.slice(0, 200).includes(emoji)) {
      tags.add(tag);
    }
  }

  // 提取技术关键词
  const techPatterns = [
    { pattern: /\b(github|git|docker|k8s|node\.?js|typescript|react|vue|python|golang)\b/gi, tag: '技术栈' },
    { pattern: /\b(openclaw|lark|feishu|飞书)\b/gi, tag: '飞书' },
    { pattern: /\b(api|rest|graphql|webhook)\b/gi, tag: 'API' },
    { pattern: /\b(ci\/cd|github\s*actions|deploy)\b/gi, tag: '部署' },
    { pattern: /dashboard|前端|后端|ui|ux/gi, tag: '产品' },
  ];

  const combined = `${title} ${content}`.toLowerCase();
  for (const { pattern, tag } of techPatterns) {
    if (pattern.test(combined)) {
      tags.add(tag);
    }
  }

  return [...tags];
}

// ─── 核心类 ─────────────────────────────────────────────────

export class MemoryIndex {
  private entries: IndexEntry[] = [];
  private idfCache: Map<string, number> = new Map();
  private config: IndexerConfig;
  private builtAt: string = '';
  private indexedFiles: string[] = [];

  constructor(config: IndexerConfig) {
    this.config = {
      stopWords: DEFAULT_STOP_WORDS,
      fileFilter: (name) => name.endsWith('.md'),
      ...config,
    };
  }

  // ─── 索引构建 ─────────────────────────────────────────────

  /**
   * 构建/重建索引
   * 支持增量：只重新索引变更的文件
   */
  async rebuild(): Promise<void> {
    this.entries = [];
    this.idfCache.clear();
    this.indexedFiles = [];

    // 索引 MEMORY.md
    if (fs.existsSync(this.config.memoryPath)) {
      await this.indexFile(this.config.memoryPath);
      this.indexedFiles.push(this.config.memoryPath);
    }

    // 索引 memory/*.md
    if (fs.existsSync(this.config.memoryDirPath)) {
      const files = fs.readdirSync(this.config.memoryDirPath)
        .filter(f => this.config.fileFilter!(f))
        .map(f => path.join(this.config.memoryDirPath, f));

      for (const file of files) {
        await this.indexFile(file);
        this.indexedFiles.push(file);
      }
    }

    // 构建 IDF 缓存
    this.buildIdfCache();
    this.builtAt = new Date().toISOString();
  }

  /**
   * 索引单个文件
   */
  private async indexFile(filePath: string): Promise<void> {
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.split('\n');
    const sections = parseSections(lines);
    const date = extractDate(filePath, content);

    for (const section of sections) {
      // 跳过太短的分区（< 3 行实质内容）
      const sectionContent = lines.slice(section.startLine - 1, section.endLine).join('\n');
      if (sectionContent.trim().length < 20) continue;

      const category = inferCategory(section.title, sectionContent);
      const tags = extractTags(section.title, sectionContent);
      const tokens = tokenize(sectionContent);
      const termFreq = new Map<string, number>();

      for (const token of tokens) {
        if (this.config.stopWords!.has(token) || token.length < 2) continue;
        termFreq.set(token, (termFreq.get(token) || 0) + 1);
      }

      const id = `${filePath}:${section.startLine}-${section.endLine}`;

      this.entries.push({
        id,
        filePath,
        startLine: section.startLine,
        endLine: section.endLine,
        title: section.title,
        content: sectionContent,
        category,
        date,
        termFreq,
        tags,
      });
    }

    // 如果文件没有标题，按内容块索引
    if (sections.length === 0 && content.trim().length > 20) {
      const category = inferCategory(path.basename(filePath), content);
      const tags = extractTags(path.basename(filePath), content);
      const tokens = tokenize(content);
      const termFreq = new Map<string, number>();

      for (const token of tokens) {
        if (this.config.stopWords!.has(token) || token.length < 2) continue;
        termFreq.set(token, (termFreq.get(token) || 0) + 1);
      }

      this.entries.push({
        id: `${filePath}:1-${lines.length}`,
        filePath,
        startLine: 1,
        endLine: lines.length,
        title: path.basename(filePath, '.md'),
        content,
        category,
        date,
        termFreq,
        tags,
      });
    }
  }

  /**
   * 构建 IDF（逆文档频率）缓存
   */
  private buildIdfCache(): void {
    const docCount = this.entries.length;
    const termDocCount = new Map<string, number>();

    for (const entry of this.entries) {
      for (const term of entry.termFreq.keys()) {
        termDocCount.set(term, (termDocCount.get(term) || 0) + 1);
      }
    }

    for (const [term, count] of termDocCount) {
      // IDF = log(N / (1 + df))，加 1 防止除零
      this.idfCache.set(term, Math.log(docCount / (1 + count)));
    }
  }

  // ─── 搜索 ─────────────────────────────────────────────────

  /**
   * 语义搜索记忆
   *
   * @param query - 搜索关键词（空格分隔）
   * @param options - 搜索选项
   * @returns 按相关度排序的搜索结果
   */
  search(query: string, options: SearchOptions = {}): SearchResult[] {
    const {
      topK = 5,
      category,
      dateRange,
      minScore = 0,
    } = options;

    if (this.entries.length === 0) return [];

    // 分词查询
    const queryTokens = tokenize(query);
    const filteredQueryTokens = queryTokens.filter(
      t => !this.config.stopWords!.has(t) && t.length >= 2
    );

    if (filteredQueryTokens.length === 0) return [];

    // 计算每个条目的相关度
    const results: SearchResult[] = [];

    for (const entry of this.entries) {
      // 分类过滤
      if (category && entry.category !== category) continue;

      // 日期过滤
      if (dateRange && entry.date) {
        if (dateRange.from && entry.date < dateRange.from) continue;
        if (dateRange.to && entry.date > dateRange.to) continue;
      }

      // TF-IDF 评分
      const matchedTerms: string[] = [];
      let score = 0;

      for (const queryToken of filteredQueryTokens) {
        // 精确匹配
        const tf = entry.termFreq.get(queryToken);
        if (tf && tf > 0) {
          const idf = this.idfCache.get(queryToken) || 1;
          score += tf * idf;
          matchedTerms.push(queryToken);
          continue;
        }

        // 模糊匹配（子串包含）
        for (const [entryTerm, entryTf] of entry.termFreq) {
          if (entryTerm.includes(queryToken) || queryToken.includes(entryTerm)) {
            const idf = this.idfCache.get(entryTerm) || 1;
            score += entryTf * idf * 0.5; // 模糊匹配权重减半
            matchedTerms.push(entryTerm);
            break;
          }
        }
      }

      // 标题匹配加权（标题权重 x3）
      const titleLower = entry.title.toLowerCase();
      for (const queryToken of filteredQueryTokens) {
        if (titleLower.includes(queryToken)) {
          score *= 1.5;
          if (!matchedTerms.includes(queryToken)) {
            matchedTerms.push(queryToken);
          }
        }
      }

      // 标签匹配加权
      for (const tag of entry.tags) {
        for (const queryToken of filteredQueryTokens) {
          if (tag.toLowerCase().includes(queryToken)) {
            score *= 1.2;
          }
        }
      }

      if (score > 0) {
        results.push({
          entry,
          score,
          matchedTerms: [...new Set(matchedTerms)],
        });
      }
    }

    // 归一化评分到 0-1
    if (results.length > 0) {
      const maxScore = Math.max(...results.map(r => r.score));
      if (maxScore > 0) {
        for (const r of results) {
          r.score = Math.round((r.score / maxScore) * 100) / 100;
        }
      }
    }

    // 过滤低分结果 + 排序 + 截断
    return results
      .filter(r => r.score >= minScore)
      .sort((a, b) => b.score - a.score)
      .slice(0, topK);
  }

  // ─── 精确获取 ─────────────────────────────────────────────

  /**
   * 获取文件指定行号范围的内容片段
   *
   * @param filePath - 文件路径
   * @param fromLine - 起始行（1-indexed, inclusive）
   * @param toLine - 结束行（1-indexed, inclusive）
   * @returns 片段文本，行号超出范围时返回可用部分
   */
  getSnippet(filePath: string, fromLine: number, toLine: number): string {
    if (!fs.existsSync(filePath)) {
      throw new Error(`文件不存在: ${filePath}`);
    }

    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.split('\n');

    const start = Math.max(0, fromLine - 1);
    const end = Math.min(lines.length, toLine);

    if (start >= end) return '';

    return lines.slice(start, end).join('\n');
  }

  // ─── 统计 ─────────────────────────────────────────────────

  /**
   * 获取索引统计信息
   */
  getStats(): IndexStats {
    const categoryCounts: Record<string, number> = {};
    let totalTerms = 0;

    for (const entry of this.entries) {
      categoryCounts[entry.category] = (categoryCounts[entry.category] || 0) + 1;
      totalTerms += entry.termFreq.size;
    }

    // 确保所有分类都有值
    const allCategories: MemoryCategory[] = ['技术', '工作流', '主人偏好', '安全', '日志', '其他'];
    for (const cat of allCategories) {
      if (!(cat in categoryCounts)) categoryCounts[cat] = 0;
    }

    return {
      totalEntries: this.entries.length,
      totalFiles: this.indexedFiles.length,
      categoryCounts: categoryCounts as Record<MemoryCategory, number>,
      totalTerms,
      builtAt: this.builtAt,
      indexedFiles: [...this.indexedFiles],
    };
  }

  // ─── 访问器 ───────────────────────────────────────────────

  /** 获取所有索引条目（只读） */
  getEntries(): ReadonlyArray<IndexEntry> {
    return this.entries;
  }

  /** 按分类获取条目 */
  getEntriesByCategory(category: MemoryCategory): IndexEntry[] {
    return this.entries.filter(e => e.category === category);
  }

  /** 按日期获取条目 */
  getEntriesByDate(date: string): IndexEntry[] {
    return this.entries.filter(e => e.date === date);
  }

  /** 获取最近 N 天的条目 */
  getRecentEntries(days: number): IndexEntry[] {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);
    const cutoffStr = cutoff.toISOString().slice(0, 10);
    return this.entries.filter(e => e.date && e.date >= cutoffStr);
  }

  /** 检查索引是否为空 */
  isEmpty(): boolean {
    return this.entries.length === 0;
  }
}

// ─── 快捷工厂函数 ───────────────────────────────────────────

/**
 * 创建并构建 MemoryIndex 实例（便捷函数）
 *
 * @param workspaceRoot - 工作区根目录（默认当前目录）
 * @returns 已构建索引的 MemoryIndex 实例
 */
export async function createMemoryIndex(workspaceRoot: string = '.'): Promise<MemoryIndex> {
  const index = new MemoryIndex({
    memoryPath: path.join(workspaceRoot, 'MEMORY.md'),
    memoryDirPath: path.join(workspaceRoot, 'memory'),
  });
  await index.rebuild();
  return index;
}
