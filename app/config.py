import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    # --- GEMINI EMBEDDINGS ---
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # --- VECTOR DB (QDRANT) ---
    QDRANT_URL = os.getenv("QDRANT_CLUSTER_ENDPOINT")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION = "enterprise_rag"

    # --- REASONING ENGINE (GROQ) ---
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = "openai/gpt-oss-120b"      # main model (planner + responder)
    GROQ_FAST_MODEL = "openai/gpt-oss-20b"  # fast model (guardrails + fallback)
    GROQ_FALLBACK_API_KEY = os.getenv("GROQ_FALLBACK_API_KEY")

    # --- LLM GATEWAY (CLOUDFLARE AI GATEWAY) ---
    CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
    CF_GATEWAY_ID = os.getenv("CF_GATEWAY_ID")
    CF_AIG_TOKEN = os.getenv("CF_AIG_TOKEN")

    # Streamlit UI -> FastAPI
    BACKEND_URL = os.getenv("BACKEND_URL")

    # Eval judge LLM (keep separate from main key to avoid rate-limiting the live app)
    JUDGE_GROQ = os.getenv("JUDGE_GROQ")
    
# Apply LangChain environment variables for automatic tracing
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGSMITH_TRACING", "true")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "rag_scale_test")
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

settings = Settings()