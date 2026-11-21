# LLM Chat Backend Assessment

A Python-based LLM backend built with **FastAPI**, demonstrating LLM integration, token usage tracking, cost estimation, retry handling, asynchronous execution, tool calling, conversation memory, and secure session-based chat APIs.

## Technology Stack

- Python 3.14
- FastAPI
- OpenAI Python SDK
- Anthropic Python SDK
- Ollama — local LLM runtime
- Pydantic and Pydantic Settings
- asyncio
- Tenacity
- pytest and pytest-cov

## Project Features

### Task 1 — LLM Integration and Usage Tracking

- LLM integration using OpenAI-compatible and Anthropic-compatible SDKs.
- Local Ollama model integration.
- Token usage tracking.
- Estimated API cost calculation.
- Daily usage logging.
- Chat and usage API endpoints.
- Streaming and benchmarking support.

### Task 2 — Retry Mechanism and Async Execution

**Retry handling**
- Automatic retries for HTTP 429 and HTTP 5xx errors.
- Maximum of five total attempts.
- Exponential backoff with randomized jitter.
- Retry attempt and waiting-time logging.
- Non-retryable errors, such as HTTP 401, are not retried.

**Asynchronous execution**
- AsyncOpenAI integration.
- Sequential and concurrent execution of multiple prompts.
- `asyncio.gather()` for concurrent execution.
- `asyncio.Semaphore(3)` to limit concurrent requests.
- Individual request failure isolation.
- Sequential versus concurrent benchmark reporting.

### Task 3 — Tool Calling and Conversation Memory

- Tool execution through a dedicated tool loop.
- Tool argument validation and error handling.
- Multiple tool executions in a single round.
- Conversation history management.
- Token-budget monitoring.
- Summarization of older conversation messages.
- Preservation of important early conversation facts.
- Retention of recent conversation messages.

### Task 4 — Session Management API and Security

- Create individual chat sessions.
- Send messages within a session.
- Retrieve session message history.
- Conversation context maintained across requests.
- API-key authentication using the `x-api-key` header.
- Secure API-key comparison using `secrets.compare_digest`.
- Pydantic request and response validation.
- Message length validation: 1–2000 characters.
- HTTP error handling for missing sessions, oversized messages, and LLM failures.
- CORS restricted to configured frontend origins.
- Dependency injection for application settings, LLM clients, and session storage.

**Session storage note:** Sessions are stored in memory. They are lost when the application restarts.

## Project Structure

```text
llm-chat-backend-assessment/
│
├── app/
│   ├── llm/
│   ├── memory/
│   ├── routes/
│   ├── sessions/
│   ├── tools/
│   ├── auth.py
│   ├── config.py
│   ├── dependencies.py
│   ├── exceptions.py
│   └── main.py
│
├── scripts/
├── tests/
│   ├── test_api.py
│   ├── test_async_service.py
│   ├── test_conversation.py
│   ├── test_llm_service.py
│   ├── test_retry.py
│   ├── test_sessions.py
│   ├── test_task1.py
│   └── test_tool_loop.py
│
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/ajayharrieshtYT260949/llm-chat-backend-assessment.git
cd llm-chat-backend-assessment
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

Create your local `.env` file:

```powershell
Copy-Item .env.example .env
```

Configure the following variables:

```env
OLLAMA_BASE_URL=http://localhost:11434

OPENAI_API_KEY=ollama
ANTHROPIC_API_KEY=ollama

OPENAI_MODEL=qwen2.5:1.5b
ANTHROPIC_MODEL=qwen2.5:1.5b

CHAT_API_KEY=replace-with-a-long-random-secret

TOKEN_BUDGET=6000
MAX_OUTPUT_TOKENS=1000
```

Replace the chat API key with a strong private secret. Never commit your actual `.env` file.

### 5. Start Ollama

Install Ollama and download the configured model:

```powershell
ollama pull qwen2.5:1.5b
```

Make sure the Ollama service is running.

**Note:** The project is configured to use a local Ollama model. The placeholder SDK keys are not paid OpenAI or Anthropic API credentials.

## Running the Application

Start the FastAPI development server:

```powershell
uvicorn app.main:app --reload
```

API base URL:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

## Session API Endpoints

The session endpoints require the `x-api-key` request header.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/sessions` | Create a new session |
| POST | `/sessions/{session_id}/chat` | Send a message in a session |
| GET | `/sessions/{session_id}/messages` | Retrieve session message history |

### Example: Create a session

```http
POST /sessions
x-api-key: your-secret-key
```

### Example: Send a chat message

```http
POST /sessions/{session_id}/chat
Content-Type: application/json
x-api-key: your-secret-key
```

```json
{
  "message": "Explain Python functions."
}
```

### Example: Retrieve message history

```http
GET /sessions/{session_id}/messages
x-api-key: your-secret-key
```

### Important HTTP status codes

| Status | Meaning |
|---|---|
| 201 | Session created |
| 200 | Request successful |
| 401 | API key missing |
| 403 | Invalid API key |
| 404 | Session not found |
| 413 | Message too large or token budget exceeded |
| 422 | Request validation failed |
| 502 | LLM service failure |

## CORS Configuration

The application allows these frontend origins by default:

- `http://localhost:5173`
- `http://localhost:3000`

These origins can be adjusted in the application configuration.

## Running Tests

Run the complete automated test suite:

```powershell
python -m pytest -v
```

Run tests with code coverage:

```powershell
python -m pytest -v --cov=app --cov-report=term-missing
```

### Verified Test Results

- Total tests: **61**
- Passed: **61**
- Failed: **0**
- Total application code coverage: **88%**

Tests include API endpoints, authentication, session management, conversation memory, LLM integration, retry handling, asynchronous execution, and tool calling.

## Async Performance Benchmark

Run the benchmark:

```powershell
python -m scripts.benchmark_async
```

The benchmark compares sequential and concurrent LLM requests, with a maximum concurrency of three.

Observed results from the local Ollama environment:

| Metric | Sequential | Concurrent |
|---|---:|---:|
| Questions | 10 | 10 |
| Successful requests | 10 | 10 |
| Failed requests | 0 | 0 |
| Execution time | 207.143 sec | 215.149 sec |

Measured speedup: **0.96x**

In this local Ollama environment, concurrent execution was approximately 3.9% slower than sequential execution. Asynchronous execution does not guarantee faster inference; performance depends on the model, hardware, and inference server capacity.

## Security

- Keep `.env` private.
- Never commit real API keys or secrets.
- Session endpoints require API-key authentication.
- API keys are compared using constant-time comparison.
- CORS is restricted to configured origins.
- Generated logs and temporary benchmark files should remain outside version control unless explicitly required.

## Development Progress

- [x] Task 1 — LLM Integration and Usage Tracking
- [x] Task 2 — Retry Mechanism and Async Execution
- [x] Task 3 — Tool Calling and Conversation Memory
- [x] Task 4 — Session Management API and Security

## Author

Ajay Harriesh T.