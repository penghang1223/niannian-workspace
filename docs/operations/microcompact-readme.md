# Microcompact Context Compactor

Implementation of Claude Code's microcompact context compression mechanism for optimizing prompt cache usage and reducing token consumption.

## Overview

The microcompact algorithm implements lightweight context compression with 4 stages:

1. **Time-based clearing**: When gap since last assistant message > threshold, clear old tool results
2. **Duplicate detection**: Merge messages with same role and similar content  
3. **Tool result grouping**: Combine consecutive tool result messages
4. **Long text compression**: Truncate large tool results while preserving head/tail

## Features

- **Fast**: Lightweight algorithm runs in milliseconds
- **Configurable**: Adjustable thresholds and tool types
- **Token-aware**: Estimates token usage during compression
- **Claude Code compatible**: Follows the same principles as Claude Code's implementation
- **Multiple interfaces**: Python API, CLI, and file-based operations

## Architecture

```
┌──────────────────────────────────────────────┐
│              microcompactMessages             │
│  ┌────────────────────────────────────────┐  │
│  │  1. Time-based MC (timeBasedMC)        │  │
│  │     gap > 60min → clear old results    │  │
│  ├────────────────────────────────────────┤  │
│  │  2. Duplicate Detection                │  │
│  │     same role + similar content → merge│  │
│  ├────────────────────────────────────────┤  │
│  │  3. Tool Result Grouping               │  │
│  │     consecutive tool_results → merge   │  │
│  ├────────────────────────────────────────┤  │
│  │  4. Long Text Compression              │  │
│  │     truncate + keep head/tail          │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

## Installation

No installation required - pure Python script in `scripts/context_compactor.py`

## Usage

### 1. Python API

```python
from scripts.context_compactor import microcompact

messages = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}, 
    {"role": "user", "content": "Hello"}  # Will be merged
]

compacted, stats = microcompact(messages)
print(stats.summary())
```

### 2. Custom Configuration

```python
from scripts.context_compactor import MicrocompactConfig, ContextCompactor

config = MicrocompactConfig(
    similarity_threshold=0.80,           # 80% similarity = duplicate
    max_tool_result_tokens=2000,         # Compress results > 2000 tokens
    gap_threshold_minutes=30.0,          # Time-based clearing after 30 min
)

compactor = ContextCompactor(config)
compacted = compactor.compact_json(messages)
```

### 3. Command Line Interface

```bash
# Compact from stdin
cat messages.json | python scripts/context_compactor.py

# Compact a file
python scripts/context_compactor.py input.json -o output.json

# With custom config
python scripts/context_compactor.py input.json --config scripts/context_compact_config.json

# Dry run (show stats only)
python scripts/context_compactor.py input.json --dry-run
```

### 4. File Operations

```python
from scripts.context_compactor import microcompact_from_file

# Process file directly
stats = microcompact_from_file(
    input_path="messages.json",
    output_path="compacted.json", 
    config_path="scripts/context_compact_config.json"
)
print(stats.summary())
```

## Configuration Options

The config file `scripts/context_compact_config.json` contains:

- `similarity_threshold`: Content similarity ratio to consider duplicates (0-1)
- `max_tool_result_tokens`: Max tokens before compressing tool results
- `tool_result_head_tokens`: Tokens to keep from head of compressed results
- `tool_result_tail_tokens`: Tokens to keep from tail of compressed results
- `time_based_enabled`: Whether to enable time-based clearing
- `gap_threshold_minutes`: Minutes of inactivity to trigger clearing
- `keep_recent_tool_results`: How many recent results to preserve
- `compactable_tools`: List of tool names whose results can be cleared
- `max_input_tokens`: Threshold that triggers compaction
- `target_input_tokens`: Target after compaction

## Integration Example

```python
class AgentContext:
    def __init__(self):
        self.messages = []
        self.compactor = ContextCompactor()

    def check_and_compact(self, token_threshold=10000):
        compacted, stats = microcompact(self.messages)
        if stats.tokens_before >= token_threshold:
            self.messages = compacted
            return True
        return False
```

## Claude Code Compatibility

This implementation mirrors Claude Code's microcompact behavior:
- Same 4-stage pipeline
- Similar configuration options
- Compatible data structures
- Time-based clearing when cache expires
- Tool result compression for common tools

## Performance

- Fast execution (typically <100ms for 100-message conversations)
- Significant token savings (20-80% reduction for large conversations)
- Maintains semantic integrity of conversation
- Preserves important context while removing redundancy