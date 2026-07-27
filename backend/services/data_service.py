from datetime import datetime, timedelta
from sqlalchemy import func, extract, and_
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import Device, SensorPoint, TimeseriesData


def get_device_id_by_name(device_name: str) -> int:
    db = next(get_db())
    try:
        device = db.query(Device).filter_by(device_name=device_name).first()
        return device.id if device else None
    finally:
        db.close()


def get_sensor_info(db: Session, device_id: int, parameter: str):
    sensor = db.query(SensorPoint).filter(
        SensorPoint.device_id == device_id,
        SensorPoint.point_name == parameter
    ).first()
    return sensor


def query_timeseries_data(params: dict) -> dict:
    device_name = params.get('device_id', '')
    parameter = params.get('parameter', '')
    start_time = params.get('start_time')
    end_time = params.get('end_time')
    aggregation = params.get('aggregation', None)
    
    db = next(get_db())
    try:
        device = db.query(Device).filter_by(device_name=device_name).first()
        if not device:
            return {'error': f"Device '{device_name}' not found"}
        
        sensor = get_sensor_info(db, device.id, parameter)
        if not sensor:
            return {'error': f"Parameter '{parameter}' not found for device '{device_name}'"}
        
        query = db.query(
            TimeseriesData.recorded_at,
            TimeseriesData.value
        ).filter(
            TimeseriesData.device_id == device.id,
            TimeseriesData.sensor_id == sensor.id
        )
        
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
            query = query.filter(TimeseriesData.recorded_at >= start_dt)
        
        if end_time:
            end_dt = datetime.fromisoformat(end_time)
            query = query.filter(TimeseriesData.recorded_at <= end_dt)
        
        if aggregation:
            result = aggregate_query(query, aggregation)
        else:
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
            
            if start_time:
                stats_query = stats_query.filter(TimeseriesData.recorded_at >= start_dt)
            if end_time:
                stats_query = stats_query.filter(TimeseriesData.recorded_at <= end_dt)
            
            stats_result = stats_query.first()
            result = {
                'device_id': device_name,
                'parameter': parameter,
                'unit': sensor.unit,
                'data': data,
                'stats': {
                    'min': round(stats_result[0], 2) if stats_result[0] else None,
                    'max': round(stats_result[1], 2) if stats_result[1] else None,
                    'avg': round(stats_result[2], 2) if stats_result[2] else None,
                    'count': stats_result[3] if stats_result[3] else 0
                }
            }
        
        return result
    
    finally:
        db.close()


def aggregate_query(query, aggregation: str):
    interval_map = {
        '5min': '5 minutes',
        '15min': '15 minutes',
        '1h': '1 hour',
        '6h': '6 hours',
        '1d': '1 day'
    }
    
    interval = interval_map.get(aggregation, '1 hour')
    
    bucketed_query = query.from_self().with_entities(
        func.date_trunc(interval, TimeseriesData.recorded_at).label('bucket'),
        func.avg(TimeseriesData.value).label('avg_value'),
        func.min(TimeseriesData.value).label('min_value'),
        func.max(TimeseriesData.value).label('max_value'),
        func.count(TimeseriesData.value).label('count')
    ).group_by('bucket').order_by('bucket')
    
    rows = bucketed_query.all()
    data = [{
        'time': row.bucket.isoformat(),
        'value': round(row.avg_value, 2) if row.avg_value else None,
        'min': round(row.min_value, 2) if row.min_value else None,
        'max': round(row.max_value, 2) if row.max_value else None,
        'count': row.count if row.count else 0
    } for row in rows]
    
    return {
        'data': data,
        'aggregation': aggregation
    }


def query_multiple_devices(params: dict) -> dict:
    device_names = params.get('device_ids', [])
    parameter = params.get('parameter', '')
    start_time = params.get('start_time')
    end_time = params.get('end_time')
    
    db = next(get_db())
    try:
        results = {}
        
        for device_name in device_names:
            device = db.query(Device).filter_by(device_name=device_name).first()
            if not device:
                results[device_name] = {'error': f"Device '{device_name}' not found"}
                continue
            
            sensor = get_sensor_info(db, device.id, parameter)
            if not sensor:
                results[device_name] = {'error': f"Parameter '{parameter}' not found"}
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
            
            results[device_name] = {
                'parameter': parameter,
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