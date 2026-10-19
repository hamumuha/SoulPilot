<template>
  <div class="chat-page" :class="`emotion-${store.emotionTheme}`">
    <aside class="conversation-sidebar">
      <div class="sidebar-heading">
        <el-button class="back-button" text @click="router.push({ name: 'soul' })">← 心灵之旅</el-button>
        <h1>AI 智能对话</h1>
      </div>
      <el-button class="new-chat-button" type="primary" :icon="Plus" :disabled="store.isGenerating" @click="startNewConversation">
        新建对话
      </el-button>
      <div class="conversation-list">
        <button
          v-for="conversation in conversations"
          :key="conversation.id"
          class="conversation-entry"
          :class="{ active: conversation.id === store.conversationId }"
          @click="openConversation(conversation.id)"
        >
          <span class="conversation-entry-title">{{ conversation.title || '新对话' }}</span>
          <el-icon
            class="conversation-delete"
            title="删除对话"
            @click.stop="deleteConversationEntry(conversation)"
          ><Delete /></el-icon>
        </button>
        <p v-if="!conversations.length" class="history-empty">暂无历史对话</p>
      </div>
      <el-button class="settings-link" text :icon="Setting" @click="router.push({ name: 'settings' })">
        设置
      </el-button>
    </aside>

    <main class="chat-workspace">
      <header class="chat-page-header">
        <div>
          <strong>{{ currentConversationTitle }}</strong>
          <span v-if="currentConversationSource === 'soul'" class="source-label">心灵之旅记录</span>
        </div>
        <div class="chat-toolbar">
          <el-select v-model="store.activeConfigId" placeholder="选择 API 配置" size="small" @change="onConfigChange">
            <el-option v-for="c in store.apiConfigs" :key="c.id" :label="c.name" :value="c.id" :disabled="!c.enabled" />
          </el-select>
          <el-button size="small" :icon="Download" @click="saveChat" title="导出对话" />
        </div>
      </header>

      <div class="quick-templates">
        <el-button v-for="tpl in quickTemplates" :key="tpl.id" size="small" round @click="applyTemplate(tpl)">
          {{ tpl.icon }} {{ tpl.name }}
        </el-button>
      </div>

      <div ref="messagesRef" class="chat-messages">
        <div v-if="store.messages.length === 0" class="welcome">
          <p>👋 你好！我是 SoulPilot · 心灵领航员</p>
          <p>可以开始一段新对话，或从左侧选择历史记录继续交流。</p>
        </div>
        <div
          v-for="(msg, idx) in store.messages"
          :key="idx"
          class="message"
          :class="msg.role"
          @click="msg.role === 'user' ? editMessage(idx) : undefined"
        >
          <div class="message-content" :class="{ streaming: msg.streaming }">
            <span v-if="msg.role === 'assistant' && msg.model" class="model-tag">{{ msg.model }}</span>
            <span v-if="msg.role === 'assistant' && msg.reasoning" class="reasoning-block">{{ msg.reasoning }}</span>
            {{
              msg.content ||
              (msg.role === 'assistant' && !msg.streaming ? '本条回复为空，请重试或检查模型配置。' : '')
            }}
            <span v-if="msg.streaming" class="cursor-blink">|</span>
          </div>
        </div>
        <div v-if="store.isGenerating && !hasStreamingMsg" class="loading-dots">
          <span /><span /><span />
        </div>
      </div>

      <div class="chat-input-area">
        <div class="chat-composer">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="3"
            placeholder="输入消息，Ctrl+Enter 发送..."
            @keydown.ctrl.enter="sendMessage"
          />
          <div class="input-actions">
            <el-upload :show-file-list="false" accept="image/*" :auto-upload="false" @change="onImageUpload">
              <el-button size="small" :icon="Picture">图片分析</el-button>
            </el-upload>
            <el-button size="small" :icon="Camera" :loading="capturing" @click="captureScreen">截图分析</el-button>
            <el-button v-if="store.isGenerating" type="danger" size="small" @click="stopGeneration">停止</el-button>
            <el-button type="primary" size="small" :disabled="!inputText.trim() || store.isGenerating" @click="sendMessage">
              发送
            </el-button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { h, ref, computed, nextTick, watch, onMounted } from 'vue'
