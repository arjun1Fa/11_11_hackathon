"""
reply_generator.py
Generates personalised, RAG-grounded LLM replies for student WhatsApp messages.
All replies are addressed by the student's first name and grounded ONLY in
the consultancy's real knowledge base — never in generic internet knowledge.
"""

import sys
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


# ── Main Reply Prompt ─────────────────────────────────────────────────────────

REPLY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful and friendly study abroad counsellor at Smartilee consultancy.
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

KNOWLEDGE BASE (use ONLY this information to answer):
{rag_context}

RECENT CONVERSATION HISTORY:
{chat_history}

INSTRUCTIONS:
1. Address the student by their first name ({student_name}).
2. Answer using ONLY the knowledge base above. Never invent facts.
3. ANTI-HALLUCINATION: UNDER NO CIRCUMSTANCES should you estimate dates, fees, or requirements if they are missing from the Knowledge Base. If the answer is not in the Knowledge Base, reply exactly: "I will need to check with a senior counsellor and get back to you shortly."
4. IMPORTANT: If the student asks about a country DIFFERENT from their Preferred Country, you MUST still answer their question using the knowledge base. Acknowledge their preferred country briefly, but DO NOT refuse to give the requested info.
5. FORMATTING / TONE: If the student's Preferred tone is 'casual', use 1-2 emojis and friendly sentence structures. If the tone is 'formal', strictly use ZERO emojis and professional, academic syntax.
6. Reply in the language: {language}. If they wrote in Malayalam, reply in Malayalam.
7. Keep the reply conversational, warm, and under 150 words — this is WhatsApp.
8. Do NOT repeat the student's question back to them.

Your reply for WhatsApp:"""),
    ("human", "{message}")
])


# ── Upsell Prompt ─────────────────────────────────────────────────────────────

UPSELL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a friendly study abroad counsellor at Smartilee.
The student has been asking about {preferred_country} packages and seems genuinely interested.
Your job is to naturally weave in ONE additional benefit — a scholarship, a related package upgrade, or a lesser-known advantage — that they haven't specifically asked about.

STUDENT PROFILE:
- Name: {student_name}
- Preferred country: {preferred_country}
- Reply language: {language}

KNOWLEDGE BASE (use ONLY these facts):
{rag_context}

RECENT CONVERSATION HISTORY:
{chat_history}

INSTRUCTIONS:
1. First, directly answer or acknowledge their message briefly.
2. NATURAL TRANSITION: Use a bridging phrase like "By the way,", "Since you're interested in studying there,", or "Also," to smoothly transition into the new benefit. Do not make the upsell abrupt.
3. Keep it under 120 words. Warm, conversational WhatsApp tone.
4. Reply in: {language}
5. ANTI-HALLUCINATION: Do NOT invent scholarships, amounts, or deadlines. If no benefit exists in the Knowledge Base, do not add one.

Your upsell reply:"""),
    ("human", "{message}")
])


# ── Onboarding Prompt ─────────────────────────────────────────────────────────

ONBOARDING_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a friendly study abroad counsellor at Smartilee.
The student has just texted you, but their profile in our database is incomplete.

STUDENT PROFILE:
- Name: {student_name}
- Preferred country: {preferred_country}
- Education level: {education_level}
- Field of study: {field_of_study}
- IELTS score: {ielts_score}
- Reply language: {language}

INSTRUCTIONS:
1. Briefly acknowledge their message.
2. We MUST collect their Name, Preferred Country, Education Level, Field of Study, and IELTS Score.
3. Check the STUDENT PROFILE above. Find ONE missing piece of information (something listed as 'not provided') and ask a conversational question to get it. 
4. DO NOT ask multiple questions at once. Keep it friendly like a WhatsApp text.
5. If they just said "Hi", always ask for their name first.
6. If asking for IELTS score, ask if they have taken it yet. (If they haven't, that's fine).
7. Reply in: {language}
8. Keep it under 60 words.

Your onboarding reply:"""),
    ("human", "{message}")
])


# ── Generate Reply ────────────────────────────────────────────────────────────

def generate_reply(
    message_text: str,
    intent: str,
    sentiment: str,
    language: str,
    student_profile: dict,
    rag_context: str,
    chat_history: str = "",
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
        chat_history:    Recent conversation history string.
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
        "chat_history":     chat_history if chat_history else "No previous history.",
        "message":          message_text,
    })

    return result.content.strip()


# ── Generate Upsell Reply ─────────────────────────────────────────────────────

def upsell_reply(
    message_text: str,
    language: str,
    student_profile: dict,
    rag_context: str,
    chat_history: str = "",
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
        chat_history:    Recent conversation history string.
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
        "chat_history":      chat_history if chat_history else "No previous history.",
        "message":           message_text,
        "language":          language,
    })

    return result.content.strip()

# ── Generate Onboarding Reply ──────────────────────────────────────────────────

def onboarding_reply(
    message_text: str,
    language: str,
    student_profile: dict,
    llm: ChatOpenAI = None,
) -> str:
    """
    Generate an onboarding reply asking for ONE missing profile field.
    """
    if llm is None:
        raise ValueError("LLM client must be provided to onboarding_reply()")

    chain = ONBOARDING_PROMPT | llm
    
    # If their IELTS is -1.0, they said they haven't taken it. Don't prompt for it anymore.
    ielts_val = student_profile.get("ielts_score")
    if ielts_val == -1.0:
        ielts_display = "Student hasn't taken IELTS"
    elif ielts_val is not None:
        ielts_display = str(ielts_val)
    else:
        ielts_display = "not provided"
        
    result = chain.invoke({
        "student_name":      student_profile.get("name", "not provided") or "not provided",
        "preferred_country": student_profile.get("preferred_country", "not provided") or "not provided",
        "education_level":   student_profile.get("education_level", "not provided") or "not provided",
        "field_of_study":    student_profile.get("field_of_study", "not provided") or "not provided",
        "ielts_score":       ielts_display,
        "message":           message_text,
        "language":          language,
    })

    return result.content.strip()
