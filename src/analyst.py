#agente analista --> si occupa di calcoli e logica

import pandas as pd
from db import get_soglie
from datetime import datetime
import numpy as np

#coordina tutti i sotto-analisti e restituisce il dizionario completo
#che verrà passato al writer per generare il report
def build_report_data(df_monitoraggio, df_ambientale, df_azioni, df_meteo, df_meteo_marine, metadata):
    soglie     = get_soglie(metadata["azienda_id"])
    benessere  = compute_benessere(df_monitoraggio, metadata.get("numero_pesci_iniziale"))
    ambientale = compute_ambientale(df_ambientale, soglie)
    meteo      = compute_meteo(df_meteo, df_meteo_marine, soglie)
    eventi     = compute_eventi(benessere, ambientale, meteo)
    azioni     = compute_azioni(df_azioni)

    return {
        "metadata": build_metadata(metadata),
        "benessere": benessere,
        "ambientale": ambientale,
        "meteo": meteo,
        "eventi": eventi,
        "azioni_correttive": azioni
    }

#costruisce l'intestazione del report con i dati identificativi
#della gabbia e del periodo analizzato
def build_metadata(meta):
    start = meta["data_inizio"]
    end = meta["data_fine"]

    num_days = (pd.to_datetime(end) - pd.to_datetime(start)).days + 1

    return {
        "azienda_id": meta["azienda_id"],
        "gabbia_id": meta["gabbia_id"],
        #"codice_gabbia": meta.get("codice_gabbia", ""),
        "periodo": {
            "data_inizio": start,
            "data_fine": end,
            "numero_giorni": num_days
        }
    }

#coordina il calcolo di tutti gli indicatori di benessere dei pesci
def compute_benessere(df, numero_pesci_iniziale=None):
    mortalita = compute_mortalita(df)
    return {
        "mortalita":     mortalita,
        "appetito":      compute_appetito(df),
        "comportamento": compute_comportamento(df),
        "sintomi":       compute_sintomi(df, numero_pesci_iniziale, morti_tot=mortalita["totale"])
    }

#calcola le statistiche di mortalità (totale, media giornaliera e trend)
def compute_mortalita(df):
    totale = df["n_pesci_morti"].sum()
    #media su tutti i giorni del periodo, non solo sui giorni con valori non nulli
    media = totale / len(df)  #invece di df["n_pesci_morti"].mean()
    trend = compute_trend(df["n_pesci_morti"])

    return {
        "totale": int(totale),
        "media_giornaliera": round(media, 2),
        "trend": trend
    }

#per l'appetito la media viene calcolata solo sui giorni con rilevazione:
#un giorno senza dato non significa appetito zero, ma dato mancante
def compute_appetito(df):
    serie = df["id_appetito_id"].dropna()

    if serie.empty:
        return {
            "valore_medio": None,
            "trend": "unavailable"
        }

    media = serie.mean()
    trend = compute_trend(serie)

    return {
        "valore_medio": round(media, 2),
        "trend": trend
    }

#analizza la frequenza di comportamenti anomali nel periodo
def compute_comportamento(df):
    totale = len(df)

    if totale == 0:
        return {
            "giorni_con_anomalie": 0,
            "percentuale_giorni_anomali": 0
        }
    
    #i giorni senza rilevazione del comportamento vengono trattati come normali (fillna(0))
    giorni_anomali = df["comportamento_anomalo"].fillna(0).sum()

    return {
        "giorni_con_anomalie": int(giorni_anomali),
        "percentuale_giorni_anomali": round(giorni_anomali / totale, 2)
    }

