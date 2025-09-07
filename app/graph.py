from typing import Sequence
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent

from app.schemas.schemas import LogDiagnosisReport
from app.prompts.system_prompt import SYSTEM_PROMPT
from app.tools import parse_logs, generate_test_logs, score_report

# --- Model: Gemini 2.0 Flash ---
model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.2,
)

# --- Prompt (use a real MessagesPlaceholder) ---
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("messages"),
    ]
)

# --- Tools ---
tools: Sequence = [parse_logs, generate_test_logs, score_report]

# --- Agent ---
graph = create_react_agent(
    model=model,
    tools=tools,
    prompt=prompt,
    response_format=LogDiagnosisReport,
    name="devtriage",
)
