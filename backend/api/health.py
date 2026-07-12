"""
健康检查接口
用于监控和负载均衡器检测服务是否存活
"""
from fastapi import APIRouter
from backend.utils.response import success_response

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """
    健康检查接口
    - 返回服务状态
    - 用于 K8s/Docker 存活探针
    """
    return success_response(
        data={"status": "healthy", "service": "power-agent-api"},
        message="Service is running",
    )
