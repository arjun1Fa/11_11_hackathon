# 🗄️ Smartilee Database (Study Abroad Edition)

This is the central memory layer for Smartilee Study Abroad. It stores student profiles, packages, conversations, and the RAG knowledge base.

## 🚀 Getting Started

1.  **Configure Environment**: Create a `.env` file in this directory:
    ```env
    SUPABASE_URL=your_supabase_url
    SUPABASE_KEY=your_supabase_service_role_key
    ```
2.  **Deploy Schema**: Run the contents of [schema.sql](./schema.sql) in your Supabase SQL Editor.
3.  **Seed Data**: Install dependencies and run the seed script:
    ```bash
    pip install -r requirements.txt
    python seed_data.py
    ```

## 🏗️ Tables

*   **`customers`**: Student profiles (Digital Twins).
*   **`packages`**: Structured details of the 3 country packages (DE, FR, NL).
*   **`knowledge_base`**: Granular facts for RAG (tuition, visa, etc.).
*   **`conversations`**: Full chat history with sentiment and intent.
*   **`enquiry_events`**: Tracks active/abandoned enquiries.
*   **`handoff_queue`**: Live queue for human counsellor escalation.
*   **`followups`**: Scheduled re-engagement messages.

## 🧠 Features

*   **pgvector RAG**: Uses `match_knowledge_base` function for semantic search.
*   **Idempotent Seeding**: Solved the `ON CONFLICT` error by adding a `UNIQUE` constraint on the `title` column of `knowledge_base`.
*   **Multi-tenant Security**: RLS policies enforce data isolation by `business_id`.
*   **Real-time Readiness**: Configured for `enquiry_events` and `handoff_queue`.

## 🛠️ Query Functions

The [query_functions.py](./query_functions.py) file provides a complete SDK for the AI Backend and Integration engineers.
