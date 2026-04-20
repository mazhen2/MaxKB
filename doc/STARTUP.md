# GCode 启动手册

## 快速启动

### Docker 部署 (推荐用于生产环境)

```bash
docker run -d --name=maxkb --restart=always -p 8080:8080 \
  -v ~/.maxkb:/opt/maxkb \
  1panel/maxkb
```

访问地址: `http://your_server_ip:8080`
- 默认用户名: `admin`
- 默认密码: `MaxKB@123..`

---

## 环境要求

### 运行时依赖

| 组件 | 版本要求 | 说明 |
|-----|---------|------|
| Python | 3.11+ | 后端运行环境 |
| PostgreSQL | 17+ | 主数据库 (需启用 pgvector 扩展) |
| Redis | 6+ | 缓存和消息队列 |
| Node.js | 24+ | 前端构建 |

### 使用 Docker 安装

```bash
# 克隆项目
git clone https://github.com/1Panel-dev/MaxKB.git
cd MaxKB

# 进入安装目录
cd installer

# 启动所有服务 (PostgreSQL + Redis + MaxKB)
chmod +x start-all.sh
./start-all.sh
```

---

## 开发环境配置

### 1. 后端配置

#### 方式一: 使用 config.yaml 配置文件

在项目根目录创建 `config.yaml`:

```yaml
db:
  name: maxkb
  host: 127.0.0.1
  port: 5432
  user: postgres
  password: your_password

redis:
  host: 127.0.0.1
  port: 6379
  password: your_redis_password

app:
  host: 0.0.0.0
  port: 8080
  secret_key: your-secret-key

embedding:
  model_path: /opt/maxkb/model/embedding
```

#### 方式二: 使用环境变量

```bash
# 数据库配置
export MAXKB_DB_NAME=maxkb
export MAXKB_DB_HOST=127.0.0.1
export MAXKB_DB_PORT=5432
export MAXKB_DB_USER=postgres
export MAXKB_DB_PASSWORD=your_password

# Redis 配置
export MAXKB_REDIS_HOST=127.0.0.1
export MAXKB_REDIS_PORT=6379
export MAXKB_REDIS_PASSWORD=your_redis_password

# 应用配置
export MAXKB_APP_PORT=8080
export MAXKB_SECRET_KEY=your-secret-key

# 本地模型配置
export MAXKB_LOCAL_MODEL_HOST=127.0.0.1
export MAXKB_LOCAL_MODEL_PORT=11636
export MAXKB_EMBEDDING_MODEL_PATH=/opt/maxkb/model/embedding

# 配置类型
export MAXKB_CONFIG_TYPE=ENV
```

### 2. 数据库初始化

#### PostgreSQL 配置

```bash
# 登录 PostgreSQL
psql -U postgres

# 创建数据库
CREATE DATABASE maxkb;

# 启用 pgvector 扩展
\c maxkb
CREATE EXTENSION IF NOT EXISTS vector;

# 创建用户并授权
CREATE USER maxkb_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE maxkb TO maxkb_user;
GRANT ALL ON SCHEMA public TO maxkb_user;
```

### 3. Python 依赖安装

```bash
# 使用 uv 安装 (推荐)
cd D:\coding\github\MaxKB
uv sync

# 或使用 pip
pip install -e .
```

### 4. 数据库迁移

```bash
cd apps

# 运行数据库迁移
python manage.py migrate

# 或者使用 main.py
cd D:\coding\github\MaxKB
python main.py upgrade_db
```

### 5. 静态文件收集

```bash
python main.py collect_static
```

---

## 启动应用

### 本地开发环境启动 (推荐方式 - 三终端)

需要同时启动 3 个服务，建议在 3 个独立终端中运行：

#### 终端 1: 启动 Django Web 服务器

```bash
cd D:\coding\github\MaxKB\apps
python manage.py runserver 0.0.0.0:8080
```

访问地址：`http://127.0.0.1:8080`

#### 终端 2: 启动 Celery Worker (处理异步任务)

```bash
cd D:\coding\github\MaxKB
python main.py dev celery
```

