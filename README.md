# Gestionale Clienti

**Gestionale Clienti** è un'applicazione di gestione clienti sviluppata in Python utilizzando PyQt5 e pyodbc. L'applicazione consente di gestire i dati dei clienti tramite un'interfaccia utente grafica e un database Microsoft Access.

## Requisiti

- Python 3.x
- PyQt5
- pyodbc
- Microsoft Access Driver (*.mdb, *.accdb)

## Installazione

1. **Clona il repository**:

    ```bash
    git clone https://github.com/AntoP96/gestionale-clienti
    ```

2. **Naviga nella directory del progetto**:

    ```bash
    cd gestionale-clienti
    ```

3. **Installa le dipendenze**:

    ```bash
    pip install -r requirements.txt
    ```

    Assicurati di avere Microsoft Access Driver installato sul tuo sistema.

4. **Configura il file `config.txt`**:

    Modifica il file `config.txt` per specificare il percorso del tuo database Access. Esempio di contenuto:

    ```
    C:\percorso\al\tuo\database.accdb
    ```

## Utilizzo

1. **Avvia l'applicazione**:

    Esegui il file Python principale `gestioneClienti.py`:

    ```bash
    python gestioneClienti.py
    ```

2. **Interfaccia Utente**:

    - **Login**: Inserisci il nome utente e la password per accedere all'applicazione.
    - **Home Page**: Cerca un cliente esistente o crea un nuovo cliente.
    - **Customer Page**: Visualizza e modifica i dati del cliente selezionato.

3. **Costruzione dell'applicazione (opzionale)**:

    Se desideri creare un eseguibile standalone, puoi utilizzare PyInstaller:

    ```bash
    python -m PyInstaller --name "Gestionale Clienti" --onefile gestioneClienti.py
    ```

    Modifica il file `.spec` per inserire i file esterni se necessario e poi esegui (come nel file `Gestionale Clienti.spec.example`)

    Builda l'applicazione completa:

    ```bash
    python -m PyInstaller "Gestionale Clienti.spec"
    ```

## Contributi

I contributi sono benvenuti! Se hai suggerimenti o migliorie, sentiti libero di aprire una *pull request* o di segnalare un problema.

## Licenza

Questo progetto è concesso in licenza sotto la Licenza MIT - vedi il file [LICENSE](LICENSE) per i dettagli.

## Contatti

Per supporto o domande, contattami a: [apaolino96@gmail.com](mailto:apaolino96@gmail.com)
