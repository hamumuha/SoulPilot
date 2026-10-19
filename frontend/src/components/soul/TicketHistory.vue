<template>
  <Transition name="history-window">
    <div
      v-if="show"
      class="ticket-history-overlay"
      role="presentation"
      @click.self="$emit('close')"
    >
      <div class="ticket-history-container" role="dialog" aria-modal="true" aria-label="我的心灵车票">
        <div class="history-header">
          <div class="mac-folder">
            <div class="folder-icon">
              <svg
                width="48"
                height="40"
                viewBox="0 0 48 40"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M4 8C4 6.89543 4.89543 6 6 6H14L18 10H42C43.1046 10 44 10.8954 44 12V36C44 37.1046 43.1046 38 42 38H6C4.89543 38 4 37.1046 4 36V8Z"
                  fill="url(#folder_gradient_hist)"
                />
                <path d="M6 6C4.89543 6 4 6.89543 4 8V12H18L14 8H6Z" fill="url(#folder_top_gradient_hist)" />
                <defs>
                  <linearGradient
                    id="folder_gradient_hist"
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
                    id="folder_top_gradient_hist"
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
              <div class="ticket-count">{{ tickets.length }}个项目</div>
            </div>
          </div>
          <div class="mac-window-controls">
            <div class="control close" @click="$emit('close')"></div>
            <div class="control minimize"></div>
            <div class="control expand"></div>
          </div>
          <button class="history-close-btn" @click="$emit('close')">✕ 关闭</button>
        </div>

        <div class="search-filters">
          <div class="filter-group">
            <div class="filter-label">情绪筛选</div>
            <div class="emotion-filters">
              <div
                v-for="emotion in emotions"
                :key="emotion.name"
                :class="['emotion-filter', { active: selectedEmotions.includes(emotion.name) }]"
                @click="toggleEmotionFilter(emotion.name)"
              >
                <span class="emotion-icon">{{ emotion.icon }}</span>
                <span class="emotion-name">{{ emotion.name }}</span>
              </div>
            </div>
          </div>

          <div class="filter-group">
            <div class="filter-label">日期范围</div>
            <div class="date-filters">
              <div
                v-for="period in datePeriods"
                :key="period.value"
                :class="['date-filter', { active: selectedDatePeriod === period.value }]"
                @click="selectDatePeriod(period.value)"
              >
                {{ period.label }}
              </div>
            </div>
          </div>
        </div>

        <div class="history-list">
          <div
            v-for="(ticket, index) in filteredTickets"
            :key="index"
            class="history-item"
            :style="getTicketThemeStyle(ticket)"
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

          <div v-if="filteredTickets.length === 0" class="no-tickets">
            没有找到符合条件的车票
          </div>
        </div>

        <!-- 车票详情弹窗 -->
        <div v-if="showDetail && selectedTicket" class="ticket-detail-modal">
          <div class="modal-content" :style="getTicketThemeStyle(selectedTicket)">
            <div class="modal-header">
              <h3>车票详情</h3>
              <div class="close-button" @click="closeDetail">&times;</div>
            </div>
            <div class="modal-body">
              <div class="detail-item">
                <div class="detail-label">日期</div>
                <div class="detail-value">{{ selectedTicket.date }}</div>
              </div>
              <div class="detail-item">
                <div class="detail-label">航班</div>
                <div class="detail-value">{{ selectedTicket.flightCode }}</div>
              </div>
              <div class="detail-item">
                <div class="detail-label">路线</div>
                <div class="detail-value">{{ selectedTicket.from }} → {{ selectedTicket.to }}</div>
              </div>
              <div class="detail-item">
                <div class="detail-label">消息</div>
                <div class="detail-value">{{ selectedTicket.message }}</div>
              </div>
              <div v-if="selectedTicket.analysis" class="detail-item">
                <div class="detail-label">心理分析</div>
                <div class="detail-value">{{ selectedTicket.analysis }}</div>
              </div>
              <div v-if="selectedTicket.advice" class="detail-item">
                <div class="detail-label">心灵建议</div>
                <div class="detail-value">{{ selectedTicket.advice }}</div>
              </div>
              <div class="detail-item">
                <div class="detail-label">关键词</div>
                <div class="detail-value keywords">
                  <span
                    v-for="(keyword, i) in selectedTicket.keywords || []"
                    :key="i"
                    class="keyword"
                  >
                    {{ keyword }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Ticket } from '@/types'
import { sortTicketsDesc, parseTicketDate } from '@/store/ticketStore'

interface Emotion {
  name: string
  icon: string
}

interface DatePeriod {
  label: string
  value: string
}

