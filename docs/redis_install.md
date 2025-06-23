# Redis 安装指南

## 下载和安装
1. 访问: https://github.com/tporadowski/redis/releases
2. 下载最新版本的 Redis-x64-xxx.msi
3. 或者直接下载: https://github.com/tporadowski/redis/releases/download/v5.0.14.1/Redis-x64-5.0.14.1.msi

## 安装配置
运行 .msi 安装程序：

### 安装选项：
- [x] Add the Redis installation folder to the PATH environment variable
- [x] Run the Redis server as a Service
- 端口: 6379 (默认)
- 最大内存: 使用默认设置

### 服务配置：
- Redis会自动作为Windows服务安装
- 服务名: Redis
- 启动类型: 自动

## 验证安装
1. 打开命令提示符
2. 运行以下命令测试连接：

```cmd
redis-cli ping
```

如果返回 "PONG"，说明Redis安装成功。

## 服务管理
### 启动Redis服务：
```cmd
net start Redis
```

### 停止Redis服务：
```cmd
net stop Redis
```

### 重启Redis服务：
```cmd
net stop Redis && net start Redis
```

## 配置文件
Redis配置文件位置: C:\Program Files\Redis\redis.windows-service.conf
默认配置即可满足开发需求。
