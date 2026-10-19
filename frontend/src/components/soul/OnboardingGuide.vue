<template>
  <div class="onboarding-container" v-if="showOnboarding">
    <!-- 遮罩层 -->
    <div class="onboarding-overlay" @click="skipOnboarding"></div>

    <!-- 步骤弹窗 -->
    <div class="onboarding-modal" :class="{ show: showModal }">
      <div class="modal-content glass-card">
        <div class="close-button" @click="skipOnboarding">
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M18 6L6 18"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
            <path
              d="M6 6L18 18"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </div>

        <!-- 步骤内容 -->
        <div class="step-content">
          <div v-if="currentStep === 1" class="step-slide">
            <div class="step-icon">✨</div>
            <h2>欢迎体验心灵之旅！</h2>
            <p>这是一个关注心理健康的旅程，让我们一起开始吧。</p>
            <div class="illustration">
              <div class="illustration-icon">🧠 💭 💫</div>
            </div>
            <button class="primary-button" @click="startRecordEmotion">开始记录情绪 🚀</button>
          </div>

          <div v-if="currentStep === 2" class="step-slide">
            <div class="step-icon">📝</div>
            <h2>记录你的心情和感受</h2>
            <p>选择一个情绪，分享你的感受，AI将为你提供个性化的心理健康建议。</p>
            <div class="illustration">
              <div class="emoji-row">
                <span>😊</span>
                <span>😌</span>
                <span>😢</span>
                <span>😰</span>
                <span>😠</span>
                <span>😩</span>
              </div>
            </div>
            <div class="highlight-area" ref="emotionInputHighlight"></div>
          </div>

          <div v-if="currentStep === 3" class="step-slide">
            <div class="step-icon">🎫</div>
            <h2>查看专属于你的心灵车票</h2>
            <p>每次分享都会生成一张独特的心灵车票，记录你的情感旅程。</p>
            <div class="illustration">
              <div class="ticket-illustration">
                <div class="mini-ticket">
                  <div class="mini-ticket-header"></div>
                  <div class="mini-ticket-body"></div>
                  <div class="mini-ticket-footer"></div>
                </div>
              </div>
            </div>
            <div class="highlight-area" ref="ticketHighlight"></div>
            <button class="primary-button" @click="viewTicketHistory">查看历史车票 🔍</button>
          </div>
        </div>

        <!-- 步骤导航 -->
        <div class="step-navigation">
          <div class="step-dots">
            <div
              v-for="step in 3"
              :key="step"
              :class="['step-dot', { active: currentStep === step }]"
              @click="goToStep(step)"
            ></div>
          </div>
          <button v-if="currentStep < 3" class="next-button" @click="nextStep">下一步</button>
          <button v-else class="finish-button" @click="finishOnboarding">开始体验 ✨</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'

interface TargetElements {
  emotionSelector: HTMLElement | null
  inputArea: HTMLElement | null
  historySection: HTMLElement | null
}

// 响应式数据
const showOnboarding = ref<boolean>(false)
const showModal = ref<boolean>(false)
const currentStep = ref<number>(1)
const storageKey = ref<string>('onboardingCompleted')
const fallbackCookieName = ref<string>('onboardingCompleted')

// DOM 引用
const emotionInputHighlight = ref<HTMLElement | null>(null)
const ticketHighlight = ref<HTMLElement | null>(null)

// 目标元素
const targetElements = ref<TargetElements>({
  emotionSelector: null,
  inputArea: null,
  historySection: null
})

// 生命周期
onMounted(() => {
  checkFirstVisit()

  nextTick(() => {
    try {
      targetElements.value.emotionSelector = document.querySelector('.emotion-selector')
      targetElements.value.inputArea = document.querySelector('.input-area')
      targetElements.value.historySection = document.querySelector('.history-section')
    } catch (error) {
      console.error('引导动画加载目标元素失败:', error)
    }
  })
})

// 定义事件
const emit = defineEmits<{
  'show-all-tickets': []
}>()

// 方法
function checkFirstVisit(): void {
  try {
    const completed = localStorage.getItem(storageKey.value)
    if (!completed) {
      setTimeout(() => {
        showOnboarding.value = true
        setTimeout(() => {
          showModal.value = true
        }, 100)
      }, 1000)
    }
  } catch (error) {
    console.warn('localStorage不可用，回退到Cookie:', error)
    checkCookie()
  }
}

function checkCookie() {
  const cookies = document.cookie.split(';')
  const cookieExists = cookies.some((cookie) => {
    return cookie.trim().startsWith(`${fallbackCookieName.value}=`)
  })

  if (!cookieExists) {
    setTimeout(() => {
      showOnboarding.value = true
      setTimeout(() => {
        showModal.value = true
      }, 100)
    }, 1000)
  }
}

