## 修改内容

完成 P0-5 Agent 对话接口开发，打通 DeepSeek API，实现"自然语言输入 → AI 诊断建议"闭环——

1. **`.env` / `.env.example` 环境变量迁移**：将 `OPENAI_API_KEY` 替换为 DeepSeek 专用配置项 `DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL`，与 `settings.py` 对齐
2. **`backend/config/settings.py` 新增 DeepSeek 配置**：原 `OPENAI_API_KEY` → `DEEPSEEK_API_KEY`，并新增 `DEEPSEEK_BASE_URL`（默认 `https://api.deepseek.com/v1`）和 `DEEPSEEK_MODEL`（默认 `deepseek-chat`）
3. **`backend/api/agent.py` P0-5 接口实现**：从 4 行 TODO 空壳 → 126 行完整实现，含——
   - `ChatRequest` Pydantic 请求模型（`message` + `mode` 字段）
   - System Prompt 定义（电厂诊断助手角色 + 三段式诊断输出格式）
   - `_call_deepseek()`：使用 Python 标准库 `urllib` 直接调 DeepSeek Chat API（OpenAI 兼容接口），无需额外依赖
   - `POST /api/v1/agent/chat`：接收自然语言，调用 DeepSeek 返回诊断建议
   - Mock 降级：Key 未配置时自动返回引导提示
4. **`backend/main.py` 路由注册**：取消注释 agent_router 的两行注册代码，使接口可访问

---

## 影响模块

### 修改文件

| 文件 | 变更 |
|------|------|
| `.env` | `OPENAI_API_KEY` → `DEEPSEEK_API_KEY`（键名修正） |
| `.env.example` | 同步更新为 DeepSeek 三行配置（Key / BaseURL / Model） |
| `backend/config/settings.py` | `OPENAI_API_KEY` → `DEEPSEEK_API_KEY`；新增 `DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL` |
| `backend/api/agent.py` | TODO 空壳 → 126 行完整实现（ChatRequest + SystemPrompt + _call_deepseek + agent_chat） |
| `backend/main.py` | 注册 agent_router（第 82-83 行取消注释） |

### 接口变化

| 接口 | 状态变化 |
|------|---------|
| `POST /api/v1/agent/chat` | 从 🔨 Week 2 占位 → ✅ 完成（DeepSeek API 对接，Mock 降级保护） |
| `/api/v1/health` | 无变化 |
| `/api/v1/telemetry/live` | 无变化 |
| 其他接口 | 无变化 |

---

## 测试结果

### 1. 配置加载验证

```powershell
python -c "from backend.config.settings import settings; print('Key:', settings.DEEPSEEK_API_KEY[:8]+'...')"
```

```
Key: sk-b151c...
```

✅ `DEEPSEEK_API_KEY` 正确加载

### 2. 接口请求验证

```powershell
curl -X POST http://localhost:8000/api/v1/agent/chat -H "Content-Type: application/json" -d "{\"message\":\"分析2号机组主蒸汽温度偏高可能的原因\",\"mode\":\"diagnose\"}"
```

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "reply": "根据您的问题，2号机组主蒸汽温度偏高...",
    "mode": "diagnose"
  }
}
```

- **Status：200 OK** ✅
- **响应格式**：符合 `{success, message, data}` 统一规范 ✅
- **AI 回复**：中文诊断内容完整，DeepSeek API 调用成功 ✅

### 3. Swagger 文档验证

浏览器打开 `http://localhost:8000/docs`，**POST /api/v1/agent/chat** 接口可见，Try it out 交互正常 ✅

---

## 排错记录

| 问题 | 原因 | 解决 |
|------|------|------|
| `DEEPSEEK_API_KEY` 加载为空 | `.env` 文件中键名为 `OPENAI_API_KEY`，与 `settings.py` 不一致 | 改为 `DEEPSEEK_API_KEY` |
| `Invoke-WebRequest` 命令不可用 | 在 cmd 而非 PowerShell 中执行 | 改用 `curl` 或切换到 PowerShell |
| 终端返回中文乱码 | cmd 默认 GBK 编码，JSON 为 UTF-8 | 使用浏览器访问 `/docs` Swagger；或 PowerShell 中设 `[Console]::OutputEncoding = [Text.Encoding]::UTF8` |
