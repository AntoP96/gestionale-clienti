import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class DatabaseViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Database Viewer")
        self.root.geometry("600x400")

        self.conn = None
        self.cursor = None

        self.create_widgets()

    def create_widgets(self):
        # Frame per la selezione del database e delle tabelle
        frame_controls = tk.Frame(self.root)
        frame_controls.pack(fill=tk.X, padx=10, pady=5)

        self.open_button = tk.Button(frame_controls, text="Apri Database", command=self.open_database)
        self.open_button.pack(side=tk.LEFT, padx=5)

        # Frame per la selezione delle tabelle
        frame_select = tk.Frame(self.root)
        frame_select.pack(fill=tk.X, padx=10, pady=5)

        self.table_listbox = tk.Listbox(frame_select, width=40, height=15)
        self.table_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_y = tk.Scrollbar(frame_select, orient=tk.VERTICAL, command=self.table_listbox.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.table_listbox.config(yscrollcommand=scroll_y.set)

        self.table_listbox.bind('<<ListboxSelect>>', self.on_table_select)

        # Frame per i dati della tabella
        frame_data = tk.Frame(self.root)
        frame_data.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)

        self.data_text = tk.Text(frame_data, wrap=tk.NONE)
        self.data_text.pack(fill=tk.BOTH, expand=True)

    def open_database(self):
        # Apri una finestra di dialogo per selezionare il file del database
        file_path = filedialog.askopenfilename(
            title="Seleziona il file SQLite",
            filetypes=[("SQLite files", "*.sqlite"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.conn = sqlite3.connect(file_path)
                self.cursor = self.conn.cursor()
                self.load_tables()
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", str(e))
        else:
            messagebox.showinfo("Info", "Nessun file selezionato. L'applicazione si chiuderà.")
            self.root.quit()

    def load_tables(self):
        if not self.cursor:
            return
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = self.cursor.fetchall()
            self.table_listbox.delete(0, tk.END)
            for table in tables:
                self.table_listbox.insert(tk.END, table[0])
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))

    def on_table_select(self, event):
        selected_table = self.table_listbox.get(tk.ACTIVE)
        if not selected_table:
            return
        
        self.load_table_data(selected_table)

    def load_table_data(self, table_name):
        if not self.cursor:
            return
        
        try:
            self.cursor.execute(f"SELECT * FROM '{table_name}'")
            rows = self.cursor.fetchall()

            self.data_text.delete(1.0, tk.END)
            if rows:
                column_names = [description[0] for description in self.cursor.description]
                self.data_text.insert(tk.END, '\t'.join(column_names) + '\n')
                for row in rows:
                    self.data_text.insert(tk.END, '\t'.join(map(str, row)) + '\n')
            else:
                self.data_text.insert(tk.END, "No data found.")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))

    def __del__(self):
        if self.conn:
            self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = DatabaseViewer(root)
    root.mainloop()
