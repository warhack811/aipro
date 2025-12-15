# Critical Files Inventory

A shortlist of the most important files in the repository, categorized by function.

## Entrypoints
- `app/main.py`: FastAPI application entrypoint, middleware, and startup events.
- `app/config.py`: Application configuration settings (Pydantic).
- `app/websocket_sender.py`: WebSocket connection handling.

## Core Core & Infrastructure
- `app/core/database.py`: Database connection and session management.
- `app/core/models.py`: Main SQLAlchemy/SQLModel database models (User, Conversation, Message).
- `app/core/logger.py`: Centralized logging configuration.
- `app/core/usage_limiter.py`: User rate limiting logic.

## Auth & Security
- `app/auth/user_manager.py`: User creation, authentication implementation.
- `app/auth/permissions.py`: Permission checks (local model access, internet access).
- `app/auth/session.py`: Session management logic.

## Chat & AI Logic
- `app/chat/processor.py`: Core logic for processing chat messages, routing to engines.
- `app/chat/decider.py`: Logic to decide how to handle a message (store memory, etc).
- `app/ai/prompts/compiler.py`: System prompt construction (persona, context).
- `app/ai/groq/`: Groq API integration.
- `app/ai/ollama/gemma_handler.py`: Local model handler.

## API Routers
- `app/api/user_routes.py`: Main user interaction endpoints (chat, upload).
- `app/api/admin_routes.py`: Administrative endpoints.
- `app/api/auth_routes.py`: Authentication endpoints.

## Database & Migrations
- `alembic/env.py`: Alembic migration environment configuration.
- `alembic/versions/`: Database migration scripts.

## Image Generation
- `app/image/job_queue.py`: Manages the queue for image generation jobs.
- `app/image/image_manager.py`: Image file handling.
- `app/image/gpu_state.py`: GPU availability state management.

## Memory & RAG
- `app/memory/store.py`: Vector store or database interactions for long-term memory.
- `app/memory/rag.py`: RAG (Retrieval Augmented Generation) logic.

## Frontend (Critical)
- `ui/chat.html`: Main chat interface (Legacy/Current).
- `ui/js/chat-core.js`: Core frontend chat logic.
- `ui-new/src/App.tsx`: New React frontend root.
