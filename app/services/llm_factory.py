"""LLM factory: builds the configured LangChain chat model."""

from langchain_core.language_models import BaseChatModel

from app.config import settings


def get_llm() -> BaseChatModel:
    """Return the configured LLM (OpenAI or Google Gemini)."""
    if settings.llm_provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required when LLM_PROVIDER=google")
        return ChatGoogleGenerativeAI(
            model=settings.google_model,
            google_api_key=settings.google_api_key,
            temperature=0.7,
        )
    # default: OpenAI
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.7,
    )
