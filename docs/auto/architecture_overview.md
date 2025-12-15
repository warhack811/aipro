# Architecture Overview

## System Components

Mami AI is a modern AI assistant application composed of a FastAPI backend and a dual-frontend architecture (Legacy HTML/JS and New React/Vite-based UI).

### 1. API Server (FastAPI)
The core of the application. Handles HTTP requests, manages Websockets, and orchestrates AI interactions.
- **Entrypoint**: `app/main.py`.
- **API Routes**: Located in `app/api/`. Versioned under `/api/v1`.
- **Middleware**: CORS handling, Session management.

### 2. Database
- **Primary DB**: SQL-based (likely SQLite or PostgreSQL, managed via SQLModel/SQLAlchemy).
- **Schema Management**: Alembic handles migrations (`alembic/versions`).
- **Models**: Defined in `app/core/models.py`.

### 3. AI & Chat Engine
The application routes user messages to different engines based on context and configuration:
- **Groq API**: High-speed inference for standard chat.
- **Local LLM (Ollama/Gemma)**: Privacy-focused or offline capable chat.
- **Image Gen**: Flux/Stable Diffusion integration managed via a job queue.
- **Memory/RAG**: Injects relevant past context into the system prompt.

### 4. Background Jobs & Asynchrony
- **Image Queue**: `app/image/job_queue.py` manages asynchronous image generation tasks.
- **Websockets**: Real-time updates for chat streaming and job status notifications.

## Key Flows

### Request Lifecycle
1. **Auth**: Request hits `app/main.py`. Middleware/dependencies resolve user (Session/Cookie).
2. **Routing**: `app/api/user_routes.py` handles the request (e.g., `/chat`).
3. **Processing**: `app/chat/processor.py` determines the intent (Text, Image, Memory operation).
4. **AI Inference**: Calls external API or local model handler.
5. **Response**: Streamed back to usage via `StreamingResponse` or standard JSON.

### Authentication
- Uses Session Cookies.
- "Remember Me" token mechanism.
- Invite-code based registration (`app/auth/invite_manager.py`).

### Observability
- Custom logger in `app/core/logger.py`.
- Usage limits tracked in `app/core/usage_limiter.py`.

## Configuration
- Environment variables loaded via `.env` file.
- Managed by `pydantic-settings` in `app/config.py`.
- Dynamic configuration for features and personas.
