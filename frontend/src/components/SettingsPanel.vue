<template>
  <div class="settings-page">
    <header class="settings-page-header">
      <el-button text @click="router.push({ name: 'soul' })">← 心灵之旅</el-button>
      <h1>设置</h1>
      <el-button text @click="router.push({ name: 'chat' })">AI 智能对话 →</el-button>
    </header>
    <main class="settings-page-content">
    <el-alert
      v-if="providerLoadError || configLoadError"
      class="settings-load-alert"
      type="error"
      :closable="false"
      show-icon
      title="部分设置加载失败"
    >
      <template #default>
        <p v-if="providerLoadError">服务商列表：{{ providerLoadError }}</p>
        <p v-if="configLoadError">API 配置：{{ configLoadError }}</p>
        <el-button size="small" @click="loadSettingsPage">重试</el-button>
      </template>
    </el-alert>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="API 配置" name="api">
        <div class="tab-header">
          <el-button type="primary" size="small" @click="showAddConfig">添加配置</el-button>
        </div>
        <div v-if="store.apiConfigs.length === 0" class="empty-hint">暂无 API 配置，请添加</div>
        <el-card v-for="cfg in store.apiConfigs" :key="cfg.id" class="config-card" shadow="hover">
          <div class="config-header">
            <span class="config-name">{{ cfg.name }}</span>
            <el-tag size="small" :type="cfg.id === store.activeConfigId ? 'success' : 'info'">
              {{ cfg.id === store.activeConfigId ? '当前' : cfg.provider }}
            </el-tag>
          </div>
          <div class="config-info">{{ cfg.selectedModel }}</div>
          <div class="config-actions">
            <el-button size="small" @click="activateConfig(cfg.id)" :disabled="cfg.id === store.activeConfigId">启用</el-button>
            <el-button size="small" @click="testConfig(cfg)">测试</el-button>
            <el-button size="small" @click="editConfig(cfg)">编辑</el-button>
            <el-button size="small" type="danger" @click="removeConfig(cfg.id)">删除</el-button>
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="外观设置" name="appearance">
        <el-form label-width="100px">
          <el-form-item label="宠物大小">
            <el-radio-group v-model="store.petSettings.petSize" @change="savePet">
              <el-radio value="small">小</el-radio>
              <el-radio value="medium">中</el-radio>
              <el-radio value="large">大</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="宠物图片">
            <el-upload :show-file-list="false" accept="image/*" :auto-upload="false" @change="onPetImageChange">
              <el-button size="small">上传图片</el-button>
            </el-upload>
            <el-button size="small" style="margin-left:8px" @click="resetPetImage">恢复默认</el-button>
          </el-form-item>
          <el-form-item label="始终置顶">
            <el-switch v-model="store.petSettings.alwaysOnTop" @change="savePet" />
          </el-form-item>
          <el-form-item label="点击穿透">
            <el-switch v-model="store.petSettings.clickThrough" @change="savePet" />
          </el-form-item>
          <el-form-item label="深色模式">
            <el-switch v-model="store.themeSettings.darkMode" @change="saveTheme" />
          </el-form-item>
          <el-form-item label="对话主题">
            <el-radio-group v-model="store.themeSettings.chatTheme" @change="saveTheme">
              <el-radio value="shiba">柴犬橙</el-radio>
              <el-radio value="blue">蓝色</el-radio>
              <el-radio value="purple">紫色</el-radio>
              <el-radio value="green">绿色</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="字体大小">
            <el-radio-group v-model="store.themeSettings.chatFontSize" @change="saveTheme">
              <el-radio value="small">小</el-radio>
              <el-radio value="medium">中</el-radio>
              <el-radio value="large">大</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="效果预览">
            <div class="theme-preview">
              <div class="preview-row user">
                <div class="preview-bubble">你好，今天心情不太好...</div>
              </div>
              <div class="preview-row">
                <div class="preview-bubble assistant">别担心，我会一直陪着你 🐾</div>
              </div>
            </div>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="通用设置" name="general">
        <el-form label-width="120px">
          <el-form-item label="启动打开对话">
            <el-switch v-model="store.petSettings.autoOpenChat" @change="savePet" />
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="上下文记忆" name="memory">
        <p class="memory-intro">
          对话请求按任务上下文、会话摘要、用户偏好、相关工具结果和全局知识分层组装。摘要与工具结果自动生成，偏好可自行维护。
        </p>
        <el-alert
          v-if="contextState && !contextState.is_admin"
          title="全局知识和保留期限由部署管理员维护"
          type="info"
          :closable="false"
          show-icon
        />
        <div class="tab-header memory-toolbar">
          <el-button size="small" type="primary" @click="openMemoryEditor()">添加长期偏好</el-button>
          <el-button v-if="contextState?.is_admin" size="small" @click="openMemoryEditor(undefined, 'global_knowledge')">
            添加全局知识
          </el-button>
          <el-button size="small" :loading="memoryLoading" @click="cleanupMemories">清理过期记忆</el-button>
          <el-button size="small" type="danger" @click="clearMemories">清除我的记忆</el-button>
        </div>
        <div v-if="contextState && contextState.memories.length === 0" class="empty-hint">暂无记忆；偏好、会话摘要和工具结果会在此管理。</div>
        <el-card v-for="memory in contextState?.memories" :key="memory.id" class="config-card" shadow="hover">
          <div class="config-header">
            <span class="config-name">{{ memory.title }}</span>
            <el-tag size="small" :type="memory.is_global ? 'warning' : 'info'">{{ memoryKindLabel(memory.kind) }}</el-tag>
          </div>
          <div class="memory-content">{{ memory.content }}</div>
          <div class="config-info">
            {{ memory.source === 'automatic' ? '自动摘要' : memory.source === 'mcp' ? 'MCP 工具' : '手动维护' }}
            <span v-if="memory.expires_at"> · 到期 {{ new Date(memory.expires_at).toLocaleDateString() }}</span>
            <span v-else> · 永不过期</span>
          </div>
          <div class="config-actions">
            <el-button
              v-if="memory.kind === 'preference' || (memory.kind === 'global_knowledge' && contextState?.is_admin)"
              size="small"
              @click="openMemoryEditor(memory)"
            >编辑</el-button>
            <el-button size="small" type="danger" @click="deleteMemory(memory)">删除</el-button>
          </div>
        </el-card>

        <template v-if="contextState?.is_admin">
          <el-divider content-position="left">自动清理保留期限</el-divider>
          <el-form label-width="120px">
            <el-form-item v-for="item in retentionKinds" :key="item.value" :label="item.label">
              <el-input-number
                v-model="retentionDraft[item.value]"
                :min="1"
                :max="3650"
                :disabled="retentionDraft[item.value] === null"
              />
              <el-checkbox
                :model-value="retentionDraft[item.value] === null"
                @change="setNoExpiry(item.value, $event)"
              >永不过期</el-checkbox>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" size="small" :loading="retentionSaving" @click="saveRetention">保存保留期限</el-button>
              <span class="memory-hint">清理在记忆读取或手动清理时执行；1–3650 天，或选择永不过期。</span>
            </el-form-item>
          </el-form>
        </template>
      </el-tab-pane>

      <el-tab-pane label="MCP 工具" name="mcp">
        <el-alert
          v-if="mcpLoadError"
          class="settings-load-alert"
          type="error"
          :closable="false"
          show-icon
          title="MCP 设置加载失败"
        >
          <template #default>
            <p>{{ mcpLoadError }}</p>
            <el-button size="small" :loading="mcpLoading" @click="loadMcp">重试</el-button>
          </template>
        </el-alert>
        <el-form label-width="120px">
          <el-form-item label="MCP 工具调用">
            <el-switch v-model="mcpEnabled" @change="saveMcpEnabled" />
          </el-form-item>
        </el-form>

        <div class="tab-header mcp-header">
          <span class="preset-label">预设：</span>
          <el-button v-for="p in mcpPresets" :key="p.name" size="small" @click="applyMcpPreset(p)">
            {{ p.icon }} {{ p.name }}
          </el-button>
        </div>

        <div v-if="!mcpLoadError && mcpServers.length === 0" class="empty-hint">暂无 MCP 服务器，点击预设快速添加</div>
        <el-card v-for="srv in mcpServers" :key="srv.id" class="config-card" shadow="hover">
          <div class="config-header">
            <span class="config-name">{{ srv.name }}</span>
            <el-tag size="small" :type="srv.connected ? 'success' : srv.enabled ? 'warning' : 'info'">
              {{ srv.connected ? `已连接 · ${srv.toolCount} 个工具` : srv.enabled ? '未连接' : '已禁用' }}
            </el-tag>
          </div>
          <div class="config-info">{{ srv.command }} {{ srv.args.join(' ') }}</div>
          <div v-if="srv.connected && srv.tools.length" class="mcp-tools">
            <div v-for="t in srv.tools" :key="t.name" class="mcp-tool-item">
              <div class="mcp-tool-details">
                <span class="tool-name">{{ t.name }}</span>
                <span class="tool-desc">{{ t.description }}</span>
              </div>
              <el-select
                v-model="t.mode"
                size="small"
                class="mcp-policy-select"
                aria-label="工具执行权限"
                @change="setToolMode(srv.id, t)"
              >
                <el-option label="只读自动执行" value="read_only" />
                <el-option label="每次确认" value="confirm" />
                <el-option label="禁止执行" value="blocked" />
              </el-select>
            </div>
          </div>
          <p v-if="srv.connected && srv.tools.length" class="mcp-policy-hint">
            默认仅明显只读工具可自动执行；未知和有副作用的工具需逐次确认。修改为自动执行表示你信任该工具及其所有参数。
          </p>
          <div class="config-actions">
            <el-switch
              v-model="srv.enabled"
              size="small"
              active-text="启用此服务器"
              @change="toggleServer(srv)"
              style="margin-right: 10px"
            />
            <el-button size="small" :loading="connectingId === srv.id" @click="toggleConnect(srv)">
              {{ srv.connected ? '断开' : '连接' }}
            </el-button>
            <el-button size="small" type="danger" @click="removeServer(srv.id)">删除</el-button>
          </div>
        </el-card>

        <el-dialog v-model="mcpFormVisible" :title="mcpEditingId ? '编辑服务器' : '添加 MCP 服务器'" width="480px">
          <el-form :model="mcpForm" label-width="100px">
            <el-form-item label="名称" required>
              <el-input v-model="mcpForm.name" placeholder="如：文件系统" />
            </el-form-item>
            <el-form-item label="启动命令" required>
              <el-input v-model="mcpForm.command" placeholder="如：npx" />
            </el-form-item>
            <el-form-item label="参数">
              <el-input v-model="mcpForm.argsText" type="textarea" :rows="3" placeholder="每行一个参数，如：&#10;-y&#10;@modelcontextprotocol/server-filesystem" />
            </el-form-item>
            <el-form-item label="环境变量">
              <el-input v-model="mcpForm.envText" type="textarea" :rows="2" placeholder="每行一个，格式 KEY=VALUE（可选）" />
            </el-form-item>
            <el-form-item label="启用此服务器">
              <el-switch v-model="mcpForm.enabled" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="mcpFormVisible = false">取消</el-button>
            <el-button type="primary" @click="saveMcpServer">{{ mcpEditingId ? '保存' : '添加' }}</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>

      <el-tab-pane label="关于" name="about">
        <div class="about-section">
          <h3>🐕 SoulPilot · 心灵领航员</h3>
          <p>版本: 3.0.0 (Web 版)</p>
          <p>技术栈: Vue3 + Vite + TypeScript + Element Plus + FastAPI + MySQL</p>
          <p>透明悬浮宠物 · AI 智能对话 · SSE 流式回复</p>
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="configDialogVisible" :title="editingConfig ? '编辑配置' : '添加配置'" width="480px">
      <el-form :model="configForm" label-width="90px">
        <el-form-item label="名称" required>
          <el-input v-model="configForm.name" placeholder="配置名称" />
        </el-form-item>
        <el-form-item label="提供商" required>
          <el-select
            v-model="configForm.provider"
            filterable
            placeholder="请选择提供商"
            @change="onProviderChange"
            style="width:100%"
          >
            <el-option v-for="(tpl, key) in providers" :key="key" :label="tpl.name" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="API URL" required>
          <el-input
            v-model="configForm.apiUrl"
            autocomplete="off"
            placeholder="请输入 API URL"
          />
        </el-form-item>
        <el-form-item label="API Key" required>
          <el-input
            v-model="configForm.apiKey"
            type="password"
            autocomplete="new-password"
            show-password
            :placeholder="editingConfig?.hasApiKey ? '已配置；留空则保留原密钥' : '请输入 API Key'"
          />
        </el-form-item>
        <el-form-item label="模型" required>
          <el-select
            v-model="configForm.selectedModel"
            style="width:100%"
            filterable
            allow-create
            placeholder="请选择模型"
          >
            <el-option
              v-for="m in currentModels"
              :key="m.id"
              :label="m.name"
              :value="m.id"
              :disabled="m.isCustomInput"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="默认配置">
          <el-switch v-model="configForm.isDefault" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="configDialogVisible = false">取消</el-button>
        <el-button @click="testFormConfig">测试连接</el-button>
        <el-button type="primary" @click="saveConfig">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="memoryEditorVisible" :title="editingMemoryId ? '编辑记忆' : '添加记忆'" width="480px">
      <el-form :model="memoryForm" label-width="90px">
        <el-form-item v-if="!editingMemoryId" label="类型">
          <el-select v-model="memoryForm.kind">
            <el-option label="用户长期偏好" value="preference" />
            <el-option v-if="contextState?.is_admin" label="全局知识" value="global_knowledge" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" required>
          <el-input v-model="memoryForm.title" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input v-model="memoryForm.content" type="textarea" :rows="5" maxlength="5000" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="memoryEditorVisible = false">取消</el-button>
        <el-button type="primary" :loading="memorySaving" @click="saveMemory">保存</el-button>
      </template>
    </el-dialog>
    </main>
  </div>
