import request from './index'

/**
 * 获取实时监控数据
 * @param {string} deviceId - 设备ID
 * @returns {Promise}
 */
export function getLiveTelemetry(deviceId = 'boiler_002') {
  return request({
    url: '/telemetry/live',
    method: 'get',
    params: { device_id: deviceId }
  })
}

/**
 * 获取多台设备实时数据
 * @param {string[]} deviceIds - 设备ID列表
 * @returns {Promise}
 */
export function getMultipleDevicesTelemetry(deviceIds = ['boiler_002', 'turbine_003', 'generator_004']) {
  const promises = deviceIds.map(id => getLiveTelemetry(id))
  return Promise.all(promises)
}