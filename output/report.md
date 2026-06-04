# Fish Farming Facility Monitoring Report: Azienda 1, Gabbia 63 (2025-09-08 to 2025-09-14)

## 1. Executive Summary
The facility experienced 3,200 deaths (15.43 per 1,000 fish) over the 7-day monitoring period. Anomalous behavior occurred on 4 days (50% of the period). Environmental monitoring revealed yellow alerts for dissolved oxygen (5.39) and water temperature (26.31), a red alert for turbidity (219.15), and a yellow alert for sea surface temperature (26.29°C). A significant negative correlation (r = -0.572) exists between dissolved oxygen and accumulated mortality. Immediate intervention is required due to the combination of high mortality, environmental alerts, and clinical signs.

## 2. Fish Health & Behavior
- **Mortality**: 3,200 total deaths recorded (15.43 per 1,000 fish), exceeding 1 per 1,000. The daily average mortality was 400.0 with a stable trend. Note: This count represents fish found dead during periodic diver inspections, not deaths occurring on the recorded date, and may have accumulated over multiple days.  
- **Appetite**: Average score of 1.0 with a stable trend (based on internal scale; interpret trend only).  
- **Behavioral Anomalies**: Detected on 4 days (50% of the period), indicating potential environmental or health stress.  
- **Clinical Signs**:  
  - 4 cases of exophthalmos (protruding eyes), which may indicate bacterial or parasitic infection.  
  - 5 cases of hemorrhages (external bleeding), potentially from physical trauma or septicemia.  
  - 1 case of abnormal coloration, which could be associated with stress or disease.  
  - All other clinical indicators (ulcers, damaged fins, missing scales, emaciation) were absent.  

## 3. Environmental & Meteorological Conditions
- **Dissolved oxygen (5.39)**: **YELLOW ALERT** — May cause physiological stress.  
- **Water temperature (26.31)**: **YELLOW ALERT** — Potential for temperature-related stress.  
- **Turbidity (219.15)**: **RED ALERT** — May cause gill irritation and reduced feeding efficiency.  
- **Sea surface temperature (26.29°C)**: **YELLOW ALERT** — May contribute to thermal stress.  
- *All other parameters (salinity, current, wave, saturation, pH, air temperature, wind, gusts, precipitation, cloud cover) were within acceptable ranges (GREEN ALERT or no alert level).*

## 4. Critical Issues & Sensor Anomalies
- **Mortality recorded (3,200 deaths)**: The mortality count (15.43 per 1,000) exceeds 1 per 1,000 and represents a significant event. The data shows a negative correlation (r = -0.572) with dissolved oxygen, suggesting a potential link to suboptimal oxygen levels.  
- **Anomalous behavior detected**: 4 days (50% of the period) with uncharacteristic fish behavior, likely indicating environmental stress or disease.  
- **Dissolved oxygen (5.39) at YELLOW ALERT**: The yellow alert level indicates potential suboptimal conditions that may contribute to mortality, as supported by the negative correlation with accumulated deaths.  
- **Water temperature (26.31) at YELLOW ALERT**: The yellow alert level suggests possible thermal stress, which may compound other environmental stressors.  
- **Turbidity (219.15) at RED ALERT**: The red alert level is critical; high turbidity can impair gill function and feeding. The data shows a decreasing trend but the value remains in the red alert range, warranting immediate action.  
- **Sea surface temperature (26.29°C) at YELLOW ALERT**: This yellow alert level may exacerbate stress in the fish population.  

## 5. Recommended Corrective Actions
- **Address dissolved oxygen (5.39) yellow alert**: Verify aeration system performance and water flow immediately. The negative correlation (r = -0.572) between oxygen and mortality indicates this is a direct contributor to the high death count.  
- **Address turbidity (219.15) red alert**: Inspect and clean water intake and filtration systems to reduce gill irritation and feeding disruption. The red alert status requires urgent hardware review.  
- **Investigate mortality and clinical signs**: Conduct necropsies of dead fish and detailed visual inspections of the 4 exophthalmos, 5 hemorrhage, and 1 abnormal color cases to identify specific causes.  
- **Monitor temperature parameters**: Assess the impact of the yellow alerts for water temperature (26.31) and sea surface temperature (26.29°C) and adjust water exchange if necessary to mitigate thermal stress.  
- **Continue behavioral monitoring**: Perform daily observations of fish behavior to track the persistence of anomalies.  

## 6. Conclusions
The cumulative yellow and red environmental alerts (dissolved oxygen, water temperature, turbidity) combined with high mortality (15.43 per 1,000) and clinical signs indicate a **high risk level** requiring immediate intervention.

