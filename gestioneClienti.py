import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import sqlite3
from datetime import datetime
import os

def resource_path(relative_path):
    """ Get the absolute path to a resource, works for dev and for PyInstaller """
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

# File di configurazione dove salvare il percorso del database Access
CONFIG_FILE = resource_path("config.txt")

def load_config():
    global db_path
    try:
        with open(CONFIG_FILE, 'r') as file:
            db_path = file.readline().strip()
    except Exception as e:
        QMessageBox.critical(None, "Errore di Configurazione", f"Errore durante la lettura del file di configurazione: {str(e)}")
        print(f"Config error: {e}")
load_config()

# Connessione al database Access
def connect_db():
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        QMessageBox.critical(None, "Errore di Connessione", f"Errore durante la connessione al database: {str(e)}")
        print(f"Connection error: {e}")
        return None

def load_customers(customer_table):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()
    customer_table.setRowCount(len(tables))
    for row_idx, table in enumerate(tables):
        customer_name = table[0]
        cursor.execute(f"""
            SELECT SUM(TOTALE) 
            FROM [{customer_name}]
        """)
        total = cursor.fetchone()[0]
        total = total if total is not None else 0
        name_item = QTableWidgetItem(customer_name)
        name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        customer_table.setItem(row_idx, 0, name_item)

        total_item = QTableWidgetItem(str(total))
        total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        customer_table.setItem(row_idx, 1, total_item)
    customer_table.resizeColumnsToContents()
    conn.close()

# Funzione per caricare i dati di un cliente
def load_customer_data(customer_name):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        query = f"SELECT * FROM [{customer_name}]"
        cursor.execute(query)
        data = cursor.fetchall()  # Fetch data while the connection is open

        formatted_data = []
        for row in data:
            formatted_row = list(row)
            # Check if the date value is not None and is in the second column (index 1)
            date_value = row[1]  # Assuming the date is in the second column (index 1)
            if date_value:
                # Check if date_value is a datetime object or a string
                if isinstance(date_value, datetime):
                    formatted_row[1] = date_value.strftime("%d-%m-%Y")
                else:
                    # Try to convert the date if it's in string format
                    try:
                        # Handle common date formats
                        date_obj = datetime.strptime(date_value, "%Y-%m-%d %H:%M:%S.%f")
                        formatted_row[1] = date_obj.strftime("%d-%m-%Y")
                    except ValueError:
                        try:
                            date_obj = datetime.strptime(date_value, "%Y-%m-%d")
                            formatted_row[1] = date_obj.strftime("%d-%m-%Y")
                        except ValueError:
                            try:
                                date_obj = datetime.strptime(date_value, "%d-%m-%Y")
                                formatted_row[1] = date_obj.strftime("%d-%m-%Y")
                            except ValueError:
                                formatted_row[1] = date_value  # Keep the original value if not convertible
            else:
                formatted_row[1] = None  # Set to None if the original date was None

            formatted_data.append(tuple(formatted_row))  # Convert the list back to a tuple
        return formatted_data
    except Exception as e:
        print(f"Errore durante il caricamento dei dati del cliente: {e}")
        return None
    finally:
        conn.close()