import { Camera, Delete, Download, Picture, Plus, Setting } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAppStore } from '@/store/app'
import { useRouter, useRoute } from 'vue-router'
import * as api from '@/api'
import type { ConversationItem, PromptTemplate } from '@/types'

const store = useAppStore()
const router = useRouter()
const route = useRoute()

const inputText = ref('')
const messagesRef = ref<HTMLElement | null>(null)
const quickTemplates = ref<PromptTemplate[]>([])
const conversations = ref<ConversationItem[]>([])
const initialized = ref(false)
let abortController: AbortController | null = null
let conversationLoadToken = 0

const hasStreamingMsg = computed(() => store.messages.some(m => m.streaming))
const activeConversation = computed(() =>
  conversations.value.find((conversation) => conversation.id === store.conversationId),
)
const currentConversationTitle = computed(() => activeConversation.value?.title || '新对话')
const currentConversationSource = computed(() => activeConversation.value?.source)

onMounted(async () => {
  try {
    await store.refreshApiConfigs()
    const [builtin, quickIds] = await Promise.all([
      api.getBuiltinTemplates(),
      api.getQuickAccessTemplates(),
    ])
    quickTemplates.value = builtin.filter((t: PromptTemplate) => quickIds.includes(t.id))
    await refreshConversations()
    const routeConversationId = route.params.conversationId
    if (typeof routeConversationId === 'string') {
      await loadConversation(routeConversationId)
    } else {
      const active = await api.getActiveConversation()
      await router.replace({ name: 'chat', params: { conversationId: active.id } })
      await loadConversation(active.id)
    }
    initialized.value = true
  } catch (error) {
    console.error('初始化对话页失败:', error)
    ElMessage.error('加载对话失败，请稍后重试')
  }
})

watch(
  () => route.params.conversationId,
  async (conversationId) => {
    if (!initialized.value) return
    if (typeof conversationId === 'string') {
      if (conversationId !== store.conversationId) await loadConversation(conversationId)
      return
    }
    try {
      const active = await api.getActiveConversation()
      await router.replace({ name: 'chat', params: { conversationId: active.id } })
    } catch (error) {
      console.error('恢复最近对话失败:', error)
      ElMessage.error('加载最近对话失败')
    }
  },
)

async function refreshConversations() {
  conversations.value = await api.listUserConversations()
}

async function loadConversation(conversationId: string) {
  if (store.isGenerating) {
    ElMessage.warning('回复生成中，请先停止后再切换对话')
    await router.replace({ name: 'chat', params: { conversationId: store.conversationId || undefined } })
    return
  }
  const requestToken = ++conversationLoadToken
  try {
    const [items, messages] = await Promise.all([
      api.listUserConversations(),
      api.getConversationMessages(conversationId),
    ])
    if (requestToken !== conversationLoadToken) return
    conversations.value = items
    store.conversationId = conversationId
    store.messages = messages.map((message) => ({
      role: message.role as 'user' | 'assistant' | 'system',
      content: message.content,
      model: message.model ?? undefined,
    }))
    inputText.value = ''
    scrollToBottom()
  } catch (error) {
    if (requestToken !== conversationLoadToken) return
    console.error('加载历史对话失败:', error)
    ElMessage.error('无法加载该对话')
    try {
      const active = await api.getActiveConversation()
      if (active.id !== conversationId) {
        await router.replace({ name: 'chat', params: { conversationId: active.id } })
        await loadConversation(active.id)
      }
    } catch (fallbackError) {
      console.error('恢复最近对话失败:', fallbackError)
    }
  }
}

async function startNewConversation() {
  if (store.isGenerating) return
  try {
    const conversation = await api.createConversation()
    await refreshConversations()
    store.conversationId = conversation.id
    store.clearMessages()
    inputText.value = ''
    await router.push({ name: 'chat', params: { conversationId: conversation.id } })
  } catch (error) {
    console.error('创建对话失败:', error)
    ElMessage.error('新建对话失败，请稍后重试')
  }
}

