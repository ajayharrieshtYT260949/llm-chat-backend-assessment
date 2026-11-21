# LLM Chat Backend Assessment



A Python-based LLM backend built with FastAPI, integrating LLM providers through compatible APIs. This project demonstrates LLM integration, token usage tracking, cost estimation, retry handling, and asynchronous request execution.



**Current development milestones:** Task 1 and Task 2 completed.



## Technology Stack



- Python

- FastAPI

- OpenAI Python SDK

- Anthropic Python SDK

- Ollama (local LLM runtime)

- Tenacity (retry handling)

- asyncio (asynchronous execution)

- pytest (automated testing)



## Project Features



### Task 1 â€” LLM Integration and Usage Tracking



- LLM integration using OpenAI-compatible and Anthropic-compatible SDKs.

- Local Ollama integration without requiring paid cloud API keys.

- Token usage tracking.

- Estimated API cost calculation.

- Daily usage logging.

- Chat and usage API endpoints.

- Streaming and benchmarking support.



### Task 2 â€” Retry Mechanism and Async Execution



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



## Project Structure



```text

llm-chat-backend-assessment/

â”‚

â”œâ”€â”€ app/

â”‚   â”œâ”€â”€ llm/

â”‚   â”‚   â”œâ”€â”€ service.py

â”‚   â”‚   â”œâ”€â”€ async_service.py

â”‚   â”‚   â”œâ”€â”€ retry.py

â”‚   â”‚   â”œâ”€â”€ cost.py

â”‚   â”‚   â”œâ”€â”€ token_counter.py

â”‚   â”‚   â””â”€â”€ usage_tracker.py

â”‚   â”‚

â”‚   â”œâ”€â”€ routes/

â”‚   â”‚   â”œâ”€â”€ chat.py

â”‚   â”‚   â””â”€â”€ usage.py

â”‚   â”‚

â”‚   â”œâ”€â”€ config.py

â”‚   â””â”€â”€ main.py

â”‚

â”œâ”€â”€ scripts/

â”‚   â””â”€â”€ benchmark_async.py

â”‚

â”œâ”€â”€ tests/

â”‚   â”œâ”€â”€ test_task1.py

â”‚   â”œâ”€â”€ test_llm_service.py

â”‚   â”œâ”€â”€ test_api.py

â”‚   â”œâ”€â”€ test_retry.py

â”‚   â””â”€â”€ test_async_service.py

â”‚

â”œâ”€â”€ .env.example

â”œâ”€â”€ .gitignore

â”œâ”€â”€ pytest.ini

â”œâ”€â”€ requirements.txt

â””â”€â”€ README.md

```



## Installation and Setup



### 1. Clone the repository



```bash

git clone https://github.com/ajayharrieshtYT260949/llm-chat-backend-assessment.git

cd llm-chat-backend-assessment

```



### 2. Create a virtual environment



```bash

python -m venv .venv

```



Activate it on Windows PowerShell:



```powershell

.venv\\Scripts\\Activate.ps1

```



### 3. Install dependencies



```bash

pip install -r requirements.txt

```



### 4. Configure environment variables



Create a `.env` file using `.env.example` as a template.



Configure your local Ollama URL, model name, and application settings.



### 5. Start Ollama



Install and run Ollama, then download a model:



```bash

ollama pull qwen2.5:1.5b

```



Make sure the Ollama service is running.



**Note:** This project uses Ollama through OpenAI-compatible and Anthropic-compatible interfaces. The local integration does not mean that actual OpenAI or Anthropic cloud services were used.



## Running the Application



Start the FastAPI server:



```bash

uvicorn app.main:app --reload

```



Open the interactive API documentation:



http://127.0.0.1:8000/docs



## Running Tests



Run the complete test suite:



```bash

python -m pytest -v

```



Run retry tests:



```bash

python -m pytest tests/test_retry.py -v

```



Run asynchronous execution tests:



```bash

python -m pytest tests/test_async_service.py -v

```



### Current Test Results



- Total tests: 35

- Passed: 35

- Failed: 0



## Async Performance Benchmark



Run the benchmark:



```bash

python -m scripts.benchmark_async

```



The benchmark compares ten sequential LLM requests against ten concurrent LLM requests, with a maximum concurrency of three.



### Observed Results



| Metric | Sequential | Concurrent |

|---|---:|---:|

| Questions | 10 | 10 |

| Successful requests | 10 | 10 |

| Failed requests | 0 | 0 |

| Execution time | 207.143 sec | 215.149 sec |



**Measured speedup:** 0.96x



In this local Ollama environment, concurrent execution was approximately 3.9% slower than sequential execution. This demonstrates that asynchronous execution does not guarantee faster inference: actual performance depends on the model, available hardware, and inference server capacity.



## Security



- Keep `.env` private.

- Never commit real API keys or secrets.

- Generated logs and benchmark output should remain outside version control unless explicitly required for submission.



## Development Progress



- [x] Task 1 â€” LLM Integration and Usage Tracking

- [x] Task 2 â€” Retry Mechanism and Async Execution

- [ ] Future assessment tasks



## Author



Ajay Harriesh T.


