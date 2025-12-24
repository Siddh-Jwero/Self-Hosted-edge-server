from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import os
import httpx
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

app = FastAPI()

@app.post("/slack/events")
async def slack_events(request: Request):
    payload = await request.json()

    # 1. Slack URL Verification (first-time verification)
    if payload.get("type") == "url_verification":
        return JSONResponse(content={"challenge": payload["challenge"]})

    # 2. Message event from a user
    if payload.get("type") == "event_callback":
        event = payload.get("event", {})
        if event.get("type") == "message" and "bot_id" not in event:
            text = event.get("text")
            channel = event.get("channel")

            # 3. Call your RAG API (main.py's /ask endpoint)
            try:
                async with httpx.AsyncClient() as client:
                    rag_response = await client.post(
                        "http://192.168.1.99:8080/ask",  # or your public IP/hostname
                        json={"query": text},
                        timeout=30.0
                    )
                    data = rag_response.json()
                    answer = data.get("answer", "No answer received.")
            except Exception as e:
                answer = f"Error: {str(e)}"

            # 4. Send the answer back to Slack
            try:
                slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
                slack_client.chat_postMessage(channel=channel, text=answer)
            except SlackApiError as slack_err:
                print(f"Slack API error: {slack_err}")

    return {"ok": True}

if __name__ == "__main__":
    uvicorn.run("app.slack_bot:app", host="0.0.0.0", port=3000, reload=True)
