#salvataggio del report

import os
import markdown

#salva il report in due formati:
#    - .md --> testo Markdown grezzo
#    - .html --> apribile nel browser senza software aggiuntivo
#
#text: il testo del report generato dal writer
#path: il percorso completo del file di destinazione definito in config.py
def save_report(text, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    #os.path.dirname(path) estrae solo la parte della cartella dal percorso
    #exist_ok=True evita errori se la cartella esiste già

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    #w --> apre il file in modalità scrittura: se il file non esiste lo crea; se esiste già lo sovrascrive

    #salva anche la versione html apribile nel browser
    #markdown.markdown() converte la sintassi markdown in tag html
    html_path = path.replace(".md", ".html")
    html_content = markdown.markdown(text)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; line-height: 1.6; color: #333; }}
  h1 {{ color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 8px; }}
  h2 {{ color: #2c3e50; border-bottom: 1px solid #ddd; padding-bottom: 4px; }}
  h3 {{ color: #2c3e50; }}
  ul {{ padding-left: 20px; }}
  li {{ margin-bottom: 6px; }}
  strong {{ color: #2c3e50; }}
  hr {{ border: none; border-top: 1px solid #ddd; margin: 20px 0; }}
</style>
</head>
<body>{html_content}</body>
</html>""")

    print("Report HTML salvato in:", html_path)
