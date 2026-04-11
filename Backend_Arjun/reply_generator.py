"""
reply_generator.py
Generates personalised, RAG-grounded LLM replies for student WhatsApp messages.
All replies are addressed by the student's first name and grounded ONLY in
the consultancy's real knowledge base — never in generic internet knowledge.
"""

import sys
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI


# ── Main Reply Prompt ─────────────────────────────────────────────────────────

REPLY_PROMPT = PromptTemplate(
    input_variables=[
        "student_name",
        "preferred_country",
        "education_level",
        "field_of_study",
        "ielts_score",
        "tone",
        "language",
        "intent",
        "sentiment",
        "rag_context",
        "message",
    ],
    template="""
You are a helpful and friendly study abroad counsellor at Smartilee consultancy.
You are replying to a WhatsApp message from a prospective student.

STUDENT PROFILE:
- Name: {student_name}
- Preferred country: {preferred_country}
- Education level: {education_level}
- Field of study: {field_of_study}
- IELTS score: {ielts_score}
- Preferred tone: {tone}

MESSAGE CONTEXT:
- Detected intent: {intent}
- Detected sentiment: {sentiment}
- Reply language: {language}

KNOWLEDGE BASE (use ONLY this information to answer — do not invent fees, dates, or scholarship amounts):
{rag_context}

STUDENT'S MESSAGE:
\"\"\"{message}\"\"\"

INSTRUCTIONS:
1. Address the student by their first name ({student_name}).
2. Answer using ONLY the knowledge base above. Never invent or assume facts.
3. Reply in the language: {language}. If the student wrote in Malayalam, reply in Malayalam. Same for Hindi, Tamil, etc.
4. Keep the reply conversational, warm, and under 150 words — this is WhatsApp, not an email.
5. If the knowledge base does not contain the answer, say you will check and get back to them shortly.
6. Do NOT repeat the student's question back to them.

Your reply:
""",
)


# ── Upsell Prompt ─────────────────────────────────────────────────────────────

UPSELL_PROMPT = PromptTemplate(
    input_variables=[
        "student_name",
        "preferred_country",
        "rag_context",
        "message",
        "language",
    ],
    template="""
You are a friendly study abroad counsellor at Smartilee.
The student has been asking about {preferred_country} packages and seems genuinely interested.
Your job is to naturally weave in one additional benefit — a scholarship, a related package upgrade,
or a lesser-known advantage — that they haven't specifically asked about.

STUDENT NAME: {student_name}
PREFERRED COUNTRY: {preferred_country}
REPLY LANGUAGE: {language}

KNOWLEDGE BASE (use ONLY these facts):
{rag_context}

STUDENT'S MESSAGE:
\"\"\"{message}\"\"\"

INSTRUCTIONS:
1. First, directly answer or acknowledge their message briefly.
2. Then naturally mention ONE additional relevant benefit or opportunity from the knowledge base.
3. Keep it under 120 words. Warm, conversational WhatsApp tone.
4. Reply in: {language}
5. Do NOT invent scholarships, amounts, or deadlines not in the knowledge base.

Your upsell reply:
""",
)


# ── Generate Reply ────────────────────────────────────────────────────────────

def generate_reply(
    message_text: str,
    intent: str,
    sentiment: str,
    language: str,
    student_profile: dict,
    rag_context: str,
    llm: ChatOpenAI = None,
) -> str:
    """
    Generate a personalised, RAG-grounded reply for the student.

    Args:
        message_text:    The raw student WhatsApp message.
        intent:          Detected intent label.
        sentiment:       Detected sentiment label.
        language:        Detected language code (e.g. 'en', 'ml', 'hi').
        student_profile: Dict from Supabase with name, country, education, ielts, etc.
        rag_context:     Relevant knowledge base rows as a single string.
        llm:             Initialised LLM client from app.py.

    Returns:
        Reply text string — ready to send to the student via WhatsApp.
    """
    if llm is None:
        raise ValueError("LLM client must be provided to generate_reply()")

    chain = REPLY_PROMPT | llm
    result = chain.invoke({
        "student_name":     student_profile.get("name", "Student"),
        "preferred_country": student_profile.get("preferred_country", "your preferred country"),
        "education_level":  student_profile.get("education_level", "not specified"),
        "field_of_study":   student_profile.get("field_of_study", "not specified"),
        "ielts_score":      student_profile.get("ielts_score", "not specified"),
        "tone":             student_profile.get("tone_preference", "friendly"),
        "language":         language,
        "intent":           intent,
        "sentiment":        sentiment,
        "rag_context":      rag_context if rag_context else "No specific context available.",
        "message":          message_text,
    })

    return result.content.strip()


# ── Generate Upsell Reply ─────────────────────────────────────────────────────

def upsell_reply(
    message_text: str,
    language: str,
    student_profile: dict,
    rag_context: str,
    llm: ChatOpenAI = None,
) -> str:
    """
    Generate a reply that acknowledges the student's enquiry and naturally
    introduces an additional package benefit or scholarship opportunity.

    Args:
        message_text:    The raw student WhatsApp message.
        language:        Detected language code.
        student_profile: Dict from Supabase with name and preferred_country.
        rag_context:     Relevant knowledge base context string.
        llm:             Initialised LLM client from app.py.

    Returns:
        Upsell reply text string — ready to send via WhatsApp.
    """
    if llm is None:
        raise ValueError("LLM client must be provided to upsell_reply()")

    chain = UPSELL_PROMPT | llm
    result = chain.invoke({
        "student_name":      student_profile.get("name", "Student"),
        "preferred_country": student_profile.get("preferred_country", "your preferred country"),
        "rag_context":       rag_context if rag_context else "No specific context available.",
        "message":           message_text,
        "language":          language,
    })

    return result.content.strip()
