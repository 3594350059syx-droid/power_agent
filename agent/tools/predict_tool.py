from backend.services.predict_service import predict_parameter, train_and_save_model


def predict_tool(device_id: str, parameter: str, hours: int = 6) -> dict:
    """
    时序预测工具函数

    参数:
        device_id: str - 设备编码（英文ID如 "boiler_002", "turbine_003", "generator_004"，或中文名）
        parameter: str - 测点参数名（如 "steam_temp", "rpm", "power"）
        hours: int - 预测时长（小时），默认 6 小时

    返回:
        dict - 预测结果
            - device_id: str - 设备编码
            - device_name: str - 设备中文名
            - parameter: str - 参数名
            - unit: str - 单位
            - predictions: list - 预测值列表 [{"time": "...", "value": 545.2, "lower": 540, "upper": 550}, ...]
            - trend: str - 趋势 ('rising', 'falling', 'stable')
            - confidence: float - 置信度 (0-1)
            - last_actual_value: float - 最后实际值
            - last_predicted_value: float - 最后预测值
            - model_type: str - 模型类型 ('prophet' 或 'sklearn')
    """
    return predict_parameter(device_id, parameter, hours)


def train_model_tool(device_id: str, parameter: str, model_name: str = None) -> dict:
    """
    训练并保存预测模型工具

    参数:
        device_id: str - 设备编码
        parameter: str - 测点参数名
        model_name: str - 模型文件名（可选）

    返回:
        dict - 训练结果，包含模型路径和评估指标
    """
    return train_and_save_model(device_id, parameter, model_name)