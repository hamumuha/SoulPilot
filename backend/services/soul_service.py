import json
import re
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from models.db_models import Conversation, Message, User
from services.ai_service import ai_service
from services.privacy import decrypt_secret, redact_sensitive_data
from services.setting_service import get_active_config

SOUL_SYSTEM_PROMPT = (
    "你是心灵向导EmoGuide，一位专业的心理健康顾问，专注于分析用户的情感状态并提供积极、有建设性的建议。"
    "用户正在经历{emotion}的情绪。\n\n"
    "**核心原则**：\n"
    "1. 人本主义导向，相信用户具有自我成长和解决问题的潜力\n"
    "2. 以积极倾听为主（70%倾听+30%引导）\n"
    "3. 保持非评判中立态度，避免道德说教\n"
    "4. 文化敏感性（不预设用户背景）\n"
    "5. 严格遵守心理咨询伦理边界\n\n"
    "请分析用户的输入并只返回如下 JSON（不要包含 markdown 代码块、不要多余文字）：\n"
    '{{\n  "analysis": "对用户感受的详细分析（150-200字）",\n  '
    '"advice": "基于分析的具体建议（100-150字）",\n  '
    '"keywords": ["关键词1", "关键词2", "关键词3"]\n}}\n\n'
    "请提取 3 个最能代表用户感受的关键词。避免直接医疗建议、占卜/预测、价值判断。"
    "使用温暖而专业的语言风格。"
)

SOUL_FALLBACK = {
    "开心": ("你正在经历积极的情绪状态，这种快乐的感受对身心健康有重要的积极影响。积极情绪能增强免疫系统、促进创造性思维并改善人际关系。大脑会释放多巴胺与内啡肽，自然提升情绪与能量。", "珍惜并延长这种积极体验，可通过记录感恩日记、与亲友分享、投入创造性活动来实现。留意触发这种情绪的契机，以便未来创造更多类似体验。", ["快乐", "积极", "阳光"]),
    "焦虑": ("焦虑是面对不确定性或潜在威胁时的自然反应，可能表现为持续担忧、身体紧张或注意力难以集中。长期焦虑可能影响睡眠、消化与免疫，但适度焦虑也能保持警觉。", "尝试深呼吸缓解身体紧张，每天 5-10 分钟冥想或正念。把担忧具体化分析其可能性与应对策略。适当运动释放紧张。若持续影响生活可寻求专业支持。", ["压力", "担忧", "不安"]),
    "平静": ("平静是内在的平衡与稳定状态，反映了情绪的自我调节能力和心理韧性。这种状态下你能更客观清晰地看待事物，有助于专注、决策与创造力。", "通过定期冥想或正念练习培养并维持这种状态。创建支持平静的环境，保持规律作息、均衡饮食与适当运动以维持内心平衡。", ["安宁", "平和", "稳定"]),
    "难过": ("悲伤是人类基本情绪之一，通常源于失去、失败或与期望的落差。难过是对内心痛苦的自然反应，需要被承认和接纳。情绪波动是心理调整的必要部分。", "允许自己感受悲伤，不要急于压抑。找到安全的表达方式，如写日记、与信任的人交流。保持基本的自我照顾。寻求专业帮助是自我关爱的行动。", ["伤心", "低落", "情绪"]),
    "生气": ("愤怒是对感知到的不公、伤害或挫折的自然反应，可能源于边界被侵犯或期望未满足。短期会引起身体应激反应，长期未处理可能影响健康与人际关系。", "回应前给自己一个冷静期，深呼吸或短暂离开情境。识别愤怒背后的真正原因。用\"我\"陈述的沟通方式表达感受和需求。", ["愤怒", "不满", "冲突"]),
    "疲惫": ("疲惫是身心资源暂时耗尽的信号，可能源于持续压力、超负荷工作、睡眠不足或情绪消耗。这种状态提醒我们需要休息和恢复，是身体的自我保护机制。", "优先考虑休息和睡眠质量。重新评估日常安排，必要时学会委派或降低标准。引入自然散步、轻度伸展或冥想等恢复性活动。", ["疲劳", "休息", "恢复"]),
}