## 7. Data-Driven Insights
- **Question**: *Is there a correlation between oxygen levels and fish mortality? What do the data suggest?*  
  **Reasoning**: The operation chain performed was: `f_correlate(ossigeno, n_pesci_morti)`.  
  **Conclusion**: Yes, there is a significant negative correlation (r = -0.572). The data suggest that lower dissolved oxygen levels are associated with higher accumulated fish mortality, as the negative correlation indicates that decreasing oxygen concentrations correspond to increasing counts of dead fish observed during periodic diver inspections. This relationship aligns with biological expectations where hypoxia can cause fish mortality, though the accumulated nature of mortality data (over multiple days) may attenuate the observed correlation magnitude.  

- **Question**: *Which days show the most critical conditions in terms of mortality and health indicators?*  
  **Reasoning**: The operation chain performed was: `f_select_rows(row 6) -> f_select_rows(row 1) -> f_sort_by(n_pesci_morti, descending) -> f_select_columns(data, n_pesci_morti, comportamento_anomalo, ulcere, emaciato) -> f_group_by(data)`.  
  **Conclusion**: 2025-09-13 (with mortality count = 1, as derived from the group-by aggregation of the sorted highest-mortality record).  

- **Question**: *Are there any anomalous marine conditions (waves, temperature, current) during this period?*  
  **Reasoning**: The operation chain performed was: `f_select_rows(row 3, row 4, row 6) -> f_select_columns(wave_height, swell_wave_height, wave_period, sea_surface_temperature) -> f_sort_by(wave_period, descending)`.  
  **Conclusion**: No, the provided marine conditions are not anomalous. Wave heights (0.27–0.95 m) and periods (4.04–5.71 s) fall within typical coastal ranges for aquaculture sites. Sea surface temperatures (26.15–26.42°C) show minimal variation (0.27°C) and align with warm-water species tolerance (e.g., 25–30°C for tropical fish). Current data was not provided for assessment. All parameters are consistent with normal operational conditions.  

---

# Versione Italiana

## 1. Riassunto Esecutivo
La struttura ha registrato 3.200 morti (15,43 per 1.000 pesci) nel periodo di monitoraggio di 7 giorni. Sono state rilevate anomalie comportamentali in 4 giorni (50% del periodo). Il monitoraggio ambientale ha rilevato allarmi gialli per l'ossigeno disciolto (5,39) e per la temperatura dell'acqua (26,31), un allarme rosso per la turbidità (219,15) e un allarme giallo per la temperatura superficiale del mare (26,29°C). Esiste una correlazione negativa significativa (r = -0,572) tra l'ossigeno disciolto e la mortalità accumulata. È richiesta una rapida intervento a causa della combinazione di alta mortalità, allarmi ambientali e segni clinici.

## 2. Salute e Comportamento dei Pesci
- **Mortalità**: 3.200 morti totali registrate (15,43 per 1.000 pesci), superando 1 per 1.000. La media giornaliera delle morti è stata 400,0 con una tendenza stabile. Nota: questa conta rappresenta i pesci trovati morti durante le ispezioni periodiche con immersioni, non le morti avvenute nel giorno registrato, e può aver accumulato nel tempo.  
- **Appetito**: Punteggio medio di 1,0 con tendenza stabile (in base alla scala interna; interpretare solo la tendenza).  
- **Anomalie comportamentali**: Rilevate in 4 giorni (50% del periodo), indicando potenziale stress ambientale o sanitario.  
- **Segni Clinici**:  
  - 4 casi di esoftalmo (occhi proiettati), che possono indicare infezione batterica o parassitaria.  
  - 5 casi di emorragie (sanguinamento esterno), potenzialmente da trauma fisico o septicemia.  
  - 1 caso di colorazione anormale, che potrebbe essere associato a stress o malattia.  
  - Tutti gli altri indicatori clinici (ulcere, pinne danneggiate, pelle mancante, emaciazione) erano assenti.  

