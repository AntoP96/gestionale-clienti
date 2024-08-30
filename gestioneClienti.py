import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import pyodbc
from datetime import datetime
import os

def resource_path(relative_path):
    """ Get the absolute path to a resource, works for dev and for PyInstaller """
    if getattr(sys, 'frozen', False):  # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

# File di configurazione dove salvare il percorso del database Access
CONFIG_FILE = resource_path("config.txt")

# Connessione al database Access
def connect_db():
    try:
        conn_str = f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};'
        return pyodbc.connect(conn_str)
    except pyodbc.Error as e:
        QMessageBox.critical(None, "Errore di Connessione", f"Errore durante la connessione al database: {str(e)}")
        return None

# Funzione per caricare i dati di un cliente
def load_customer_data(customer_name):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        query = f"SELECT * FROM [{customer_name}]"
        cursor.execute(query)
        data = cursor.fetchall()
        conn.close()
        
        formatted_data = []
        for row in data:
            formatted_row = list(row)
            if isinstance(row[1], datetime):
                formatted_row[1] = row[1].strftime("%Y-%m-%d")
            formatted_data.append(formatted_row)
        
        return formatted_data
    except Exception as e:
        conn.close()
        # QMessageBox.critical(None, "Errore", f"Impossibile trovare il cliente: {customer_name}.")
        return None

