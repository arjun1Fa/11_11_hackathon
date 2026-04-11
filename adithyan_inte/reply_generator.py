"""
reply_generator.py
------------------
Personalized LLM response generation grounded in RAG context.
"""

import os
import logging
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate

logger = logging.getLogger(__name__)

model = ChatGroq(
    model_name="llama3-8b-8192",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7
)

def generate_reply(message_text, intent, sentiment, language, student_profile: dict, rag_context: str) -> str:
    """Generates a study abroad grounded reply."""
    
    name = student_profile.get("name", "there")
    pref_country = student_profile.get("preferred_country", "your country of interest")
    edu_level = student_profile.get("education_level", "higher studies")
    field = student_profile.get("field_of_study", "your field")
    tone = student_profile.get("tone_preference", "formal")
    
    tone_instr = "respectful" if tone == "formal" else "warm and friendly"
    
    prompt = PromptTemplate.from_template(
        "You are a helpful study abroad counsellor assistant. "
        "Use ONLY the following package information to answer: {rag_context}\n\n"
        "Respond ONLY in {language}. Address the student by first name: {name}.\n"
        "They are interested in {preferred_country} for {education_level} in {field_of_study}.\n"
        "Tone: {tone_instruction}.\n\n"
        "Requirements:\n"
        "- Keep reply under 3 sentences.\n"
        "- This is WhatsApp, not email.\n"
        "- Never sound like a bot.\n"
        "- Never invent fees, dates, or scholarship amounts not in rag_context.\n\n"
        "Student Message: {message}\n"
        "AI Reply:"
    )
    
    chain = prompt | model
    try:
        response = chain.invoke({
            "rag_context": rag_context,
            "language": language,
            "name": name,
            "preferred_country": pref_country,
            "education_level": edu_level,
            "field_of_study": field,
            "tone_instruction": tone_instr,
            "message": message_text
        })
        return response.content.strip()
    except Exception as exc:
        logger.error("Reply generation failed: %s", exc)
        return "Thank you for asking! Let me check the details and get back to you about our study abroad packages."

def upsell_reply(message_text, student_profile: dict, rag_context: str) -> str:
    """Acknowledges interest and suggests a relevant scholarship or benefit."""
    name = student_profile.get("name", "there")
    pref_country = student_profile.get("preferred_country", "your country of interest")
    
    prompt = PromptTemplate.from_template(
        "You are a study abroad counsellor. Acknowledge the student's interest in {preferred_country} first.\n"
        "Then, use this context to recommend ONE relevant benefit or scholarship they haven't mentioned: {rag_context}\n"
        "Keep it natural and casual for WhatsApp. Under 2 sentences.\n"
        "Address them as {name}.\n\n"
        "Student Message: {message}\n"
        "Upsell Message:"
    )
    
    chain = prompt | model
    try:
        response = chain.invoke({
            "preferred_country": pref_country,
            "rag_context": rag_context,
            "name": name,
            "message": message_text
        })
        return response.content.strip()
    except Exception:
        return f"Great choice with {pref_country}! By the way, we also have some amazing scholarship info for that region. Would you like to see it?"