def soul_fallback(emotion: str, user_input: str) -> dict:
    if emotion in SOUL_FALLBACK:
        analysis, advice, keywords = SOUL_FALLBACK[emotion]
        return {"analysis": analysis, "advice": advice, "keywords": keywords}
    return {
        "analysis": f"我理解你正在经历{emotion}的情绪。记录你的感受本身就是一种自我关照。",
        "advice": "建议你尝试深呼吸、冥想或与亲友交流，关注自己的心理健康。",
        "keywords": [emotion or "感受", "情绪", "自我关怀"],
    }


def parse_soul_response(content: str, emotion: str, user_input: str) -> dict:
    text = content.strip()
    # 去除可能的 markdown 代码块包裹
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        text = m.group(0)
    try:
        parsed = json.loads(text)
        analysis = str(parsed.get("analysis", "")).strip()
        advice = str(parsed.get("advice", "")).strip()
        keywords = parsed.get("keywords", [])
        if isinstance(keywords, list):
            keywords = [str(k) for k in keywords if str(k).strip()][:3]
        else:
            keywords = []
        if analysis and advice:
            return {"analysis": analysis, "advice": advice, "keywords": keywords or soul_fallback(emotion, user_input)["keywords"]}
    except Exception:
        pass
    return soul_fallback(emotion, user_input)


async def analyze(db: Session, user: User, emotion: str, user_input: str, conversation_id: str | None) -> dict:
    """心灵之旅情绪分析：复用 hamu-pet 的 API 配置调用 AI，并将对话存入共享数据库。"""
    emotion = redact_sensitive_data(emotion)
    user_input = redact_sensitive_data(user_input)
    config = get_active_config(db)

    # 解析 AI 返回
    parsed = soul_fallback(emotion, user_input)
    used_model = None
    if config:
        messages = [
            {"role": "system", "content": SOUL_SYSTEM_PROMPT.format(emotion=emotion)},
            {"role": "user", "content": user_input or f"我感到{emotion}"},
        ]
        full, error = await ai_service.chat_completion(
            config.provider,
            config.api_url,
            decrypt_secret(config.api_key),
            config.selected_model,
            messages,
            config.name,
        )
        if error:
            parsed = soul_fallback(emotion, user_input)
        elif full:
            parsed = parse_soul_response(full, emotion, user_input)
            used_model = f"{config.name} ({config.selected_model})"

    # 写入共享对话记录（与 hamu-pet 聊天联动）
    conv_id = conversation_id
    # 防御：传入的对话可能已被用户在聊天面板删除，校验归属与存在性，
    # 失效则回退到最近的活跃对话，避免向已删除对话写入孤儿消息
    if conv_id:
        owned = (
            db.query(Conversation)
            .filter(Conversation.id == conv_id, Conversation.user_id == user.id)
            .first()
        )
        if not owned:
            conv_id = None
    if not conv_id:
        conv = (
            db.query(Conversation)
            .filter(Conversation.user_id == user.id)
            .order_by(Conversation.updated_at.desc())
            .first()
        )
        if conv:
            conv_id = conv.id
    if not conv_id:
        conv_id = str(uuid.uuid4())
        db.add(Conversation(id=conv_id, title=f"心灵之旅 · {emotion}", user_id=user.id, source="soul"))
        db.commit()

    user_content = f"[情绪:{emotion}] {user_input}".strip()
    assistant_content = redact_sensitive_data(
        f"【心理分析】{parsed['analysis']}\n\n【心灵建议】{parsed['advice']}"
    )
    db.add(Message(id=str(uuid.uuid4()), conversation_id=conv_id, role="user", content=user_content))
    db.add(Message(id=str(uuid.uuid4()), conversation_id=conv_id, role="assistant", content=assistant_content, model=used_model))
    db.query(Conversation).filter(Conversation.id == conv_id).update(
        {Conversation.updated_at: datetime.utcnow()},
        synchronize_session=False,
    )
    db.commit()

    return {
        "analysis": redact_sensitive_data(parsed["analysis"]),
        "advice": redact_sensitive_data(parsed["advice"]),
        "keywords": [redact_sensitive_data(keyword) for keyword in parsed["keywords"]],
        "conversation_id": conv_id,
    }
