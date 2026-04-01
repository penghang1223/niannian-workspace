"""
Debug script to test streaming detection
"""

import sys
import os
import asyncio
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from scripts.streaming_executor import StreamingToolDetector, StreamingToolExecutor, ToolBlock, create_tool_definition

from scripts.streaming_executor import ToolResult

async def execute_read_file(block: ToolBlock):
    """Mock read file tool"""
    file_path = block.input.get("file_path", "unknown")
    print(f"📖 Reading file: {file_path}")
    await asyncio.sleep(0.1)  # Simulate I/O delay
    return ToolResult(
        tool_use_id=block.id,
        tool_name="read_file",
        content=f"Content of {file_path}",
    )

async def execute_web_search(block: ToolBlock):
    """Mock web search tool"""
    query = block.input.get("query", "")
    print(f"🔍 Searching: {query}")
    await asyncio.sleep(0.1)  # Simulate network delay
    return ToolResult(
        tool_use_id=block.id,
        tool_name="web_search", 
        content=f"Results for {query}",
    )

def create_tool_registry():
    """Create mock tool registry"""
    return {
        "read_file": create_tool_definition(
            name="read_file",
            executor=execute_read_file,
            description="Read file content",
            is_concurrency_safe=True,
        ),
        "web_search": create_tool_definition(
            name="web_search",
            executor=execute_web_search,
            description="Search web",
            is_concurrency_safe=True,
        ),
    }

def test_streaming_detection():
    """Test streaming detection with debug output"""
    
    tools = create_tool_registry()
    executor = StreamingToolExecutor(tools)
    detector = StreamingToolDetector(executor)

    # Simulate LLM streaming output
    chunks = [
        '好的，我来帮你查看这些文件。首先',
        '让我读取项目结构...\n',
        '{"type": "tool_use", "id": "toolu_001", "name": "read_file", "input": {"file_path": "/project/README.md"}}',
        '\n然后搜索相关文档...\n',
        '{"type": "tool_use", "id": "toolu_002", "name": "web_search", "input": {"query": "Python project structure best practices"}}',
        '\n最后检查依赖文件...\n',
        '{"type": "tool_use", "id": "toolu_003", "name": "read_file", "input": {"file_path": "/project/requirements.txt"}}',
    ]

    print("Testing streaming detection:")
    print("=" * 50)
    
    async def run_test():
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i}: {repr(chunk)}")
            print(f"  Buffer before: {repr(detector._buffer)}")
            
            detected = detector.feed(chunk)
            print(f"  Detected: {len(detected)} tools")
            for d in detected:
                print(f"    - {d.name} (id={d.id})")
            print(f"  Buffer after: {repr(detector._buffer)}")
            print()

        print(f"Total tools in executor: {executor.tool_count}")
        
        # Now run the tools to completion
        if executor.tool_count > 0:
            print("\nRunning tools...")
            results = []
            async for update in executor.get_results():
                if update.result:
                    results.append(update.result)
                    print(f"  Result: {update.result.tool_name} - {update.result.content}")
            print(f"Got {len(results)} results")
    
    asyncio.run(run_test())

if __name__ == "__main__":
    test_streaming_detection()