</template>

<script setup lang="ts">
import { h, ref, computed, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAppStore } from '@/store/app'
import { useRouter } from 'vue-router'
import * as api from '@/api'
import type { ApiConfig, ContextMemory, ContextMemoryKind, ContextMemoryState, McpServerInfo, McpToolInfo, ProviderTemplate } from '@/types'

const store = useAppStore()
const router = useRouter()

const activeTab = ref('api')
const providers = ref<Record<string, ProviderTemplate>>({})
const providerLoadError = ref('')
const configLoadError = ref('')
const mcpLoadError = ref('')
const mcpLoading = ref(false)
const configDialogVisible = ref(false)
const editingConfig = ref<ApiConfig | null>(null)
const contextState = ref<ContextMemoryState | null>(null)
const memoryLoading = ref(false)
const memorySaving = ref(false)
const memoryEditorVisible = ref(false)
const editingMemoryId = ref('')
const retentionSaving = ref(false)
const memoryForm = reactive<{ kind: 'preference' | 'global_knowledge'; title: string; content: string }>({
  kind: 'preference',
  title: '',
  content: '',
})
const retentionKinds: { value: ContextMemoryKind; label: string }[] = [
  { value: 'session_summary', label: '会话摘要' },
  { value: 'preference', label: '用户偏好' },
  { value: 'tool_result', label: '工具结果' },
  { value: 'global_knowledge', label: '全局知识' },
]
const retentionDraft = reactive<Record<ContextMemoryKind, number | null>>({
  session_summary: 180,
  preference: null,
  tool_result: 7,
  global_knowledge: null,
})

