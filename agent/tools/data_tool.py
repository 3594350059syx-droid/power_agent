from backend.services.data_service import query_timeseries_data, query_multiple_devices, get_device_list, get_sensor_points


def data_tool(params: dict) -> dict:
    """
    查询时序数据的工具函数
    
    参数:
        params: dict - 查询参数
            - device_id: str - 设备名称（如 "2号锅炉", "3号汽轮机", "4号发电机"）
            - parameter: str - 测点参数名（如 "steam_temp", "speed", "active_power"）
            - start_time: str - 开始时间（ISO格式，如 "2026-07-10T00:00:00"）
            - end_time: str - 结束时间（ISO格式）
            - aggregation: str - 聚合间隔（可选，如 "5min", "15min", "1h", "6h", "1d"）
    
    返回:
        dict - 查询结果
            - device_id: str - 设备名称
            - parameter: str - 参数名
            - unit: str - 单位
            - data: list - 数据点列表 [{"time": "...", "value": 540.5}, ...]
            - stats: dict - 统计信息 {"min": 535.0, "max": 575.0, "avg": 548.3, "count": 1440}
    """
    return query_timeseries_data(params)


def compare_devices_tool(params: dict) -> dict:
    """
    多设备对比查询工具
    
    参数:
        params: dict - 查询参数
            - device_ids: list - 设备名称列表
            - parameter: str - 测点参数名
            - start_time: str - 开始时间
            - end_time: str - 结束时间
    
    返回:
        dict - 各设备查询结果
    """
    return query_multiple_devices(params)


def list_devices_tool() -> list:
    """
    获取设备列表工具
    
    返回:
        list - 设备信息列表
    """
    return get_device_list()


def list_sensors_tool(device_name: str) -> list:
    """
    获取设备测点列表工具
    
    参数:
        device_name: str - 设备名称
    
    返回:
        list - 测点信息列表
    """
    devices = get_device_list()
    for device in devices:
        if device['name'] == device_name:
            return get_sensor_points(device['id'])
    return []