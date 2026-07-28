import numpy as np
from datetime import datetime, timedelta


def generate_normal_value(base: float, variance: float, hour: int = None) -> float:
    value = base + np.random.normal(0, variance / 3)
    
    if hour is not None:
        diurnal_pattern = np.sin(2 * np.pi * hour / 24) * variance / 2
        value += diurnal_pattern
    
    return round(value, 2)


def generate_normal_boiler_data(start_time: datetime, minutes: int):
    data = []
    for i in range(minutes):
        timestamp = start_time + timedelta(minutes=i)
        hour = timestamp.hour
        
        data.append({
            'point_name': 'steam_temp',
            'value': generate_normal_value(540, 15, hour),
            'timestamp': timestamp
        })
        data.append({
            'point_name': 'steam_pressure',
            'value': generate_normal_value(16.7, 0.5, hour),
            'timestamp': timestamp
        })
        data.append({
            'point_name': 'furnace_temp',
            'value': generate_normal_value(1200, 50, hour),
            'timestamp': timestamp
        })
        data.append({
            'point_name': 'water_flow',
            'value': generate_normal_value(100, 5, hour),
            'timestamp': timestamp
        })
    
    return data


def generate_normal_turbine_data(start_time: datetime, minutes: int):
    data = []
    for i in range(minutes):
        timestamp = start_time + timedelta(minutes=i)
        hour = timestamp.hour
        
        data.append({
            'point_name': 'rpm',
            'value': generate_normal_value(3000, 50, hour),
            'timestamp': timestamp
        })
        data.append({
            'point_name': 'bearing_temp',
            'value': generate_normal_value(85, 10, hour),
            'timestamp': timestamp
        })
        data.append({
            'point_name': 'vibration',
            'value': generate_normal_value(0.03, 0.02, hour),
            'timestamp': timestamp
        })
        data.append({
            'point_name': 'oil_pressure',
            'value': generate_normal_value(0.35, 0.05, hour),
            'timestamp': timestamp
        })
    
    return data


def generate_normal_generator_data(start_time: datetime, minutes: int):
    data = []
    for i in range(minutes):
        timestamp = start_time + timedelta(minutes=i)
        hour = timestamp.hour
        
        data.append({
            'point_name': 'power',
            'value': generate_normal_value(300, 50, hour),
            'timestamp': timestamp
        })
        data.append({
            'point_name': 'stator_temp',
            'value': generate_normal_value(105, 15, hour),
            'timestamp': timestamp
        })
        data.append({
            'point_name': 'rotor_temp',
            'value': generate_normal_value(95, 10, hour),
            'timestamp': timestamp
        })
        data.append({
            'point_name': 'power_factor',
            'value': generate_normal_value(0.95, 0.03, hour),
            'timestamp': timestamp
        })
    
    return data