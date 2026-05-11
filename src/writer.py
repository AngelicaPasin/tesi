#agente writer
#genera il report tramite LLM (per ora Mistral di Ollama)
#fallback: template statico se Ollama non è disponibile

import json
#import ollama
import requests
from datetime import datetime
from config import LLM_URL, LLM_MODEL

#costruisco il prompt per il modello LLM
#i dati vengono passati come JSON strutturato — il modello NON deve fare calcoli,
#solo interpretare e scrivere in modo professionale
def build_prompt(report_data):
    return f"""
You are an aquaculture expert and your task is to interpret the provided structured monitoring data and write a professional, actionable monitoring report for a fish farming facility.

The data has already been pre-processed and analyzed by our backend systems. DO NOT perform any mathematical calculations.

Guidelines:
- Output Format: Use Markdown to format the report clearly (use headers, bullet points, and bold text for emphasis).
- Tone: Formal, objective, concise, and highly technical.
- Use English only, translate any Italian terms.
- Strict Factuality: Base your analysis EXCLUSIVELY on the provided data. Do NOT invent or hallucinate information. 
- No Recalculation: All numerical values (averages, totals, proportions, trends) are pre-computed by the backend. Use them exactly as provided — do NOT derive, recompute, or reinterpret them.
- Leverage Backend Insights: Pay special attention to the "eventi" (Critical Issues) and "warnings" already flagged in the JSON. Expand on these algorithmic findings with your domain expertise.
- Environmental Parameters: Comment on EVERY environmental parameter that has a YELLOW or RED alert level. Do not skip any flagged parameter.
- Sensor Data: If environmental data is missing, state clearly that "No environmental monitoring data was available for this period." If the data flags sensor inconsistencies (e.g., turbidity rising but oxygen stable), advise immediate hardware inspection.
- Uncertainty: Avoid absolute conclusions unless perfectly supported by the data. Use phrases like "indicates a potential issue" or "warrants further investigation."

Structure the report EXACTLY with the following sections:
1. **Executive Summary**: A brief, high-level overview of the facility's status.
2. **Fish Health & Behavior**: Detail mortality trends, appetite changes, and behavioral anomalies. Explicitly state the mortality numbers and use the pre-computed values provided in the data.
3. **Environmental & Meteorological Conditions**: Summarize water quality and weather impacts. Highlight any parameters in [YELLOW] or [RED] alert levels.
4. **Critical Issues & Sensor Anomalies**: Discuss the technical and biological warnings detected in the data.
5. **Recommended Corrective Actions**: Provide practical, immediate steps the farm manager should take based on the critical issues.
6. **Conclusions**: A final wrap-up sentence on the overall risk level for this period.

Data:
{json.dumps(report_data, indent=2, ensure_ascii=False)}
"""

#chiamo il modello deepseek
def call_llm(prompt):
    response = requests.post(
        LLM_URL, #porta locale del tunnel
        json={
            "model": LLM_MODEL, #modello su donatello
            "prompt": prompt,
            "stream": False
        },
        timeout=300
    )

    if response.status_code != 200:
        raise Exception(f"LLM error: {response.status_code} - {response.text}")

    return response.json()["response"]

#FALLBACK: template statico --> usato quando Ollama non è disponibile
#formatta un singolo parametro ambientale (es. ossigeno, ph, ...)
#gestisce automaticamente:
#- parametro assente
#- dati mancanti
#- presenza di warning
def format_parametro(nome, param):
    #caso di parametro inesistente
    if param is None:
        return f"  {nome.capitalize()}: no data available"
    
    #caso di parametro con valori non validi
    media = param.get("media")
    if media is None:
        warning = param.get("warning", "no data")
        return f"  {nome.capitalize()}: N/A ({warning})"
    
    livello = param.get("livello")
    livello_str = f" [{livello.upper()}]" if livello else ""

    #caso con dati disponibili
    lines = [
        f"  {nome.capitalize()}{livello_str}:",
        f"    Average: {param['media']}",
        f"    Min: {param['min']}  |  Max: {param['max']}",
        f"    Trend: {param['trend']}",
    ]

    #aggiunge warning se presente
    if param.get("warning"):
        lines.append(f"    Warning: {param['warning']}")
    return "\n".join(lines)

#formatta la lista delle azioni correttive
def format_azioni(azioni):
    if not azioni:
        return "  No corrective actions recorded."
    lines = []
    for a in azioni:
        lines.append(f"  [{a['data']}] {a['descrizione']} — Outcome: {a['esito']}")
    return "\n".join(lines)

#formatta gli eventi/anomalie rilevati
def format_eventi(eventi):
    if not eventi:
        return "  No critical issues detected."
    return "\n".join(f"  • {e}" for e in eventi)

