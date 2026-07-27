import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.database.connection import get_db, engine
from backend.database.models import Device, SensorPoint, TimeseriesData, AlarmRecord
from normal_pattern import (
    generate_normal_boiler_data,
    generate_normal_turbine_data,
    generate_normal_generator_data
)
from anomaly_scenarios import (
    inject_steam_temp_rise,
    inject_vibration_spike,
    inject_pressure_drop,
    inject_stator_overheat
)


DEVICES = [
    {'id': 1, 'name': '2号锅炉', 'type': 'boiler', 'location': '锅炉房A区'},
    {'id': 2, 'name': '3号汽轮机', 'type': 'turbine', 'location': '汽机厂房B区'},
    {'id': 3, 'name': '4号发电机', 'type': 'generator', 'location': '发电机厂房C区'},
]

SENSOR_POINTS = {
    'boiler': [
        {'name': 'steam_temp', 'unit': '℃', 'normal_min': 525, 'normal_max': 555, 'threshold_high': 570, 'threshold_low': 510},
        {'name': 'steam_pressure', 'unit': 'MPa', 'normal_min': 16.2, 'normal_max': 17.2, 'threshold_high': 18.0, 'threshold_low': 15.5},
        {'name': 'furnace_temp', 'unit': '℃', 'normal_min': 1150, 'normal_max': 1250, 'threshold_high': 1300, 'threshold_low': 1100},
        {'name': 'water_flow', 'unit': 't/h', 'normal_min': 95, 'normal_max': 105, 'threshold_high': 115, 'threshold_low': 85},
    ],
    'turbine': [
        {'name': 'speed', 'unit': 'rpm', 'normal_min': 2950, 'normal_max': 3050, 'threshold_high': 3100, 'threshold_low': 2900},
        {'name': 'bearing_temp', 'unit': '℃', 'normal_min': 75, 'normal_max': 95, 'threshold_high': 110, 'threshold_low': 65},
        {'name': 'vibration', 'unit': 'mm', 'normal_min': 0.01, 'normal_max': 0.05, 'threshold_high': 0.10, 'threshold_low': 0.005},
        {'name': 'oil_pressure', 'unit': 'MPa', 'normal_min': 0.30, 'normal_max': 0.40, 'threshold_high': 0.45, 'threshold_low': 0.25},
    ],
    'generator': [
        {'name': 'active_power', 'unit': 'MW', 'normal_min': 250, 'normal_max': 350, 'threshold_high': 380, 'threshold_low': 220},
        {'name': 'stator_temp', 'unit': '℃', 'normal_min': 90, 'normal_max': 120, 'threshold_high': 140, 'threshold_low': 75},
        {'name': 'rotor_temp', 'unit': '℃', 'normal_min': 85, 'normal_max': 105, 'threshold_high': 120, 'threshold_low': 70},
        {'name': 'power_factor', 'unit': '', 'normal_min': 0.92, 'normal_max': 0.98, 'threshold_high': 1.0, 'threshold_low': 0.85},
    ],
}


def init_devices(db):
    print("Initializing devices...")
    for device in DEVICES:
        db_device = Device(
            id=device['id'],
            device_name=device['name'],
            device_type=device['type'],
            location=device['location'],
            status='running'
        )
        db.add(db_device)
    db.commit()
    print(f"Created {len(DEVICES)} devices")


def init_sensor_points(db):
    print("Initializing sensor points...")
    point_id = 1
    for device in DEVICES:
        device_type = device['type']
        for point in SENSOR_POINTS[device_type]:
            db_point = SensorPoint(
                id=point_id,
                device_id=device['id'],
                point_name=point['name'],
                unit=point['unit'],
                normal_min=point['normal_min'],
                normal_max=point['normal_max'],
                threshold_high=point['threshold_high'],
                threshold_low=point['threshold_low']
            )
            db.add(db_point)
            point_id += 1
    db.commit()
    print(f"Created {point_id - 1} sensor points")


def generate_data_for_device(device_id: int, device_type: str, start_time: datetime, days: int = 7):
    minutes = days * 24 * 60
    
    if device_type == 'boiler':
        data = generate_normal_boiler_data(start_time, minutes)
    elif device_type == 'turbine':
        data = generate_normal_turbine_data(start_time, minutes)
    elif device_type == 'generator':
        data = generate_normal_generator_data(start_time, minutes)
    else:
        data = []
    
    return data


