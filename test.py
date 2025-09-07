# test.py (clean print)
from langgraph_sdk import get_sync_client

client = get_sync_client(url="http://127.0.0.1:2024")
thread = client.threads.create()

run = client.runs.create(
    thread_id=thread["thread_id"],
    assistant_id="devtriage",
    input={"messages": [
        {"role": "user",
         "content": "Generate a node-unhandled-rejection log (about 50 lines), analyze it, and return a structured report."}
    ]}
)

final = client.runs.join(thread_id=thread["thread_id"], run_id=run["run_id"])

report = final.get("structured_response") or {}
print("=== LogDiagnosisReport ===")
print("Summary:", report.get("summary"))
print("Severity:", report.get("severity"))
print("Suspected Causes:", *report.get("suspected_causes", []), sep="\n - ")
print("Evidence:", *report.get("evidence", []), sep="\n - ")
print("Next Actions:", *report.get("next_actions", []), sep="\n - ")
