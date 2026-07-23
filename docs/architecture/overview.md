# AI Service — Architecture Overview

## Layers

| Layer | Package | Responsibility |
|---|---|---|
| Presentation | `src/presentation/` | HTTP/WS/SSE routing, auth middleware |
| Application | `src/application/` | Pipeline orchestration, step sequencing |
| Domain | `src/domain/` | Types, interfaces, prompt contracts |
| Infrastructure | `src/infrastructure/` | LLM SDKs, vector store, storage, workers |

## Runtime pipelines

```
┌──────────────┐     SSE      ┌─────────────────────────────────────┐
│  Chat client │ ──────────►  │  chat_runtime pipeline              │
└──────────────┘             │  1. load_agent_config                │
                             │  2. retrieve_context (RAG)           │
┌──────────────┐     WS       │  3. build_prompt                     │
│  Twilio      │ ──────────►  │  4. call_llm (streaming)             │
│  Media Stream│             │  5. handle_tool_calls                │
└──────────────┘             │  6. persist_conversation_turn        │
                             └─────────────────────────────────────┘

┌──────────────┐   HTTP POST  ┌─────────────────────────────────────┐
│  Backend     │ ──────────►  │  evaluation pipeline                │
│  (trigger)   │             │  1. load_agent_config                │
└──────────────┘             │  2. simulate_user_turn (LLM)         │
                             │  3. run_agent_turn (LLM)             │
                             │  4. check_termination                │
                             │  5. score_with_judge (LLM)           │
                             │  6. persist_evaluation_result        │
                             └─────────────────────────────────────┘

┌──────────────┐ Dramatiq job ┌─────────────────────────────────────┐
│  Backend     │ ──────────►  │  indexing pipeline                  │
│  (KB upload) │             │  1. fetch_document_from_storage      │
└──────────────┘             │  2. parse_document                   │
                             │  3. chunk_text                       │
                             │  4. embed_chunks (LLM)               │
                             │  5. upsert_to_vector_store           │
                             │  6. notify_backend (indexed status)  │
                             └─────────────────────────────────────┘
```
