#gestisce la connessione al db e le query principali

#centralizza tutto in un unico posto: se cambiano credenziali o struttura del db,
#si modifica solo questo file senza toccare il resto del codice

from sqlalchemy import create_engine, text
import pandas as pd
import unicodedata
from config import DB_URI #importa la stringa di connessione dal file di configurazione
                          #DB_URI contiene user, password, host e nome del db

def normalize_key(s):
    #converte "Torbidità" in "torbidita", "Salinità" in "salinita"
    return unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode()


#alcuni parametri in soglia_allerta hanno nomi diversi da quelli usati nel codice
#questa mappatura li allinea
SOGLIE_ALIAS = {
    "wave_height": "onde",
    "sea_surface_temperature": "temp_mare",
    "windspeed_10m": "vento", #velocità del vento a 10m di altezza 
    "windgusts_10m": "raffiche",
    "rain": "pioggia",
    "swell_wave_height": "onde_swell"
}


#client per il database MySQL. L'engine viene creato una sola volta (pattern singleton)
#e riusato da tutte le query — evita connessioni duplicate e spreco di risorse
class DatabaseClient:

    _engine = None

    #classmethod --> non richiede un'istanza
    #cls = la classe stessa
    @classmethod
    def get_engine(cls):
        #lazy connection: l'engine viene creato solo alla prima chiamata
        if cls._engine is None:
            cls._engine = create_engine(DB_URI)
        return cls._engine

    #recupera il numero totale di pesci del ciclo di allevamento attivo alla data di inizio del periodo analizzato
    #usato per calcolare mortalità e malattia per mille
    @classmethod
    def get_numero_pesci(cls, gabbia_id, data_inizio):
        query = text("""
            SELECT numero_totale_iniziale
            FROM tciclo_allevamento
            WHERE id_gabbia_id = :gabbia_id
            AND data_inizio <= :data_inizio
            ORDER BY data_inizio DESC
            LIMIT 1
        """)
        with cls.get_engine().connect() as conn:
            df = pd.read_sql(query, conn, params={
                "gabbia_id": gabbia_id,
                "data_inizio": data_inizio
            })
        
        if df.empty or df["numero_totale_iniziale"].iloc[0] is None:
            return None
        return int(df["numero_totale_iniziale"].iloc[0])

    #query monitoraggio
    #recupera i dati di monitoraggio giornaliero per una gabbia e un periodo specifici
    #naviga su tre tabelle: tmonitoraggio_giornaliero, tciclo_allevamento e tgabbia
    #filtra per gabbia_id e azienda_id
    @classmethod
    def get_monitoraggio(cls, meta):
        query = text("""
            SELECT 
                mg.data,
                mg.n_pesci_morti,
                mg.n_pesci_malati,
                mg.id_appetito_id,
                mg.comportamento_anomalo,
                mg.ulcere,
                mg.emaciato,
                mg.pinne_danneggiate,
                mg.colore_anormale,
                mg.pelle_mancante,
                mg.occhi_esoftalmo,
                mg.occhi_emorragie,
                mg.addome_gonfio,
                mg.note
            FROM tmonitoraggio_giornaliero mg
            JOIN tciclo_allevamento ca
                ON mg.id_ciclo_allevamento_id = ca.id
            JOIN tgabbia g
                ON ca.id_gabbia_id = g.id
            WHERE g.id = :gabbia_id
            AND g.id_azienda_id = :azienda_id
            AND mg.data BETWEEN :start AND :end
            ORDER BY mg.data ASC
        """)
        #:gabbia_id, :azienda_id, :start, :end sono parametri che SQLAlchemy sostituisce con i valori reali passati nel dizionario params

        with cls.get_engine().connect() as conn:
            df = pd.read_sql(query, conn, params={
                "azienda_id": meta["azienda_id"],
                "gabbia_id": meta["gabbia_id"],
                "start": meta["data_inizio"],
                "end": meta["data_fine"]
            })

        return df

    #recupero i dati ambientali provenienti da fonti esterne (satellite o servizi meteo)
    #associati all'azienda e al periodo temporale specificato
    @classmethod
    def get_meteo(cls, meta):
        query = text("""
            SELECT 
                DATE(timestamp) AS data,
                AVG(temperature_2m) AS temperature_2m,
                AVG(windspeed_10m) AS windspeed_10m,
                AVG(windgusts_10m) AS windgusts_10m,
                AVG(precipitation) AS precipitation,
                AVG(cloudcover) AS cloudcover
            FROM meteo_dati
            WHERE timestamp BETWEEN :start AND :end
            AND punto = :punto
            GROUP BY DATE(timestamp)
            ORDER BY data ASC
        """)

        with cls.get_engine().connect() as conn:
            df = pd.read_sql(query, conn, params={
                "start": meta["data_inizio"],
                "end": meta["data_fine"],
                "punto": meta["azienda_id"] #punto coincide con azienda_id
            })

        return df if not df.empty else pd.DataFrame()

    #recupero parametri come onde, temperatura mare ecc per l’azienda e il periodo specificato
    @classmethod
    def get_meteo_marine(cls, meta):
        query = text("""
            SELECT 
                DATE(timestamp) AS data,
                AVG(wave_height) AS wave_height,
                AVG(swell_wave_height) AS swell_wave_height,
                AVG(wave_period) AS wave_period,
                AVG(sea_surface_temperature) AS sea_surface_temperature
            FROM meteo_marine_dati
            WHERE timestamp BETWEEN :start AND :end
            AND punto = :punto
            GROUP BY DATE(timestamp)
            ORDER BY data ASC
        """)

        with cls.get_engine().connect() as conn:
            df = pd.read_sql(query, conn, params={
                "start": meta["data_inizio"],
                "end": meta["data_fine"],
                "punto": meta["azienda_id"]
            })

        return df if not df.empty else pd.DataFrame()

    #query ambientale
    #recupera i dati ambientali (sonde in-situ) per un'azienda e un periodo specifici
    #struttura del db:
    #   tmonitoraggio_ambientale -> contiene una riga per ogni sessione di monitoraggio
    #   tmonitoraggio_valori -> contiene i valori effettivi in formato long (una riga per parametro)
    #
    #il risultato viene trasformato in formato wide tramite pivot_table,
    #così ogni parametro diventa una colonna (es. ossigeno, temperatura, ph...)
    @classmethod
    def get_ambientale(cls, meta):
        query = text("""
        SELECT 
            ma.data,
            mv.tipo_valore,
            mv.valore
        FROM tmonitoraggio_ambientale ma
        JOIN tmonitoraggio_valori mv ON mv.id_monitoraggio_ambientale_id = ma.id
        WHERE ma.id_azienda_id = :azienda_id
        AND ma.data BETWEEN :start AND :end
        AND mv.valore IS NOT NULL
        AND NOT (mv.tipo_valore = 'salinità' AND mv.unita = 'ppm')
    """) #ci sono due colonne "salinità" con unita=ppm e unita=psu

        with cls.get_engine().connect() as conn:
            df = pd.read_sql(query, conn, params={
                "azienda_id": meta["azienda_id"],
                "start": meta["data_inizio"],
                "end": meta["data_fine"]
            })

        if df.empty:
            return pd.DataFrame()

        #pivot
        #trasforma il formato long in wide: ogni tipo_valore diventa una colonna
        #aggfunc="mean" gestisce i casi in cui ci siano più misurazioni nello stesso giorno
        df_pivot = df.pivot_table(
            index="data",
            columns="tipo_valore",
            values="valore",
            aggfunc="mean"
        ).reset_index()
        
        #rinomina le colonne per uniformare i nomi usati nel resto del codice
        mapping_finale = {
            "torbidità": "torbidita",
            "salinità": "salinita",
            "velocita_totale": "corrente",
            "altezza_significativa": "onde"
        } #temperatura, ossigeno, saturazione e ph non hanno bisogno di rinomina perché il loro tipo_valore nel db è già uguale al nome che uso nel codice

        df_pivot = df_pivot.rename(columns=mapping_finale)

        return df_pivot

    #query azioni correttive
    #recupera le azioni correttive registrate per una gabbia e un periodo specifici
    #usa LEFT JOIN su tesito_azione perché l'esito può essere NULL (azione registrata ma esito non ancora inserito)
    @classmethod
    def get_azioni(cls, meta):
        query = text("""
            SELECT 
                ac.data,
                ea.descrizione AS esito,
                ac.note AS descrizione
            FROM tazioni_correttive ac

            JOIN tciclo_allevamento ca
                ON ac.id_ciclo_allevamento_id = ca.id

            JOIN tgabbia g
                ON ca.id_gabbia_id = g.id

            LEFT JOIN tesito_azione ea 
                ON ac.id_esito_azione_id = ea.id

            WHERE g.id = :gabbia_id
            AND g.id_azienda_id = :azienda_id
            AND ac.data BETWEEN :start AND :end
        """)

        with cls.get_engine().connect() as conn:
            df = pd.read_sql(query, conn, params={
                "azienda_id": meta["azienda_id"],
                "gabbia_id": meta["gabbia_id"],
                "start": meta["data_inizio"],
                "end": meta["data_fine"]
            })

        return df

    #recupero le soglie di allerta per i parametri ambientali di un'azienda
    #filtro solo le soglie attive (attivo = 1)
    #queste soglie vengono usate in analyst.py per rilevare valori anomali
    #restituisce un dizionario {nome_parametro: {livelli, range}}
    @classmethod
    def get_soglie(cls, azienda_id):
        query = text("""
            SELECT parametro, soglia_min, soglia_max, livello
            FROM soglia_allerta
            WHERE azienda_id = :azienda_id
            AND attivo = 1
            ORDER BY soglia_max ASC
        """)

        with cls.get_engine().connect() as conn:
            df = pd.read_sql(query, conn, params={"azienda_id": azienda_id})

        #costruisco un dizionario {nome_parametro: {livelli, range}}
        #dove livelli è la lista di tutte le fasce (verde/giallo/rosso)
        #e range è l'intervallo complessivo [min_assoluto, max_assoluto].
        #
        #esempio risultato finale per "torbidita":
        # {
        #   "livelli": [
        #     {"livello": "verde",  "soglia_min": 0,     "soglia_max": 10},
        #     {"livello": "giallo", "soglia_min": 10.01, "soglia_max": 20},
        #     {"livello": "rosso",  "soglia_min": 20.01, "soglia_max": 9999}
        #   ],
        #   "range": (0, 9999)
        # }
        soglie = {}
        for _, row in df.iterrows():
            key = normalize_key(row["parametro"]) #normalizzo il nome: "Torbidità" in "torbidita", "Ph" in "ph", ...
            #applico alias per i parametri con nome diverso tra soglia_allerta e il codice
            #es. "wave_height" --> "onde", "sea_surface_temperature" --> "temp_mare"
            key = SOGLIE_ALIAS.get(key, key)

            #inizializzo la struttura per questo parametro se non esiste ancora
            #range parte da [+inf, -inf] così il primo confronto min/max funziona sempre
            if key not in soglie:
                soglie[key] = {"livelli": [], "range": [float("inf"), float("-inf")]}
            
            #aggiungo la fascia corrente alla lista dei livelli
            soglie[key]["livelli"].append({
                "livello": row["livello"],
                "soglia_min": float(row["soglia_min"]),
                "soglia_max": float(row["soglia_max"])
            })
            
            #range complessivo: dal minimo assoluto al massimo assoluto tra tutte le soglie
            #tengo traccia del valore minimo e del valore massimo tra tutte le fasce
            soglie[key]["range"][0] = min(soglie[key]["range"][0], float(row["soglia_min"]))
            soglie[key]["range"][1] = max(soglie[key]["range"][1], float(row["soglia_max"]))

        #converto il range da lista [min, max] a tupla (min, max)
        #per coerenza con il resto del codice che usa tuple per i range
        for key in soglie:
            soglie[key]["range"] = tuple(soglie[key]["range"])

        return soglie

