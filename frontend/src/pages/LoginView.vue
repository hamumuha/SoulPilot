<template>
  <div class="login-page">
    <div class="login-card">
      <div class="logo">
        <img src="@/assets/logo.svg" alt="心灵之旅" />
        <h1>心灵之旅</h1>
        <p class="subtitle">登录后开启你的心灵旅程</p>
      </div>

      <el-tabs v-model="activeTab" class="login-tabs">
        <el-tab-pane label="登录" name="login">
          <el-form @submit.prevent="onSubmit" class="login-form">
            <el-input
              v-model="username"
              placeholder="用户名"
              size="large"
              :prefix-icon="User"
              @keyup.enter="onSubmit"
            />
            <el-input
              v-model="password"
              type="password"
              placeholder="密码"
              size="large"
              :prefix-icon="Lock"
              show-password
              @keyup.enter="onSubmit"
            />
            <el-button
              type="primary"
              size="large"
              class="submit-btn"
              :loading="loading"
              @click="onSubmit"
            >
              {{ loading ? '登录中...' : '登录' }}
            </el-button>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form @submit.prevent="onSubmit" class="login-form">
            <el-input
              v-model="username"
              placeholder="用户名（至少 2 个字符）"
              size="large"
              :prefix-icon="User"
              @keyup.enter="onSubmit"
            />
            <el-input
              v-model="password"
              type="password"
              placeholder="密码（至少 4 个字符）"
              size="large"
              :prefix-icon="Lock"
              show-password
              @keyup.enter="onSubmit"
            />
            <el-button
              type="primary"
              size="large"
              class="submit-btn"
              :loading="loading"
              @click="onSubmit"
            >
              {{ loading ? '注册中...' : '注册并登录' }}
            </el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>

      <p class="tip">欢迎注册和登录“ SoulPilot · 心灵领航员 ”网页</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const auth = useAuthStore()

const activeTab = ref<'login' | 'register'>('login')
const username = ref('')
const password = ref('')
const loading = ref(false)

watch(activeTab, (tab) => {
  if (tab === 'register') {
    username.value = ''
    password.value = ''
  }
})

async function onSubmit() {
  const name = username.value.trim()
  const pwd = password.value

  if (name.length < 2) {
    ElMessage.warning('用户名至少 2 个字符')
    return
  }
  if (pwd.length < 4) {
    ElMessage.warning('密码至少 4 个字符')
    return
  }

  loading.value = true
  try {
    if (activeTab.value === 'login') {
      await auth.login(name, pwd)
      ElMessage.success('登录成功，欢迎回来')
    } else {
      await auth.register(name, pwd)
      ElMessage.success('注册成功，已自动登录')
    }
    router.replace('/')
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '操作失败'
    ElMessage.error(typeof msg === 'string' ? msg : '操作失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5f9ff 0%, #f7f9f7 50%, #faf7fa 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 40px 32px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.4);
}

.logo {
  text-align: center;
  margin-bottom: 24px;
}

.logo img {
  width: 72px;
  height: 72px;
  display: block;
  margin: 0 auto 12px;
}

.logo h1 {
  font-size: 26px;
  color: #1a73e8;
  margin: 0 0 6px;
  font-weight: 700;
}

.subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.login-tabs {
  margin-top: 8px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 12px;
}

.submit-btn {
  width: 100%;
  margin-top: 6px;
  background: linear-gradient(135deg, #3b82f6, #1a73e8);
  border: none;
  font-size: 16px;
  height: 44px;
  border-radius: 10px;
}

.submit-btn:hover {
  background: linear-gradient(135deg, #2563eb, #1557b8);
}

.tip {
  text-align: center;
  font-size: 12px;
  color: #9ca3af;
  margin: 20px 0 0;
  line-height: 1.6;
}

:deep(.el-tabs__nav) {
  width: 100%;
}

:deep(.el-tabs__item) {
  flex: 1;
  text-align: center;
  font-size: 15px;
}

:deep(.el-tabs__active-bar) {
  background-color: #1a73e8;
}

:deep(.el-input__wrapper) {
  border-radius: 10px;
}
</style>
