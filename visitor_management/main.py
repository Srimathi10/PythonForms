from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QGridLayout, \
    QLineEdit, QPushButton, QMainWindow, QTableWidget, QTableWidgetItem, QDialog, \
    QVBoxLayout, QComboBox, QToolBar, QStatusBar, QMessageBox
from PyQt6.QtGui import QAction, QIcon
import sys
import sqlite3


class DatabaseConnection:
    def __init__(self, database_file="visitor_db.db"):
        self.database_file = database_file

    def connect(self):
        connection = sqlite3.connect(self.database_file)
        return connection

    def create_table(self):
        connection = self.connect()
        cursor = connection.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company TEXT NOT NULL,
            contact TEXT NOT NULL
        );
        """)
        connection.commit()
        cursor.close()
        connection.close()



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visitor Management System")
        self.setMinimumSize(800, 600)

        # Create the database table if it doesn't exist
        DatabaseConnection().create_table()

        file_menu_item = self.menuBar().addMenu("&File")
        help_menu_item = self.menuBar().addMenu("&Help")
        edit_menu_item = self.menuBar().addMenu("&Edit")

        add_visitor_action = QAction(QIcon("icons/add.png"), "Add Visitor", self)
        add_visitor_action.triggered.connect(self.insert)
        file_menu_item.addAction(add_visitor_action)

        about_action = QAction("About", self)
        help_menu_item.addAction(about_action)
        about_action.setMenuRole(QAction.MenuRole.NoRole)
        about_action.triggered.connect(self.about)

        search_action = QAction(QIcon("icons/search.png"), "Search", self)
        edit_menu_item.addAction(search_action)
        search_action.triggered.connect(self.search)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(("Id", "Visitor Name", "Company", "Contact"))
        self.table.verticalHeader().setVisible(False)
        self.setCentralWidget(self.table)

        # Create toolbar and add toolbar elements
        toolbar = QToolBar()
        toolbar.setMovable(True)
        self.addToolBar(toolbar)

        toolbar.addAction(add_visitor_action)
        toolbar.addAction(search_action)

        # Create status bar and add status bar elements
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        # Detect a cell click
        self.table.cellClicked.connect(self.cell_clicked)

    def cell_clicked(self):
        edit_button = QPushButton("Edit Record")
        edit_button.clicked.connect(self.edit)

        delete_button = QPushButton("Delete Record")
        delete_button.clicked.connect(self.delete)

        children = self.findChildren(QPushButton)
        if children:
            for child in children:
                self.statusbar.removeWidget(child)

        self.statusbar.addWidget(edit_button)
        self.statusbar.addWidget(delete_button)

    def load_data(self):
        connection = DatabaseConnection().connect()
        result = connection.execute("SELECT * FROM visitors")
        self.table.setRowCount(0)
        for row_number, row_data in enumerate(result):
            self.table.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.table.setItem(row_number, column_number, QTableWidgetItem(str(data)))
        connection.close()

    def insert(self):
        dialog = InsertDialog()
        dialog.exec()

    def search(self):
        dialog = SearchDialog()
        dialog.exec()

    def edit(self):
        dialog = EditDialog()
        dialog.exec()

    def delete(self):
        dialog = DeleteDialog()
        dialog.exec()

    def about(self):
        dialog = AboutDialog()
        dialog.exec()


class AboutDialog(QMessageBox):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("About")
        content = """
        This app is developed to manage visitor information in a building or organization.
        Feel free to modify and reuse this app.
        """
        self.setText(content)


class EditDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Update Visitor Data")
        self.setFixedWidth(300)
        self.setFixedHeight(300)

        layout = QVBoxLayout()
        # Get visitor name from selected row
        index = main_window.table.currentRow()
        visitor_name = main_window.table.item(index, 1).text()

        # Get id from selected row
        self.visitor_id = main_window.table.item(index, 0).text()

        # Add visitor name widget
        self.visitor_name = QLineEdit(visitor_name)
        self.visitor_name.setPlaceholderText("Name")
        layout.addWidget(self.visitor_name)

        # Add company name widget
        company_name = main_window.table.item(index, 2).text()
        self.company_name = QLineEdit(company_name)
        self.company_name.setPlaceholderText("Company")
        layout.addWidget(self.company_name)

        # Add contact number widget
        contact_number = main_window.table.item(index, 3).text()
        self.contact_number = QLineEdit(contact_number)
        self.contact_number.setPlaceholderText("Contact Number")
        layout.addWidget(self.contact_number)

        # Add a submit button
        button = QPushButton("Update")
        button.clicked.connect(self.update_visitor)
        layout.addWidget(button)

        self.setLayout(layout)

    def update_visitor(self):
        connection = DatabaseConnection().connect()
        cursor = connection.cursor()
        cursor.execute("UPDATE visitors SET name = ?, company = ?, contact = ? WHERE id = ?",
                       (self.visitor_name.text(),
                        self.company_name.text(),
                        self.contact_number.text(),
                        self.visitor_id))
        connection.commit()
        cursor.close()
        connection.close()

        # Refresh the table
        main_window.load_data()


class DeleteDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Delete Visitor Data")

        layout = QGridLayout()
        confirmation = QLabel("Are you sure you want to delete this visitor?")
        yes = QPushButton("Yes")
        no = QPushButton("No")

        layout.addWidget(confirmation, 0, 0, 1, 2)
        layout.addWidget(yes, 1, 0)
        layout.addWidget(no, 1, 1)
        self.setLayout(layout)

        yes.clicked.connect(self.delete_visitor)

    def delete_visitor(self):
        # Get selected row index and visitor id
        index = main_window.table.currentRow()
        visitor_id = main_window.table.item(index, 0).text()

        connection = sqlite3.connect("visitor_db.db")
        cursor = connection.cursor()
        cursor.execute("DELETE from visitors WHERE id = ?", (visitor_id,))
        connection.commit()
        cursor.close()
        connection.close()
        main_window.load_data()

        self.close()

        confirmation_widget = QMessageBox()
        confirmation_widget.setWindowTitle("Success")
        confirmation_widget.setText("The visitor record was deleted successfully!")
        confirmation_widget.exec()


class InsertDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Insert Visitor Data")
        self.setFixedWidth(300)
        self.setFixedHeight(300)

        layout = QVBoxLayout()

        # Add visitor name widget
        self.visitor_name = QLineEdit()
        self.visitor_name.setPlaceholderText("Visitor Name")
        layout.addWidget(self.visitor_name)

        # Add company name widget
        self.company_name = QLineEdit()
        self.company_name.setPlaceholderText("Company Name")
        layout.addWidget(self.company_name)

        # Add contact number widget
        self.contact_number = QLineEdit()
        self.contact_number.setPlaceholderText("Contact Number")
        layout.addWidget(self.contact_number)

        # Add a submit button
        button = QPushButton("Register Visitor")
        button.clicked.connect(self.add_visitor)
        layout.addWidget(button)

        self.setLayout(layout)

    def add_visitor(self):
        name = self.visitor_name.text()
        company = self.company_name.text()
        contact = self.contact_number.text()
        connection = DatabaseConnection().connect()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO visitors (name, company, contact) VALUES (?, ?, ?)",
                       (name, company, contact))
        connection.commit()
        cursor.close()
        connection.close()
        main_window.load_data()


class SearchDialog(QDialog):
    def __init__(self):
        super().__init__()
        # Set window title and size
        self.setWindowTitle("Search Visitor")
        self.setFixedWidth(300)
        self.setFixedHeight(300)

        # Create layout and input widget
        layout = QVBoxLayout()
        self.visitor_name = QLineEdit()
        self.visitor_name.setPlaceholderText("Visitor Name")
        layout.addWidget(self.visitor_name)

        # Create button
        button = QPushButton("Search")
        button.clicked.connect(self.search)
        layout.addWidget(button)

        self.setLayout(layout)

    def search(self):
        name = self.visitor_name.text()
        connection = DatabaseConnection().connect()
        cursor = connection.cursor()
        result = cursor.execute("SELECT * FROM visitors WHERE name = ?", (name,))
        rows = list(result)
        items = main_window.table.findItems(name, Qt.MatchFlag.MatchFixedString)
        for item in items:
            main_window.table.item(item.row(), 1).setSelected(True)

        cursor.close()
        connection.close()


app = QApplication(sys.argv)
main_window = MainWindow()
main_window.show()
main_window.load_data()
sys.exit(app.exec())
