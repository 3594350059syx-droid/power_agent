<template>
  <div class="chat-view">
    <el-card class="chat-card" shadow="hover">
      <!-- 头部 -->
      <template #header>
        <div class="chat-header">
          <div class="header-left">
            <el-avatar :size="40" style="background: #1890ff">
              <el-icon><ChatDotRound /></el-icon>
            </el-avatar>
            <span class="title">AI 智能助手</span>
            <el-tag :type="isConnected ? 'success' : 'danger'" size="small">
              {{ isConnected ? '在线' : '离线' }}
            </el-tag>
          </div>
          <el-button type="text" @click="clearMessages">
            <el-icon><Delete /></el-icon> 清空对话
          </el-button>
        </div>
      </template>

      <!-- 快捷指令 -->
      <QuickCommands @select="handleCommandSelect" />

      <!-- 消息列表 -->
      <div class="message-list" ref="messageListRef">
        <ChatMessage
          v-for="(msg, index) in messages"
          :key="index"
          :role="msg.role"
          :content="msg.content"
          :diagnosis="msg.diagnosis"
          :time="msg.time"
        />

        <!-- Loading 状态 -->
        <div v-if="isLoading" class="message-item assistant">
          <div class="message-avatar">
            <el-avatar :size="36">🤖</el-avatar>
          </div>
          <div class="message-body">
            <div class="message-bubble typing">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="messages.length === 0" class="empty-state">
          <el-empty description="开始你的第一次对话吧" />
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="2"
          placeholder="请输入您的问题，按 Enter 发送..."
          @keydown.enter.prevent="sendMessage"
          resize="none"
          maxlength="2000"
          show-word-limit
        />
        <el-button
          type="primary"
          :loading="isLoading"
          :disabled="!inputText.trim()"
          @click="sendMessage"
        >
          <el-icon><Promotion /></el-icon> 发送
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { ChatDotRound, Delete, Promotion } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import ChatMessage from '@/components/ChatMessage.vue'
import QuickCommands from '@/components/QuickCommands.vue'
import { sendChatMessage } from '@/api/agent'

// ============ 状态 ============
const messages = ref([])
const inputText = ref('')
const isLoading = ref(false)
const isConnected = ref(true)
const messageListRef = ref(null)

// ============ 方法 ============

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  const el = messageListRef.value
  if (el) {
    el.scrollTop = el.scrollHeight
  }
}

// 添加消息
const addMessage = (role, content, diagnosis = null) => {
  messages.value.push({
    role,
    content,
    diagnosis,
    time: new Date().toLocaleTimeString()
  })
  scrollToBottom()
}

// 发送消息
const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return

  addMessage('user', text)
  inputText.value = ''
  isLoading.value = true

  try {
    const res = await sendChatMessage(text)
    
    // ✅ 关键：用 res.success 判断
    if (res.success) {
      const reply = res.data?.reply || '抱歉，我没有理解您的问题。'
      addMessage('assistant', reply)
      isConnected.value = true
    } else {
      const errorMsg = res.message || '请求失败，请稍后重试'
      addMessage('assistant', `❌ ${errorMsg}`)
      isConnected.value = false
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    addMessage('assistant', '❌ 请求失败，请检查后端服务是否正常运行（localhost:8000）')
    isConnected.value = false
  } finally {
    isLoading.value = false
  }
}

// 快捷指令选择
const handleCommandSelect = (value) => {
  inputText.value = value
  const textarea = document.querySelector('.el-textarea__inner')
  if (textarea) {
    textarea.focus()
  }
}

// 清空对话
const clearMessages = () => {
  messages.value = []
  ElMessage.success('对话已清空')
}

// ============ 生命周期 ============
onMounted(() => {
  addMessage('assistant', '您好！我是 Power-Agent 电力运维助手，有什么可以帮您？')
})
</script>

<style scoped>
.chat-view {
  max-width: 1000px;
  margin: 0 auto;
  height: calc(100vh - 140px);
}

.chat-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px 20px 20px 20px;
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left .title {
  font-size: 16px;
  font-weight: 600;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px 8px 8px 8px;
  background: #fafafa;
  border-radius: 8px;
  margin: 8px 0 12px 0;
  min-height: 200px;
  max-height: 500px;
}

.message-list::-webkit-scrollbar {
  width: 4px;
}

.message-list::-webkit-scrollbar-thumb {
  background: #d9d9d9;
  border-radius: 4px;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  animation: fadeIn 0.3s ease;
}

.message-item.assistant {
  justify-content: flex-start;
}

.message-avatar {
  flex-shrink: 0;
}

.message-body {
  max-width: 75%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e8e8e8;
  word-wrap: break-word;
  line-height: 1.7;
  font-size: 14px;
}

.typing {
  display: flex;
  gap: 4px;
  padding: 8px 16px;
  min-width: 52px;
}

.typing span {
  width: 8px;
  height: 8px;
  background: #999;
  border-radius: 50%;
  animation: bounce 1.4s infinite both;
}

.typing span:nth-child(1) { animation-delay: 0s; }
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-8px); }
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #999;
}

.input-area {
  display: flex;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid #e8e8e8;
  flex-shrink: 0;
}

.input-area .el-textarea {
  flex: 1;
}

.input-area .el-button {
  align-self: flex-end;
  padding: 10px 28px;
  border-radius: 8px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>