def save_customer_data(customer_name, data, deleted_row_ids):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Ottieni gli ID esistenti per evitare conflitti e duplicati
        cursor.execute(f"SELECT ID FROM [{customer_name}]")
        existing_ids = {row[0] for row in cursor.fetchall()}

        # Costruisci l'elenco di ID da eliminare
        ids_to_delete = list(deleted_row_ids)  # Righe eliminate
        ids_to_delete.extend([row[0] for row in data if row[0] in existing_ids])

        # Rimuovi le righe esistenti che devono essere aggiornate o eliminate
        if ids_to_delete:
            ids_to_delete_str = ', '.join(map(str, ids_to_delete))
            cursor.execute(f"DELETE FROM [{customer_name}] WHERE ID IN ({ids_to_delete_str})")

        # Inserisci i nuovi dati
        for row in data:
            row_id = row[0]  # ID della riga
            date_value = row[1]
            if date_value:
                try:
                    date_value = datetime.strptime(date_value, "%Y-%m-%d")
                except ValueError:
                    date_value = None
            numero_fattura_value = row[2] if row[2] else None
            dare_value = float(row[3]) if row[3] else 0.0
            avere_value = float(row[4]) if row[4] else 0.0
            totale_value = float(row[5]) if row[5] else 0.0
            note_value = row[6] if row[6] else None

            if row_id:  # Se l'ID esiste, esegui un aggiornamento
                query = f"""
                    UPDATE [{customer_name}]
                    SET [DATA] = ?, [NUMERO FATTURA] = ?, [DARE] = ?, [AVERE] = ?, [TOTALE] = ?, [NOTE] = ?
                    WHERE ID = ?
                """
                cursor.execute(query, (date_value, numero_fattura_value, dare_value, avere_value, totale_value, note_value, row_id))
            else:  # Altrimenti, inserisci una nuova riga
                query = f"""
                    INSERT INTO [{customer_name}] 
                    ([DATA], [NUMERO FATTURA], [DARE], [AVERE], [TOTALE], [NOTE])  
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                cursor.execute(query, (date_value, numero_fattura_value, dare_value, avere_value, totale_value, note_value))

        # Commetti le modifiche
        conn.commit()
    except Exception as e:
        print(f"Errore durante l'inserimento dei dati: {e}")
    finally:
        QMessageBox.information(None, "Successo", f"Dati del cliente {customer_name} salvati con successo.")
        conn.close()

# Funzione per verificare se il nome del cliente è unico
def is_customer_name_unique(customer_name):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Prova a eseguire una query sulla tabella specifica
        cursor.execute(f"SELECT 1 FROM [{customer_name}] WHERE 1=0")
        conn.close()
        return False  # La tabella esiste già
    except pyodbc.Error:
        conn.close()
        return True  # La tabella non esiste, quindi il nome è unico

# Funzione per creare una nuova tabella cliente
def create_new_customer(customer_name):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        query = f"""
        CREATE TABLE [{customer_name}] (
            ID AUTOINCREMENT PRIMARY KEY,
            [DATA] DATE,
            [NUMERO FATTURA] TEXT(50),
            [DARE] CURRENCY,
            [AVERE] CURRENCY,
            [TOTALE] CURRENCY,
            [NOTE] TEXT(255)
        )
        """
        cursor.execute(query)
        conn.commit()
        conn.close()
        QMessageBox.information(None, "Successo", f"Tabella per {customer_name} creata con successo.")
    except Exception as e:
        print(str(e))
        # QMessageBox.critical(None, "Errore", f"Impossibile creare la tabella per {customer_name}: {str(e)}")

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
        self.password_input.setEchoMode(QLineEdit.Password)
        input_layout.addWidget(self.password_input)
        self.login_button = QPushButton("Accedi")
        self.login_button.clicked.connect(self.check_login)
        input_layout.addWidget(self.login_button)
        input_layout.setAlignment(Qt.AlignCenter)

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
        self.table = QTableWidget(0, 7)  # 6 colonne
        headers = ["ID", "DATA", "NUMERO FATTURA", "DARE", "AVERE", "TOTALE", "NOTE"]
        self.table.setHorizontalHeaderLabels(headers)

        # Nascondi la colonna ID (colonna 0)
        self.table.setColumnHidden(0, True)

        # Imposta il font in grassetto per le intestazioni
        header_font = QFont()
        header_font.setBold(True)
        header_view = self.table.horizontalHeader()
        header_view.setStyleSheet("font-weight: bold;")  # Imposta il font in grassetto usando lo stylesheet

        # Allarga la colonna "NUMERO FATTURA"
        self.table.setColumnWidth(2, 150)

        # Estende l'ultima sezione per riempire la larghezza della tabella
        header_view.setStretchLastSection(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # Applicazione del delegate alla colonna della data
        self.date_delegate = DateDelegate(self.table)
        self.table.setItemDelegateForColumn(1, self.date_delegate)

        layout.addWidget(self.table)

        # Riga dei totali
        total_layout = QHBoxLayout()

        self.total_label = QLabel("TOTALE")
        self.total_label.setFont(header_font)

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
        total_layout.addWidget(self.total_label)
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
        self.apply_dark_theme()  # Applica il tema scuro

        # Connetti le modifiche della tabella ai calcoli totali
        self.table.itemChanged.connect(self.on_item_changed)

        # Imposta i validatori per le colonne Dare e Avere
        self.dare_validator = QDoubleValidator(0.0, 1e6, 2)
        self.avere_validator = QDoubleValidator(0.0, 1e6, 2)

    def apply_dark_theme(self):
        # Applica il tema scuro alla tabella
        table_style = """
            QTableWidget {
                background-color: #333;
                color: #fff;
            }
            QHeaderView::section {
                background-color: #444;
                color: #fff;
                padding: 4px;
                border: 1px solid #555;
            }
            QTableWidget::item {
                border: 1px solid #555;
            }
        """
        self.table.setStyleSheet(table_style)

    def load_data(self, customer_name):
        self.customer_name = customer_name
        data = load_customer_data(customer_name)
        if data is not None:
            self.table.setRowCount(0)  # Pulisce la tabella
            for row_data in data:
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                for col_index, cell_data in enumerate(row_data):  # Include ID here
                    item_text = str(cell_data) if cell_data is not None else ""
                    item = QTableWidgetItem(item_text)
                    
                    if col_index == 0:  # ID column
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    elif col_index in [3, 4, 5]:  # DARE and AVERE columns
                        item.setText(self.format_number(float(cell_data)) if cell_data else "0.00")
                    if col_index == 5:  # TOTALE column
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    
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
        
        save_customer_data(customer_name, data, self.deleted_row_ids)
        
        # Pulisci la lista degli ID eliminati
        self.deleted_row_ids.clear()

    def on_item_changed(self, item):
        if item.column() in [3, 4]:  # Colonne Dare e Avere
            item.setText(self.format_number(float(item.text())) if item.text() else "0.00")
            self.calculate_row_total(item.row())
            self.calculate_totals()

    def calculate_row_total(self, row):
        dare_item = self.table.item(row, 3)
        avere_item = self.table.item(row, 4)
        
        dare_value = float(dare_item.text()) if dare_item and dare_item.text() else 0
        avere_value = float(avere_item.text()) if avere_item and avere_item.text() else 0
        totale_value = round(dare_value - avere_value, 2)

        totale_item = QTableWidgetItem(self.format_number(totale_value))
        totale_item.setFlags(totale_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, 5, totale_item)

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

        menu.exec_(self.table.viewport().mapToGlobal(pos))

    def add_row_above(self):
        current_row = self.table.currentRow()
        self.table.insertRow(current_row)
        self.set_current_row(current_row)

    def add_row_below(self):
        current_row = self.table.currentRow()
        self.table.insertRow(current_row + 1)
        self.set_current_row(current_row + 1)

    def delete_row(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            item_id = self.table.item(current_row, 0)
            if item_id:
                self.deleted_row_ids.add(item_id.text())  # Aggiungi questa riga
            self.table.removeRow(current_row)
            self.calculate_totals()

    def set_current_row(self, row):
        self.table.setCurrentCell(row, 0)

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
        
        # Elementi dell'interfaccia utente
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
        input_layout.setAlignment(Qt.AlignCenter)  # Centra gli elementi

        container_widget = QWidget(self)
        container_widget.setLayout(input_layout)
        container_widget.setGeometry(10, self.height() - 150, self.width() - 20, 140)  # Posiziona il layout in basso
        layout.addWidget(container_widget)
        self.setLayout(layout)
    
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
                self.parent().widget(2).load_data(customer_name)
                self.parent().setCurrentIndex(2)
            else:
                QMessageBox.warning(self, "Attenzione", f"Il nome del cliente '{customer_name}' esiste già. Scegli un altro nome.")

class DateDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def createEditor(self, parent, option, index):
        editor = QDateEdit(parent)
        editor.setCalendarPopup(True)
        editor.setDisplayFormat("yyyy-MM-dd")
        return editor

    def setEditorData(self, editor, index):
        date_str = index.model().data(index, Qt.EditRole)
        if date_str:
            try:
                date = QDate.fromString(date_str, "yyyy-MM-dd")
                editor.setDate(date)
            except:
                editor.setDate(QDate.currentDate())
        else:
            editor.setDate(QDate.currentDate())
    
    def setModelData(self, editor, model, index):
        model.setData(index, editor.date().toString("yyyy-MM-dd"), Qt.EditRole)

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
        self.central_widget.addWidget(self.settings_page)  # Aggiungi la pagina delle impostazioni

        # Mostra la pagina di login all'avvio
        self.central_widget.setCurrentIndex(0)

        # Menu principale
        self.create_menu()

        # Applicazione del tema scuro
        self.apply_dark_theme()
        

    def create_menu(self):
        """ Crea la barra di menu principale """
        menu_bar = self.menuBar()

        # Menu principale
        self.home_action = QAction("Home", self)
        self.home_action.triggered.connect(self.go_to_home)
        menu_bar.addAction(self.home_action)
        
        self.settings_action = QAction("Settings", self)
        self.settings_action.triggered.connect(self.go_to_settings)
        menu_bar.addAction(self.settings_action)
        
        self.info_action = QAction("Info", self)
        self.info_action.triggered.connect(self.show_info)
        menu_bar.addAction(self.info_action)
        
        self.logout_action = QAction("Logout", self)
        self.logout_action.triggered.connect(self.logout)
        menu_bar.addAction(self.logout_action)

        # Disabilita inizialmente le azioni che devono essere visibili solo dopo il login
        self.logout_action.setVisible(False)
        self.home_action.setEnabled(False)
        self.settings_action.setVisible(True)

    def apply_dark_theme(self):
        """ Applica un tema scuro con colori più vivaci """
        dark_style_sheet = """
            QWidget {
                background-color: #2E2E2E;
                color: #E0E0E0;
                font-size: 14px;
            }
            QPushButton {
                background-color: #3D3D3D;
                color: #FFFFFF;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #4A4A4A;
            }
            QLineEdit {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 8px;
            }
            QLabel {
                color: #E0E0E0;
            }
            QMenuBar {
                background-color: #3C3C3C;
                color: #E0E0E0;
            }
            QMenuBar::item {
                background-color: #3C3C3C;
                color: #E0E0E0;
            }
            QMenuBar::item::selected {
                background-color: #4A4A4A;
            }
            QTableWidget {
                background-color: #2E2E2E;
                color: #E0E0E0;
            }
            QTableWidget::item {
                border: 1px solid #555555;
            }
            QHeaderView::section {
                background-color: #3C3C3C;
                color: #E0E0E0;
                padding: 4px;
                border: 1px solid #555555;
            }
        """
        self.setStyleSheet(dark_style_sheet)

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
        # Disabilita le azioni del menu
        self.home_action.setEnabled(False)
        self.logout_action.setVisible(False)
        self.settings_action.setVisible(True)

    def enable_menu_actions(self):
        """ Abilita le azioni del menu dopo il login """
        self.home_action.setEnabled(True)
        self.logout_action.setVisible(True)
        self.settings_action.setVisible(False)

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

        layout.setAlignment(Qt.AlignCenter)

        self.setLayout(layout)
        
    def save_db_path(self):
        global db_path
        new_path = self.path_input.text()
        try:
            with open(CONFIG_FILE, 'w') as file:
                file.write(new_path.strip())
                print(f"Percorso salvato: {new_path.strip()}")
        except Exception as e:
            QMessageBox.critical(None, "Errore", f"Errore durante il salvataggio del percorso del file: {str(e)}")

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
                QMessageBox.critical(None, "Errore", f"Errore durante il caricamento del percorso del file: {str(e)}")
        else:
            QMessageBox.warning(None, "Attenzione", "File di configurazione non trovato.")

    def browse_file(self):
        """ Permette all'utente di selezionare un nuovo file Access """
        file_dialog = QFileDialog(self, "Seleziona File Access", "", "Access Database (*.accdb)")
        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            self.path_.setText(selected_file)

    def go_back(self):
        """ Torna alla pagina di login """
        self.parent().setCurrentIndex(0)

    def browse_file(self):
        """ Permette all'utente di selezionare un nuovo file Access """
        file_dialog = QFileDialog(self, "Seleziona File Access", "", "Access Database (*.accdb)")
        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            self.path_input.setText(selected_file)

    def go_back(self):
        """ Torna alla pagina di login """
        self.parent().setCurrentIndex(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())