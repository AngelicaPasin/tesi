#versione adattata di Chain-of-Table
#invece di fact verification su tabelle generiche, esegue ragionamento iterativo su DataFrame di monitoraggio
#per estrarre insights che il codice Python puro non riesce a derivare

import re
import warnings
import pandas as pd
from llm_client import LLMClient

warnings.filterwarnings("ignore")

#OPERAZIONI DISPONIBILI
#pool di operazioni che l'LLM può scegliere ad ogni iterazione, adattate al dominio dell'acquacoltura
OPERATION_POOL = [
    "f_select_rows",     #seleziona giorni con anomalie o mortalità elevata
    "f_select_columns",  #seleziona i parametri più rilevanti per la domanda
    "f_sort_by",         #ordina per un parametro (es. mortalità decrescente)
    "f_group_by",        #raggruppa per livello di allerta o categoria
    "f_correlate",       #cerca correlazioni tra parametri ambientali e mortalità
    "f_end"              #termina la catena
]

MAX_ITERATIONS = 5 #numero massimo di operazioni prima di forzare f_end

#nota di dominio passata a tutti i prompt per contestualizzare i dati di mortalità
DOMAIN_CONTEXT = """Important domain note: mortality data (n_pesci_morti) represents the count of dead fish found during periodic diver inspections,
not the number of fish that died on that specific date. Deaths may have accumulated over several days before the inspection.
This must be considered when interpreting correlations with daily environmental parameters."""

#SERIALIZZAZIONE 
#converte un DataFrame pandas in formato testuale leggibile dall'LLM
#formato: col : col1 | col2 | ...
#         row 1 : val1 | val2 | ...
def df_to_table_string(df, max_rows=20):
    if df is None or df.empty:
        return "No data available."

    df = df.head(max_rows)
    cols = list(df.columns)
    lines = []
    lines.append("col : " + " | ".join(str(c) for c in cols))
    for i, (_, row) in enumerate(df.iterrows()):
        values = " | ".join(str(v) if v is not None else "NULL" for v in row)
        lines.append(f"row {i+1} : {values}")
    return "\n".join(lines)


#DYNAMIC PLAN
#chiede all'LLM quale operazione eseguire come prossimo step,
#in base alla tabella corrente, alla domanda e alla storia delle operazioni
def dynamic_plan(llm, table_string, question, operation_history):
    history_str = " -> ".join(operation_history) if operation_history else "none"

    prompt = f"""You are an aquaculture data analyst. You are reasoning step by step over monitoring data.

{DOMAIN_CONTEXT}

Available operations:
- f_select_rows: select rows with anomalies, high mortality, or relevant conditions
- f_select_columns: keep only the columns relevant to the question
- f_sort_by: sort rows by a specific column (descending or ascending)
- f_group_by: group rows by alert level or category
- f_correlate: identify correlations between environmental parameters and mortality
- f_end: stop the reasoning chain when enough information has been gathered

Current table:
/*
{table_string}
*/

Question: {question}
Operation history: {history_str}

Choose the next operation from the list above. Reply with ONLY the operation name (e.g. f_select_rows).
Next operation:"""

    response = llm.invoke(prompt)

    #estrae solo il nome dell'operazione dalla risposta
    for op in OPERATION_POOL:
        if op in response:
            return op
    return "f_end" #fallback se non riconosce nessuna operazione


#GENERATE ARGS
#dato il nome dell'operazione scelta, chiede all'LLM gli argomenti necessari per eseguirla
#il prompt è volutamente restrittivo per evitare che il modello aggiunga testo descrittivo agli argomenti
def generate_args(llm, table_string, question, operation):

    format_instructions = {
        "f_select_rows": 'Reply with ONLY row numbers separated by commas. Example: "row 1, row 3, row 5"',
        "f_select_columns": 'Reply with ONLY column names separated by commas. Example: "data, n_pesci_morti, ossigeno"',
        "f_sort_by": 'Reply with ONLY column name and order. Example: "n_pesci_morti descending"',
        "f_group_by": 'Reply with ONLY the column name. Example: "comportamento_anomalo"',
        "f_correlate": 'Reply with ONLY two column names separated by a comma. Example: "ossigeno, n_pesci_morti"',
        "f_end": 'Reply with ONLY the word "end"'
    }

    format_str = format_instructions.get(operation, 'Reply with ONLY the arguments, no explanations.')

    prompt = f"""You are an aquaculture data analyst reasoning over monitoring data.

{DOMAIN_CONTEXT}

Current table:
/*
{table_string}
*/

Question: {question}
Operation to execute: {operation}

{format_str}
Do NOT include any explanation, description, or extra text — ONLY the arguments in the exact format shown.

Arguments:"""

    response = llm.invoke(prompt)

    #pulizia della risposta: prende solo la prima riga non vuota
    #per eliminare eventuali spiegazioni aggiuntive del modello
    for line in response.strip().split("\n"):
        line = line.strip()
        if line and not line.lower().startswith(("to ", "based", "the ", "since", "note")):
            return line
    
    response = response.strip()
    #rimuove prefissi tipo "Arguments:" o "f_group_by(" annidati
    response = re.sub(r'^(Arguments:\s*)', '', response)
    response = re.sub(r'^f_\w+\(', '', response)
    response = response.rstrip(')')
    return response.split('\n')[0].strip()


