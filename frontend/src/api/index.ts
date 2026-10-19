import axios from 'axios'
import type {
  ApiConfig,
  AuthResponse,
  ChatMessage,
  ContextMemory,
  ContextMemoryState,
  ConversationItem,
  McpServerInfo,
  PetSettings,
  StoredMessage,
  SoulAnalysis,
  ThemeSettings,
  UserInfo,
} from '@/types'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

// 请求拦截：自动附带 token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('hamu_token')
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：401 时清除登录态
api.interceptors.response.use(
  (resp) => resp,
  (err) => {
    if (err?.response?.status === 401) {
      localStorage.removeItem('hamu_token')
      localStorage.removeItem('hamu_user')
      if (location.pathname !== '/login') {
        location.href = '/login'
      }
    }
    return Promise.reject(err)
  },
)

function mapApiConfig(raw: Record<string, unknown>): ApiConfig {
  return {
    id: raw.id as string,
    name: raw.name as string,
    provider: raw.provider as string,
    apiUrl: (raw.api_url ?? raw.apiUrl) as string,
    apiKey: '',
    hasApiKey: raw.has_api_key === true || raw.hasApiKey === true,
    selectedModel: (raw.selected_model ?? raw.selectedModel) as string,
    enabled: raw.enabled as boolean,
    isDefault: (raw.is_default ?? raw.isDefault) as boolean,
  }
}

export async function getProviders() {
  const { data } = await api.get('/providers')
  return data
}

export async function getSetting<T>(key: string): Promise<T> {
  const { data } = await api.get(`/settings/${key}`)
  return data
}

export async function updateSetting(key: string, value: unknown) {
  const { data } = await api.put(`/settings/${key}`, { value })
  return data
}

export async function getPetSettings(): Promise<PetSettings> {
  return getSetting<PetSettings>('pet_settings')
}

export async function savePetSettings(value: PetSettings) {
  return updateSetting('pet_settings', value)
}

export async function getThemeSettings(): Promise<ThemeSettings> {
  return getSetting<ThemeSettings>('theme_settings')
}

export async function saveThemeSettings(value: ThemeSettings) {
  return updateSetting('theme_settings', value)
}

export async function getApiConfigs(): Promise<ApiConfig[]> {
  const { data } = await api.get('/api-configs')
  return data.map(mapApiConfig)
}

export async function getActiveConfig(): Promise<ApiConfig | null> {
  const { data } = await api.get('/api-configs/active')
  return data ? mapApiConfig(data) : null
}

export async function createApiConfig(config: Omit<ApiConfig, 'id' | 'hasApiKey'>) {
  const { data } = await api.post('/api-configs', {
    name: config.name,
    provider: config.provider,
    api_url: config.apiUrl,
    api_key: config.apiKey,
    selected_model: config.selectedModel,
    enabled: config.enabled,
    is_default: config.isDefault,
  })
  return mapApiConfig(data)
}

export async function updateApiConfig(id: string, config: Partial<ApiConfig>) {
  const payload: Record<string, unknown> = {}
  if (config.name !== undefined) payload.name = config.name
  if (config.provider !== undefined) payload.provider = config.provider
  if (config.apiUrl !== undefined) payload.api_url = config.apiUrl
  if (config.apiKey !== undefined) payload.api_key = config.apiKey
  if (config.selectedModel !== undefined) payload.selected_model = config.selectedModel
  if (config.enabled !== undefined) payload.enabled = config.enabled
  if (config.isDefault !== undefined) payload.is_default = config.isDefault
  const { data } = await api.put(`/api-configs/${id}`, payload)
  return mapApiConfig(data)
}

export async function deleteApiConfig(id: string) {
  await api.delete(`/api-configs/${id}`)
}

export async function activateConfig(id: string) {
  await api.post(`/api-configs/${id}/activate`)
}

export async function testApiConfig(provider: string, apiUrl: string, apiKey: string, selectedModel: string) {
  const { data } = await api.post('/api-configs/test', {
    provider, api_url: apiUrl, api_key: apiKey, selected_model: selectedModel,
  })
  return data
}

export async function testSavedApiConfig(id: string) {
  const { data } = await api.post(`/api-configs/${id}/test`)
  return data
}

export async function getBuiltinTemplates() {
  const { data } = await api.get('/templates/builtin')
  return data
}

