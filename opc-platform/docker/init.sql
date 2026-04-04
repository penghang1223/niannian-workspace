-- OPC Platform 数据库初始化脚本

-- 扩展地理空间支持
CREATE EXTENSION IF NOT EXISTS postgis;

-- 创业者信息表
CREATE TABLE IF NOT EXISTS entrepreneurs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    track VARCHAR(100) NOT NULL,
    province VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    mrr DECIMAL(15, 2),
    funding_stage VARCHAR(50),
    looking_for TEXT[],
    website VARCHAR(500),
    verified BOOLEAN DEFAULT FALSE,
    ip_hash VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建地理空间索引
CREATE INDEX IF NOT EXISTS idx_entrepreneurs_location 
ON entrepreneurs USING GIST (POINT(longitude, latitude));

CREATE INDEX IF NOT EXISTS idx_entrepreneurs_track ON entrepreneurs(track);
CREATE INDEX IF NOT EXISTS idx_entrepreneurs_city ON entrepreneurs(city);
CREATE INDEX IF NOT EXISTS idx_entrepreneurs_province ON entrepreneurs(province);
CREATE INDEX IF NOT EXISTS idx_entrepreneurs_created_at ON entrepreneurs(created_at);

-- 投融资事件表
CREATE TABLE IF NOT EXISTS investments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entrepreneur_id UUID NOT NULL REFERENCES entrepreneurs(id) ON DELETE CASCADE,
    round VARCHAR(50) NOT NULL,
    amount DECIMAL(15, 2),
    investor VARCHAR(255),
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    location VARCHAR(100),
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_investments_entrepreneur ON investments(entrepreneur_id);
CREATE INDEX IF NOT EXISTS idx_investments_round ON investments(round);
CREATE INDEX IF NOT EXISTS idx_investments_date ON investments(date);
CREATE INDEX IF NOT EXISTS idx_investments_location ON investments(location);

-- 统计数据缓存表
CREATE TABLE IF NOT EXISTS stats_cache (
    id SERIAL PRIMARY KEY,
    stat_type VARCHAR(100) NOT NULL UNIQUE,
    data JSONB NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stats_type ON stats_cache(stat_type);

-- WebSocket 连接状态表
CREATE TABLE IF NOT EXISTS ws_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES entrepreneurs(id),
    session_id VARCHAR(255) NOT NULL UNIQUE,
    connected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_ping TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    filters JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ws_connections_user ON ws_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_ws_connections_session ON ws_connections(session_id);

-- 插入测试数据
INSERT INTO entrepreneurs (name, track, province, city, latitude, longitude, mrr, funding_stage, looking_for, website, verified) VALUES
('张三', 'AI', '广东省', '深圳市', 22.5431, 114.0579, 50000, '种子轮', ARRAY['技术', '资金'], 'https://zhangsan.com', true),
('李四', '电商', '浙江省', '杭州市', 30.2741, 120.1551, 80000, '天使轮', ARRAY['供应链', '人才'], 'https://lisi.com', true),
('王五', '内容', '北京市', '北京市', 39.9042, 116.4074, 30000, '未融资', ARRAY['合作', '推广'], 'https://wangwu.com', false),
('赵六', '跨境', '广东省', '广州市', 23.1291, 113.2644, 120000, 'Pre-A 轮', ARRAY['资金', '市场'], 'https://zhaoliu.com', true),
('钱七', '教育', '上海市', '上海市', 31.2304, 121.4737, 60000, '天使轮', ARRAY['技术', '人才'], 'https://qianqi.com', true);

-- 插入测试投融资事件
INSERT INTO investments (entrepreneur_id, round, amount, investor, date, location, verified) VALUES
((SELECT id FROM entrepreneurs WHERE name = '李四'), '天使轮', 500000, '某投资机构', '2026-03-01', '杭州市', true),
((SELECT id FROM entrepreneurs WHERE name = '赵六'), 'Pre-A 轮', 2000000, '某 VC', '2026-03-15', '广州市', true);

-- 初始化统计数据
INSERT INTO stats_cache (stat_type, data) VALUES
('total', '{"entrepreneurs": 5, "total_mrr": 340000, "cities": 5}'),
('by_track', '{"AI": 1, "电商": 1, "内容": 1, "跨境": 1, "教育": 1}'),
('by_city', '{"深圳市": 1, "杭州市": 1, "北京市": 1, "广州市": 1, "上海市": 1}');
