import request from './index'

const isMock = import.meta.env.VITE_USE_MOCK === 'true'

// Mock 告警数据（5条以上）
const MOCK_ALARMS = [
  { id: 1, time: '2026-08-31 14:23:15', device_name: '2号机组', parameter: '主蒸汽温度', alarm_type: '温度超限', severity: 'high', current_value: 568, threshold: 550, status: 'active' },
  { id: 2, time: '2026-08-31 13:45:02', device_name: '3号汽轮机', parameter: '轴承振动', alarm_type: '振动异常', severity: 'medium', current_value: 0.08, threshold: 0.05, status: 'active' },
  { id: 3, time: '2026-08-31 12:10:33', device_name: '4号发电机', parameter: '定子温度', alarm_type: '温度偏高', severity: 'low', current_value: 112, threshold: 105, status: 'acknowledged' },
  { id: 4, time: '2026-08-31 10:05:21', device_name: '2号机组', parameter: '主蒸汽压力', alarm_type: '压力波动', severity: 'medium', current_value: 18.2, threshold: 17.5, status: 'active' },
  { id: 5, time: '2026-08-31 08:30:45', device_name: '3号汽轮机', parameter: '润滑油温度', alarm_type: '温度异常', severity: 'low', current_value: 78, threshold: 72, status: 'active' },
  { id: 6, time: '2026-08-30 22:15:08', device_name: '4号发电机', parameter: '无功功率', alarm_type: '功率越限', severity: 'high', current_value: 85, threshold: 75, status: 'acknowledged' },
  { id: 7, time: '2026-08-30 18:40:22', device_name: '2号机组', parameter: '炉膛温度', alarm_type: '温度超限', severity: 'high', current_value: 1280, threshold: 1250, status: 'active' }
]

/**
 * 获取告警列表
 * @param {string} severity - 严重等级: all / high / medium / low
 * @param {string} sort - 排序: time_desc / time_asc
 */
export function getAlarmList(severity = 'all', sort = 'time_desc') {
  if (isMock) {
    let list = [...MOCK_ALARMS]

    // 按严重等级过滤
    if (severity !== 'all') {
      list = list.filter(item => item.severity === severity)
    }

    // 按时间排序
    list.sort((a, b) => {
      const timeA = new Date(a.time).getTime()
      const timeB = new Date(b.time).getTime()
      return sort === 'time_desc' ? timeB - timeA : timeA - timeB
    })

    return Promise.resolve({
      success: true,
      data: list,
      total: list.length
    })
  }

  return request({
    url: '/alarm/list',
    method: 'get',
    params: { severity, sort }
  })
}

/**
 * 确认告警
 * @param {number} alarmId - 告警ID
 */
export function acknowledgeAlarm(alarmId) {
  if (isMock) {
    const alarm = MOCK_ALARMS.find(item => item.id === alarmId)
    if (alarm) {
      alarm.status = 'acknowledged'
    }
    return Promise.resolve({
      success: true,
      message: '告警已确认'
    })
  }

  return request({
    url: `/alarm/${alarmId}/acknowledge`,
    method: 'post'
  })
}