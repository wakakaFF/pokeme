import base64
import json
import os

from openai import AsyncOpenAI

# 聊天模型（MiniMax-M2.7，支持文本流式）
chat_client = AsyncOpenAI(
    api_key=os.environ.get("CHAT_API_KEY"),
    base_url=os.environ.get("CHAT_BASE_URL"),
    timeout=60.0,
)
CHAT_MODEL = os.environ.get("CHAT_MODEL", "MiniMax-M2.7").strip('"')

# 视觉识别模型（支持图片输入的模型，如 Claude）
vision_client = AsyncOpenAI(
    api_key=os.environ.get("VISION_API_KEY"),
    base_url=os.environ.get("VISION_BASE_URL"),
    timeout=60.0,
)
VISION_MODEL = os.environ.get("VISION_MODEL", "claude-sonnet-4-6").strip('"')

# 兼容旧代码
client = chat_client
MODEL = CHAT_MODEL

SYSTEM_PROMPT = """你是「动物图鉴」AI 系统，专门识别动物并生成图鉴条目。

【重要】你的回复必须且只能是一个 JSON 对象，不能有任何其他文字、解释、markdown 代码块、警告或说明。

规则：
1. 如果图片中没有动物，只返回：{"error": "no_animal"}
2. 如果有动物，只返回以下 JSON，不含任何其他文字：
{
  "number": "随机4位数字字符串，如0847",
  "name": "动物中文名，尽量精确到品种",
  "scientific_name": "拉丁学名",
  "category": "动物类别，只能是以下之一：哺乳动物/鸟类/爬行动物/两栖动物/鱼类/昆虫/其他",
  "height": "估算体型高度或体长，带单位",
  "weight": "估算体重，带单位",
  "habitat": "自然栖息地",
  "diet": "食性简短描述",
  "predator": "主要天敌",
  "conservation": "IUCN保护状态，格式如：无危(LC) / 近危(NT) / 易危(VU) / 濒危(EN) / 极危(CR)",
  "description": "50字以内，图鉴风格，有趣略带拟人，适合儿童阅读",
  "rarity": "根据常见程度：普通 / 稀有 / 极稀有 / 传说",
  "attributes": ["属性1", "属性2"],
  "narration": "80字以内，语音播报风格，以'发现了一只[动物名]！'开头，介绍外观特征和有趣习性，口语化，适合朗读"
}

稀有度判定：
- 传说：极危(CR) 或 野外灭绝物种
- 极稀有：濒危(EN) 或 易危(VU) 物种
- 稀有：近危(NT) 或 不常见野生动物
- 普通：无危(LC) 且 日常常见"""


CHAT_SYSTEM_PROMPT = """你是「PokeMe 动物图鉴」的 AI 助手，名叫"图图"。你热爱动物，知识渊博，风格活泼友好，略带宝可梦图鉴的感觉。

你可以：
- 介绍各种动物的习性、栖息地、保护状态等知识
- 回答关于动物的有趣问题
- 分享动物小知识和趣闻

语气轻松有趣，适合各年龄段。回答简洁，不超过200字，除非用户明确要求详细。"""


def _log(msg):
    with open("F:/fun/pokeme/debug.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def _strip_think(text: str) -> str:
    """去掉推理模型输出的 <think>...</think> 思考过程"""
    import re
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


async def chat_stream(messages: list):
    """流式输出，自动过滤 <think>...</think> 推理过程。"""
    stream = await chat_client.chat.completions.create(
        model=CHAT_MODEL,
        max_tokens=800,
        messages=[{"role": "system", "content": CHAT_SYSTEM_PROMPT}] + messages,
        stream=True,
    )

    OPEN, CLOSE = "<think>", "</think>"
    buf = ""
    in_think = False

    async for chunk in stream:
        delta = (chunk.choices[0].delta.content or "") if chunk.choices else ""
        if not delta:
            continue
        buf += delta

        while buf:
            if in_think:
                idx = buf.find(CLOSE)
                if idx != -1:
                    buf = buf[idx + len(CLOSE):]
                    in_think = False
                else:
                    buf = buf[-len(CLOSE):]   # 保留尾部防止标签被截断
                    break
            else:
                idx = buf.find(OPEN)
                if idx != -1:
                    if idx > 0:
                        yield buf[:idx]
                    buf = buf[idx + len(OPEN):]
                    in_think = True
                else:
                    safe = max(0, len(buf) - len(OPEN))
                    if safe:
                        yield buf[:safe]
                    buf = buf[safe:]
                    break

    if buf and not in_think:
        yield buf


async def identify_animal(image_bytes: bytes, media_type: str = "image/jpeg") -> tuple:
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    image_url = f"data:{media_type};base64,{image_b64}"

    _log(f"[DEBUG] vision base_url={vision_client.base_url} model={VISION_MODEL} img_b64_len={len(image_b64)}")
    try:
        response = await vision_client.chat.completions.create(
            model=VISION_MODEL,
            max_tokens=1000,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_url, "detail": "auto"}},
                        {"type": "text", "text": "识别图中的动物，生成图鉴条目。"},
                    ],
                },
            ],
        )
    except Exception as e:
        import traceback
        _log(f"[ERROR] API调用失败: {type(e).__name__}: {e}")
        _log(traceback.format_exc())
        raise

    import re as _re
    msg = response.choices[0].message
    _log(f"[DEBUG] 完整message: role={msg.role} content={msg.content!r} extra={vars(msg)}")
    raw_text = _strip_think(msg.content or "")
    # 去掉 markdown 代码块包裹
    raw_text = _re.sub(r"```(?:json)?\s*", "", raw_text).strip()
    _log(f"[DEBUG] 模型返回: {raw_text!r}")

    start = raw_text.find("{")
    end = raw_text.rfind("}") + 1
    if start == -1 or end == 0 or start >= end:
        raise ValueError(f"模型返回内容无法解析为JSON: {raw_text[:200]}")
    json_str = raw_text[start:end]

    try:
        result = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON解析失败: {e}")
    return result, raw_text
