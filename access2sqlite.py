import os
import pyodbc
import sqlite3
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from sqlalchemy import create_engine

def access_to_sqlite(access_db_path):
    # Estrai la cartella e il nome del file senza estensione
    folder_path, file_name = os.path.split(access_db_path)
    base_name, _ = os.path.splitext(file_name)
    
    # Crea il percorso del file SQLite con estensione .sqlite
    sqlite_db_path = os.path.join(folder_path, f"{base_name}.sqlite")
    
    # Connessione al database Access
    access_conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_db_path};"
    access_conn = pyodbc.connect(access_conn_str)
    
    # Connessione al database SQLite usando SQLAlchemy
    sqlite_engine = create_engine(f"sqlite:///{sqlite_db_path}")

    # Ottieni tutte le tabelle nel database Access
    access_cursor = access_conn.cursor()
    tables = [row.table_name for row in access_cursor.tables(tableType='TABLE')]
    
    for table in tables:
        try:
            # Aggiungi parentesi quadre attorno al nome della tabella per gestire i nomi con spazi
            sql_query = f"SELECT * FROM [{table}]"
            # Leggi i dati dalla tabella Access
            df = pd.read_sql_query(sql_query, access_conn)
            
            # Scrivi i dati nella tabella SQLite con la creazione automatica della tabella
            df.to_sql(table, sqlite_engine, if_exists='replace', index=False)

            # Controlla se la tabella ha una colonna ID e deve essere autoincrementata
            if 'ID' in df.columns:
                set_autoincrement(sqlite_engine, table, df)
        
        except Exception as e:
            print(f"Errore durante la lettura della tabella '{table}': {e}")
            messagebox.showerror("Errore", f"Si è verificato un errore durante la lettura della tabella '{table}': {e}")

    # Chiudi le connessioni
    access_conn.close()
    sqlite_engine.dispose()

    print(f"Conversione completata: {sqlite_db_path}")

def set_autoincrement(sqlite_engine, table_name, df):
    sqlite_conn = sqlite_engine.raw_connection()
    cursor = sqlite_conn.cursor()

    # Ottieni il nome delle colonne e i loro tipi dal DataFrame
    columns_with_types = []
    for col, dtype in zip(df.columns, df.dtypes):
        sql_dtype = 'TEXT'
        if dtype.name.startswith('int'):
            sql_dtype = 'INTEGER'
        elif dtype.name.startswith('float'):
            sql_dtype = 'REAL'
        columns_with_types.append(f"[{col}] {sql_dtype}")

    columns_def = ", ".join(columns_with_types)
    
    # Crea una nuova tabella temporanea con AUTOINCREMENT per la colonna ID
    temp_table_name = f"{table_name}_temp"
    create_table_sql = f"CREATE TABLE '{temp_table_name}' (ID INTEGER PRIMARY KEY AUTOINCREMENT, {', '.join(columns_with_types[1:])})"
    
    cursor.execute(create_table_sql)
    
    # Copia i dati dalla vecchia tabella alla nuova tabella
    columns = ", ".join([f"[{col}]" for col in df.columns])  # Racchiude ogni nome di colonna tra apici quadri
    cursor.execute(f"INSERT INTO '{temp_table_name}' ({columns}) SELECT {columns} FROM [{table_name}]")
    
    # Elimina la vecchia tabella e rinomina la nuova tabella
    cursor.execute(f"DROP TABLE [{table_name}]")
    cursor.execute(f"ALTER TABLE '{temp_table_name}' RENAME TO [{table_name}]")
    
    sqlite_conn.commit()
    sqlite_conn.close()

def browse_file():
    # Apri una finestra di dialogo per selezionare il file Access
    file_path = filedialog.askopenfilename(
        filetypes=[("Access Database Files", "*.accdb")],
        title="Seleziona il file Access"
    )
    if file_path:
        # Avvia il processo di conversione
        try:
            access_to_sqlite(file_path)
            messagebox.showinfo("Successo", "Conversione completata con successo!")
        except Exception as e:
            print(f"Errore durante la conversione:\n{e}")
            messagebox.showerror("Errore", f"Si è verificato un errore durante la conversione:\n{e}")

def create_gui():
    # Crea la finestra principale
    root = tk.Tk()
    root.title("Convertitore Access a SQLite")
    
    # Imposta la dimensione della finestra
    root.geometry("300x150")
    
    # Crea un pulsante per selezionare il file Access e avviare la conversione
    browse_button = tk.Button(root, text="Seleziona file Access", command=browse_file)
    browse_button.pack(expand=True)
    
    # Avvia il loop principale dell'interfaccia grafica
    root.mainloop()

# Avvia l'interfaccia grafica
create_gui()
