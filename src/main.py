from analyst import build_report_data
from writer import generate_report
from db import get_monitoraggio, get_ambientale, get_azioni, get_numero_pesci, get_meteo, get_meteo_marine
from config import REPORT_PATH
from utils import save_report

def main():
    #input parametri
    metadata = {
        "azienda_id": 1,
        "gabbia_id": 63,
        "data_inizio": "2025-09-08",
        "data_fine": "2025-09-14"
    }

    #query db
    df_monitoraggio = get_monitoraggio(metadata)
    df_ambientale = get_ambientale(metadata)
    df_azioni = get_azioni(metadata)
    df_meteo = get_meteo(metadata)
    df_meteo_marine = get_meteo_marine(metadata)

    #recupera il numero di pesci del ciclo attivo in quella settimana
    metadata["numero_pesci_iniziale"] = get_numero_pesci(
        metadata["gabbia_id"],
        metadata["data_inizio"]
    )

    #analyst
    report_data = build_report_data(
        df_monitoraggio,
        df_ambientale,
        df_azioni,
        df_meteo,
        df_meteo_marine,
        metadata
    )

    #writer
    report = generate_report(report_data)
    save_report(report, REPORT_PATH)
    print("Report salvato in:", REPORT_PATH)

if __name__ == "__main__":
    main()