#ESECUZIONE OPERAZIONI
#esegue l'operazione sul DataFrame corrente e restituisce il DataFrame aggiornato
#e una stringa descrittiva dell'operazione eseguita
def execute_operation(df, operation, args):
    if df is None or df.empty:
        return df, f"skip {operation} (empty table)"

    try:
        if operation == "f_select_rows":
            #estrae i numeri di riga dalla risposta dell'LLM
            row_nums = re.findall(r'row\s*(\d+)', args)
            if row_nums:
                indices = [int(r) - 1 for r in row_nums if int(r) - 1 < len(df)]
                if indices:
                    df = df.iloc[indices].reset_index(drop=True)
            return df, f"f_select_rows({args.strip()})"

        elif operation == "f_select_columns":
            #seleziona le colonne menzionate negli argomenti
            cols_to_keep = [c.strip() for c in args.split(",")]
            valid_cols = [c for c in cols_to_keep if c in df.columns]
            if valid_cols:
                df = df[valid_cols]
            return df, f"f_select_columns({', '.join(valid_cols)})"

        elif operation == "f_sort_by":
            #ordina per la colonna specificata
            parts = args.strip().split()
            col = parts[0]
            ascending = "ascending" in args.lower()
            if col in df.columns:
                df = df.sort_values(by=col, ascending=ascending).reset_index(drop=True)
            return df, f"f_sort_by({col}, {'ascending' if ascending else 'descending'})"

        elif operation == "f_group_by":
            #raggruppa per la colonna specificata e conta
            col = args.strip()
            if col in df.columns:
                df = df.groupby(col).size().reset_index(name="count")
            return df, f"f_group_by({col})"

        elif operation == "f_correlate":
            #calcola la correlazione tra due colonne numeriche
            cols = [c.strip() for c in args.split(",")]
            if len(cols) == 2 and all(c in df.columns for c in cols):
                #converte a numerico e ignora errori (es. date)
                col1 = pd.to_numeric(df[cols[0]], errors='coerce')
                col2 = pd.to_numeric(df[cols[1]], errors='coerce')
                corr = col1.corr(col2)
                #crea una tabella di sintesi con il valore di correlazione
                df = pd.DataFrame({
                    "column_1": [cols[0]],
                    "column_2": [cols[1]],
                    "correlation": [round(corr, 3) if pd.notna(corr) else "insufficient data"]
                })
            return df, f"f_correlate({cols[0]}, {cols[1]})"

    except Exception as e:
        return df, f"skip {operation} (error: {e})"

    return df, f"skip {operation}"


#FINAL QUERY
#dopo che la catena di operazioni è terminata, chiede all'LLM di rispondere alla domanda basandosi sulla tabella trasformata
def final_query(llm, table_string, question, operation_history):
    history_str = " -> ".join(operation_history)

    prompt = f"""You are an aquaculture expert. You have performed the following reasoning steps on monitoring data:
{history_str}
{DOMAIN_CONTEXT}

The resulting table after all operations is:
/*
{table_string}
*/

Based on this table, answer the following question concisely and technically:
Question: {question}

Answer:"""

    return llm.invoke(prompt)


#CHAIN OF TABLE LOOP
#esegue il loop principale di Chain-of-Table su un DataFrame
#ad ogni iterazione:
#    1. serializza la tabella corrente
#    2. chiede all'LLM quale operazione eseguire (dynamic_plan)
#    3. chiede gli argomenti (generate_args)
#    4. esegue l'operazione sul DataFrame (execute_operation)
#    5. aggiorna la storia delle operazioni
#termina quando l'LLM sceglie f_end o si raggiunge max_iterations
def run_chain_of_table(llm, df, question, max_iterations=MAX_ITERATIONS):
    operation_history = []
    current_df = df.copy() if df is not None and not df.empty else df

    for i in range(max_iterations):
        table_string = df_to_table_string(current_df)

        #step 1: scegli la prossima operazione
        operation = dynamic_plan(llm, table_string, question, operation_history)
        if operation == "f_end":
            break

        #step 2: genera gli argomenti
        args = generate_args(llm, table_string, question, operation)

        #step 3: esegui l'operazione
        current_df, op_description = execute_operation(current_df, operation, args)
        operation_history.append(op_description)

    #step 4: query finale sulla tabella trasformata
    final_table_string = df_to_table_string(current_df)
    insight = final_query(llm, final_table_string, question, operation_history)

    return {
        "question": question,
        "operation_chain": operation_history,
        "insight": insight
    }


