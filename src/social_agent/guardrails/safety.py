from social_agent.llm.providers import get_llm
from social_agent.llm.prompts import SAFETY_SYSTEM_PROMPT, build_safety_prompt
from social_agent.models.safety import SafetyCheckResult


async def check_content_safety(text: str) -> SafetyCheckResult:
    llm = get_llm(schema=SafetyCheckResult)
    return await llm.ainvoke(
        [
            ("system", SAFETY_SYSTEM_PROMPT),
            ("human", build_safety_prompt(text)),
        ]
    ) # type: ignore