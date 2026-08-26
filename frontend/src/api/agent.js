// Agent 对话 API
import request from '@/api/index'

/**
 * AI 对话接口
 * @param {string} message - 用户输入的消息
 * @param {string} mode - 对话模式: chat / diagnose / predict
 * @returns {Promise}
 */
export function sendChatMessage(message, mode = 'chat') {
  if (import.meta.env.VITE_USE_MOCK === 'true') {
    return Promise.resolve({
      success: true,
      message: 'mock',
      data: {
        reply: `【Mock 模式】已收到您的问题：${message}`,
        diagnosis: null
      }
    })
  }

  return request({
    url: '/agent/chat',
    method: 'post',
    data: { message, mode }
  })
}