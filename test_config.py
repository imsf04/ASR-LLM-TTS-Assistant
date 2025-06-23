#!/usr/bin/env python3
"""
测试配置读取
"""
import os
from dotenv import load_dotenv
from config import Config

# 加载环境变量
load_dotenv()

print("=== 测试配置读取 ===")
print(f"环境变量 DASHSCOPE_API_KEY: {os.getenv('DASHSCOPE_API_KEY')}")

# 创建配置实例
config = Config()
print(f"配置实例 DASHSCOPE_API_KEY: {config.DASHSCOPE_API_KEY}")
print(f"配置实例 LLM_MODEL: {config.LLM_MODEL}")
print(f"配置实例 HOST: {config.HOST}")
print(f"配置实例 PORT: {config.PORT}")

# 验证配置
try:
    config.validate_config()
    print("✓ 配置验证通过")
except Exception as e:
    print(f"✗ 配置验证失败: {e}")
