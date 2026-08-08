<template>
  <div class="chat-message" :class="role">
    <div class="message-avatar">
      <el-avatar :size="36">
        {{ role === 'user' ? '👤' : '🤖' }}
      </el-avatar>
    </div>
    <div class="message-body">
      <div class="message-bubble" v-html="renderedContent"></div>
      <!-- 诊断卡片（仅 Agent 消息且有诊断数据时显示） -->
      <DiagnosisCard v-if="role === 'assistant' && diagnosis" :data="diagnosis" />
      <div class="message-time">{{ time }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import DiagnosisCard from './DiagnosisCard.vue'

// 配置 marked
marked.setOptions({
  highlight: (code, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
  gfm: true
})

const props = defineProps({
  role: {
    type: String,
    required: true,
    validator: (val) => ['user', 'assistant'].includes(val)
  },
  content: {
    type: String,
    default: ''
  },
  diagnosis: {
    type: Object,
    default: null
  },
  time: {
    type: String,
    default: ''
  }
})

const renderedContent = computed(() => {
  if (!props.content) return ''
  try {
    return marked(props.content)
  } catch {
    return props.content
  }
})
</script>

<style scoped>
.chat-message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  animation: fadeIn 0.3s ease;
}

.chat-message.user {
  flex-direction: row-reverse;
}

.chat-message.user .message-bubble {
  background: #1890ff;
  color: #fff;
}

.chat-message.assistant .message-bubble {
  background: #f0f2f5;
  color: #333;
}

.message-avatar {
  flex-shrink: 0;
}

.message-body {
  max-width: 70%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  word-wrap: break-word;
  line-height: 1.7;
  font-size: 14px;
}

.message-bubble :deep(pre) {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px 16px;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.6;
}

.message-bubble :deep(code) {
  background: rgba(0, 0, 0, 0.08);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.message-bubble :deep(pre code) {
  background: transparent;
  padding: 0;
  border-radius: 0;
}

.message-bubble :deep(p) {
  margin: 6px 0;
}

.message-bubble :deep(ul), .message-bubble :deep(ol) {
  padding-left: 20px;
  margin: 6px 0;
}

.message-bubble :deep(blockquote) {
  border-left: 4px solid #1890ff;
  padding-left: 12px;
  margin: 8px 0;
  color: #666;
}

.message-time {
  font-size: 12px;
  color: #999;
  padding: 0 4px;
}

.user .message-time {
  text-align: right;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>