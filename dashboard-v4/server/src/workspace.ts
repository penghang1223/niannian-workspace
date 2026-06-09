import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const WORKSPACE_ROOT = path.resolve(__dirname, '..', '..', '..');

type QueueSummary = {
  pending: number;
  processing: number;
  done: number;
};

type AgentRegistryEntry = {
  id: string;
  display_name: string;
  role: string;
};

export type WorkspaceSummary = {
  root: string;
  generated_at: string;
  agents: {
    total: number;
    ids: string[];
    registry_total: number;
    registry: AgentRegistryEntry[];
  };
  skills: {
    total: number;
    root_skills: number;
    catalog_skills: number;
  };
  memory: {
    files: number;
    daily_notes: number;
    latest_daily_note: string | null;
  };
  knowledge: {
    files: number;
  };
  queues: {
    inbox: QueueSummary;
    outbox: QueueSummary;
    tasks_files: number;
  };
  docs: {
    files: number;
  };
  apps: {
    dashboard_v4: boolean;
    legacy_dashboard: boolean;
  };
};

function safeReadDir(relativePath: string): fs.Dirent[] {
  try {
    return fs.readdirSync(path.join(WORKSPACE_ROOT, relativePath), { withFileTypes: true });
  } catch {
    return [];
  }
}

function countFiles(relativePath: string): number {
  const root = path.join(WORKSPACE_ROOT, relativePath);
  let count = 0;

  function walk(dir: string) {
    let entries: fs.Dirent[];
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }

    for (const entry of entries) {
      if (entry.name === 'node_modules' || entry.name === 'dist' || entry.name === '.git') continue;
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(fullPath);
      else if (entry.isFile()) count += 1;
    }
  }

  walk(root);
  return count;
}

function countQueue(relativePath: string): QueueSummary {
  return {
    pending: countFiles(path.join(relativePath, 'pending')),
    processing: countFiles(path.join(relativePath, 'processing')),
    done: countFiles(path.join(relativePath, 'done')),
  };
}

function countSkillManifests(relativePath: string): number {
  return safeReadDir(relativePath).filter((entry) => {
    if (!entry.isDirectory()) return false;
    return fs.existsSync(path.join(WORKSPACE_ROOT, relativePath, entry.name, 'SKILL.md'));
  }).length;
}

function readAgentRegistry(): AgentRegistryEntry[] {
  const registryPath = path.join(WORKSPACE_ROOT, 'agents', 'registry', 'agents.json');
  try {
    const parsed = JSON.parse(fs.readFileSync(registryPath, 'utf8')) as AgentRegistryEntry[];
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((agent) => agent && typeof agent.id === 'string')
      .map((agent) => ({
        id: agent.id,
        display_name: agent.display_name || agent.id,
        role: agent.role || 'Agent',
      }))
      .sort((a, b) => a.id.localeCompare(b.id));
  } catch {
    return [];
  }
}

export function getWorkspaceSummary(): WorkspaceSummary {
  const agentIds = safeReadDir('agents')
    .filter((entry) => entry.isDirectory() && entry.name !== 'registry')
    .map((entry) => entry.name)
    .sort();
  const agentRegistry = readAgentRegistry();

  const dailyNotes = safeReadDir('memory')
    .filter((entry) => entry.isFile() && /^\d{4}-\d{2}-\d{2}.*\.md$/.test(entry.name))
    .map((entry) => entry.name)
    .sort();

  const rootSkillDirs = safeReadDir('.').filter((entry) => {
    if (!entry.isDirectory()) return false;
    return fs.existsSync(path.join(WORKSPACE_ROOT, entry.name, 'SKILL.md'));
  }).length;
  const catalogSkillDirs = countSkillManifests('skills');

  return {
    root: WORKSPACE_ROOT,
    generated_at: new Date().toISOString(),
    agents: {
      total: agentIds.length,
      ids: agentIds,
      registry_total: agentRegistry.length,
      registry: agentRegistry,
    },
    skills: {
      total: rootSkillDirs + catalogSkillDirs,
      root_skills: rootSkillDirs,
      catalog_skills: catalogSkillDirs,
    },
    memory: {
      files: countFiles('memory'),
      daily_notes: dailyNotes.length,
      latest_daily_note: dailyNotes.at(-1) ?? null,
    },
    knowledge: {
      files: countFiles('knowledge-base'),
    },
    queues: {
      inbox: countQueue(path.join('workspace', 'inbox')),
      outbox: countQueue(path.join('workspace', 'outbox')),
      tasks_files: countFiles(path.join('workspace', 'tasks')),
    },
    docs: {
      files: countFiles('docs'),
    },
    apps: {
      dashboard_v4: fs.existsSync(path.join(WORKSPACE_ROOT, 'dashboard-v4')),
      legacy_dashboard: fs.existsSync(path.join(WORKSPACE_ROOT, 'dashboard')),
    },
  };
}
