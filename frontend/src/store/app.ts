import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ApiConfig, ChatMessage, PetSettings, ThemeSettings } from '@/types'
import * as api from '@/api'

export const useAppStore = defineStore('app', () => {
  const petSettings = ref<PetSettings>({
    petSize: 'medium',
    petImageUrl: null,
    alwaysOnTop: false,
    clickThrough: false,
    autoOpenChat: false,
  })

  const themeSettings = ref<ThemeSettings>({
    darkMode: false,
    chatTheme: 'shiba',
    chatFontSize: 'medium',
  })

  const apiConfigs = ref<ApiConfig[]>([])
  const activeConfigId = ref<string | null>(null)
  const petVisible = ref(true)
  // 当前心情主题（由心灵之旅选择情绪时写入），用于联动对话抽屉等界面配色
  // 取值：default | sunshine | healing | ocean | comfort | release | rest
  const emotionTheme = ref('default')
  const messages = ref<ChatMessage[]>([])
  const conversationId = ref<string | null>(null)
  const isGenerating = ref(false)

  async function loadSettings() {
    petSettings.value = await api.getPetSettings()
    themeSettings.value = await api.getThemeSettings()
    apiConfigs.value = await api.getApiConfigs()
    const active = await api.getActiveConfig()
    activeConfigId.value = active?.id ?? null
    applyTheme()
  }

  /** 加载当前用户的共享对话（与心灵之旅联动） */
  async function loadSharedConversation() {
    try {
      const conv = await api.getActiveConversation()
      conversationId.value = conv.id
      const stored = await api.getConversationMessages(conv.id)
      messages.value = stored.map((m) => ({
        role: m.role as ChatMessage['role'],
        content: m.content,
        model: m.model ?? undefined,
      }))
    } catch {
      // 未登录或后端未启动时静默处理
    }
  }

  async function savePetSettings() {
    await api.savePetSettings(petSettings.value)
  }

  async function saveThemeSettings() {
    // 先应用主题再持久化：即使后端保存失败，界面也能立即生效
    applyTheme()
    try {
      await api.saveThemeSettings(themeSettings.value)
    } catch (e) {
      console.error('保存主题设置失败:', e)
    }
  }

  function applyTheme() {
    const root = document.documentElement
    // Element Plus 深色变量挂在 html.dark 上
    root.classList.toggle('dark', themeSettings.value.darkMode)
    // 与心灵之旅联动：心灵之旅的深色样式挂在 body.dark-mode 上
    document.body.classList.toggle('dark-mode', themeSettings.value.darkMode)
    root.setAttribute('data-theme', themeSettings.value.chatTheme)
    root.setAttribute('data-font-size', themeSettings.value.chatFontSize)
  }

  async function refreshApiConfigs() {
    apiConfigs.value = await api.getApiConfigs()
    const active = await api.getActiveConfig()
    activeConfigId.value = active?.id ?? null
  }

  function addMessage(msg: ChatMessage) {
    messages.value.push(msg)
  }

  function updateLastAssistant(content: string, model?: string) {
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'assistant') {
      last.content = content
      if (model) last.model = model
    }
  }

  function clearMessages() {
    messages.value = []
  }

  /** 心灵之旅选择情绪时调用，联动对话抽屉等界面的心情配色 */
  function setEmotionTheme(theme: string) {
    emotionTheme.value = theme || 'default'
  }

  return {
    petSettings, themeSettings, apiConfigs, activeConfigId,
    petVisible, emotionTheme, messages, conversationId, isGenerating,
    loadSettings, loadSharedConversation, savePetSettings, saveThemeSettings, refreshApiConfigs,
    addMessage, updateLastAssistant, clearMessages, setEmotionTheme, applyTheme,
  }
})
