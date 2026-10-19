<template>
  <div class="tray-menu" :class="{ expanded: isExpanded }">
    <div class="tray-toggle" @click="isExpanded = !isExpanded" title="托盘菜单">
      <span class="tray-icon">🐾</span>
    </div>
    <transition name="tray-slide">
      <div v-if="isExpanded" class="tray-items">
        <div class="tray-item" title="打开对话" @click="openChat">
          <el-icon><ChatDotRound /></el-icon>
          <span>对话</span>
        </div>
        <div class="tray-item" title="设置" @click="openSettings">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </div>
        <div class="tray-item" :title="store.petSettings.clickThrough ? '关闭穿透' : '开启穿透'" @click="toggleClickThrough">
          <el-icon><Pointer /></el-icon>
          <span>{{ store.petSettings.clickThrough ? '穿透开' : '穿透关' }}</span>
        </div>
        <div class="tray-item" :title="store.petVisible ? '隐藏宠物' : '显示宠物'" @click="togglePet">
          <el-icon><View v-if="store.petVisible" /><Hide v-else /></el-icon>
          <span>{{ store.petVisible ? '隐藏' : '显示' }}</span>
        </div>
        <div class="tray-item" :title="store.petSettings.alwaysOnTop ? '取消置顶' : '始终置顶'" @click="toggleAlwaysOnTop">
          <el-icon><Top /></el-icon>
          <span>置顶</span>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ChatDotRound, Setting, Pointer, View, Hide, Top } from '@element-plus/icons-vue'
import { useAppStore } from '@/store/app'
import { useRouter } from 'vue-router'

const store = useAppStore()
const router = useRouter()
const isExpanded = ref(false)

function openChat() { router.push({ name: 'chat' }); isExpanded.value = false }
function openSettings() { router.push({ name: 'settings' }); isExpanded.value = false }

function toggleClickThrough() {
  store.petSettings.clickThrough = !store.petSettings.clickThrough
  store.savePetSettings()
}

function togglePet() { store.petVisible = !store.petVisible }

function toggleAlwaysOnTop() {
  store.petSettings.alwaysOnTop = !store.petSettings.alwaysOnTop
  store.savePetSettings()
}
</script>

<style scoped>
.tray-menu {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 100001;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  pointer-events: auto;
  transition: right 0.25s ease;
}

.tray-toggle {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #FF9800, #F57C00);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(255, 152, 0, 0.5);
  transition: transform 0.2s, box-shadow 0.2s;
}

.tray-toggle:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(255, 152, 0, 0.6);
}

.tray-icon { font-size: 22px; }

.tray-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(255, 152, 0, 0.3);
}

.tray-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #606266;
  transition: background 0.2s, color 0.2s;
  white-space: nowrap;
}

.tray-item:hover {
  background: #FFF3E0;
  color: #FF9800;
}

.tray-slide-enter-active, .tray-slide-leave-active {
  transition: all 0.25s ease;
}

.tray-slide-enter-from, .tray-slide-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

:root.dark .tray-items {
  background: rgba(26, 26, 46, 0.95);
  border-color: rgba(255, 152, 0, 0.2);
}

:root.dark .tray-item { color: #c0c4cc; }
:root.dark .tray-item:hover { background: rgba(255, 152, 0, 0.15); color: #FF9800; }
</style>
