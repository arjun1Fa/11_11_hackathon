# Smartilee WhatsApp Simulator

A local WhatsApp-like UI to test the Integration Layer **without** a real WhatsApp account.

## How to run

> Make sure your main integration layer (`app.py`) is already running on port 5000.

```bash
# From adithyan_inte/simulator/
python simulator_server.py
```

Then open: **http://localhost:5050**

## How to demo with Ngrok

### Option A — Expose the Simulator UI (for the judges)
```bash
ngrok http 5050
```
Share the ngrok URL so anyone can type into the WhatsApp simulator from their browser.

### Option B — Expose the Integration Layer (for real Meta webhook)
```bash
ngrok http 5000
```
Then paste that URL into the Meta Developer Console as your webhook URL.

## What happens when you send a message

1. You type a message in the UI.
2. The simulator formats it as a real **Meta Webhook JSON payload**.
3. It POSTs to `http://localhost:5000/webhook` (your integration layer).
4. Your integration layer parses it, calls your teammate's AI backend.
5. The AI reply is logged to Supabase.
6. The simulator **polls Supabase every 2 seconds** and displays the reply.

## Dev Panel

The right-side panel shows:
- **Logs tab**: Live JSON payloads being sent/received.
- **Config tab**: Change the simulated phone number or point the simulator to a different webhook URL (e.g., a teammate's ngrok URL).