// ---------- MCP 工具状态 ----------
const mcpEnabled = ref(false)
const mcpServers = ref<McpServerInfo[]>([])
const connectingId = ref('')
const mcpFormVisible = ref(false)
const mcpEditingId = ref('')
const mcpForm = reactive({ name: '', command: '', argsText: '', envText: '', enabled: true })

interface McpPreset {
  name: string
  icon: string
  command: string
  args: string[]
}

// 与原桌面版文档一致的三个预设
const mcpPresets: McpPreset[] = [
  { name: '文件系统', icon: '📁', command: 'npx', args: ['-y', '@modelcontextprotocol/server-filesystem', 'C:/Users/hp/Documents'] },
  { name: '终端命令', icon: '🖥️', command: 'npx', args: ['-y', '@wonderwhy-er/desktop-commander'] },
  { name: '网络请求', icon: '🌐', command: 'uvx', args: ['mcp-server-fetch'] },
]

function parseLines(text: string): string[] {
  return text.split('\n').map((l) => l.trim()).filter(Boolean)
}

function parseEnv(text: string): Record<string, string> {
  const env: Record<string, string> = {}
  for (const line of parseLines(text)) {
    const i = line.indexOf('=')
    if (i > 0) env[line.slice(0, i).trim()] = line.slice(i + 1).trim()
  }
  return env
}

