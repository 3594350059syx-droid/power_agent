<template>
  <div class="chat-container">
    <div class="chat-list">
      <div
        v-for="item in msgList"
        :key="item.id"
        :class="item.type === 'user' ? 'user-box' : 'ai-box'"
      >
        {{ item.text }}
      </div>
    </div>
    <div class="chat-input-area">
      <el-input
        v-model="inputText"
        placeholder="输入问题，回车发送"
        @keyup.enter="sendMsg"
      />
      <el-button type="primary" @click="sendMsg">发送</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElLoading } from 'element-plus'
import { sendChatMsg } from '@/api/chat'

const inputText = ref('')
const msgList = ref([])
let id = 1

const sendMsg = async () => {
  if (!inputText.value.trim()) return
  const text = inputText.value
  msgList.value.push({
    id: id++,
    type: 'user',
    text
  })
  inputText.value = ''

  const loading = ElLoading.service({ text: 'AI思考中...' })
  try {
    const res = await sendChatMsg(text)
    msgList.value.push({
      id: id++,
      type: 'ai',
      text: res.answer
    })
  } catch (err) {
    msgList.value.push({
      id: id++,
      type: 'ai',
      text: '接口请求失败，可使用Mock数据调试'
    })
  } finally {
    loading.close()
  }
}
</script>

<style scoped>
.chat-container {
  width: 800px;
  margin: 20px auto;
}
.chat-list {
  height: 500px;
  border: 1px solid #eee;
  padding: 10px;
  overflow-y: auto;
  margin-bottom: 10px;
}
.user-box {
  text-align: right;
  background: #409eff;
  color: #fff;
  padding: 6px 12px;
  border-radius: 8px;
  margin: 4px 0;
}
.ai-box {
  text-align: left;
  background: #f5f5f5;
  padding: 6px 12px;
  border-radius: 8px;
  margin: 4px 0;
}
.chat-input-area {
  display: flex;
  gap: 10px;
}
</style>