<template>
  <div
    ref="petRef"
    class="pet-window"
    :class="{ 'click-through': store.petSettings.clickThrough }"
    :style="petStyle"
    @mousedown="onDragStart"
    @contextmenu.prevent="showContextMenu"
  >
    <div
      class="pet-image"
      :class="{ 'has-custom': !!store.petSettings.petImageUrl, 'drag-over': isDragOver }"
      :style="imageStyle"
      @dblclick="router.push({ name: 'chat' })"
      @dragover.prevent="onDragOver"
      @dragleave="isDragOver = false"
      @drop.prevent="onDrop"
    >
      <img v-if="petImageSrc" :src="petImageSrc" alt="宠物" />
      <span v-else class="pet-emoji">🐕</span>
      <div v-if="store.petSettings.clickThrough" class="pet-interactive-zone" title="点击穿透模式 - 此区域可交互" />
    </div>

    <div v-if="contextMenuVisible" class="context-menu" :style="menuStyle" @click.stop>
      <div class="menu-item" @click="handleMenu('chat')">💬 打开对话</div>
      <div class="menu-item" @click="handleMenu('settings')">⚙️ 设置</div>
      <div class="menu-divider" />
      <div class="menu-item" @click="handleMenu('clickThrough')">
        {{ store.petSettings.clickThrough ? '🔓 关闭穿透' : '👆 开启穿透' }}
      </div>
      <div class="menu-divider" />
      <div class="menu-item" @click="handleMenu('hide')">👁️ 隐藏宠物</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '@/store/app'
import { useRouter } from 'vue-router'

const store = useAppStore()
const router = useRouter()

const petRef = ref<HTMLElement | null>(null)
const contextMenuVisible = ref(false)
const menuPos = ref({ x: 0, y: 0 })
const isDragOver = ref(false)

const sizeMap = { small: 150, medium: 200, large: 250 }

const petImageSrc = computed(() => store.petSettings.petImageUrl || '/shiba.svg')

const imageStyle = computed(() => {
  const size = sizeMap[store.petSettings.petSize] || 200
  return { width: `${size}px`, height: `${size}px` }
})

const petStyle = computed(() => ({
  zIndex: store.petSettings.alwaysOnTop ? 99999 : 1000,
}))

const menuStyle = computed(() => ({
  left: `${menuPos.value.x}px`,
  top: `${menuPos.value.y}px`,
}))

let dragging = false
let dragOffset = { x: 0, y: 0 }
let petPosition = { x: 0, y: 0 }

function initPosition() {
  const size = sizeMap[store.petSettings.petSize] || 200
  petPosition = {
    x: window.innerWidth - size - 40,
    y: window.innerHeight - size - 80,
  }
  applyPosition()
}

function applyPosition() {
  if (!petRef.value) return
  let x = petPosition.x
  petRef.value.style.left = `${x}px`
  petRef.value.style.top = `${petPosition.y}px`
}

watch(() => store.petSettings.petSize, initPosition)

function onDragStart(e: MouseEvent) {
  if ((e.target as HTMLElement).closest('.context-menu')) return
  if (store.petSettings.clickThrough) return
  // 同步实际渲染位置（抽屉避让时渲染位置可能与记录位置不同），避免拖拽起跳
  if (petRef.value) {
    petPosition = { x: petRef.value.offsetLeft, y: petRef.value.offsetTop }
  }
  dragging = true
  dragOffset = { x: e.clientX - petPosition.x, y: e.clientY - petPosition.y }
  document.addEventListener('mousemove', onDragMove)
  document.addEventListener('mouseup', onDragEnd)
}

function onDragMove(e: MouseEvent) {
  if (!dragging) return
  petPosition = {
    x: Math.max(0, Math.min(window.innerWidth - 100, e.clientX - dragOffset.x)),
    y: Math.max(0, Math.min(window.innerHeight - 100, e.clientY - dragOffset.y)),
  }
  applyPosition()
}

function onDragEnd() {
  dragging = false
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
}

function showContextMenu(e: MouseEvent) {
  menuPos.value = { x: e.clientX, y: e.clientY }
  contextMenuVisible.value = true
}

function handleMenu(action: string) {
  contextMenuVisible.value = false
  switch (action) {
    case 'chat': router.push({ name: 'chat' }); break
    case 'settings': router.push({ name: 'settings' }); break
    case 'clickThrough':
      store.petSettings.clickThrough = !store.petSettings.clickThrough
      store.savePetSettings()
      break
    case 'hide': store.petVisible = false; break
  }
}

function onDragOver(e: DragEvent) {
  if (e.dataTransfer?.types.includes('Files')) isDragOver.value = true
}

function onDrop(e: DragEvent) {
  isDragOver.value = false
  const file = e.dataTransfer?.files[0]
  if (file?.type.startsWith('image/')) {
    const reader = new FileReader()
    reader.onload = () => {
      store.petSettings.petImageUrl = reader.result as string
      store.savePetSettings()
    }
    reader.readAsDataURL(file)
  }
}

function closeMenu() { contextMenuVisible.value = false }

onMounted(() => {
  initPosition()
  document.addEventListener('click', closeMenu)
  window.addEventListener('resize', initPosition)
})

onUnmounted(() => {
  document.removeEventListener('click', closeMenu)
  window.removeEventListener('resize', initPosition)
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
})
</script>

<style scoped>
.pet-window {
  position: fixed;
  cursor: move;
  user-select: none;
  background: transparent;
}

.pet-window.click-through {
  pointer-events: none;
}

.pet-image {
  border-radius: 50%;
  background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
  border: 4px solid #FF9800;
  box-shadow: 0 8px 20px rgba(255, 152, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  animation: float 3s ease-in-out infinite, breathe 2s ease-in-out infinite;
  transition: transform 0.2s;
}

.pet-image:hover { transform: scale(1.05); }
.pet-image.has-custom { background: transparent; }
.pet-image.drag-over { transform: scale(1.15); border-style: dashed; }

.pet-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.pet-emoji {
  font-size: 60px;
  animation: blink 4s infinite;
}

.pet-interactive-zone {
  position: absolute;
  bottom: 5px;
  right: 5px;
  width: 30px;
  height: 30px;
  background: rgba(255, 152, 0, 0.6);
  border-radius: 50%;
  pointer-events: auto;
  cursor: pointer;
  border: 2px solid #fff;
}

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  25% { transform: translateY(-10px) rotate(2deg); }
  50% { transform: translateY(-5px) rotate(-2deg); }
  75% { transform: translateY(-12px) rotate(1deg); }
}

@keyframes breathe {
  0%, 100% { box-shadow: 0 8px 20px rgba(255, 152, 0, 0.4); }
  50% { box-shadow: 0 12px 30px rgba(255, 152, 0, 0.6), 0 0 20px 10px rgba(255, 152, 0, 0.2); }
}

@keyframes blink {
  0%, 90%, 100% { opacity: 1; }
  95% { opacity: 0.1; }
}

.context-menu {
  position: fixed;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 100000;
  min-width: 160px;
  pointer-events: auto;
}

.menu-item {
  padding: 10px 15px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.menu-item:hover { background: #f5f5f5; }
.menu-divider { height: 1px; background: #eee; margin: 4px 0; }
</style>