async function loadMcp() {
  mcpLoading.value = true
  mcpLoadError.value = ''
  try {
    const [general, servers] = await Promise.all([
      api.getSetting<Record<string, unknown> | null>('general_settings'),
      api.listMcpServers(),
    ])
    mcpEnabled.value = !!(general && general.mcpEnabled)
    mcpServers.value = servers
  } catch (error: unknown) {
    mcpLoadError.value = getLoadError(error, '无法读取 MCP 配置')
    console.error('加载 MCP 设置失败:', error)
  } finally {
    mcpLoading.value = false
  }
}

async function saveMcpEnabled() {
  const general = (await api.getSetting<Record<string, unknown> | null>('general_settings')) || {}
  await api.updateSetting('general_settings', { ...general, mcpEnabled: mcpEnabled.value })
  ElMessage.success(mcpEnabled.value ? '已开启 MCP 工具调用' : '已关闭 MCP 工具调用')
}

function memoryKindLabel(kind: ContextMemoryKind): string {
  return {
    session_summary: '会话摘要',
    preference: '用户偏好',
    tool_result: '工具结果',
    global_knowledge: '全局知识',
  }[kind]
}

async function loadContextMemories() {
  memoryLoading.value = true
  try {
    contextState.value = await api.getContextMemories()
    Object.assign(retentionDraft, contextState.value.ttl_days)
  } catch (error: unknown) {
    contextState.value = null
    const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '加载上下文记忆失败')
  } finally {
    memoryLoading.value = false
  }
}

