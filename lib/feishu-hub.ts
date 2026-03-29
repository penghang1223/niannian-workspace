/**
 * 飞书集成中枢 — FeishuHub
 * 统一日历、任务、文档、群聊能力，为团队自动化提供单一入口
 *
 * 设计原则：
 * - 适配 OpenClaw feishu_* 工具的 API 约定（ISO 8601 时间、分页格式）
 * - 所有外部依赖通过构造函数注入（ApiClient），方便测试 mock
 * - 返回值统一为类型安全的 Promise<Result>，不做隐式异常
 */

// ─── Types ───────────────────────────────────────────────────────────────────

/** 日程事件 */
export interface CalendarEvent {
  eventId: string;
  summary: string;
  startTime: string;  // ISO 8601
  endTime: string;    // ISO 8601
  location?: string;
  description?: string;
  attendees?: Array<{ id: string; type: string }>;
}

/** 飞书任务 */
export interface FeishuTask {
  taskGuid: string;
  summary: string;
  description?: string;
  due?: string;       // ISO 8601
  completed: boolean;
  completedAt?: string;
  members?: Array<{ id: string; role: string }>;
}

/** 空闲时间段 */
export interface FreeSlot {
  start: string;  // ISO 8601
  end: string;    // ISO 8601
  durationMinutes: number;
}

/** 飞书文档摘要 */
export interface DocSummary {
  docId: string;
  title: string;
  url?: string;
  type: string;       // doc / docx / sheet / bitable
}

/** 互动卡片 */
export interface InteractiveCard {
  header: {
    title: string;
    template?: 'blue' | 'green' | 'red' | 'orange' | 'purple' | 'grey';
  };
  elements: unknown[];  // Card element array, 飞书卡片 JSON 格式
}

/** 飞书 API 客户端接口 — 所有方法对应 OpenClaw feishu_* 工具 */
export interface FeishuApiClient {
  // 日历
  calendarEventList(params: {
    start_time: string;
    end_time: string;
    page_size?: number;
    page_token?: string;
  }): Promise<{ items: CalendarEvent[]; has_more: boolean; page_token?: string }>;

  calendarEventCreate(params: {
    summary: string;
    start_time: string;
    end_time: string;
    description?: string;
    location?: { name: string };
    attendees?: Array<{ type: string; id: string }>;
    user_open_id?: string;
  }): Promise<{ event_id: string }>;

  calendarFreebusyList(params: {
    time_min: string;
    time_max: string;
    user_ids: string[];
  }): Promise<{ busy_periods: Array<{ start: string; end: string }> }>;

  // 任务
  taskList(params: {
    completed?: boolean;
    page_size?: number;
    page_token?: string;
  }): Promise<{ items: FeishuTask[]; has_more: boolean; page_token?: string }>;

  taskCreate(params: {
    summary: string;
    description?: string;
    due?: { timestamp: string; is_all_day?: boolean };
    members?: Array<{ id: string; role: string }>;
    current_user_id?: string;
  }): Promise<{ task_guid: string }>;

  taskPatch(params: {
    task_guid: string;
    completed_at?: string;
    summary?: string;
  }): Promise<void>;

  // 文档
  docCreate(params: {
    title: string;
    markdown: string;
    folder_token?: string;
  }): Promise<{ doc_id: string; url?: string }>;

  docFetch(docId: string): Promise<{ title: string; content: string }>;

  docUpdate(params: {
    doc_id: string;
    markdown: string;
    mode: 'append' | 'overwrite' | 'replace_all';
  }): Promise<void>;

  docSearch(params: {
    query: string;
    page_size?: number;
    page_token?: string;
  }): Promise<{ items: DocSummary[]; has_more: boolean; page_token?: string }>;

  // 群聊
  imSendMessage(params: {
    receive_id_type: 'chat_id' | 'open_id';
    receive_id: string;
    msg_type: string;
    content: string;
  }): Promise<{ message_id: string }>;

