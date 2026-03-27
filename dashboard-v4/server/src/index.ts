import Fastify from 'fastify';
import cors from '@fastify/cors';
import { initDatabase } from './db.js';
import { registerRoutes } from './routes.js';
import { registerWebSocket } from './ws.js';

const PORT = Number(process.env.PORT) || 3456;

async function main() {
  const app = Fastify({ logger: true });
  
  await app.register(cors, { origin: '*' });
  
  const db = initDatabase();
  await registerRoutes(app, db);
  await registerWebSocket(app, db);

  app.get('/api/health', async () => ({
    status: 'ok',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  }));

  try {
    await app.listen({ port: PORT, host: '0.0.0.0' });
    console.log(`🚀 Dashboard v4 Server running on http://localhost:${PORT}`);
  } catch (err) {
    app.log.error(err);
    process.exit(1);
  }
}

main();