function openMemoryEditor(memory?: ContextMemory, defaultKind: 'preference' | 'global_knowledge' = 'preference') {
  editingMemoryId.value = memory?.id ?? ''
  Object.assign(memoryForm, {
    kind: memory ? (memory.kind === 'global_knowledge' ? 'global_knowledge' : 'preference') : defaultKind,
    title: memory?.title ?? '',
    content: memory?.content ?? '',
  })
  memoryEditorVisible.value = true
}

async function saveMemory() {
  if (!memoryForm.title.trim() || !memoryForm.content.trim()) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  memorySaving.value = true
  try {
    if (editingMemoryId.value) {
      await api.updateContextMemory(editingMemoryId.value, {
        title: memoryForm.title.trim(),
        content: memoryForm.content.trim(),
      })
    } else {
      await api.createContextMemory({
        kind: memoryForm.kind,
        title: memoryForm.title.trim(),
        content: memoryForm.content.trim(),
      })
    }
    memoryEditorVisible.value = false
    await loadContextMemories()
    ElMessage.success('记忆已保存')
  } catch (error: unknown) {
    const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '保存记忆失败')
  } finally {
    memorySaving.value = false
  }
}

async function deleteMemory(memory: ContextMemory) {
  try {
    await ElMessageBox.confirm(`确定删除“${memory.title}”吗？`, '删除记忆', { type: 'warning' })
  } catch {
    return
  }
  try {
    await api.deleteContextMemory(memory.id)
    await loadContextMemories()
    ElMessage.success('记忆已删除')
  } catch (error: unknown) {
    const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '删除记忆失败')
  }
}

