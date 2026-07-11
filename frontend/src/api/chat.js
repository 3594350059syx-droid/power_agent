import request from './request'

export function sendChatMsg(query, device_id = 'dev_001') {
  return request.post('/agent/chat', {
    query,
    device_id
  })
}