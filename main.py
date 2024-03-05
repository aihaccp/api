from fastapi import HTTPException, status, Security, FastAPI
from fastapi.security import APIKeyHeader, APIKeyQuery
from dotenv import load_dotenv
from pydantic import BaseModel
import openai
import time
import re
import json
import os

API_KEYS = [
    "9d207bf0-10f5-4d8f-a479-22ff5aeff8d1",
    "f47d4a2c-24cf-4745-937e-620a5963c0b8",
    "b7061546-75e8-444b-a2c4-f19655d07eb8",
]

api_key_query = APIKeyQuery(name="api-key", auto_error=False)
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
) -> str:
    """Retrieve and validate an API key from the query parameters or HTTP header.

    Args:
        api_key_query: The API key passed as a query parameter.
        api_key_header: The API key passed in the HTTP header.

    Returns:
        The validated API key.

    Raises:
        HTTPException: If the API key is invalid or missing.
    """
    if api_key_query in API_KEYS:
        return api_key_query
    if api_key_header in API_KEYS:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )

load_dotenv()

app = FastAPI(title="AiHACCP API")

openai.api_key = os.getenv("CHATGPT_API_KEY")
if not openai.api_key:
    raise ValueError("A variável de ambiente CHATGPT_API_KEY não está definida.")


class ChatRequest(BaseModel):
    message: str
    
@app.post("/gpt-assistant/")
async def chat_with_assistant(request: ChatRequest):
    try:
        # Abrindo e carregando os arquivos CSV
        
        thread = openai.beta.threads.create()
        message = openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=request.message
        )
        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id="asst_ta6yiyUQ0lyIM7P6RYfn6peE"
        )
        run = openai.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        while run.status != "completed":
            keep_retrieving_run = openai.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            print(f"Run status: {keep_retrieving_run.status}")

            if keep_retrieving_run.status == "completed":
                print("\n")
                break

        # Retrieve messages added by the Assistant to the thread
        all_messages = openai.beta.threads.messages.list(
            thread_id=thread.id
        )

        print("###################################################### \n")
        print(f"USER: {message.content[0].text.value}")
        print(f"ASSISTANT: {all_messages.data[0].content[0].text.value}")
        return all_messages.data[0].content[0].text.value
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

