"""诊断报告接口。"""
import logging

from fastapi import APIRouter, Query

from backend.services.report_service import get_latest_report
from backend.utils.response import success_response, http_error

logger = logging.getLogger(__name__)

router = APIRouter(tags=["report"])


@router.get("/report/latest")
def latest_report(
    device_id: str = Query(..., min_length=1, description="设备编码或设备名称"),
    hours: int = Query(24, ge=1, le=72, description="分析时长（小时），1~72"),
):
    """获取指定设备最新诊断报告（Markdown）。"""
    try:
        result = get_latest_report(device_id, hours=hours)
        return success_response(data=result, message="报告生成完成")
    except ValueError as exc:
        return http_error(message=str(exc), status_code=400)
    except Exception as exc:
        logger.error(f"诊断报告生成失败: {exc}", exc_info=True)
        return http_error(message="诊断报告暂时不可用", status_code=503)