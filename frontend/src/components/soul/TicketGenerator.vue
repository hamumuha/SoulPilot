<template>
  <Transition name="ticket-modal">
    <div
      v-if="show"
      class="ticket-generator-modal"
      role="dialog"
      aria-modal="true"
      aria-label="心灵车票"
      @click.self="$emit('close')"
    >
      <div class="modal-content">
      <div class="close-button" @click="$emit('close')">
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M18 6L6 18"
            stroke="#6B7280"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <path
            d="M6 6L18 18"
            stroke="#6B7280"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </div>
      <div class="confetti-container" :class="{ 'show-confetti': showConfetti }">
        <div v-for="n in 100" :key="n" class="confetti-piece" :style="getConfettiStyle(n)"></div>
      </div>
      <div
        class="ticket-container glass-card"
        :class="{ 'show-ticket': showTicket, 'dark-mode': isDarkMode }"
      >
        <div class="ticket" :class="[`theme-${emotionTheme}`, { 'dark-ticket': isDarkMode }]">
          <div class="ticket-header">
            <div class="airline-logo">
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M12 2L4 5V11.09C4 16.14 7.41 20.85 12 22C16.59 20.85 20 16.14 20 11.09V5L12 2Z"
                  fill="currentColor"
                  fill-opacity="0.9"
                />
                <path
                  d="M12 17L12 11M12 8V8.01"
                  stroke="white"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
              <div class="airline-name">心灵航空</div>
            </div>
            <div class="flight-info">
              <div class="flight-label">航班号</div>
              <div class="flight-number">{{ flightCode }}</div>
            </div>
          </div>
          <div class="ticket-body">
            <div class="ticket-content">
              <div class="route-info">
                <div class="departure-info">
                  <div class="departure-label">出发</div>
                  <div class="departure-name">{{ departure }}</div>
                </div>
                <div class="flight-path">
                  <div class="path-line">
                    <div class="dot departure-dot"></div>
                    <div class="line full-line"></div>
                    <div class="dot arrival-dot"></div>
                  </div>
                </div>
                <div class="arrival-info">
                  <div class="arrival-label">到达</div>
                  <div class="arrival-name">{{ destination }}</div>
                </div>
              </div>

              <div class="ticket-header-info">
                <div class="passenger-section seat-number">
                  <div class="passenger-label">座位</div>
                  <div class="passenger-value">{{ seatNumber }}</div>
                </div>
              </div>
              <div class="passenger-info">
                <div class="passenger-section">
                  <div class="passenger-label">日期</div>
                  <div class="passenger-value">{{ currentDate }}</div>
                </div>
                <div class="passenger-section">
                  <div class="passenger-label">登机组</div>
                  <div class="passenger-value">{{ ticketId }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="ticket-footer">
            <div class="message-container">
              <div class="message">{{ message }}</div>
              <div class="keywords">
                <span
                  v-for="(keyword, index) in keywords"
                  :key="index"
                  :class="`keyword-${index + 1}`"
                  >{{ keyword }}</span
                >
              </div>
            </div>
            <div class="barcode"></div>
            <div class="stamp" :class="{ stamped: showStamp }">
              <div class="stamp-date">{{ currentDate }}</div>
              <div class="stamp-serial">{{ serialNumber }}</div>
            </div>
          </div>

          <div class="ticket-tear" @click="tearTicket">
            <div class="tear-line"></div>
            <div class="tear-hint">撕开这里</div>
          </div>
        </div>
      </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface Emotion {
  main: string
  sub?: string
}

interface TicketData {
  date: string
  flightCode: string
  from: string
  to: string
  message: string
  keywords: string[]
  analysis: string
  advice: string
  seatNumber: string
  serialNumber: string
  emotion: string
}

interface EmotionTheme {
  theme: string
  destination: string
  flightPrefix: string
}

// 接收父组件传参
const props = defineProps<{
  emotion: Emotion
  userInput: string
  analysis: string
  advice: string
  show: boolean
}>()

// 自定义事件
const emit = defineEmits<{
  close: []
  'ticket-generated': [data: TicketData]
}>()

// 响应式数据
const showTicket = ref<boolean>(false)
const showStamp = ref<boolean>(false)
const showConfetti = ref<boolean>(false)
const isTorn = ref<boolean>(false)
const isGenerating = ref<boolean>(false)

// 打开展示时锁定本次车票对应的情绪：生成后即使父组件清空了情绪选择，
// 已展示的车票主题色与小贴士也不会随之跳变
const displayEmotion = ref<string>(props.emotion.main)

const emotionThemes = ref<Record<string, EmotionTheme>>({
  开心: { theme: 'sunshine', destination: '阳光城', flightPrefix: 'SN' },
  焦虑: { theme: 'healing', destination: '治愈湾', flightPrefix: 'HL' },
  平静: { theme: 'ocean', destination: '平静湖', flightPrefix: 'OC' },
  难过: { theme: 'comfort', destination: '温暖岛', flightPrefix: 'CM' },
  生气: { theme: 'release', destination: '释放峰', flightPrefix: 'RL' },
  疲惫: { theme: 'rest', destination: '休息谷', flightPrefix: 'RS' }
})

const keywords = ref<string[]>([])
const message = ref<string>('')
const flightCode = ref<string>('')
const seatNumber = ref<string>('A1')
const ticketId = ref<number>(Math.floor(Math.random() * 100))
const serialNumber = ref<string>(generateSerialNumber())
const departure = ref<string>('现实世界')
const destination = ref<string>('')
const currentDate = ref<string>(formatDate(new Date()))

// 计算属性
const emotionTheme = computed(() => {
  const themeConf = displayEmotion.value ? emotionThemes.value[displayEmotion.value] : null
  return themeConf ? themeConf.theme : 'default'
})

const isDarkMode = computed(() => {
  return document.body.classList.contains('dark-mode')
})

// 监听 show 变化
watch(
  () => props.show,
  (newVal) => {
    if (newVal) {
      // 打开瞬间锁定本次情绪，生成过程中/完成后父组件清空选择不影响车票展示
      displayEmotion.value = props.emotion.main
      isGenerating.value = true
      showTicket.value = false
      setTimeout(() => {
        generateTicket()
      }, 50)
    }
  },
  { immediate: true }
)

// 方法
function generateTicket(): void {
  try {
    extractKeywords()

    if (displayEmotion.value && emotionThemes.value[displayEmotion.value]) {
      const theme = emotionThemes.value[displayEmotion.value]
      destination.value = theme.destination
      flightCode.value = `${theme.flightPrefix}${Math.floor(Math.random() * 900) + 100}`
    } else {
      destination.value = '心灵港湾'
      flightCode.value = 'MJ481'
    }

    message.value =
      props.userInput.length > 0
        ? props.userInput.substring(0, 30) + (props.userInput.length > 30 ? '...' : '')
        : '记录你的心情'

    const seatRows = ['A', 'B', 'C', 'D', 'E', 'F']
    const seatNum = Math.floor(Math.random() * 30) + 1
    seatNumber.value = `${seatRows[Math.floor(Math.random() * seatRows.length)]}${seatNum}`

    serialNumber.value = generateSerialNumber()

    isTorn.value = false

    setTimeout(() => {
      showTicket.value = true
      showConfetti.value = true

      setTimeout(() => {
        showStamp.value = true

        setTimeout(() => {
          const ticketData: TicketData = {
            date: currentDate.value,
            flightCode: flightCode.value,
            from: departure.value,
            to: destination.value,
            message: message.value,
            keywords: keywords.value,
            analysis: props.analysis,
            advice: props.advice,
            seatNumber: seatNumber.value,
            serialNumber: serialNumber.value,
            emotion: displayEmotion.value
          }

          emit('ticket-generated', ticketData)
          isGenerating.value = false
        }, 1200)
      }, 1800)
    }, 600)
  } catch (error) {
    console.error('生成车票失败:', error)
    extractKeywords()
    message.value =
      props.userInput.length > 0
        ? props.userInput.substring(0, 30) + (props.userInput.length > 30 ? '...' : '')
        : '记录你的心情'
  }
}

function extractKeywords(): void {
  if (!props.userInput) {
    keywords.value = ['记录', '心情', '成长']
    return
  }

  const words = props.userInput.split(/[,，.。!！?？\s]/)
  const filteredWords = words.filter((word) => word.length >= 2 && word.length <= 4)

  if (filteredWords.length >= 3) {
    keywords.value = filteredWords.slice(0, 3)
  } else {
    const defaultKeywords = ['心情', '记录', '成长', '感受', '思考']
    keywords.value = [...filteredWords, ...defaultKeywords.slice(0, 3 - filteredWords.length)]
  }
}

function tearTicket(): void {
  if (isTorn.value) return

  const ticketElement = document.querySelector('.ticket')
  if (ticketElement) {
    ticketElement.classList.add('torn-ticket')
  }

  isTorn.value = true

  setTimeout(() => {
    const bottomElement = document.createElement('div')
    bottomElement.className = 'torn-bottom'

    const tips = [
      '每天花几分钟静坐冥想，可以帮助你平静心情。',
      '深呼吸是缓解焦虑的简单有效方法。',
      '记录感恩日记，关注生活中的美好事物。',
      '与朋友分享你的感受，不要独自承担压力。',
      '适当的运动可以释放压力，改善心情。',
      '保持充足的睡眠对心理健康至关重要。',
      '学会对自己说"不"，设定健康的边界。',
      '尝试新的爱好，拓展你的兴趣和社交圈。',
      '允许自己感受情绪，但不被情绪控制。',
      '小小的自我奖励可以增强积极情绪。',
      '接纳不完美，对自己和他人保持宽容。',
      '定期远离电子设备，给心灵一个休息的空间。'
    ]

    let tipIndex = Math.floor(Math.random() * tips.length)
    if (displayEmotion.value) {
      switch (displayEmotion.value) {
        case '焦虑':
          tipIndex = 1
          break
        case '难过':
          tipIndex = 2
          break
        case '生气':
          tipIndex = 8
          break
        case '疲惫':
          tipIndex = 5
          break
      }
    }

    bottomElement.innerHTML = `
      <div class="heart-tip">
        <div class="tip-title">心灵小贴士</div>
        <div class="tip-content">${tips[tipIndex]}</div>
        <div style="font-size: 12px; color: #9CA3AF; text-align: center; margin-top: 10px;">
          感谢使用心灵之旅，愿你的心情更加美好
        </div>
      </div>
    `

    const modalContent = document.querySelector('.modal-content')
    if (modalContent) {
      modalContent.appendChild(bottomElement)
      setTimeout(() => {
        bottomElement.classList.add('show')
      }, 100)
    }
  }, 500)
}

function formatDate(date: Date): string {
  const month = date.getMonth() + 1
  const day = date.getDate()
  return `${month}月${day}日`
}

function generateSerialNumber(): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  let result = ''
  for (let i = 0; i < 6; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

function getConfettiStyle(index: number): Record<string, string> {
  const colors = [
    '#FF6B6B', '#4ECDC4', '#FFE66D', '#6B5B95', '#88D8B0',
    '#FF8C94', '#FFC857', '#E9724C', '#C5D86D', '#255F85',
    '#A846A0', '#F9A03F', '#59CD90', '#3FA7D6', '#EF476F',
    '#FFD166', '#06D6A0', '#118AB2'
  ]
  const size = Math.floor(Math.random() * 12) + 5
  const left = Math.floor(Math.random() * 100)
  const animationDelay = Math.random() * 5
  const animationDuration = Math.random() * 4 + 3
  const rotation = Math.floor(Math.random() * 360)
  const opacity = Math.random() * 0.5 + 0.5

  return {
    backgroundColor: colors[index % colors.length],
    width: `${size}px`,
    height: `${size}px`,
    left: `${left}%`,
    animationDelay: `${animationDelay}s`,
    animationDuration: `${animationDuration}s`,
    transform: `rotate(${rotation}deg)`,
    opacity: String(opacity)
  }
}
</script>

<style scoped>
.ticket-generator-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(17, 24, 39, 0.5);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  opacity: 1;
}

.ticket-modal-enter-active,
.ticket-modal-leave-active {
  transition: opacity 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}

.ticket-modal-enter-active .modal-content,
.ticket-modal-leave-active .modal-content {
  transition:
    opacity 0.45s cubic-bezier(0.16, 1, 0.3, 1),
    transform 0.45s cubic-bezier(0.16, 1, 0.3, 1);
}

.ticket-modal-enter-from,
.ticket-modal-leave-to {
  opacity: 0;
}

.ticket-modal-enter-from .modal-content,
.ticket-modal-leave-to .modal-content {
  opacity: 0;
  transform: translateY(24px) scale(0.94) rotateX(-4deg);
}

.glass-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

/* 车票撕开动画相关样式 */
.ticket.torn-ticket {
  transform: perspective(1000px) rotateX(10deg) translateY(-20px);
  transition: transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow:
    0 20px 40px rgba(0, 0, 0, 0.2),
    0 0 0 1px rgba(255, 255, 255, 0.1);
  opacity: 0.9;
}

.modal-content {
  background-color: rgba(255, 255, 255, 0.94);
  border-radius: 22px;
  padding: 20px 16px;
  width: 95%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  box-shadow:
    0 20px 40px rgba(0, 0, 0, 0.2),
    0 0 0 1px rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

body.dark-mode .modal-content {
  background-color: rgba(30, 30, 30, 0.85);
  box-shadow:
    0 20px 40px rgba(0, 0, 0, 0.3),
    0 0 0 1px rgba(60, 60, 60, 0.3);
  border: 1px solid rgba(80, 80, 80, 0.2);
}

.close-button {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 20;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.9);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.close-button:hover {
  background-color: rgba(255, 255, 255, 1);
  transform: scale(1.1) rotate(90deg);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.ticket-container {
  padding: 0;
  overflow: hidden;
  opacity: 0;
  transform: scale(0.95) translateY(20px);
  transition:
    opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1),
    transform 0.8s cubic-bezier(0.16, 1, 0.3, 1);
  perspective: 1200px;
  margin: 0 auto;
  width: 100%;
  max-width: 440px;
  filter: drop-shadow(0 20px 30px rgba(0, 0, 0, 0.15));
  border-radius: 20px;
}

.ticket-container.show-ticket {
  opacity: 1;
  transform: scale(1) translateY(0);
}

.ticket {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 20px;
  overflow: hidden;
  position: relative;
  box-shadow:
    0 10px 30px rgba(0, 0, 0, 0.08),
    0 0 0 1px rgba(229, 231, 235, 0.6);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  transform-style: preserve-3d;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  border: 1px solid rgba(229, 231, 235, 0.8);
  background-image: none;
}

/* 主题样式 */
.theme-sunshine .ticket-header {
  background: linear-gradient(135deg, #ffd700, #ffa500);
}
.theme-healing .ticket-header {
  background: linear-gradient(135deg, #9370db, #8a2be2);
}
.theme-ocean .ticket-header {
  background: linear-gradient(135deg, #87ceeb, #4682b4);
}
.theme-comfort .ticket-header {
  background: linear-gradient(135deg, #4682b4, #1e3a8a);
}
.theme-release .ticket-header {
  background: linear-gradient(135deg, #ff6347, #dc2626);
}
.theme-rest .ticket-header {
  background: linear-gradient(135deg, #708090, #2f4f4f);
}

.ticket-header {
  background: linear-gradient(135deg, #3b82f6, #1e40af);
  color: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  position: relative;
  overflow: hidden;
}

.ticket-header-info {
  display: flex;
  justify-content: flex-end;
  padding: 8px 20px;
  background: rgba(249, 250, 251, 0.5);
}

.seat-number {
  background: rgba(59, 130, 246, 0.1);
  border-radius: 8px;
  padding: 4px 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.airline-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: 10px;
  position: relative;
  z-index: 2;
}

.airline-name {
  font-weight: 700;
  font-size: 18px;
  letter-spacing: 0.5px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.flight-info {
  text-align: right;
  position: relative;
  z-index: 2;
  background: rgba(255, 255, 255, 0.15);
  padding: 8px 12px;
  border-radius: 12px;
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.flight-label {
  font-size: 12px;
  opacity: 0.9;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 2px;
}

.flight-number {
  font-weight: 800;
  font-size: 20px;
  letter-spacing: 1px;
}

.ticket-body {
  padding: 25px;
}

body.dark-mode .ticket-body {
  background-image: none;
  background-color: rgba(30, 30, 30, 0.9);
}

body.dark-mode .route-info {
  background: rgba(40, 40, 40, 0.8);
}

.ticket-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.route-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: rgba(249, 250, 251, 0.8);
  padding: 20px 15px;
  border-radius: 16px;
  position: relative;
}

.departure-info,
.arrival-info {
  flex: 1;
  position: relative;
  z-index: 2;
  padding: 0 10px;
  text-align: center;
}

.departure-label,
.arrival-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 500;
}

.departure-name,
.arrival-name {
  font-weight: 700;
  font-size: 18px;
  color: #111827;
  position: relative;
}

body.dark-mode .departure-name,
body.dark-mode .arrival-name {
  color: #ffffff;
}

.departure-name::after,
.arrival-name::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%);
  width: 30px;
  height: 3px;
  border-radius: 3px;
  background-color: #3b82f6;
}

.flight-path {
  flex: 2;
  padding: 0 15px;
  position: relative;
  margin: 0 10px;
}

.path-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  height: 40px;
  margin: 10px 0;
}

.dot {
  width: 10px;
  height: 10px;
  background-color: #3b82f6;
  border-radius: 50%;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
  z-index: 2;
  position: relative;
}

.departure-dot {
  background-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
}

.arrival-dot {
  background-color: #f59e0b;
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.2);
}

.full-line {
  flex: 1;
  height: 3px;
  background: linear-gradient(90deg, #10b981, #3b82f6, #f59e0b);
  border-radius: 3px;
  position: relative;
  overflow: hidden;
}

.full-line::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent);
  animation: shimmerLine 3s infinite;
}

@keyframes shimmerLine {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.passenger-info {
  display: flex;
  justify-content: space-evenly;
  background: linear-gradient(135deg, rgba(249, 250, 251, 0.9), rgba(243, 244, 246, 0.9));
  padding: 18px 12px;
  border-radius: 16px;
  margin-bottom: 20px;
  position: relative;
  overflow: hidden;
}

.passenger-section {
  text-align: center;
  position: relative;
  z-index: 2;
  padding: 0 10px;
  flex: 1;
}

.passenger-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 500;
}

.passenger-value {
  font-weight: 700;
  font-size: 16px;
  color: #111827;
  letter-spacing: 0.5px;
}

body.dark-mode .passenger-value {
  color: #ffffff;
}

body.dark-mode .passenger-label {
  color: #d0d0d0;
}

.ticket-footer {
  padding: 25px 20px;
  border-top: 2px dashed rgba(229, 231, 235, 0.8);
  position: relative;
  background: linear-gradient(to bottom, rgba(249, 250, 251, 0.5), rgba(255, 255, 255, 0.8));
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.message-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message {
  font-size: 16px;
  font-weight: 500;
  color: #1f2937;
  line-height: 1.5;
  position: relative;
  padding: 0 20px;
  margin-bottom: 15px;
  word-wrap: break-word;
  overflow-wrap: break-word;
  max-width: 100%;
  text-align: center;
}

body.dark-mode .message {
  color: #ffffff;
  background-color: rgba(30, 30, 30, 0.6);
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 15px;
  justify-content: center;
  padding: 0 10px;
}

.keywords span {
  background-color: #f3f4f6;
  padding: 8px 16px;
  border-radius: 100px;
  font-size: 13px;
  color: #4b5563;
  font-weight: 500;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  white-space: nowrap;
  margin-bottom: 5px;
}

.keywords span:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.08);
}

.keyword-1 {
  background-color: #fef3c7 !important;
  color: #92400e !important;
  border: 1px solid rgba(146, 64, 14, 0.2);
}

.keyword-2 {
  background-color: #dbeafe !important;
  color: #1e40af !important;
  border: 1px solid rgba(30, 64, 175, 0.2);
}

.keyword-3 {
  background-color: #d1fae5 !important;
  color: #065f46 !important;
  border: 1px solid rgba(6, 95, 70, 0.2);
}

.barcode {
  height: 50px;
  background: repeating-linear-gradient(90deg, #555, #555 2px, transparent 2px, transparent 4px);
  margin-bottom: 20px;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
  margin-top: 5px;
}

.stamp {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 80px;
  height: 80px;
  border: 3px solid #ef4444;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #ef4444;
  font-weight: 700;
  transform: rotate(15deg);
  opacity: 0;
  transition: all 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.stamp.stamped {
  opacity: 1;
  transform: rotate(15deg) scale(1.05);
}

.stamp-date {
  font-size: 14px;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.stamp-serial {
  font-size: 12px;
  letter-spacing: 1px;
}

.ticket-tear {
  padding: 12px;
  background: linear-gradient(to bottom, #f9fafb, #f3f4f6);
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  border-bottom-left-radius: 20px;
  border-bottom-right-radius: 20px;
  border-top: 1px solid rgba(229, 231, 235, 0.8);
  position: relative;
  overflow: hidden;
}

.ticket-tear::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent);
  transform: translateX(-100%);
  transition: transform 0.6s ease;
}

.ticket-tear:hover {
  background: linear-gradient(to bottom, #f3f4f6, #e5e7eb);
  transform: translateY(2px);
}

.ticket-tear:hover::before {
  transform: translateX(100%);
}

.tear-line {
  width: 100%;
  height: 3px;
  background: repeating-linear-gradient(
    90deg,
    #d1d5db,
    #d1d5db 6px,
    transparent 6px,
    transparent 12px
  );
  margin-bottom: 8px;
  position: relative;
  overflow: hidden;
}

.tear-line::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.tear-hint {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
  letter-spacing: 0.5px;
  position: relative;
}

.tear-hint::before,
.tear-hint::after {
  content: '✂';
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
  font-size: 10px;
}

.tear-hint::before { left: -20px; }
.tear-hint::after { right: -20px; }

/* 撕开后的底部部分 */
.torn-bottom {
  margin-top: 25px;
  padding: 20px;
  background: linear-gradient(to bottom, #f9fafb, #f3f4f6);
  border-radius: 16px;
  box-shadow:
    0 10px 25px rgba(0, 0, 0, 0.1),
    0 0 0 1px rgba(229, 231, 235, 0.8);
  transform: perspective(1200px) rotateX(-8deg);
  opacity: 0;
  transition:
    opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1),
    transform 0.8s cubic-bezier(0.16, 1, 0.3, 1);
  border-top: 4px solid #3b82f6;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
}

.torn-bottom.show {
  opacity: 1;
  transform: perspective(1200px) rotateX(0);
}

.heart-tip {
  display: flex;
  flex-direction: column;
  gap: 15px;
  text-align: center;
}

.tip-title {
  font-size: 18px;
  font-weight: 700;
  color: #3b82f6;
  margin-bottom: 5px;
  display: inline-block;
  margin: 0 auto;
}

.tip-title::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: #3b82f6;
  border-radius: 2px;
}

.tip-content {
  font-size: 16px;
  line-height: 1.6;
  color: #4b5563;
  padding: 10px;
  background-color: rgba(255, 255, 255, 0.7);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin: 0 auto;
  max-width: 90%;
}

/* 五彩纸屑样式 */
.confetti-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 10;
  opacity: 0;
  transition: opacity 0.8s ease;
  overflow: hidden;
  perspective: 1000px;
}

.confetti-container.show-confetti {
  opacity: 1;
}

.confetti-piece {
  position: absolute;
  top: -50px;
  animation: confettiFall linear forwards;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  z-index: 15;
}

.confetti-piece:nth-child(3n) {
  border-radius: 50%;
  animation-duration: 4s;
}

.confetti-piece:nth-child(3n + 1) {
  border-radius: 4px;
  animation-duration: 6s;
}

.confetti-piece:nth-child(3n + 2) {
  clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
  animation-duration: 5s;
}

@keyframes confettiFall {
  0% {
    transform: translateY(0) rotate(0deg) scale(1);
    opacity: 0;
  }
  10% { opacity: 1; }
  25% {
    transform: translateY(25vh) rotate(90deg) scale(1.2) translateX(20px);
  }
  50% {
    opacity: 1;
    transform: translateY(50vh) rotate(180deg) scale(1) translateX(-10px);
  }
  75% {
    transform: translateY(75vh) rotate(270deg) scale(0.8) translateX(15px);
    opacity: 0.7;
  }
  100% {
    transform: translateY(100vh) rotate(360deg) scale(0.5) translateX(-5px);
    opacity: 0;
  }
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .modal-content {
    padding: 18px 12px;
    width: 98%;
  }

  .ticket-header {
    padding: 15px;
  }

  .airline-name {
    font-size: 16px;
  }

  .flight-number {
    font-size: 18px;
  }

  .ticket-body {
    padding: 20px 15px;
  }

  .route-info {
    padding: 15px 10px;
  }

  .departure-name,
  .arrival-name {
    font-size: 16px;
  }

  .passenger-info {
    padding: 15px 10px;
  }

  .passenger-value {
    font-size: 14px;
  }

  .ticket-footer {
    padding: 20px 15px;
  }

  .message {
    font-size: 14px;
    padding: 0 15px;
  }

  .keywords span {
    padding: 6px 12px;
    font-size: 12px;
  }

  .stamp {
    width: 70px;
    height: 70px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .ticket-modal-enter-active,
  .ticket-modal-leave-active,
  .ticket-modal-enter-active .modal-content,
  .ticket-modal-leave-active .modal-content,
  .ticket-container,
  .ticket,
  .stamp,
  .full-line::after,
  .tear-line::after,
  .confetti-piece {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
