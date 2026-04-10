# 🚀 Smartilee — AI-Powered WhatsApp Commerce Platform

## 📌 Overview

Smartilee is an AI-powered WhatsApp automation platform that helps businesses handle customer conversations, increase sales, and reduce churn — all in real time.

It integrates AI directly into WhatsApp to:

* Understand customer intent
* Generate intelligent, personalized replies
* Recover abandoned carts
* Predict churn and re-engage users
* Escalate conversations to humans when needed

---

## 🎯 Problem Statement

Businesses using WhatsApp face major challenges:

* ❌ Missed customer messages
* ❌ Cart abandonment without follow-up
* ❌ Generic, non-personalized replies

Smartilee solves these by adding an intelligent AI layer to WhatsApp communication.

---

## 💡 Solution

Smartilee acts as a **24/7 AI assistant** that:

* Reads incoming messages
* Understands intent, sentiment, and language
* Decides the best action
* Responds instantly and intelligently
* Learns from customer behavior over time

---

## 🧠 Core Features

### 🤖 AI Intelligence

* Intent detection (purchase, complaint, enquiry, etc.)
* Sentiment analysis
* Multilingual support (Malayalam, Hindi, etc.)
* Personalized response generation (LLM-based)

---

### 🛍️ Commerce Automation

* Cart abandonment detection
* Smart follow-up messages
* Upselling recommendations

---

### 📉 Churn Prediction

* Detects inactive users
* Scores churn risk
* Automatically triggers re-engagement

---

### ⚠️ Human Handoff

* Escalates complex or negative conversations
* Notifies business owner
* Stops AI when human takes over

---

### 📊 Business Dashboard

* Real-time conversation monitoring
* Customer profiles (digital twin)
* Analytics & insights
* Handoff queue management

---

## 🏗️ System Architecture

Smartilee is built as a **4-layer system**:

```id="c8e0h1"
WhatsApp (Happilee)
        ↓
Integration Layer (Node.js)
        ↓
AI Backend (Flask + Groq + LLaMA 3)
        ↓
Database (Supabase)
        ↓
Frontend Dashboard (Flutter)
```

---

## ⚙️ Tech Stack

### 🧠 AI / Backend

* Python + Flask
* Groq API (LLaMA 3)
* LangChain
* langdetect

### 🔌 Integration

* Node.js + Express
* Happilee (WhatsApp API)
* Axios
* node-cron

### 🗄️ Database

* Supabase (PostgreSQL)
* Real-time subscriptions
* Row-Level Security (RLS)

### 📊 Frontend

* Flutter (Web + Mobile)
* supabase_flutter
* fl_chart

---

## 🔄 How It Works

1. Customer sends a WhatsApp message
2. Happilee forwards it to the backend webhook
3. Integration layer sends it to AI backend
4. AI:

   * Detects intent, sentiment, language
   * Computes churn score
   * Decides action
5. AI generates response using LLM
6. Reply is sent back via WhatsApp
7. Data is stored in Supabase
8. Dashboard updates in real time

---

## 📁 Project Structure

```id="c3n7f1"
smartilee/
│
├── backend/        # AI backend (Flask)
├── integration/    # WhatsApp + routing (Node.js)
├── frontend/       # Dashboard (Flutter)
├── database/       # Schema & queries
│
├── .gitignore
├── README.md
```

---

## 🚀 Getting Started

### 1. Clone Repository

```id="7p8t2n"
git clone https://github.com/your-username/smartilee.git
cd smartilee
```

---

### 2. Setup Backend

```id="7q1caa"
cd backend
pip install -r requirements.txt
python app.py
```

---

### 3. Setup Integration

```id="08h7h7"
cd integration
npm install
node server.js
```

---

### 4. Setup Frontend

```id="r6m7ya"
cd frontend
flutter pub get
flutter run -d chrome
```

---

## 🔐 Environment Variables

Each service requires its own `.env` file.

### Backend

```id="x1yq7j"
GROQ_API_KEY=
SUPABASE_URL=
SUPABASE_KEY=
```

### Integration

```id="xk6h8k"
HAPPILEE_TOKEN=
AI_BACKEND_URL=
SUPABASE_URL=
SUPABASE_KEY=
```

---

## 🎬 Demo Flow

1. Open dashboard → show metrics
2. Send WhatsApp message
3. Watch message appear live
4. AI reply is generated instantly
5. Open customer profile → show data
6. Trigger complaint → handoff to human

---

## 🧠 Key Highlights

* ⚡ Real-time system (no delays)
* 🌍 Multilingual AI support
* 🧩 Modular microservice architecture
* 🤖 LLM-powered intelligence
* 📊 Full business analytics dashboard

---

## 🔮 Future Improvements

* Multi-business support (SaaS model)
* Payment integration
* Advanced analytics & forecasting
* Voice message support
* Mobile app for business owners

---

## 🤝 Team Roles

* AI / Backend Engineer — Intelligence & decision making
* Integration Engineer — WhatsApp + automation
* Database Engineer — Data architecture
* Frontend Engineer — Dashboard UI

---

## 📜 License

MIT License

---

## ❤️ Final Note

Smartilee is built to transform how businesses communicate on WhatsApp — turning conversations into conversions with AI.
