"""
Production-grade logging setup for all scripts.
Usage: from log_setup import get_logger; log = get_logger(__name__)
"""

import logging
import logging.handlers
import sys
import json
import functools
from datetime import datetime
from pathlib import Path


# ANSI color codes for terminal output
COLORS = {
    'DEBUG': '\033[36m',     # Cyan
    'INFO': '\033[32m',      # Green
    'WARNING': '\033[33m',   # Yellow
    'ERROR': '\033[31m',     # Red
    'CRITICAL': '\033[41m',  # Red background
    'RESET': '\033[0m',
}


class ColoredFormatter(logging.Formatter):
    """彩色终端输出格式器"""
    
    def format(self, record):
        color = COLORS.get(record.levelname, COLORS['RESET'])
        reset = COLORS['RESET']
        
        # 彩色时间 + 级别 + 消息
        time_str = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        prefix = f"{color}[{record.levelname[0]}]{reset}"
        
        return f"{time_str} {prefix} {record.getMessage()}"


class JSONFormatter(logging.Formatter):
    """JSON 格式输出（便于日志聚合）"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'line': record.lineno,
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def get_logger(
    name: str = None,
    level: int = logging.DEBUG,
    log_file: str = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    获取配置好的 logger
    
    Args:
        name: logger 名称，默认使用调用模块名
        level: 日志级别
        log_file: 日志文件路径（可选）
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的备份文件数
    
    Returns:
        配置好的 logger
    
    Example:
        from log_setup import get_logger
        log = get_logger(__name__)
        log.info("Server started")
        log.error("Connection failed", exc_info=True)
    """
    logger = logging.getLogger(name or __name__)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # 终端输出（彩色）
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)
    
    # 文件输出（JSON 格式 + 轮转）
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8',
        )
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    
    return logger


def log_calls(logger=None, level=logging.DEBUG):
    """
    装饰器：自动记录函数调用和返回
    
    Example:
        @log_calls()
        def fetch_data(url):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or logging.getLogger(func.__module__)
            _logger.log(level, f"→ {func.__name__}()")
            
            try:
                result = func(*args, **kwargs)
                _logger.log(level, f"← {func.__name__}() done")
                return result
            except Exception as e:
                _logger.error(f"✗ {func.__name__}() failed: {e}", exc_info=True)
                raise
        
        return wrapper
    return decorator


# Quick test
if __name__ == "__main__":
    log = get_logger("test", log_file="/tmp/test.log")
    
    log.debug("Debug message")
    log.info("Info message")
    log.warning("Warning message")
    log.error("Error message")
    
    try:
        1 / 0
    except:
        log.error("Division failed", exc_info=True)
    
    print("\n✅ log_setup.py works! Check /tmp/test.log for JSON output")
