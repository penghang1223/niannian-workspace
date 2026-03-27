import { useState, useMemo } from 'react'
import { Card, Tag, Tooltip, Select, Input, Empty, Button } from 'antd'
import {
  PlusOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { DragDropContext, Droppable, Draggable, type DropResult } from '@hello-pangea/dnd'
import { useDashboardStore } from '../stores/dashboardStore'
import type { Task, TaskStatus, TaskPriority } from '../types'

// 看板列配置
const COLUMNS: { key: TaskStatus; title: string; color: string; icon: string }[] = [
  { key: 'todo', title: '待办 TODO', color: '#6b7280', icon: '📋' },
  { key: 'in_progress', title: '进行中 DOING', color: '#6366f1', icon: '⚡' },
  { key: 'review', title: '审查 REVIEW', color: '#f59e0b', icon: '🔍' },
  { key: 'done', title: '已完成 DONE', color: '#10b981', icon: '✅' },
]

// 优先级颜色
const PRIORITY_COLORS: Record<TaskPriority, string> = {
  P0: '#ef4444',
  P1: '#f59e0b',
  P2: '#3b82f6',
  P3: '#6b7280',
}

// 任务卡片组件
function TaskCard({ task, index }: { task: Task; index: number }) {
  const agents = useDashboardStore((s) => s.agents)
  const ownerAgent = agents.find((a) => a.id === task.assignee_id)

  return (
    <Draggable draggableId={task.id} index={index}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          style={{
            ...provided.draggableProps.style,
            marginBottom: 8,
          }}
        >
          <Card
            size="small"
            style={{
              background: snapshot.isDragging ? '#2a2a40' : 'var(--color-bg-card)',
              border: snapshot.isDragging
                ? '1px solid var(--color-primary)'
                : '1px solid var(--color-border)',
              boxShadow: snapshot.isDragging
                ? '0 8px 24px rgba(0,0,0,0.4)'
                : 'none',
              transition: 'box-shadow 0.2s',
            }}
            styles={{ body: { padding: '12px 14px' } }}
          >
            {/* 优先级 + ID */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <Tag
                color={PRIORITY_COLORS[task.priority]}
                style={{ margin: 0, borderRadius: 4, fontSize: 11, fontWeight: 600, border: 'none' }}
              >
                {task.priority}
              </Tag>
              <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>{task.id}</span>
            </div>

            {/* 标题 */}
            <div
              style={{
                fontSize: 13,
                fontWeight: 500,
                color: 'var(--color-text-primary)',
                marginBottom: 8,
                lineHeight: 1.4,
              }}
            >
              {task.title}
            </div>

            {/* 底部信息 */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: 11,
                color: 'var(--color-text-muted)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                {ownerAgent && (
                  <Tooltip title={ownerAgent.name}>
                    <Tag
                      style={{
                        margin: 0,
                        borderRadius: 4,
                        fontSize: 10,
                        background: '#1e1e30',
                        border: 'none',
                        color: 'var(--color-text-secondary)',
                      }}
                    >
                      <UserOutlined style={{ marginRight: 2 }} />
                      {ownerAgent.name}
                    </Tag>
                  </Tooltip>
                )}
              </div>
            </div>

            {/* Wave 标记 */}
            {task.wave > 0 && (
              <div style={{ marginTop: 6, fontSize: 10, color: 'var(--color-text-muted)' }}>
                🌊 Wave {task.wave}
              </div>
            )}
          </Card>
        </div>
      )}
    </Draggable>
  )
}