#aggrega i sintomi osservati e calcola gli indici critici di salute (OWIs)
#se il numero di pesci è disponibile, calcola la prevalenza per mille (‰) per la mortalità 
#e su base 5000 per le malattie, verificando il superamento delle soglie di allerta
def compute_sintomi(df, numero_pesci_iniziale=None, morti_tot=None):
    sintomi = {
        "malati_tot":        int(df["n_pesci_malati"].fillna(0).sum()),
        "emaciati_tot":      int(df["emaciato"].fillna(0).sum()),
        "ulcere_tot":        int(df["ulcere"].fillna(0).sum()),
        "pinne_danneggiate": int(df["pinne_danneggiate"].fillna(0).sum()),
        "pelle_mancante":    int(df["pelle_mancante"].fillna(0).sum()),
        "esoftalmo":         int(df["occhi_esoftalmo"].fillna(0).sum()),
        "emorragie":         int(df["occhi_emorragie"].fillna(0).sum()),
        "addome_gonfio":     int(df["addome_gonfio"].fillna(0).sum()),
        "colore_anormale":   int(df["colore_anormale"].fillna(0).sum()),
    }

    #le allerte richiedono il numero totale di pesci in vasca
    #per calcolare la proporzione rispetto alla popolazione totale
    #se non è disponibile, i campi vengono impostati a None
    if numero_pesci_iniziale and numero_pesci_iniziale > 0 and morti_tot is not None:
        #mortalità: calcolata sul per mille
        #es. 10 morti su 5000 pesci --> (10/5000)*1000 = 2‰
        morti_per_mille = (morti_tot / numero_pesci_iniziale) * 1000
        #malati: calcolati su base 5000
        malati_su_5000 = (sintomi["malati_tot"] / numero_pesci_iniziale) * 5000
        
        sintomi["morti_per_mille"] = round(morti_per_mille, 2)
        sintomi["malati_su_5000"] = round(malati_su_5000, 2)

        #flag booleani: True se si supera la soglia critica definita dalla tabella OWIs
        #deaths_above_1_permille --> allerta se la mortalità supera 1 su 1000
        #ill_above_1_per5000 --> allerta se i pesci malati superano 1 su 5000
        sintomi["deaths_above_1_permille"] = morti_per_mille > 1
        sintomi["ill_above_1_per5000"] = malati_su_5000 > 1
    else:
        #numero_pesci_iniziale non disponibile: impossibile calcolare le proporzioni
        sintomi["morti_per_mille"] = None
        sintomi["malati_su_5000"] = None
        sintomi["deaths_above_1_permille"] = None
        sintomi["ill_above_1_per5000"] = None

    return sintomi

#calcola le statistiche per ogni parametro ambientale
#i range ottimali vengono letti dal db tramite get_soglie()
#fallback (0, 9999) per parametri non presenti in soglia_allerta
def compute_ambientale(df, soglie):
    if df is None or df.empty or len(df.columns) <= 1:
        return {
            "parametri": {},
            "anomalie_globali": [],
            "note": "No environmental data available"
        }

    parametri_da_calcolare = [
        "ossigeno", "temperatura", "salinita", "torbidita",
        "corrente", "onde", "saturazione", "ph"
    ]

    return {
        "parametri": {
            nome: compute_parametro(
                df, nome,
                valid_range=soglie[nome]["range"] if nome in soglie else (0, 9999),
                livelli=soglie[nome]["livelli"] if nome in soglie else []
            )
            for nome in parametri_da_calcolare
        },
        "anomalie_globali": []
    }

#classifica un valore in base ai livelli di allerta definiti in soglia_allerta
#cerca la soglia in cui il valore rientra nell'intervallo [soglia_min, soglia_max]
#gestisce parametri con soglie multiple dello stesso livello (es. Ph ha due fasce gialle)
#
#controlla soglia_min <= valore <= soglia_max
#invece di solo valore <= soglia_max, così trova correttamente l'intervallo giusto per ogni valore
def classify_livello(valore, livelli):
    if valore is None or not livelli:
        return None
    
    for soglia in sorted(livelli, key=lambda x: x["soglia_min"]):
        if soglia["soglia_min"] <= valore <= soglia["soglia_max"]:
            return soglia["livello"]
    
    #se cade in un "buco", trovo la soglia che ha l'estremo (min o max) matematicamente più vicino al valore misurato
    soglia_piu_vicina = min(
        livelli,
        key=lambda s: min(abs(valore - s["soglia_min"]), abs(valore - s["soglia_max"]))
    )
    
    return soglia_piu_vicina["livello"]

