#configurazione del db

DB_URI = "mysql+pymysql://root:psw@localhost/marinet_db"
REPORT_PATH = "../output/report.md"

#scelgo il backend attivo
#opzioni disponibili:
# "ollama_local" --> mistral sul mio PC
# "ollama_donatello" --> modello su Donatello (vedi OLLAMA_DONATELLO_ACTIVE_MODEL)
# "gemini" --> Gemini 2.0 Flash (Google AI)
LLM_BACKEND = "ollama_donatello"

OLLAMA_LOCAL_URL   = "http://localhost:11434"
OLLAMA_LOCAL_MODEL = "mistral"

#ollama su Donatello (via tunnel SSH porta 11435)
OLLAMA_DONATELLO_URL = "http://localhost:11435"

OLLAMA_DONATELLO_MODELS = {
    "gpt-oss": "gpt-oss:20b",
    "qwen":     "qwen3-vl:32b",
    "gemma":    "gemma4:latest",
    "mistral":  "mistral:latest"
}

#modello attivo su Donatello (usato quando LLM_BACKEND contiene "donatello")
OLLAMA_DONATELLO_ACTIVE_MODEL = "qwen" #cambia in "gemma" per comparare

GEMINI_API_KEY = "key"
GEMINI_MODEL   = "gemini-2.0-flash"

