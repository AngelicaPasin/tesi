#agente writer
#genera il report tramite LLM
#fallback: template statico se l'LLM non è disponibile

import json
from datetime import datetime
from llm_client import LLMClient
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)

#agente writer che genera il report di monitoraggio usando un LLM
class WriterAgent:

    def __init__(self, llm_client=None):
        self.llm = llm_client or LLMClient()
    
    #provo a generare il report con LLM
    #se l'LLM non è disponibile, uso il template statico
    def generate_report(self, report_data, previous_problems=None):
            try:
                prompt = self._build_prompt(report_data, previous_problems)
                return self.llm.invoke(prompt)
            except Exception as e:
                print(f"LLM unavailable ({e}), falling back to static template.")
                return self._generate_report_statico(report_data)

    #costruisco il prompt per il modello LLM
    #i dati vengono passati come JSON strutturato — il modello NON deve fare calcoli,
    #ma solo interpretare e scrivere in modo professionale
    def _build_prompt(self, report_data, previous_problems=None):
        cot = report_data.get("cot_insights", {})
        cot_str = ""
        if cot:
            cot_str = "\n\nADDITIONAL INSIGHTS FROM ITERATIVE TABLE REASONING:\n"
            for key, result in cot.items():
                cot_str += f"\nQuestion: {result['question']}\n"
                cot_str += f"Reasoning chain: {' -> '.join(result['operation_chain'])}\n"
                cot_str += f"Finding: {result['insight']}\n"
        
        problems_str = ""
        if previous_problems:
            problems_str = "\n\nPREVIOUS ATTEMPT PROBLEMS TO FIX:\n"
            problems_str += "The previous report generation had these issues. Fix ALL of them:\n"
            for p in previous_problems:
                problems_str += f"- {p}\n"

        return f"""
    You are an aquaculture expert and your task is to interpret the provided structured monitoring data and write a professional, actionable monitoring report for a fish farming facility.

    The data has already been pre-processed and analyzed by our backend systems. DO NOT perform any mathematical calculations.

    Guidelines:
    - Output Format: Use Markdown to format the report clearly (use headers, bullet points, and bold text for emphasis).
    - Tone: Formal, objective, concise, and highly technical.
    - Use English only, translate any Italian terms.
    - Strict Factuality: Base your analysis EXCLUSIVELY on the provided data. Do NOT invent or hallucinate information. 
    - No Recalculation: All numerical values (averages, totals, proportions, trends) are pre-computed by the backend. Use them exactly as provided — do NOT derive, recompute, or reinterpret them.
    - No Assumptions: Do NOT interpret numerical values without context. Do not judge whether a value is "low", "high", "poor", or "good" unless the data explicitly provides an alert level or reference scale. If a field contains a "nota" or "note" key, treat it as a strict instruction on how to interpret that value.
    - No Invented Thresholds: Do NOT state any specific numerical threshold values in your report. Only reference alert levels (GREEN, YELLOW, RED) as provided in the data. Never write phrases like "above X mg/L" or "below Y°C" unless that exact value appears verbatim in the data.
    - Leverage Backend Insights: The "eventi" field contains critical issues already detected by the backend analysis system. You MUST address every single item in this list explicitly in the report, expanding on each with your domain expertise. Do not ignore or summarize them collectively.
    - Chain-of-Table Insights: The "ADDITIONAL INSIGHTS FROM ITERATIVE TABLE REASONING" section below contains findings derived by iteratively reasoning over the raw monitoring tables. You MUST explicitly reference and incorporate these findings into the relevant sections of the report. Do not ignore them.
    - Environmental Parameters: Comment on EVERY environmental parameter that has a YELLOW or RED alert level, including those in the weather and marine section. For each flagged parameter, always state the alert level explicitly.
    - Clinical Signs: When clinical symptoms are present (e.g., exophthalmos, haemorrhages, ulcers), comment on their potential clinical significance and possible causes.
    - Sensor Data: If environmental data is missing, state clearly that "No environmental monitoring data was available for this period." If the data flags sensor inconsistencies (e.g., turbidity rising but oxygen stable), advise immediate hardware inspection and explain the biological reasoning behind the inconsistency.
    - Corrective Actions: Every recommended action must be directly traceable to a specific flagged issue in the "eventi" field or in the Chain-of-Table insights. Do NOT suggest generic, unsupported, or speculative recommendations.
    - Uncertainty: Avoid absolute conclusions unless perfectly supported by the data. Use phrases like "indicates a potential issue" or "warrants further investigation."
    - Mortality Data Interpretation: The mortality count represents fish found dead during periodic diver inspections, not fish that died on the recorded date. Deaths may have accumulated over several days before the inspection. Do not imply that all deaths occurred on a single day or derive a meaningful daily rate from a single inspection count.

    Structure the report EXACTLY with the following sections:
    1. **Executive Summary**: A brief, high-level overview of the facility's status.
    2. **Fish Health & Behavior**: Detail mortality trends, appetite changes, and behavioral anomalies. Explicitly state the mortality numbers and use the pre-computed values provided in the data. Comment on any clinical signs present and their potential significance.
    3. **Environmental & Meteorological Conditions**: Summarize water quality and weather impacts. For every parameter with a YELLOW or RED alert level, state the alert level explicitly and comment on the potential biological impact.
    4. **Critical Issues & Sensor Anomalies**: Address EVERY item in the "eventi" list individually. Discuss both technical issues (sensor anomalies) and biological warnings.
    5. **Recommended Corrective Actions**: Provide practical, immediate steps the farm manager should take. Every action must be directly traceable to a specific issue in the data — do NOT suggest generic or unsupported recommendations.
    6. **Conclusions**: A final wrap-up sentence on the overall risk level for this period.
    7. **Data-Driven Insights**: Report explicitly the findings from the iterative table reasoning. For each insight, state the question analyzed, summarize the reasoning chain performed, and present the conclusion reached.

    After completing all 7 sections in English, add a horizontal rule (---) and then provide a complete Italian translation of the entire report.
    The Italian version must:
    - have the same structure and sections as the English version
    - keep all numerical values unchanged
    - translate all content including technical terms
    - start with the header "# Versione Italiana"

    {problems_str}
    {cot_str}

    Data:
    {json.dumps(report_data, indent=2, ensure_ascii=False)}
    """

    #FALLBACK: template statico --> usato quando Ollama non è disponibile
    #formatta un singolo parametro ambientale (es. ossigeno, ph, ...)
    #gestisce automaticamente:
    #- parametro assente
    #- dati mancanti
    #- presenza di warning
    def _format_parametro(self, nome, param):
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
    def _format_azioni(self, azioni):
        if not azioni:
            return "  No corrective actions recorded."
        lines = []
        for a in azioni:
            lines.append(f"  [{a['data']}] {a['descrizione']} — Outcome: {a['esito']}")
        return "\n".join(lines)

    #formatta gli eventi/anomalie rilevati
    def _format_eventi(self, eventi):
        if not eventi:
            return "  No critical issues detected."
        return "\n".join(f"  • {e}" for e in eventi)

    #funzione che genera il report statico finale 
    def _generate_report_statico(self, report_data):
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

        #report
        return f"""FISH FARM AUTOMATIC MONITORING REPORT:

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
    Ill (per 5000)          : {sintomi.get('malati_su_5000', 'N/A')}
    Deaths above 1‰         : {'YES' if sintomi.get('deaths_above_1_permille') else 'NO'}
    Ill above 1/5000        : {'YES' if sintomi.get('ill_above_1_per5000') else 'NO'}
    
    ENVIRONMENTAL CONDITIONS
    {"  Warning: " + nota_ambientale if nota_ambientale else ""}
    {self._format_parametro("oxygen", parametri.get("ossigeno"))}

    {self._format_parametro("pH", parametri.get("ph"))}

    {self._format_parametro("temperature", parametri.get("temperatura"))}

    {self._format_parametro("turbidity", parametri.get("torbidita"))}

    {self._format_parametro("salinity", parametri.get("salinita"))}

    {self._format_parametro("current", parametri.get("corrente"))}

    {self._format_parametro("waves", parametri.get("onde"))}

    {self._format_parametro("saturation", parametri.get("saturazione"))}

    WEATHER & MARINE CONDITIONS (satellite/remote sensing)
    {""}
    {self._format_parametro("air temperature", meteo.get("temperatura_aria"))}

    {self._format_parametro("wind speed", meteo.get("vento"))}

    {self._format_parametro("wind gusts", meteo.get("raffiche"))}

    {self._format_parametro("precipitation", meteo.get("precipitazioni"))}

    {self._format_parametro("cloud cover", meteo.get("copertura_nuv"))}

    {self._format_parametro("wave height", meteo.get("altezza_onde"))}

    {self._format_parametro("swell wave height", meteo.get("onde_swell"))}

    {self._format_parametro("wave period", meteo.get("periodo_onde"))}

    {self._format_parametro("sea surface temperature", meteo.get("temp_mare"))}

    CRITICAL ISSUES & ANOMALIES
    {self._format_eventi(eventi)}

    CORRECTIVE ACTIONS
    {self._format_azioni(azioni)}

    CONCLUSIONS
    This report provides a structured overview of the monitoring data recorded
    for cage {meta.get('gabbia_id', 'N/A')} during the specified period.
    All statistics are computed automatically from raw monitoring records.
    """

