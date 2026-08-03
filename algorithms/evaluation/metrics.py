import numpy as np


def calculate_rmse(y_true, y_pred) -> float:
    """
    计算均方根误差 (RMSE)

    参数:
        y_true: array-like - 真实值
        y_pred: array-like - 预测值

    返回:
        float - RMSE 值
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def calculate_mae(y_true, y_pred) -> float:
    """
    计算平均绝对误差 (MAE)

    参数:
        y_true: array-like - 真实值
        y_pred: array-like - 预测值

    返回:
        float - MAE 值
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    return float(np.mean(np.abs(y_true - y_pred)))


def calculate_mape(y_true, y_pred) -> float:
    """
    计算平均绝对百分比误差 (MAPE)

    参数:
        y_true: array-like - 真实值
        y_pred: array-like - 预测值

    返回:
        float - MAPE 值（百分比）
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    nonzero_mask = np.abs(y_true) > 1e-8
    if not np.any(nonzero_mask):
        return 0.0

    return float(np.mean(np.abs((y_true[nonzero_mask] - y_pred[nonzero_mask]) / y_true[nonzero_mask])) * 100)


def evaluate_predictions(y_true, y_pred) -> dict:
    """
    综合评估预测结果

    参数:
        y_true: array-like - 真实值
        y_pred: array-like - 预测值

    返回:
        dict - 评估指标
            - rmse: float - 均方根误差
            - mae: float - 平均绝对误差
            - mape: float - 平均绝对百分比误差
            - r2: float - 决定系数
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    rmse = calculate_rmse(y_true, y_pred)
    mae = calculate_mae(y_true, y_pred)
    mape = calculate_mape(y_true, y_pred)

    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    return {
        'rmse': round(rmse, 4),
        'mae': round(mae, 4),
        'mape': round(mape, 2),
        'r2': round(r2, 4)
    }


def compare_models(results: dict) -> dict:
    """
    对比多个模型的评估结果

    参数:
        results: dict - 模型评估结果 {model_name: {rmse, mae, ...}}

    返回:
        dict - 对比结果，包含最优模型
    """
    if not results:
        return {}

    best_model = min(results.items(), key=lambda x: x[1].get('rmse', float('inf')))

    comparison = {}
    for name, metrics in results.items():
        comparison[name] = metrics

    comparison['best_model'] = best_model[0]
    comparison['best_rmse'] = best_model[1].get('rmse', None)

    return comparison