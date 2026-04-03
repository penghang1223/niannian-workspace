/**
 * OPC 平台后端服务
 * 主应用入口
 */

require('dotenv').config();
const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:5173';
const PORT = Number(process.env.PORT) || 3001;

const TRACKS = ['AI', '电商', '内容', '跨境', '教育'];

// 初始化数据库连接
const db = require('./database');
const Entrepreneur = require('./models/entrepreneur');
const User = require('./models/user');
const { authenticateToken } = require('./middleware/auth');

// 初始化数据
async function initializeData() {
  try {
    // 检查是否有数据，如果没有则插入种子数据
    const count = await Entrepreneur.count();
    if (count === 0) {
      console.log('🌱 初始化企业家数据...');

      const seedData = [
        {
          id: 'opc-001',
          name: '林一舟',
          city: '北京',
          province: '北京',
          track: 'AI',
          lat: 39.9042,
          lng: 116.4074,
          mrr: 180000,
          createdAt: new Date(Date.now() - 40 * 60 * 1000).toISOString()
        },
        {
          id: 'opc-002',
          name: '苏语宁',
          city: '上海',
          province: '上海',
          track: '跨境',
          lat: 31.2304,
          lng: 121.4737,
          mrr: 132000,
          createdAt: new Date(Date.now() - 75 * 60 * 1000).toISOString()
        },
        {
          id: 'opc-003',
          name: '周景行',
          city: '深圳',
          province: '广东',
          track: '电商',
          lat: 22.5431,
          lng: 114.0579,
          mrr: 96000,
          createdAt: new Date(Date.now() - 130 * 60 * 1000).toISOString()
        },
        {
          id: 'opc-004',
          name: '顾南栀',
          city: '杭州',
          province: '浙江',
          track: '内容',
          lat: 30.2741,
          lng: 120.1551,
          mrr: 56000,
          createdAt: new Date(Date.now() - 180 * 60 * 1000).toISOString()
        },
        {
          id: 'opc-005',
          name: '沈知遥',
          city: '广州',
          province: '广东',
          track: '教育',
          lat: 23.1291,
          lng: 113.2644,
          mrr: 88000,
          createdAt: new Date(Date.now() - 240 * 60 * 1000).toISOString()
        },
        {
          id: 'opc-006',
          name: '唐牧川',
          city: '成都',
          province: '四川',
          track: 'AI',
          lat: 30.5728,
          lng: 104.0668,
          mrr: 74000,
          createdAt: new Date(Date.now() - 310 * 60 * 1000).toISOString()
        },
        {
          id: 'opc-007',
          name: '许星遥',
          city: '武汉',
          province: '湖北',
          track: '内容',
          lat: 30.5928,
          lng: 114.3055,
          mrr: 47000,
          createdAt: new Date(Date.now() - 420 * 60 * 1000).toISOString()
        },
        {
          id: 'opc-008',
          name: '乔见山',
          city: '西安',
          province: '陕西',
          track: '跨境',
          lat: 34.3416,
          lng: 108.9398,
          mrr: 61000,
          createdAt: new Date(Date.now() - 520 * 60 * 1000).toISOString()
        },
        {
          id: 'opc-009',
          name: '贺知微',
          city: '南京',
          province: '江苏',
          track: '电商',
          lat: 32.0603,
          lng: 118.7969,
          mrr: 53000,
          createdAt: new Date(Date.now() - 610 * 60 * 1000).toISOString()
        },
        {
          id: 'opc-010',
          name: '宋清晏',
          city: '厦门',
          province: '福建',
          track: '教育',
          lat: 24.4798,
          lng: 118.0894,
          mrr: 39000,
          createdAt: new Date(Date.now() - 760 * 60 * 1000).toISOString()
        },
        {
          id: 'opc-011',
          name: '柳时安',
          city: '苏州',
          province: '江苏',
          track: 'AI',
          lat: 31.2989,
          lng: 120.5853,
          mrr: 82000,
          createdAt: new Date(Date.now() - 890 * 60 * 1000).toISOString()
        },
        {
          id: 'opc-012',
          name: '程越',
          city: '长沙',
          province: '湖南',
          track: '内容',
          lat: 28.2282,
          lng: 112.9388,
          mrr: 44000,
          createdAt: new Date(Date.now() - 1020 * 60 * 1000).toISOString()
        }
      ];

      for (const data of seedData) {
        await Entrepreneur.create(data);
      }
      console.log('✅ 种子数据初始化完成');
    }
  } catch (error) {
    console.error('❌ 数据初始化失败:', error);
  }
}

// 启动时初始化数据
initializeData();

function numberOrZero(value) {
  const parsedValue = Number(value);
  return Number.isFinite(parsedValue) ? parsedValue : 0;
}

function startOfToday() {
  const date = new Date();
  date.setHours(0, 0, 0, 0);
  return date;
}

