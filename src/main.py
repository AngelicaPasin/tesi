import warnings
warnings.filterwarnings("ignore")

from datetime import date, timedelta
from db import DatabaseClient
from llm_client import LLMClient
from analyst import AnalystAgent
from writer import WriterAgent
#from chain_of_table import compute_chain_of_table_insights
from validator import validate_report
from utils import save_report
from config import REPORT_PATH

#restituisce lunedì e domenica della settimana precedente
def get_last_week():
    today = date.today()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    return str(last_monday), str(last_sunday)

#chiede all'operatore il periodo da analizzare
#se l'operatore preme INVIO senza inserire nulla, viene usata automaticamente la settimana più recente
def get_periodo():
    default_inizio, default_fine = get_last_week()

    print("\nSISTEMA DI MONITORAGGIO ACQUACOLTURA:")
    print(f"Periodo di default: {default_inizio} --> {default_fine} (settimana scorsa)")
    print("Premi INVIO per usare il periodo di default, oppure inserisci le date.\n")

    data_inizio = input(f"Data inizio (YYYY-MM-DD) [{default_inizio}]: ").strip()
    if not data_inizio:
        data_inizio = default_inizio

    data_fine = input(f"Data fine (YYYY-MM-DD) [{default_fine}]: ").strip()
    if not data_fine:
        data_fine = default_fine

    print(f"\nPeriodo selezionato: {data_inizio} --> {data_fine}\n")
    return data_inizio, data_fine

def main():
    #chiedo il periodo all'operatore
    data_inizio, data_fine = get_periodo()

    #input parametri
    #TODO usare questo --> intanto uso un periodo significativo
    #TODO permettere all'operatore di scegliere anche la gabbia
    """
    metadata = {
        "azienda_id": 1,
        "gabbia_id": 63,
        "data_inizio": data_inizio,
        "data_fine": data_fine
    }
    """

    metadata = {
        "azienda_id": 1,
        "gabbia_id": 63,
        "data_inizio": "2025-09-08",
        "data_fine": "2025-09-14"
    }

    #db
    db = DatabaseClient()
    df_monitoraggio = db.get_monitoraggio(metadata)
    df_ambientale   = db.get_ambientale(metadata)
    df_azioni       = db.get_azioni(metadata)
    df_meteo        = db.get_meteo(metadata)
    df_meteo_marine = db.get_meteo_marine(metadata)

    metadata["numero_pesci_iniziale"] = db.get_numero_pesci(
        metadata["gabbia_id"], metadata["data_inizio"]
    )

    #llm client condiviso tra analyst, writer e validator
    llm = LLMClient()

    #analyst
    analyst = AnalystAgent(llm_client=llm)
    report_data = analyst.build_report_data(
        df_monitoraggio, df_ambientale, df_azioni,
        df_meteo, df_meteo_marine, metadata
    )

    #chain-of-table
    #report_data["cot_insights"] = compute_chain_of_table_insights(
    #    df_monitoraggio, df_ambientale, df_meteo_marine, llm=llm
    #)

    #writer
    writer = WriterAgent(llm_client=llm)
    report = writer.generate_report(report_data)

    #validazione
    report = validate_report(report, report_data, writer.generate_report, llm=llm)

    #salva
    save_report(report, REPORT_PATH)
    print("Report salvato in:", REPORT_PATH)


if __name__ == "__main__":
    main()