#funzione che genera il report statico finale 
def generate_report_statico(report_data):
    today = datetime.today().strftime("%Y-%m-%d") #data generazione report

    #estrazione sicura delle varie sezioni dal JSON
    meta = report_data.get("metadata", {})
    periodo = meta.get("periodo", {})
    benessere = report_data.get("benessere", {})
    ambientale = report_data.get("ambientale", {})
    meteo = report_data.get("meteo", {})
    eventi = report_data.get("eventi", [])
    azioni = report_data.get("azioni_correttive", [])

    mortalita = benessere.get("mortalita", {})
    appetito = benessere.get("appetito", {})
    comportamento = benessere.get("comportamento", {})
    sintomi = benessere.get("sintomi", {})

    parametri = ambientale.get("parametri", {})
    nota_ambientale = ambientale.get("note", None)

    #costruzione del report
    report = f"""FISH FARM AUTOMATIC MONITORING REPORT:

Generated on : {today}
Company ID   : {meta.get('azienda_id', 'N/A')}
Cage ID      : {meta.get('gabbia_id', 'N/A')}
Period       : {periodo.get('data_inizio', 'N/A')} --> {periodo.get('data_fine', 'N/A')}
              ({periodo.get('numero_giorni', 'N/A')} days)

MORTALITY 
  Total deaths recorded   : {mortalita.get('totale', 'N/A')}
  Daily average           : {mortalita.get('media_giornaliera', 'N/A')}
  Trend                   : {mortalita.get('trend', 'N/A')}
  Note: counts reflect inspection findings, not necessarily daily death events.

FEEDING & BEHAVIOR
  Average appetite score  : {appetito.get('valore_medio') if appetito.get('valore_medio') is not None else 'N/A'}
  Appetite trend          : {appetito.get('trend', 'N/A')}
  Days with anomalies     : {comportamento.get('giorni_con_anomalie', 'N/A')}
  Anomalous behavior rate : {comportamento.get('percentuale_giorni_anomali', 'N/A')}

HEALTH INDICATORS
  Total sick fish         : {sintomi.get('malati_tot', 'N/A')}
  Emaciated fish          : {sintomi.get('emaciati_tot', 'N/A')}
  Ulcer cases             : {sintomi.get('ulcere_tot', 'N/A')}
  Damaged fins            : {sintomi.get('pinne_danneggiate', 'N/A')}
  Missing skin            : {sintomi.get('pelle_mancante', 'N/A')}
  Exophthalmos            : {sintomi.get('esoftalmo', 'N/A')}
  Haemorrhages            : {sintomi.get('emorragie', 'N/A')}
  Swollen abdomen         : {sintomi.get('addome_gonfio', 'N/A')}
  Abnormal coloration     : {sintomi.get('colore_anormale', 'N/A')}
  Deaths (‰)              : {sintomi.get('morti_per_mille', 'N/A')}
  Ill (per 5000)                 : {sintomi.get('malati_su_5000', 'N/A')}
  Deaths above 1‰         : {'YES' if sintomi.get('deaths_above_1_permille') else 'NO'}
  Ill above 1/5000           : {'YES' if sintomi.get('ill_above_1_per5000') else 'NO'}
  
ENVIRONMENTAL CONDITIONS
{"  Warning: " + nota_ambientale if nota_ambientale else ""}
{format_parametro("oxygen", parametri.get("ossigeno"))}

{format_parametro("pH", parametri.get("ph"))}

{format_parametro("temperature", parametri.get("temperatura"))}

{format_parametro("turbidity", parametri.get("torbidita"))}

{format_parametro("salinity", parametri.get("salinita"))}

{format_parametro("current", parametri.get("corrente"))}

{format_parametro("waves", parametri.get("onde"))}

{format_parametro("saturation", parametri.get("saturazione"))}

WEATHER & MARINE CONDITIONS (satellite/remote sensing)
{""}
{format_parametro("air temperature", meteo.get("temperatura_aria"))}

{format_parametro("wind speed", meteo.get("vento"))}

{format_parametro("wind gusts", meteo.get("raffiche"))}

{format_parametro("precipitation", meteo.get("precipitazioni"))}

{format_parametro("cloud cover", meteo.get("copertura_nuv"))}

{format_parametro("wave height", meteo.get("altezza_onde"))}

{format_parametro("swell wave height", meteo.get("onde_swell"))}

{format_parametro("wave period", meteo.get("periodo_onde"))}

{format_parametro("sea surface temperature", meteo.get("temp_mare"))}

CRITICAL ISSUES & ANOMALIES
{format_eventi(eventi)}

CORRECTIVE ACTIONS
{format_azioni(azioni)}

CONCLUSIONS
  This report provides a structured overview of the monitoring data recorded
  for cage {meta.get('gabbia_id', 'N/A')} during the specified period.
  All statistics are computed automatically from raw monitoring records.
"""

#provo a generare il report con LLM
#se Ollama non è disponibile, uso il template statico
def generate_report(report_data):
    try:
        prompt = build_prompt(report_data)
        return call_llm(prompt)
    except Exception as e:
        print(f"LLM unavailable ({e}), falling back to static template.")
        return generate_report_statico(report_data)