function deriveStats(dataset) {
  const cities = new Set();
  const tracks = new Set();
  const today = startOfToday();

  let totalMrr = 0;
  let todayNew = 0;

  dataset.forEach((item) => {
    if (item.city) {
      cities.add(item.city);
    }

    if (item.track) {
      tracks.add(item.track);
    }

    totalMrr += numberOrZero(item.mrr);

    if (item.createdAt) {
      const createdAt = new Date(item.createdAt);
      if (!Number.isNaN(createdAt.getTime()) && createdAt >= today) {
        todayNew += 1;
      }
    }
  });

  return {
    totalEntrepreneurs: dataset.length,
    todayNew,
    coveredCities: cities.size,
    activeTracks: tracks.size,
    totalMrr,
    lastUpdated: new Date().toISOString(),
    source: 'api'
  };
}

function normalizeKeyword(value) {
  return String(value || '').trim().toLowerCase();
}

function filterEntrepreneurs(dataset, filters = {}) {
  const search = normalizeKeyword(filters.search);
  const track = String(filters.track || '').trim();

  return dataset.filter((item) => {
    const matchesTrack = !track || track === 'ALL' || item.track === track;
    const matchesSearch = !search || [
      item.name,
      item.city,
      item.province,
      item.track
    ].filter(Boolean).some((field) => field.toLowerCase().includes(search));

    return matchesTrack && matchesSearch;
  });
}

function sortByCreatedAtDesc(dataset) {
  return [...dataset].sort((left, right) => {
    const leftTime = new Date(left.createdAt || 0).getTime();
    const rightTime = new Date(right.createdAt || 0).getTime();
    return rightTime - leftTime;
  });
}

function createMockRegistration() {
  const templatePool = [
    { city: '青岛', province: '山东', lat: 36.0671, lng: 120.3826 },
    { city: '合肥', province: '安徽', lat: 31.8206, lng: 117.2272 },
    { city: '郑州', province: '河南', lat: 34.7473, lng: 113.6249 },
    { city: '宁波', province: '浙江', lat: 29.8683, lng: 121.5440 },
    { city: '天津', province: '天津', lat: 39.3434, lng: 117.3616 }
  ];

  const names = ['陈曜', '叶临风', '顾闻溪', '纪知远', '孟时宜'];
  const location = templatePool[mockSequence % templatePool.length];
  const track = TRACKS[mockSequence % TRACKS.length];
  const name = names[mockSequence % names.length];

  mockSequence += 1;

  return {
    id: `opc-${String(mockSequence).padStart(3, '0')}`,
    name,
    city: location.city,
    province: location.province,
    track,
    lat: location.lat,
    lng: location.lng,
    mrr: 30000 + (mockSequence % 6) * 9000,
    createdAt: new Date().toISOString()
  };
}

const app = express();
const server = http.createServer(app);

const io = new Server(server, {
  cors: {
    origin: FRONTEND_URL,
    methods: ['GET', 'POST']
  },
  pingTimeout: 60000,
  pingInterval: 25000
});

app.use(helmet());
app.use(cors());
app.use(express.json());

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100
});
app.use('/api/', limiter);

app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    service: 'OPC Platform Backend'
  });
});

app.get('/api/entrepreneurs', async (req, res) => {
  try {
    const { search, track, limit = 50, offset = 0 } = req.query;
    const filters = { search, track, limit, offset };

    const entrepreneurs = await Entrepreneur.findAll(filters);
    const total = await Entrepreneur.count(filters);

    res.json({
      data: {
        items: entrepreneurs,
        pagination: {
          total,
          limit: parseInt(limit),
          offset: parseInt(offset)
        }
      }
    });
  } catch (error) {
    res.status(500).json({ error: '获取企业家列表失败' });
  }
});

app.get('/api/registrations', async (req, res) => {
  try {
    const { search, track, limit = 50, offset = 0 } = req.query;
    const filters = { search, track, limit, offset };

    const entrepreneurs = await Entrepreneur.findAll(filters);
    const total = await Entrepreneur.count(filters);

    res.json({
      entrepreneurs,
      pagination: {
        total,
        limit: parseInt(limit),
        offset: parseInt(offset)
      }
    });
  } catch (error) {
    res.status(500).json({ error: '获取注册列表失败' });
  }
});

app.get('/api/dashboard/entrepreneurs', async (req, res) => {
  try {
    const { search, track, limit = 50, offset = 0 } = req.query;
    const filters = { search, track, limit, offset };

    const entrepreneurs = await Entrepreneur.findAll(filters);
    const total = await Entrepreneur.count(filters);

    res.json({
      list: entrepreneurs,
      pagination: {
        total,
        limit: parseInt(limit),
        offset: parseInt(offset)
      }
    });
  } catch (error) {
    res.status(500).json({ error: '获取仪表板企业家列表失败' });
  }
});

app.get('/api/stats', async (req, res) => {
  try {
    const stats = await Entrepreneur.getStats();
    res.json({ data: stats });
  } catch (error) {
    res.status(500).json({ error: '获取统计数据失败' });
  }
});