// 接收父组件传参
const props = defineProps<{
  tickets: Ticket[]
  show: boolean
}>()

defineEmits<{
  close: []
}>()

// 响应式数据
const emotions = ref<Emotion[]>([
  { name: '开心', icon: '😊' },
  { name: '焦虑', icon: '😰' },
  { name: '平静', icon: '😌' },
  { name: '难过', icon: '😢' },
  { name: '生气', icon: '😠' },
  { name: '疲惫', icon: '😩' }
])

const selectedEmotions = ref<string[]>([])

const datePeriods = ref<DatePeriod[]>([
  { label: '全部', value: 'all' },
  { label: '今天', value: 'today' },
  { label: '本周', value: 'week' },
  { label: '本月', value: 'month' }
])

const selectedDatePeriod = ref<string>('all')
const showDetail = ref<boolean>(false)
const selectedTicket = ref<Ticket | null>(null)

// 计算属性 - 筛选车票
const filteredTickets = computed(() => {
  let result = [...props.tickets]

  // 情绪筛选
  if (selectedEmotions.value.length > 0) {
    result = result.filter((ticket) => {
      const emotion = getEmotionFromDestination(ticket.to)
      return selectedEmotions.value.includes(emotion)
    })
  }

  // 日期筛选
  if (selectedDatePeriod.value !== 'all') {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())

    result = result.filter((ticket) => {
      const ticketDate = parseTicketDate(ticket.date)

      switch (selectedDatePeriod.value) {
        case 'today':
          return ticketDate >= today.getTime()
        case 'week': {
          const weekStart = new Date(today)
          weekStart.setDate(today.getDate() - today.getDay())
          return ticketDate >= weekStart.getTime()
        }
        case 'month': {
          const monthStart = new Date(now.getFullYear(), today.getMonth(), 1)
          return ticketDate >= monthStart.getTime()
        }
        default:
          return true
      }
    })
  }

  // 时间倒序：最新的车票排在最上面，久远的排在下面
  result = sortTicketsDesc(result, props.tickets)

  return result
})

// 方法
function toggleEmotionFilter(emotion: string) {
  const index = selectedEmotions.value.indexOf(emotion)
  if (index === -1) {
    selectedEmotions.value.push(emotion)
  } else {
    selectedEmotions.value.splice(index, 1)
  }
}

function selectDatePeriod(period: string) {
  selectedDatePeriod.value = period
}

function viewTicketDetail(ticket: Ticket) {
  selectedTicket.value = ticket
  showDetail.value = true
}

function closeDetail() {
  showDetail.value = false
  selectedTicket.value = null
}

function getEmotionFromDestination(destination: string): string {
  const destinationMap: Record<string, string> = {
    阳光城: '开心',
    治愈湾: '焦虑',
    平静湖: '平静',
    温暖岛: '难过',
    释放峰: '生气',
    休息谷: '疲惫',
    心灵港湾: '平静'
  }
  return destinationMap[destination] || '平静'
}

function getTicketThemeStyle(ticket: Ticket): Record<string, string> {
  const emotion = ticket.emotion || getEmotionFromDestination(ticket.to)
  const themeStyles: Record<string, Record<string, string>> = {
    开心: {
      '--ticket-bg': '#fff8df',
      '--ticket-bg-dark': '#453a20',
      '--ticket-border': '#f0d98f',
      '--ticket-border-dark': '#76613a',
      '--ticket-accent': '#a86d00'
    },
    焦虑: {
      '--ticket-bg': '#f4edff',
      '--ticket-bg-dark': '#3b3155',
      '--ticket-border': '#d9c8f2',
      '--ticket-border-dark': '#68558d',
      '--ticket-accent': '#7650a8'
    },
    平静: {
      '--ticket-bg': '#eaf6ff',
      '--ticket-bg-dark': '#2b3e54',
      '--ticket-border': '#c5e3f7',
      '--ticket-border-dark': '#496681',
      '--ticket-accent': '#2878a8'
    },
    难过: {
      '--ticket-bg': '#edf3fa',
      '--ticket-bg-dark': '#2a3441',
      '--ticket-border': '#cbd8e8',
      '--ticket-border-dark': '#4c6078',
      '--ticket-accent': '#526e91'
    },
    生气: {
      '--ticket-bg': '#fff0ec',
      '--ticket-bg-dark': '#472a26',
      '--ticket-border': '#f2c7bc',
      '--ticket-border-dark': '#805046',
      '--ticket-accent': '#b84d3c'
    },
    疲惫: {
      '--ticket-bg': '#f5f2e8',
      '--ticket-bg-dark': '#3a362c',
      '--ticket-border': '#ded7c3',
      '--ticket-border-dark': '#68614d',
      '--ticket-accent': '#817454'
    }
  }

  return themeStyles[emotion] || themeStyles['平静']
}
</script>

