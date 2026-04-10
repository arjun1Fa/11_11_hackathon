# 🗄️ Smartilee Database (Supabase)

## 📌 Overview

This is the central data layer of Smartilee.
It stores customer profiles, conversations, cart events, and system data.

---

## ⚙️ Tech Stack

* Supabase (PostgreSQL)
* SQL
* Supabase Realtime
* Row-Level Security (RLS)

---

## 🧱 Tables

### customers

* Stores customer profile (digital twin)

### conversations

* Stores all messages (inbound + outbound)

### cart_events

* Tracks cart activity (active, abandoned, recovered)

### products

* Product catalog for upselling

### handoff_queue

* Tracks escalations to human agents

### followups

* Scheduled messages

---

## ⚡ Features

* Real-time subscriptions
* Secure multi-tenant access (RLS)
* Query functions for all services
* Demo seed data

---

## 🔐 Security (RLS)

* Each business accesses only its own data
* Based on `business_id = auth.uid()`

---

## 🔄 Real-Time Setup

Enable for:

* `cart_events`
* `handoff_queue`

Used for:

* cart recovery triggers
* live dashboard updates

---

## 📊 Example Queries

### Get customer

```
SELECT * FROM customers WHERE phone_number = '...';
```

### Log conversation

```
INSERT INTO conversations (...)
```

---

## 🌱 Seed Data

* Customer: Priya
* Abandoned cart
* Sample products
* Conversation history

---

## 🧠 Notes

* Acts as the “memory” of Smartilee
* Shared across backend, integration, and frontend
