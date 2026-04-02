#!/usr/bin/env python3
"""
search_fallback.py - 搜索引擎自动降级
多引擎依次尝试，确保搜索始终可用

用法：
    python3 scripts/search_fallback.py "搜索关键词"
    python3 scripts/search_fallback.py --test
    python3 scripts/search_fallback.py --status
"""

import json
import sys
import subprocess
import urllib.parse
import urllib.request
import re
import os
from typing import List, Dict, Optional


class SearchEngine:
    """搜索引擎基类"""
    def __init__(self, name: str, priority: int):
        self.name = name
        self.priority = priority
    
    def search(self, query: str, count: int = 5) -> Optional[List[Dict[str, str]]]:
        raise NotImplementedError


class BraveEngine(SearchEngine):
    """Brave Search API"""
    def __init__(self):
        super().__init__("Brave", priority=1)
        self.api_key = os.environ.get("BRAVE_API_KEY", "BSA3a8XP3owAy7KuKOZdoQKVNKrOKwF")
    
    def search(self, query: str, count: int = 5) -> Optional[List[Dict[str, str]]]:
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://api.search.brave.com/res/v1/web/search?q={encoded}&count={count}"
            
            req = urllib.request.Request(url, headers={
                "Accept": "application/json",
                "X-Subscription-Token": self.api_key
            })
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            results = []
            for item in data.get("web", {}).get("results", [])[:count]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("description", "")
                })
            
            return results if results else None
        except Exception as e:
            print(f"  [{self.name}] 失败: {e}", file=sys.stderr)
            return None


class GoogleEngine(SearchEngine):
    """Google 搜索"""
    def __init__(self):
        super().__init__("Google", priority=2)
    
    def search(self, query: str, count: int = 5) -> Optional[List[Dict[str, str]]]:
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://www.google.com/search?q={encoded}&num={count}"
            
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "text/html",
                "Accept-Language": "zh-CN,zh;q=0.9"
            })
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            
            results = []
            pattern = r'<a[^>]*href="/url\?q=([^&"]+)"[^>]*>(.*?)</a>'
            matches = re.findall(pattern, html, re.DOTALL)
            
            for url, title in matches[:count]:
                title = re.sub(r'<[^>]+>', '', title).strip()
                if title and url and not url.startswith("https://www.google.com"):
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": ""
                    })
            
            return results if results else None
        except Exception as e:
            print(f"  [{self.name}] 失败: {e}", file=sys.stderr)
            return None


class BingEngine(SearchEngine):
    """Bing 搜索"""
    def __init__(self):
        super().__init__("Bing", priority=3)
    
    def search(self, query: str, count: int = 5) -> Optional[List[Dict[str, str]]]:
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://www.bing.com/search?q={encoded}&count={count}"
            
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "text/html",
                "Accept-Language": "zh-CN,zh;q=0.9"
            })
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            
            results = []
            pattern = r'<a[^>]*href="(https?://[^"]+)"[^>]*><h2>(.*?)</h2></a>'
            matches = re.findall(pattern, html, re.DOTALL)
            
            for url, title in matches[:count]:
                title = re.sub(r'<[^>]+>', '', title).strip()
                if title and url:
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": ""
                    })
            
            return results if results else None
        except Exception as e:
            print(f"  [{self.name}] 失败: {e}", file=sys.stderr)
            return None


class DuckDuckGoEngine(SearchEngine):
    """DuckDuckGo API"""
    def __init__(self):
        super().__init__("DuckDuckGo", priority=4)
    
    def search(self, query: str, count: int = 5) -> Optional[List[Dict[str, str]]]:
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
            
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            })
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            results = []
            
            # Abstract
            if data.get("Abstract"):
                results.append({
                    "title": data.get("Heading", query),
                    "url": data.get("AbstractURL", ""),
                    "snippet": data.get("Abstract", "")
                })
            
            # Related topics
            for topic in data.get("RelatedTopics", [])[:count-len(results)]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "title": topic.get("Text", "")[:80],
                        "url": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", "")
                    })
            
            return results if results else None
        except Exception as e:
            print(f"  [{self.name}] 失败: {e}", file=sys.stderr)
            return None


class SearXEngine(SearchEngine):
    """SearX 公共实例"""
    def __init__(self):
        super().__init__("SearX", priority=5)
        self.instances = [
            "https://searx.be",
            "https://search.sapti.me",
            "https://searx.tiekoetter.com"
        ]
    
    def search(self, query: str, count: int = 5) -> Optional[List[Dict[str, str]]]:
        for instance in self.instances:
            try:
                encoded = urllib.parse.quote(query)
                url = f"{instance}/search?q={encoded}&format=json"
                
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
                })
                
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                
                results = []
                for item in data.get("results", [])[:count]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("content", "")
                    })
                
                if results:
                    return results
            except:
                continue
        
        print(f"  [{self.name}] 所有实例均失败", file=sys.stderr)
        return None


class SearchFallback:
    """搜索降级管理器"""
    
    def __init__(self):
        self.engines = [
            BraveEngine(),
            GoogleEngine(),
            BingEngine(),
            DuckDuckGoEngine(),
            SearXEngine(),
        ]
        self.engines.sort(key=lambda e: e.priority)
        self.last_engine = None
    
    def search(self, query: str, count: int = 5) -> Dict:
        """按优先级依次尝试搜索引擎"""
        print(f"🔍 搜索: {query}", file=sys.stderr)
        
        for engine in self.engines:
            print(f"  尝试 {engine.name}...", file=sys.stderr)
            results = engine.search(query, count)
            
            if results:
                print(f"  ✅ {engine.name} 成功，返回 {len(results)} 条结果", file=sys.stderr)
                self.last_engine = engine.name
                return {
                    "success": True,
                    "engine": engine.name,
                    "query": query,
                    "results": results
                }
        
        print(f"  ❌ 所有搜索引擎均失败", file=sys.stderr)
        return {
            "success": False,
            "engine": None,
            "query": query,
            "results": []
        }
    
    def get_status(self) -> Dict:
        """获取所有搜索引擎状态"""
        status = {}
        for engine in self.engines:
            test_result = engine.search("test", 1)
            status[engine.name] = "✅ 可用" if test_result else "❌ 不可用"
        return status


def test_search():
    """测试搜索降级"""
    print("=" * 60)
    print("搜索降级测试")
    print("=" * 60)
    
    fallback = SearchFallback()
    
    # Test status
    print("\n=== 引擎状态 ===")
    status = fallback.get_status()
    for name, state in status.items():
        print(f"  {state} {name}")
    
    # Test search
    print("\n=== 搜索测试 ===")
    result = fallback.search("Python Agent Framework", 3)
    
    if result["success"]:
        print(f"\n✅ 搜索成功 (引擎: {result['engine']})")
        for i, r in enumerate(result["results"], 1):
            print(f"  {i}. {r['title']}")
            print(f"     {r['url']}")
            if r.get("snippet"):
                print(f"     {r['snippet'][:80]}...")
    else:
        print("\n❌ 搜索失败")
    
    print("\n✅ 测试完成!")


if __name__ == "__main__":
    if "--test" in sys.argv:
        test_search()
    elif "--status" in sys.argv:
        fallback = SearchFallback()
        status = fallback.get_status()
        for name, state in status.items():
            print(f"{state} {name}")
    elif len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        fallback = SearchFallback()
        result = fallback.search(query)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("用法:")
        print("  python3 scripts/search_fallback.py '搜索关键词'")
        print("  python3 scripts/search_fallback.py --test")
        print("  python3 scripts/search_fallback.py --status")
