from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import Device, SensorPoint, TimeseriesData

PARAM_MAP = {
    'speed': 'rpm',
    'active_power': 'power',
    'rpm': 'rpm',
    'power': 'power',
    'steam_temp': 'steam_temp',
    'steam_pressure': 'steam_pressure',
    'furnace_temp': 'furnace_temp',
    'water_flow': 'water_flow',
    'bearing_temp': 'bearing_temp',
    'vibration': 'vibration',
    'oil_pressure': 'oil_pressure',
    'stator_temp': 'stator_temp',
    'rotor_temp': 'rotor_temp',
    'power_factor': 'power_factor',
}


def resolve_param_name(parameter: str) -> str:
    return PARAM_MAP.get(parameter, parameter)


def get_device_by_code_or_name(db: Session, identifier: str) -> Device:
    device = db.query(Device).filter_by(device_code=identifier).first()
    if device:
        return device
    device = db.query(Device).filter_by(device_name=identifier).first()
    return device


def get_sensor_info(db: Session, device_id: int, parameter: str):
    resolved_name = resolve_param_name(parameter)
    sensor = db.query(SensorPoint).filter(
        SensorPoint.device_id == device_id,
        SensorPoint.point_name == resolved_name
    ).first()
    return sensor


def _empty_result(device_id: str = '', parameter: str = '', error: str = None) -> dict:
    """Week 2 契约：无匹配数据时返回空数组而非异常，同时附带 error 供调试"""
    result = {
        'device_id': device_id,
        'parameter': parameter,
        'unit': '',
        'data': [],
        'stats': {'min': None, 'max': None, 'avg': None, 'count': 0},
    }
    if error:
        result['error'] = error
    return result


def query_timeseries_data(params: dict) -> dict:
    device_id = params.get('device_id', '')
    parameter = params.get('parameter', '')
    start_time = params.get('start_time')
    end_time = params.get('end_time')
    time_range_hours = params.get('time_range_hours', None)
    aggregation = params.get('aggregation', None)

    db = next(get_db())
    try:
        device = get_device_by_code_or_name(db, device_id)
        if not device:
            return _empty_result(device_id, parameter, f"Device '{device_id}' not found")

        sensor = get_sensor_info(db, device.id, parameter)
        if not sensor:
            return _empty_result(device.device_code, parameter,
                                 f"Parameter '{parameter}' not found for device '{device.device_code}'")

        # 兼容两种传参方式：优先显式 start_time/end_time；未传时用 time_range_hours 推导
        end_dt = None
        start_dt = None
        if end_time:
            end_dt = datetime.fromisoformat(end_time)
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
        elif time_range_hours is not None:
            end_dt = end_dt or datetime.now()
            start_dt = end_dt - timedelta(hours=time_range_hours)

        resolved_param = resolve_param_name(parameter)

        if aggregation:
            return aggregate_query(db, device, sensor, start_dt, end_dt, aggregation, resolved_param)

        query = db.query(
            TimeseriesData.recorded_at,
            TimeseriesData.value
        ).filter(
            TimeseriesData.device_id == device.id,
            TimeseriesData.sensor_id == sensor.id
        )

        if start_dt:
            query = query.filter(TimeseriesData.recorded_at >= start_dt)
        if end_dt:
            query = query.filter(TimeseriesData.recorded_at <= end_dt)

        rows = query.order_by(TimeseriesData.recorded_at).all()
        data = [{'time': row.recorded_at.isoformat(), 'value': row.value} for row in rows]

        stats_query = db.query(
            func.min(TimeseriesData.value),
            func.max(TimeseriesData.value),
            func.avg(TimeseriesData.value),
            func.count(TimeseriesData.value)
        ).filter(
            TimeseriesData.device_id == device.id,
            TimeseriesData.sensor_id == sensor.id
        )

        if start_dt:
            stats_query = stats_query.filter(TimeseriesData.recorded_at >= start_dt)
        if end_dt:
            stats_query = stats_query.filter(TimeseriesData.recorded_at <= end_dt)

        stats_result = stats_query.first()
        # 不能用 "if stats_result[0]" 判断 None，否则恰为 0 的合法值会被误判为 None
        return {
            'device_id': device.device_code,
            'device_name': device.device_name,
            'parameter': resolved_param,
            'unit': sensor.unit,
            'data': data,
            'stats': {
                'min': round(stats_result[0], 2) if stats_result[0] is not None else None,
                'max': round(stats_result[1], 2) if stats_result[1] is not None else None,
                'avg': round(stats_result[2], 2) if stats_result[2] is not None else None,
                'count': stats_result[3] if stats_result[3] is not None else 0,
            }
        }

    finally:
        db.close()


