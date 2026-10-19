<template>
  <div class="app-container" :class="`theme-${emotionTheme}`">
    <!-- 情绪氛围光斑层：随所选表情平滑变色，营造温馨包裹感 -->
    <div class="ambient-bg" aria-hidden="true">
      <span class="ambient-blob blob-a"></span>
      <span class="ambient-blob blob-b"></span>
      <span class="ambient-blob blob-c"></span>
    </div>
    <div class="app-content">
      <header class="app-header">
        <div class="theme-toggle">
          <button @click="toggleTheme" class="theme-toggle-btn" :class="{ dark: isDarkMode }">
            <div class="toggle-icon">
              <span v-if="isDarkMode" class="moon-icon">🌙</span>
              <span v-else class="sun-icon">☀️</span>
            </div>
            <span class="toggle-text">{{ isDarkMode ? 'Founder Mode' : 'VC mode' }}</span>
          </button>
          <button class="logout-btn" @click="onLogout" title="退出登录">退出</button>
        </div>
        <div class="logo">
          <div class="logo-center">
            <img src="@/assets/logo.svg" alt="心灵之旅" />
            <h1 class="app-title">心灵之旅</h1>
          </div>
        </div>
      </header>

      <OnboardingGuide @show-all-tickets="showAllTickets" />

      <main>
        <div class="integrated-container">
          <div class="glass-card input-section">
            <h2>今天，你的心情如何?</h2>
            <p class="subtitle">分享你的感受，AI将为你提供个性化的心理健康建议</p>

            <div class="emotion-selector">
              <div
                v-for="emotion in emotions"
                :key="emotion.name"
                :class="['emotion-item', { active: selectedEmotion === emotion.name }]"
                @click="selectEmotion(emotion.name)"
              >
                <div class="emotion-icon">{{ emotion.icon }}</div>
                <div class="emotion-name">{{ emotion.name }}</div>
              </div>
            </div>

            <div class="input-area">
              <textarea
                v-model="userInput"
                placeholder="今天发生了什么？告诉我你的感受..."
                rows="3"
              ></textarea>
              <el-button class="send-button" @click="getAdvice" type="primary">发送</el-button>
            </div>

            <div v-if="showInlineAdvice" class="inline-advice-container">
              <div class="advice-content" :class="`theme-${emotionTheme}`">
                <div class="advice-header">
                  <div class="emotion-icon">
                    {{ selectedEmotionObj ? selectedEmotionObj.icon : '🙂' }}
                  </div>
                  <div class="emotion-title">{{ getEmotionTitle(selectedEmotion) }}</div>
                </div>

                <div class="advice-body">
                  <div class="analysis-section">
                    <h3>心理分析</h3>
                    <p>{{ adviceData.analysis }}</p>
                  </div>

                  <div class="keywords-section">
                    <div class="keywords">
                      <span
                        v-for="(keyword, index) in adviceData.keywords"
                        :key="index"
                        :class="`keyword-${index + 1}`"
                        >{{ keyword }}</span
                      >
                    </div>
                  </div>

                  <div class="advice-section">
                    <h3>心灵建议</h3>
                    <p>{{ adviceData.advice }}</p>
                  </div>
                </div>

                <div class="advice-footer">
                  <button class="generate-ticket-btn" @click="generateTicket">生成心灵车票</button>
                </div>
              </div>
            </div>
          </div>

          <div class="history-section glass-card" v-if="!showAllTicketHistory">
            <div class="history-header" @click="showAllTickets" title="点击查看全部心灵车票">
              <div class="mac-folder">
                <div class="folder-icon">
                  <svg
                    width="36"
                    height="30"
                    viewBox="0 0 48 40"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M4 8C4 6.89543 4.89543 6 6 6H14L18 10H42C43.1046 10 44 10.8954 44 12V36C44 37.1046 43.1046 38 42 38H6C4.89543 38 4 37.1046 4 36V8Z"
                      fill="url(#folder_gradient_soul)"
                    />
                    <path
                      d="M6 6C4.89543 6 4 6.89543 4 8V12H18L14 8H6Z"
                      fill="url(#folder_top_gradient_soul)"
                    />
                    <defs>
                      <linearGradient
                        id="folder_gradient_soul"
                        x1="24"
                        y1="10"
                        x2="24"
                        y2="38"
                        gradientUnits="userSpaceOnUse"
                      >
                        <stop offset="0" stop-color="#3B82F6" />
                        <stop offset="1" stop-color="#2563EB" />
                      </linearGradient>
                      <linearGradient
                        id="folder_top_gradient_soul"
                        x1="11"
                        y1="6"
                        x2="11"
                        y2="12"
                        gradientUnits="userSpaceOnUse"
                      >
                        <stop offset="0" stop-color="#60A5FA" />
                        <stop offset="1" stop-color="#3B82F6" />
                      </linearGradient>
                    </defs>
                  </svg>
                </div>
                <div class="folder-content">
                  <div class="history-title">我的心灵车票</div>
                  <div class="ticket-count">{{ ticketHistoryList.length }}个项目</div>
                </div>
              </div>
            </div>

            <div class="history-list">
              <div
                v-for="(ticket, index) in latestTickets.slice(0, 5)"
                :key="index"
                class="history-item"
                @click="viewTicketDetail(ticket)"
              >
                <div class="history-date">{{ ticket.date }}</div>
                <div class="history-flight">
                  <div class="flight-code">{{ ticket.flightCode }}</div>
                  <div class="flight-route">
                    <div class="route-from">{{ ticket.from }}</div>
                    <div class="route-arrow">→</div>
                    <div class="route-to">{{ ticket.to }}</div>
                  </div>
                </div>
                <div class="ticket-message">{{ ticket.message }}</div>
              </div>

              <div v-if="ticketHistoryList.length === 0" class="no-tickets">
                还没有心灵车票，创建你的第一张吧
              </div>

              <div v-if="ticketHistoryList.length > 5" class="view-more" @click="showAllTickets">
                查看更多车票
              </div>
            </div>
          </div>
        </div>

        <AdviceDisplay
          v-if="showAdvice"
          :emotion="{ main: selectedEmotion }"
          :analysis="adviceData.analysis"
          :advice="adviceData.advice"
          :keywords="adviceData.keywords"
          :show="showAdvice"
          @generate-ticket="generateTicket"
          @close="showAdvice = false"
        />

        <TicketGenerator
          v-if="showTicket"
          :emotion="{ main: selectedEmotion }"
          :userInput="userInput"
          :analysis="adviceData.analysis"
          :advice="adviceData.advice"
          :show="showTicket"
          @ticket-generated="addTicketToHistory"
          @close="showTicket = false"
        />

        <TicketHistory
          :tickets="ticketHistoryList"
          :show="showAllTicketHistory"
          @close="showAllTicketHistory = false"
        />

        <footer class="app-footer">
          <p>© 2026 心灵之旅 - 关爱心理健康</p>
        </footer>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElButton, ElMessage } from 'element-plus'