async function openConversation(conversationId: string) {
  if (conversationId === store.conversationId) return
  await router.push({ name: 'chat', params: { conversationId } })
}

async function deleteConversationEntry(conversation: ConversationItem) {
  if (store.isGenerating) {
    ElMessage.warning('回复生成中，请先停止后再删除对话')
    return
  }
  try {
    await ElMessageBox.confirm(`确定删除“${conversation.title || '新对话'}”及其全部消息吗？`, '删除对话', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await api.deleteConversation(conversation.id)
    await refreshConversations()
    if (conversation.id === store.conversationId) {
      store.clearMessages()
      store.conversationId = null
      const next = conversations.value[0]
      if (next) await router.replace({ name: 'chat', params: { conversationId: next.id } })
      else await startNewConversation()
    }
    ElMessage.success('对话已删除')
  } catch (error) {
    console.error('删除对话失败:', error)
    ElMessage.error('删除对话失败，请稍后重试')
  }
}

async function onConfigChange(id: string) {
  await api.activateConfig(id)
  store.activeConfigId = id
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  })
}

watch(() => store.messages.length, scrollToBottom)

function applyTemplate(tpl: PromptTemplate) {
  const text = inputText.value.trim()
  inputText.value = tpl.prompt.replace('{{text}}', text || '（请在此输入内容）')
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || store.isGenerating) return
  if (!store.conversationId) {
    ElMessage.warning('对话尚未准备好，请稍后重试')
    return
  }
  if (!store.activeConfigId) {
    ElMessage.warning('请先在设置中添加并选择 API 配置')
    return
  }

  store.addMessage({ role: 'user', content: text })
  inputText.value = ''
  store.isGenerating = true

  store.addMessage({ role: 'assistant', content: '', streaming: true })
  const assistantIdx = store.messages.length - 1
  let fullContent = ''

  abortController = api.streamChat(
    store.messages.filter(m => !m.streaming),
    store.activeConfigId,
    store.conversationId,
    (chunk) => {
      fullContent += chunk
      store.messages[assistantIdx].content = fullContent
      scrollToBottom()
    },
    (error) => {
      store.messages[assistantIdx].content = error
      store.messages[assistantIdx].streaming = false
      store.isGenerating = false
    },
    (model) => {
      if (!fullContent.trim()) {
        fullContent = '模型没有返回可显示的回答，请检查模型输出额度或更换模型后重试。'
        store.messages[assistantIdx].content = fullContent
      }
      store.messages[assistantIdx].streaming = false
      if (model) store.messages[assistantIdx].model = model
      store.isGenerating = false
      scrollToBottom()
      void refreshConversations().catch((error) => {
        console.error('刷新对话历史失败:', error)
      })
    },
    async (confirmation) => {
      const args = JSON.stringify(confirmation.arguments, null, 2)
      let approve = false
      try {
        await ElMessageBox.confirm(
          h('div', [
            h('p', `服务器：${confirmation.server_name}`),
            h('p', `工具：${confirmation.tool_name}`),
            h('p', '该操作可能修改数据、访问外部系统或产生其他副作用；请核对参数，确认后才会执行。'),
            confirmation.description ? h('p', confirmation.description) : null,
            h('p', '将提交的参数：'),
            h('pre', {
              style: 'max-height: 220px; overflow: auto; padding: 10px; background: var(--el-fill-color-light); white-space: pre-wrap; overflow-wrap: anywhere;',
            }, args),
            h('p', `该请求将在 ${Math.ceil(confirmation.expires_in_seconds / 60)} 分钟后失效。只确认你理解且信任的操作。`),
          ]),
          'MCP 操作需要人工确认',
          {
            confirmButtonText: '确认并执行',
            cancelButtonText: '拒绝',
            distinguishCancelAndClose: true,
            closeOnClickModal: false,
            closeOnPressEscape: false,
            type: 'warning',
          },
        )
        approve = true
      } catch {
        approve = false
      }
      try {
        await api.decideMcpToolApproval(confirmation.approval_id, approve)
      } catch (error: unknown) {
        const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        throw new Error(detail || '确认结果未能送达服务器；工具不会执行')
      }
      if (!approve) ElMessage.info('已拒绝此次工具调用')
    },
    (reasoning) => {
      // 推理模型的思考内容单独展示，避免思考阶段界面看起来“没有回复”
      const target = store.messages[assistantIdx]
      target.reasoning = (target.reasoning || '') + reasoning
      scrollToBottom()
    },
  )
}

