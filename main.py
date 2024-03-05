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

# Substitua 'YOUR_OPENAI_API_KEY' pela sua chave de API da OpenAI
openai.api_key = os.getenv("CHATGPT_API_KEY")

class ChatRequest(BaseModel):
    message: str

@app.post("/chat-with-assistant/")
async def chat_with_assistant(request: ChatRequest):
    try:
        response = openai.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "user", "content": request.message}
            ]
        )

        response_message = response.choices[0].message.content
        # Usando uma expressão regular para encontrar todas as ocorrências de strings JSON
        json_strings = re.findall(r'\{[^{}]*\}', response_message)
        dados = json.dumps(json_strings)
        lista_decodificada = json.loads(dados)
        print(lista_decodificada)
        return dados 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
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
    

@app.get("/")
def read_root(api_key: str = Security(get_api_key)):
    return {"Hello": "World"}

@app.get("/public")
def public():
    """A public endpoint that does not require any authentication."""
    return "Public Endpoint"

@app.get("/private")
def private(api_key: str = Security(get_api_key)):
    """A private endpoint that requires a valid API key to be provided."""
    return f"Private Endpoint. API Key: {api_key}"