async function clearMemories() {
  try {
    await ElMessageBox.confirm('这会删除你的长期偏好、会话摘要和工具结果，但不会删除聊天记录或全局知识。', '清除我的记忆', {
      type: 'warning',
      confirmButtonText: '清除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    const result = await api.clearContextMemories()
    await loadContextMemories()
    ElMessage.success(`已清除 ${result.deleted} 条记忆`)
  } catch (error: unknown) {
    const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '清除记忆失败')
  }
}

async function cleanupMemories() {
  try {
    const result = await api.cleanupContextMemories()
    await loadContextMemories()
    ElMessage.success(`过期记忆清理完成，删除 ${result.deleted} 条`)
  } catch (error: unknown) {
    const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '清理过期记忆失败')
  }
}

function setNoExpiry(kind: ContextMemoryKind, checked: unknown) {
  retentionDraft[kind] = checked === true ? null : (contextState.value?.default_ttl_days[kind] ?? 30)
}

async function saveRetention() {
  if (!contextState.value?.is_admin) return
  retentionSaving.value = true
  try {
    const result = await api.updateContextRetention({ ...retentionDraft })
    Object.assign(retentionDraft, result.ttl_days)
    await loadContextMemories()
    ElMessage.success('记忆保留期限已更新')
  } catch (error: unknown) {
    const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '保存保留期限失败')
  } finally {
    retentionSaving.value = false
  }
}

function applyMcpPreset(preset: McpPreset) {
  mcpEditingId.value = ''
  Object.assign(mcpForm, {
    name: preset.name,
    command: preset.command,
    argsText: preset.args.join('\n'),
    envText: '',
    enabled: true,
  })
  mcpFormVisible.value = true
}

async function saveMcpServer() {
  if (!mcpForm.name || !mcpForm.command) {
    ElMessage.warning('请填写名称和启动命令')
    return
  }
  const payload = {
    name: mcpForm.name,
    command: mcpForm.command,
    args: parseLines(mcpForm.argsText),
    env: parseEnv(mcpForm.envText),
    enabled: mcpForm.enabled,
  }
  await api.createMcpServer(payload)
  mcpFormVisible.value = false
  await loadMcp()
  ElMessage.success('MCP 服务器已添加')
}

async function toggleServer(srv: McpServerInfo) {
  await api.updateMcpServer(srv.id, { enabled: srv.enabled })
  // 禁用即断开连接，避免继续参与工具调用
  if (!srv.enabled && srv.connected) {
    await api.disconnectMcpServer(srv.id)
  }
  await loadMcp()
}

async function setToolMode(serverId: string, tool: McpToolInfo) {
  try {
    await api.updateMcpToolPolicy(serverId, tool.name, tool.mode)
    ElMessage.success(`已更新「${tool.name}」执行策略`)
  } catch (error: unknown) {
    const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '更新工具权限失败')
    await loadMcp()
  }
}

async function toggleConnect(srv: McpServerInfo) {
  connectingId.value = srv.id
  try {
    if (srv.connected) {
      await api.disconnectMcpServer(srv.id)
      ElMessage.success('已断开连接')
    } else {
      const result = await api.connectMcpServer(srv.id)
      ElMessage.success(`连接成功，发现 ${result.toolCount} 个工具`)
    }
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(detail || '连接失败，请检查命令与参数')
  } finally {
    connectingId.value = ''
    await loadMcp()
  }
}

async function removeServer(id: string) {
  await ElMessageBox.confirm('确定删除此 MCP 服务器？', '确认')
  await api.deleteMcpServer(id)
  await loadMcp()
  ElMessage.success('已删除')
}

const configForm = reactive({
  name: '',
  provider: '',
  apiUrl: '',
  apiKey: '',
  selectedModel: '',
  isDefault: false,
})

const currentModels = computed(() => {
  const tpl = providers.value[configForm.provider]
  return tpl?.models || []
})