function stopGeneration() {
  abortController?.abort()
  store.isGenerating = false
  const last = store.messages[store.messages.length - 1]
  if (last?.streaming) last.streaming = false
}

function editMessage(idx: number) {
  const msg = store.messages[idx]
  inputText.value = msg.content
  store.messages.splice(idx, store.messages.length - idx)
}

async function saveChat() {
  if (store.messages.length === 0) {
    ElMessage.warning('没有对话可保存')
    return
  }
  const result = await api.saveConversation(
    store.messages.filter(m => !m.streaming),
    activeConversation.value?.title,
  )
  const blob = new Blob([result.markdown], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `AI对话_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.md`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('对话已保存')
}

function onImageUpload(uploadFile: { raw?: File }) {
  const file = uploadFile.raw
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    const base64 = reader.result as string
    analyzeImage(base64)
  }
  reader.readAsDataURL(file)
}

function analyzeImage(base64: string) {
  if (!store.activeConfigId) {
    ElMessage.warning('请先选择 API 配置')
    return
  }
  store.addMessage({ role: 'user', content: '📸 [图片分析]' })
  store.addMessage({ role: 'assistant', content: '', streaming: true })
  const idx = store.messages.length - 1
  let full = ''
  store.isGenerating = true

  abortController = api.streamVision(
    base64, store.activeConfigId, undefined,
    (chunk) => { full += chunk; store.messages[idx].content = full; scrollToBottom() },
    (error) => { store.messages[idx].content = error; store.messages[idx].streaming = false; store.isGenerating = false },
    () => { store.messages[idx].streaming = false; store.isGenerating = false },
  )
}

const capturing = ref(false)

async function captureScreen() {
  if (capturing.value || store.isGenerating) return
  if (!navigator.mediaDevices?.getDisplayMedia) {
    ElMessage.warning('当前浏览器不支持屏幕截图')
    return
  }
  capturing.value = true
  let stream: MediaStream | null = null
  try {
    // 自动隐藏对话窗口后截图，确保截图画面干净
    const chatPage = document.querySelector('.chat-page')
    chatPage?.classList.add('capture-hidden')
    await new Promise((r) => setTimeout(r, 500))

    stream = await navigator.mediaDevices.getDisplayMedia({ video: { frameRate: 30 } })
    const track = stream.getVideoTracks()[0]
    const video = document.createElement('video')
    video.srcObject = new MediaStream([track])
    await video.play()
    await new Promise((r) => requestAnimationFrame(r))

    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    canvas.getContext('2d')?.drawImage(video, 0, 0)
    const base64 = canvas.toDataURL('image/png')

    track.stop()
    video.pause()
    chatPage?.classList.remove('capture-hidden')
    analyzeImage(base64)
  } catch (e) {
    document.querySelector('.chat-page')?.classList.remove('capture-hidden')
    const err = e as Error
    if (err.name !== 'NotAllowedError') {
      ElMessage.error('截图失败：' + (err.message || '未知错误'))
    }
  } finally {
    stream?.getTracks().forEach((t) => t.stop())
    capturing.value = false
  }
}
</script>

<style scoped>
.chat-page {
  display: flex;
  width: 100%;
  height: 100vh;
  min-height: 560px;
  color: var(--theme-text);
  background: var(--theme-chat-bg);
}

.conversation-sidebar {
  width: 280px;
  flex: 0 0 280px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 12px;
  background: var(--theme-bg);
  border-right: 1px solid var(--theme-border);
}

.sidebar-heading {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 0 4px 8px;
}

.sidebar-heading h1 {
  font-size: 19px;
  font-weight: 650;
}

