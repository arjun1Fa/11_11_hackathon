"""
intelligence.py
Handles language detection, intent classification, and sentiment analysis
for every incoming student WhatsApp message.
"""

import sys
from langdetect import detect, LangDetectException
from langchain_core.prompts import ChatPromptTemplate
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

INTENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an AI assistant for a study abroad consultancy called Smartilee.
Classify the student's WhatsApp message into exactly one of these intent labels:

- package_enquiry   : Asking about a country package, fees, universities, or consultancy services
- visa_question     : Questions about visa process, blocked account, APS, MVV, Campus France
- scholarship_query : Asking about DAAD, Eiffel, Holland Scholarship, or other funding
- complaint         : Student is unhappy — delayed response, incorrect info, pricing concern
- churn_risk        : Signalling disengagement — "looking at other consultancies", long silence signals
- general           : Casual conversation, greeting, or completely unclassifiable message

EXAMPLES:
"What are the fees for Germany?" -> package_enquiry
"How do I apply for the DAAD?" -> scholarship_query
"I haven't heard back from my counsellor in 2 weeks" -> complaint
"Thanks, I will think about it" -> churn_risk
"How does the APS certificate work?" -> visa_question
"Hello" -> general

Additional context (from knowledge base or conversation history):
{context}

RECENT CONVERSATION HISTORY (Use this to understand the current message context):
{chat_history}

Respond with ONLY the intent label. No explanation. No punctuation. Just the label."""),
    ("human", "{message}")
])


def detect_intent(message_text: str, context: str = "", chat_history: str = "", llm: ChatOpenAI = None) -> str:
    """
    Classify a student's message into one of 6 study abroad intent labels.

    Uses LangChain ChatPromptTemplate + ChatGroq LLaMA 3 8B for fast classification.

    Args:
        message_text: The raw student message.
        context:      Optional RAG context string retrieved from knowledge base.
        chat_history: Optional string containing recent previous messages.
        llm:          The initialised LLM client from app.py.

    Returns:
        One of: package_enquiry, visa_question, scholarship_query,
                complaint, churn_risk, general.
    """
    if llm is None:
        raise ValueError("LLM client must be provided to detect_intent()")

    chain = INTENT_PROMPT | llm
    result = chain.invoke({"message": message_text, "context": context, "chat_history": chat_history})

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

SENTIMENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an AI assistant for a study abroad consultancy.
Analyse the sentiment of the following student WhatsApp message.

Respond with ONLY one of these three words:
- positive
- neutral
- negative

EXAMPLES:
"Thank you so much! This is great" -> positive
"Okay, send me the details" -> neutral
"This is absolutely terrible service" -> negative

Respond with ONLY the sentiment label. No explanation."""),
    ("human", "{message}")
])


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

# ── Information Extraction ────────────────────────────────────────────────────

import json

EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an AI data extraction engine for a study abroad consultancy.
Your job is to read the student's message and extract ONLY the profile information they explicitly mention.
Do NOT guess or infer missing information. If a piece of information is not mentioned, leave its value completely out of the JSON.

Recent conversational context (use this to understand what the student's message is replying to):
{chat_history}

Extract exactly these fields if they exist:
- "name": string
- "preferred_country": string
- "education_level": string (e.g. "Bachelors", "Masters", "High School")
- "field_of_study": string (e.g. "Computer Science", "Business", "Automotive")
- "ielts_score": number (If they explicitly say they HAVE NOT taken the IELTS, or say 'No' to a question asking if they took it, extract the number -1.0)

Respond with ONLY valid JSON and absolutely no other text.
"""),
    ("human", "{message}")
])

def extract_profile_data(message_text: str, chat_history: str, llm: ChatOpenAI) -> dict:
    """
    Reads a student's message and extracts structured profile data like name or IELTS score.
    Bypasses LangChain's strict json_schema wrapper for Groq compatibility.
    """
    try:
        # Bind the JSON mode format that Groq DOES support
        json_llm = llm.bind(response_format={"type": "json_object"})
        chain = EXTRACTION_PROMPT | json_llm
        
        result = chain.invoke({
            "message": message_text,
            "chat_history": chat_history or "No previous context."
        })
        raw_json = result.content.strip()
        
        data = json.loads(raw_json)
        
        # Clean up empty values
        extracted_dict = {k: v for k, v in data.items() if v is not None and v != ""}
        
        # Auto-map package_id based on preferred_country
        country = extracted_dict.get("preferred_country")
        if country:
            country_lower = country.lower()
            pkg_map = {
                "germany": "pkg_germany_001",
                "france": "pkg_france_001",
                "netherlands": "pkg_netherlands_001"
            }
            extracted_dict["interested_package_id"] = "pkg_general_001"
            for map_country, pkg_id in pkg_map.items():
                if map_country in country_lower:
                    extracted_dict["interested_package_id"] = pkg_id
                    break

        return extracted_dict
        
    except Exception as e:
        print(f"[WARN] Data extraction failed: {e}", file=sys.stderr)
        return {}
