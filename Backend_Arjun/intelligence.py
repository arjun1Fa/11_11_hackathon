"""
intelligence.py
Handles language detection, intent classification, and sentiment analysis
for every incoming student WhatsApp message.
"""

import sys
from langdetect import detect, LangDetectException
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI


# ── Language Detection ────────────────────────────────────────────────────────

def detect_language(text: str) -> str:
    """
    Detect the language of a student's message.

    Returns an ISO 639-1 language code:
      'en' (English), 'hi' (Hindi), 'ml' (Malayalam), 'ta' (Tamil), etc.
    Falls back to 'en' if detection fails.

    Args:
        text: Raw message text from the student.

    Returns:
        Language code string (e.g. 'en', 'ml', 'hi', 'ta').
    """
    try:
        lang = detect(text)
        return lang
    except LangDetectException:
        print("[WARN] Language detection failed, defaulting to 'en'", file=sys.stderr)
        return "en"


# ── Intent Detection ──────────────────────────────────────────────────────────

INTENT_LABELS = [
    "package_enquiry",
    "visa_question",
    "scholarship_query",
    "complaint",
    "churn_risk",
    "general",
]

INTENT_PROMPT = PromptTemplate(
    input_variables=["message", "context"],
    template="""
You are an AI assistant for a study abroad consultancy called Smartilee.
Classify the student's WhatsApp message into exactly one of these intent labels:

- package_enquiry   : Asking about a country package, fees, universities, or consultancy services
- visa_question     : Questions about visa process, blocked account, APS, MVV, Campus France
- scholarship_query : Asking about DAAD, Eiffel, Holland Scholarship, or other funding
- complaint         : Student is unhappy — delayed response, incorrect info, pricing concern
- churn_risk        : Signalling disengagement — "looking at other consultancies", long silence signals
- general           : Casual conversation, greeting, or completely unclassifiable message

Additional context (from knowledge base or conversation history):
{context}

Student message:
\"\"\"{message}\"\"\"

Respond with ONLY the intent label. No explanation. No punctuation. Just the label.
""",
)


def detect_intent(message_text: str, context: str = "", llm: ChatOpenAI = None) -> str:
    """
    Classify a student's message into one of 6 study abroad intent labels.

    Uses LangChain PromptTemplate + ChatGroq LLaMA 3 8B for fast classification.

    Args:
        message_text: The raw student message.
        context:      Optional RAG context string retrieved from knowledge base.
        llm:          The initialised LLM client (passed from app.py).

    Returns:
        One of: package_enquiry, visa_question, scholarship_query,
                complaint, churn_risk, general.
    """
    if llm is None:
        raise ValueError("LLM client must be provided to detect_intent()")

    chain = INTENT_PROMPT | llm
    result = chain.invoke({"message": message_text, "context": context})

    # Extract and sanitise the label
    raw = result.content.strip().lower().replace(".", "").replace("\n", "")

    if raw in INTENT_LABELS:
        return raw

    # Fuzzy fallback — if response contains a valid label, extract it
    for label in INTENT_LABELS:
        if label in raw:
            return label

    print(f"[WARN] Unexpected intent label '{raw}', defaulting to 'general'", file=sys.stderr)
    return "general"


# ── Sentiment Detection ───────────────────────────────────────────────────────

SENTIMENT_LABELS = ["positive", "neutral", "negative"]

SENTIMENT_PROMPT = PromptTemplate(
    input_variables=["message"],
    template="""
You are an AI assistant for a study abroad consultancy.
Analyse the sentiment of the following student WhatsApp message.

Respond with ONLY one of these three words:
- positive
- neutral
- negative

Student message:
\"\"\"{message}\"\"\"

Respond with ONLY the sentiment label. No explanation.
""",
)


def detect_sentiment(message_text: str, llm: ChatOpenAI = None) -> str:
    """
    Detect the sentiment of a student's message.

    Args:
        message_text: The raw student message.
        llm:          The initialised LLM client (passed from app.py).

    Returns:
        One of: positive, neutral, negative.
    """
    if llm is None:
        raise ValueError("LLM client must be provided to detect_sentiment()")

    chain = SENTIMENT_PROMPT | llm
    result = chain.invoke({"message": message_text})

    raw = result.content.strip().lower().replace(".", "").replace("\n", "")

    if raw in SENTIMENT_LABELS:
        return raw

    for label in SENTIMENT_LABELS:
        if label in raw:
            return label

    print(f"[WARN] Unexpected sentiment '{raw}', defaulting to 'neutral'", file=sys.stderr)
    return "neutral"
