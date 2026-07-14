"""
Agent 对话接口
P0-5 (Week 2): POST /api/v1/agent/chat
前置条件：DeepSeek API 已配置（.env 中 DEEPSEEK_API_KEY）
"""
import json
import logging
import urllib.request
import urllib.error

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.config.settings import settings
from backend.utils.response import success_response, error_response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agent"])


# ---------- 请求模型 ----------
class ChatRequest(BaseModel):
    message: str = Field(..., description="用户输入的自然语言消息", min_length=1)
    mode: str = Field("chat", description="对话模式: chat / diagnose / predict")


# ---------- System Prompt ----------
SYSTEM_PROMPT = (
    "你是 Power-Agent，一个电厂智能预警与故障诊断助手。"
    "你的职责是：\n"
    "1. 分析用户提供的设备参数和运行状态\n"
    "2. 判断是否存在异常或潜在风险\n"
    "3. 给出专业的诊断建议和处置方案\n"
    "4. 引用电厂运行规程中的相关知识\n\n"
    "请用中文回答，专业、简洁。如果用户提供的是具体设备参数，"
    "请给出「风险评分 / 异常类型 / 处置建议」三段式诊断结果。"
)


# ---------- 核心逻辑 ----------
def _call_deepseek(messages: list[dict], temperature: float = 0.7, max_tokens: int = 1024) -> str:
    """
    调用 DeepSeek Chat API（OpenAI 兼容接口）
    使用标准库 urllib，无额外依赖
    """
    url = f"{settings.DEEPSEEK_BASE_URL}/chat/completions"
    payload = json.dumps({
        "model": settings.DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else str(e)
        logger.error(f"DeepSeek API 返回 {e.code}: {body}")
        raise RuntimeError(f"DeepSeek API 错误 ({e.code})") from e
    except Exception as e:
        logger.error(f"调用 DeepSeek 失败: {e}")
        raise RuntimeError(f"AI 服务连接失败: {e}") from e


# ---------- 路由 ----------
@router.post("/agent/chat")
def agent_chat(request: ChatRequest):
    """
    Agent 对话接口
    - 接收用户自然语言输入
    - 调用 DeepSeek API 进行诊断分析
    - 返回 AI 回复 + 诊断结果
    """
    logger.info(f"收到对话请求: mode={request.mode}, message={request.message[:50]}...")

    # 未配置 API Key 时降级为 mock
    if not settings.DEEPSEEK_API_KEY or settings.DEEPSEEK_API_KEY.startswith("sk-your"):
        return success_response(
            data={
                "reply": (
                    f"【Mock 模式】已收到您的问题：「{request.message}」\n\n"
                    "⚠️ DeepSeek API Key 未配置。请编辑 .env 文件，"
                    "将 DEEPSEEK_API_KEY 替换为真实的 API Key。\n"
                    "获取地址：https://platform.deepseek.com/api_keys"
                ),
                "diagnosis": None,
            },
            message="mock",
        )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request.message},
    ]

    try:
        reply = _call_deepseek(messages)
        return success_response(
            data={
                "reply": reply,
                "mode": request.mode,
            },
            message="ok",
        )
    except RuntimeError as e:
        return error_response(
            message=f"AI 服务暂时不可用",
            data={
                "reply": f"抱歉，DeepSeek 服务暂时不可用。请稍后重试。",
                "error": str(e),
            },
        )
