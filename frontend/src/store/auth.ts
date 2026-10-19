import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo } from '@/types'
import * as api from '@/api'

const TOKEN_KEY = 'hamu_token'
const USER_KEY = 'hamu_user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const user = ref<UserInfo | null>(loadUser())

  const isLoggedIn = computed(() => !!token.value && !!user.value)

  function loadUser(): UserInfo | null {
    try {
      const raw = localStorage.getItem(USER_KEY)
      return raw ? (JSON.parse(raw) as UserInfo) : null
    } catch {
      return null
    }
  }

  function persist(t: string | null, u: UserInfo | null) {
    token.value = t
    user.value = u
    if (t) localStorage.setItem(TOKEN_KEY, t)
    else localStorage.removeItem(TOKEN_KEY)
    if (u) localStorage.setItem(USER_KEY, JSON.stringify(u))
    else localStorage.removeItem(USER_KEY)
  }

  async function login(username: string, password: string) {
    const res = await api.login(username, password)
    persist(res.token, res.user)
  }

  async function register(username: string, password: string) {
    const res = await api.register(username, password)
    persist(res.token, res.user)
  }

  async function logout() {
    await api.logout()
    persist(null, null)
  }

  /** 启动时校验 token 是否仍然有效 */
  async function fetchMe() {
    if (!token.value) return false
    try {
      const me = await api.getMe()
      user.value = me
      localStorage.setItem(USER_KEY, JSON.stringify(me))
      return true
    } catch {
      persist(null, null)
      return false
    }
  }

  return { token, user, isLoggedIn, login, register, logout, fetchMe }
})