function markAsCompleted() {
  try {
    localStorage.setItem(storageKey.value, 'true')
  } catch (error) {
    console.warn('localStorage不可用，回退到Cookie:', error)
    const expiryDate = new Date()
    expiryDate.setFullYear(expiryDate.getFullYear() + 1)
    document.cookie = `${fallbackCookieName.value}=true; expires=${expiryDate.toUTCString()}; path=/`
  }
}

function nextStep() {
  if (currentStep.value < 3) {
    currentStep.value++
    highlightTargetElement()
  }
}

function goToStep(step: number) {
  currentStep.value = step
  highlightTargetElement()
}

function highlightTargetElement() {
  nextTick(() => {
    const highlights = document.querySelectorAll('.element-highlight')
    highlights.forEach((el) => {
      el.classList.remove('element-highlight')
      ;(el as HTMLElement).style.transform = ''
    })

    try {
      if (
        currentStep.value === 2 &&
        targetElements.value.emotionSelector &&
        targetElements.value.inputArea
      ) {
        targetElements.value.emotionSelector.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        })

        setTimeout(() => {
          targetElements.value.emotionSelector!.classList.add('element-highlight')
          targetElements.value.inputArea!.classList.add('element-highlight')
          targetElements.value.emotionSelector!.style.transition =
            'transform 0.5s cubic-bezier(0.16, 1, 0.3, 1)'
          targetElements.value.emotionSelector!.style.transform = 'scale(1.02)'

          const textareaElement = targetElements.value.inputArea!.querySelector('textarea')
          if (textareaElement) {
            setTimeout(() => {
              textareaElement.focus()
            }, 800)
          }
        }, 400)
      } else if (currentStep.value === 3 && targetElements.value.historySection) {
        targetElements.value.historySection.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        })

        setTimeout(() => {
          targetElements.value.historySection!.classList.add('element-highlight')
          targetElements.value.historySection!.style.transition =
            'transform 0.5s cubic-bezier(0.16, 1, 0.3, 1)'
          targetElements.value.historySection!.style.transform = 'scale(1.02)'

          setTimeout(() => {
            targetElements.value.historySection!.style.transform = 'scale(1)'
          }, 500)
        }, 400)
      }
    } catch (error) {
      console.error('高亮目标元素失败:', error)
    }
  })
}

function startRecordEmotion() {
  markAsCompleted()
  closeOnboarding()

  if (targetElements.value.emotionSelector) {
    targetElements.value.emotionSelector.scrollIntoView({
      behavior: 'smooth',
      block: 'center'
    })

    setTimeout(() => {
      targetElements.value.emotionSelector!.classList.add('element-highlight')
      targetElements.value.emotionSelector!.style.transition =
        'transform 0.5s cubic-bezier(0.16, 1, 0.3, 1)'
      targetElements.value.emotionSelector!.style.transform = 'scale(1.02)'

      setTimeout(() => {
        targetElements.value.emotionSelector!.style.transform = 'scale(1)'
        setTimeout(() => {
          targetElements.value.emotionSelector!.classList.remove('element-highlight')
        }, 2500)
      }, 500)
    }, 600)
  }
}

function viewTicketHistory() {
  markAsCompleted()
  closeOnboarding()
  emit('show-all-tickets')

  if (targetElements.value.historySection) {
    targetElements.value.historySection.scrollIntoView({
      behavior: 'smooth',
      block: 'center'
    })

    setTimeout(() => {
      targetElements.value.historySection!.classList.add('element-highlight')
      targetElements.value.historySection!.style.transition =
        'transform 0.5s cubic-bezier(0.16, 1, 0.3, 1)'
      targetElements.value.historySection!.style.transform = 'scale(1.02)'

      setTimeout(() => {
        targetElements.value.historySection!.style.transform = 'scale(1)'
      }, 500)
    }, 400)
  }
}

function skipOnboarding() {
  markAsCompleted()
  closeOnboarding()
}

function finishOnboarding() {
  markAsCompleted()
  closeOnboarding()
}

function closeOnboarding() {
  showModal.value = false
  const modalElement = document.querySelector('.onboarding-modal') as HTMLElement | null

  if (modalElement) {
    modalElement.style.transition =
      'opacity 0.5s cubic-bezier(0.16, 1, 0.3, 1), transform 0.5s cubic-bezier(0.16, 1, 0.3, 1)'
    modalElement.style.opacity = '0'
    modalElement.style.transform = 'scale(0.95) translateY(10px)'
  }

  setTimeout(() => {
    showOnboarding.value = false
  }, 500)
}
</script>

<style scoped>
/* 引导动画容器 */
.onboarding-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}

/* 遮罩层 */
.onboarding-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  animation: fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 弹窗样式 */
.onboarding-modal {
  position: relative;
  z-index: 10000;
  width: 90%;
  max-width: 480px;
  opacity: 0;
  transform: scale(0.95) translateY(10px);
  transition:
    opacity 0.6s cubic-bezier(0.16, 1, 0.3, 1),
    transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: transform, opacity;
}

