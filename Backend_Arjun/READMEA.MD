# 🧠 Smartilee AI Backend

## 📌 Overview

This is the AI backend for Smartilee — an AI-powered WhatsApp commerce platform.
It handles message understanding, decision making, and response generation using LLMs.

---

## ⚙️ Tech Stack

* Python + Flask
* Groq API (LLaMA 3)
* LangChain
* Supabase (PostgreSQL)
* langdetect

---

## 🚀 Features

* Intent detection (purchase, complaint, enquiry, etc.)
* Sentiment analysis
* Language detection (multilingual support)
* Decision engine (reply / upsell / handoff / follow-up)
* AI response generation
* Churn prediction

---

## 📁 Project Structure

```
smartilee_backend/
│
├── app.py
├── requirements.txt
├── .env.example
│
├── modules/
│   ├── intelligence.py
│   ├── decision_engine.py
│   ├── reply_generator.py
│   ├── churn_scorer.py
│
├── services/
│   ├── groq_service.py
│   ├── supabase_service.py
```

---

## 🔐 Environment Variables

Create a `.env` file:

```
GROQ_API_KEY=your_api_key
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
FLASK_PORT=5000
```

---

## 📦 Installation

```
pip install -r requirements.txt
```

---

## ▶️ Run Server

```
python app.py
```

---

## 🔌 API Endpoints

### Health Check

```
GET /health
```

### Analyze Message

```
POST /analyze
```

### Generate Reply

```
POST /generate-reply
```

### Upsell

```
POST /upsell
```

### Churn Score

```
POST /churn-score
```

---

## 🔄 Flow

1. Receive message from integration layer
2. Detect intent, sentiment, language
3. Compute churn score
4. Decide action
5. Generate response

---

## 🧠 Notes

* Uses Groq API (no local LLaMA setup required)
* Designed for real-time WhatsApp interactions
