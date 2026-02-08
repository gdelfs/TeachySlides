"""LLM factory: builds the configured LangChain chat model (cached, with timeout)."""

from langchain_core.language_models import BaseChatModel

from app.config import settings

_llm_cache: BaseChatModel | None = None


def get_llm() -> BaseChatModel:
    """Return the configured LLM (OpenAI), reused across requests to avoid reconnecting."""
    global _llm_cache
    if _llm_cache is not None:
        return _llm_cache
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
    from langchain_openai import ChatOpenAI

    _llm_cache = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.7,
        request_timeout=settings.llm_request_timeout_seconds,
    )
    return _llm_cache
