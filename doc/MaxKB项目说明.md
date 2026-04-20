# GCode 项目说明

## 项目概述

**GCode = GCode** 是一个开源的企业级 AI 知识库问答平台，基于 RAG (Retrieval-Augmented Generation) 技术，支持工作流编排和 MCP (Model Context Protocol) 工具调用。

**版本**: 2.0.0
**前端**: Vue.js
**后端**: Python / Django
**LLM 框架**: LangChain / LangGraph
**数据库**: PostgreSQL + pgvector
**任务队列**: Celery + Redis

---

## 核心版本

| 类别 | 技术 | 版本 |
|-----|------|------|
| **后端 Python** | Python | **3.11+** |
| **前端 Node.js** | Node.js | **22.x** |
| **前端框架** | Vue.js | **3.5.13** |
| **项目版本** | GCode | **2.0.0** |

---

## 目录结构

```
D:\coding\github\MaxKB/
├── apps/                          # Django 应用主目录
├── ui/                            # Vue.js 前端源码
├── installer/                     # Docker 构建和启动脚本
├── .github/                       # GitHub 配置
├── main.py                        # 应用入口
├── pyproject.toml                 # Python 依赖配置
├── README.md                      # 英文说明文档
├── README_CN.md                   # 中文说明文档
├── LICENSE                        # GPL v3 许可证
└── USE-CASES.md                   # 使用案例
```

---

## 详细目录说明

### apps/ - Django 应用主目录

```
apps/
├── maxkb/                         # Django 项目配置
│   ├── settings/                  # Django 设置模块
│   │   ├── __init__.py            # 根据环境导入 base/web 或 base/model
│   │   ├── base/                 # 基础设置
│   │   │   ├── web.py            # Web 服务器设置
│   │   │   └── model.py          # 本地模型设置
│   │   ├── auth/                 # 认证相关设置
│   │   ├── logging.py            # 日志配置
│   │   ├── lib.py                # 库设置
│   │   └── mem.py                # 内存设置
│   ├── urls.py                   # URL 路由
│   ├── wsgi.py                   # WSGI 配置
│   ├── asgi.py                   # ASGI 配置
│   ├── conf.py                   # 配置类 (读取 YAML/环境变量)
│   └── const.py                  # 常量定义
│
├── application/                   # 应用管理模块
│   ├── api/                      # REST API 端点
│   ├── models/                   # 数据库模型
│   ├── serializers/              # DRF 序列化器
│   ├── views/                    # 视图类
│   ├── urls.py                   # URL 路由
│   ├── flow/                     # 工作流引擎
│   │   ├── step_node/            # 工作流步骤节点 (35+ 类型)
│   │   │   ├── ai_chat_step_node/    # AI 对话节点
│   │   │   ├── search_knowledge_node/ # 知识检索节点
│   │   │   ├── loop_node/             # 循环节点
│   │   │   ├── mcp_node/               # MCP 工具节点
│   │   │   └── ... (更多节点类型)
│   │   ├── workflow_manage.py
│   │   └── default_workflow*.json     # 默认工作流模板
│   └── chat_pipeline/            # 聊天处理管道
│       └── step/                 # 管道步骤
│
├── knowledge/                     # 知识库模块
│   ├── api/                      # 知识 API 端点
│   ├── models/                   # 知识库模型
│   ├── vector/                   # 向量检索实现
│   │   ├── base_vector.py       # 向量基类
│   │   ├── pg_vector.py        # PostgreSQL 向量存储
│   │   └── index/              # 向量索引
│   ├── task/                    # 后台任务
│   └── views/
│
├── chat/                         # 聊天模块
│   ├── api/
│   ├── models/
│   ├── views/
│   ├── mcp/                     # MCP 服务器实现
│   └── template/
│
├── common/                       # 公共工具模块
│   ├── utils/                   # 工具函数
│   │   ├── split_model.py      # 文本分割
│   │   ├── search.py           # 搜索工具
│   │   ├── tool_code.py        # 工具执行
│   │   └── ...
│   ├── db/                      # 数据库工具
│   ├── cache/                   # 缓存工具
│   ├── cache_data/              # 缓存数据管理
│   ├── chunk/                  # 文档分块
│   ├── config/                  # 配置管理
│   ├── constants/               # 常量定义
│   ├── encoder/                 # 文本编码
│   ├── exception/               # 异常处理
│   ├── field/                  # 字段定义
│   ├── forms/                  # 表单定义
│   ├── handle/                 # 事件处理
│   ├── job/                    # 任务调度
│   ├── lock/                   # 分布式锁
│   ├── log/                    # 日志
│   ├── middleware/             # Django 中间件
│   ├── mixins/                 # Django mixins
│   ├── result/                 # 结果处理
│   ├── auth/                   # 认证
│   └── sql/                    # SQL 工具
│
├── users/                       # 用户管理模块
├── system_manage/              # 系统管理模块
├── models_provider/             # LLM 模型提供商集成
│   ├── impl/                   # 提供商实现
│   │   ├── openai_model_provider/
│   │   ├── anthropic_model_provider/
│   │   ├── deepseek_model_provider/
│   │   ├── qwen_model_provider/
│   │   ├── local_model_provider/
│   │   ├── ollama_model_provider/
│   │   ├── xinference_model_provider/
│   │   └── ... (20+ 更多提供商)
│   ├── base_model_provider.py
│   └── tools.py
├── local_model/                 # 本地模型服务
│   ├── auth/
│   ├── base/
│   ├── lib.py
│   └── logging.py
├── tools/                       # 工具定义
│   ├── api/
│   ├── models/
│   ├── handler/
│   └── views/
├── trigger/                    # 事件触发器
├── oss/                        # 对象存储
├── folders/                    # 文件夹管理
├── ops/                        # 运维模块 (Celery)
│   └── celery/
├── locales/                    # 国际化资源
└── manage.py                   # Django 管理脚本
```

