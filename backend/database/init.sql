CREATE TABLE device (
    id SERIAL PRIMARY KEY,
    device_name VARCHAR(100) NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    location VARCHAR(200),
    status VARCHAR(20) DEFAULT 'running',
    create_time TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON COLUMN device.id IS '设备ID';
COMMENT ON COLUMN device.device_name IS '设备名称';
COMMENT ON COLUMN device.device_type IS '设备类型';
COMMENT ON COLUMN device.location IS '设备位置';
COMMENT ON COLUMN device.status IS '设备状态';
COMMENT ON COLUMN device.create_time IS '创建时间';

CREATE TABLE sensor_point (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES device(id),
    point_name VARCHAR(100) NOT NULL,
    unit VARCHAR(20),
    normal_min DOUBLE PRECISION,
    normal_max DOUBLE PRECISION,
    threshold_high DOUBLE PRECISION,
    threshold_low DOUBLE PRECISION,
    create_time TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON COLUMN sensor_point.id IS '测点ID';
COMMENT ON COLUMN sensor_point.device_id IS '所属设备ID';
COMMENT ON COLUMN sensor_point.point_name IS '测点名称';
COMMENT ON COLUMN sensor_point.unit IS '单位';
COMMENT ON COLUMN sensor_point.normal_min IS '正常值下限';
COMMENT ON COLUMN sensor_point.normal_max IS '正常值上限';
COMMENT ON COLUMN sensor_point.threshold_high IS '高阈值';
COMMENT ON COLUMN sensor_point.threshold_low IS '低阈值';
COMMENT ON COLUMN sensor_point.create_time IS '创建时间';

CREATE TABLE timeseries_data (
    id BIGSERIAL,
    device_id INTEGER REFERENCES device(id),
    sensor_id INTEGER REFERENCES sensor_point(id),
    value DOUBLE PRECISION NOT NULL,
    quality VARCHAR(10) DEFAULT 'good',
    recorded_at TIMESTAMPTZ NOT NULL
);

COMMENT ON COLUMN timeseries_data.id IS '数据ID';
COMMENT ON COLUMN timeseries_data.device_id IS '设备ID';
COMMENT ON COLUMN timeseries_data.sensor_id IS '测点ID';
COMMENT ON COLUMN timeseries_data.value IS '测量值';
COMMENT ON COLUMN timeseries_data.quality IS '数据质量';
COMMENT ON COLUMN timeseries_data.recorded_at IS '记录时间';

SELECT create_hypertable('timeseries_data', 'recorded_at');

CREATE TABLE alarm_record (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES device(id),
    sensor_id INTEGER REFERENCES sensor_point(id),
    alarm_type VARCHAR(50),
    severity VARCHAR(10),
    current_value DOUBLE PRECISION,
    threshold_value DOUBLE PRECISION,
    message TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    triggered_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON COLUMN alarm_record.id IS '告警ID';
COMMENT ON COLUMN alarm_record.device_id IS '设备ID';
COMMENT ON COLUMN alarm_record.sensor_id IS '测点ID';
COMMENT ON COLUMN alarm_record.alarm_type IS '告警类型';
COMMENT ON COLUMN alarm_record.severity IS '严重程度';
COMMENT ON COLUMN alarm_record.current_value IS '当前值';
COMMENT ON COLUMN alarm_record.threshold_value IS '阈值';
COMMENT ON COLUMN alarm_record.message IS '告警消息';
COMMENT ON COLUMN alarm_record.status IS '告警状态';
COMMENT ON COLUMN alarm_record.triggered_at IS '触发时间';

CREATE TABLE diagnosis_result (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES device(id),
    alarm_id INTEGER REFERENCES alarm_record(id),
    diagnosis_type VARCHAR(50),
    fault_type VARCHAR(100),
    confidence DOUBLE PRECISION,
    causes TEXT[],
    suggestions TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON COLUMN diagnosis_result.id IS '诊断结果ID';
COMMENT ON COLUMN diagnosis_result.device_id IS '设备ID';
COMMENT ON COLUMN diagnosis_result.alarm_id IS '关联告警ID';
COMMENT ON COLUMN diagnosis_result.diagnosis_type IS '诊断类型';
COMMENT ON COLUMN diagnosis_result.fault_type IS '故障类型';
COMMENT ON COLUMN diagnosis_result.confidence IS '置信度';
COMMENT ON COLUMN diagnosis_result.causes IS '可能原因';
COMMENT ON COLUMN diagnosis_result.suggestions IS '处理建议';
COMMENT ON COLUMN diagnosis_result.created_at IS '创建时间';

CREATE INDEX idx_device_type ON device(device_type);
CREATE INDEX idx_sensor_device ON sensor_point(device_id);
CREATE INDEX idx_alarm_device ON alarm_record(device_id);
CREATE INDEX idx_alarm_status ON alarm_record(status);
CREATE INDEX idx_diagnosis_device ON diagnosis_result(device_id);