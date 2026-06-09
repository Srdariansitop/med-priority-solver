import os
from dotenv import load_dotenv
from groq import Groq, AsyncGroq

# Cargar variables de entorno
load_dotenv()

# Cliente síncrono (para llm_analyzer)
sync_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Cliente asíncrono (para patient_generator)
async_client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

def get_sync_client() -> Groq:
    """Retorna el cliente Groq síncrono."""
    return sync_client

def get_async_client() -> AsyncGroq:
    """Retorna el cliente Groq asíncrono."""
    return async_client
