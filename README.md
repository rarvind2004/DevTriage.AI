# Dev Triage (LangGraph + Gemini Flash 2.0)

Analyze .log files, identify likely issues, and generate a debugging roadmap. Includes a test-log generator to evaluate agent performance.

## Quick start

1) Install deps and set env vars

```bash
python3 -m venv .venv        # python version 3.11+
source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env
# edit .env to add GOOGLE_API_KEY (and optionally LANGSMITH_API_KEY)
````

2. Run local LangGraph API server

```bash
langgraph dev
```

The server starts on [http://127.0.0.1:2024](http://127.0.0.1:2024) and exposes the `devtriage` graph. You can also open LangGraph Studio UI (URL printed in terminal) to chat.

3. Talk to the agent via SDK:

```bash
python test.py
```

OR (Python sync example):

```python
from langgraph_sdk import get_sync_client

client = get_sync_client(url="http://127.0.0.1:2024")
thread = client.threads.create()

# Ask the agent to generate test logs, then analyze them
run = client.runs.create(
    thread_id=thread["thread_id"],
    assistant_id="devtriage",
    input={
        "messages": [
            {
                "role": "user",
                "content": (
                    "Generate a Node.js server log with an uncaught exception and timeouts, "
                    "then diagnose it and give me an actionable roadmap."
                )
            }
        ]
    }
)

final = client.runs.join(thread_id=thread["thread_id"], run_id=run["run_id"])
print(final)
```

4. Or send your own logs

```python
log_text = open("/path/to/my_app.log", "r", encoding="utf-8").read()
run = client.runs.create(
    thread_id=thread["thread_id"],
    assistant_id="devtriage",
    input={
        "messages": [
            {"role": "user", "content": "Analyze these logs and give me a fix roadmap."},
            {"role": "user", "content": log_text}
        ]
    }
)
final = client.runs.join(thread_id=thread["thread_id"], run_id=run["run_id"])
print(final)
```

## What the agent can do

* Parse common log formats and stack traces (Python, Node/JS, Java, Nginx, Kubernetes, etc.)
* Surface anomalies: exceptions, error bursts, latency spikes, retries, memory issues
* Produce a structured **LogDiagnosisReport** with root causes, evidence, repro steps, experiments, and next actions
* Generate **synthetic logs** for benchmarking/evaluation
* Optionally score the report versus ground truth on synthetic scenarios
