"""
DeepSeek LLM 客户端
P0-3: 封装 DeepSeek API 调用，供意图识别与参数抽取使用

优先使用 langchain-openai（A.md 要求），未安装时降级为 urllib（零依赖）。
两种路径返回值一致，调用方无需感知底层差异。
"""
import json
import logging
import urllib.error
import urllib.request

from backend.config.settings import settings

logger = logging.getLogger(__name__)


# ---------- 可用性检查 ----------

def is_llm_available() -> bool:
    """
    检查 DeepSeek LLM 是否可用（API Key 已配置且非占位符）。
    """
    key = settings.DEEPSEEK_API_KEY
    if not key:
        return False
    # 过滤占位符
    placeholders = ("sk-your", "sk-你的", "sk-xxx", "sk-placeholder")
    return not key.startswith(placeholders)


# ---------- 核心调用 ----------

def call_deepseek(
    messages: list[dict],
    temperature: float = 0.1,
    max_tokens: int = 512,
) -> str:
    """
    调用 DeepSeek Chat API（OpenAI 兼容接口）。

    优先使用 langchain-openai，未安装时降级为 urllib。

    Args:
        messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
        temperature: 低温度用于结构化输出（默认 0.1）
        max_tokens: 意图识别 JSON 不需要太多 token（默认 512）

    Returns:
        LLM 响应文本

    Raises:
        ValueError: API Key 未配置
        RuntimeError: API 调用失败
    """
    if not is_llm_available():
        raise ValueError("DEEPSEEK_API_KEY 未配置或为占位符")

    # 路径 1: langchain-openai（A.md 推荐方式）
    try:
        return _call_via_langchain(messages, temperature, max_tokens)
    except ImportError:
        logger.info("langchain-openai 未安装，降级为 urllib 调用")

    # 路径 2: urllib（零依赖降级）
    return _call_via_urllib(messages, temperature, max_tokens)


# ---------- 路径 1: langchain-openai ----------

def _call_via_langchain(
    messages: list[dict],
    temperature: float,
    max_tokens: int,
) -> str:
    """通过 langchain-openai 调用 DeepSeek API"""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import (
        AIMessage,
        HumanMessage,
        SystemMessage,
    )

    llm = ChatOpenAI(
        model=settings.DEEPSEEK_MODEL,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # 转换消息格式
    lc_messages = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            lc_messages.append(SystemMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))
        else:
            lc_messages.append(HumanMessage(content=content))

    response = llm.invoke(lc_messages)
    return response.content


# ---------- 路径 2: urllib 降级 ----------

def _call_via_urllib(
    messages: list[dict],
    temperature: float,
    max_tokens: int,
) -> str:
    """通过 urllib 调用 DeepSeek API（零依赖）"""
    url = f"{settings.DEEPSEEK_BASE_URL}/chat/completions"
    payload = json.dumps(
        {
            "model": settings.DEEPSEEK_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
    ).encode("utf-8")

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