def inject_anomalies(device_type: str, data: list):
    anomalies = []
    
    if device_type == 'boiler':
        steam_anomalies = inject_steam_temp_rise(data, 3 * 24 * 60 + 12 * 60, 3 * 60)
        anomalies.extend(steam_anomalies)
        
        pressure_anomalies = inject_pressure_drop(data, 5 * 24 * 60 + 8 * 60, 2 * 60)
        anomalies.extend(pressure_anomalies)
    
    elif device_type == 'turbine':
        vibration_anomalies = inject_vibration_spike(data, 4 * 24 * 60 + 3 * 60)
        anomalies.extend(vibration_anomalies)
    
    elif device_type == 'generator':
        stator_anomalies = inject_stator_overheat(data, 6 * 24 * 60 + 18 * 60, 4 * 60)
        anomalies.extend(stator_anomalies)
    
    return anomalies


def write_data_to_db(db, device_id: int, data: list, sensor_map: dict):
    print(f"Writing data for device {device_id}...")
    batch_size = 1000
    records = []
    
    for item in data:
        sensor_id = sensor_map.get(item['point_name'])
        if sensor_id:
            record = TimeseriesData(
                device_id=device_id,
                sensor_id=sensor_id,
                value=item['value'],
                quality='good',
                recorded_at=item['timestamp']
            )
            records.append(record)
            
            if len(records) >= batch_size:
                db.add_all(records)
                db.commit()
                records = []
    
    if records:
        db.add_all(records)
        db.commit()
    
    print(f"Written {len(data)} records")


def create_alarm_records(db, device_id: int, anomalies: list, sensor_map: dict):
    print(f"Creating alarm records for device {device_id}...")
    for item in anomalies:
        sensor_id = sensor_map.get(item['point_name'])
        if sensor_id:
            sensor = db.query(SensorPoint).filter_by(id=sensor_id).first()
            if sensor:
                alarm_type = 'threshold'
                severity = 'high'
                
                if item['value'] > sensor.threshold_high:
                    threshold_value = sensor.threshold_high
                    message = f"{sensor.point_name} 超过高阈值: {item['value']} > {threshold_value}"
                elif item['value'] < sensor.threshold_low:
                    threshold_value = sensor.threshold_low
                    message = f"{sensor.point_name} 低于低阈值: {item['value']} < {threshold_value}"
                else:
                    continue
                
                alarm = AlarmRecord(
                    device_id=device_id,
                    sensor_id=sensor_id,
                    alarm_type=alarm_type,
                    severity=severity,
                    current_value=item['value'],
                    threshold_value=threshold_value,
                    message=message,
                    status='pending',
                    triggered_at=item['timestamp']
                )
                db.add(alarm)
    
    db.commit()
    print(f"Created {len(anomalies)} alarm records")


def main():
    db = next(get_db())
    
    try:
        existing_devices = db.query(Device).count()
        if existing_devices == 0:
            init_devices(db)
        
        existing_points = db.query(SensorPoint).count()
        if existing_points == 0:
            init_sensor_points(db)
        
        start_time = datetime.now() - timedelta(days=7)
        total_records = 0
        total_anomalies = 0
        
        for device in DEVICES:
            data = generate_data_for_device(device['id'], device['type'], start_time)
            anomalies = inject_anomalies(device['type'], data)
            
            sensor_map = {}
            points = db.query(SensorPoint).filter_by(device_id=device['id']).all()
            for point in points:
                sensor_map[point.point_name] = point.id
            
            write_data_to_db(db, device['id'], data, sensor_map)
            create_alarm_records(db, device['id'], anomalies, sensor_map)
            
            total_records += len(data)
            total_anomalies += len(anomalies)
        
        print(f"\n=== Data Generation Complete ===")
        print(f"Total records written: {total_records}")
        print(f"Total anomalies injected: {total_anomalies}")
        print(f"Start time: {start_time}")
        print(f"End time: {start_time + timedelta(days=7)}")
        
    finally:
        db.close()


if __name__ == '__main__':
    main()