async function loadSettingsPage() {
  providerLoadError.value = ''
  configLoadError.value = ''
  const [providersResult, configsResult] = await Promise.allSettled([
    api.getProviders(),
    store.refreshApiConfigs(),
  ])

  if (providersResult.status === 'fulfilled') {
    providers.value = providersResult.value
  } else {
    providerLoadError.value = getLoadError(providersResult.reason, '无法读取服务商列表')
    console.error('加载服务商列表失败:', providersResult.reason)
  }

  if (configsResult.status === 'rejected') {
    configLoadError.value = getLoadError(configsResult.reason, '无法读取 API 配置')
    console.error('加载 API 配置失败:', configsResult.reason)
  }

  await Promise.all([loadMcp(), loadContextMemories()])
}

onMounted(() => { void loadSettingsPage() })

function getLoadError(error: unknown, fallback: string): string {
  const responseDetail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (typeof responseDetail === 'string') return responseDetail
  if (error instanceof Error && error.message) return error.message
  return fallback
}

function showAddConfig() {
  editingConfig.value = null
  // 添加配置时表单全部置空，由用户自行下拉选择提供商；选择后再自动填充对应 API URL 与模型
  Object.assign(configForm, {
    name: '',
    provider: '',
    apiUrl: '',
    apiKey: '',
    selectedModel: '',
    isDefault: false,
  })
  configDialogVisible.value = true
}

function editConfig(cfg: ApiConfig) {
  editingConfig.value = cfg
  Object.assign(configForm, {
    name: cfg.name,
    provider: cfg.provider,
    apiUrl: cfg.apiUrl,
    apiKey: '',
    selectedModel: cfg.selectedModel,
    isDefault: cfg.isDefault,
  })
  configDialogVisible.value = true
}

function onProviderChange(provider: string) {
  const tpl = providers.value[provider]
  if (tpl) {
    // API URL 和密钥由用户明确提供；只根据提供商预选推荐模型。
    configForm.selectedModel = tpl.defaultModel
  } else {
    configForm.selectedModel = ''
  }
}

async function saveConfig() {
  if (!configForm.provider) {
    ElMessage.warning('请选择提供商')
    return
  }
  if (
    !configForm.name
    || !configForm.apiUrl
    || (!configForm.apiKey && !editingConfig.value?.hasApiKey)
    || !configForm.selectedModel
  ) {
    ElMessage.warning('请填写完整配置信息')
    return
  }
  if (editingConfig.value) {
    await api.updateApiConfig(editingConfig.value.id, {
      ...configForm,
      apiKey: configForm.apiKey || undefined,
    })
  } else {
    await api.createApiConfig({ ...configForm, enabled: true })
  }
  await store.refreshApiConfigs()
  configDialogVisible.value = false
  ElMessage.success('配置已保存')
}

async function testFormConfig() {
  if (editingConfig.value && !configForm.apiKey && editingConfig.value.hasApiKey) {
    const result = await api.testSavedApiConfig(editingConfig.value.id)
    if (result.success) ElMessage.success(result.message)
    else ElMessage.error(result.error)
    return
  }
  if (!configForm.provider || !configForm.apiUrl || !configForm.apiKey || !configForm.selectedModel) {
    ElMessage.warning('请先选择提供商并填写完整配置信息')
    return
  }
  const result = await api.testApiConfig(configForm.provider, configForm.apiUrl, configForm.apiKey, configForm.selectedModel)
  if (result.success) ElMessage.success(result.message)
  else ElMessage.error(result.error)
}

async function testConfig(cfg: ApiConfig) {
  const result = await api.testSavedApiConfig(cfg.id)
  if (result.success) ElMessage.success(result.message)
  else ElMessage.error(result.error)
}

async function activateConfig(id: string) {
  await api.activateConfig(id)
  store.activeConfigId = id
  ElMessage.success('已切换配置')
}

async function removeConfig(id: string) {
  await ElMessageBox.confirm('确定删除此配置？', '确认')
  await api.deleteApiConfig(id)
  await store.refreshApiConfigs()
  ElMessage.success('已删除')
}

function savePet() { store.savePetSettings() }
function saveTheme() { store.saveThemeSettings() }

