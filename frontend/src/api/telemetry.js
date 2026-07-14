import request from './request'

export function getLiveTelemetry(device_id = 'dev_001') {
  return request.get('/telemetry/live', {
    params: { device_id }
  })
}
