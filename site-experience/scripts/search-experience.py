#!/usr/bin/env python3
"""
搜索站点经验脚本
用法: python3 search-experience.py <keyword>
"""

import json
import os
import sys
from pathlib import Path

# 配置
BASE_DIR = Path("/Users/narain/.openclaw/workspace/site-experience/domains")


def search_experience(keyword):
    """搜索经验"""
    results = []
    
    if not BASE_DIR.exists():
        return results
    
    for file in BASE_DIR.glob("*.json"):
        with open(file, "r") as f:
            experience = json.load(f)
        
        # 搜索所有字段
        matches = []
        
        # 搜索域名
        if keyword.lower() in experience.get("domain", "").lower():
            matches.append(f"域名: {experience['domain']}")
        
        # 搜索URL模式
        for pattern in experience.get("url_patterns", []):
            if keyword.lower() in pattern.lower():
                matches.append(f"URL模式: {pattern}")
        
        # 搜索提示
        for tip in experience.get("tips", []):
            if keyword.lower() in tip.lower():
                matches.append(f"提示: {tip}")
        
        # 搜索陷阱
        for trap in experience.get("traps", []):
            if keyword.lower() in trap.lower():
                matches.append(f"陷阱: {trap}")
        
        # 搜索已知问题
        for issue in experience.get("known_issues", []):
            if keyword.lower() in issue.lower():
                matches.append(f"已知问题: {issue}")
        
        # 搜索成功模式
        for pattern in experience.get("success_patterns", []):
            if keyword.lower() in pattern.lower():
                matches.append(f"成功模式: {pattern}")
        
        if matches:
            results.append({
                "domain": experience.get("domain", file.stem),
                "matches": matches
            })
    
    return results


def main():
    if len(sys.argv) < 2:
        print("用法: python3 search-experience.py <keyword>")
        print("示例: python3 search-experience.py 登录")
        sys.exit(1)
    
    keyword = sys.argv[1]
    results = search_experience(keyword)
    
    if results:
        print(f"搜索 '{keyword}' 找到 {len(results)} 个结果:\n")
        for result in results:
            print(f"📁 {result['domain']}:")
            for match in result["matches"]:
                print(f"  - {match}")
            print()
    else:
        print(f"未找到包含 '{keyword}' 的经验")


if __name__ == "__main__":
    main()