function onPetImageChange(uploadFile: { raw?: File }) {
  const file = uploadFile.raw
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    store.petSettings.petImageUrl = reader.result as string
    store.savePetSettings()
    ElMessage.success('宠物图片上传成功')
  }
  reader.onerror = () => {
    ElMessage.error('图片读取失败，请重试')
  }
  reader.readAsDataURL(file)
}

function resetPetImage() {
  store.petSettings.petImageUrl = null
  store.savePetSettings()
  ElMessage.success('已恢复默认宠物图片')
}
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
  padding: 20px;
  background: var(--theme-chat-bg);
  color: var(--theme-text);
}

.settings-page-header {
  max-width: 1080px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0 16px;
  border-bottom: 1px solid var(--theme-border);
}

.settings-page-header h1 {
  font-size: 22px;
}

.settings-page-content {
  max-width: 1080px;
  margin: 0 auto;
  padding: 18px 20px;
  background: var(--theme-bg);
  border: 1px solid var(--theme-border);
  border-radius: 14px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.06);
}

.settings-load-alert {
  margin-bottom: 14px;
}

.tab-header { margin-bottom: 12px; }
.empty-hint { color: #909399; text-align: center; padding: 30px; }
.config-card { margin-bottom: 10px; }
.config-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.config-name { font-weight: 600; }
.config-info { font-size: 12px; color: #909399; margin-bottom: 8px; }
.config-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.about-section { padding: 20px; line-height: 2; }
.about-section h3 { margin-bottom: 12px; color: var(--theme-primary); }
.memory-intro { color: #606266; line-height: 1.6; margin: 0 0 12px; }
.memory-toolbar { display: flex; flex-wrap: wrap; gap: 6px; }
.memory-content { white-space: pre-wrap; overflow-wrap: anywhere; line-height: 1.5; margin-bottom: 8px; }
.memory-hint { color: #909399; font-size: 12px; margin-left: 10px; }
.mcp-tool-details { min-width: 0; display: flex; flex-direction: column; }
.mcp-policy-select { width: 150px; flex: 0 0 150px; }
.mcp-policy-hint { margin: 4px 0 10px; color: #909399; font-size: 12px; line-height: 1.5; }

/* MCP 工具页签 */
.mcp-header { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.preset-label { font-size: 13px; color: #909399; }
.mcp-tools {
  margin: 6px 0 8px;
  padding: 8px 10px;
  background: var(--el-fill-color-light);
  border-radius: 6px;
  max-height: 160px;
  overflow-y: auto;
}
.mcp-tool-item { display: flex; align-items: center; justify-content: space-between; gap: 8px; line-height: 1.5; font-size: 12px; }
.mcp-tool-item .tool-name { font-weight: 600; color: var(--el-color-primary); white-space: nowrap; }
.mcp-tool-item .tool-desc { color: #909399; overflow-wrap: anywhere; }

/* 外观设置实时预览：跟随对话主题与字体大小即时变化 */
.theme-preview {
  width: 100%;
  padding: 10px;
  background: var(--theme-chat-bg);
  border-radius: 8px;
  font-size: var(--chat-font-size, 14px);
  transition: background 0.3s;
}
.preview-row { display: flex; margin-bottom: 8px; }
.preview-row.user { justify-content: flex-end; }
.preview-row:last-child { margin-bottom: 0; }
.preview-bubble {
  max-width: 80%;
  padding: 8px 12px;
  border-radius: 10px;
  line-height: 1.5;
}
.preview-row.user .preview-bubble {
  background: var(--theme-primary);
  color: #fff;
  transition: background 0.3s;
}
.preview-bubble.assistant {
  background: var(--theme-bg);
  color: var(--theme-text);
  border: 1px solid var(--theme-border);
  transition: background 0.3s, color 0.3s;
}

@media (max-width: 600px) {
  .settings-page {
    padding: 12px;
  }

  .settings-page-header {
    flex-wrap: wrap;
  }

  .settings-page-header h1 {
    order: -1;
    width: 100%;
  }

  .settings-page-content {
    padding: 12px;
  }
}
</style>
