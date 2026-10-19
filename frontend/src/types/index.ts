export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  model?: string
  /** 推理模型的思考内容（仅流式展示，不入库、不参与后续请求） */
  reasoning?: string
  streaming?: boolean
}

export interface ApiConfig {
  id: string
  name: string
  provider: string
  apiUrl: string
  apiKey: string
  hasApiKey: boolean
  selectedModel: string
  enabled: boolean
  isDefault: boolean
}

export interface PetSettings {
  petSize: 'small' | 'medium' | 'large'
  petImageUrl: string | null
  alwaysOnTop: boolean
  clickThrough: boolean
  autoOpenChat: boolean
}

export interface ThemeSettings {
  darkMode: boolean
  chatTheme: 'shiba' | 'blue' | 'purple' | 'green'
  chatFontSize: 'small' | 'medium' | 'large'
}

export interface ProviderModel {
  id: string
  name: string
  supportsVision?: boolean
  recommended?: boolean
  isCustomInput?: boolean
}

export interface ProviderTemplate {
  name: string
  brandColor: string
  defaultApiUrl: string
  defaultModel: string
  authType: string
  models: ProviderModel[]
  allowCustomModel?: boolean
}

export interface PromptTemplate {
  id: string
  name: string
  icon: string
  category: string
  prompt: string
  isBuiltin: boolean
}

// ---------- 认证 ----------
export interface UserInfo {
  id: string
  username: string
}

export interface AuthResponse {
  token: string
  user: UserInfo
}

// ---------- 心灵之旅：情绪分析 ----------
export interface SoulAnalysis {
  analysis: string
  advice: string
  keywords: string[]
  conversationId: string
}

// ---------- 共享对话记录 ----------
export interface ConversationItem {
  id: string
  title: string
  source: 'chat' | 'soul'
  created_at?: string | null
}

export interface StoredMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  model?: string | null
  created_at?: string | null
}

export type ContextMemoryKind = 'session_summary' | 'preference' | 'tool_result' | 'global_knowledge'

export interface ContextMemory {
  id: string
  kind: ContextMemoryKind
  title: string
  content: string
  source: string
  conversation_id: string | null
  expires_at: string | null
  created_at: string | null
  updated_at: string | null
  is_global: boolean
}

export interface ContextMemoryState {
  is_admin: boolean
  memories: ContextMemory[]
  ttl_days: Record<ContextMemoryKind, number | null>
  default_ttl_days: Record<ContextMemoryKind, number | null>
}

// ---------- MCP 工具 ----------
export interface McpToolInfo {
  name: string
  description: string
  mode: 'read_only' | 'confirm' | 'blocked'
}

export interface McpServerInfo {
  id: string
  name: string
  command: string
  args: string[]
  env: Record<string, string>
  enabled: boolean
  connected: boolean
  toolCount: number
  tools: McpToolInfo[]
}

// ---------- 心灵车票 ----------
export interface Ticket {
  id?: string
  date: string
  flightCode: string
  from: string
  to: string
  message: string
  keywords: string[]
  analysis?: string
  advice?: string
  seatNumber?: string
  serialNumber?: string
  emotion?: string
}