import OnboardingGuide from '@/components/soul/OnboardingGuide.vue'
import AdviceDisplay from '@/components/soul/AdviceDisplay.vue'
import TicketGenerator from '@/components/soul/TicketGenerator.vue'
import TicketHistory from '@/components/soul/TicketHistory.vue'
import { useTicketStore, sortTicketsDesc } from '@/store/ticketStore'
import { useAuthStore } from '@/store/auth'
import { useAppStore } from '@/store/app'
import * as api from '@/api'
import type { Ticket } from '@/types'

interface Emotion {
  name: string
  icon: string
  color: string
  gradient: string
  theme: string
}

interface AdviceItem {
  analysis: string
  advice: string
  keywords: string[]
}

// Pinia stores
const ticketStore = useTicketStore()
const authStore = useAuthStore()
const appStore = useAppStore()
const router = useRouter()

const ticketHistoryList = computed(() => ticketStore.ticketHistoryList)

// 主页历史列表：按时间倒序，最新的车票排在最前面
const latestTickets = computed(() => sortTicketsDesc(ticketHistoryList.value, ticketHistoryList.value))

// 当前共享对话 id（由 hamu-pet 后端提供，与聊天面板联动）
const sharedConversationId = ref<string | null>(null)

// 生命周期
onMounted(async () => {
  // 深色模式由 app store 的 themeSettings 统一管理（与设置面板联动），无需本地恢复

  // 加载当前用户的共享对话（与 hamu-pet 聊天面板共享）
  try {
    const conv = await api.getActiveConversation()
    sharedConversationId.value = conv.id
  } catch (e) {
    console.error('加载共享对话失败:', e)
  }
})

