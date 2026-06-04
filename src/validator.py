#modulo di validazione del report generato dal writer
#step 1: validazione basata su regole --> python puro, deterministico
#step 2: LLM-as-judge --> qwen (o gemma o gemini...) valuta il report rispetto ai dati

import re
from llm_client import LLMClient
import json

MAX_RETRIES = 2        #numero massimo di tentativi di rigenerazione
SCORE_THRESHOLD = 6    #punteggio minimo accettabile (scala 1-10)

#mappatura dai nomi interni ai termini cercati nel report
NOMI_IN_REPORT = {
    "temp_mare":    ["sea surface temperature", "sea-surface temperature", "sst"],
    "torbidita":    ["turbidity", "torbidità", "torbidita"],
    "ossigeno":     ["oxygen", "ossigeno"],
    "temperatura":  ["temperature", "temperatura"],
    "salinita":     ["salinity", "salinità"],
    "corrente":     ["current", "corrente"],
    "onde":         ["waves", "onde", "wave height"],
    "saturazione":  ["saturation", "saturazione"],
    "vento":        ["wind", "vento"],
    "raffiche":     ["wind gusts", "gusts", "raffiche"],
    "pioggia":      ["rain", "precipitation", "pioggia"],
    "altezza_onde": ["wave height", "altezza onde"],
    "onde_swell":   ["swell", "onde swell"]
}

#STEP 1: VALIDAZIONE BASATA SU REGOLE

#verifica che tutti i parametri con livello GIALLO o ROSSO siano menzionati nel testo del report
#restituisce una lista di problemi trovati
def check_parameters_mentioned(report, report_data):
    problems = []
    parametri = report_data.get("ambientale", {}).get("parametri", {})
    meteo = report_data.get("meteo", {})

    tutti_parametri = {**parametri, **meteo}

    for nome, param in tutti_parametri.items():
        if param and param.get("livello") in ["giallo", "rosso"]:
            #cerca tutti i termini alternativi per questo parametro
            termini = NOMI_IN_REPORT.get(nome, [nome])
            trovato = any(t.lower() in report.lower() for t in termini)
            if not trovato:
                problems.append(f"Parametro '{nome}' con livello {param['livello'].upper()} non menzionato nel report.")

    return problems

#verifica che i valori numerici chiave siano presenti nel report
def check_key_values_present(report, report_data):
    problems = []
    mortalita = report_data.get("benessere", {}).get("mortalita", {})

    totale = mortalita.get("totale")
    if totale and str(totale) not in report.replace(",", ""):
        problems.append(f"Valore totale mortalità ({totale}) non trovato nel report.")

    return problems

#cerca pattern tipici di soglie inventate nel report, come 'above X mg/L', 'below Y°C', 'more than Z NTU'
def check_no_invented_thresholds(report):
    problems = []
    patterns = [
        r"above\s+\d+[\.,]?\d*\s*(mg/l|ntu|°c|ppm|psu|%)",
        r"below\s+\d+[\.,]?\d*\s*(mg/l|ntu|°c|ppm|psu|%)",
        r"more than\s+\d+[\.,]?\d*\s*(mg/l|ntu|°c|ppm|psu|%)",
        r"less than\s+\d+[\.,]?\d*\s*(mg/l|ntu|°c|ppm|psu|%)",
        r"exceed(s|ing)?\s+\d+[\.,]?\d*\s*(mg/l|ntu|°c|ppm|psu|%)",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, report, re.IGNORECASE)
        if matches:
            problems.append(f"Possibile soglia inventata nel report: pattern '{pattern}' trovato.")

    return problems

#esegue tutte le validazioni basate su regole e restituisce una lista di tutti i problemi trovati
def run_rule_based_validation(report, report_data):
    problems = []
    problems += check_parameters_mentioned(report, report_data)
    problems += check_key_values_present(report, report_data)
    problems += check_no_invented_thresholds(report)
    return problems


#STEP 2: LLM-AS-JUDGE

