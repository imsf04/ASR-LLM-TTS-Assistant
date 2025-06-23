"""
初始化数据库的脚本
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import DatabaseManager
from config import Config

def init_database():
    """初始化数据库"""
    try:
        print("正在初始化数据库...")
        
        # 创建数据库管理器
        db_manager = DatabaseManager(Config)
        
        # 检查数据库连接
        health = db_manager.health_check()
        
        if health['postgres']:
            print("✅ PostgreSQL 连接成功")
        else:
            print("❌ PostgreSQL 连接失败")
            return False
            
        if health['redis']:
            print("✅ Redis 连接成功")
        else:
            print("❌ Redis 连接失败")
            return False
        
        print("✅ 数据库初始化完成")
        return True
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