#### 终端 3: 启动前端开发服务器

```bash
cd D:\coding\github\MaxKB\ui
npm install  # 首次需要安装依赖
npm run dev
```

前端访问地址：`http://localhost:3000`

---

### 使用 main.py 启动 (生产/一键启动)

```bash
cd D:\coding\github\MaxKB

# 启动所有服务 (Web + Celery Worker) 后台运行
python main.py start all -d

# 启动 Web 服务
python main.py start web

# 启动指定数量的 Celery Worker (例如 4 个)
python main.py start all --worker 4
```

---

### 故障排查

#### Celery Worker 无法启动

如果出现 `Module 'maxkb' has no attribute 'celery'` 错误：

```bash
# 正确的启动方式
cd D:\coding\github\MaxKB
python main.py dev celery

# 或使用 Django 管理命令
cd D:\coding\github\MaxKB\apps
python manage.py celery celery
```

#### Redis 连接错误

如果出现 `AUTH <password> called without any password` 错误：

1. 检查 `.env` 文件中的 Redis 配置：
```bash
export MAXKB_REDIS_PASSWORD=
```

2. 确保 Redis 服务正在运行：
```bash
redis-cli ping
# 应返回 PONG
```

#### 前端代理错误 (ECONNREFUSED)

确保 Django Web 服务器正在运行（终端 1），并且监听正确的端口：
```bash
# 应该看到
Starting development server at http://127.0.0.1:8080/
```

---

## 前端开发

### 安装依赖

```bash
cd D:\coding\github\MaxKB\ui
npm install
```

### 启动开发服务器

**前提条件：** 确保后端 Web 服务已启动（见上面的终端 1）

```bash
cd D:\coding\github\MaxKB\ui

# 管理后台 (默认端口 3000)
npm run dev

# 聊天 UI (如果需要)
npm run chat
```

前端访问地址：`http://localhost:3000`

### 构建生产版本

```bash
cd D:\coding\github\MaxKB\ui

# 构建前端
npm run build

# 构建 chat UI
npm run build:chat
```

构建完成后，运行以下命令收集静态文件到 Django：
```bash
cd D:\coding\github\MaxKB
python main.py collect_static
```

---

## Docker Compose 部署

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg17
    environment:
      POSTGRES_DB: maxkb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    command: redis-server --requirepass your_redis_password
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "your_redis_password", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  maxkb:
    image: 1panel/maxkb
    environment:
      MAXKB_DB_HOST: postgres
      MAXKB_DB_PORT: 5432
      MAXKB_DB_NAME: maxkb
      MAXKB_DB_USER: postgres
      MAXKB_DB_PASSWORD: your_password
      MAXKB_REDIS_HOST: redis
      MAXKB_REDIS_PORT: 6379
      MAXKB_REDIS_PASSWORD: your_redis_password
    ports:
      - "8080:8080"
    volumes:
      - maxkb_data:/opt/maxkb
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

volumes:
  postgres_data:
  redis_data:
  maxkb_data:
```

启动:
```bash
docker-compose up -d
```

---

## 验证安装

1. 访问 `http://localhost:8080`
2. 使用默认账号登录:
   - 用户名: `admin`
   - 密码: `MaxKB@123..`

---

## 常见问题

### 1. 数据库连接失败

确保 PostgreSQL 已启动且 pgvector 扩展已启用:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

**Windows 上检查 PostgreSQL 状态：**
```bash
# 查看服务
Get-Service | findstr postgres

# 或在任务管理器中查看 PostgreSQL 进程
```

### 2. Redis 连接错误 (AUTH <password> called without any password)

**问题：** `.env` 中有 Redis 密码，但本地 Redis 没有配置密码

**解决方案：**

清空 `.env` 中的 Redis 密码：
```bash
# .env
export MAXKB_REDIS_PASSWORD=
```

或配置 Redis 使用密码：
```bash
redis-cli
> CONFIG SET requirepass "your_password"
> CONFIG REWRITE
```

### 3. Celery Worker 无法连接 Redis

检查 Redis 是否运行：
```bash
redis-cli ping
# 应返回 PONG
```

