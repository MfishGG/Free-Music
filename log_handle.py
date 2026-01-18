#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author: unknown
@Date: 2026-01-18
@File: log_handle.py
"""

import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name='app_logger', log_file='app.log', level=logging.INFO, max_bytes=1*1024*1024, backup_count=5):
    """
    设置日志记录器
    
    Args:
        name: logger名称
        log_file: 日志文件路径
        level: 日志级别
        max_bytes: 单个日志文件最大大小（字节）
        backup_count: 保留的备份文件数量
    
    Returns:
        logging.Logger: 配置好的logger对象
    """
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 创建formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    # 创建RotatingFileHandler，当日志文件达到max_bytes时轮转
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=max_bytes, 
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # 创建console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # 添加handlers到logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 创建应用主logger
app_logger = setup_logger('free_music_app', 'free_music.log')
