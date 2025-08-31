# DevTriage AI • MVP with Agentic Architecture

---

## What changed vs original spec

* Added an agentic layer built with **LangGraph** by default, with an **optional ADK or OpenAI Agents SDK path**. The agent executes triage, plans actions, and generates postmortems. It keeps durable state and hands off to humans when needed.
* Backend now exposes tool style endpoints for the agent and emits events to the stream bus. It also manages timers inside Postgres for SLA enforcement.
* Frontend adds a Runbooks page, an Agent Runs viewer, and live incident rooms with chat and annotation.

---

## High level architecture

```
                         ┌──────────────────────────────┐
                         │   React Frontend on Vercel   │
                         │  Dashboard • Inputs • Chat   │
                         │  Status • History • Runs     │
                         └─────────────┬────────────────┘
                                       │ WebSocket
                                       │ REST
                            ┌──────────▼──────────┐
                            │   NestJS Backend    │
                            │  Auth • Incidents   │
                            │  SLA • Runbooks     │
                            │  Kafka producer     │
                            │  Postgres access    │
                            └───────┬─────┬───────┘
                                    │     │
                     Kafka topics ◄─┘     └─► pg_cron timers
                                    │
                     ┌──────────────▼───────────────┐
                     │  Python Agent Engine         │
                     │  LangGraph state machine     │
                     │  Tools: code search, RAG,    │
                     │  alerting, ticketing         │
                     └──────────────┬───────────────┘
                                    │
                          Object storage for logs
                               and artifacts
```

---

## Monorepo layout

```
.devtriage/
  README.md                   # this doc
  docker-compose.yml
  .env.example                # root env sample
  packages/
    frontend/                 # React + Vite + Tailwind + Socket.IO client
    backend/                  # NestJS + Prisma + Kafka + WebSocket gateway
    agent/                    # Python FastAPI + LangGraph + Gemini client
  infra/
    prisma/                   # db schema
    sql/                      # migrations and pg_cron helpers
    k8s/                      # optional manifests for later
```

---

## Environment variables

Create a file named `.env` in repo root. Replace placeholders.

```
# shared
POSTGRES_URL=postgresql://postgres:postgres@localhost:5432/devtriage
JWT_SECRET=devtriage-local
KAFKA_BROKER=localhost:9092
KAFKA_CLIENT_ID=devtriage

# mail
MAIL_FROM=no-reply@devtriage.local
SENDGRID_KEY=your_sendgrid_key

# frontend
VITE_WS_URL=ws://localhost:3000
VITE_API_URL=http://localhost:3000/api

# agent
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
VECTORSTORE_URL=postgresql://postgres:postgres@localhost:5432/devtriage
AGENT_URL=http://agent:8000
```

---

## Docker compose for local dev

```yaml
version: "3.9"
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: devtriage
    ports:
      - "5432:5432"
    volumes:
      - dbdata:/var/lib/postgresql/data

  kafka:
    image: redpandadata/redpanda:v24.1.5
    command: ["redpanda", "start", "--overprovisioned", "--smp", "1", "--memory", "512M", "--reserve-memory", "0M", "--node-id", "0", "--check=false"]
    ports:
      - "9092:9092"
      - "9644:9644"

  backend:
    build: ./packages/backend
    env_file: .env
    depends_on: [db, kafka]
    ports:
      - "3000:3000"

  agent:
    build: ./packages/agent
    env_file: .env
    depends_on: [db, backend]
    ports:
      - "8000:8000"

  frontend:
    build: ./packages/frontend
    env_file: .env
    depends_on: [backend]
    ports:
      - "5173:5173"

volumes:
  dbdata:
```

---

## Database schema with Prisma

The backend includes a `/prisma/schema.prisma` for codegen. A mirror of this file also exists under `infra/prisma/schema.prisma` for infra workflows.

---

## Run locally

```
# from repo root
cp .env.example .env
# fill keys
npm run dev:all
```

If not using a helper script, run docker compose:

```
docker compose up --build
```

Then open Frontend on http://localhost:5173  
Backend on http://localhost:3000  
Agent on http://localhost:8000

---

## Deploy

* Frontend to Vercel. Set VITE variables. Point to backend URL.
* Backend to Render or Railway with Docker. Connect to a managed Postgres. Set KAFKA broker and mail key.
* Agent to Render as a separate service. Provide GEMINI key. Allow outbound to backend.
* Use Redpanda Cloud or Upstash for a managed stream bus. Create topic `sla.events`.
* Use Neon or Supabase for Postgres. Enable pg_cron if available, else run the simple ticker.

---

## Agent tools and prompts

**Tools**

* append_event(incident_id, type, detail)
* get_incident(incident_id)
* search_code(query)  placeholder provides basic grep over attached logs or code index
* notify(team, message)  delegates to backend mailer or chat integration

**Prompt seeds**

* System prompt for classify node: short JSON only, with branch and severity
* Plan node: at most four steps, clear imperative verbs
* Summarize node: three line postmortem summary

---

## Playbooks

Make a file `packages/backend/runbooks.yml` with entries like

```yaml
- name: api 500 spike
  detect: "rate(http_5xx) > 0.05 for 5m"
  actions:
    - check: "deploy diff last 30m"
    - check: "error budget and SLO"
    - mitigate: "roll back to previous deployment"
```

The agent can load these into context for planning.

---

## Analytics

* MTTR computed per incident id and plotted on dashboard
* SLA misses counted from SLATimer firings
* Bottlenecks identified by time spent between specific event types

---

## Testing

* Backend unit tests with Jest for services
* Agent graph tests by invoking nodes with sample inputs
* Frontend cypress smoke for create incident and run agent

---

## Swap to ADK or OpenAI Agents

* ADK path uses its project structure and skill declarations while keeping the same tool endpoints
* OpenAI Agents path uses the Agents SDK to create a planner with tools backed by backend routes

Both are drop in alternatives for the LangGraph engine in this MVP.

---

## Next steps for production

* Move timers to `pg_cron` jobs or listen notify channel to avoid polling
* Add code index and log retrieval with a proper vector store
* Add access control and audit trails
* Add streaming traces with Langfuse and OpenTelemetry
