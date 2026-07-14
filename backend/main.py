"""
Power-Agent 后端服务入口
- FastAPI 应用初始化
- CORS 配置
- 路由注册
- 全局异常处理
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from backend.config.settings import settings
from backend.utils.response import success_response, error_response, http_error
from backend.api.health import router as health_router

# ---------- 日志配置 ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------- 生命周期 ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动/关闭时执行"""
    logger.info("Power-Agent API 启动中...")
    yield
    logger.info("Power-Agent API 已关闭")


# ---------- 创建 FastAPI 应用 ----------
app = FastAPI(
    title="Power-Agent API",
    description="电厂智能预警系统后端接口",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---------- CORS 中间件 ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- 全局异常处理 ----------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """捕获所有未处理异常，返回统一格式"""
    logger.error(f"未处理异常: {exc}", exc_info=True)
    return http_error(message="服务器内部错误", status_code=500)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求参数校验错误"""
    logger.warning(f"参数校验失败: {exc.errors()}")
    return http_error(
        message=f"参数校验失败: {exc.errors()}",
        status_code=422,
    )


# ---------- 路由注册 ----------
app.include_router(health_router, prefix=settings.API_V1_PREFIX)

from backend.api.telemetry import router as telemetry_router
app.include_router(telemetry_router, prefix=settings.API_V1_PREFIX)

# 后续模块在此追加：
# from backend.api.agent import router as agent_router
# app.include_router(agent_router, prefix=settings.API_V1_PREFIX)


# ---------- 启动入口 ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