---

### ui/ - Vue.js 前端

```
ui/
├── src/                        # 前端源码
├── public/                     # 静态资源
├── env/                        # 环境配置
│   ├── .env                    # 管理后台配置
│   └── .env.chat               # 聊天 UI 配置
├── package.json                # 前端依赖
├── vite.config.ts             # Vite 配置
└── dist/                       # 构建输出
```

---

### installer/ - Docker 构建和启动

```
installer/
├── Dockerfile                  # 主应用 Dockerfile
├── Dockerfile-base             # 基础镜像 Dockerfile
├── Dockerfile-vector-model    # 向量模型 Dockerfile
├── start-all.sh               # 启动 PostgreSQL、Redis、MaxKB
├── start-maxkb.sh            # 启动 MaxKB 应用
├── start-postgres.sh         # 启动 PostgreSQL
├── start-redis.sh            # 启动 Redis
├── init.sql                   # 数据库初始化脚本
├── install_model.py           # 模型安装脚本
└── sandbox.c                  # C 沙箱用于代码执行
```

---

## 关键文件说明

| 文件路径 | 说明 |
|---------|------|
| `main.py` | 应用入口，负责 Django 初始化、数据库迁移、静态文件收集、服务启动 |
| `pyproject.toml` | Python 项目依赖配置 |
| `apps/maxkb/settings/base/web.py` | Django Web 服务器配置 |
| `apps/maxkb/settings/base/model.py` | 本地模型服务器配置 |
| `apps/maxkb/conf.py` | 配置类，读取 config.yaml 或环境变量 |
| `apps/maxkb/const.py` | 常量定义 (版本号 2.0.0) |
| `installer/Dockerfile` | 多阶段 Docker 构建 |
| `ui/package.json` | 前端依赖 (Vue 3, Element Plus, ECharts 等) |

---

## 技术栈说明

### 后端技术栈 (Python)

#### Web 框架

| 组件 | 版本 | 说明 |
|-----|------|------|
| Django | 5.2.13 | Web 框架 |
| djangorestframework | 3.17.1 | RESTful API |
| drf-spectacular | 0.28.0 | API 文档生成 |

#### LLM / AI 框架

| 组件 | 版本 | 说明 |
|-----|------|------|
| LangChain | 1.2.15 | LLM 应用框架 |
| LangChain Core | 1.2.31 | 核心组件 |
| LangGraph | 1.1.6 | 工作流编排 |
| sentence-transformers | 5.0.0 | 文本嵌入模型 |

#### 数据库

| 组件 | 版本 | 说明 |
|-----|------|------|
| psycopg | 3.2.9 | PostgreSQL 驱动 |
| django-db-connection-pool | 1.2.6 | 数据库连接池 |
| PostgreSQL | 17+ (需 pgvector) | 主数据库 |

#### 缓存 / 消息队列

| 组件 | 版本 | 说明 |
|-----|------|------|
| django-redis | 6.0.0 | Redis 缓存 |
| Celery | 5.5.3 | 异步任务队列 |
| django-celery-beat | 2.8.1 | 定时任务 |

#### 深度学习

| 组件 | 版本 | 说明 |
|-----|------|------|
| torch | 2.8.0 | PyTorch 深度学习框架 |
| numpy | 1.26.4 | 数值计算 |

#### 文档处理

| 组件 | 版本 | 说明 |
|-----|------|------|
| pypdf | 6.10.2 | PDF 处理 |
| pymupdf | 1.26.3 | PDF 处理 |
| python-docx | 1.2.0 | Word 文档 |
| openpyxl | 3.1.5 | Excel 文档 |

#### 模型提供商

| 组件 | 版本 | 说明 |
|-----|------|------|
| langchain-openai | 1.1.14 | OpenAI |
| langchain-anthropic | 1.4.0 | Anthropic (Claude) |
| langchain-deepseek | 1.0.1 | DeepSeek |
| langchain-ollama | 1.1.0 | Ollama |
| langchain-aws | 1.4.4 | AWS Bedrock |
| langchain-google-genai | 4.2.2 | Google Gemini |
| anthropic | 0.89.0 | Anthropic SDK |
| dashscope | 1.25.16 | 阿里通义 |
| xinference-client | 1.7.1.post1 | Xinference |
| cohere | 5.17.0 | Cohere |
| qianfan | 0.4.12.3 | 百度千帆 |
| zhipuai | 2.1.5.20250708 | 智谱 AI |
| volcengine-sdk | 4.0.5 | 火山引擎 |

