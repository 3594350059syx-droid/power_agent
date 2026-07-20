from sqlalchemy import Column, Integer, String, Double, DateTime, ForeignKey, Text, ARRAY
from sqlalchemy.sql import func
from backend.database.connection import Base


class Device(Base):
    __tablename__ = "device"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_name = Column(String(100), nullable=False)
    device_type = Column(String(50), nullable=False)
    location = Column(String(200))
    status = Column(String(20), default="running")
    create_time = Column(DateTime(timezone=True), default=func.now())


class SensorPoint(Base):
    __tablename__ = "sensor_point"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("device.id"))
    point_name = Column(String(100), nullable=False)
    unit = Column(String(20))
    normal_min = Column(Double)
    normal_max = Column(Double)
    threshold_high = Column(Double)
    threshold_low = Column(Double)
    create_time = Column(DateTime(timezone=True), default=func.now())


class TimeseriesData(Base):
    __tablename__ = "timeseries_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("device.id"))
    sensor_id = Column(Integer, ForeignKey("sensor_point.id"))
    value = Column(Double, nullable=False)
    quality = Column(String(10), default="good")
    recorded_at = Column(DateTime(timezone=True), nullable=False)


class AlarmRecord(Base):
    __tablename__ = "alarm_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("device.id"))
    sensor_id = Column(Integer, ForeignKey("sensor_point.id"))
    alarm_type = Column(String(50))
    severity = Column(String(10))
    current_value = Column(Double)
    threshold_value = Column(Double)
    message = Column(Text)
    status = Column(String(20), default="pending")
    triggered_at = Column(DateTime(timezone=True), default=func.now())


class DiagnosisResult(Base):
    __tablename__ = "diagnosis_result"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("device.id"))
    alarm_id = Column(Integer, ForeignKey("alarm_record.id"))
    diagnosis_type = Column(String(50))
    fault_type = Column(String(100))
    confidence = Column(Double)
    causes = Column(ARRAY(Text))
    suggestions = Column(ARRAY(Text))
    created_at = Column(DateTime(timezone=True), default=func.now())