def aggregate_query(db, device, sensor, start_dt, end_dt, aggregation: str, resolved_param: str):
    """
    SQLAlchemy 2.x 兼容的聚合查询。
    直接构建带 date_trunc 的聚合查询，避免已移除的子查询包装方法。
    """
    interval_map = {
        '5min': '5 minutes',
        '15min': '15 minutes',
        '1h': '1 hour',
        '6h': '6 hours',
        '1d': '1 day',
    }
    interval = interval_map.get(aggregation, '1 hour')

    bucket = func.date_trunc(interval, TimeseriesData.recorded_at).label('bucket')
    query = db.query(
        bucket,
        func.avg(TimeseriesData.value).label('avg_value'),
        func.min(TimeseriesData.value).label('min_value'),
        func.max(TimeseriesData.value).label('max_value'),
        func.count(TimeseriesData.value).label('count'),
    ).filter(
        TimeseriesData.device_id == device.id,
        TimeseriesData.sensor_id == sensor.id,
    )

    if start_dt:
        query = query.filter(TimeseriesData.recorded_at >= start_dt)
    if end_dt:
        query = query.filter(TimeseriesData.recorded_at <= end_dt)

    rows = query.group_by(bucket).order_by(bucket).all()
    data = [{
        'time': row.bucket.isoformat(),
        'value': round(row.avg_value, 2) if row.avg_value is not None else None,
        'min': round(row.min_value, 2) if row.min_value is not None else None,
        'max': round(row.max_value, 2) if row.max_value is not None else None,
        'count': row.count if row.count is not None else 0,
    } for row in rows]

    return {
        'device_id': device.device_code,
        'device_name': device.device_name,
        'parameter': resolved_param,
        'unit': sensor.unit,
        'data': data,
        'aggregation': aggregation,
        'stats': {
            'count': sum(r['count'] for r in data),
        },
    }


def query_multiple_devices(params: dict) -> dict:
    device_ids = params.get('device_ids', [])
    parameter = params.get('parameter', '')
    start_time = params.get('start_time')
    end_time = params.get('end_time')
    
    db = next(get_db())
    try:
        results = {}
        resolved_param = resolve_param_name(parameter)
        
        for device_id in device_ids:
            device = get_device_by_code_or_name(db, device_id)
            if not device:
                results[device_id] = {'error': f"Device '{device_id}' not found"}
                continue
            
            sensor = get_sensor_info(db, device.id, parameter)
            if not sensor:
                results[device_id] = {'error': f"Parameter '{parameter}' not found"}
                continue
            
            query = db.query(
                TimeseriesData.recorded_at,
                TimeseriesData.value
            ).filter(
                TimeseriesData.device_id == device.id,
                TimeseriesData.sensor_id == sensor.id
            )
            
            if start_time:
                query = query.filter(TimeseriesData.recorded_at >= datetime.fromisoformat(start_time))
            if end_time:
                query = query.filter(TimeseriesData.recorded_at <= datetime.fromisoformat(end_time))
            
            rows = query.order_by(TimeseriesData.recorded_at).all()
            data = [{'time': row.recorded_at.isoformat(), 'value': row.value} for row in rows]
            
            results[device.device_code] = {
                'device_code': device.device_code,
                'device_name': device.device_name,
                'parameter': resolved_param,
                'unit': sensor.unit,
                'data': data,
                'count': len(data)
            }
        
        return results
    
    finally:
        db.close()


def get_device_list() -> list:
    db = next(get_db())
    try:
        devices = db.query(Device).all()
        return [{
            'id': device.id,
            'code': device.device_code,
            'name': device.device_name,
            'type': device.device_type,
            'location': device.location,
            'status': device.status
        } for device in devices]
    finally:
        db.close()


def get_sensor_points(device_id: int) -> list:
    db = next(get_db())
    try:
        points = db.query(SensorPoint).filter_by(device_id=device_id).all()
        return [{
            'id': point.id,
            'name': point.point_name,
            'unit': point.unit,
            'normal_min': point.normal_min,
            'normal_max': point.normal_max,
            'threshold_high': point.threshold_high,
            'threshold_low': point.threshold_low
        } for point in points]
    finally:
        db.close()
