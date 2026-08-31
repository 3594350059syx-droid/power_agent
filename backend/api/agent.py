"""
Agent 对话接口
P0-5: POST /api/v1/agent/chat
集成 LangGraph Agent 工作流（intent_router → tool_executor → response_generator）

流程:
    用户消息 → Agent 工作流（意图识别 → Tool 调用 → 响应生成）
    → LLM 增强 → 返回结构化结果（reply + chart_data + diagnosis + report）
"""
import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.services.agent_service import run_agent
from backend.utils.response import success_response, error_response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agent"])


# ---------- 请求模型 ----------
class ChatRequest(BaseModel):
    message: str = Field(..., description="用户输入的自然语言消息", min_length=1)
    mode: str = Field("chat", description="对话模式: chat / diagnose / predict")


# ---------- 路由 ----------
@router.post("/agent/chat")
def agent_chat(request: ChatRequest):
    """
    Agent 对话接口

    - 接收用户自然语言输入
    - 调用 LangGraph Agent 工作流（意图识别 → Tool 调用 → 响应生成）
    - 当 DeepSeek LLM 可用时，增强诊断回复为自然语言
    - 返回 AI 回复 + 图表数据 + 诊断结果

    响应示例:
        {
            "success": true,
            "data": {
                "reply": "检测到2号锅炉主蒸汽温度异常...",
                "intent": "anomaly_detection",
                "mode": "diagnose",
                "chart_data": {
                    "device_id": "boiler_002",
                    "parameter": "steam_temp",
                    "unit": "℃",
                    "times": ["2026-07-10T00:00:00", ...],
                    "values": [540.5, ...],
                    "stats": {"min": 535.0, "max": 575.0, "avg": 548.3, "count": 1440}
                },
                "diagnosis": {
                    "device_id": "boiler_002",
                    "risk_score": 0.85,
                    "risk_level": "high",
                    "alarm_count": 2,
                    "alarms": [...],
                    "knowledge_refs": [...]
                },
                "report": "# 设备诊断报告 ...",
                "tool_calls": [
                    {"tool": "data_tool", "status": "success"},
                    {"tool": "alarm_tool", "status": "success"}
                ]
            }
        }
    """
    logger.info(f"收到对话请求: mode={request.mode}, message={request.message[:50]}...")

    try:
        result = run_agent(request.message, mode=request.mode)

        return success_response(
            data=result,
            message="ok",
        )

    except Exception as e:
        logger.error(f"Agent 对话失败: {e}", exc_info=True)
        return error_response(
            message="Agent 服务暂时不可用",
            data={
                "reply": f"抱歉，处理您的请求时发生错误：{e}",
                "intent": "error",
                "mode": request.mode,
                "chart_data": None,
                "diagnosis": None,
                "report": None,
                "tool_calls": [],
            },
        )
