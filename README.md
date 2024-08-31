# Customer Management System

**Customer Management System** is a client management application developed in Python using PyQt5 and pyodbc. The application allows you to manage client data through a graphical user interface and a Microsoft Access database.

## Requirements

- Python 3.x
- PyQt6
- pyodbc
- Microsoft Access Driver (*.mdb, *.accdb)

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

    Make sure you have the Microsoft Access Driver installed on your system.

4. **Configure the `config.txt` file**:

    Edit the `config.txt` file to specify the path to your Access database. Example content:

    ```
    C:\path\to\your\database.accdb
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
    python -m PyInstaller --name "Customer Management System" --onefile gestioneClienti.py
    ```

    Modify the `.spec` file to include external files if necessary, then run (as shown in the `Customer Management System.spec.example` file).

    Build the complete application:

    ```bash
    python -m PyInstaller "Customer Management System.spec"
    ```

## Contributions

Contributions are welcome! If you have suggestions or improvements, feel free to open a pull request or report an issue.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For support or questions, contact me at: [apaolino96@gmail.com](mailto:apaolino96@gmail.com)