// 响应式数据
const emotions = ref<Emotion[]>([
  { name: '开心', icon: '😊', color: '#FFD700', gradient: '135deg, #FFD700 0%, #FFA500 100%', theme: 'sunshine' },
  { name: '焦虑', icon: '😰', color: '#9370DB', gradient: '135deg, #9370DB 0%, #8A2BE2 100%', theme: 'healing' },
  { name: '平静', icon: '😌', color: '#87CEEB', gradient: '135deg, #87CEEB 0%, #4682B4 100%', theme: 'ocean' },
  { name: '难过', icon: '😢', color: '#4682B4', gradient: '135deg, #4682B4 0%, #1E3A8A 100%', theme: 'comfort' },
  { name: '生气', icon: '😠', color: '#FF6347', gradient: '135deg, #FF6347 0%, #DC2626 100%', theme: 'release' },
  { name: '疲惫', icon: '😩', color: '#708090', gradient: '135deg, #708090 0%, #2F4F4F 100%', theme: 'rest' }
])

const selectedEmotion = ref<string>('')
const userInput = ref<string>('')
const showTicket = ref<boolean>(false)
const showAdvice = ref<boolean>(false)
const showInlineAdvice = ref<boolean>(false)
const isDarkMode = computed(() => appStore.themeSettings.darkMode)
const showAllTicketHistory = ref<boolean>(false)
const selectedEmotionObj = ref<Emotion | null>(null)

const adviceData = ref<AdviceItem>({
  analysis: '',
  advice: '',
  keywords: []
})

// 计算属性
const emotionTheme = computed(() => {
  if (!selectedEmotion.value) return 'default'
  const emotion = emotions.value.find((e) => e.name === selectedEmotion.value)
  return emotion ? emotion.theme : 'default'
})

// 方法
function toggleTheme(): void {
  // 深色模式统一写入 app store，与 hamu-pet 设置面板联动
  appStore.themeSettings.darkMode = !appStore.themeSettings.darkMode
  appStore.saveThemeSettings()
}

function selectEmotion(emotion: string): void {
  selectedEmotion.value = emotion
  // 同步心情主题到全局 store，联动 AI 智能对话抽屉等界面的背景配色
  const matched = emotions.value.find((e) => e.name === emotion)
  appStore.setEmotionTheme(matched ? matched.theme : 'default')
}

function getEmotionTitle(emotion: string): string {
  const titles: Record<string, string> = {
    开心: '快乐时光',
    焦虑: '平静心灵',
    平静: '内心平和',
    难过: '温暖慰藉',
    生气: '情绪释放',
    疲惫: '休息充电'
  }
  return emotion ? titles[emotion] || '心灵建议' : '心灵建议'
}

async function getAdvice(): Promise<void> {
  if (!selectedEmotion.value) {
    ElMessage.warning('请先选择一个情绪')
    return
  }
  if (!userInput.value.trim()) {
    ElMessage.warning('请输入你的感受')
    return
  }

  showInlineAdvice.value = true
  adviceData.value = {
    analysis: '分析中...',
    advice: '生成建议中...',
    keywords: ['加载', '中', '...']
  }

  try {
    const result = await api.analyzeSoulEmotion(
      selectedEmotion.value,
      userInput.value,
      sharedConversationId.value
    )

    // 后端返回的对话 id（可能新建了一条共享对话）
    if (result.conversationId) {
      sharedConversationId.value = result.conversationId
      appStore.conversationId = result.conversationId
    }
    appStore.messages.push(
      { role: 'user', content: `[情绪:${selectedEmotion.value}] ${userInput.value.trim()}` },
      { role: 'assistant', content: `【心理分析】${result.analysis}\n\n【心灵建议】${result.advice}` },
    )

    adviceData.value = {
      analysis: result.analysis || `我理解你正在经历${selectedEmotion.value}的情绪`,
      advice: result.advice || '记录你的心情，关注心理健康',
      keywords:
        result.keywords?.length > 0
          ? result.keywords
          : userInput.value
              .split(/[,，、\s]+/)
              .filter((w) => w.length >= 2)
              .slice(0, 3) || ['感受', selectedEmotion.value, '情绪']
    }

    selectedEmotionObj.value = emotions.value.find((e) => e.name === selectedEmotion.value) || null
    showAdvice.value = false
  } catch (error) {
    console.error('获取心理建议失败:', error)
    adviceData.value = {
      analysis: `我理解你正在经历${selectedEmotion.value}的情绪。`,
      advice: '建议你尝试深呼吸、冥想或与亲友交流。',
      keywords: [selectedEmotion.value, '情绪', '自我关怀']
    }
    selectedEmotionObj.value = emotions.value.find((e) => e.name === selectedEmotion.value) || null
  }
}

