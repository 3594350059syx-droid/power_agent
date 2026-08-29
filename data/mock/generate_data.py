"""
电厂模拟数据生成主脚本（P0-2）

一键生成 7 天模拟数据并写入 TimescaleDB。

幂等保证：重复运行时仅清空本脚本管理设备的关联诊断、告警和时序数据，
再重新插入，不会产生重复数据或影响其他设备。

运行方式：
    python data/mock/generate_data.py
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

_mock_dir = str(Path(__file__).resolve().parent)
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if _mock_dir not in sys.path:
    sys.path.insert(0, _mock_dir)

from backend.database.connection import get_db
from backend.database.models import (
    AlarmRecord,
    Device,
    DiagnosisResult,
    SensorPoint,
    TimeseriesData,
)
from config import DEVICES, SENSOR_POINTS, ANOMALY_WINDOWS
from normal_pattern import (
    generate_normal_boiler_data,
    generate_normal_turbine_data,
    generate_normal_generator_data,
)
from mock_utils import get_generation_start_time, inject_configured_anomalies


def init_devices(db):
    """按 device_code 做 get-or-create，不依赖硬编码主键"""
    created = 0
    for device in DEVICES:
        existing = db.query(Device).filter_by(device_code=device['code']).first()
        if existing:
            # 更新可能变更的属性，保持 id 不变
            existing.device_name = device['name']
            existing.device_type = device['type']
            existing.location = device['location']
            existing.status = 'running'
        else:
            db.add(Device(
                device_code=device['code'],
                device_name=device['name'],
                device_type=device['type'],
                location=device['location'],
                status='running',
            ))
            created += 1
    db.commit()
    print(f"Devices ready (newly created: {created})")


def init_sensor_points(db):
    """按 (device_id, point_name) 做 get-or-create"""
    created = 0
    for device in DEVICES:
        db_device = db.query(Device).filter_by(device_code=device['code']).first()
        if not db_device:
            continue
        for point in SENSOR_POINTS[device['type']]:
            existing = db.query(SensorPoint).filter_by(
                device_id=db_device.id, point_name=point['name']
            ).first()
            if existing:
                existing.unit = point['unit']
                existing.normal_min = point['normal_min']
                existing.normal_max = point['normal_max']
                existing.threshold_high = point['threshold_high']
                existing.threshold_low = point['threshold_low']
            else:
                db.add(SensorPoint(
                    device_id=db_device.id,
                    point_name=point['name'],
                    unit=point['unit'],
                    normal_min=point['normal_min'],
                    normal_max=point['normal_max'],
                    threshold_high=point['threshold_high'],
                    threshold_low=point['threshold_low'],
                ))
                created += 1
    db.commit()
    print(f"Sensor points ready (newly created: {created})")


def get_mock_device_ids(db) -> list:
    """返回数据库中由当前 mock 配置管理的设备 ID。"""
    device_codes = [device['code'] for device in DEVICES]
    devices = db.query(Device).filter(Device.device_code.in_(device_codes)).all()
    return [device.id for device in devices]


def clear_device_data(db, device_ids: list):
    """按外键依赖顺序清空指定 mock 设备的数据，保证幂等。"""
    if not device_ids:
        return

    # diagnosis_result.alarm_id 引用 alarm_record.id，必须先删除关联诊断。
    # 同时按 device_id 限定范围，确保不影响非 mock 设备的数据，并清理 alarm_id
    # 为空的 mock 诊断记录。
    db.query(DiagnosisResult).filter(
        DiagnosisResult.device_id.in_(device_ids)
    ).delete(synchronize_session=False)
    db.query(AlarmRecord).filter(
        AlarmRecord.device_id.in_(device_ids)
    ).delete(synchronize_session=False)
    db.query(TimeseriesData).filter(
        TimeseriesData.device_id.in_(device_ids)
    ).delete(synchronize_session=False)
    db.commit()
    print(f"Cleared old diagnosis_result, alarm_record & timeseries_data for devices {device_ids}")


def generate_data_for_device(device_type: str, start_time: datetime, days: int = 7):
    minutes = days * 24 * 60
    if device_type == 'boiler':
        return generate_normal_boiler_data(start_time, minutes)
    elif device_type == 'turbine':
        return generate_normal_turbine_data(start_time, minutes)
    elif device_type == 'generator':
        return generate_normal_generator_data(start_time, minutes)
    return []


def inject_anomalies(device_type: str, data: list):
    """按 Week 2 规格注入异常场景，返回受影响的异常数据点列表"""
    return inject_configured_anomalies(device_type, data, ANOMALY_WINDOWS)


def write_data_to_db(db, device_id: int, data: list, sensor_map: dict):
    batch_size = 1000
    records = []
    for item in data:
        sensor_id = sensor_map.get(item['point_name'])
        if sensor_id:
            records.append(TimeseriesData(
                device_id=device_id,
                sensor_id=sensor_id,
                value=float(item['value']),
                quality='good',
                recorded_at=item['timestamp'],
            ))
            if len(records) >= batch_size:
                db.add_all(records)
                db.commit()
                records = []
    if records:
        db.add_all(records)
        db.commit()
    print(f"  Written {len(data)} records for device {device_id}")


def create_alarm_records(db, device_id: int, anomalies: list, sensor_map: dict):
    alarm_count = 0
    for item in anomalies:
        sensor_id = sensor_map.get(item['point_name'])
        if not sensor_id:
            continue
        sensor = db.query(SensorPoint).filter_by(id=sensor_id).first()
        if not sensor:
            continue

        if item['value'] > sensor.threshold_high:
            threshold_value = sensor.threshold_high
            excess = item['value'] - sensor.threshold_high
            message = f"{sensor.point_name} 超过高阈值: {item['value']} > {threshold_value}"
        elif item['value'] < sensor.threshold_low:
            threshold_value = sensor.threshold_low
            excess = sensor.threshold_low - item['value']
            message = f"{sensor.point_name} 低于低阈值: {item['value']} < {threshold_value}"
        else:
            continue

        # severity 按超限幅度分级，与 ThresholdDetector 的 score 逻辑一致
        margin = (sensor.threshold_high - sensor.threshold_low) or 1.0
        score = min(1.0, excess / margin * 2)
        severity = 'high' if score > 0.5 else 'medium'

        db.add(AlarmRecord(
            device_id=device_id,
            sensor_id=sensor_id,
            alarm_type='threshold',
            severity=severity,
            current_value=float(item['value']),
            threshold_value=float(threshold_value),
            message=message,
            status='pending',
            triggered_at=item['timestamp'],
        ))
        alarm_count += 1
    db.commit()
    print(f"  Created {alarm_count} alarm records for device {device_id}")


def main():
    db = next(get_db())
    try:
        init_devices(db)
        init_sensor_points(db)

        # 幂等：只清空由当前 mock 配置管理的设备，避免删除其他设备的业务数据。
        clear_device_data(db, get_mock_device_ids(db))

        start_time = get_generation_start_time()
        total_records = 0
        total_anomalies = 0

        for device_cfg in DEVICES:
            db_device = db.query(Device).filter_by(device_code=device_cfg['code']).first()
            if not db_device:
                continue
            print(f"\n[{device_cfg['name']}] generating data...")

            data = generate_data_for_device(device_cfg['type'], start_time)
            anomalies = inject_anomalies(device_cfg['type'], data)

            points = db.query(SensorPoint).filter_by(device_id=db_device.id).all()
            sensor_map = {p.point_name: p.id for p in points}

            write_data_to_db(db, db_device.id, data, sensor_map)
            create_alarm_records(db, db_device.id, anomalies, sensor_map)

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