如果有密码，测试连接：
```bash
redis-cli -a your_password ping
```

### 4. Celery Worker 启动失败 (Module 'maxkb' has no attribute 'celery')

**正确的启动方式：**
```bash
cd D:\coding\github\MaxKB
python main.py dev celery

# 不要使用
# celery -A maxkb worker -l INFO  (这会失败)
```

### 5. Celery Worker 显示 FileNotFoundError (worker_heartbeat)

这是 Windows 兼容性问题。应该已在 `apps/ops/celery/heartbeat.py` 中修复。

如果仍有问题：
```bash
# 确保 Windows 兼容性补丁已加载
# main.py 应该包含：from common.utils.windows_compat import *
```

### 6. 前端代理错误 (ECONNREFUSED 127.0.0.1:8080)

**问题：** 前端无法连接后端 API

**解决方案：**
1. 确保 Django Web 服务器正在运行
2. 检查 Django 监听的端口是否正确 (应该是 8080)
3. 查看前端 Vite 代理配置指向正确的后端地址

```bash
# 检查后端是否运行
curl http://127.0.0.1:8080/admin/api/profile
```

### 7. 前端静态资源 404

运行静态文件收集:
```bash
cd D:\coding\github\MaxKB
python main.py collect_static
```

### 8. 嵌入模型加载失败

确保 `embedding_model_path` 配置正确，或使用默认模型:
```bash
# Windows 模型默认路径
# 检查路径是否存在
dir C:\opt\maxkb\model\embedding

# 或使用相对路径
ls /opt/maxkb/model/embedding
```

### 9. 端口被占用

**修改 Django 端口：**
```bash
python manage.py runserver 0.0.0.0:8081
```

**修改前端 Vite 端口：**
编辑 `ui/vite.config.js`：
```javascript
server: {
  port: 3001,  // 改成其他端口
  proxy: {
    '/admin/api/': {
      target: 'http://127.0.0.1:8080',
    }
  }
}
```

### 10. Windows 下无法识别 Unix 路径

本项目已在 `common/utils/windows_compat.py` 中添加 Windows 兼容性补丁。

如果遇到 `No such file or directory: /opt/...` 错误，检查：
1. `main.py` 是否导入了 `windows_compat`
2. 使用的是 Windows 标准路径还是 Unix 路径

---

## 环境变量完整列表

| 变量名 | 默认值 | 说明 |
|-------|-------|------|
| `MAXKB_CONFIG_TYPE` | `FILE` | 配置来源: FILE 或 ENV |
| `MAXKB_DB_NAME` | `maxkb` | 数据库名称 |
| `MAXKB_DB_HOST` | `127.0.0.1` | 数据库主机 |
| `MAXKB_DB_PORT` | `5432` | 数据库端口 |
| `MAXKB_DB_USER` | `postgres` | 数据库用户名 |
| `MAXKB_DB_PASSWORD` | - | 数据库密码 |
| `MAXKB_REDIS_HOST` | `127.0.0.1` | Redis 主机 |
| `MAXKB_REDIS_PORT` | `6379` | Redis 端口 |
| `MAXKB_REDIS_PASSWORD` | - | Redis 密码 |
| `MAXKB_APP_HOST` | `0.0.0.0` | 应用监听地址 |
| `MAXKB_APP_PORT` | `8080` | 应用监听端口 |
| `MAXKB_SECRET_KEY` | - | Django Secret Key |
| `MAXKB_DEBUG` | `false` | 调试模式 |
| `MAXKB_LOCAL_MODEL_HOST` | `127.0.0.1` | 本地模型主机 |
| `MAXKB_LOCAL_MODEL_PORT` | `11636` | 本地模型端口 |
| `MAXKB_EMBEDDING_MODEL_PATH` | `/opt/maxkb-app/model/embedding` | 嵌入模型路径 |

---

## 停止服务

```bash
# Docker 部署
docker-compose down

# 开发环境
# 停止 Django 服务器和 Celery Worker 进程
pkill -f "manage.py runserver"
pkill -f "celery worker"
```
