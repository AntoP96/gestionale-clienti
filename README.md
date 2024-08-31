# Customer Management System

**Customer Management System** is a client management application developed in Python using PyQt5 and sqlite3. The application allows you to manage client data through a graphical user interface and a sqlite database.

## Requirements

- Python 3.x
- PyQt6
- pyodbc
- sqlite3

## Installation

1. **Clone the repository**:

    ```bash
    git clone https://github.com/AntoP96/gestionale-clienti
    ```

2. **Navigate to the project directory**:

    ```bash
    cd gestionale-clienti
    ```

3. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

    Make sure you have the sqlite3 installed on your system.

4. **Configure the `config.txt` file**:

    Edit the `config.txt` file to specify the path to your sqlite database. Example content:

    ```
    C:\path\to\your\database.sqlite
    ```

## Usage

1. **Run the application**:

    Execute the main Python file `gestioneClienti.py`:

    ```bash
    python gestioneClienti.py
    ```

2. **User Interface**:

    - **Login**: Enter the username and password to access the application.
    - **Home Page**: Search for an existing client or create a new one.
    - **Customer Page**: View and edit the selected client’s data.

3. **Building the application (optional)**:

    If you want to create a standalone executable, you can use PyInstaller:

    ```bash
    python -m PyInstaller --name "Gestione Clienti" --onefile gestioneClienti.py
    ```

    Modify the `.spec` file to include external files if necessary, then run (as shown in the `gestioneClienti.spec` file).

    Build the complete application:

    ```bash
    python -m PyInstaller "gestioneClienti.spec"
    ```

## Contributions

Contributions are welcome! If you have suggestions or improvements, feel free to open a pull request or report an issue.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For support or questions, contact me at: [apaolino96@gmail.com](mailto:apaolino96@gmail.com)