<style scoped>
.ticket-history-container {
  width: min(610px, calc(100vw - 32px));
  max-height: 80vh;
  background: rgba(245, 245, 247, 0.9);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.ticket-history-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(31, 41, 55, 0.24);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.history-window-enter-active,
.history-window-leave-active {
  transition: opacity 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.history-window-enter-active .ticket-history-container,
.history-window-leave-active .ticket-history-container {
  transition:
    opacity 0.35s cubic-bezier(0.2, 0.8, 0.2, 1),
    transform 0.35s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.history-window-enter-from,
.history-window-leave-to {
  opacity: 0;
}

.history-window-enter-from .ticket-history-container,
.history-window-leave-to .ticket-history-container {
  opacity: 0;
  transform: translateY(18px) scale(0.96);
}

body.dark-mode .ticket-history-container {
  background: rgba(30, 30, 30, 0.85);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(80, 80, 80, 0.3);
}

.history-header {
  display: flex;
  align-items: center;
  padding: 16px 16px 16px 70px;
  position: relative;
  background: linear-gradient(to bottom, #f5f5f7, #e5e5ea);
  border-bottom: 1px solid #d1d1d6;
  border-radius: 10px 10px 0 0;
  height: 60px;
}

body.dark-mode .history-header {
  background: linear-gradient(to bottom, #2c2c2e, #1c1c1e);
  border-bottom: 1px solid #3a3a3c;
}

.mac-folder {
  display: flex;
  align-items: center;
  flex: 1;
}

.folder-icon {
  margin-right: 12px;
}

.folder-content {
  display: flex;
  flex-direction: column;
}

.history-title {
  font-size: 15px;
  font-weight: 600;
  color: #1d1d1f;
  margin-bottom: 2px;
}

.ticket-count {
  font-size: 12px;
  color: #86868b;
  font-weight: 400;
}

body.dark-mode .history-title {
  color: #ffffff;
}

body.dark-mode .ticket-count {
  color: #d0d0d0;
}

.mac-window-controls {
  display: flex;
  align-items: center;
  position: absolute;
  left: 16px;
  top: 16px;
  gap: 8px;
}

.control {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
}

.control.close { background-color: #ff5f57; border: 1px solid #e04343; }
.control.minimize { background-color: #ffbd2e; border: 1px solid #e0a92e; }
.control.expand { background-color: #28c940; border: 1px solid #1daa32; }

.control:hover { filter: brightness(1.1); }

/* 明显的关闭按钮 */
.history-close-btn {
  margin-left: 10px;
  padding: 6px 14px;
  border: none;
  border-radius: 16px;
  background: rgba(255, 95, 87, 0.12);
  color: #e04343;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.history-close-btn:hover {
  background: #ff5f57;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(255, 95, 87, 0.35);
}

body.dark-mode .history-close-btn {
  background: rgba(255, 95, 87, 0.2);
  color: #ff8a80;
}

body.dark-mode .history-close-btn:hover {
  background: #ff5f57;
  color: white;
}

/* 筛选器样式 */
.search-filters {
  padding: 16px;
  background-color: #f5f5f7;
  border-bottom: 1px solid #d1d1d6;
}

.filter-group {
  margin-bottom: 14px;
}

.filter-group:last-child {
  margin-bottom: 0;
}

.filter-label {
  font-size: 12px;
  color: #3a3a3c;
  margin-bottom: 8px;
  font-weight: 500;
  letter-spacing: -0.1px;
}

.emotion-filters,
.date-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.emotion-filter,
.date-filter {
  padding: 5px 10px;
  border-radius: 16px;
  background: white;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid #d1d1d6;
  color: #3a3a3c;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.emotion-filter {
  display: flex;
  align-items: center;
}

.emotion-icon {
  margin-right: 5px;
}

.emotion-filter:hover,
.date-filter:hover {
  background: #f9f9fa;
  border-color: #c7c7cc;
}

.emotion-filter.active,
.date-filter.active {
  background: rgba(0, 122, 255, 0.1);
  border: 1px solid rgba(0, 122, 255, 0.3);
  color: #007aff;
  font-weight: 500;
}

/* 历史列表样式 */
.history-list {
  max-height: 400px;
  overflow-y: auto;
  padding: 0 16px;
  margin: 0 0 16px 0;
  scrollbar-width: thin;
  scrollbar-color: rgba(156, 163, 175, 0.5) transparent;
  background: white;
  border-radius: 0 0 10px 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #d1d1d6;
  border-top: none;
}

body.dark-mode .history-list {
  background: #2c2c2e;
}

.history-list::-webkit-scrollbar {
  width: 8px;
}

.history-list::-webkit-scrollbar-track {
  background: #f5f5f7;
  border-radius: 0 0 10px 0;
}

.history-list::-webkit-scrollbar-thumb {
  background-color: #c1c1c6;
  border-radius: 4px;
  border: 2px solid #f5f5f7;
}

.history-list::-webkit-scrollbar-thumb:hover {
  background-color: #a1a1a6;
}

.history-item {
  padding: 12px;
  border-radius: 8px;
  background: var(--ticket-bg, white);
  margin: 12px 0;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid var(--ticket-border, #e5e5ea);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  position: relative;
}

body.dark-mode .history-item {
  background: var(--ticket-bg-dark, #3a3a3c);
  border: 1px solid var(--ticket-border-dark, #4a4a4c);
}

.history-item:hover {
  filter: brightness(0.98);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

.history-date {
  font-size: 11px;
  color: #8e8e93;
  margin-bottom: 6px;
  font-weight: 500;
}

.history-flight {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.flight-code {
  font-weight: 600;
  color: var(--ticket-accent, #007aff);
  font-size: 14px;
}

.flight-route {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: #3a3a3c;
}

.route-arrow {
  margin: 0 5px;
  color: #8e8e93;
}

.ticket-message {
  font-size: 12px;
  color: #3a3a3c;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

body.dark-mode .history-date { color: #c1c1c6; }
body.dark-mode .flight-code { color: var(--ticket-accent, #3a97ff); }
body.dark-mode .flight-route { color: #ffffff; }
body.dark-mode .route-arrow { color: #c1c1c6; }
body.dark-mode .ticket-message {
  color: #ffffff;
  background-color: rgba(0, 0, 0, 0.2);
  padding: 4px 8px;
  border-radius: 4px;
  margin-top: 4px;
}

.no-tickets {
  text-align: center;
  padding: 20px;
  color: #8e8e93;
  font-style: italic;
  font-size: 13px;
}

/* 详情弹窗样式 */
.ticket-detail-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  width: 90%;
  max-width: 480px;
  background: var(--ticket-bg, rgba(245, 245, 247, 0.98));
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  animation: modal-in 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
  border: 1px solid var(--ticket-border, #d1d1d6);
}

body.dark-mode .modal-content {
  background: var(--ticket-bg-dark, #2c2c2e);
  border-color: var(--ticket-border-dark, #4a4a4c);
}

@keyframes modal-in {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(
    to bottom,
    var(--ticket-bg, #f5f5f7),
    var(--ticket-border, #e5e5ea)
  );
  border-bottom: 1px solid #d1d1d6;
}

body.dark-mode .modal-header {
  background: linear-gradient(
    to bottom,
    var(--ticket-bg-dark, #2c2c2e),
    var(--ticket-border-dark, #1c1c1e)
  );
  border-bottom-color: var(--ticket-border-dark, #3a3a3c);
}

.modal-header h3 {
  margin: 0;
  font-size: 15px;
  color: #1d1d1f;
  font-weight: 600;
}

body.dark-mode .modal-header h3 {
  color: #ffffff;
}

.modal-header .close-button {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #ff5f57;
  border: 1px solid #e04343;
  color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  transition: all 0.2s ease;
}

.modal-header .close-button:hover {
  filter: brightness(1.1);
}

.modal-body {
  padding: 16px;
  max-height: 70vh;
  overflow-y: auto;
  background: var(--ticket-bg, white);
}

body.dark-mode .modal-body {
  background: var(--ticket-bg-dark, #2c2c2e);
}

.detail-item {
  margin-bottom: 14px;
}

.detail-label {
  font-size: 11px;
  color: #86868b;
  margin-bottom: 4px;
  font-weight: 500;
}

body.dark-mode .detail-label {
  color: #a1a1a6;
}

.detail-value {
  font-size: 13px;
  color: #1d1d1f;
  line-height: 1.4;
}

body.dark-mode .detail-value {
  color: #ffffff;
}

.keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.keyword {
  background: color-mix(in srgb, var(--ticket-accent, #007aff) 12%, transparent);
  color: var(--ticket-accent, #007aff);
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

body.dark-mode .keyword {
  background: rgba(10, 132, 255, 0.3);
  color: #ffffff;
  border: 1px solid rgba(10, 132, 255, 0.5);
}

@media (prefers-reduced-motion: reduce) {
  .history-window-enter-active,
  .history-window-leave-active,
  .history-window-enter-active .ticket-history-container,
  .history-window-leave-active .ticket-history-container {
    transition-duration: 0.01ms !important;
  }
}
</style>
