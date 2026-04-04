const db = require('../src/database');

async function migrate() {
  try {
    console.log('开始数据库迁移...');

    // 创建 users 表
    await db.query(`
      CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(20) DEFAULT 'user',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // 创建 entrepreneurs 表
    await db.query(`
      CREATE TABLE IF NOT EXISTS entrepreneurs (
        id VARCHAR(20) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        city VARCHAR(50) NOT NULL,
        province VARCHAR(50) NOT NULL,
        track VARCHAR(50) NOT NULL,
        lat DECIMAL(10, 8) NOT NULL,
        lng DECIMAL(11, 8) NOT NULL,
        mrr INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // 创建 investments 表
    await db.query(`
      CREATE TABLE IF NOT EXISTS investments (
        id SERIAL PRIMARY KEY,
        entrepreneur_id VARCHAR(20) REFERENCES entrepreneurs(id) ON DELETE CASCADE,
        investor_name VARCHAR(100) NOT NULL,
        amount INTEGER NOT NULL,
        round VARCHAR(50),
        date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // 创建索引
    await db.query('CREATE INDEX IF NOT EXISTS idx_entrepreneurs_track ON entrepreneurs(track)');
    await db.query('CREATE INDEX IF NOT EXISTS idx_entrepreneurs_city ON entrepreneurs(city)');
    await db.query('CREATE INDEX IF NOT EXISTS idx_entrepreneurs_created_at ON entrepreneurs(created_at)');

    console.log('✅ 数据库迁移完成');
  } catch (error) {
    console.error('❌ 数据库迁移失败:', error);
    process.exit(1);
  }
}

migrate();