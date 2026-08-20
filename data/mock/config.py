"""
设备 / 测点 / 阈值配置常量

Week 2 规格：3 台设备 × 3 测点 = 9 个测点
预计数据量：3 × 3 × 7天 × 1440点 ≈ 90,720 条

注意：此处不包含数据库主键 id —— 主键由数据库自增分配，
脚本通过 device_code 查询实际 id，避免硬编码导致的外键错乱。
"""

DEVICES = [
    {'code': 'boiler_002', 'name': '2号锅炉', 'type': 'boiler', 'location': '锅炉房A区'},
    {'code': 'turbine_003', 'name': '3号汽轮机', 'type': 'turbine', 'location': '汽机厂房B区'},
    {'code': 'generator_004', 'name': '4号发电机', 'type': 'generator', 'location': '发电机厂房C区'},
]

SENSOR_POINTS = {
    'boiler': [
        {'name': 'steam_temp', 'unit': '℃', 'normal_min': 525, 'normal_max': 555,
         'threshold_high': 570, 'threshold_low': 510},
        {'name': 'steam_pressure', 'unit': 'MPa', 'normal_min': 16.2, 'normal_max': 17.2,
         'threshold_high': 18.0, 'threshold_low': 15.5},
        {'name': 'furnace_temp', 'unit': '℃', 'normal_min': 1150, 'normal_max': 1250,
         'threshold_high': 1300, 'threshold_low': 1100},
    ],
    'turbine': [
        {'name': 'rpm', 'unit': 'rpm', 'normal_min': 2950, 'normal_max': 3050,
         'threshold_high': 3100, 'threshold_low': 2900},
        {'name': 'bearing_temp', 'unit': '℃', 'normal_min': 75, 'normal_max': 95,
         'threshold_high': 110, 'threshold_low': 65},
        {'name': 'vibration', 'unit': 'mm', 'normal_min': 0.01, 'normal_max': 0.05,
         'threshold_high': 0.10, 'threshold_low': 0.005},
    ],
    'generator': [
        {'name': 'power', 'unit': 'MW', 'normal_min': 250, 'normal_max': 350,
         'threshold_high': 380, 'threshold_low': 220},
        {'name': 'stator_temp', 'unit': '℃', 'normal_min': 90, 'normal_max': 120,
         'threshold_high': 140, 'threshold_low': 75},
        {'name': 'reactive_power', 'unit': 'Mvar', 'normal_min': 30, 'normal_max': 70,
         'threshold_high': 80, 'threshold_low': 20},
    ],
}

# 异常场景时间窗口（相对数据起点 start_time 的分钟偏移）
# 严格按 Week 2 规格：
#   - 主蒸汽温度：第 4 天 14:00-16:00（线性 540→575℃）
#   - 振动：第 5 天 02:00-06:00（持续升高 0.03→0.12mm）
ANOMALY_WINDOWS = {
    'steam_temp_rise': {
        'device_type': 'boiler',
        'start_offset': 3 * 24 * 60 + 14 * 60,   # 第 4 天 14:00
        'duration': 2 * 60,                       # 持续 2 小时
    },
    'vibration_rise': {
        'device_type': 'turbine',
        'start_offset': 4 * 24 * 60 + 2 * 60,     # 第 5 天 02:00
        'duration': 4 * 60,                       # 持续 4 小时
    },
}