#ENTRY POINT
#esegue Chain-of-Table su più domande rilevanti per il report di acquacoltura
#restituisce un dizionario di insights da aggiungere a report_data
#
#domande analizzate:
#   1. correlazione tra parametri ambientali (ossigeno, temperatura, torbidità, saturazione) e mortalità
#   2. giorni con maggiore criticità per mortalità e indicatori di salute
#   3. pattern e co-occorrenze nei sintomi clinici (esoftalmia, emorragie, ulcere ecc.)
#   4. condizioni marine anomale (onde, temperatura superficiale, corrente)
#   5. correlazione tra condizioni marine e comportamento anomalo dei pesci (analisi cross-dominio)
def compute_chain_of_table_insights(df_monitoraggio, df_ambientale, df_meteo_marine, llm=None):
    llm = llm or LLMClient()
    insights = {}

    #domanda 1: correlazione parametri ambientali-mortalità
    #ampliata rispetto alla versione precedente: include ossigeno, temperatura, torbidità e saturazione
    #invece del solo ossigeno, per identificare quale parametro mostra la correlazione più forte
    if df_monitoraggio is not None and not df_monitoraggio.empty and \
       df_ambientale is not None and not df_ambientale.empty:

        #normalizza il tipo della colonna data in entrambi i DataFrame, così il merge funziona correttamente
        df_monitoraggio["data"] = pd.to_datetime(df_monitoraggio["data"]).dt.date
        df_ambientale["data"]   = pd.to_datetime(df_ambientale["data"]).dt.date
        df_monitoraggio["n_pesci_morti"] = df_monitoraggio["n_pesci_morti"].fillna(0)

        #include tutti i parametri ambientali disponibili nel merge
        cols_ambientale = ["data"]
        for col in ["ossigeno", "temperatura", "torbidita", "saturazione"]:
            if col in df_ambientale.columns:
                cols_ambientale.append(col)

        df_mon_daily = df_monitoraggio[["data", "n_pesci_morti"]].groupby("data").sum().reset_index() #aggrego per data anche il monitoraggio per evitare duplicati
        df_amb_daily = df_ambientale[cols_ambientale].groupby("data").mean().reset_index()
        df_merged    = pd.merge(df_mon_daily, df_amb_daily, on="data", how="left")

        insights["environmental_mortality_correlation"] = run_chain_of_table(
            llm,
            df_merged,
            "Are there correlations between environmental parameters (oxygen, temperature, turbidity, saturation) and fish mortality? Which parameter shows the strongest association?"
        )

    #domanda 2: giorni più critici per mortalità e indicatori di salute
    if df_monitoraggio is not None and not df_monitoraggio.empty:
        insights["critical_days"] = run_chain_of_table(
            llm,
            df_monitoraggio[["data", "n_pesci_morti", "comportamento_anomalo", "ulcere", "emaciato"]],
            "Which days show the most critical conditions in terms of mortality and health indicators?"
        )

    #domanda 3: pattern nei sintomi clinici
    #cerca co-occorrenze tra sintomi diversi che potrebbero suggerire una malattia specifica o uno stressor
    if df_monitoraggio is not None and not df_monitoraggio.empty:
        insights["clinical_pattern"] = run_chain_of_table(
            llm,
            df_monitoraggio[["data", "occhi_esoftalmo", "occhi_emorragie",
                              "ulcere", "emaciato", "comportamento_anomalo",
                              "colore_anormale", "addome_gonfio"]],
            "Are there any patterns or co-occurrences among clinical signs (exophthalmos, haemorrhages, ulcers, abnormal coloration) that could suggest a specific disease or environmental stressor?"
        )

    #domanda 4: condizioni marine anomale
    if df_meteo_marine is not None and not df_meteo_marine.empty:
        insights["marine_anomalies"] = run_chain_of_table(
            llm,
            df_meteo_marine,
            "Are there any anomalous marine conditions (waves, temperature, current) during this period?"
        )

    #domanda 5: correlazione cross-dominio tra condizioni marine e comportamento anomalo
    #analisi più sofisticata che cerca legami causa-effetto tra domini diversi
    if df_meteo_marine is not None and not df_meteo_marine.empty and \
       df_monitoraggio is not None and not df_monitoraggio.empty:

        df_meteo_marine["data"]  = pd.to_datetime(df_meteo_marine["data"]).dt.date
        df_monitoraggio["data"]  = pd.to_datetime(df_monitoraggio["data"]).dt.date

        df_meteo_mon = pd.merge(
            df_monitoraggio[["data", "comportamento_anomalo", "n_pesci_morti"]],
            df_meteo_marine[["data", "wave_height", "sea_surface_temperature"]],
            on="data",
            how="left"
        )

        insights["weather_behavior_correlation"] = run_chain_of_table(
            llm,
            df_meteo_mon,
            "Is there a relationship between marine conditions (wave height, sea surface temperature) and anomalous fish behavior or mortality? What do the data suggest?"
        )

    return insights

