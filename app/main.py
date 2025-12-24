from app.server_manager import system_metrics
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.qa import ask
import uvicorn

app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust for production
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    query: str


@app.get("/metrics")
def metrics():
    return system_metrics()

@app.post("/ask")
async def ask_endpoint(query: Query):
    answer = ask(query.query)
    return {"answer": answer}

# CLI entry
def cli_main():
    print("🔍 Local RAG System Ready. Ask your questions.")
    while True:
        query = input("\n❓ Your Query (or 'exit'): ")
        if query.lower() in ["exit", "quit"]:
            break
        result = ask(query)
        print(f"💬 {result}")

if __name__ == "__main__":
    import sys
    if "cli" in sys.argv:
        cli_main()
    else:
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