#analizza i dati meteo-marini
#utilizza una mappatura centralizzata per processare ogni parametro, 
#applicando le soglie e i range validi recuperati dal database (se presenti) 
#o utilizzando valori di default predefiniti per garantire la robustezza del calcolo
def compute_meteo(df_meteo, df_meteo_marine, soglie=None):
    soglie = soglie or {}
    result = {}

    #mappatura: {chiave_report: (colonna_df, default_min, default_max, nome_soglia_db)}
    #se il nome_soglia_db è None, il parametro non ha livelli di allerta
    mapping_meteo = {
        "temperatura_aria": ("temperature_2m", -10, 50, "temperatura_aria"),
        "vento":            ("windspeed_10m",    0, 150, "vento"),
        "raffiche":         ("windgusts_10m",    0, 200, "raffiche"),
        "precipitazioni":   ("precipitation",    0, 200, "pioggia"),
        "copertura_nuv":    ("cloudcover",       0, 100, "copertura_nuv")
    }

    mapping_marine = {
        "altezza_onde": ("wave_height",             0, 10, "onde"),
        "onde_swell":   ("swell_wave_height",       0, 10, "onde_swell"),
        "periodo_onde": ("wave_period",             0, 30, "periodo_onde"),
        "temp_mare":    ("sea_surface_temperature", 0, 35, "temp_mare")
    }

    #funzione interna per processare i gruppi
    def process_group(df, mapping):
        if df is not None and not df.empty:
            for res_key, (col, d_min, d_max, s_key) in mapping.items():
                s = soglie.get(s_key, {})
                result[res_key] = compute_parametro(
                    df, col, 
                    valid_range=s.get("range", (d_min, d_max)),
                    livelli=s.get("livelli", [])
                )

    process_group(df_meteo, mapping_meteo)
    process_group(df_meteo_marine, mapping_marine)

    return result

#esegue il processing completo di un singolo parametro ambientale: pulizia dati (rimozione nulli e outlier), 
#calcolo statistiche/trend e classificazione finale del livello di allerta (verde/giallo/rosso) 
#in base alle soglie presenti nel db
def compute_parametro(df, col, valid_range, livelli=None):
    #controllo colonna esistente
    if col not in df.columns:
        return empty_parametro()

    raw = df[col].dropna()

    if len(raw) == 0:
        return empty_parametro()

    #cleaning
    cleaned = raw[(raw >= valid_range[0]) & (raw <= valid_range[1])]
    perc_outlier = 1 - len(cleaned) / len(raw)

    #se tutti i valori sono fuori range, probabilmente la sonda è guasta
    if len(cleaned) == 0:
        return {
            "media": None,
            "min": None,
            "max": None,
            "trend": "unavailable",
            "warning": "All values out of range: possible sensor malfunction"
        }

    summary = summarize_series(cleaned)
    trend = compute_trend(cleaned)
    warning = compute_warning(raw, perc_outlier, valid_range)

    #classifica il valore medio in base ai livelli di allerta
    livello = classify_livello(summary["media"], livelli) if livelli else None

    return {
        **summary,
        "trend": trend,
        "warning": warning,
        "livello": livello  #"verde", "giallo", "rosso" o None
    }

#restituito quando non ci sono dati disponibili per un parametro
def empty_parametro():
    return {
        "media": None,
        "min": None,
        "max": None,
        "trend": "unavailable",
        "warning": "No data available"
    }

def summarize_series(series):
    return {
        "media": round(series.mean(), 2),
        "min": round(series.min(), 2),
        "max": round(series.max(), 2)
    }

#genera un warning se:
#- più del 20% dei valori è fuori range (possibile sonda instabile)
#- i valori estremi superano di molto i limiti del range (possibile sonda guasta)
#restituisce None se non ci sono anomalie significative
def compute_warning(raw, perc_outlier, valid_range):
    if perc_outlier > 0.2:
        return "High percentage of anomalous values: possible sensor malfunction"

    if raw.min() < valid_range[0] * 0.5 or raw.max() > valid_range[1] * 1.5:
        return "Extreme values detected: sensor likely faulty"

    return None

#determina la tendenza della serie temporale tramite regressione lineare
#- applica l'interpolazione per gestire eventuali dati mancanti
#- calcola la pendenza (slope) della retta di regressione (best fit)
#- normalizza la pendenza rispetto alla media per rendere il calcolo indipendente dall'unità di misura
#- restituisce 'increasing', 'decreasing' o 'stable' in base a una soglia di variazione relativa
def compute_trend(series):
    series = series.dropna().reset_index(drop=True)
    if len(series) < 2: #troppi pochi dati
        return "stable"

    #interpolazione per riempire eventuali buchi
    series_interp = series.interpolate()

    #asse x = tempo (indice)
    x = np.arange(len(series_interp))
    y = series_interp.values

    #regressione lineare (fit retta)
    slope, _ = np.polyfit(x, y, 1)

    #normalizzo lo slope rispetto alla media della serie
    #così la soglia è relativa e funziona su scale diverse
    media = series.mean()
    if media == 0:
        return "stable"

    slope_relativo = slope / abs(media)

    threshold = 0.01 #default 1% per unità di tempo

    if slope_relativo > threshold:
        return "increasing"
    elif slope_relativo < -threshold:
        return "decreasing"
    else:
        return "stable"

