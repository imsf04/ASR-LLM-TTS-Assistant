# 数据库安装指导

## 当前状态
✅ **Python环境**: 已配置完成
✅ **核心依赖**: psycopg2-binary, redis, SQLAlchemy 已安装
✅ **简化版应用**: 正在运行 http://127.0.0.1:5000

## 选项1：快速测试（推荐）
使用当前运行的简化版本 `app_simple.py`：
- 支持ASR语音识别
- 支持LLM对话（Qwen-Plus）
- 支持TTS语音合成（CosyVoice v2）
- **无需数据库**，可立即测试AI功能

在浏览器访问：http://127.0.0.1:5000

## 选项2：完整功能（需要安装数据库）

### PostgreSQL 安装
1. **下载安装包**
   - 访问：https://www.postgresql.org/download/windows/
   - 下载 PostgreSQL 15.x Windows x86-64

2. **安装配置**
   - 运行安装程序
   - 组件选择：PostgreSQL Server + pgAdmin 4 + Command Line Tools
   - 设置超级用户密码：`postgres123`
   - 端口：5432（默认）

3. **创建数据库**
   ```sql
   -- 方法1：使用pgAdmin 4图形界面
   -- 连接到PostgreSQL → 右键Databases → Create → Database
   -- 数据库名：asr_llm_tts
   
   -- 方法2：命令行
   cd "C:\Program Files\PostgreSQL\15\bin"
   createdb -U postgres asr_llm_tts
   ```

### Redis 安装
1. **下载安装包**
   - 访问：https://github.com/tporadowski/redis/releases
   - 下载 Redis-x64-xxx.msi

2. **安装配置**
   - 运行 .msi 安装程序
   - ✅ Add Redis to PATH
   - ✅ Run as Windows Service
   - 端口：6379（默认）

3. **验证安装**
   ```cmd
   redis-cli ping
   # 应该返回 PONG
   ```

### 启动完整版应用
安装完数据库后：
```cmd
# 停止简化版（如果在运行）
# Ctrl+C

# 初始化数据库
python scripts/init_db.py

# 启动完整版
python app.py
```

## 功能对比

| 功能         | 简化版 (app_simple.py) | 完整版 (app.py) |
| ------------ | ---------------------- | --------------- |
| ASR语音识别  | ✅                      | ✅               |
| LLM对话      | ✅                      | ✅               |
| TTS语音合成  | ✅                      | ✅               |
| 文件上传     | ❌                      | ✅               |
| 知识库RAG    | ❌                      | ✅               |
| 用户会话管理 | ❌                      | ✅               |
| 缓存功能     | ❌                      | ✅               |
| 数据持久化   | ❌                      | ✅               |

## 推荐流程
1. 🚀 **先测试简化版**：确认AI功能正常（当前已运行）
2. 📚 **体验核心功能**：语音识别、对话、语音合成
3. 💾 **按需安装数据库**：如需完整功能再安装
4. 🔧 **切换到完整版**：获得所有高级功能

## 故障排除
- **简化版无法启动**：检查DashScope API密钥
- **数据库连接失败**：确认服务状态和密码
- **端口占用**：修改.env中的PORT配置

## 联系支持
如遇问题，请提供：
- 错误信息截图
- 当前使用的版本（简化版/完整版）
- 操作系统版本
