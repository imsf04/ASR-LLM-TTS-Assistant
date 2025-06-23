"""
最简单的测试版本，用于诊断连接问题
"""

import os
from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-key'
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return "<h1>Flask-SocketIO 测试成功!</h1><p>如果您看到这个页面，说明服务器正在正常运行。</p>"

@app.route('/test')
def test():
    return "测试页面工作正常"

if __name__ == '__main__':
    print("=" * 60)
    print("启动最简单的测试服务器...")
    print("请在浏览器中访问:")
    print("  http://127.0.0.1:8080")
    print("  http://127.0.0.1:8080/test")
    print("=" * 60)
    
    # 使用8080端口避免与其他服务冲突
    socketio.run(app, 
        host='127.0.0.1', 
        port=8080, 
        debug=False
    )
