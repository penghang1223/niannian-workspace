/**
 * Agent 结构化通信协议 - ClawTeam 改进 Phase 1
 * 
 * 功能：标准化 Agent 间消息格式，便于追踪和审计
 * 输出：统一的消息 schema
 * 
 * @author 年年 🎀
 * @created 2026-03-21 01:25
 */

/**
 * 消息类型枚举
 */
const MessageType = {
  TASK_ASSIGN: 'task_assign',           // 任务分配
  TASK_COMPLETE: 'task_complete',        // 任务完成
  TASK_FAILED: 'task_failed',            // 任务失败
  TASK_PROGRESS: 'task_progress',        // 任务进度更新
  REQUEST_HELP: 'request_help',          // 请求帮助
  PROVIDE_INFO: 'provide_info',          // 提供信息
  STATUS_UPDATE: 'status_update',        // 状态更新
  HEARTBEAT: 'heartbeat'                 // 心跳
};

/**
 * 优先级枚举
 */
const Priority = {
  P0: 'P0',  // 紧急
  P1: 'P1',  // 重要
  P2: 'P2'   // 一般
};

/**
 * Agent 状态枚举
 */
const AgentStatus = {
  IDLE: 'idle',           // 空闲
  BUSY: 'busy',           // 忙碌
  AWAITING: 'awaiting',   // 等待依赖
  ERROR: 'error'          // 错误
};

/**
 * 构建标准化的 Agent 消息
 * @param {Object} options - 消息选项
 * @returns {Object} 标准化消息
 */
function buildAgentMessage(options) {
  const {
    from,
    to,
    type,
    taskId,
    priority = Priority.P1,
    data = {},
    timestamp = Date.now()
  } = options;
  
  const message = {
    // 基础信息
    id: generateMessageId(),
    version: '1.0',
    timestamp,
    
    // 发送者/接收者
    from: {
      agentId: from,
      timestamp
    },
    to: {
      agentId: to
    },
    
    // 消息类型和优先级
    type,
    priority,
    
    // 任务关联
    taskId,
    
    // 消息数据（根据类型不同而不同）
    data,
    
    // 元数据
    metadata: {
      protocol: 'clawteam-v1',
      encoding: 'utf-8'
    }
  };
  
  // 验证消息
  validateMessage(message);
  
  return message;
}

/**
 * 验证消息格式
 */
function validateMessage(message) {
  const required = ['id', 'version', 'timestamp', 'from', 'to', 'type', 'taskId'];
  
  for (const field of required) {
    if (!message[field]) {
      throw new Error(`消息缺少必需字段：${field}`);
    }
  }
  
  if (!Object.values(MessageType).includes(message.type)) {
    throw new Error(`无效的消息类型：${message.type}`);
  }
  
  if (!Object.values(Priority).includes(message.priority)) {
    throw new Error(`无效的优先级：${message.priority}`);
  }
}

/**
 * 生成消息 ID
 */
function generateMessageId() {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substring(2, 8);
  return `msg_${timestamp}_${random}`;
}

/**
 * 构建任务分配消息
 */
function buildTaskAssignMessage(from, to, task) {
  return buildAgentMessage({
    from,
    to,
    type: MessageType.TASK_ASSIGN,
    taskId: task.id,
    priority: task.priority,
    data: {
      taskDesc: task.desc,
      dependencies: task.deps,
      estimatedMinutes: task.estimatedMinutes,
      assignedAt: Date.now()
    }
  });
}

/**
 * 构建任务完成消息
 */
function buildTaskCompleteMessage(from, to, task, result) {
  return buildAgentMessage({
    from,
    to,
    type: MessageType.TASK_COMPLETE,
    taskId: task.id,
    data: {
      completedAt: Date.now(),
      result,
      duration: result.duration
    }
  });
}

/**
 * 构建任务失败消息
 */
function buildTaskFailedMessage(from, to, task, error) {
  return buildAgentMessage({
    from,
    to,
    type: MessageType.TASK_FAILED,
    taskId: task.id,
    priority: Priority.P0,
    data: {
      failedAt: Date.now(),
      error: {
        message: error.message,
        stack: error.stack
      }
    }
  });
}