function generateTicket(): void {
  showAdvice.value = false
  showTicket.value = false
  setTimeout(() => {
    showTicket.value = true
  }, 50)
}

function addTicketToHistory(ticket: Ticket): void {
  ticketStore.addNewTicket(ticket)
  // 车票生成完成后，自动清空心情选择、输入内容与建议卡片，恢复到初始状态
  resetSoulForm()
}

// 重置「今天，你的心情如何?」整块内容：情绪选择、文本输入、心理分析建议
function resetSoulForm(): void {
  userInput.value = ''
  selectedEmotion.value = ''
  selectedEmotionObj.value = null
  adviceData.value = {
    analysis: '',
    advice: '',
    keywords: []
  }
  showInlineAdvice.value = false
  showAdvice.value = false
  // 同步重置全局心情主题，AI 对话抽屉等联动界面恢复默认配色
  appStore.setEmotionTheme('default')
}

function showAllTickets(): void {
  showAllTicketHistory.value = true
}

function viewTicketDetail(ticket: Ticket): void {
  showAllTicketHistory.value = true
}

async function onLogout() {
  await authStore.logout()
  router.replace('/login')
}
</script>

<style>
@import '@/assets/main.css';

.app-container {
  min-height: 100vh;
  transition: background-color 1.2s ease;
  position: relative;
  overflow-x: hidden;
  background-color: #f1f4f8;
}

/* 情绪氛围光斑层：background-color 可平滑过渡，切换表情时颜色如夕阳般渐变 */
.ambient-bg {
  position: fixed;
  inset: 0;
  overflow: hidden;
  z-index: 0;
  pointer-events: none;
}

.ambient-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.5;
  transition: background-color 1.4s ease, opacity 1.4s ease;
  animation: blob-drift 26s ease-in-out infinite;
}

.blob-a { width: 55vmax; height: 55vmax; top: -18vmax; left: -12vmax; }
.blob-b { width: 45vmax; height: 45vmax; top: 32%; right: -16vmax; animation-delay: -9s; }
.blob-c { width: 42vmax; height: 42vmax; bottom: -14vmax; left: 28%; animation-delay: -18s; }

/* 默认（未选择情绪）：晨雾般的多彩柔光 */
.blob-a { background-color: rgba(175, 200, 250, 0.35); }
.blob-b { background-color: rgba(250, 200, 180, 0.30); }
.blob-c { background-color: rgba(175, 235, 210, 0.28); }

@keyframes blob-drift {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(4vmax, -3vmax) scale(1.08); }
  66% { transform: translate(-3vmax, 4vmax) scale(0.94); }
}

