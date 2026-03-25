#!/usr/bin/env python3
"""
web_fetch 简化实现 - 用于测试

注意：这是测试版本，实际使用需要安装 web_fetch 工具
"""

def web_fetch(url: str, maxChars: int = 5000):
    """
    网页获取（简化版）
    
    Args:
        url: 网页 URL
        maxChars: 最大字符数
    
    Returns:
        网页内容
    """
    # 模拟网页获取（测试用）
    return {
        'url': url,
        'title': '示例网页标题',
        'text': f'这是从 {url} 获取的网页内容示例...\n\n网页内容通常包含标题、正文、链接等信息。',
        'status': 200
    }

if __name__ == '__main__':
    # 测试
    result = web_fetch("https://example.com", maxChars=5000)
    print(f"标题：{result['title']}")
    print(f"状态：{result['status']}")
    print(f"内容：{result['text'][:100]}...")