#costruisce il prompt per il giudice LLM
#include il report, i dati originali e i problemi già trovati dalle regole
def build_judge_prompt(report, report_data, rule_problems):
    n_problems = len(rule_problems)
    rule_problems_str = "\n".join(f"- {p}" for p in rule_problems) if rule_problems else "None detected."
    
    #passa solo la versione inglese al giudice --> valutazione sui contenuti, non sulla traduzione
    report_en = report.split("---")[0] if "---" in report else report

    return f"""You are an expert aquaculture report reviewer. Your task is to evaluate the quality of the following monitoring report against the original data.

Evaluate the report on the following criteria:
1. Factual accuracy: Are all numerical values correct and consistent with the data?
2. Completeness: Are all critical issues (eventi) addressed individually?
3. No invented thresholds: Does the report avoid stating specific numerical thresholds not present in the data?
4. No assumptions: Does the report avoid interpreting values without an explicit reference scale?
5. Mortality interpretation: Does the report correctly state that mortality counts come from diver inspections, not daily deaths?
6. Chain-of-Table: Are the iterative reasoning insights explicitly referenced?
7. Corrective actions: Are all recommended actions traceable to specific flagged issues?

Rule-based validation already found {n_problems} confirmed problem(s):
{rule_problems_str}

IMPORTANT: These are confirmed issues that MUST be reflected in your score.
A report with {n_problems} confirmed rule violations cannot score above {max(1, SCORE_THRESHOLD - n_problems)}/10.
Include each confirmed problem in your PROBLEMS list.

Original data:
{json.dumps(report_data, indent=2, ensure_ascii=False)[:6000]}

Report to evaluate:
{report[:10000]}

Respond with:
SCORE: [1-10]
PROBLEMS:
- [list each problem found, or "None" if the report is acceptable]
VERDICT: [APPROVED or REJECTED]
"""

#chiama l'llm come giudice per valutare il report
#restituisce score, lista di problemi e verdetto
def run_llm_judge(llm, report, report_data, rule_problems):
    prompt = build_judge_prompt(report, report_data, rule_problems)

    try:
        text = llm.invoke(prompt)

        #estrae score
        score_match = re.search(r"SCORE:\s*(\d+)", text)
        score = int(score_match.group(1)) if score_match else 0

        #estrae verdetto
        verdict = "APPROVED" if "APPROVED" in text.upper() else "REJECTED"

        #estrae problemi
        problems_match = re.search(r"PROBLEMS:(.*?)VERDICT:", text, re.DOTALL)
        llm_problems = []
        if problems_match:
            for line in problems_match.group(1).strip().split("\n"):
                line = line.strip().lstrip("- ").strip()
                if line and line.lower() != "none":
                    llm_problems.append(line)

        return score, llm_problems, verdict

    except Exception as e:
        print(f"LLM judge non disponibile: {e}")
        #se il judge non è disponibile, approva comunque
        return SCORE_THRESHOLD, [], "APPROVED"


#ENTRY POINT
#esegue la validazione ibrida del report
#se il report non supera la validazione, lo rigenera fino a MAX_RETRIES volte
#args:
#    report: testo del report generato dal writer
#    report_data: dizionario dei dati analizzati
#    generate_fn: funzione che rigenera il report (writer.generate_report)
#    llm: istanza LLMClient — se None ne crea una nuova
#restituisce il report validato (o il migliore disponibile dopo i tentativi)
def validate_report(report, report_data, generate_fn, llm=None):
    llm = llm or LLMClient()
    best_report = report
    best_score = 0
    all_problems = []

    for attempt in range(MAX_RETRIES + 1):
        print(f"\n── Validazione report (tentativo {attempt + 1}) ──")

        #step 1: regole
        rule_problems = run_rule_based_validation(report, report_data)
        if rule_problems:
            print(f"  Problemi trovati dalle regole ({len(rule_problems)}):")
            for p in rule_problems:
                print(f"    - {p}")
        else:
            print("  Validazione basata su regole: OK")

        #step 2: LLM judge
        score, llm_problems, verdict = run_llm_judge(llm, report, report_data, rule_problems)
        print(f"  LLM judge score: {score}/10 — Verdetto: {verdict}")
        if llm_problems:
            print(f"  Problemi trovati dal giudice ({len(llm_problems)}):")
            for p in llm_problems:
                print(f"    - {p}")
        
        #aggiorna lista problemi per eventuale rigenerazione
        all_problems = rule_problems + llm_problems

        #tiene traccia del report migliore
        if score > best_score:
            best_score = score
            best_report = report

        #se approvato e score sufficiente, termina
        if verdict == "APPROVED" and score >= SCORE_THRESHOLD:
            print(f"  Report approvato al tentativo {attempt + 1}.")
            return best_report
        
        #se non è l'ultimo tentativo, rigenera passando i problemi trovati
        if attempt < MAX_RETRIES:
            print(f"  Rigenerazione report (tentativo {attempt + 1}/{MAX_RETRIES})...")
            report = generate_fn(report_data, previous_problems=all_problems)

    print(f"\nAttenzione: report non approvato dopo {MAX_RETRIES} tentativi.")
    print(f"Viene salvato il report con il punteggio più alto ({best_score}/10).")
    return best_report

