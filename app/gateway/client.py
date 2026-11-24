import json

from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from openai import OpenAI

from app.config import settings

# Cloudflare AI Gateway setup:
#   - Fallback: primary settings.GROQ_MODEL → settings.GROQ_FAST_MODEL on failure
#   - Cache: turned on in the Cloudflare dashboard (AI → AI Gateway → your gateway → Settings)
#   - Retry: 2 retries per model (handled by the OpenAI client) before trying the fallback model
PRIMARY_MODEL = f"groq/{settings.GROQ_MODEL}"
FALLBACK_MODEL = f"groq/{settings.GROQ_FAST_MODEL}"
MODELS = [PRIMARY_MODEL, FALLBACK_MODEL]

# The "/compat" endpoint is OpenAI-compatible, so any OpenAI client can talk to it.
BASE_URL = (
    f"https://gateway.ai.cloudflare.com/v1/"
    f"{settings.CF_ACCOUNT_ID}/{settings.CF_GATEWAY_ID}/compat"
)


def _headers(feature: str) -> dict:
    """Cloudflare headers: gateway auth token + metadata (shown in the Cloudflare logs)."""
    return {
        "cf-aig-authorization": f"Bearer {settings.CF_AIG_TOKEN}",
        "cf-aig-metadata": json.dumps(
            {"feature": feature, "environment": "production"}
        ),
    }


# Plain OpenAI client — used where we need the raw response headers (cache status).
gateway_client = OpenAI(
    api_key=settings.GROQ_API_KEY,  # Groq key — Cloudflare forwards it to Groq
    base_url=BASE_URL,
    max_retries=2,
    default_headers=_headers("responder"),
)


def _llm(model: str, feature: str) -> ChatOpenAI:
    return ChatOpenAI(
        api_key=settings.GROQ_API_KEY,  # Groq key — Cloudflare forwards it to Groq
        base_url=BASE_URL,
        model=model,
        temperature=0,
        max_retries=2,
        default_headers=_headers(feature),
    )


def get_langchain_llm(feature: str = "rag") -> Runnable:
    """
    Returns a Cloudflare-backed LLM for LangChain nodes, with a fallback model.

    Why ChatOpenAI and not ChatGroq:
      Cloudflare AI Gateway is a proxy with an OpenAI-compatible endpoint (BASE_URL).
      ChatOpenAI lets us set base_url and extra headers; ChatGroq always talks to Groq
      directly. You are still using Groq models — Cloudflare is just in the middle.

    Note: .with_fallbacks() returns a wrapper, not a plain ChatOpenAI. .invoke() works
    the same way.
    """
    primary = _llm(PRIMARY_MODEL, feature)
    backup = _llm(FALLBACK_MODEL, feature)
    return primary.with_fallbacks([backup])


def chat_with_cache_status(
    messages: list[dict], temperature: float = 0.1
) -> tuple[str, str]:
    """
    Calls the gateway (primary model first, then fallback) and returns
    (answer_text, cache_status). cache_status is 'HIT' or 'MISS'.
    """
    last_error = None
    for model in MODELS:
        try:
            raw = gateway_client.chat.completions.with_raw_response.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            response = raw.parse()
            return response.choices[0].message.content, extract_cache_status(
                raw.headers
            )
        except Exception as e:
            last_error = e
    raise last_error


def extract_cache_status(headers) -> str:
    """Read Cloudflare's cf-aig-cache-status header. Returns 'MISS' if it is not there."""
    status = headers.get("cf-aig-cache-status", "") if headers else ""
    return status.upper() if status else "MISS"