// ===== 任务看板页 =====
export default function TasksPage() {
  const { tasks, updateTask } = useDashboardStore()
  const [filterPriority, setFilterPriority] = useState<string>('all')
  const [searchText, setSearchText] = useState('')

  // 按状态分组任务
  const columns = useMemo(() => {
    let filtered = tasks
    if (filterPriority !== 'all') {
      filtered = filtered.filter((t) => t.priority === filterPriority)
    }
    if (searchText) {
      const lower = searchText.toLowerCase()
      filtered = filtered.filter(
        (t) =>
          t.title.toLowerCase().includes(lower) ||
          t.id.toLowerCase().includes(lower) ||
          (t.description ?? '').toLowerCase().includes(lower)
      )
    }

    return COLUMNS.map((col) => ({
      ...col,
      tasks: filtered
        .filter((t) => t.status === col.key)
        .sort((a, b) => {
          // P0 > P1 > P2 > P3 排序
          const pa = parseInt(a.priority.replace('P', ''))
          const pb = parseInt(b.priority.replace('P', ''))
          return pa - pb
        }),
    }))
  }, [tasks, filterPriority, searchText])

  // 拖拽结束
  const onDragEnd = (result: DropResult) => {
    if (!result.destination) return

    const { draggableId, destination } = result
    const newStatus = destination.droppableId as TaskStatus

    updateTask({
      ...tasks.find((t) => t.id === draggableId)!,
      status: newStatus,
      ...(newStatus === 'in_progress' ? { started_at: new Date().toISOString() } : {}),
      ...(newStatus === 'done' ? { completed_at: new Date().toISOString() } : {}),
    })
  }

  return (
    <div>
      {/* 工具栏 */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 20,
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>📋 任务看板</h2>
          <Tag
            style={{
              borderRadius: 12,
              background: '#6366f120',
              color: '#a78bfa',
              border: 'none',
            }}
          >
            {tasks.length} 个任务
          </Tag>
        </div>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <Input.Search
            placeholder="搜索任务..."
            allowClear
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
            size="middle"
          />
          <Select
            value={filterPriority}
            onChange={setFilterPriority}
            size="middle"
            style={{ width: 100 }}
            options={[
              { label: '全部', value: 'all' },
              { label: 'P0', value: 'P0' },
              { label: 'P1', value: 'P1' },
              { label: 'P2', value: 'P2' },
              { label: 'P3', value: 'P3' },
            ]}
          />
          <Button type="primary" icon={<PlusOutlined />} size="middle">
            新建任务
          </Button>
        </div>
      </div>

      {/* 看板 */}
      <DragDropContext onDragEnd={onDragEnd}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: 16,
            minHeight: 'calc(100vh - 220px)',
          }}
        >
          {columns.map((col) => (
            <div key={col.key}>
              {/* 列头 */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  marginBottom: 12,
                  padding: '10px 14px',
                  background: 'var(--color-bg-secondary)',
                  borderRadius: 'var(--radius-lg)',
                  border: '1px solid var(--color-border)',
                }}
              >
                <span style={{ fontSize: 16 }}>{col.icon}</span>
                <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--color-text-primary)' }}>
                  {col.title}
                </span>
                <Tag
                  style={{
                    marginLeft: 'auto',
                    borderRadius: 10,
                    background: col.color + '20',
                    color: col.color,
                    border: 'none',
                    fontSize: 12,
                    fontWeight: 600,
                  }}
                >
                  {col.tasks.length}
                </Tag>
              </div>

              {/* 可拖拽区域 */}
              <Droppable droppableId={col.key}>
                {(provided, snapshot) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                    style={{
                      minHeight: 200,
                      padding: '8px',
                      borderRadius: 'var(--radius-lg)',
                      background: snapshot.isDraggingOver
                        ? 'rgba(99, 102, 241, 0.05)'
                        : 'transparent',
                      border: snapshot.isDraggingOver
                        ? '2px dashed rgba(99, 102, 241, 0.3)'
                        : '2px dashed transparent',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    {col.tasks.length === 0 ? (
                      <div
                        style={{
                          textAlign: 'center',
                          padding: '40px 16px',
                          color: 'var(--color-text-muted)',
                          fontSize: 13,
                        }}
                      >
                        {snapshot.isDraggingOver ? '释放以移动到此处' : '暂无任务'}
                      </div>
                    ) : (
                      col.tasks.map((task, idx) => (
                        <TaskCard key={task.id} task={task} index={idx} />
                      ))
                    )}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </div>
          ))}
        </div>
      </DragDropContext>
    </div>
  )
}
