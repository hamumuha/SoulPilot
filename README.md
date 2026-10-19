# SoulPilot · 心灵领航员

> 🐾 Your AI companion that not only chats, but acts. —— 不止会聊，更能行动的网页 AI 伴侣。

**原名 hamu-pet** · 纯网页版 SoulPilot · 心灵领航员 · 后端 v3.0.0 / 前端 v4.0.0

这是一个**纯网页的 AI 宠物项目**，以「**心灵之旅**」为主页面：用户登录后即进入心灵之旅，在其中记录心情、生成心灵车票；可拖拽、可穿透交互的透明宠物浮层提供快捷入口，对话历史与设置分别在独立页面中管理。项目集三种核心能力于一身——

1. **陪伴**：心灵之旅页面内置的透明、可拖拽、可穿透交互的宠物浮层。
2. **行动**：宠物作为 **AI Agent** 自主调用工具（MCP + Function Calling）完成多模型智能对话。
3. **共情**：心灵之旅本身的情绪领航能力，用户记录当前心情后，宠物会以专业心理咨询视角进行结构化情绪分析，生成可收藏的「**心灵车票**」，并自动把这次心情对话沉淀进宠物的聊天记忆——宠物因此能基于「刚刚记下的心情」与用户展开更深入、更有温度的对话，让陪伴从一次问答走向长期情绪档案。

三种能力共享同一套后端、同一套对话表，同属于这一个项目。无需安装桌面客户端，打开浏览器即可使用。

---

## 目录

