#!/usr/bin/env python3
"""
诊断脚本 - 检查应用启动问题
"""
import sys
import os
import traceback

print("=== 诊断开始 ===")

try:
    print("1. 导入基础模块...")
    from flask import Flask
    from flask_socketio import SocketIO
    print("✓ Flask和SocketIO导入成功")
    
    print("2. 导入配置...")
    from config import Config
    config = Config()
    print(f"✓ 配置加载成功，HOST: {config.HOST}, PORT: {config.PORT}")
    
    print("3. 测试基础应用...")
    app = Flask(__name__)
    
    @app.route('/test')
    def test():
        return {'status': 'ok'}
    
    print("4. 测试SocketIO...")
    socketio = SocketIO(app, async_mode='threading')
    print("✓ SocketIO初始化成功")
    
    print("5. 测试导入自定义模块...")
    from utils.logger import setup_logger
    logger = setup_logger('test', 'INFO')
    print("✓ Logger导入成功")
    
    print("6. 启动测试服务器...")
    app.run(host='127.0.0.1', port=5001, debug=False)
    
except Exception as e:
    print(f"✗ 错误: {e}")
    print("详细错误信息:")
    traceback.print_exc()
