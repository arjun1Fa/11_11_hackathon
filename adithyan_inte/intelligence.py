"""
intelligence.py
---------------
Language, Intent, and Sentiment detection using LangChain + ChatGroq.
"""

import os
import logging
from langdetect import detect, DetectorFactory
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate

# Set seed for consistent langdetect results
DetectorFactory.seed = 0

logger = logging.getLogger(__name__)

# Initialize LLM
model = ChatGroq(
    model_name="llama3-8b-8192",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

def detect_language(text: str) -> str:
    """Identifies the student's language (ml, hi, ta, en, etc)."""
    try:
        if not text.strip():
            return "en"
        return detect(text)
    except Exception:
        return "en"

def detect_intent(message_text: str, context: str = "") -> str:
    """Classifies message into specific study abroad intent labels."""
    prompt = PromptTemplate.from_template(
        "You are an AI classifier for a study abroad consultancy. "
        "Classify the student's message into EXACTLY one of these labels: "
        "package_enquiry, visa_question, scholarship_query, complaint, churn_risk, general.\n\n"
        "Context: {context}\n"
        "Message: {message}\n\n"
        "Label:"
    )
    
    chain = prompt | model
    try:
        response = chain.invoke({"message": message_text, "context": context})
        label = response.content.strip().lower()
        # Validation
        valid_labels = ["package_enquiry", "visa_question", "scholarship_query", "complaint", "churn_risk", "general"]
        for vl in valid_labels:
            if vl in label:
                return vl
        return "general"
    except Exception as exc:
        logger.error("Intent detection failed: %s", exc)
        return "general"

def detect_sentiment(message_text: str) -> str:
    """Returns positive, neutral, or negative."""
    prompt = PromptTemplate.from_template(
        "Classify the sentiment of this student message as 'positive', 'neutral', or 'negative'.\n\n"
        "Message: {message}\n"
        "Sentiment:"
    )
    chain = prompt | model
    try:
        response = chain.invoke({"message": message_text})
        sentiment = response.content.strip().lower()
        if "positive" in sentiment: return "positive"
        if "negative" in sentiment: return "negative"
        return "neutral"
    except Exception:
        return "neutral"