#### 其他依赖

| 组件 | 版本 | 说明 |
|-----|------|------|
| gunicorn | 23.0.0 | WSGI 服务器 |
| python-dotenv | 1.1.1 | 环境变量 |
| beautifulsoup4 | 4.13.4 | HTML 解析 |
| jieba | 0.42.1 | 中文分词 |
| celery-once | 3.0.1 | 任务去重 |
| django-apscheduler | 0.7.0 | 定时任务 |
| django-mptt | 0.17.0 | 树形结构 |

---

### 前端技术栈 (Node.js / Vue)

#### 核心框架

| 组件 | 版本 | 说明 |
|-----|------|------|
| Vue.js | 3.5.13 | 前端框架 |
| vue-router | 4.5.0 | 路由管理 |
| pinia | 3.0.1 | 状态管理 |
| vue-i18n | 11.1.3 | 国际化 |
| TypeScript | 5.8.0 | 类型系统 |
| Vite | 6.2.4 | 构建工具 |

#### UI 组件库

| 组件 | 版本 | 说明 |
|-----|------|------|
| element-plus | 2.13.5 | UI 组件库 |
| @antv/layout | 0.3.1 | 图形布局 |

#### 工作流 / 图表

| 组件 | 版本 | 说明 |
|-----|------|------|
| @logicflow/core | 1.2.27 | 流程图引擎 |
| @logicflow/extension | 1.2.27 | 流程图扩展 |
| echarts | 5.6.0 | 图表库 |
| mermaid | 11.12.0 | 图表/流程图 |

#### 工具库

| 组件 | 版本 | 说明 |
|-----|------|------|
| axios | 1.8.4 | HTTP 客户端 |
| vue-clipboard3 | 2.0.0 | 剪贴板 |
| screenfull | 6.0.2 | 全屏 |
| nprogress | 0.2.0 | 进度条 |
| marked | 12.0.2 | Markdown 解析 |
| highlight.js | 11.11.1 | 代码高亮 |
| katex | 0.16.10 | 数学公式 |

#### 开发工具

| 组件 | 版本 | 说明 |
|-----|------|------|
| @vitejs/plugin-vue | 5.2.3 | Vite Vue 插件 |
| @vitejs/plugin-vue-jsx | 4.1.2 | Vue JSX 支持 |
| vite-plugin-vue-devtools | 7.7.2 | Vue 开发工具 |
| vue-tsc | 2.2.8 | TypeScript 检查 |
| eslint | 9.22.0 | 代码检查 |
| prettier | 3.5.3 | 代码格式化 |
| sass | 1.86.3 | CSS 预处理器 |

---

## 部署技术栈

### Docker 相关

| 组件 | 说明 |
|-----|------|
| PostgreSQL 17+ | 需启用 pgvector 扩展 |
| Redis 7+ | 缓存和消息队列 |
| 1Panel MaxKB | 官方 Docker 镜像 |

### 生产环境推荐配置

| 组件 | 最低配置 | 推荐配置 |
|-----|---------|---------|
| CPU | 2 核 | 4 核+ |
| 内存 | 4 GB | 8 GB+ |
| 磁盘 | 50 GB | 100 GB+ |
| PostgreSQL | 2 GB 内存 | 4 GB+ 内存 |

---

## 技术架构图

```
┌─────────────────────────────────────────────────────────┐
│                      前端 (Vue.js)                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │ Admin UI │  │ Chat UI │  │ 图表组件 │  │工作流编辑│  │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  │
│       │            │            │            │         │
│       └────────────┴────────────┴────────────┘         │
│                         │ HTTP/API                       │
└─────────────────────────┼───────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────┐
│                   后端 (Django)                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │ 应用管理 │  │ 知识库   │  │ 聊天    │  │ 工具库  │  │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  │
│       │            │            │            │         │
│       └────────────┴────────────┴────────────┘         │
│                         │                               │
│              ┌──────────┴──────────┐                    │
│              │    LangChain/LangGraph │                  │
│              │    (LLM 编排框架)     │                    │
│              └──────────┬──────────┘                    │
└─────────────────────────┼───────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────┐
│                    数据存储层                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │PostgreSQL│  │  Redis   │  │ 文件存储 │  │ 向量存储 │  │
│  │+pgvector │  │ (缓存/队列)│  │  (OSS)  │  │(pgvector)│  │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────┐
│                    LLM 模型层                           │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │ OpenAI  │  │Claude   │  │DeepSeek │  │ 本地模型 │  │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 版本对应关系

```
GCode 2.0.0
├── Python 3.11+
├── Django 5.2.13
├── Vue 3.5.13
├── Vite 6.2.4
├── TypeScript 5.8.0
├── LangChain 1.2.15
├── LangGraph 1.1.6
├── torch 2.8.0
├── sentence-transformers 5.0.0
└── Element Plus 2.13.5
```
