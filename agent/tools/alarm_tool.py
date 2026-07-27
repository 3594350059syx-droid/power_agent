from backend.services.alarm_service import analyze_device_anomalies, get_alarm_history, get_all_pending_alarms, acknowledge_alarm


def alarm_tool(device_id: str, hours: int = 24) -> dict:
    """
    告警检测工具函数
    
    参数:
        device_id: str - 设备名称（如 "2号锅炉", "3号汽轮机", "4号发电机"）
        hours: int - 分析时长（小时），默认为 24 小时
    
    返回:
        dict - 告警检测结果
            - device_id: str - 设备名称
            - risk_score: float - 综合风险评分 (0-1)
            - alarms: list - 告警列表
                - type: str - 告警类型 ('threshold', 'trend')
                - parameter: str - 参数名
                - current_value: float - 当前值
                - threshold: float - 阈值（仅阈值告警）
                - severity: str - 严重程度 ('high', 'medium', 'low')
                - score: float - 异常得分
                - triggered_at: str - 触发时间
                - trend_desc: str - 趋势描述（仅趋势告警）
                - slope: float - 斜率（仅趋势告警）
            - recommendations: list - 建议措施
    """
    return analyze_device_anomalies(device_id, hours)


def alarm_history_tool(device_id: str, hours: int = 24, status: str = None) -> list:
    """
    获取告警历史记录工具
    
    参数:
        device_id: str - 设备名称
        hours: int - 查询时长（小时）
        status: str - 告警状态过滤（可选：'pending', 'acknowledged'）
    
    返回:
        list - 告警历史记录列表
    """
    return get_alarm_history(device_id, hours, status)


def pending_alarms_tool() -> list:
    """
    获取所有待处理告警工具
    
    返回:
        list - 待处理告警列表
    """
    return get_all_pending_alarms()


def acknowledge_alarm_tool(alarm_id: int) -> dict:
    """
    确认告警工具
    
    参数:
        alarm_id: int - 告警ID
    
    返回:
        dict - 确认结果
    """
    success = acknowledge_alarm(alarm_id)
    return {
        'success': success,
        'alarm_id': alarm_id,
        'message': '告警已确认' if success else '确认失败，告警不存在'
    }