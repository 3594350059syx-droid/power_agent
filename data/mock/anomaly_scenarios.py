from datetime import datetime, timedelta


def inject_steam_temp_rise(data: list, start_offset: int, duration_minutes: int):
    affected_points = []
    for item in data:
        if item['point_name'] == 'steam_temp':
            timestamp = item['timestamp']
            base_time = data[0]['timestamp'] + timedelta(minutes=start_offset)
            end_time = base_time + timedelta(minutes=duration_minutes)
            
            if base_time <= timestamp <= end_time:
                elapsed = (timestamp - base_time).total_seconds() / 60
                progress = elapsed / duration_minutes
                item['value'] = 540 + 35 * (1 - (1 - progress) ** 3)
                affected_points.append(item)
    
    return affected_points


def inject_vibration_spike(data: list, spike_minute: int):
    affected_points = []
    for item in data:
        if item['point_name'] == 'vibration':
            timestamp = item['timestamp']
            spike_time = data[0]['timestamp'] + timedelta(minutes=spike_minute)
            window_start = spike_time - timedelta(minutes=5)
            window_end = spike_time + timedelta(minutes=30)
            
            if window_start <= timestamp <= window_end:
                distance = abs((timestamp - spike_time).total_seconds() / 60)
                if distance <= 5:
                    spike_magnitude = 1 - (distance / 5)
                    item['value'] = 0.03 + spike_magnitude * 0.09
                    affected_points.append(item)
                elif distance <= 30:
                    decay = 1 - (distance - 5) / 25
                    item['value'] = 0.03 + decay * 0.03
                    affected_points.append(item)
    
    return affected_points


def inject_pressure_drop(data: list, start_offset: int, duration_minutes: int):
    affected_points = []
    for item in data:
        if item['point_name'] == 'steam_pressure':
            timestamp = item['timestamp']
            base_time = data[0]['timestamp'] + timedelta(minutes=start_offset)
            end_time = base_time + timedelta(minutes=duration_minutes)
            
            if base_time <= timestamp <= end_time:
                elapsed = (timestamp - base_time).total_seconds() / 60
                progress = elapsed / duration_minutes
                drop_amount = 2.0 * (1 - (1 - progress) ** 2)
                item['value'] = max(14.7, 16.7 - drop_amount)
                affected_points.append(item)
    
    return affected_points


def inject_stator_overheat(data: list, start_offset: int, duration_minutes: int):
    affected_points = []
    for item in data:
        if item['point_name'] == 'stator_temp':
            timestamp = item['timestamp']
            base_time = data[0]['timestamp'] + timedelta(minutes=start_offset)
            end_time = base_time + timedelta(minutes=duration_minutes)
            
            if base_time <= timestamp <= end_time:
                elapsed = (timestamp - base_time).total_seconds() / 60
                progress = elapsed / duration_minutes
                item['value'] = 105 + 20 * (1 - (1 - progress) ** 2)
                affected_points.append(item)
    
    return affected_points