app.get('/api/stats/total', async (req, res) => {
  try {
    const stats = await Entrepreneur.getStats();
    res.json(stats);
  } catch (error) {
    res.status(500).json({ error: '获取总统计数据失败' });
  }
});

app.get('/api/dashboard/stats', async (req, res) => {
  try {
    const stats = await Entrepreneur.getStats();
    res.json({ stats });
  } catch (error) {
    res.status(500).json({ error: '获取仪表板统计数据失败' });
  }
});

app.post('/api/registrations', async (req, res) => {
  try {
    const registrationData = {
      ...req.body,
      createdAt: new Date().toISOString()
    };

    const registration = await Entrepreneur.create(registrationData);
    const stats = await Entrepreneur.getStats();

    io.to('registrations').emit('new_registration', {
      ...registration,
      stats
    });
    io.emit('stats_update', stats);

    res.status(201).json({
      message: '注册创建成功',
      registration,
      stats
    });
  } catch (error) {
    res.status(500).json({ error: '创建注册失败' });
  }
});

// 用户注册
app.post('/api/auth/register', async (req, res) => {
  try {
    const { name, email, password } = req.body;

    if (!name || !email || !password) {
      return res.status(400).json({ error: '缺少必要字段' });
    }

    const user = await User.create({ name, email, password });

    res.status(201).json({
      message: '注册成功',
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
        role: user.role
      }
    });
  } catch (error) {
    if (error.message === '邮箱已存在') {
      res.status(409).json({ error: '邮箱已存在' });
    } else {
      res.status(500).json({ error: '注册失败' });
    }
  }
});

// 用户登录
app.post('/api/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: '缺少必要字段' });
    }

    const user = await User.validatePassword(email, password);

    if (!user) {
      return res.status(401).json({ error: '邮箱或密码错误' });
    }

    const token = generateToken(user);

    res.json({
      message: '登录成功',
      token,
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
        role: user.role
      }
    });
  } catch (error) {
    res.status(500).json({ error: '登录失败' });
  }
});

// 获取当前用户信息
app.get('/api/auth/me', authenticateToken, async (req, res) => {
  try {
    const user = await User.findById(req.user.id);
    res.json(user);
  } catch (error) {
    res.status(500).json({ error: '获取用户信息失败' });
  }
});

// 受保护的企业家列表
app.get('/api/entrepreneurs/protected', authenticateToken, async (req, res) => {
  try {
    const { search, track, limit = 50, offset = 0 } = req.query;
    const filters = { search, track, limit, offset };

    const entrepreneurs = await Entrepreneur.findAll(filters);
    const total = await Entrepreneur.count(filters);

    res.json({
      data: {
        items: entrepreneurs,
        pagination: {
          total,
          limit: parseInt(limit),
          offset: parseInt(offset)
        }
      }
    });
  } catch (error) {
    res.status(500).json({ error: '获取受保护的企业家列表失败' });
  }
});

io.on('connection', async (socket) => {
  console.log('客户端连接:', socket.id);

  try {
    const entrepreneurs = await Entrepreneur.findAll();
    socket.emit('initial_data', {
      entrepreneurs: sortByCreatedAtDesc(entrepreneurs),
      stats: deriveStats(entrepreneurs)
    });
  } catch (error) {
    console.error('获取初始数据失败:', error);
  }

  socket.on('subscribe:registration', async () => {
    socket.join('registrations');
    try {
      const entrepreneurs = await Entrepreneur.findAll();
      socket.emit('initial_data', {
        entrepreneurs: sortByCreatedAtDesc(entrepreneurs),
        stats: deriveStats(entrepreneurs)
      });
      console.log('客户端订阅注册事件:', socket.id);
    } catch (error) {
      console.error('获取注册数据失败:', error);
    }
  });

  socket.on('subscribe:investment', async () => {
    socket.join('investments');
    try {
      const entrepreneurs = await Entrepreneur.findAll();
      socket.emit('stats_update', deriveStats(entrepreneurs));
      console.log('客户端订阅投融资事件:', socket.id);
    } catch (error) {
      console.error('获取投融资数据失败:', error);
    }
  });

  socket.on('disconnect', () => {
    console.log('客户端断开:', socket.id);
  });
});

function broadcastNewRegistration(data) {
  io.to('registrations').emit('new_registration', data);
  console.log('广播新注册事件:', data);
}

function broadcastInvestment(data) {
  io.to('investments').emit('new_investment', data);
  console.log('广播投融资事件:', data);
}

app.set('io', io);
app.set('broadcastNewRegistration', broadcastNewRegistration);
app.set('broadcastInvestment', broadcastInvestment);

function startServer(port = PORT) {
  return server.listen(port, () => {
    console.log(`✅ OPC 平台后端服务启动在端口 ${port}`);
    console.log(`📊 健康检查：http://localhost:${port}/api/health`);
    console.log(`🔌 WebSocket: ws://localhost:${port}`);
  });
}

if (require.main === module) {
  startServer();
}

module.exports = {
  app,
  io,
  server,
  startServer,
  deriveStats,
  filterEntrepreneurs
};
