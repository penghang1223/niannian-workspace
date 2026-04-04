# 站点经验系统

参考 web-access 项目的站点经验积累功能，为 OpenClaw 构建的站点操作经验库。

## 核心功能

1. **按域名存储操作经验** - URL模式、平台特征、已知陷阱
2. **跨session复用** - 经验持久化，避免重复踩坑
3. **智能加载** - 访问站点时自动加载相关经验
4. **经验更新** - 发现新经验时自动更新

## 目录结构

```
site-experience/
├── README.md           # 本文件
├── config.json         # 系统配置
├── domains/            # 按域名存储的经验
│   ├── baidu.com.json
│   ├── xiaohongshu.com.json
│   └── ...
└── scripts/            # 工具脚本
    ├── load-experience.py    # 加载经验
    ├── save-experience.py    # 保存经验
    └── search-experience.py  # 搜索经验
```

## 使用方法

### 在心跳时加载经验
```python
from site_experience import load_experience_for_domain

# 访问百度时加载经验
experience = load_experience_for_domain("baidu.com")
print(experience.get("tips", []))
```

### 保存新经验
```python
from site_experience import save_experience

# 保存百度搜索经验
save_experience("baidu.com", {
    "url_patterns": [
        "https://www.baidu.com/s?wd={query}",
        "https://www.baidu.com/s?wd={query}&pn={page}"
    ],
    "tips": [
        "搜索时使用引号可以精确匹配",
        "使用site:限定搜索范围"
    ],
    "traps": [
        "百度推广链接需要跳过",
        "某些页面有反爬机制"
    ]
})
```

## 经验格式

每个域名的经验文件格式：

```json
{
  "domain": "baidu.com",
  "last_updated": "2026-04-02T22:00:00+08:00",
  "url_patterns": [
    "https://www.baidu.com/s?wd={query}",
    "https://www.baidu.com/s?wd={query}&pn={page}"
  ],
  "platform_features": {
    "search": "百度搜索",
    "login_required": false,
    "anti_scraping": true
  },
  "tips": [
    "搜索时使用引号可以精确匹配",
    "使用site:限定搜索范围"
  ],
  "traps": [
    "百度推广链接需要跳过",
    "某些页面有反爬机制"
  ],
  "known_issues": [
    "搜索结果页面可能有动态加载"
  ],
  "success_patterns": [
    "使用web_search工具比直接抓取更可靠"
  ]
}
```