- [技术栈](#技术栈)
- [核心架构](#核心架构)
- [功能特性](#功能特性)
- [情绪领航工作流](#情绪领航工作流)
- [支持的 AI 提供商](#支持的-ai-提供商)
- [快速启动](#快速启动)
- [环境变量](#环境变量)
- [项目结构](#项目结构)
- [数据库设计](#数据库设计)
- [API 接口](#api-接口)
- [前端架构](#前端架构)
- [关键实现细节](#关键实现细节)
- [生产构建](#生产构建)
- [许可证](#许可证)

---

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端框架 | Vue 3 + Composition API | ^3.5.13 |
| 构建工具 | Vite | ^6.0.5 |
| 语言 | TypeScript | ~5.6.2 |
| UI 库 | Element Plus + @element-plus/icons-vue | ^2.9.1 |
| 状态管理 | Pinia + pinia-plugin-persistedstate | ^2.3.0 |
| HTTP 客户端 | axios（常规）+ Fetch（SSE 流式） | ^1.7.9 |
| 路由 | vue-router | ^4.5.0 |
| 后端框架 | Python FastAPI（异步） | 0.115.6 |
| ASGI 服务器 | uvicorn[standard] | 0.34.0 |
| ORM | SQLAlchemy | 2.0.36 |
| MySQL 驱动 | PyMySQL + cryptography | 1.1.1 / 44.0.0 |
| HTTP 客户端（后端） | httpx（异步流式） | 0.28.1 |
| 数据校验 | Pydantic + pydantic-settings | 2.10.3 / 2.7.0 |
| 配置管理 | python-dotenv | 1.0.1 |
| 数据库 | MySQL（utf8mb4） | — |
| AI 协议 | OpenAI / Gemini / Claude 三大协议统一适配 | — |
| Agent 协议 | MCP stdio（JSON-RPC 2.0，protocolVersion 2024-11-05） | — |

---

## 核心架构

项目采用「心灵之旅、独立对话/设置页面、悬浮宠物入口 + 一套后端」的一体化架构。心灵之旅是登录后的主页面；`/chat/:conversationId?` 提供新建对话、历史查询、删除和继续交流，`/settings` 提供独立设置页面。对话、情绪分析和 MCP 工具共用同一份用户与对话历史。

```
┌─────────────────────────────────────────────────────────┐
│                    浏览器（前端 5173）                      │
│                                                         │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  SoulJourneyView 心灵之旅主页面（登录后进入）         │ │
│  │  情绪选择 / 心情输入 / 车票生成 / 车票历史 / 新手引导  │ │
│  │                                                     │ │
│  │     ┌────────────────────────────────────────┐      │ │
│  │     │  Pet Overlay（宠物浮层，内置在主页面之上）│      │ │
│  │     │  ┌────────┐ ┌──────────┐ ┌────────┐   │      │ │
│  │     │  │PetWindow│ │ChatPanel │ │TrayMenu│   │      │ │
│  │     │  │(宠物浮层)│ │(AI对话)  │ │(托盘)  │   │      │ │
│  │     │  └────────┘ └──────────┘ └────────┘   │      │ │
│  │     │  ┌──────────────────────────────────┐    │      │ │
│  │     │  │ SettingsPanel (设置/ API/MCP/主题)│    │      │ │
│  │     │  └──────────────────────────────────┘    │      │ │
│  │     └────────────────────────────────────────┘      │ │
│  └─────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────┘
                             │ Vite 代理 /api → 127.0.0.1:8000
┌────────────────────────────▼────────────────────────────┐
│              FastAPI 后端（8000）单一服务                  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐     │
│  │  api/v1 路由层（同一套接口承载全部能力）            │     │
│  │  user · setting · chat · agent · template      │     │
│  │  conversation · mcp                              │     │
│  └───────────────┬─────────────────────────────────┘     │
│                  │                                       │
│  ┌───────────────▼──────────────┐  ┌──────────────────┐  │
│  │  services 服务层               │  │  core/security   │  │
│  │  ai_service  (多模型+视觉+SSE)  │  │  PBKDF2+Token会话 │  │
│  │  mcp_service (MCP stdio客户端)  │  └──────────────────┘  │
│  │  soul_service(情绪分析+兜底)    │  ┌──────────────────┐  │
│  │  setting_service              │  │  models (ORM/Schema)│ │
│  └───────────────┬──────────────┘  └──────────────────┘  │
│                  │                                       │
│           ┌──────▼──────┐                        ┌──────────────┐
│           │  MySQL      │      MCP 子进程          │ 外部 AI API   │
│           │  (AIChat库)  │     (npx/uvx/...)       │ (11家提供商)   │
│           └─────────────┘                        └──────────────┘
└─────────────────────────────────────────────────────────┘
```

**设计要点**：

- **心灵之旅为主、宠物为快捷入口**：心灵之旅是登录后的主页面；PetWindow / TrayMenu 浮在页面上提供快捷入口，对话和设置分别使用独立路由页面，且共享同一份登录态与对话上下文。
- **共享对话表**：聊天与情绪分析写入同一套 `conversations` / `messages` 表；情绪分析结果自动写入当前用户的活跃对话，宠物聊天面板启动时即加载该对话上下文，因此「记下的心情」能被宠物在后续对话中「记得」。
- **三协议统一入口**：OpenAI 兼容 / Gemini / Claude 在后端 `ai_service` 内统一为 `stream_chat` / `chat_completion` / `analyze_vision` 三个入口，对话与情绪分析复用同一份 API 配置，前端无感知切换。
- **MCP 子进程托管**：在专用 Proactor 事件循环线程中管理，跨请求保持连接；Windows 下经 `cmd.exe` 启动 `.cmd` 脚本。

---

## 功能特性

功能按三种核心能力 + 配套能力组织。所有能力均属于同一个项目，由心灵之旅主页面与内置宠物浮层共同承载。

### 能力一 · 网页陪伴（心灵之旅内置宠物浮层）

- 透明宠物浮层（纯 CSS 实现），内置在心灵之旅主页面之上，默认浮于页面右下角。
- 三档尺寸：small(150px) / medium(200px) / large(250px)。
- 可拖拽移动，位置随拖拽更新。
- 双击宠物打开对话面板。
- 右键上下文菜单：打开对话 / 设置 / 切换点击穿透 / 隐藏宠物。
- 点击穿透模式：穿透时仅保留小交互区域可点击，其余区域鼠标事件透传到页面。
- 置顶开关（alwaysOnTop，z-index 99999）。
- 自动打开对话开关（autoOpenChat，进入页面时自动展开对话面板）。
- 自定义宠物图片：支持拖拽图片或粘贴 URL 替换默认柴犬 SVG。
- 页面右下角悬浮托盘菜单。

### 能力二 · 行动（AI Agent + 多模型对话）

- 多模型统一适配：OpenAI 兼容协议 / Gemini / Claude 三套实现，覆盖 11 家提供商。
- SSE 流式打字机回复，前端 Fetch + ReadableStream 解析，支持随时中断（AbortController）。
- 一套配置零成本切换：切换激活的 API 配置即切换模型，无需改代码。
- API 配置管理：增删改查、启用/禁用、设为默认、激活当前使用配置。
- 连接测试：保存前向提供商发「你好」验证连通性，返回友好化错误提示。
- 友好错误降级：密钥错误 / 配额耗尽 / 限流 / 超时 / 网络异常 / 权限 / 404 / 5xx 等，全部翻译为中文友好提示。
- 对话实时入库：用户最后一条消息 + 模型纯输出（不含工具状态行）写入共享对话表。
- 消息中断保护：对话可能已被用户删除，入库前校验存在性，避免孤儿消息。
- 手写 MCP stdio 客户端（JSON-RPC 2.0，换行分隔），完成 initialize 握手 → notifications/initialized → tools/list 全流程。
- MCP 服务器管理：增删改查，字段含 name / command / args / env / enabled。
- 子进程生命周期管理：专用 Proactor 事件循环线程，跨请求保持连接；配置变更后旧连接自动作废重连。
- Windows 兼容：npx/uvx 等 `.cmd` 脚本经 `cmd.exe /c` 启动；专用 Proactor 循环解决 Windows SelectorEventLoop 不支持子进程问题。
- stderr 尾部收集：连接失败时输出最近 3 行 stderr 辅助排查；首次运行 npx/uvx 下载依赖超时友好提示（握手超时 150s）。
- 工具聚合：仅当 `general_settings.mcpEnabled=true` 且服务器 `enabled=true` 且已连接时，把工具转为 OpenAI function 格式注入对话。
- 多轮 Function Calling 循环：单次回复最多 5 轮（防死循环），每轮回填 assistant tool_calls → 调用 MCP → 携带 tool 结果继续对话。
- MCP 工具权限分级：明显只读工具默认可自动执行；未知工具和可能产生副作用的操作默认逐次确认；用户可按工具设为只读自动、每次确认或禁止。
- 高风险操作人工确认：后端先持久化精确的服务器/工具/参数请求，再向前端发 SSE 确认事件；确认通过后才调用 MCP，拒绝、超时、策略封禁或服务器停用均不会执行。确认关联登录用户且 3 分钟过期。
- MCP 管理、策略配置、手动工具调用和确认决策接口均要求登录；手动调用只允许有效的只读策略，其他调用必须走聊天确认链路。
- 工具名去重/转义：非法字符替换为 `_`，重名加服务器前缀，截断至 64 字符；维护 `index` 表把工具名映射回 `(server_id, 原始工具名)`。
- 工具状态可视化：调用时插入「🛠 正在调用工具「xxx」…」状态行流式展示。
- 工具结果抽取：MCP content 中 `type=text` 的文本拼接，超长截断至 8000 字符回填对话。
- 手动调试接口：直接调用已连接 MCP 服务器的任意工具。
- 图片视觉分析：一键截屏 + 多模态模型解读；视觉能力探测（`supportsVision` 标记不支持时友好提示）；三协议视觉流式（OpenAI `image_url` / Gemini `inline_data` / Claude `image source(base64)`）；自动清洗 base64 前缀。

### 能力三 · 共情（心灵之旅情绪领航）

这是心灵之旅主页面的核心能力，由 `soul_service` + SoulJourneyView 承载。用户在心灵之旅主页面选择情绪 + 记录心情后，宠物会以心理咨询视角分析并生成可收藏的「心灵车票」，同时把这次心情对话沉淀进宠物的聊天记忆。

- 情绪选择：开心 / 焦虑 / 平静 / 难过 / 生气 / 疲惫，单击选中。
- 心情输入框记录感受，点击发送触发情绪分析。
- 结构化情绪分析：以「EmoGuide 心理健康顾问」system prompt 约束 AI 只返回 JSON `{analysis, advice, keywords[3]}`，无 markdown 包裹。
- 容错解析：正则提取 JSON、字段缺失兜底、keywords 强制截取前 3 个。
- 无感降级兜底：AI 调用失败 / 返回空 / 解析失败时，按情绪查预置 `SOUL_FALLBACK` 表返回 analysis/advice/keywords，不向用户暴露错误。
- 心灵车票生成：把分析结果渲染成可收藏的「心灵航空机票」卡片，含航班号、情绪主题、关键词、时间、座位号、序列号。
- 情绪主题联动全局：所选情绪实时驱动背景光斑、车票配色、关键词着色（sunshine / healing / ocean / comfort / release / rest 等主题）。
- 彩带庆祝动效：车票生成瞬间触发 100 片 confetti 动画。
- 车票历史收藏：历史车票随时回看，按时间倒序排序，支持单条删除与全部清空，localStorage 持久化。
- 新手引导：首次进入自动引导，可一键查看全部车票。
- 与宠物深度对话联动：心情记录以「[情绪:xxx] 用户输入」「【心理分析】… 【心灵建议】…」格式写入共享对话表，宠物后续对话能基于用户刚记录的心情展开更深入陪伴。
- 对话归属校验：传入的 conversation_id 若已不存在或非本人所有，自动回退到最近活跃对话。

### 配套能力

以下能力服务于上述三种核心能力，属于同一项目的配套设施：

- **用户认证**：注册（用户名 ≥ 2、密码 ≥ 4，唯一性校验）/ 登录（PBKDF2-SHA256，100,000 轮 + 随机 salt）/ 单点登录（新登录清理旧会话，全局仅一个 Token）/ 7 天有效期 / Token Bearer 鉴权（前端拦截器自动附带，401 跳转登录）/ 登出。
- **对话历史管理**：创建对话（归属当前用户，source=chat）/ 获取活跃对话（无则新建，供聊天与情绪分析共享）/ 列出全部对话（按 updated_at 倒序）/ 删除（先删消息再删会话，越权返回 403）/ 读取消息（按 created_at 升序）/ 导出 Markdown（「问题 N / 回答 N」结构）。
- **模板管理**：6 个内置模板（总结要点 / 中英互译 / 润色优化 / 快速解释 / 代码审查 / 解释代码）/ 自定义模板 CRUD / 4 个快捷访问模板配置 / 分类（快速处理 / 编程开发 / 自定义）。
- **设置中心**：通用 JSON 键值设置（`GET/PUT /api/settings/{key}`，含默认兜底）/ 深色模式 / 主题切换（darkMode / chatTheme / chatFontSize）/ 网络代理配置 / 前端代理配置。

---

## 情绪领航工作流

这是心灵之旅主页面「共情」能力的完整闭环。从用户在心灵之旅记录心情，到生成车票、沉淀进宠物的聊天记忆、再到宠物后续对话能基于这次心情展开，整条链路都在同一个项目、同一套对话表内完成：

```
用户进入心灵之旅主页面（/ 路由，需登录） → 选择当前情绪
  （开心 / 焦虑 / 平静 / 难过 / 生气 / 疲惫 → emotionTheme 联动全局界面配色）
        │
        ▼
输入感受 → 点击发送
        │
        ▼
POST /api/soul/analyze
  → soul_service.analyze 复用当前激活的 AI 配置
  → EmoGuide system prompt 约束输出 {analysis, advice, keywords} JSON
        │
        ▼
容错解析 + 无感降级兜底
  （AI 失败/解析异常 → 按情绪查 SOUL_FALLBACK 预置表）
        │
        ▼
渲染「心灵车票」
  （情绪主题色 / 关键词 / 航班号 / 座位号 / 序列号 / 彩带动效）
  → 写入 ticketStore（localStorage 持久化）
        │
        ▼
本次心情对话写入共享 conversations/messages 表
  （[情绪:xxx] 用户输入  +  【心理分析】【心灵建议】AI 回复）
        │
        ▼
心灵之旅内置的宠物聊天面板启动时 loadSharedConversation 读取该对话上下文
        │
        ▼
用户双击宠物 → 围绕刚记录的心情展开更深入、更懂你的陪伴对话
```

---

## 上下文工程与记忆分层

聊天请求由后端统一组装五层上下文，不再把前端加载的完整历史不加区分地直接发送给模型：

| 层级 | 来源与注入策略 | 生命周期 |
|------|----------------|----------|
| 任务上下文 | 当前用户请求 + 最近最多 12 条 user/assistant 消息，整体最多 16,000 字符；本轮任务优先 | 仅本次模型请求 |
| 会话摘要 | 按对话单独维护；每新增 12 条已保存消息尝试生成/更新摘要，并与最近消息共同注入 | 默认 180 天，可配置 |
| 用户长期偏好 | 用户在「设置 → 上下文记忆」中手动维护；最多选择 5 条相关偏好 | 默认不过期，可配置 |
| 工具结果 | MCP 工具调用完成后保存工具名、参数和截断结果；只在原会话内检索 | 默认 7 天，可配置 |
| 全局知识 | 管理员录入并面向所有用户共享；只挑选与当前请求关键词匹配的最多 3 条 | 默认不过期，可配置 |

检索在本地执行，不调用 Embedding API 或外部向量数据库：英文按词、中文按相邻双字切分，按查询词覆盖和记忆词匹配排序。全局知识与工具结果必须命中查询词才会注入；偏好从匹配结果中优先选择，最多 5 条。已过期记忆在聊天检索时惰性清理，也可在设置页手动触发清理。删除会话时会一并删除其摘要和工具结果；「清除我的记忆」不删除聊天记录或全局知识。

摘要/记忆作为参考数据注入，不视为系统指令。会话摘要使用当前激活模型生成；生成失败会记录后端日志，不阻断已生成的聊天回复。长期偏好采用用户显式维护，避免未经确认地把模型猜测固化为用户画像。

首次部署时 `backend/db/schema.sql` 会创建上下文记忆和 MCP 安全策略表。已有数据库部署这些功能时，按顺序执行 `backend/db/migrations/001_context_memories.sql` 和 `backend/db/migrations/002_mcp_tool_safety.sql`，例如 `mysql -u root -p -D <数据库名> < backend/db/migrations/001_context_memories.sql`，然后对 `002_mcp_tool_safety.sql` 重复执行。通过 `backend/.env` 中的 `CONTEXT_ADMIN_USERNAMES` 设置逗号分隔的上下文管理员用户名，例如 `CONTEXT_ADMIN_USERNAMES=alice,bob`；未配置时不会授予任何用户全局知识或保留期限管理权限。修改环境变量后需重启后端。

---

## 支持的 AI 提供商

| Provider | 名称 | 默认模型 | 视觉支持 | 鉴权方式 |
|----------|------|----------|----------|----------|
| deepseek | DeepSeek | deepseek-chat | — | Bearer |
| qwen | 通义千问 Qwen | qwen-plus | ✓ (VL 系列) | Bearer |
| gemini | Google Gemini | gemini-2.5-flash | ✓ | Query 参数 |
| openai | OpenAI | gpt-4o | ✓ | Bearer |
| claude | Anthropic Claude | claude-sonnet-4 | ✓ | x-api-key + anthropic-version |
| groq | Groq | llama-3.3-70b-versatile | — | Bearer |
| zhipu | 智谱 GLM | glm-4-plus | ✓ (GLM-4V) | Bearer |
| moonshot | 月之暗面 Kimi | moonshot-v1-128k | ✓ (Vision) | Bearer |
| yi | 零一万物 Yi | yi-lightning | ✓ (Vision V2) | Bearer |
| siliconflow | 硅基流动 | Qwen2.5-72B | ✓ (VL) | Bearer |
| custom | 自定义 API | gpt-4o | ✓ | Bearer（支持手动输入模型 ID） |

---

## 快速启动

### 一键启动

```bash
# Windows
start.bat

# Linux / macOS
chmod +x start.sh && ./start.sh
```

脚本会先后启动后端（8000）和前端（5173），并打印访问地址与 API 文档地址。
Windows 启动前会检查 8000 和 5173 端口是否已被占用；若已占用，请先关闭旧的后端/前端终端再运行。前端不会自动切换到其他端口，避免浏览器打开旧服务。

### 手动启动

#### 1. 初始化数据库

```bash
mysql -u root -p < backend/db/schema.sql
```

#### 2. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env 填入 MySQL 连接信息
# 设置 DATA_ENCRYPTION_KEY（例如：python -c "import secrets; print(secrets.token_urlsafe(48))"）
```

`DATA_ENCRYPTION_KEY` 必须是至少 32 个字符的长期随机值。可用 `python -c "import secrets; print(secrets.token_urlsafe(48))"` 生成，替换示例文件中的占位值。首次启动会对现有会话 token 做哈希、加密 API/MCP 凭据，并对历史对话、记忆中的手机号、邮箱、身份证号和银行卡号做规则脱敏；迁移完成后，新写入和发给 AI 的文本也会执行相同脱敏。该历史数据变更不可逆，建议先备份数据库；既有未加密备份不会被自动清理。密钥丢失或更换后，已加密的 API/MCP 凭据将无法解密。

生产部署必须通过 HTTPS 反向代理对外提供服务，不要直接公开 HTTP 端口。文本规则无法识别图片中的个人信息；发送图片前请先检查并自行遮挡。

#### 3. 启动后端

```bash
pip install -r requirements.txt
python main.py
```

后端默认运行在 `http://127.0.0.1:8000`（开发模式热重载）。

#### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://localhost:5173`。

---

## 环境变量

后端配置文件 `backend/.env`（参考 `.env.example`）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| MYSQL_HOST | 127.0.0.1 | MySQL 主机 |
| MYSQL_PORT | 3306 | MySQL 端口 |
| MYSQL_USER | root | MySQL 用户名 |
| MYSQL_PASSWORD | (空) | MySQL 密码 |
| MYSQL_DATABASE | hamu_pet | 数据库名（schema.sql 中为 AIChat） |
| API_HOST | 0.0.0.0 | 后端监听地址 |
| API_PORT | 8000 | 后端监听端口 |
| CORS_ORIGINS | http://localhost:5173,http://127.0.0.1:5173 | CORS 白名单 |
| CONTEXT_ADMIN_USERNAMES | (空) | 逗号分隔的上下文管理员用户名；可维护全局知识和记忆保留期限 |
| DATA_ENCRYPTION_KEY | (必填；至少 32 字符) | API 密钥/MCP 环境变量的数据库加密主密钥；需备份且不可随意更换 |

---

## 项目结构

```
hamu-pet/
├── backend/
│   ├── main.py                  # FastAPI 入口（uvicorn，开发模式热重载）
│   ├── api/
│   │   ├── dependencies.py      # get_current_user / optional_user（Token Bearer 鉴权）
│   │   └── v1/
│   │       ├── user.py          # 注册 / 登录 / 登出 / 获取当前用户
│   │       ├── setting.py       # 设置读写 + API 配置管理 + 连接测试
│   │       ├── chat.py          # SSE 流式对话 + 视觉分析 + MCP 工具编排
│   │       ├── context.py       # 记忆管理、检索清理与管理员知识库
│   │       ├── agent.py         # 情绪领航能力接口（/api/soul/analyze）
│   │       ├── template.py      # 内置/自定义模板 + 快捷访问配置
│   │       ├── conversation.py  # 对话 CRUD + 活跃对话 + 消息读取 + Markdown 导出
│   │       └── mcp.py           # MCP 服务器管理 + 连接/断开 + 手动调用
│   ├── services/
│   │   ├── ai_service.py        # 多模型适配（三大协议 11 家）+ SSE 流式 + 视觉理解
│   │   ├── context_service.py   # 分层上下文装配、关键词检索、摘要/TTL
│   │   ├── mcp_service.py       # 手写 MCP stdio 客户端（JSON-RPC 2.0）+ 工具编排
│   │   ├── soul_service.py      # 情绪领航能力：结构化 Prompt + 容错解析 + 降级兜底
│   │   └── setting_service.py   # 设置读写 + 激活配置查找
│   ├── core/security.py         # PBKDF2 密码哈希 + Token 会话（单点登录，7 天有效）
│   ├── models/
│   │   ├── db_models.py         # SQLAlchemy ORM 模型
│   │   └── schemas.py           # Pydantic 请求/响应 Schema
│   ├── config/
│   │   ├── settings.py          # 环境变量加载（MySQL / Server / CORS）
│   │   └── constants.py         # 11 家提供商模板 + 6 个内置模板
│   ├── db/
│   │   ├── session.py           # SQLAlchemy Engine + SessionLocal + Base
│   │   └── schema.sql           # MySQL 建表脚本（含默认设置）
│   ├── .env.example             # 环境变量示例
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.ts              # 应用入口（Pinia + Router + Element Plus 中文）
│   │   ├── App.vue              # 根组件（心灵之旅主页面 + 内置宠物浮层）
│   │   ├── router/index.ts      # 路由（/login → /soul，鉴权守卫）
│   │   ├── api/index.ts         # API 客户端（axios + Fetch SSE 流式解析）
│   │   ├── types/index.ts      # TypeScript 类型定义
│   │   ├── store/
│   │   │   ├── app.ts           # 宠物设置/主题/API配置/对话/情绪主题
│   │   │   ├── auth.ts          # 登录态（localStorage 持久化 token+user）
│   │   │   └── ticketStore.ts   # 心灵车票历史（localStorage 持久化）
│   │   ├── pages/
│   │   │   ├── LoginView.vue    # 登录/注册页
│   │   │   └── SoulJourneyView.vue  # 心灵之旅主页面（登录后默认路由，内置宠物浮层）
│   │   ├── components/
│   │   │   ├── PetWindow.vue    # 宠物浮层本体（拖拽/穿透/右键菜单/自定义图片）
│   │   │   ├── ChatPanel.vue    # AI 对话页（新建/历史/继续交流，SSE 流式 + 中断）
│   │   │   ├── SettingsPanel.vue# 设置页（API配置/MCP/主题/模板）
│   │   │   ├── TrayMenu.vue     # 右下角托盘菜单
│   │   │   └── soul/            # 心灵之旅情绪领航组件（主页面核心模块）
│   │   │       ├── TicketGenerator.vue  # 心灵车票生成（彩带动效）
│   │   │       ├── TicketHistory.vue    # 车票历史收藏
│   │   │       ├── AdviceDisplay.vue   # 情绪分析结果展示
│   │   │       └── OnboardingGuide.vue  # 新手引导
│   │   └── styles/global.css    # 全局样式
│   ├── vite.config.ts           # Vite 配置（@ 别名 + /api 代理 → 8000）
│   ├── tsconfig.json
│   └── package.json
├── start.bat                   # Windows 一键启动脚本
├── start.sh                    # Linux/macOS 一键启动脚本
├── LICENSE
└── README.md
```

---

## 数据库设计

数据库名 `AIChat`，字符集 `utf8mb4`，共 11 张表：

| 表名 | 主要字段 | 说明 |
|------|----------|------|
| `users` | id, username, password_hash, created_at | 用户（UUID 主键） |
| `sessions` | token, user_id, created_at, expires_at | 单点登录会话，7 天有效 |
| `settings` | setting_key, setting_value(JSON), updated_at | 通用键值设置 |
| `api_configs` | name, provider, api_url, api_key, selected_model, enabled, is_default | 多 API 配置 |
| `conversations` | id, title, user_id, source(chat/soul), created_at, updated_at | 对话（宠物的对话能力与共情能力共享） |
| `messages` | id, conversation_id, role(user/assistant/system), content, model | 消息 |
| `context_memories` | user_id, conversation_id, kind, title, content, expires_at, last_accessed_at | 会话摘要、用户偏好、工具结果和全局知识 |
| `custom_templates` | name, icon, category, prompt | 自定义模板 |
| `mcp_servers` | name, command, args(JSON), env(JSON), enabled | MCP 服务器配置 |
| `mcp_tool_policies` | user_id, server_id, tool_name, mode | 用户对工具设置的自动执行/确认/禁止策略 |
| `mcp_tool_approvals` | user_id, conversation_id, server_id, tool_name, arguments(JSON), status, expires_at | 一次性人工确认请求及决策状态 |

默认设置（schema.sql 初始化写入）：

| setting_key | 默认值 |
|-------------|--------|
| pet_settings | `{petSize: medium, petImageUrl: null, alwaysOnTop: false, clickThrough: false, autoOpenChat: false}` |
| theme_settings | `{darkMode: false, chatTheme: shiba, chatFontSize: medium}` |
| general_settings | `{saveHistory: true, markdownPath: ./conversations, mcpEnabled: false}` |
| network_proxy | `{enabled: false, host: 127.0.0.1, port: 7890}` |
| proxy_config | `{enabled: false, port: 3001, autoSyncApiConfigs: true}` |
| quick_access_templates | `["summarize","translate","polish","explain"]` |
| active_config_id | `null` |

---

## API 接口

启动后端后访问 `http://127.0.0.1:8000/docs` 查看 Swagger 交互式文档。

### 认证（/api/auth）

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| POST | /api/auth/register | 注册（用户名≥2，密码≥4） | — |
| POST | /api/auth/login | 登录（PBKDF2 校验，颁发 Token） | — |
| POST | /api/auth/logout | 登出（清除全部会话） | ✓ |
| GET | /api/auth/me | 获取当前用户信息 | ✓ |

### 设置与提供商（/api）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/providers | 获取 11 家提供商模板 |
| GET | /api/settings/{key} | 读取设置项（含默认兜底） |
| PUT | /api/settings/{key} | 更新设置项 |

### API 配置管理（/api/api-configs）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/api-configs | 列出全部配置 |
| POST | /api/api-configs | 新建配置 |
| PUT | /api/api-configs/{id} | 更新配置 |
| DELETE | /api/api-configs/{id} | 删除配置 |
| POST | /api/api-configs/{id}/activate | 激活配置 |
| GET | /api/api-configs/active | 获取当前激活配置 |
| POST | /api/api-configs/test | 测试连通性 |

### AI 对话（/api/chat）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/chat/stream | SSE 流式对话（含 MCP 工具编排，最多 5 轮） |
| POST | /api/chat/vision/stream | SSE 流式视觉分析（多模态） |

### 情绪领航（/api/soul）

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| POST | /api/soul/analyze | 宠物共情能力：情绪结构化分析 + 写入共享对话 | ✓ |

### MCP 服务器管理（/api/mcp）

所有 MCP 管理、权限策略和人工确认接口均要求登录。工具默认策略只自动放行明确的低风险元数据/列表类只读操作；文件内容读取、搜索、未知操作和副作用操作需逐次确认。禁止策略会将工具从模型可用工具列表移除。将工具手动设为自动执行，表示用户明确选择信任该工具。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/mcp/servers | 列出全部 MCP 服务器（含连接状态） |
| POST | /api/mcp/servers | 新建服务器 |
| PUT | /api/mcp/servers/{id} | 更新服务器（变更后自动断开旧连接） |
| DELETE | /api/mcp/servers/{id} | 删除服务器（先断开再删除） |
| POST | /api/mcp/servers/{id}/connect | 连接服务器（initialize 握手 + tools/list） |
| POST | /api/mcp/servers/{id}/disconnect | 断开服务器 |
| PUT | /api/mcp/servers/{id}/tool-policy | 设置工具权限级别（只读自动/每次确认/禁止） |
| POST | /api/mcp/approvals/{id}/decision | 对当前用户的一次性工具调用请求确认或拒绝 |
| POST | /api/mcp/call | 手动调用工具（仅只读自动策略允许） |

### 对话历史（/api/conversations）

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| POST | /api/conversations | 创建对话 | ✓ |
| GET | /api/conversations/user/active | 获取活跃对话（无则新建） | ✓ |
| GET | /api/conversations/user | 列出当前用户全部对话 | ✓ |
| DELETE | /api/conversations/{id} | 删除对话+消息（校验归属） | ✓ |
| GET | /api/conversations/{id}/messages | 读取消息（校验归属） | ✓ |
| POST | /api/conversations/save | 导出 Markdown | ✓ |

### 上下文记忆（/api/context）

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| GET | /api/context/memories | 列出当前用户记忆与全局知识，并返回管理员状态/TTL | ✓ |
| POST | /api/context/memories | 新增长期偏好；全局知识仅管理员可写 | ✓ |
| PUT | /api/context/memories/{id} | 编辑手动偏好或全局知识 | ✓ |
| DELETE | /api/context/memories/{id} | 删除本人记忆；全局知识仅管理员可删 | ✓ |
| DELETE | /api/context/memories | 清除当前用户上下文记忆，不影响聊天记录 | ✓ |
| POST | /api/context/cleanup | 手动清理当前用户过期记忆 | ✓ |
| PUT | /api/context/retention | 设置四类记忆 TTL，并重算已有记忆到期时间 | 管理员 |

### 模板（/api/templates）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/templates/builtin | 6 个内置模板 |
| GET | /api/templates/custom | 自定义模板列表 |
| POST | /api/templates/custom | 新建自定义模板 |
| PUT | /api/templates/custom/{id} | 更新自定义模板 |
| DELETE | /api/templates/custom/{id} | 删除自定义模板 |
| GET | /api/templates/quick-access | 快捷访问模板 id 列表 |
| PUT | /api/templates/quick-access | 更新快捷访问模板 |

### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | `{status: ok, version: 3.0.0}` |

---

## 前端架构

### 路由

| 路径 | 组件 | 说明 |
|------|------|------|
| /login | LoginView | 登录/注册页 |
| / | SoulJourneyView | 心灵之旅主页面（登录后默认路由，requiresAuth） |
| /chat/:conversationId? | ChatPanel | AI 对话、新建对话、历史选择、继续对话（requiresAuth） |
| /settings | SettingsPanel | 独立设置页面（requiresAuth） |
| /:pathMatch(.*)* | — | 重定向到 / |

路由守卫：未登录访问受保护页面跳转 /login；已登录访问 /login 跳转 /（心灵之旅主页面）。

### 状态管理（Pinia）

| Store | 职责 | 持久化 |
|-------|------|--------|
| auth | token / user / 登录态校验 | localStorage（hamu_token / hamu_user） |
| app | petSettings / themeSettings / apiConfigs / activeConfigId / messages / conversationId / emotionTheme / petVisible | — |
| ticketStore | ticketHistoryList / currentTicket | localStorage（ticketStore，仅持久化 ticketHistoryList） |

### API 客户端（api/index.ts）

- axios 实例：baseURL `/api`，30s 超时；请求拦截器自动附带 Bearer Token；响应拦截器 401 时清除登录态并跳转 /login。
- `streamChat` / `streamVision`：基于 Fetch + ReadableStream 的 SSE 流式解析，返回 AbortController 支持随时中断。
- `analyzeSoulEmotion`：情绪领航能力调用（POST /api/soul/analyze），与对话共用同一份登录态。
- MCP 服务器管理：listMcpServers / createMcpServer / updateMcpServer / deleteMcpServer / connectMcpServer / disconnectMcpServer。

### 根组件 App.vue

- `<router-view />` 渲染心灵之旅、独立 AI 对话或独立设置页面。
- 登录后显示 `.pet-overlay` 浮层，包含 PetWindow / TrayMenu 快捷入口；对话和设置通过路由切换到独立页面。
- 点击穿透模式下，宠物浮层 `pointer-events: none`，仅 `.pet-interactive-zone` 可交互。
- onMounted 时校验 Token → 加载宠物设置 → 加载共享对话上下文（情绪分析写入的记忆在此被读取）。

---

## 关键实现细节

### 三大 AI 协议统一适配

`ai_service.py` 把 OpenAI 兼容 / Gemini / Claude 三套协议统一为三个入口：

- `stream_chat(provider, api_url, api_key, model, messages, config_name, tools)` → SSE 流式生成器
- `chat_completion(...)` → 非流式收集完整内容（情绪领航能力用）
- `analyze_vision(provider, api_url, api_key, model, image_base64, prompt)` → 视觉流式生成器

URL 规范化：OpenAI 兼容协议自动补全 `/chat/completions` 后缀。

工具调用流式聚合：OpenAI 协议的 `tool_calls` 以增量方式返回，按 `index` 聚合 `id` / `name` / `arguments` 后一次性抛出。

### MCP stdio 客户端

- JSON-RPC 2.0，换行分隔，protocolVersion `2024-11-05`。
- 专用 Proactor 事件循环线程（`_McpLoopThread`）：Windows 下 uvicorn 默认 SelectorEventLoop 不支持子进程，所有 MCP 协程调度到该线程的 ProactorEventLoop 执行，会话跨请求保持。
- 命令解析：`shutil.which` 查找命令路径；Windows 下 `.cmd` / `.bat` 脚本经 `cmd.exe /c` 启动。
- 握手超时 150s（兼容首次 npx/uvx 下载依赖），工具调用超时 90s，普通请求超时 30s。
- stderr 尾部保留最近 20 行，连接失败时输出最近 3 行辅助排查。

### 多轮 Function Calling

`chat.py` 的 `event_generator` 实现多轮工具调用循环：

1. 流式调用 `ai_service.stream_chat`，累积 `content` 和 `tool_calls`。
2. 若有 `tool_calls`：回填 assistant 消息（含 tool_calls）→ 逐个调用 MCP 工具 → 携带 tool 结果继续下一轮。
3. 最多 5 轮（`MAX_TOOL_ROUNDS`），防止死循环。
4. 工具状态行（🛠）仅流式展示给用户，不计入 `db_content` 入库。

### 情绪领航降级兜底

`soul_service.py` 实现宠物共情能力的三级容错：

1. AI 正常返回 → `parse_soul_response` 正则提取 JSON + 字段校验。
2. AI 失败/解析异常 → `soul_fallback(emotion)` 查 `SOUL_FALLBACK` 预置表（6 种情绪各一套 analysis/advice/keywords）。
3. 未知情绪 → 通用兜底文案。

用户始终拿到完整结果，不会看到 AI 错误。

### 密码安全

`core/security.py`：

- PBKDF2-HMAC-SHA256，100,000 轮迭代。
- 每次哈希生成 16 字节随机 salt，存储格式 `salt$hash_hex`。
- Token：`secrets.token_urlsafe(32)` 生成，64 字符。
- 单点登录：新会话清理旧会话，全局仅一个有效 Token。

### 对话共享与防孤儿消息

心灵之旅的情绪领航能力与宠物的对话能力共用同一份对话表，因此宠物「记得」用户在心灵之旅记下的心情：

- 聊天（chat.py）与情绪分析（soul_service.py）写入同一 `conversations` / `messages` 表，构成宠物的统一记忆。
- 情绪分析写入前校验 `conversation_id` 归属与存在性，失效则回退到最近活跃对话。
- 聊天入库前校验对话是否仍存在（用户可能已删除），避免孤儿消息。

---

## 生产构建

```bash
cd frontend
npm run build
# 静态文件输出到 frontend/dist/ 目录
```

构建过程：`vue-tsc -b`（TypeScript 类型检查）+ `vite build`（打包）。

---

## 许可证

MIT License
