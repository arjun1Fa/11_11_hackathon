# 📊 Smartilee Frontend (Business Dashboard)

## 📌 Overview

This is the frontend dashboard for Smartilee — an AI-powered WhatsApp commerce platform.

It allows business owners to:

* Monitor customer conversations in real-time
* View analytics and performance metrics
* Track churn risk and cart activity
* Handle escalated (handoff) conversations

---

## ⚙️ Tech Stack

* Flutter (Dart)
* supabase_flutter
* fl_chart (analytics charts)
* provider / riverpod (state management)
* Supabase Realtime

---

## 🚀 Features

### 📊 Dashboard

* Total messages today
* AI reply rate (%)
* Cart recoveries
* Customers at churn risk
* Real-time updates

---

### 💬 Conversations

* List of all conversations
* Intent badges (color-coded)
* Real-time message updates

---

### 📩 Chat View

* WhatsApp-style UI
* Inbound (customer) vs outbound (AI) messages
* Intent + action labels

---

### 👤 Customer Profile

* Full customer details (digital twin)
* Language & preferences
* Churn score visualization
* Cart contents
* Conversation history

---

### ⚠️ Handoff Queue

* Escalated conversations
* Resolve button for agents
* Real-time alerts

---

### 📉 Churn Risk List

* Customers with high churn score (>0.7)
* Re-engagement trigger

---

## 📁 Project Structure

```id="y8gqk2"
smartilee_frontend/
│
├── lib/
│   ├── main.dart
│   │
│   ├── screens/
│   │   ├── dashboard_screen.dart
│   │   ├── conversations_screen.dart
│   │   ├── conversation_detail_screen.dart
│   │   ├── customer_profile_screen.dart
│   │   ├── handoff_queue_screen.dart
│   │   ├── churn_list_screen.dart
│   │
│   ├── widgets/
│   │   ├── stat_card.dart
│   │   ├── conversation_tile.dart
│   │   ├── intent_badge.dart
│   │   ├── churn_score_bar.dart
│   │
│   ├── services/
│   │   └── supabase_service.dart
│   │
│   ├── models/
│   │   ├── customer.dart
│   │   ├── conversation.dart
│   │   ├── cart_event.dart
```

---

## 🔐 Environment Setup

Update your Supabase credentials in `main.dart`:

```id="d5h0h7"
await Supabase.initialize(
  url: 'YOUR_SUPABASE_URL',
  anonKey: 'YOUR_SUPABASE_ANON_KEY',
);
```

---

## 📦 Installation

```id="yul5rj"
flutter pub get
```

---

## ▶️ Run App

### For Web (recommended for demo)

```id="4x3bdv"
flutter run -d chrome
```

### For Mobile

```id="zhrn8b"
flutter run
```

---

## 🔄 Real-Time Data

The app uses Supabase Realtime for:

* New messages in conversations
* Handoff queue updates
* Dashboard metrics updates

---

## 🎬 Demo Flow (Hackathon Ready)

1. Open Dashboard → show churn + metrics
2. Send WhatsApp message
3. Watch it appear live in Conversations
4. AI reply shows instantly
5. Open Customer Profile → show full data
6. Trigger complaint → show Handoff Queue

---

## 🧠 Notes

* Designed for real-time experience (no manual refresh)
* Uses Supabase as single source of truth
* Optimized for demo + scalability

---

## 🔮 Future Improvements

* Authentication for multiple businesses
* Push notifications for handoffs
* Advanced analytics (conversion rates, funnels)
* Mobile-first UI enhancements