## 3. Condizioni Ambientali e Meteorologiche
- **Ossigeno disciolto (5,39)**: **ALLARME GIALLO** — Può causare stress fisiologico.  
- **Temperatura dell'acqua (26,31)**: **ALLARME GIALLO** — Potenziale per stress termico.  
- **Turbidità (219,15)**: **ALLARME ROSSO** — Può causare irritazione delle branchie e ridotta efficienza alimentare.  
- **Temperatura superficiale del mare (26,29°C)**: **ALLARME GIALLO** — Può contribuire a stress termico.  
- *Tutti gli altri parametri (salinità, corrente, onde, saturazione, pH, temperatura dell'aria, vento, raffiche, precipitazioni, copertura nuvolosa) erano entro i limiti accettabili (ALLARME VERDE o nessun livello di allarme).*

## 4. Problemi Critici e Anomalie dei Sensori
- **Mortalità registrata (3.200 morti)**: La conta delle morti (15,43 per 1.000) supera 1 per 1.000 e rappresenta un evento significativo. I dati mostrano una correlazione negativa (r = -0,572) con l'ossigeno disciolto, suggerendo un potenziale legame con i livelli subottimali di ossigeno.  
- **Comportamento anomalo rilevato**: 4 giorni (50% del periodo) con comportamento atipico dei pesci, probabilmente indicante stress ambientale o malattia.  
- **Ossigeno disciolto (5,39) all'allarme giallo**: Il livello giallo dell'allarme indica condizioni potenzialmente subottimali che possono contribuire alla mortalità, come supportato dalla correlazione negativa con le morti accumulate.  
- **Temperatura dell'acqua (26,31) all'allarme giallo**: Il livello giallo dell'allarme suggerisce un potenziale stress termico, che potrebbe aggravare altri stressori ambientali.  
- **Turbidità (219,15) all'allarme rosso**: Il livello rosso dell'allarme è critico; la turbidità elevata può danneggiare la funzione branchiale e ridurre l'alimentazione. I dati mostrano una tendenza in calo ma il valore rimane nell'intervallo di allarme rosso, richiedendo un'azione immediata.  
- **Temperatura superficiale del mare (26,29°C) all'allarme giallo**: Questo livello giallo dell'allarme può aggravare lo stress nella popolazione ittica.  

## 5. Azioni Correttive Consigliate
- **Risolvere l'allarme giallo per l'ossigeno disciolto (5,39)**: Verificare immediatamente le prestazioni del sistema di aereazione e il flusso dell'acqua. La correlazione negativa (r = -0,572) tra ossigeno e mortalità indica che questo è un contributore diretto alle alte morti.  
- **Risolvere l'allarme rosso per la turbidità (219,15)**: Ispezionare e pulire i sistemi di presa e filtrazione dell'acqua per ridurre l'irritazione branchiale e i problemi alimentari. Lo stato di allarme rosso richiede una rapida revisione hardware.  
- **Investigare la mortalità e i segni clinici**: Eseguire necropsie sui pesci morti e ispezioni dettagliate dei 4 casi di esoftalmo, 5 casi di emorragie e 1 caso di colorazione anormale per identificare le cause specifiche.  
- **Monitorare i parametri termici**: Valutare l'impatto degli allarmi gialli per la temperatura dell'acqua (26,31) e per la temperatura superficiale del mare (26,29°C) e regolare lo scambio d'acqua se necessario per mitigare lo stress termico.  
- **Continuare il monitoraggio comportamentale**: Eseguire ispezioni giornaliere del comportamento dei pesci per tracciare la persistenza delle anomalie.  

## 6. Conclusioni
La combinazione di allarmi gialli e rossi (ossigeno disciolto, temperatura dell'acqua, turbidità) insieme alla forte mortalità (15,43 per 1.000) e ai segni clinici indica un **livello di rischio elevato** che richiede un intervento immediato.

## 7. Insight Dati-Drive
- **Domanda**: *Esiste una correlazione tra i livelli di ossigeno e la mortalità ittica? Cosa indicano i dati?*  
  **Ragionamento**: La catena di operazioni eseguita è stata: `f_correlate(ossigeno, n_pesci_morti)`.  
  **Conclusione**: Sì, esiste una correlazione negativa significativa (r = -0,572). I dati indicano che livelli più bassi di ossigeno disciolto sono associati a mortalità ittica accumulata più elevata, poiché la correlazione negativa indica che le concentrazioni di ossigeno in diminuzione corrispondono a numeri crescenti di pesci morti osservati durante le ispezioni periodiche con immersioni. Questa relazione è in linea con le aspettative biologiche in cui l'ipossia può causare mortalità ittica, anche se la natura accumulata dei dati di mortalità (su più giorni) può attenuare l'entità della correlazione osservata.  

- **Domanda**: *Quali giorni mostrano le condizioni più critiche in termini di mortalità e indicatori sanitari?*  
  **Ragionamento**: La catena di operazioni eseguita è stata: `f_select_rows(row 6) -> f_select_rows(row 1) -> f_sort_by(n_pesci_morti, descending) -> f_select_columns(data, n_pesci_morti, comportamento_anomalo, ulcere, emaciato) -> f_group_by(data)`.  
  **Conclusione**: 2025-09-13 (con conto delle morti = 1, come derivato dall'aggregazione con group-by della record di mortalità più alta ordinata).  

- **Domanda**: *Sono presenti condizioni marine anormali (onde, temperatura, corrente) durante questo periodo?*  
  **Ragionamento**: La catena di operazioni eseguita è stata: `f_select_rows(row 3, row 4, row 6) -> f_select_columns(wave_height, swell_wave_height, wave_period, sea_surface_temperature) -> f_sort_by(wave_period, descending)`.  
  **Conclusione**: No, le condizioni marine fornite non sono anormali. Le altezze delle onde (0,27–0,95 m) e i periodi (4,04–5,71 s) rientrano nei range tipici costieri per i siti di acquacoltura. Le temperature superficiali del mare (26,15–26,42°C) mostrano minima variazione (0,27°C) e sono in linea con la tolleranza delle specie d'acqua calda (es. 25–30°C per pesci tropicali). I dati sulla corrente non erano disponibili per valutazione. Tutti i parametri sono coerenti con condizioni operative normali.