  chatSearch(params: {
    query: string;
    page_size?: number;
  }): Promise<{ items: Array<{ chat_id: string; name: string }> }>;
}

/** 同步结果 */
export interface SyncResult {
  synced: number;
  created: number;
  updated: number;
  errors: string[];
}

/** 本地任务存储接口 */
export interface LocalTaskStore {
  list(): Promise<FeishuTask[]>;
  upsert(task: FeishuTask): Promise<void>;
  removeByGuid(guid: string): Promise<void>;
}

// ─── Errors ──────────────────────────────────────────────────────────────────

export class FeishuApiError extends Error {
  constructor(
    message: string,
    public readonly operation: string,
    public readonly statusCode?: number,
  ) {
    super(message);
    this.name = 'FeishuApiError';
  }
}

// ─── FeishuHub ───────────────────────────────────────────────────────────────

export class FeishuHub {
  private readonly api: FeishuApiClient;
  private readonly localStore?: LocalTaskStore;
  private readonly defaultPageSize = 50;

  /**
   * @param api 飞书 API 客户端（生产环境注入真实实现，测试时注入 mock）
   * @param localStore 可选的本地任务存储，用于 task 同步
   */
  constructor(api: FeishuApiClient, localStore?: LocalTaskStore) {
    this.api = api;
    this.localStore = localStore;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // 📅 日历联动
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * 获取未来 N 小时内的日程
   * @param hours 未来几小时，默认 24
   */
  async getUpcomingEvents(hours = 24): Promise<CalendarEvent[]> {
    const now = new Date();
    const end = new Date(now.getTime() + hours * 3600_000);

    return this.fetchAllEvents(
      now.toISOString(),
      end.toISOString(),
    );
  }

  /**
   * 快速创建日程
   * @param title 日程标题
   * @param startTime 开始时间（ISO 8601 或 Date）
   * @param durationMinutes 持续分钟数，默认 60
   * @param options 可选：location, description, attendees, userId
   */
  async createQuickEvent(
    title: string,
    startTime: string | Date,
    durationMinutes = 60,
    options?: {
      location?: string;
      description?: string;
      attendees?: Array<{ type: string; id: string }>;
      userId?: string;
    },
  ): Promise<{ eventId: string }> {
    const start = new Date(startTime);
    const end = new Date(start.getTime() + durationMinutes * 60_000);

    try {
      return await this.api.calendarEventCreate({
        summary: title,
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        description: options?.description,
        location: options?.location ? { name: options.location } : undefined,
        attendees: options?.attendees,
        user_open_id: options?.userId,
      });
    } catch (err) {
      throw new FeishuApiError(
        `创建日程失败: ${err instanceof Error ? err.message : err}`,
        'createQuickEvent',
      );
    }
  }

  /**
   * 查询某天的空闲时间段
   * @param date 日期（YYYY-MM-DD 或 Date）
   * @param durationMinutes 最小可用时长（分钟）
   * @param userId 查询的用户 open_id
   * @param workHourRange 工作时间范围，默认 [9, 18]
   */
  async getFreeSlots(
    date: string | Date,
    durationMinutes: number,
    userId: string,
    workHourRange: [number, number] = [9, 18],
  ): Promise<FreeSlot[]> {
    const day = typeof date === 'string' ? new Date(date) : date;
    const dayStr = day.toISOString().split('T')[0];

    const dayStart = new Date(`${dayStr}T${String(workHourRange[0]).padStart(2, '0')}:00:00`);
    const dayEnd = new Date(`${dayStr}T${String(workHourRange[1]).padStart(2, '0')}:00:00`);

    const result = await this.api.calendarFreebusyList({
      time_min: dayStart.toISOString(),
      time_max: dayEnd.toISOString(),
      user_ids: [userId],
    });

    // 用忙时区间填充，计算空闲段
    const busyPeriods = result.busy_periods
      .map((p) => ({
        start: new Date(p.start).getTime(),
        end: new Date(p.end).getTime(),
      }))
      .sort((a, b) => a.start - b.start);

    const freeSlots: FreeSlot[] = [];
    let cursor = dayStart.getTime();

    for (const busy of busyPeriods) {
      if (busy.start > cursor) {
        const gap = busy.start - cursor;
        if (gap >= durationMinutes * 60_000) {
          freeSlots.push({
            start: new Date(cursor).toISOString(),
            end: new Date(busy.start).toISOString(),
            durationMinutes: Math.floor(gap / 60_000),
          });
        }
      }
      cursor = Math.max(cursor, busy.end);
    }

    // 尾部空闲
    if (cursor < dayEnd.getTime()) {
      const gap = dayEnd.getTime() - cursor;
      if (gap >= durationMinutes * 60_000) {
        freeSlots.push({
          start: new Date(cursor).toISOString(),
          end: dayEnd.toISOString(),
          durationMinutes: Math.floor(gap / 60_000),
        });
      }
    }

    return freeSlots;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // ✅ 任务联动
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * 获取我的飞书任务
   * @param status 过滤状态：'open' | 'completed' | undefined（全部）
   */
  async getMyTasks(status?: 'open' | 'completed'): Promise<FeishuTask[]> {
    const completed = status === 'completed' ? true : status === 'open' ? false : undefined;
    const tasks: FeishuTask[] = [];
    let pageToken: string | undefined;

    try {
      do {
        const resp = await this.api.taskList({
          completed,
          page_size: this.defaultPageSize,
          page_token: pageToken,
        });
        tasks.push(...resp.items);
        pageToken = resp.has_more ? resp.page_token : undefined;
      } while (pageToken);
    } catch (err) {
      throw new FeishuApiError(
        `获取任务列表失败: ${err instanceof Error ? err.message : err}`,
        'getMyTasks',
      );
    }

    return tasks;
  }

  /**
   * 快速创建任务
   * @param title 任务标题
   * @param due 截止时间（ISO 8601 或 Date）
   * @param options 可选：description, assigneeId
   */
  async createTask(
    title: string,
    due?: string | Date,
    options?: {
      description?: string;
      assigneeId?: string;
      currentUserId?: string;
    },
  ): Promise<{ taskGuid: string }> {
    try {
      return await this.api.taskCreate({
        summary: title,
        description: options?.description,
        due: due
          ? { timestamp: (typeof due === 'string' ? new Date(due) : due).toISOString() }
          : undefined,
        members: options?.assigneeId
          ? [{ id: options.assigneeId, role: 'assignee' }]
          : undefined,
        current_user_id: options?.currentUserId,
      });
    } catch (err) {
      throw new FeishuApiError(
        `创建任务失败: ${err instanceof Error ? err.message : err}`,
        'createTask',
      );
    }
  }

  /**
   * 飞书任务同步到本地存储
   * 返回同步结果摘要
   */
  async syncToLocalTasks(): Promise<SyncResult> {
    if (!this.localStore) {
      throw new FeishuApiError('未配置本地存储（LocalTaskStore），无法执行同步', 'syncToLocalTasks');
    }

    const result: SyncResult = { synced: 0, created: 0, updated: 0, errors: [] };

    try {
      // 拉取飞书全部任务
      const remoteTasks = await this.getMyTasks();
      const localTasks = await this.localStore.list();
      const localMap = new Map(localTasks.map((t) => [t.taskGuid, t]));

      for (const remote of remoteTasks) {
        try {
          const existing = localMap.get(remote.taskGuid);
          if (!existing) {
            await this.localStore.upsert(remote);
            result.created++;
          } else if (
            existing.summary !== remote.summary ||
            existing.completed !== remote.completed ||
            existing.due !== remote.due
          ) {
            await this.localStore.upsert(remote);
            result.updated++;
          }
          result.synced++;
        } catch (err) {
          result.errors.push(`同步失败 [${remote.taskGuid}]: ${err instanceof Error ? err.message : err}`);
        }
      }

      // 清除本地已不存在的远程任务
      const remoteGuids = new Set(remoteTasks.map((t) => t.taskGuid));
      for (const local of localTasks) {
        if (!remoteGuids.has(local.taskGuid)) {
          await this.localStore.removeByGuid(local.taskGuid);
        }
      }
    } catch (err) {
      result.errors.push(`同步异常: ${err instanceof Error ? err.message : err}`);
    }

    return result;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // 📄 文档联动
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * 快速创建飞书文档
   * @param title 文档标题
   * @param content Markdown 内容
   * @param folderToken 目标文件夹 token（可选）
   */
  async createNote(
    title: string,
    content: string,
    folderToken?: string,
  ): Promise<{ docId: string; url?: string }> {
    try {
      return await this.api.docCreate({ title, markdown: content, folder_token: folderToken });
    } catch (err) {
      throw new FeishuApiError(
        `创建文档失败: ${err instanceof Error ? err.message : err}`,
        'createNote',
      );
    }
  }

  /**
   * 搜索飞书文档
   * @param query 搜索关键词
   * @param maxResults 最大返回数，默认 15
   */
  async searchDocs(query: string, maxResults = 15): Promise<DocSummary[]> {
    const results: DocSummary[] = [];
    let pageToken: string | undefined;

    try {
      do {
        const resp = await this.api.docSearch({
          query,
          page_size: Math.min(maxResults, 20),
          page_token: pageToken,
        });
        results.push(...resp.items);
        pageToken = resp.has_more ? resp.page_token : undefined;
      } while (pageToken && results.length < maxResults);
    } catch (err) {
      throw new FeishuApiError(
        `搜索文档失败: ${err instanceof Error ? err.message : err}`,
        'searchDocs',
      );
    }

    return results.slice(0, maxResults);
  }

  /**
   * 向飞书文档追加内容（日志）
   * @param docId 文档 ID
   * @param content 追加的 Markdown 内容
   */
  async appendLog(docId: string, content: string): Promise<void> {
    const timestamp = new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' });
    const logBlock = `\n\n---\n**${timestamp}**\n\n${content}`;

    try {
      await this.api.docUpdate({ doc_id: docId, markdown: logBlock, mode: 'append' });
    } catch (err) {
      throw new FeishuApiError(
        `追加日志失败: ${err instanceof Error ? err.message : err}`,
        'appendLog',
      );
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // 💬 群聊联动
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * 发送飞书互动卡片到群聊
   * @param chatId 群聊 ID (oc_xxx)
   * @param card 互动卡片 JSON
   */
  async sendCard(
    chatId: string,
    card: InteractiveCard,
  ): Promise<{ messageId: string }> {
    try {
      const resp = await this.api.imSendMessage({
        receive_id_type: 'chat_id',
        receive_id: chatId,
        msg_type: 'interactive',
        content: JSON.stringify(card),
      });
      return { messageId: resp.message_id };
    } catch (err) {
      throw new FeishuApiError(
        `发送卡片失败: ${err instanceof Error ? err.message : err}`,
        'sendCard',
      );
    }
  }

  /**
   * 向多个群广播文本消息
   * @param message 广播内容
   * @param channels 群聊 ID 列表（oc_xxx 格式）
   */
  async broadcast(
    message: string,
    channels: string[],
  ): Promise<Array<{ chatId: string; messageId?: string; error?: string }>> {
    const results = await Promise.allSettled(
      channels.map(async (chatId) => {
        const resp = await this.api.imSendMessage({
          receive_id_type: 'chat_id',
          receive_id: chatId,
          msg_type: 'text',
          content: JSON.stringify({ text: message }),
        });
        return { chatId, messageId: resp.message_id };
      }),
    );

    return results.map((r, i) => {
      if (r.status === 'fulfilled') return r.value;
      return {
        chatId: channels[i],
        error: r.reason instanceof Error ? r.reason.message : String(r.reason),
      };
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // 🏗️ 场景组合
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * 晨会报告生成器
   * 从日历获取今日日程 + 从任务列表获取待办 → 生成 Markdown 报告
   */
  async generateMorningReport(userId?: string): Promise<{
    calendarSection: string;
    taskSection: string;
    fullReport: string;
  }> {
    // 日程：未来 8 小时
    const events = await this.getUpcomingEvents(8);

    // 待办任务
    const openTasks = await this.getMyTasks('open');

    // 日历段
    const calendarSection = events.length === 0
      ? '📅 今天没有日程安排'
      : '📅 **今日日程**\n' + events
          .map((e) => {
            const start = new Date(e.startTime).toLocaleTimeString('zh-CN', {
              hour: '2-digit',
              minute: '2-digit',
              timeZone: 'Asia/Shanghai',
            });
            return `- ${start} — ${e.summary}`;
          })
          .join('\n');

    // 任务段
    const taskSection = openTasks.length === 0
      ? '✅ 没有待办任务'
      : '📋 **待办任务**\n' + openTasks
          .map((t) => {
            const due = t.due
              ? `（截止 ${new Date(t.due).toLocaleDateString('zh-CN', { timeZone: 'Asia/Shanghai' })}）`
              : '';
            return `- [ ] ${t.summary} ${due}`.trim();
          })
          .join('\n');

    const fullReport = [
      '## 🌅 晨会报告',
      '',
      calendarSection,
      '',
      taskSection,
    ].join('\n');

    return { calendarSection, taskSection, fullReport };
  }

  /**
   * 每日复盘写入飞书文档
   * @param docId 目标文档 ID
   * @param summary 复盘内容
   * @param highlights 亮点
   * @param blockers 阻碍
   * @param tomorrowPlan 明日计划
   */
  async appendDailyReview(
    docId: string,
    summary: string,
    highlights?: string[],
    blockers?: string[],
    tomorrowPlan?: string[],
  ): Promise<void> {
    const lines: string[] = [];
    lines.push(`### 📝 ${new Date().toLocaleDateString('zh-CN', { timeZone: 'Asia/Shanghai' })} 日常复盘`);
    lines.push('');
    lines.push(summary);

    if (highlights?.length) {
      lines.push('', '#### 🌟 亮点', ...highlights.map((h) => `- ${h}`));
    }
    if (blockers?.length) {
      lines.push('', '#### 🚧 阻碍', ...blockers.map((b) => `- ${b}`));
    }
    if (tomorrowPlan?.length) {
      lines.push('', '#### 📅 明日计划', ...tomorrowPlan.map((p) => `- ${p}`));
    }

    await this.appendLog(docId, lines.join('\n'));
  }

  /**
   * 任务完成时自动同步到飞书
   * @param taskGuid 任务 GUID
   * @param completionTime 完成时间（默认当前时间）
   */
  async completeTask(
    taskGuid: string,
    completionTime?: string | Date,
  ): Promise<void> {
    const ts = (completionTime
      ? (typeof completionTime === 'string' ? new Date(completionTime) : completionTime)
      : new Date()
    ).toISOString();

    try {
      await this.api.taskPatch({ task_guid: taskGuid, completed_at: ts });
    } catch (err) {
      throw new FeishuApiError(
        `完成任务失败: ${err instanceof Error ? err.message : err}`,
        'completeTask',
      );
    }
  }

  // ─── Internal helpers ─────────────────────────────────────────────────────

  private async fetchAllEvents(startTime: string, endTime: string): Promise<CalendarEvent[]> {
    const events: CalendarEvent[] = [];
    let pageToken: string | undefined;

    do {
      const resp = await this.api.calendarEventList({
        start_time: startTime,
        end_time: endTime,
        page_size: this.defaultPageSize,
        page_token: pageToken,
      });
      events.push(...resp.items);
      pageToken = resp.has_more ? resp.page_token : undefined;
    } while (pageToken);

    return events;
  }
}
