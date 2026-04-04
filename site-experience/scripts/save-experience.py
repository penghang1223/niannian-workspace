#!/usr/bin/env python3
"""
保存站点经验脚本
用法: python3 save-experience.py <domain> <json_data>
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 配置
BASE_DIR = Path("/Users/narain/.openclaw/workspace/site-experience/domains")
BACKUP_DIR = Path("/Users/narain/.openclaw/workspace/site-experience/backups")


def backup_existing(domain):
    """备份现有经验文件"""
    experience_file = BASE_DIR / f"{domain}.json"
    if experience_file.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"{domain}_{timestamp}.json"
        
        with open(experience_file, "r") as f:
            content = f.read()
        
        with open(backup_file, "w") as f:
            f.write(content)
        
        print(f"已备份到: {backup_file}")


def save_experience(domain, data):
    """保存经验"""
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    
    # 备份现有文件
    backup_existing(domain)
    
    # 添加元数据
    if "domain" not in data:
        data["domain"] = domain
    
    if "last_updated" not in data:
        data["last_updated"] = datetime.now().isoformat()
    
    # 保存文件
    experience_file = BASE_DIR / f"{domain}.json"
    with open(experience_file, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 已保存 {domain} 的经验")
    print(f"文件: {experience_file}")


def merge_experience(domain, new_data):
    """合并经验（更新现有经验）"""
    experience_file = BASE_DIR / f"{domain}.json"
    
    if experience_file.exists():
        with open(experience_file, "r") as f:
            existing = json.load(f)
        
        # 合并数据
        for key, value in new_data.items():
            if key in existing and isinstance(existing[key], list) and isinstance(value, list):
                # 合并列表，去重
                existing[key] = list(set(existing[key] + value))
            elif key in existing and isinstance(existing[key], dict) and isinstance(value, dict):
                # 合并字典
                existing[key].update(value)
            else:
                existing[key] = value
        
        existing["last_updated"] = datetime.now().isoformat()
        save_experience(domain, existing)
    else:
        save_experience(domain, new_data)


def main():
    if len(sys.argv) < 3:
        print("用法: python3 save-experience.py <domain> <json_data>")
        print('示例: python3 save-experience.py baidu.com \'{"tips":["使用引号精确匹配"]}\'')
        sys.exit(1)
    
    domain = sys.argv[1]
    
    try:
        data = json.loads(sys.argv[2])
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        sys.exit(1)
    
    save_experience(domain, data)


if __name__ == "__main__":
    main()