def save_customer_data(customer_name, data, deleted_row_ids):
    conn = connect_db()  # Ottieni la connessione al database
    cursor = conn.cursor()

    try:
        # Ottieni gli ID esistenti nel database
        cursor.execute(f"SELECT ID FROM [{customer_name}]")
        existing_ids = {str(row[0]) for row in cursor.fetchall()}  # Assicurati che siano stringhe per il confronto

        # Costruisci l'elenco di ID da eliminare, assicurandoti che gli ID siano nel set esistente
        ids_to_delete = {str(id_) for id_ in deleted_row_ids if id_ in existing_ids}

        # Elimina anche le righe vuote (dove tutte le celle sono None o vuote)
        for row in data:
            row_id = str(row[0]) if row[0] else None
            if row_id in existing_ids and all(cell is None or cell == '' for cell in row):
                ids_to_delete.add(row_id)

        # Esegui la query di eliminazione se ci sono ID da eliminare
        if ids_to_delete:
            ids_to_delete_str = ', '.join(map(str, ids_to_delete))
            # print(f"DELETE FROM [{customer_name}] WHERE ID IN ({ids_to_delete_str})")
            cursor.execute(f"DELETE FROM [{customer_name}] WHERE ID IN ({ids_to_delete_str})")

        # Inserisci o aggiorna i dati esistenti
        for row in data:
            if all(cell is None or cell == '' for cell in row):
                continue  # Salta le righe completamente vuote

            row_id = row[0] if row[0] else None  # Ottieni l'ID della riga
            date_value = row[1]
            if date_value:
                try:
                    date_obj = datetime.strptime(date_value, "%d-%m-%y")
                    date_value = date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    pass  # Mantieni il valore originale

            numero_fattura_value = row[2] if row[2] else None
            dare_value = float(row[3]) if row[3] else 0.0
            avere_value = float(row[4]) if row[4] else 0.0
            totale_value = float(row[5]) if row[5] else 0.0
            note_value = row[6] if row[6] else None

            if row_id and row_id in existing_ids:  # Aggiorna se l'ID esiste
                query = f"""
                    UPDATE [{customer_name}]
                    SET [DATA] = ?, [NUMERO FATTURA] = ?, [DARE] = ?, [AVERE] = ?, [TOTALE] = ?, [NOTE] = ?
                    WHERE ID = ?
                """
                cursor.execute(query, (date_value, numero_fattura_value, dare_value, avere_value, totale_value, note_value, row_id))
            elif row_id is None:  # Inserisci una nuova riga solo se l'ID è None
                query = f"""
                    INSERT INTO [{customer_name}] 
                    ([DATA], [NUMERO FATTURA], [DARE], [AVERE], [TOTALE], [NOTE])  
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                # print((query, (date_value, numero_fattura_value, dare_value, avere_value, totale_value, note_value)))
                cursor.execute(query, (date_value, numero_fattura_value, dare_value, avere_value, totale_value, note_value))

        # Commetti le modifiche
        conn.commit()

    except Exception as e:
        print(f"Errore durante l'inserimento dei dati: {e}")
        conn.rollback()  # Annulla le modifiche in caso di errore
    finally:
        QMessageBox.information(None, "Successo", f"Dati del cliente {customer_name} salvati con successo.")
        conn.close()

# Funzione per verificare se il nome del cliente è unico
def is_customer_name_unique(customer_name):
    conn = connect_db()  # Ottieni la connessione al database
    cursor = conn.cursor()
    
    try:
        # Esegui una query per verificare se la tabella esiste
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (customer_name,))
        
        # Se troviamo un risultato, la tabella esiste già
        if cursor.fetchone() is not None:
            return False  # La tabella esiste già
        else:
            return True  # La tabella non esiste, quindi il nome è unico
    except sqlite3.Error as e:
        print(f"Errore durante la verifica della tabella: {e}")
        return False  # In caso di errore, supponiamo che la tabella non sia unica
    finally:
        conn.close()

# Funzione per creare una nuova tabella cliente
def create_new_customer(customer_name):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Crea la query per creare una nuova tabella
        query = f"""
        CREATE TABLE {customer_name} (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            DATA DATE,
            [NUMERO FATTURA] TEXT,
            DARE REAL,
            AVERE REAL,
            TOTALE REAL,
            NOTE TEXT
        )
        """
        cursor.execute(query)
        conn.commit()
        QMessageBox.information(None, "Successo", f"Tabella per {customer_name} creata con successo.")
    except sqlite3.Error as e:
        print(f"Errore durante la creazione della tabella: {e}")
        QMessageBox.critical(None, "Errore", f"Impossibile creare la tabella per {customer_name}: {str(e)}")
    finally:
        conn.close()

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setGeometry(400, 200, 300, 200)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.image_label = QLabel(self)
        pixmap = QPixmap(resource_path("bg.png"))
        self.image_label.setPixmap(pixmap)
        self.image_label.setScaledContents(True)
        self.image_label.setGeometry(0, 0, self.width(), self.height())
        layout.addWidget(self.image_label)

        input_layout = QVBoxLayout()
        input_layout.addWidget(QLabel("Nome Utente:"))
        self.username_input = QLineEdit()
        input_layout.addWidget(self.username_input)
        input_layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        input_layout.addWidget(self.password_input)
        self.login_button = QPushButton("Accedi")
        self.login_button.clicked.connect(self.check_login)
        input_layout.addWidget(self.login_button)
        input_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container_widget = QWidget(self)
        container_widget.setLayout(input_layout)
        container_widget.setGeometry(10, self.height() - 150, self.width() - 20, 140)
        layout.addWidget(container_widget)
        self.setLayout(layout)

    def resizeEvent(self, event):
        self.image_label.setGeometry(0, 0, self.width(), self.height())

    def check_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if username == "Alfonso" and password == "password123":
            self.parent().setCurrentIndex(1)  # Vai alla home page
            self.parent().parent().enable_menu_actions()
            self.username_input.clear()
            self.password_input.clear()
        else:
            self.username_input.clear()
            self.password_input.clear()
            QMessageBox.critical(self, "Errore di accesso", "Nome utente o password errati.")

class CustomerPage(QWidget):
    def __init__(self):
        super().__init__()
        self.deleted_row_ids = set()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Tabella principale
        self.table = QTableWidget(0, 7)  # 7 colonne
        headers = ["ID", "DATA", "NUMERO FATTURA", "DARE", "AVERE", "TOTALE", "NOTE"]
        self.table.setHorizontalHeaderLabels(headers)

        # Nascondi la colonna ID (colonna 0)
        self.table.setColumnHidden(0, True)

        # Imposta il font in grassetto per le intestazioni
        header_font = QFont()
        header_font.setBold(True)
        header_view = self.table.horizontalHeader()
        header_view.setStyleSheet("font-weight: bold;")

        # Allarga colonne e estende l'ultima sezione
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 140)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 90)
        header_view.setStretchLastSection(True)

        # Imposta la politica del menu contestuale e delegate
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.date_delegate = DateDelegate(self.table)
        self.table.setItemDelegateForColumn(1, self.date_delegate)
        
        layout.addWidget(self.table)

        # Riga dei totali
        total_layout = QHBoxLayout()

        # Etichetta per il nome del cliente
        self.customer_name_label = QLabel("")
        self.customer_name_label.setFont(header_font)

        # Layout per DARE
        dare_layout = QHBoxLayout()
        self.total_dare_label = QLabel("DARE:")
        self.total_dare = QLabel("0.00 €")
        dare_layout.addWidget(self.total_dare_label)
        dare_layout.addWidget(self.total_dare)
        dare_layout.addStretch()

        # Layout per AVERE
        avere_layout = QHBoxLayout()
        self.total_avere_label = QLabel("AVERE:")
        self.total_avere = QLabel("0.00 €")
        avere_layout.addWidget(self.total_avere_label)
        avere_layout.addWidget(self.total_avere)
        avere_layout.addStretch()

        # Layout per TOTALE
        totale_layout = QHBoxLayout()
        self.total_totale_label = QLabel("TOTALE:")
        self.total_totale = QLabel("0.00 €")
        totale_layout.addWidget(self.total_totale_label)
        totale_layout.addWidget(self.total_totale)
        totale_layout.addStretch()

        # Aggiungi i layout alla riga totale principale
        total_layout.addWidget(self.customer_name_label)
        total_layout.addStretch()
        total_layout.addLayout(dare_layout)
        total_layout.addLayout(avere_layout)
        total_layout.addLayout(totale_layout)

        layout.addLayout(total_layout)

        # Pulsanti
        self.save_button = QPushButton("Salva")
        self.save_button.clicked.connect(self.save_data)

        self.back_button = QPushButton("Indietro")
        self.back_button.clicked.connect(self.go_back)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.back_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.apply_theme()

        # Connetti le modifiche della tabella ai calcoli totali
        self.table.itemChanged.connect(self.on_item_changed)

        # Imposta i validatori per le colonne Dare e Avere
        self.dare_validator = QDoubleValidator(0.0, 1e6, 2)
        self.avere_validator = QDoubleValidator(0.0, 1e6, 2)

    def apply_theme(self):
        # Applica il tema e stili alla tabella
        table_style = """
            QTableWidget {
                background-color: #f9f9f9;  /* Sfondo chiaro della tabella */
                color: #000000;              /* Colore del testo */
                border: 1px solid #d0d0d0;  /* Bordo della tabella */
            }
            QHeaderView::section {
                background-color: #e0e0e0;  /* Sfondo intestazioni chiaro */
                color: #000000;             /* Colore testo intestazioni */
                border: 1px solid #b0b0b0;  /* Bordo intestazioni chiaro */
                padding: 5px;               /* Padding intestazioni */
            }
            QTableWidget::item:selected {
                background-color: #d0d0d0;  /* Sfondo delle celle selezionate */
                color: #000000;             /* Colore testo delle celle selezionate */
            }
            QTableWidget::item:hover {
                background-color: #f0f0f0;  /* Sfondo delle celle al passaggio del mouse */
            }
            QTableWidget QTableCornerButton::section {
                background-color: #e0e0e0;  /* Sfondo angolo in alto a sinistra */
            }
        """
        self.table.setStyleSheet(table_style)

    def load_data(self, customer_name):
        self.customer_name = customer_name
        self.customer_name_label.setText(customer_name)  # Imposta il nome del cliente
        data = load_customer_data(customer_name)
        if data is not None:
            # Converti e ordina i dati in base alla colonna della data (assumendo che la data sia nella colonna 1)
            try:
                # Converti le date in QDate e ordina i dati
                data.sort(key=lambda x: QDate.fromString(x[1], "dd-MM-yyyy"))
            except Exception as e:
                QMessageBox.warning(self, "Errore", f"Errore nell'ordinamento delle date: {e}")
                data.sort(key=lambda x: x[1])  # Ordina per data come stringa se l'ordinamento per QDate fallisce

            self.table.setRowCount(0)  # Pulisce la tabella
            for row_data in data:
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                for col_index, cell_data in enumerate(row_data):
                    item_text = str(cell_data) if cell_data is not None else ""
                    item = QTableWidgetItem(item_text)
                    
                    if col_index == 0:  # ID column
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    elif col_index in [3, 4, 5]:  # DARE and AVERE columns
                        item.setText(self.format_number(float(cell_data)) if cell_data else "0.00")
                    if col_index == 5:  # TOTALE column
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    
                    self.table.setItem(row_position, col_index, item)
            
            self.calculate_totals()
        else:
            QMessageBox.warning(self, "Errore", f"Impossibile caricare i dati per il cliente '{customer_name}'.")

    def save_data(self):
        customer_name = self.customer_name
        row_count = self.table.rowCount()
        data = []

        for row in range(row_count):
            row_data = []
            for col in range(7):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        # print(f"IDs to delete: {self.deleted_row_ids}")
        save_customer_data(customer_name, data, self.deleted_row_ids)
        # Pulisci la lista degli ID eliminati
        self.deleted_row_ids.clear()

    def delete_row(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            item_id = self.table.item(current_row, 0)
            if item_id and item_id.text():  # Controlla se l'elemento ID esiste e ha testo
                # print(f"Deleting row with ID: {item_id.text()}")
                self.deleted_row_ids.add(item_id.text())  # Aggiungi l'ID alla lista
            self.table.removeRow(current_row)
            self.calculate_totals()

    def on_item_changed(self, item):
        if item.column() in [3, 4]:  # Colonne Dare e Avere
            try:
                item.setText(self.format_number(float(item.text())) if item.text() else "0.00")
                self.calculate_row_total(item.row())
                self.calculate_totals()
            except ValueError:
                item.setText("0.00")  # Imposta a zero se il valore non è valido

    def calculate_row_total(self, row):
        dare_item = self.table.item(row, 3)
        avere_item = self.table.item(row, 4)
        
        dare_value = float(dare_item.text()) if dare_item and dare_item.text() else 0
        avere_value = float(avere_item.text()) if avere_item and avere_item.text() else 0
        totale_value = round(dare_value - avere_value, 2)

        totale_item = QTableWidgetItem(self.format_number(totale_value))
        totale_item.setFlags(totale_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 5, totale_item)

        # Aggiorna il colore di sfondo della riga
        self.update_row_background_color(row)

    def calculate_totals(self):
        self.total_dare_value = 0
        self.total_avere_value = 0
        self.total_totale_value = 0

        for row in range(self.table.rowCount()):
            dare_item = self.table.item(row, 3)
            avere_item = self.table.item(row, 4)
            totale_item = self.table.item(row, 5)

            self.total_dare_value += float(dare_item.text()) if dare_item and dare_item.text() else 0
            self.total_avere_value += float(avere_item.text()) if avere_item and avere_item.text() else 0
            self.total_totale_value += float(totale_item.text()) if totale_item and totale_item.text() else 0

        self.total_dare.setText(f"{self.format_number(self.total_dare_value)} €")
        self.total_avere.setText(f"{self.format_number(self.total_avere_value)} €")
        self.total_totale.setText(f"{self.format_number(self.total_totale_value)} €")

        # Aggiorna il colore di sfondo di tutte le righe
        self.update_all_rows_background_color()

    def format_number(self, value):
        return f"{value:.2f}"

    def go_back(self):
        self.parent().setCurrentIndex(1)

    def show_context_menu(self, pos):
        menu = QMenu()
        add_above_action = QAction("Aggiungi Riga Sopra", self)
        add_below_action = QAction("Aggiungi Riga Sotto", self)
        delete_action = QAction("Elimina Riga", self)
        
        add_above_action.triggered.connect(self.add_row_above)
        add_below_action.triggered.connect(self.add_row_below)
        delete_action.triggered.connect(self.delete_row)
        
        menu.addAction(add_above_action)
        menu.addAction(add_below_action)
        menu.addAction(delete_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def add_row_above(self):
        current_row = self.table.currentRow()
        self.table.insertRow(current_row)
        self.set_current_row(current_row)

    def add_row_below(self):
        current_row = self.table.currentRow()
        self.table.insertRow(current_row + 1)
        self.set_current_row(current_row + 1)

    def set_current_row(self, row):
        self.table.setCurrentCell(row, 0)

    def set_row_background_color(self, row, color):
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setBackground(color)

    def update_row_background_color(self, row):
        totale_item = self.table.item(row, 5)
        
        if totale_item:
            totale_value = float(totale_item.text()) if totale_item.text() else 0
            
            # Applica il colore solo alla cella "Totale"
            row_color = QColor(255, 0, 0) if totale_value < 0 else QColor(255, 255, 255)
            totale_item.setBackground(row_color)  # Imposta il colore solo per la cella "Totale"
        else:
            # Se l'item non esiste, puoi creare un nuovo QTableWidgetItem con il colore di default
            totale_item = QTableWidgetItem()
            totale_item.setBackground(QColor(255, 255, 255))
            self.table.setItem(row, 5, totale_item)
        
        self.table.viewport().update()
        self.table.update()
        self.repaint()

    def update_all_rows_background_color(self):
        for row in range(self.table.rowCount()):
            self.update_row_background_color(row)

class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Aggiungi un'immagine di sfondo
        self.image_label = QLabel(self)
        pixmap = QPixmap(resource_path("bg.png"))
        self.image_label.setPixmap(pixmap)
        self.image_label.setScaledContents(True)
        self.image_label.setGeometry(0, 0, self.width(), self.height())
        layout.addWidget(self.image_label)

        # Layout orizzontale per separare la tabella dei clienti e i campi di input
        main_layout = QHBoxLayout()

        # Crea la tabella per visualizzare i clienti
        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(2)
        self.customer_table.setHorizontalHeaderLabels(["Nome Cliente", "Totale"])
        self.customer_table.cellClicked.connect(self.on_customer_click)

        # Carica i dati dei clienti
        load_customers(self.customer_table)

        # Layout della tabella
        main_layout.addWidget(self.customer_table)

        # Layout verticale per gli input
        input_layout = QVBoxLayout()
        self.customer_name_input = QLineEdit()
        self.customer_name_input.setPlaceholderText("Nome Cliente")
        input_layout.addWidget(self.customer_name_input)
        self.search_button = QPushButton("Cerca Cliente")
        self.new_button = QPushButton("Nuovo Cliente")
        self.search_button.clicked.connect(self.search_customer)
        self.new_button.clicked.connect(self.new_customer)
        input_layout.addWidget(self.search_button)
        input_layout.addWidget(self.new_button)
        input_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Aggiungi layout principale
        main_layout.addLayout(input_layout)

        # Aggiungi il layout finale alla finestra
        layout.addLayout(main_layout)
        self.setLayout(layout)

    def on_customer_click(self, row, column):
        customer_name = self.customer_table.item(row, column).text()
        self.customer_name_input.setText(customer_name)

    def resizeEvent(self, event):
        self.image_label.setGeometry(0, 0, self.width(), self.height())

    def search_customer(self):
        customer_name = self.customer_name_input.text().strip()
        if customer_name:
            try:
                data = load_customer_data(customer_name)
                if data is not None:
                    customer_page = self.parent().widget(2)
                    if customer_page:
                        customer_page.load_data(customer_name)
                        self.parent().setCurrentIndex(2)
                        self.customer_name_input.clear()
                    else:
                        QMessageBox.warning(self, "Errore", "Pagina cliente non disponibile.")
                else:
                    QMessageBox.warning(self, "Errore", f"Cliente '{customer_name}' non trovato.")
            except Exception as e:
                print("Errore", f"Errore durante la ricerca del cliente: {str(e)}")
        else:
            QMessageBox.warning(self, "Attenzione", "Inserisci il nome del cliente da cercare.")

    def new_customer(self):
        customer_name = self.customer_name_input.text().strip()
        if customer_name:
            if is_customer_name_unique(customer_name): 
                create_new_customer(customer_name)
                load_customers(self.customer_table)
                self.parent().widget(2).load_data(customer_name)
                self.parent().setCurrentIndex(2)
            else:
                QMessageBox.warning(self, "Attenzione", f"Il nome del cliente '{customer_name}' esiste già. Scegli un altro nome.")
        else:
            QMessageBox.warning(self, "Attenzione", "Inserisci il nome del cliente da creare.")

class DateDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def createEditor(self, parent, option, index):
        editor = QDateEdit(parent)
        editor.setCalendarPopup(True)
        editor.setDisplayFormat("dd-MM-yyyy")
        
        # Imposta lo stylesheet per il calendario
        editor.setStyleSheet("""
            QDateEdit {
                background-color: #FFFFFF;
                color: #000000;
            }
            QCalendarWidget {
                background-color: #FFFFFF;
                color: #000000;
            }
            QCalendarWidget QAbstractItemView {
                background-color: #FFFFFF;
                color: #000000;
            }
            QCalendarWidget QAbstractItemView::item {
                background-color: #FFFFFF;
                color: #000000;
            }
            QCalendarWidget QAbstractItemView::item:selected {
                background-color: #B0E0E6;
                color: #000000;
            }
            QCalendarWidget QAbstractItemView::item:hover {
                background-color: #D3D3D3;
            }
        """)
        
        return editor

    def setEditorData(self, editor, index):
        date_str = index.model().data(index, Qt.ItemDataRole.EditRole)
        if date_str:
            try:
                date = QDate.fromString(date_str, "dd-MM-yyyy")
                editor.setDate(date)
            except Exception:
                editor.setDate(QDate.currentDate())
        else:
            editor.setDate(QDate.currentDate())
    
    def setModelData(self, editor, model, index):
        model.setData(index, editor.date().toString("dd-MM-yyyy"), Qt.ItemDataRole.EditRole)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestionale Clienti")
        self.setGeometry(300, 100, 800, 600)

        # Imposta l'icona della finestra
        self.setWindowIcon(QIcon(resource_path("icon.ico")))

        # Creazione del widget centrale
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        # Creazione delle pagine
        self.login_page = LoginWindow()
        self.home_page = HomePage()
        self.customer_page = CustomerPage()
        self.settings_page = SettingsPage()

        # Aggiungi le pagine al QStackedWidget
        self.central_widget.addWidget(self.login_page)
        self.central_widget.addWidget(self.home_page)
        self.central_widget.addWidget(self.customer_page)
        self.central_widget.addWidget(self.settings_page)

        # Mostra la pagina di login all'avvio
        self.central_widget.setCurrentIndex(0)

        # Creazione della barra degli strumenti
        self.create_toolbar()

        # Applica il tema
        self.apply_theme()

    def create_toolbar(self):
        """ Crea la barra degli strumenti principale """
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Crea i bottoni per la toolbar
        self.home_button = QPushButton("Home")
        self.settings_button = QPushButton("Settings")
        self.info_button = QPushButton("Info")
        self.logout_button = QPushButton("Logout")
        
        # Collega i bottoni alle azioni
        self.home_button.clicked.connect(self.go_to_home)
        self.settings_button.clicked.connect(self.go_to_settings)
        self.info_button.clicked.connect(self.show_info)
        self.logout_button.clicked.connect(self.logout)
        
        # Aggiungi i bottoni alla barra degli strumenti
        toolbar_layout.addWidget(self.home_button)
        toolbar_layout.addWidget(self.settings_button)
        toolbar_layout.addWidget(self.info_button)
        toolbar_layout.addWidget(self.logout_button)
        
        toolbar.setLayout(toolbar_layout)
        self.setMenuWidget(toolbar)

        # Disabilita inizialmente i bottoni che devono essere visibili solo dopo il login
        self.logout_button.setVisible(False)
        self.home_button.setEnabled(False)
        self.settings_button.setVisible(True)

    def apply_theme(self):
        """Applica un tema chiaro con colori vivaci"""
        style_sheet = """
            QWidget {
                background-color: #F5F5F5;
                color: #333333;
                font-size: 14px;
            }
            QPushButton {
                background-color: #E0E0E0;
                color: #333333;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
            QLineEdit {
                background-color: #FFFFFF;
                color: #333333;
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                padding: 8px;
            }
            QLabel {
                color: #333333;
            }
            QWidget#toolbar {
                background-color: #E0E0E0;
                color: #333333;
            }
            QPushButton#toolbarButton {
                background-color: #E0E0E0;
                color: #333333;
            }
            QPushButton#toolbarButton:hover {
                background-color: #D0D0D0;
            }
        """
        self.setStyleSheet(style_sheet)

    def go_to_home(self):
        """ Torna alla pagina Home """
        self.central_widget.setCurrentIndex(1)

    def go_to_settings(self):
        """ Vai alla pagina delle impostazioni """
        self.central_widget.setCurrentIndex(3)

    def show_info(self):
        """ Mostra la finestra di dialogo con le informazioni """
        info_message = (
            "Created by Antonio Paolino\n" "Software Engineer\n" "For support, contact me at: apaolino96@gmail.com"
        )
        QMessageBox.information(self, "Info", info_message)

    def logout(self):
        """ Logout e torna alla pagina di login """
        self.central_widget.setCurrentIndex(0)
        # Disabilita i bottoni
        self.home_button.setEnabled(False)
        self.logout_button.setVisible(False)
        self.settings_button.setVisible(True)

    def enable_menu_actions(self):
        """ Abilita i bottoni dopo il login """
        self.home_button.setEnabled(True)
        self.logout_button.setVisible(True)
        self.settings_button.setVisible(False)

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_db_path()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Etichetta e campo di testo per il percorso del database
        layout.addWidget(QLabel("Percorso del file Access:"))
        self.path_input = QLineEdit()
        layout.addWidget(self.path_input)

        # Pulsante per cercare il file
        self.browse_button = QPushButton("Cerca...")
        self.browse_button.clicked.connect(self.browse_file)
        layout.addWidget(self.browse_button)

        # Pulsante per salvare le impostazioni
        self.save_button = QPushButton("Salva")
        self.save_button.clicked.connect(self.save_db_path)
        layout.addWidget(self.save_button)

        # Pulsante per tornare indietro
        self.back_button = QPushButton("Indietro")
        self.back_button.clicked.connect(self.go_back)
        layout.addWidget(self.back_button)

        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)
        
    def save_db_path(self):
        new_path = self.path_input.text()
        try:
            with open(CONFIG_FILE, 'w') as file:
                file.write(new_path.strip())
                print(f"Percorso salvato: {new_path.strip()}")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio del percorso del file: {str(e)}")

    def load_db_path(self):
        """ Carica il percorso del file di database dal file di configurazione """
        global db_path
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as file:
                    db_path = file.read().strip()
                    if not db_path:
                        raise ValueError("Il file di configurazione è vuoto.")
                    print(f"Percorso caricato: {db_path}")
                    self.path_input.setText(db_path)
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore durante il caricamento del percorso del file: {str(e)}")
        else:
            QMessageBox.warning(self, "Attenzione", "File di configurazione non trovato.")

    def browse_file(self):
        """ Permette all'utente di selezionare un file SQLite """
        file_dialog = QFileDialog(self, "Seleziona File SQLite", "", "SQLite Database (*.sqlite)")
        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            self.path_input.setText(selected_file)

    def go_back(self):
        """ Torna alla pagina di login """
        self.parent().setCurrentIndex(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
