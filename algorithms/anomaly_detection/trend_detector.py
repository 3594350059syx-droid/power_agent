import numpy as np
from datetime import datetime


class TrendDetector:
    """
    趋势异常检测器
    
    检测逻辑：
    - 使用滑动窗口内的线性回归计算斜率
    - 斜率超过阈值则判定为趋势异常（快速上升/下降）
    """
    
    def __init__(self, window_size: int = 60, slope_threshold: float = 0.5):
        self.window_size = window_size
        self.slope_threshold = slope_threshold
    
    def _calculate_slope(self, values: list) -> float:
        """
        使用线性回归计算斜率
        
        参数:
            values: list - 值列表 [(timestamp, value), ...]
        
        返回:
            float - 斜率
        """
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values))
        y = np.array([v[1] for v in values])
        
        n = len(x)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x * x)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope
    
    def _calculate_rate_of_change(self, values: list) -> float:
        """
        计算变化率
        
        参数:
            values: list - 值列表 [(timestamp, value), ...]
        
        返回:
            float - 变化率 (值变化/时间变化)
        """
        if len(values) < 2:
            return 0.0
        
        first = values[0]
        last = values[-1]
        
        if isinstance(first[0], datetime):
            time_diff = (last[0] - first[0]).total_seconds() / 60
        else:
            time_diff = len(values)
        
        if time_diff == 0:
            return 0.0
        
        value_diff = last[1] - first[1]
        return value_diff / time_diff
    
    def detect(self, values: list) -> dict:
        """
        检测趋势异常
        
        参数:
            values: list - 值列表 [(timestamp, value), ...]
        
        返回:
            dict - 检测结果
                - is_anomaly: bool - 是否异常
                - type: str - 异常类型 ('trend_up', 'trend_down', 'stable')
                - severity: str - 严重程度
                - score: float - 异常得分 (0-1)
                - slope: float - 线性回归斜率
                - rate_of_change: float - 变化率
                - trend_desc: str - 趋势描述
        """
        if len(values) < self.window_size:
            return {
                'is_anomaly': False,
                'type': 'stable',
                'severity': 'low',
                'score': 0.0,
                'slope': 0.0,
                'rate_of_change': 0.0,
                'trend_desc': '数据不足，无法检测趋势'
            }
        
        window = values[-self.window_size:]
        slope = self._calculate_slope(window)
        rate_of_change = self._calculate_rate_of_change(window)
        
        abs_slope = abs(slope)
        abs_rate = abs(rate_of_change)
        
        if abs_rate > self.slope_threshold:
            score = min(1.0, abs_rate / (self.slope_threshold * 2))
            
            if rate_of_change > 0:
                trend_type = 'trend_up'
                trend_desc = f"过去{self.window_size}分钟上升{abs(rate_of_change * self.window_size):.2f}"
            else:
                trend_type = 'trend_down'
                trend_desc = f"过去{self.window_size}分钟下降{abs(rate_of_change * self.window_size):.2f}"
            
            severity = 'high' if score > 0.7 else 'medium'
            
            return {
                'is_anomaly': True,
                'type': trend_type,
                'severity': severity,
                'score': round(score, 2),
                'slope': round(slope, 4),
                'rate_of_change': round(rate_of_change, 4),
                'trend_desc': trend_desc
            }
        
        else:
            trend_desc = f"趋势稳定，变化率 {rate_of_change:.4f}/分钟"
            if rate_of_change > 0:
                trend_type = 'trend_up_slow'
            elif rate_of_change < 0:
                trend_type = 'trend_down_slow'
            else:
                trend_type = 'stable'
            
            return {
                'is_anomaly': False,
                'type': trend_type,
                'severity': 'low',
                'score': 0.0,
                'slope': round(slope, 4),
                'rate_of_change': round(rate_of_change, 4),
                'trend_desc': trend_desc
            }
    
    def detect_sliding(self, values: list) -> list:
        """
        滑动窗口检测
        
        参数:
            values: list - 值列表 [(timestamp, value), ...]
        
        返回:
            list - 每个窗口的检测结果
        """
        results = []
        for i in range(len(values) - self.window_size + 1):
            window = values[i:i + self.window_size]
            result = self.detect(window)
            result['window_start'] = window[0][0]
            result['window_end'] = window[-1][0]
            results.append(result)
        
        return results
