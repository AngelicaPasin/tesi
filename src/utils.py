#salvataggio del report

import os

def save_report(text, path):
#text: il testo del report generato dal writer
#path: il percorso completo del file di destinazione definito in config.py

    os.makedirs(os.path.dirname(path), exist_ok=True)
    #os.path.dirname(path) estrae solo la parte della cartella dal percorso
    #exist_ok=True evita errori se la cartella esiste già

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    #w --> apre il file in modalità scrittura: se il file non esiste lo crea; se esiste già lo sovrascrive