/**
 * 构建进度更新消息
 */
function buildProgressMessage(from, to, task, progress) {
  return buildAgentMessage({
    from,
    to,
    type: MessageType.TASK_PROGRESS,
    taskId: task.id,
    data: {
      progress: progress, // 0-100
      updatedAt: Date.now(),
      note: progress.note || ''
    }
  });
}

/**
 * 构建请求帮助消息
 */
function buildHelpRequestMessage(from, to, task, helpNeeded) {
  return buildAgentMessage({
    from,
    to,
    type: MessageType.REQUEST_HELP,
    taskId: task.id,
    priority: Priority.P0,
    data: {
      helpType: helpNeeded.type,
      description: helpNeeded.description,
      requestedAt: Date.now()
    }
  });
}

/**
 * 构建状态更新消息
 */
function buildStatusUpdateMessage(from, to, status) {
  return buildAgentMessage({
    from,
    to,
    type: MessageType.STATUS_UPDATE,
    taskId: null,
    data: {
      status,
      updatedAt: Date.now()
    }
  });
}

/**
 * 解析消息为人类可读格式
 */
function formatMessageForHuman(message) {
  const typeLabels = {
    [MessageType.TASK_ASSIGN]: '📋 任务分配',
    [MessageType.TASK_COMPLETE]: '✅ 任务完成',
    [MessageType.TASK_FAILED]: '❌ 任务失败',
    [MessageType.TASK_PROGRESS]: '📊 进度更新',
    [MessageType.REQUEST_HELP]: '🆘 请求帮助',
    [MessageType.PROVIDE_INFO]: '📬 信息同步',
    [MessageType.STATUS_UPDATE]: '🔄 状态更新',
    [MessageType.HEARTBEAT]: '💓 心跳'
  };
  
  const priorityLabels = {
    [Priority.P0]: '🔴 紧急',
    [Priority.P1]: '🟡 重要',
    [Priority.P2]: '🟢 一般'
  };
  
  return `
${typeLabels[message.type] || '💬 消息'}
━━━━━━━━━━━━━━━━━━━━
📎 消息 ID: ${message.id}
📤 发送者：${message.from.agentId}
📥 接收者：${message.to.agentId}
🏷️ 优先级：${priorityLabels[message.priority]}
📋 任务 ID: ${message.taskId || '无'}
⏰ 时间：${new Date(message.timestamp).toLocaleString('zh-CN')}
━━━━━━━━━━━━━━━━━━━━
📝 内容：${JSON.stringify(message.data, null, 2)}
`.trim();
}

/**
 * 序列化消息（用于存储或传输）
 */
function serializeMessage(message) {
  return JSON.stringify(message, null, 2);
}

/**
 * 反序列化消息
 */
function deserializeMessage(jsonString) {
  const message = JSON.parse(jsonString);
  validateMessage(message);
  return message;
}

/**
 * 消息日志记录
 */
function logMessage(message, direction = 'outbound') {
  const logEntry = {
    timestamp: new Date().toISOString(),
    direction,
    messageId: message.id,
    from: message.from.agentId,
    to: message.to.agentId,
    type: message.type,
    taskId: message.taskId
  };
  
  console.log(`[${direction.toUpperCase()}] ${formatMessageForHuman(message)}`);
  
  // TODO: 写入日志文件
  // appendToFile('/workspace/logs/agent_messages.jsonl', JSON.stringify(logEntry) + '\n');
  
  return logEntry;
}

module.exports = {
  MessageType,
  Priority,
  AgentStatus,
  buildAgentMessage,
  buildTaskAssignMessage,
  buildTaskCompleteMessage,
  buildTaskFailedMessage,
  buildProgressMessage,
  buildHelpRequestMessage,
  buildStatusUpdateMessage,
  formatMessageForHuman,
  serializeMessage,
  deserializeMessage,
  logMessage
};