.onboarding-modal.show {
  opacity: 1;
  transform: scale(1);
}

/* 弹窗内容 */
.modal-content {
  width: 500px;
  max-width: 90%;
  padding: 30px;
  border-radius: 20px;
  position: relative;
  overflow: hidden;
  animation: modalFadeIn 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow:
    0 10px 40px rgba(0, 0, 0, 0.2),
    0 0 0 1px rgba(255, 255, 255, 0.1);
}

@keyframes modalFadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.glass-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.close-button {
  position: absolute;
  top: 15px;
  right: 15px;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: all 0.2s ease;
  color: #6b7280;
}

.close-button:hover {
  background: rgba(0, 0, 0, 0.1);
  color: #111827;
}

/* 步骤内容 */
.step-content {
  padding: 36px 28px;
  text-align: center;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.step-slide {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  animation: slideIn 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.illustration {
  margin: 20px 0;
  height: 120px;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.illustration-icon {
  font-size: 32px;
  letter-spacing: 10px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
  100% { transform: translateY(0px); }
}

.emoji-row {
  display: flex;
  gap: 15px;
  font-size: 28px;
}

.emoji-row span {
  animation: emojiPulse 2s infinite;
}

@keyframes emojiPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.15); }
}

.ticket-illustration {
  width: 100%;
  display: flex;
  justify-content: center;
}

.mini-ticket {
  width: 200px;
  height: 100px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  position: relative;
  animation: ticketFloat 3s ease-in-out infinite;
}

@keyframes ticketFloat {
  0% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-10px) rotate(2deg); }
  100% { transform: translateY(0) rotate(0deg); }
}

.mini-ticket-header {
  height: 25px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
}

.mini-ticket-body {
  height: 50px;
  padding: 5px;
  position: relative;
}

.mini-ticket-body:before {
  content: '';
  position: absolute;
  width: 70%;
  height: 8px;
  background: #e5e7eb;
  top: 15px;
  left: 15%;
  border-radius: 4px;
}

.mini-ticket-body:after {
  content: '';
  position: absolute;
  width: 40%;
  height: 8px;
  background: #e5e7eb;
  top: 30px;
  left: 30%;
  border-radius: 4px;
}

.mini-ticket-footer {
  height: 25px;
  background: #f3f4f6;
  position: relative;
}

.mini-ticket-footer:before {
  content: '';
  position: absolute;
  width: 30px;
  height: 30px;
  background: #ef4444;
  border-radius: 50%;
  right: 10px;
  top: -15px;
  opacity: 0.8;
}

.step-icon {
  font-size: 38px;
  margin-bottom: 18px;
  background: linear-gradient(135deg, #2196f3, #1976d2);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: float 3s ease-in-out infinite;
  filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.1));
}

.step-content h2 {
  font-size: 20px;
  margin-bottom: 16px;
  color: #2196f3;
}

.step-content p {
  font-size: 16px;
  line-height: 1.5;
  margin-bottom: 24px;
  color: #333;
}

/* 按钮样式 */
.primary-button {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.primary-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
  background: linear-gradient(135deg, #2563eb, #7c3aed);
}

/* 步骤导航 */
.step-navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-radius: 20px;
  padding: 18px 28px;
  margin-top: 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  background-color: rgba(248, 248, 250, 0.8);
  backdrop-filter: blur(5px);
}

.step-dots {
  display: flex;
  gap: 10px;
}

.step-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: rgba(0, 0, 0, 0.15);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.step-dot.active {
  background-color: #2196f3;
  transform: scale(1.2);
  box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2);
}

.next-button,
.finish-button {
  background-color: #4caf50;
  color: white;
  border: none;
  padding: 8px 18px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 2px 6px rgba(76, 175, 80, 0.3);
}

.next-button:hover,
.finish-button:hover {
  background-color: #43a047;
  transform: translateY(-1px);
}

/* 高亮区域 */
.highlight-area {
  position: relative;
  margin: 20px 0;
}

/* 元素高亮效果 */
.element-highlight {
  position: relative;
  z-index: 1000;
  animation: highlightPulse 2.5s infinite cubic-bezier(0.45, 0.05, 0.55, 0.95);
  box-shadow: 0 0 0 4px rgba(33, 150, 243, 0.5);
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes highlightPulse {
  0% { box-shadow: 0 0 0 0 rgba(33, 150, 243, 0.7); }
  50% { box-shadow: 0 0 0 8px rgba(33, 150, 243, 0.2); }
  100% { box-shadow: 0 0 0 0 rgba(33, 150, 243, 0); }
}

/* 响应式调整 */
@media (max-width: 768px) {
  .onboarding-modal {
    width: 95%;
    max-width: 350px;
  }

  .step-content h2 {
    font-size: 18px;
  }

  .step-content p {
    font-size: 14px;
  }
}
</style>
