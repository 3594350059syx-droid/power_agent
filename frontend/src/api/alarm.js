import request from './index'

const isMock = import.meta.env.VITE_USE_MOCK === 'true'

// Mock 告警数据使用与 GET /alarm/list 相同的字段和状态枚举。
const MOCK_ALARMS = [
  { id: 1, triggered_at: '2026-08-31T14:23:15', device_name: '2号锅炉', parameter: 'steam_temp', parameter_name: '主蒸汽温度', alarm_type: 'threshold', severity: 'high', current_value: 568, threshold_value: 550, status: 'pending' },
  { id: 2, triggered_at: '2026-08-31T13:45:02', device_name: '3号汽轮机', parameter: 'vibration', parameter_name: '振动', alarm_type: 'trend', severity: 'medium', current_value: 0.08, threshold_value: 0.05, status: 'pending' },
  { id: 3, triggered_at: '2026-08-31T12:10:33', device_name: '4号发电机', parameter: 'stator_temp', parameter_name: '定子温度', alarm_type: 'threshold', severity: 'low', current_value: 112, threshold_value: 105, status: 'acknowledged' },
  { id: 4, triggered_at: '2026-08-31T10:05:21', device_name: '2号锅炉', parameter: 'steam_pressure', parameter_name: '主蒸汽压力', alarm_type: 'trend', severity: 'medium', current_value: 18.2, threshold_value: 17.5, status: 'pending' },
  { id: 5, triggered_at: '2026-08-31T08:30:45', device_name: '3号汽轮机', parameter: 'bearing_temp', parameter_name: '轴承温度', alarm_type: 'threshold', severity: 'low', current_value: 78, threshold_value: 72, status: 'pending' },
  { id: 6, triggered_at: '2026-08-30T22:15:08', device_name: '4号发电机', parameter: 'reactive_power', parameter_name: '无功功率', alarm_type: 'threshold', severity: 'high', current_value: 85, threshold_value: 75, status: 'acknowledged' },
  { id: 7, triggered_at: '2026-08-30T18:40:22', device_name: '2号锅炉', parameter: 'furnace_temp', parameter_name: '炉膛温度', alarm_type: 'threshold', severity: 'high', current_value: 1280, threshold_value: 1250, status: 'pending' }
]

const normalizeAlarm = (alarm) => ({
  ...alarm,
  triggered_at: alarm.triggered_at || alarm.time || '',
  parameter_name: alarm.parameter_name || alarm.parameter || '',
  alarm_type: alarm.alarm_type || alarm.type || '',
  threshold_value: alarm.threshold_value ?? alarm.threshold ?? null,
  status: alarm.status === 'active' ? 'pending' : (alarm.status || 'pending')
})

const normalizeAlarmListResponse = (response) => {
  const rawData = response.data || {}
  const alarms = Array.isArray(rawData) ? rawData : (rawData.alarms || [])
  return {
    ...response,
    data: {
      alarms: alarms.map(normalizeAlarm),
      total: Array.isArray(rawData) ? (response.total ?? alarms.length) : (rawData.total ?? alarms.length)
    }
  }
}

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
      const timeA = new Date(a.triggered_at).getTime()
      const timeB = new Date(b.triggered_at).getTime()
      return sort === 'time_desc' ? timeB - timeA : timeA - timeB
    })

    return Promise.resolve(normalizeAlarmListResponse({
      success: true,
      data: { alarms: list, total: list.length },
      total: list.length
    }))
  }

  return request({
    url: '/alarm/list',
    method: 'get',
    params: { severity, sort }
  }).then(normalizeAlarmListResponse)
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