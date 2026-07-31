class RiskScorer:
    """
    综合风险评分器
    
    评分逻辑：
    risk = 0.5 * threshold_score + 0.5 * trend_score
    
    风险等级：
    - 0.0 - 0.3: low (低风险)
    - 0.3 - 0.6: medium (中等风险)
    - 0.6 - 1.0: high (高风险)
    """
    
    def __init__(self, threshold_weight: float = 0.5, trend_weight: float = 0.5):
        self.threshold_weight = threshold_weight
        self.trend_weight = trend_weight
    
    def calculate_risk(self, threshold_result: dict, trend_result: dict) -> dict:
        """
        计算综合风险评分
        
        参数:
            threshold_result: dict - 阈值检测结果
            trend_result: dict - 趋势检测结果
        
        返回:
            dict - 风险评分结果
                - risk_score: float - 综合风险评分 (0-1)
                - level: str - 风险等级 ('low', 'medium', 'high')
                - breakdown: dict - 各检测项得分
                - recommendations: list - 建议措施
        """
        threshold_score = threshold_result.get('score', 0.0)
        trend_score = trend_result.get('score', 0.0)
        
        risk_score = (threshold_score * self.threshold_weight + 
                      trend_score * self.trend_weight)
        
        if risk_score < 0.3:
            level = 'low'
        elif risk_score < 0.6:
            level = 'medium'
        else:
            level = 'high'
        
        recommendations = self._generate_recommendations(
            threshold_result, 
            trend_result, 
            risk_score
        )
        
        return {
            'risk_score': round(risk_score, 2),
            'level': level,
            'breakdown': {
                'threshold_score': round(threshold_score, 2),
                'trend_score': round(trend_score, 2),
                'threshold_weight': self.threshold_weight,
                'trend_weight': self.trend_weight
            },
            'recommendations': recommendations
        }
    
    def _generate_recommendations(self, threshold_result: dict, trend_result: dict, risk_score: float) -> list:
        """
        生成建议措施
        """
        recommendations = []
        
        if threshold_result.get('is_anomaly', False):
            t_type = threshold_result.get('type', '')
            if t_type == 'threshold_high':
                recommendations.append(f"当前值超过高阈值，建议检查设备运行状态")
            elif t_type == 'threshold_low':
                recommendations.append(f"当前值低于低阈值，建议检查设备运行状态")
        
        if trend_result.get('is_anomaly', False):
            t_type = trend_result.get('type', '')
            trend_desc = trend_result.get('trend_desc', '')
            if t_type == 'trend_up':
                recommendations.append(f"检测到快速上升趋势: {trend_desc}")
            elif t_type == 'trend_down':
                recommendations.append(f"检测到快速下降趋势: {trend_desc}")
        
        if risk_score >= 0.6:
            recommendations.append("风险等级较高，建议立即关注并采取措施")
        elif risk_score >= 0.3:
            recommendations.append("风险等级中等，建议持续监控")
        
        if not recommendations:
            recommendations.append("当前运行状态正常，建议继续监控")
        
        return recommendations
    
    def batch_score(self, records: list) -> list:
        """
        批量计算风险评分
        """
        results = []
        for record in records:
            threshold_result = record.get('threshold', {})
            trend_result = record.get('trend', {})
            risk = self.calculate_risk(threshold_result, trend_result)
            results.append({
                **record,
                'risk': risk
            })
        
        return results
