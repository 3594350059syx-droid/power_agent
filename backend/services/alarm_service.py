from datetime import datetime, timedelta
from backend.database.connection import get_db
from backend.database.models import Device, SensorPoint, AlarmRecord, TimeseriesData
from backend.services.data_service import get_device_by_code_or_name, resolve_param_name, get_sensor_info
from algorithms.anomaly_detection.threshold_detector import ThresholdDetector
from algorithms.anomaly_detection.trend_detector import TrendDetector
from algorithms.anomaly_detection.risk_scorer import RiskScorer


def analyze_device_anomalies(device_id: str, hours: int = 24) -> dict:
    """
    分析设备异常情况
    
    参数:
        device_id: str - 设备编码（英文ID或中文名均可）
        hours: int - 分析时长（小时）
    
    返回:
        dict - 异常分析结果
            - device_id: str - 设备编码
            - risk_score: float - 综合风险评分
            - alarms: list - 告警列表
    """
    db = next(get_db())
    try:
        device = get_device_by_code_or_name(db, device_id)
        if not device:
            return {'error': f"Device '{device_id}' not found"}
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        sensors = db.query(SensorPoint).filter_by(device_id=device.id).all()
        
        alarms = []
        risk_scorer = RiskScorer()
        
        for sensor in sensors:
            threshold_detector = ThresholdDetector(
                threshold_high=sensor.threshold_high,
                threshold_low=sensor.threshold_low
            )
            
            trend_detector = TrendDetector(window_size=60, slope_threshold=0.5)
            
            query = db.query(
                TimeseriesData.recorded_at,
                TimeseriesData.value
            ).filter(
                TimeseriesData.device_id == device.id,
                TimeseriesData.sensor_id == sensor.id,
                TimeseriesData.recorded_at >= start_time,
                TimeseriesData.recorded_at <= end_time
            ).order_by(TimeseriesData.recorded_at)
            
            rows = query.all()
            if not rows:
                continue
            
            data_points = [(row.recorded_at, row.value) for row in rows]
            latest_value = rows[-1].value
            
            threshold_result = threshold_detector.detect(latest_value)
            trend_result = trend_detector.detect(data_points)
            
            resolved_param = resolve_param_name(sensor.point_name)
            
            if threshold_result['is_anomaly']:
                alarms.append({
                    'type': 'threshold',
                    'parameter': resolved_param,
                    'parameter_original': sensor.point_name,
                    'current_value': threshold_result['current_value'],
                    'threshold': threshold_result['threshold_value'],
                    'severity': threshold_result['severity'],
                    'score': threshold_result['score'],
                    'triggered_at': rows[-1].recorded_at.isoformat(),
                    'message': threshold_result['message']
                })
            
            if trend_result['is_anomaly']:
                alarms.append({
                    'type': 'trend',
                    'parameter': resolved_param,
                    'parameter_original': sensor.point_name,
                    'trend_desc': trend_result['trend_desc'],
                    'slope': trend_result['slope'],
                    'rate_of_change': trend_result['rate_of_change'],
                    'severity': trend_result['severity'],
                    'score': trend_result['score'],
                    'triggered_at': rows[-1].recorded_at.isoformat()
                })
        
        threshold_score = max([a['score'] for a in alarms if a['type'] == 'threshold'], default=0)
        trend_score = max([a['score'] for a in alarms if a['type'] == 'trend'], default=0)
        
        risk_result = risk_scorer.calculate_risk(
            {'score': threshold_score},
            {'score': trend_score}
        )
        
        return {
            'device_id': device.device_code,
            'device_name': device.device_name,
            'risk_score': risk_result['risk_score'],
            'risk_level': risk_result['level'],
            'alarms': alarms,
            'recommendations': risk_result['recommendations'],
            'analysis_time': end_time.isoformat(),
            'analysis_window_hours': hours
        }
    
    finally:
        db.close()


def get_alarm_history(device_id: str, hours: int = 24, status: str = None) -> list:
    """
    获取告警历史记录
    
    参数:
        device_id: str - 设备编码（英文ID或中文名均可）
        hours: int - 查询时长（小时）
        status: str - 告警状态过滤（可选）
    
    返回:
        list - 告警记录列表
    """
    db = next(get_db())
    try:
        device = get_device_by_code_or_name(db, device_id)
        if not device:
            return []
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        query = db.query(AlarmRecord).filter(
            AlarmRecord.device_id == device.id,
            AlarmRecord.triggered_at >= start_time,
            AlarmRecord.triggered_at <= end_time
        )
        
        if status:
            query = query.filter(AlarmRecord.status == status)
        
        rows = query.order_by(AlarmRecord.triggered_at.desc()).all()
        
        alarms = []
        for row in rows:
            sensor = db.query(SensorPoint).filter_by(id=row.sensor_id).first()
            resolved_param = resolve_param_name(sensor.point_name) if sensor else ''
            alarms.append({
                'id': row.id,
                'type': row.alarm_type,
                'parameter': resolved_param,
                'parameter_original': sensor.point_name if sensor else '',
                'severity': row.severity,
                'current_value': row.current_value,
                'threshold_value': row.threshold_value,
                'message': row.message,
                'status': row.status,
                'triggered_at': row.triggered_at.isoformat()
            })
        
        return alarms
    
    finally:
        db.close()


def acknowledge_alarm(alarm_id: int) -> bool:
    """
    确认告警
    
    参数:
        alarm_id: int - 告警ID
    
    返回:
        bool - 是否确认成功
    """
    db = next(get_db())
    try:
        alarm = db.query(AlarmRecord).filter_by(id=alarm_id).first()
        if alarm:
            alarm.status = 'acknowledged'
            db.commit()
            return True
        return False
    finally:
        db.close()


def get_all_pending_alarms() -> list:
    """
    获取所有待处理告警
    
    返回:
        list - 待处理告警列表
    """
    db = next(get_db())
    try:
        query = db.query(AlarmRecord).filter(AlarmRecord.status == 'pending')
        rows = query.order_by(AlarmRecord.triggered_at.desc()).all()
        
        alarms = []
        for row in rows:
            device = db.query(Device).filter_by(id=row.device_id).first()
            sensor = db.query(SensorPoint).filter_by(id=row.sensor_id).first()
            resolved_param = resolve_param_name(sensor.point_name) if sensor else ''
            alarms.append({
                'id': row.id,
                'device_code': device.device_code if device else '',
                'device_name': device.device_name if device else '',
                'device_type': device.device_type if device else '',
                'parameter': resolved_param,
                'parameter_original': sensor.point_name if sensor else '',
                'severity': row.severity,
                'current_value': row.current_value,
                'threshold_value': row.threshold_value,
                'message': row.message,
                'triggered_at': row.triggered_at.isoformat()
            })
        
        return alarms
    
    finally:
        db.close()