.back-button {
  align-self: flex-start;
  padding-left: 0;
}

.new-chat-button {
  width: 100%;
}

.conversation-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.conversation-entry {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  margin-bottom: 4px;
  border: 0;
  border-radius: 8px;
  color: inherit;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.conversation-entry:hover,
.conversation-entry.active {
  background: var(--el-fill-color-light);
}

.conversation-entry-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}

.conversation-delete {
  flex: none;
  padding: 4px;
  color: var(--el-text-color-secondary);
  opacity: 0;
}

.conversation-entry:hover .conversation-delete,
.conversation-delete:focus {
  opacity: 1;
}

.conversation-delete:hover {
  color: var(--el-color-danger);
}

.history-empty {
  padding: 18px 8px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  text-align: center;
}

.settings-link {
  justify-content: flex-start;
  border-top: 1px solid var(--theme-border);
  padding-top: 12px;
}

.chat-workspace {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 16px clamp(16px, 4vw, 56px) 20px;
}

.chat-page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--theme-border);
}

.chat-page-header > div:first-child {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.chat-page-header strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-label {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  white-space: nowrap;
}

.chat-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: none;
}

.chat-toolbar .el-select {
  width: 200px;
}

.quick-templates {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: var(--emotion-msg-bg, var(--theme-chat-bg));
  border-radius: 12px;
  min-height: 0;
  margin: 12px 0;
  font-size: var(--chat-font-size, 14px);
  transition: background 0.8s ease;
}

.welcome {
  text-align: center;
  color: #909399;
  padding: 40px 20px;
  line-height: 2;
}

.message {
  margin-bottom: 12px;
  display: flex;
}

.message.user { justify-content: flex-end; }
.message.assistant { justify-content: flex-start; }

