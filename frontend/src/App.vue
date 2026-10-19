<template>
  <div class="app-root">
    <router-view />

    <!-- 登录后显示悬浮宠物和托盘菜单；对话与设置由独立路由页面承载 -->
    <div v-if="auth.isLoggedIn" class="pet-overlay" :class="{ 'click-through-mode': store.petSettings.clickThrough }">
      <PetWindow
        v-if="store.petVisible"
      />
      <TrayMenu />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { useAppStore } from '@/store/app'
import PetWindow from '@/components/PetWindow.vue'
import TrayMenu from '@/components/TrayMenu.vue'

const auth = useAuthStore()
const store = useAppStore()
const router = useRouter()

onMounted(async () => {
  // 启动时校验 token；若已登录则加载宠物设置 + 共享对话
  await auth.fetchMe()
  if (auth.isLoggedIn) {
    try {
      await store.loadSettings()
      await store.loadSharedConversation()
      if (store.petSettings.autoOpenChat && router.currentRoute.value.name === 'soul') {
        await router.push({ name: 'chat' })
      }
    } catch (e) {
      console.error('加载宠物设置/共享对话失败:', e)
    }
  }
})
</script>

<style scoped>
.click-through-mode :deep(.pet-window) {
  pointer-events: none;
}

.click-through-mode :deep(.pet-interactive-zone) {
  pointer-events: auto;
}
</style>
