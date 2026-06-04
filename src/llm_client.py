#classe che astrae il backend LLM usando LangChain
#supporta Ollama (locale e Donatello) e Gemini
#il backend attivo viene scelto da config.py

from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from config import (
    LLM_BACKEND,
    OLLAMA_LOCAL_URL, OLLAMA_LOCAL_MODEL,
    OLLAMA_DONATELLO_URL, OLLAMA_DONATELLO_MODELS, OLLAMA_DONATELLO_ACTIVE_MODEL,
    GEMINI_API_KEY, GEMINI_MODEL
)

#client LLM unificato che supporta più backend
#usa LangChain internamente per standardizzare le chiamate
#uso:
#    client = LLMClient()
#    response = client.invoke("il mio prompt qui")
class LLMClient:

    #inizializza il client llm con il backend specificato. Se backend è None, usa quello definito in config.py
    #timeout = secondi di attesa massima per una risposta (600=10 min)
    def __init__(self, backend=None, timeout=600):
        self.backend = backend or LLM_BACKEND
        self.timeout = timeout
        self.model = self._build_model()

    #costruisce il modello LangChain appropriato in base al backend scelto
    #ogni backend usa una classe LangChain diversa ma espone la stessa interfaccia:
    #    - ChatOllama --> per modelli Ollama (locale o Donatello)
    #    - ChatGoogleGenerativeAI --> per Gemini via API Google   
    #il modello viene creato una sola volta in __init__ e riusato per tutte le chiamate
    def _build_model(self):
        if self.backend == "ollama_local":
            print(f"LLM backend: Ollama locale ({OLLAMA_LOCAL_MODEL})")
            return ChatOllama(
                base_url=OLLAMA_LOCAL_URL,
                model=OLLAMA_LOCAL_MODEL,
                timeout=self.timeout
            )

        elif "donatello" in self.backend:
            model_name = OLLAMA_DONATELLO_MODELS.get(
                OLLAMA_DONATELLO_ACTIVE_MODEL,
                "qwen3-vl:32b" #fallback se la chiave non esiste
            )
            print(f"LLM backend: Ollama Donatello ({model_name})")
            #il server Donatello è raggiungibile tramite tunnel SSH
            #ssh -L 11435:localhost:11434 uniud-donatello
            return ChatOllama(
                base_url=OLLAMA_DONATELLO_URL,
                model=model_name,
                timeout=self.timeout
            )

        elif self.backend == "gemini":
            print(f"LLM backend: Gemini ({GEMINI_MODEL})")
            return ChatGoogleGenerativeAI(
                model=GEMINI_MODEL,
                google_api_key=GEMINI_API_KEY,
                timeout=self.timeout
            )

        else:
            raise ValueError(f"Backend LLM non riconosciuto: {self.backend}")

    #chiama il modello con un prompt testuale. Opzionalmente accetta un system prompt separato
    #restituisce la risposta come stringa
    #LangChain usa il formato "messages" per tutti i modelli chat:
    #i messaggi sono oggetti tipizzati (HumanMessage, SystemMessage) invece di semplici stringhe,
    #il che permette a LangChain di tradurli nel formato corretto per ciascun provider
    #
    #prompt: prompt principale (messaggio utente)
    #system_prompt: istruzioni di sistema opzionali (es. "sei un esperto di acquacoltura")
    def invoke(self, prompt, system_prompt=None):
        if system_prompt:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt)
            ]
        else:
            messages = [HumanMessage(content=prompt)] #solo messaggio utente

        response = self.model.invoke(messages)
        return response.content.strip()

    #rappresentazione leggibile dell'oggetto, utile per debugging
    def __repr__(self):
        return f"LLMClient(backend={self.backend})"

