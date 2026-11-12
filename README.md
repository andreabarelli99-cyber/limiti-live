# Limiti Live — quinta liceo linguistico

Lezione HTML completa con grafici interattivi individuali sugli smartphone, 10 quiz sincronizzati e statistiche aggregate sulla LIM.

## Pubblicazione

1. Crea una **repository pubblica** su GitHub (es. `limiti-live`).
2. Carica **tutti i file e la cartella `templates`**, mantenendo la struttura. Puoi estrarre lo ZIP e caricare il contenuto, non il file ZIP.
3. Vai su https://dashboard.render.com/ → **New → Blueprint**; collega GitHub, seleziona la repository e conferma la creazione dal file `render.yaml`.
4. Quando Render richiede `TEACHER_PASSWORD`, inserisci una password lunga e riservata (non nel repository). `SECRET_KEY` viene generata automaticamente.
5. Attendi il deploy e apri l'URL HTTPS indicato da Render (es. `https://nome-servizio.onrender.com`).
6. Sul computer del docente apri `https://.../teacher`, effettua l'accesso e mostra il QR code. Il QR porta gli studenti a `/lezione`.
7. Per proiettare la presentazione apri `/lezione` in una seconda scheda della LIM. I grafici e i cursori funzionano anche sul telefono.
8. Dal pannello docente: **Apri domanda → Chiudi risposte → Mostra soluzione → Termina domanda**. Le statistiche si aggiornano ogni 2 secondi.

## Funzionamento

- Gli studenti non devono registrarsi e non devono trovarsi sulla stessa rete Wi-Fi.
- I quiz vengono visualizzati in un pannello apribile/chiudibile sopra la presentazione, che resta navigabile liberamente.
- Ogni browser può inviare una sola risposta per domanda aperta; le risposte non sono nominative.
- Le risposte e lo stato della lezione sono **in memoria**: si perdono se Render riavvia il servizio. Non è adatto a valutazioni ufficiali.
- È necessario **un solo worker e una sola istanza**; il progetto non usa un database.
- Se Render usa un piano gratuito, il servizio può andare in standby e richiedere tempo al primo accesso. Avvialo prima della lezione.
- Per usare MathJax è richiesta connessione Internet; la presentazione carica MathJax da CDN.
- La password del docente va configurata in Render, mai nel codice. La sessione usa cookie firmati; usare HTTPS.
- Il QR usa l'indirizzo del server corrente. Per provarlo in locale, apri il server tramite un indirizzo raggiungibile dagli smartphone, non `localhost`.

## Test locale (opzionale)

```bash
python -m venv .venv
pip install -r requirements.txt
# Linux/macOS
export TEACHER_PASSWORD='scegli-una-password'
export SECRET_KEY='scegli-una-chiave-lunga'
python app.py
```

Su Windows PowerShell usare `$env:TEACHER_PASSWORD="..."` e `$env:SECRET_KEY="..."`.

Apri `http://127.0.0.1:10000/teacher` e `http://127.0.0.1:10000/lezione`.

## Note didattiche

La presentazione include la definizione di limite finito, i grafici con epsilon e delta, limiti laterali, limiti infiniti, esperimenti e attività. I quiz dal vivo sono selezionati dal docente, indipendentemente dalla schermata proiettata. Gli studenti possono sperimentare sui propri dispositivi senza interferire con la LIM.
