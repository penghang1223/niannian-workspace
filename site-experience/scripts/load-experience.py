#!/usr/bin/env python3
"""
加载站点经验脚本
用法: python3 load-experience.py <domain>
"""

import json
import os
import sys
from pathlib import Path

# 配置
BASE_DIR = Path("/Users/narain/.openclaw/workspace/site-experience/domains")
CONFIG_FILE = Path("/Users/narain/.openclaw/workspace/site-experience/config.json")


def load_config():
    """加载配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def load_experience(domain):
    """加载指定域名的经验"""
    # 精确匹配
    experience_file = BASE_DIR / f"{domain}.json"
    if experience_file.exists():
        with open(experience_file, "r") as f:
            return json.load(f)
    
    # 通配符匹配（如 baidu.com 匹配 www.baidu.com）
    for file in BASE_DIR.glob("*.json"):
        file_domain = file.stem
        if domain.endswith(file_domain) or file_domain.endswith(domain):
            with open(file, "r") as f:
                return json.load(f)
    
    return None


def format_experience(experience):
    """格式化经验输出"""
    if not experience:
        return "未找到该域名的经验"
    
    output = []
    output.append(f"域名: {experience.get('domain', 'unknown')}")
    output.append(f"最后更新: {experience.get('last_updated', 'unknown')}")
    
    if experience.get("url_patterns"):
        output.append("\nURL模式:")
        for pattern in experience["url_patterns"]:
            output.append(f"  - {pattern}")
    
    if experience.get("tips"):
        output.append("\n💡 提示:")
        for tip in experience["tips"]:
            output.append(f"  - {tip}")
    
    if experience.get("traps"):
        output.append("\n⚠️ 陷阱:")
        for trap in experience["traps"]:
            output.append(f"  - {trap}")
    
    if experience.get("known_issues"):
        output.append("\n❓ 已知问题:")
        for issue in experience["known_issues"]:
            output.append(f"  - {issue}")
    
    if experience.get("success_patterns"):
        output.append("\n✅ 成功模式:")
        for pattern in experience["success_patterns"]:
            output.append(f"  - {pattern}")
    
    return "\n".join(output)


def main():
    if len(sys.argv) < 2:
        print("用法: python3 load-experience.py <domain>")
        print("示例: python3 load-experience.py baidu.com")
        sys.exit(1)
    
    domain = sys.argv[1]
    experience = load_experience(domain)
    
    if experience:
        print(format_experience(experience))
    else:
        print(f"未找到 {domain} 的经验")
        print("\n可用域名:")
        if BASE_DIR.exists():
            for file in sorted(BASE_DIR.glob("*.json")):
                print(f"  - {file.stem}")


if __name__ == "__main__":
    main()