#aggrega e identifica eventi critici combinando dati di benessere, ambientali e meteo-marini
#gli eventi individuati vengono poi mostrati nella sezione "Critical Issues" del report
#
#logiche implementate:
#- benessere: trend in aumento della mortalità, presenza di pesci morti, calo dell'appetito 
#  e anomalie comportamentali
#- allarmi soglie: rileva parametri ambientali in-situ o meteo-marini (pioggia, vento, onde, 
#  temperatura mare) entrati nelle fasce di allerta [GIALLO] o [ROSSO]
#- qualità del dato: segnala warning fisici sui sensori (es. valori estremi) e anomalie logiche 
#  (es. torbidità in forte aumento ma ossigeno stabile --> potrebbe essere un problema del sensore)
#- correlazioni cross-dominio: evidenzia possibili legami causa-effetto tra domini diversi 
#  (es. picchi critici della temperatura del mare associati a un aumento della mortalità)
def compute_eventi(benessere, ambientale, meteo=None):
    eventi = []

    if benessere["mortalita"]["trend"] == "increasing":
        eventi.append(
            f"Increasing mortality trend (total: {benessere['mortalita']['totale']})" #aumento della mortalità
        )

    #segnala sempre se ci sono stati morti nel periodo, indipendentemente dal trend
    #NB: il conteggio viene registrato dal sub durante le ispezioni periodiche, non necessariamente il giorno esatto della morte
    if benessere["mortalita"]["totale"] > 0:
        eventi.append(f"Mortality recorded in this period: {benessere['mortalita']['totale']} deaths")

    if benessere["appetito"]["trend"] == "decreasing":
        eventi.append("Decreasing appetite trend") #riduzione dell'appetito

    if benessere["comportamento"]["giorni_con_anomalie"] > 0:
        eventi.append("Anomalous behavior detected") #presenza di comportamenti anomali

    for nome, param in ambientale["parametri"].items():
        if param["warning"]:
            eventi.append(f"Possible sensor issue: {nome}") #possibile problema con la sonda
        if param.get("livello") in ["giallo", "rosso"]:
            eventi.append(f"Parameter out of optimal range [{param['livello'].upper()}]: {nome} (avg: {param.get('media')})")

    #incoerenza torbidità  
    torb = ambientale["parametri"].get("torbidita")
    oss = ambientale["parametri"].get("ossigeno")
    
    if torb is not None and oss is not None:
        if torb["trend"] == "increasing" and oss["trend"] == "stable":
            eventi.append("Possible turbidity sensor issue (not supported by oxygen variation)")

    #eventi meteo
    if meteo:
        #precipitazioni elevate
        pioggia = meteo.get("precipitazioni")
        if pioggia and pioggia.get("livello") in ["giallo", "rosso"]:
            eventi.append(f"High precipitation [{pioggia['livello'].upper()}]: avg {pioggia['media']} mm")

        #vento forte
        vento = meteo.get("vento")
        if vento and vento.get("livello") in ["giallo", "rosso"]:
            eventi.append(f"Strong wind [{vento['livello'].upper()}]: avg {vento['media']} km/h")

        #onde alte
        onde = meteo.get("altezza_onde")
        if onde and onde.get("livello") in ["giallo", "rosso"]:
            eventi.append(f"High wave height [{onde['livello'].upper()}]: avg {onde['media']} m")

        #temperatura mare fuori range
        temp_mare = meteo.get("temp_mare")
        if temp_mare and temp_mare.get("livello") in ["giallo", "rosso"]:
            eventi.append(f"Sea surface temperature anomaly [{temp_mare['livello'].upper()}]: {temp_mare['media']} °C")

        #correlazione: temperatura mare alta + mortalità in aumento
        if (temp_mare and temp_mare.get("livello") == "rosso" and
                benessere["mortalita"]["trend"] == "increasing"):
            eventi.append("Possible correlation: high sea temperature and increasing mortality")
        
    return eventi

#azioni correttive --> sono molto poche nel db
#converte il DataFrame delle azioni correttive in una lista di dizionari, pronta per essere serializzata nel report
def compute_azioni(df):
    if df is None or len(df) == 0:
        return []

    azioni = []

    for _, row in df.iterrows():
        azioni.append({
            "data": str(row.get("data_azione", "")),
            "descrizione": str(row.get("descrizione", "")),
            "esito": str(row.get("esito", ""))
        })

    return azioni