/* 页面底色随情绪浸染（参考图主色柔化，饱和度适中） */
.app-container.theme-sunshine { background-color: #f5d76e; }
.app-container.theme-healing  { background-color: #c5a8e5; }
.app-container.theme-ocean    { background-color: #a5c6e1; }
.app-container.theme-comfort  { background-color: #85a0be; }
.app-container.theme-release  { background-color: #ee9187; }
.app-container.theme-rest     { background-color: #e2dcc8; }

/* 深色模式：保留主题色调的暗色变体，让氛围色在暗黑下依然可感知 */
body.dark-mode .app-container.theme-sunshine { background-color: #453a20; }
body.dark-mode .app-container.theme-healing  { background-color: #3b3155; }
body.dark-mode .app-container.theme-ocean    { background-color: #2b3e54; }
body.dark-mode .app-container.theme-comfort  { background-color: #2a3441; }
body.dark-mode .app-container.theme-release  { background-color: #472a26; }
body.dark-mode .app-container.theme-rest     { background-color: #3a362c; }

/* ——— 开心：金黄 × 暖橙，如参考图的明媚阳光 ——— */
.theme-sunshine .blob-a { background-color: rgba(250, 200, 60, 0.55); }
.theme-sunshine .blob-b { background-color: rgba(245, 170, 80, 0.45); }
.theme-sunshine .blob-c { background-color: rgba(240, 190, 90, 0.45); }

/* ——— 焦虑：紫色 × 亮紫 × 浅紫，如参考图的薰衣草暮色 ——— */
.theme-healing .blob-a { background-color: rgba(150, 110, 205, 0.5); }
.theme-healing .blob-b { background-color: rgba(165, 125, 215, 0.45); }
.theme-healing .blob-c { background-color: rgba(185, 150, 225, 0.4); }

/* ——— 平静：天蓝 × 浅蓝 × 蓝，如参考图的晴空湖面 ——— */
.theme-ocean .blob-a { background-color: rgba(105, 165, 210, 0.5); }
.theme-ocean .blob-b { background-color: rgba(130, 180, 220, 0.45); }
.theme-ocean .blob-c { background-color: rgba(115, 150, 205, 0.42); }

/* ——— 难过：深蓝灰 × 灰蓝 × 浅蓝灰，如参考图的静谧深海 ——— */
.theme-comfort .blob-a { background-color: rgba(90, 125, 165, 0.5); }
.theme-comfort .blob-b { background-color: rgba(110, 135, 170, 0.45); }
.theme-comfort .blob-c { background-color: rgba(140, 165, 200, 0.45); }

/* ——— 生气：红 × 珊瑚 × 粉红，如参考图的热烈释放 ——— */
.theme-release .blob-a { background-color: rgba(235, 95, 85, 0.5); }
.theme-release .blob-b { background-color: rgba(240, 115, 100, 0.45); }
.theme-release .blob-c { background-color: rgba(235, 110, 125, 0.4); }

/* ——— 疲惫：亚麻 × 鼠尾草 × 暖灰，休息充电 ——— */
.theme-rest .blob-a { background-color: rgba(215, 195, 155, 0.55); }
.theme-rest .blob-b { background-color: rgba(180, 195, 175, 0.45); }
.theme-rest .blob-c { background-color: rgba(210, 200, 185, 0.5); }

/* 选中情绪卡片：外圈光晕与主题色呼应（中性色调） */
.theme-sunshine .emotion-item.active { border-color: #d9a441; box-shadow: 0 8px 24px rgba(217, 164, 65, 0.35); }
.theme-healing  .emotion-item.active { border-color: #9b7fc7; box-shadow: 0 8px 24px rgba(155, 127, 199, 0.35); }
.theme-ocean    .emotion-item.active { border-color: #4a9cc7; box-shadow: 0 8px 24px rgba(74, 156, 199, 0.35); }
.theme-comfort  .emotion-item.active { border-color: #8aa5c8; box-shadow: 0 8px 24px rgba(138, 165, 200, 0.35); }
.theme-release  .emotion-item.active { border-color: #c98268; box-shadow: 0 8px 24px rgba(201, 130, 104, 0.35); }
.theme-rest     .emotion-item.active { border-color: #a8a29e; box-shadow: 0 8px 24px rgba(168, 162, 158, 0.35); }

/* 深色模式下光斑稍亮，让主题氛围色在暗黑下可感知 */
body.dark-mode .ambient-blob { opacity: 0.4; }
body.dark-mode .app-container { transition: background-color 1.2s ease; }

.app-container.dark-mode {
  background-color: #121212;
}

body.dark-mode {
  background-color: #121212;
  color: #e0e0e0;
}

body.dark-mode .app-container {
  background-color: rgba(18, 18, 18, 0.8);
}

body.dark-mode .glass-card {
  background: rgba(30, 30, 30, 0.7);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

body.dark-mode .input-section h2,
body.dark-mode .history-title,
body.dark-mode .passenger-value,
body.dark-mode .message {
  color: #e0e0e0;
}

body.dark-mode .subtitle,
body.dark-mode .passenger-label,
body.dark-mode .ticket-count {
  color: #a0a0a0;
}

body.dark-mode textarea {
  background: rgba(40, 40, 40, 0.8);
  color: #e0e0e0;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

body.dark-mode .history-item {
  background: rgba(40, 40, 40, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

body.dark-mode .theme-toggle-btn,
body.dark-mode .logout-btn {
  background: rgba(30, 30, 30, 0.8);
  color: #e0e0e0;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* 主题切换按钮样式 */
.theme-toggle {
  position: absolute;
  top: 20px;
  right: 20px;
  display: flex;
  gap: 10px;
}

.theme-toggle-btn,
.logout-btn {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.1);
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.theme-toggle-btn:hover,
.logout-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 整合容器样式 */
.integrated-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 30px;
}

.input-section {
  margin-bottom: 0;
}

/* 内联建议容器样式 */
.inline-advice-container {
  margin-top: 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  padding-top: 20px;
}

.inline-advice-container .advice-content {
  padding: 15px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.7);
}

.inline-advice-container .advice-header {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.inline-advice-container .emotion-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.inline-advice-container .emotion-title {
  font-size: 1.3rem;
  font-weight: 600;
}

.inline-advice-container .advice-body {
  margin-bottom: 20px;
  max-height: 500px;
  overflow-y: auto;
  padding-right: 10px;
  padding-left: 5px;
}

.inline-advice-container .advice-body::-webkit-scrollbar {
  width: 6px;
}

.inline-advice-container .advice-body::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
}

.inline-advice-container .advice-body::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.15);
  border-radius: 3px;
}

.inline-advice-container .analysis-section,
.inline-advice-container .advice-section {
  margin-bottom: 15px;
}

.inline-advice-container h3 {
  font-size: 1.1rem;
  margin-bottom: 8px;
  color: #4b5563;
}

.inline-advice-container p {
  line-height: 1.5;
  color: #1f2937;
}

.inline-advice-container .keywords-section {
  margin: 15px 0;
  display: flex;
  justify-content: center;
}

.inline-advice-container .keywords {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}

.inline-advice-container .keywords span {
  padding: 5px 10px;
  border-radius: 16px;
  font-size: 0.85rem;
  font-weight: 500;
  color: white;
}

.inline-advice-container .keyword-1 { background-color: #3b82f6; animation: advice-pulse 1.5s infinite ease-in-out; }
.inline-advice-container .keyword-2 { background-color: #10b981; animation: advice-pulse 1.5s infinite ease-in-out 0.5s; }
.inline-advice-container .keyword-3 { background-color: #f59e0b; animation: advice-pulse 1.5s infinite ease-in-out 1s; }

@keyframes advice-pulse {
  0% { opacity: 0.6; transform: scale(0.95); }
  50% { opacity: 1; transform: scale(1.05); }
  100% { opacity: 0.6; transform: scale(0.95); }
}

.inline-advice-container .advice-footer {
  display: flex;
  justify-content: center;
  margin-top: 15px;
}

.inline-advice-container .generate-ticket-btn {
  background-color: #3b82f6;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 6px rgba(59, 130, 246, 0.3);
}

.inline-advice-container .generate-ticket-btn:hover {
  background-color: #2563eb;
  transform: translateY(-2px);
  box-shadow: 0 6px 8px rgba(59, 130, 246, 0.4);
}

/* 历史记录区域样式 */
.history-section {
  padding: 20px;
}

.history-section .history-header {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  cursor: pointer;
  border-radius: 10px;
  padding: 6px;
  margin: -6px;
  transition: background-color 0.2s ease;
}

.history-section .history-header:hover {
  background-color: rgba(59, 130, 246, 0.06);
}

.history-section .history-header:hover .history-title {
  color: #3b82f6;
}

.mac-folder {
  display: flex;
  align-items: center;
}

.folder-icon {
  margin-right: 10px;
}

.folder-content {
  display: flex;
  flex-direction: column;
}

.history-title {
  font-weight: 500;
  font-size: 16px;
  color: #333;
}

.ticket-count {
  font-size: 12px;
  color: #666;
}

.history-list {
  max-height: 300px;
  overflow-y: auto;
  padding-right: 5px;
}

.history-list::-webkit-scrollbar {
  width: 6px;
}

.history-list::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
}

.history-list::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.15);
  border-radius: 3px;
}

.history-item {
  padding: 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.5);
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.history-item:hover {
  background: rgba(255, 255, 255, 0.8);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
}

.history-date {
  font-size: 12px;
  color: #666;
  margin-bottom: 5px;
}

.history-flight {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.flight-code {
  font-weight: 500;
  font-size: 14px;
  color: #3b82f6;
}

.flight-route {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: #333;
}

.route-arrow {
  margin: 0 5px;
  color: #999;
}

.ticket-message {
  font-size: 13px;
  color: #444;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.no-tickets {
  text-align: center;
  padding: 20px;
  color: #666;
  font-size: 14px;
}

.view-more {
  text-align: center;
  padding: 10px;
  color: #3b82f6;
  font-size: 14px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.view-more:hover {
  color: #2563eb;
  text-decoration: underline;
}
</style>