export async function getCustomTemplates() {
  const { data } = await api.get('/templates/custom')
  return data
}

export async function getQuickAccessTemplates() {
  const { data } = await api.get('/templates/quick-access')
  return data
}

export async function saveConversation(messages: ChatMessage[], title?: string) {
  const { data } = await api.post('/conversations/save', { messages, title })
  return data
}

export async function createConversation() {
  const { data } = await api.post('/conversations')
  return data
}

// 删除对话及其全部消息（后端同事务先删消息再删会话）
export async function deleteConversation(conversationId: string) {
  const { data } = await api.delete(`/conversations/${conversationId}`)
  return data
}

// 获取当前用户的活跃共享对话（hamu-pet 与心灵之旅共享）
export async function getActiveConversation(): Promise<{ id: string; title: string; source: string }> {
  const { data } = await api.get('/conversations/user/active')
  return data
}

export async function listUserConversations(): Promise<ConversationItem[]> {
  const { data } = await api.get('/conversations/user')
  return data
}

export async function getConversationMessages(conversationId: string): Promise<StoredMessage[]> {
  const { data } = await api.get(`/conversations/${conversationId}/messages`)
  return data
}

export async function getContextMemories(): Promise<ContextMemoryState> {
  const { data } = await api.get('/context/memories')
  return data
}

export async function createContextMemory(payload: Pick<ContextMemory, 'kind' | 'title' | 'content'>) {
  const { data } = await api.post('/context/memories', payload)
  return data as ContextMemory
}

export async function updateContextMemory(id: string, payload: Partial<Pick<ContextMemory, 'title' | 'content'>>) {
  const { data } = await api.put(`/context/memories/${id}`, payload)
  return data as ContextMemory
}

export async function deleteContextMemory(id: string) {
  const { data } = await api.delete(`/context/memories/${id}`)
  return data
}

export async function clearContextMemories() {
  const { data } = await api.delete('/context/memories')
  return data as { success: boolean; deleted: number }
}

export async function cleanupContextMemories() {
  const { data } = await api.post('/context/cleanup')
  return data as { success: boolean; deleted: number }
}

export async function updateContextRetention(ttlDays: ContextMemoryState['ttl_days']) {
  const { data } = await api.put('/context/retention', { ttl_days: ttlDays })
  return data as { ttl_days: ContextMemoryState['ttl_days'] }
}

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('hamu_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export function streamChat(
  messages: ChatMessage[],
  configId: string | null,
  conversationId: string | null,
  onChunk: (content: string) => void,
  onError: (error: string) => void,
  onDone: (model?: string) => void,
  onConfirmation: (confirmation: {
    approval_id: string
    server_name: string
    tool_name: string
    description: string
    arguments: Record<string, unknown>
    expires_in_seconds: number
  }) => Promise<void>,
  onReasoning?: (content: string) => void,
): AbortController {
  const controller = new AbortController()
  let settled = false
  const fail = (message: string) => {
    if (settled) return
    settled = true
    onError(message)
  }
  const complete = (model?: string) => {
    if (settled) return
    settled = true
    onDone(model)
  }

  fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({
      messages: messages.map(m => ({ role: m.role, content: m.content })),
      config_id: configId,
      conversation_id: conversationId,
    }),
    signal: controller.signal,
  }).then(async (response) => {
    if (!response.ok || !response.body) {
      let detail = ''
      try {
        const body = await response.json() as { detail?: string }
        detail = body.detail || ''
      } catch {
        detail = ''
      }
      fail(detail || `聊天请求失败（HTTP ${response.status}），请检查服务状态后重试`)
      return
    }
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    const processLine = async (line: string): Promise<boolean> => {
      const normalized = line.endsWith('\r') ? line.slice(0, -1) : line
      if (!normalized.startsWith('data:')) return false
      const payload = normalized.slice(5).trimStart()
      if (payload === '[DONE]') {
        complete()
        return true
      }
      if (!payload) return false

      let data: {
        error?: string
        content?: string
        reasoning?: string
        confirmation_required?: {
          approval_id: string
          server_name: string
          tool_name: string
          description: string
          arguments: Record<string, unknown>
          expires_in_seconds: number
        }
        done?: boolean
        model?: string
      }
      try {
        data = JSON.parse(payload)
      } catch {
        return false
      }
      if (data.error) {
        fail(data.error)
        return true
      }
      if (data.reasoning) onReasoning?.(data.reasoning)
      if (data.content) onChunk(data.content)
      if (data.confirmation_required) {
        try {
          await onConfirmation(data.confirmation_required)
        } catch (error) {
          fail(error instanceof Error ? error.message : '工具确认失败')
          return true
        }
      }
      if (data.done) {
        complete(data.model)
        return true
      }
      return false
    }

    while (!settled) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (await processLine(line)) return
      }
    }
    buffer += decoder.decode()
    if (buffer && await processLine(buffer)) return
    if (!settled) fail('聊天连接已结束，但服务端没有发送完成信号。请重试。')
  }).catch((err) => {
    if (err.name !== 'AbortError') fail(err.message || '聊天连接中断，请检查网络或后端服务后重试')
  })

  return controller
}

