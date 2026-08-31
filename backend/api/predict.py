# P1-1 / P1-2: 预测相关接口
# - GET /api/v1/predict          时序预测（Prophet / sklearn 降级）
# - GET /api/v1/predict/model    模型自适应选择（按高/低负荷工况）
# 依赖：B 的 backend/services/predict_service.py 与 algorithms/evaluation/model_selector.py
from fastapi import APIRouter, Query

from backend.utils.response import success_response, http_error
from backend.services.predict_service import predict_parameter
from algorithms.evaluation.model_selector import select_model_by_condition

router = APIRouter(tags=["predict"])


@router.get("/predict")
def predict(
    device_id: str = Query(..., description="设备编码（英文ID如 boiler_002，或中文名如 2号锅炉）"),
    parameter: str = Query(..., description="测点参数名（如 steam_temp、rpm、power）"),
    hours: int = Query(6, ge=1, le=72, description="预测时长（小时），1~72"),
):
    """预测设备某参数未来趋势，供前端/C 的监控面板趋势展示调用。"""
    result = predict_parameter(device_id, parameter, hours)
    if "error" in result:
        return http_error(message=result["error"], status_code=400)
    return success_response(data=result, message="预测完成")


@router.get("/predict/model")
def select_model(
    device_id: str = Query(..., description="设备编码（英文ID或中文名）"),
    parameter: str = Query("stator_temp", description="测点参数名"),
):
    """P1-2 模型自适应选择：按当前工况（高/低负荷）自动选择/训练对应预测模型。"""
    result = select_model_by_condition(device_id, parameter)
    if "error" in result:
        return http_error(message=result["error"], status_code=400)
    return success_response(data=result, message="模型选择完成")
