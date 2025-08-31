from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import google.generativeai as genai
import os, httpx, json, asyncio

# configure model
if os.getenv("GEMINI_API_KEY"):
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model_name = "gemini-2.5-pro"
else:
    raise RuntimeError("Set GEMINI_API_KEY")

class AgentState(BaseModel):
    incident_id: str
    input: str
    notes: List[str] = []
    findings: Dict[str, Any] = {}
    plan: List[str] = []
    actions: List[Dict[str, Any]] = []
    summary: Optional[str] = None

async def llm(prompt: str) -> str:
    model = genai.GenerativeModel(model_name)
    resp = await asyncio.to_thread(model.generate_content, prompt)
    return resp.text

async def intake(state: AgentState):
    state.notes.append("intake started")
    return state

async def classify(state: AgentState):
    prompt = f"You are an SRE triage agent. Given this alert or log, identify likely branch name and severity. Text: {state.input}. Respond as JSON with fields branch and severity."
    out = await llm(prompt)
    try:
        data = json.loads(out)
    except Exception:
        data = {"branch": "unknown", "severity": 3}
    state.findings.update(data)
    return state

async def plan(state: AgentState):
    prompt = f"Create a short plan of at most 4 steps to investigate and mitigate based on findings: {state.findings}. Use imperative verbs."
    text = await llm(prompt)
    steps = [s.strip("- ").strip() for s in text.splitlines() if s.strip()][:4]
    state.plan = steps
    return state

async def act(state: AgentState):
    actions = []
    if state.findings.get("branch") and state.findings["branch"] != "unknown":
        actions.append({"type": "notify", "team": state.findings["branch"], "message": "Agent suggests ownership"})
    actions.append({"type": "log", "message": "Agent executed plan"})
    state.actions = actions
    # call backend to append events
    async with httpx.AsyncClient() as client:
        for a in actions:
            try:
                await client.post(f"http://backend:3000/api/incidents/{state.incident_id}/events", json={"type": a["type"], "detail": a})
            except Exception:
                pass
    return state

async def summarize(state: AgentState):
    prompt = f"Write a three line postmortem style summary of what was done. Findings: {state.findings}. Plan: {state.plan}. Actions: {state.actions}."
    state.summary = await llm(prompt)
    return state

# graph
builder = StateGraph(AgentState)
for node in [intake, classify, plan, act, summarize]:
    builder.add_node(node.__name__, node)

builder.set_entry_point("intake")
builder.add_edge("intake", "classify")
builder.add_edge("classify", "plan")
builder.add_edge("plan", "act")
builder.add_edge("act", "summarize")
builder.add_edge("summarize", END)

memory = MemorySaver()
app_graph = builder.compile(checkpointer=memory)

app = FastAPI()

class RunReq(BaseModel):
    incidentId: str
    input: str

@app.post("/run")
async def run(req: RunReq):
    state = {"incident_id": req.incidentId, "input": req.input}
    final = await app_graph.ainvoke(state)
    return final