.message-content {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.message.user .message-content {
  background: var(--theme-primary);
  color: white;
  cursor: pointer;
}

.message.assistant .message-content {
  background: var(--theme-bg);
  color: var(--theme-text);
  border: 1px solid var(--theme-border);
}

.model-tag {
  display: block;
  font-size: 11px;
  opacity: 0.6;
  margin-bottom: 4px;
}

.reasoning-block {
  display: block;
  margin-bottom: 8px;
  padding: 6px 10px;
  border-left: 2px solid var(--theme-border);
  border-radius: 4px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.5;
  max-height: 180px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

.cursor-blink { animation: blink-cursor 0.8s infinite; }
@keyframes blink-cursor { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

.loading-dots {
  display: flex;
  gap: 4px;
  padding: 8px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: var(--theme-primary);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.chat-input-area { flex: none; }
.chat-composer {
  max-width: 900px;
  margin: 0 auto;
  padding: 12px;
  background: var(--theme-bg);
  border: 1px solid var(--theme-border);
  border-radius: 12px;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.06);
}
.input-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px; }

.capture-hidden {
  visibility: hidden;
}

@media (max-width: 760px) {
  .conversation-sidebar {
    width: 210px;
    flex-basis: 210px;
    align-items: center;
    padding: 12px 6px;
  }

  .sidebar-heading h1,
  .new-chat-button :deep(span),
  .settings-link :deep(span) {
    display: none;
  }

  .new-chat-button,
  .settings-link {
    width: 100%;
  }

  .conversation-entry {
    justify-content: flex-start;
    padding: 10px;
  }

  .conversation-entry-title {
    display: block;
  }

  .conversation-delete {
    display: none;
  }

  .chat-workspace {
    padding: 12px;
  }

  .chat-page-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .chat-toolbar,
  .chat-toolbar .el-select {
    width: 100%;
  }

  .input-actions {
    flex-wrap: wrap;
  }
}
</style>

<!-- 心情主题联动样式需要非 scoped 全局样式，以便应用到整页聊天容器。 -->
<style>
/* 强调色（--theme-primary 影响用户气泡/加载点，--el-color-primary 影响发送按钮）
   与消息区氛围背景（--emotion-msg-bg）、抽屉头部淡色底（--emotion-header） */
.chat-page.emotion-sunshine {
  --theme-primary: #f59e0b;
  --el-color-primary: #f59e0b;
  --emotion-msg-bg: linear-gradient(170deg, rgba(245, 200, 80, 0.30), rgba(255, 248, 225, 0.5) 60%, var(--theme-chat-bg));
  --emotion-header: rgba(245, 200, 80, 0.18);
}
.chat-page.emotion-healing {
  --theme-primary: #8b5cf6;
  --el-color-primary: #8b5cf6;
  --emotion-msg-bg: linear-gradient(170deg, rgba(197, 168, 229, 0.32), rgba(243, 238, 250, 0.5) 60%, var(--theme-chat-bg));
  --emotion-header: rgba(155, 127, 199, 0.18);
}
.chat-page.emotion-ocean {
  --theme-primary: #3b82f6;
  --el-color-primary: #3b82f6;
  --emotion-msg-bg: linear-gradient(170deg, rgba(165, 198, 225, 0.34), rgba(232, 240, 248, 0.5) 60%, var(--theme-chat-bg));
  --emotion-header: rgba(74, 156, 199, 0.18);
}
.chat-page.emotion-comfort {
  --theme-primary: #64748b;
  --el-color-primary: #64748b;
  --emotion-msg-bg: linear-gradient(170deg, rgba(133, 160, 190, 0.34), rgba(236, 240, 245, 0.5) 60%, var(--theme-chat-bg));
  --emotion-header: rgba(138, 165, 200, 0.20);
}
.chat-page.emotion-release {
  --theme-primary: #ef4444;
  --el-color-primary: #ef4444;
  --emotion-msg-bg: linear-gradient(170deg, rgba(238, 145, 135, 0.30), rgba(252, 238, 236, 0.5) 60%, var(--theme-chat-bg));
  --emotion-header: rgba(201, 130, 104, 0.18);
}
.chat-page.emotion-rest {
  --theme-primary: #78716c;
  --el-color-primary: #78716c;
  --emotion-msg-bg: linear-gradient(170deg, rgba(226, 220, 200, 0.42), rgba(247, 245, 238, 0.55) 60%, var(--theme-chat-bg));
  --emotion-header: rgba(168, 162, 158, 0.20);
}

/* 深色模式：改用更暗的半透明氛围色，避免刺眼 */
body.dark-mode .chat-page.emotion-sunshine {
  --emotion-msg-bg: linear-gradient(170deg, rgba(245, 200, 80, 0.12), rgba(0, 0, 0, 0) 55%, var(--theme-chat-bg));
  --emotion-header: rgba(245, 200, 80, 0.10);
}
body.dark-mode .chat-page.emotion-healing {
  --emotion-msg-bg: linear-gradient(170deg, rgba(155, 127, 199, 0.16), rgba(0, 0, 0, 0) 55%, var(--theme-chat-bg));
  --emotion-header: rgba(155, 127, 199, 0.12);
}
body.dark-mode .chat-page.emotion-ocean {
  --emotion-msg-bg: linear-gradient(170deg, rgba(74, 156, 199, 0.16), rgba(0, 0, 0, 0) 55%, var(--theme-chat-bg));
  --emotion-header: rgba(74, 156, 199, 0.12);
}
body.dark-mode .chat-page.emotion-comfort {
  --emotion-msg-bg: linear-gradient(170deg, rgba(138, 165, 200, 0.16), rgba(0, 0, 0, 0) 55%, var(--theme-chat-bg));
  --emotion-header: rgba(138, 165, 200, 0.12);
}
body.dark-mode .chat-page.emotion-release {
  --emotion-msg-bg: linear-gradient(170deg, rgba(201, 130, 104, 0.16), rgba(0, 0, 0, 0) 55%, var(--theme-chat-bg));
  --emotion-header: rgba(201, 130, 104, 0.12);
}
body.dark-mode .chat-page.emotion-rest {
  --emotion-msg-bg: linear-gradient(170deg, rgba(168, 162, 158, 0.16), rgba(0, 0, 0, 0) 55%, var(--theme-chat-bg));
  --emotion-header: rgba(168, 162, 158, 0.12);
}
</style>
