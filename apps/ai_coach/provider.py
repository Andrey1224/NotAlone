"""AI provider integration."""

from core.config import settings

# Prompt templates for different hint types
EMPATHY_PROMPT = """
Ты - помощник по эмпатичному общению. На основе контекста диалога предложи эмпатичную фразу или вопрос
на русском языке, который поможет поддержать собеседника.

Правила:
- Будь кратким (1-2 предложения)
- Используй активное слушание
- Валидируй чувства
- Не давай советов или диагнозов
- Не обещай "всё исправить"

Контекст: {context}

Предложи эмпатичную фразу:
"""

QUESTION_PROMPT = """
Ты - помощник по ведению диалога. На основе контекста предложи открытый вопрос на русском языке,
который поможет продолжить разговор и лучше понять собеседника.

Правила:
- Задавай открытые вопросы
- Не будь навязчивым
- Уважай границы
- Фокусируйся на чувствах и опыте

Контекст: {context}

Предложи вопрос:
"""

BOUNDARY_PROMPT = """
Ты - помощник по безопасному общению. На основе контекста напомни о границах общения на русском языке.

Правила:
- Напоминай о том, что нельзя давать мед/юрид советы
- Предупреждай о необходимости профессиональной помощи при серьёзных проблемах
- Будь тактичным

Контекст: {context}

Предложи напоминание о границах:
"""

PROMPTS = {"empathy": EMPATHY_PROMPT, "question": QUESTION_PROMPT, "boundary": BOUNDARY_PROMPT}


async def get_coaching_hint(context: str, hint_type: str = "empathy") -> str:
    """
    Get coaching hint from AI provider.

    Args:
        context: Anonymized chat context
        hint_type: Type of hint to generate

    Returns:
        Generated hint text
    """
    # TODO: Implement actual LLM integration
    # This is a placeholder implementation

    if not settings.ai_enabled:
        return "AI подсказки отключены"

    prompt_template = PROMPTS.get(hint_type, EMPATHY_PROMPT)
    prompt = prompt_template.format(context=context)

    # TODO: Call OpenAI/Anthropic API
    # Example:
    # response = await openai.ChatCompletion.acreate(
    #     model=settings.ai_model,
    #     messages=[{"role": "user", "content": prompt}],
    #     max_tokens=150,
    # )
    # return response.choices[0].message.content

    # Placeholder responses
    placeholder_hints = {
        "empathy": "Я понимаю, как это может быть сложно. Расскажите больше о том, что вы чувствуете?",
        "question": "Как вы справлялись с подобными ситуациями раньше?",
        "boundary": "Напоминаю: мы не заменяем профессиональную помощь. При серьезных проблемах обратитесь к специалисту.",
    }

    return placeholder_hints.get(hint_type, placeholder_hints["empathy"])
