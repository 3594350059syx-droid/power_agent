class ThresholdDetector:
    """
    阈值异常检测器
    
    检测逻辑：
    - 实际值 > threshold_high → 高阈值告警
    - 实际值 < threshold_low → 低阈值告警
    """
    
    def __init__(self, threshold_high: float, threshold_low: float):
        self.threshold_high = threshold_high
        self.threshold_low = threshold_low
    
    def detect(self, value: float) -> dict:
        """
        检测单个值是否超过阈值
        
        参数:
            value: float - 当前测量值
        
        返回:
            dict - 检测结果
                - is_anomaly: bool - 是否异常
                - type: str - 异常类型 ('high', 'low', 'normal')
                - severity: str - 严重程度 ('high', 'medium', 'low')
                - score: float - 异常得分 (0-1)
                - message: str - 异常描述
        """
        if value > self.threshold_high:
            excess = value - self.threshold_high
            margin = self.threshold_high - self.threshold_low
            score = min(1.0, excess / margin * 2)
            
            return {
                'is_anomaly': True,
                'type': 'threshold_high',
                'severity': 'high' if score > 0.5 else 'medium',
                'score': round(score, 2),
                'message': f"值 {value} 超过高阈值 {self.threshold_high}",
                'current_value': value,
                'threshold_value': self.threshold_high
            }
        
        elif value < self.threshold_low:
            deficit = self.threshold_low - value
            margin = self.threshold_high - self.threshold_low
            score = min(1.0, deficit / margin * 2)
            
            return {
                'is_anomaly': True,
                'type': 'threshold_low',
                'severity': 'high' if score > 0.5 else 'medium',
                'score': round(score, 2),
                'message': f"值 {value} 低于低阈值 {self.threshold_low}",
                'current_value': value,
                'threshold_value': self.threshold_low
            }
        
        else:
            return {
                'is_anomaly': False,
                'type': 'normal',
                'severity': 'low',
                'score': 0.0,
                'message': '值在正常范围内',
                'current_value': value
            }
    
    def detect_batch(self, values: list) -> list:
        """
        批量检测
        
        参数:
            values: list - 值列表，可以是 [(time, value), ...] 或 [value1, value2, ...]
        
        返回:
            list - 检测结果列表
        """
        results = []
        for item in values:
            if isinstance(item, tuple):
                timestamp, value = item
                result = self.detect(value)
                result['timestamp'] = timestamp
            else:
                result = self.detect(item)
            results.append(result)
        
        return results
