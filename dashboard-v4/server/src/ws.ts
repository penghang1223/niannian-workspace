import type { FastifyInstance } from 'fastify';
import type { DB } from './db.js';
import { WebSocket } from 'ws';

const clients = new Set<WebSocket>();

export async function registerWebSocket(app: FastifyInstance, db: DB) {
  await app.register(import('@fastify/websocket'));

  app.get('/ws', { websocket: true }, (connection, _req) => {
    const ws = connection as unknown as WebSocket;
    clients.add(ws);
    console.log(`📡 WebSocket client connected (total: ${clients.size})`);

    ws.on('message', (msg) => {
      try {
        const data = JSON.parse(msg.toString());
        handleWsMessage(data, ws, db);
      } catch (e) {
        ws.send(JSON.stringify({ type: 'error', message: 'Invalid JSON' }));
      }
    });

    ws.on('close', () => {
      clients.delete(ws);
      console.log(`📡 WebSocket client disconnected (total: ${clients.size})`);
    });

    // Send initial state
    const agents = db.prepare('SELECT * FROM agents').all();
    const tasks = db.prepare('SELECT * FROM tasks').all();
    ws.send(JSON.stringify({ type: 'init', data: { agents, tasks } }));
  });
}

function handleWsMessage(data: any, ws: WebSocket, db: DB) {
  switch (data.type) {
    case 'ping':
      ws.send(JSON.stringify({ type: 'pong' }));
      break;
    case 'subscribe':
      ws.send(JSON.stringify({ type: 'subscribed', channel: data.channel }));
      break;
  }
}

export function broadcast(type: string, data: any) {
  const msg = JSON.stringify({ type, data, timestamp: new Date().toISOString() });
  for (const ws of clients) {
    if (ws.readyState === 1) {
      ws.send(msg);
    }
  }
}