export function streamVision(
  imageBase64: string,
  configId: string | null,
  prompt?: string,
  onChunk?: (content: string) => void,
  onError?: (error: string) => void,
  onDone?: () => void,
): AbortController {
  const controller = new AbortController()

  fetch('/api/chat/vision/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ image_base64: imageBase64, config_id: configId, prompt }),
    signal: controller.signal,
  }).then(async (response) => {
    if (!response.ok || !response.body) {
      onError?.('视觉分析请求失败')
      return
    }
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const payload = line.slice(6).trim()
        if (payload === '[DONE]') { onDone?.(); return }
        try {
          const data = JSON.parse(payload)
          if (data.error) { onError?.(data.error); return }
          if (data.content) onChunk?.(data.content)
        } catch { /* skip */ }
      }
    }
    onDone?.()
  }).catch((err) => {
    if (err.name !== 'AbortError') onError?.(err.message)
  })

  return controller
}

// ---------- 认证 ----------
export async function register(username: string, password: string): Promise<AuthResponse> {
  const { data } = await api.post('/auth/register', { username, password })
  return data
}

export async function login(username: string, password: string): Promise<AuthResponse> {
  const { data } = await api.post('/auth/login', { username, password })
  return data
}

export async function logout(): Promise<void> {
  try {
    await api.post('/auth/logout')
  } catch { /* ignore */ }
}

export async function getMe(): Promise<UserInfo> {
  const { data } = await api.get('/auth/me')
  return data
}

// ---------- 心灵之旅：情绪分析（前后端分离） ----------
export async function analyzeSoulEmotion(
  emotion: string,
  userInput: string,
  conversationId: string | null,
): Promise<SoulAnalysis> {
  const { data } = await api.post('/soul/analyze', {
    emotion,
    user_input: userInput,
    conversation_id: conversationId,
  })
  return data
}

// ---------- MCP 工具 ----------
export async function listMcpServers(): Promise<McpServerInfo[]> {
  const { data } = await api.get('/mcp/servers')
  return data
}

export async function createMcpServer(payload: {
  name: string
  command: string
  args: string[]
  env: Record<string, string>
  enabled: boolean
}): Promise<McpServerInfo> {
  const { data } = await api.post('/mcp/servers', payload)
  return data
}

export async function updateMcpServer(id: string, payload: { enabled?: boolean }) {
  const { data } = await api.put(`/mcp/servers/${id}`, payload)
  return data
}

export async function deleteMcpServer(id: string) {
  await api.delete(`/mcp/servers/${id}`)
}

export async function connectMcpServer(
  id: string,
): Promise<{ success: boolean; toolCount: number; tools: { name: string; description: string }[] }> {
  const { data } = await api.post(`/mcp/servers/${id}/connect`)
  return data
}

export async function disconnectMcpServer(id: string) {
  await api.post(`/mcp/servers/${id}/disconnect`)
}

export async function updateMcpToolPolicy(
  serverId: string,
  toolName: string,
  mode: 'read_only' | 'confirm' | 'blocked',
) {
  const { data } = await api.put(`/mcp/servers/${serverId}/tool-policy`, {
    tool_name: toolName,
    mode,
  })
  return data
}

export async function decideMcpToolApproval(approvalId: string, approve: boolean) {
  const { data } = await api.post(`/mcp/approvals/${approvalId}/decision`, { approve })
  return data as { success: boolean; status: 'approved' | 'rejected' }
}
