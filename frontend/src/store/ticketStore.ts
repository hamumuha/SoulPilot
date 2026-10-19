import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Ticket } from '@/types'

// 解析车票日期字符串（格式：X月X日）为时间戳
export function parseTicketDate(dateStr: string): number {
  const currentYear = new Date().getFullYear()
  const match = dateStr.match(/(\d+)月(\d+)日/)
  if (match) {
    const month = parseInt(match[1]) - 1
    const day = parseInt(match[2])
    return new Date(currentYear, month, day).getTime()
  }
  return new Date(dateStr).getTime() || 0
}

// 按时间倒序排序：最新的车票排在最上面，久远的排在下面；同一天的票，后创建的排在前面
export function sortTicketsDesc(tickets: Ticket[], originalOrder: Ticket[]): Ticket[] {
  return [...tickets].sort((a, b) => {
    const diff = parseTicketDate(b.date) - parseTicketDate(a.date)
    if (diff !== 0) return diff
    return originalOrder.indexOf(b) - originalOrder.indexOf(a)
  })
}

export const useTicketStore = defineStore('ticketStore', () => {
  const ticketHistoryList = ref<Ticket[]>([])
  const currentTicket = ref<Ticket | null>(null)

  function addNewTicket(ticketData: Ticket) {
    ticketHistoryList.value.push(ticketData)
    currentTicket.value = ticketData
  }

  function deleteTicketById(ticketId: string) {
    ticketHistoryList.value = ticketHistoryList.value.filter((ticket) => ticket.id !== ticketId)
  }

  function clearAllTicketHistory() {
    ticketHistoryList.value = []
    currentTicket.value = null
  }

  return {
    ticketHistoryList,
    currentTicket,
    addNewTicket,
    deleteTicketById,
    clearAllTicketHistory,
  }
}, {
  persist: {
    key: 'ticketStore',
    storage: localStorage,
    paths: ['ticketHistoryList'],
  },
})
