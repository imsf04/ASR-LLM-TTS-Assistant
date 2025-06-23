# PostgreSQL 安装指南

## 下载和安装
1. 访问: https://www.postgresql.org/download/windows/
2. 点击 "Download the installer"
3. 选择最新版本（推荐 PostgreSQL 15.x）
4. 下载 Windows x86-64 版本

## 安装配置
运行安装程序时，请按以下配置：

### 安装组件选择：
- [x] PostgreSQL Server
- [x] pgAdmin 4 (管理工具)
- [x] Stack Builder (可选)
- [x] Command Line Tools

### 数据目录：
- 使用默认路径即可

### 超级用户密码：
- 设置为: postgres123
- **重要**: 记住这个密码，必须与.env文件中的POSTGRES_PASSWORD一致

### 端口配置：
- 使用默认端口: 5432

### 区域设置：
- 选择 "Default locale"

## 安装后配置
1. 安装完成后，PostgreSQL服务会自动启动
2. 创建项目数据库：

### 方法一：使用pgAdmin4 (图形界面)
1. 启动 pgAdmin 4
2. 连接到 PostgreSQL 服务器
3. 右键点击 "Databases"
4. 选择 "Create" -> "Database..."
5. 数据库名称: asr_llm_tts
6. 点击 "Save"

### 方法二：使用命令行
1. 打开命令提示符 (以管理员身份运行)
2. 执行以下命令：

```cmd
cd "C:\Program Files\PostgreSQL\15\bin"
createdb -U postgres asr_llm_tts
```

## 验证安装
在命令行中运行：
```cmd
psql -U postgres -h localhost -p 5432 -d asr_llm_tts
```
如果能连接成功，说明安装配置正确。
