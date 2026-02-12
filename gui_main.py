import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QDesktopWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QComboBox,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCursor
import json


class MailSorterApp(QMainWindow):

    def __init__(self):
        super().__init__()

        # Set window title and size
        self.setWindowTitle("Mail Sorter App")
        self.setGeometry(0, 0, 900, 700)

        self.setup_styles()

        # Create widgets and layouts
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # Read required files
        self.read_addresses()
        self.read_keywords()

        # Create navigation tabs
        layout.addWidget(self.create_navigation_tabs())

        central_widget.setLayout(layout)
        # Center the window
        geometry = self.frameGeometry()
        center = QDesktopWidget().availableGeometry().center()
        geometry.moveCenter(center)
        self.move(geometry.topLeft())

    def setup_styles(self):
        self.message_styles = {
            "error": """
                background-color: #f8d7da;
                color: #721c24;
                padding: 12px 15px;
                border: 1px solid #f5c6cb;
                border-radius: 4px;
                font-size: 14px;
            """,
            "success": """
                background-color: #d4edda;
                color: #155724;
                padding: 12px 15px;
                border: 1px solid #c3e6cb;
                border-radius: 4px;
                font-size: 14px;
            """,
        }

        self.input_style = """
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:hover {
                border: 1px solid #80bdff;
                background-color: #f8f9fa;
            }
            QLineEdit:focus {
                border: 1px solid #007bff;
            }
        """

        self.title_style = """
            font-size: 18px;
            font-weight: bold;
            color:#505050;
            margin-bottom: 10px;
            margin-top: 10px;
        """

        self.add_button_style = """
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
                outline: none;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #003d82;
            }
            QPushButton:focus {
                outline: none;
            }
        """
        self.delete_button_style = """
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 12px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #003d82;
            }
        """

        self.table_style = """
            QTableWidget {
                border: 1px solid #dee2e6;
                background-color: white;
            }
            QTableWidget::item {
                color: #303030;
            }
            QHeaderView::section {
                background-color: #838383;
                color: white;
                padding: 6px;
                border: none;
                font-weight: bold;
                font-size: 16px;
            }
            
        """

        self.tab_style = """
            QTabBar::tab {
                color: #212529;
                padding: 4px 12px;
                border: none;
                font-size: 14px;
                min-width: 120px;
                height: 20px;
            }
            QTabBar::tab:selected {
                color: #007bff;                          
                border-bottom: 3px solid #007bff;        
                background-color: white;
            }
            QTabBar::tab:hover:!selected {
                color: #0056b3;                          
            }
        """

    def create_navigation_tabs(self):
        tab = QTabWidget()

        tab.setStyleSheet(self.tab_style)

        tab.addTab(self.create_tab("Dashboard"), "Dashboard")
        tab.addTab(self.create_addresses_tab(), "Addresses")
        tab.addTab(self.create_preferences_tab(), "Preferences")
        tab.addTab(self.create_tab("Settings"), "Settings")

        return tab

    def create_preferences_tab(self):

        widget = QWidget()
        layout = QVBoxLayout()

        title = QLabel("Add new keyword")
        title.setStyleSheet(self.title_style)

        self.email_dropdown = QComboBox()
        self.populate_email_dropdown()
        self.email_dropdown.setCurrentIndex(-1)

        input_layout = QHBoxLayout()
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("Enter new keyword")
        self.keyword_input.setStyleSheet(self.input_style)
        self.keyword_input.setCursor(QCursor(Qt.IBeamCursor))
        self.add_keyword_button = QPushButton("Add")
        self.add_keyword_button.clicked.connect(self.on_add_keyword_button_clicked)
        self.add_keyword_button.setStyleSheet(self.add_button_style)
        self.add_keyword_button.setCursor(QCursor(Qt.PointingHandCursor))
        input_layout.addWidget(self.keyword_input)
        input_layout.addWidget(self.add_keyword_button)

        ## Message layout
        message_layout = QVBoxLayout()
        self.keywords_message_label = QLabel()
        self.keywords_message_label.setMinimumHeight(45)
        message_layout.addWidget(self.keywords_message_label)

        layout.addWidget(title)
        layout.addWidget(self.email_dropdown)
        layout.addLayout(input_layout)
        layout.addLayout(message_layout)
        layout.addStretch(stretch=1)
        widget.setLayout(layout)

        return widget

    def show_keywords_message(self, text, message_type=""):
        self.keywords_message_label.setStyleSheet(self.message_styles[message_type])

        self.keywords_message_label.setText(text)

        self.keywords_message_label = QTimer()
        self.keywords_message_label.setSingleShot(True)
        self.keywords_message_label.timeout.connect(self.clear_keywords_message)

    def clear_keywords_message(self):
        self.keywords_message_label.setText("")  # Empty the label
        self.keywords_message_label.setStyleSheet("")

    def on_add_keyword_button_clicked(self):
        print("Add button cliked")
        self.show_keywords_message("Hello", "success")

    def populate_email_dropdown(self):
        for email in self.tracked_addresses.keys():
            self.email_dropdown.addItem(email)

    def read_keywords(self):
        try:
            with open("keywords.json", "r") as f:
                self.tracked_keywords = json.load(f)
        except FileNotFoundError:
            self.show_message("Error: The file 'keywords.json' was not found.", "error")
        except json.JSONDecodeError:
            self.show_message(
                "Error: Failed to decode JSON from the file. Check for malformed JSON syntax.",
                "error",
            )

    def save_keywords(self):
        with open("keywords.json", "w") as f:
            json.dump(self.tracked_keywords, f)

    def create_addresses_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Input Selection Layout

        input_selection_layout = QVBoxLayout()
        title = QLabel("Add New Address")
        title.setStyleSheet(self.title_style)
        input_selection_horizontal = QHBoxLayout()
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter email address")
        self.email_input.setStyleSheet(self.input_style)
        self.email_input.setCursor(QCursor(Qt.IBeamCursor))
        self.email_input.focusInEvent = (
            lambda event: self.addresses_table.clearSelection()
        )
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Enter folder name")
        self.folder_input.setStyleSheet(self.input_style)
        self.folder_input.setCursor(QCursor(Qt.IBeamCursor))
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.on_add_button_clicked)
        self.add_button.setStyleSheet(self.add_button_style)
        self.add_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.email_input.focusInEvent = (
            lambda event: self.addresses_table.clearSelection()
        )

        input_selection_horizontal.addWidget(self.email_input)
        input_selection_horizontal.addWidget(self.folder_input)
        input_selection_horizontal.addWidget(self.add_button)

        input_selection_layout.addWidget(title)
        input_selection_layout.addLayout(input_selection_horizontal)
        input_selection_layout.setContentsMargins(0, 10, 0, 10)

        # Message layout
        message_layout = QVBoxLayout()
        self.message_label = QLabel()
        self.message_label.setMinimumHeight(45)
        message_layout.addWidget(self.message_label)

        # Table Layout
        tracked_layout = QVBoxLayout()
        tracked_title = QLabel("Tracked Addresses")
        tracked_title.setStyleSheet(self.title_style)
        tracked_layout.addWidget(tracked_title)

        self.addresses_table = QTableWidget()
        self.addresses_table.setMinimumHeight(300)  # Compact
        self.addresses_table.setMaximumHeight(400)
        self.addresses_table.setColumnCount(2)
        self.addresses_table.setHorizontalHeaderLabels(["Email Address", "Folder Name"])
        header = self.addresses_table.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { border: 1px solid #D3D3D3; }")
        self.addresses_table.verticalHeader().setVisible(False)
        self.addresses_table.setStyleSheet(self.table_style)
        self.addresses_table.setAlternatingRowColors(True)

        if self.tracked_addresses:
            for email, folder in self.tracked_addresses.items():
                self.addresses_table.insertRow(self.addresses_table.rowCount())

                self.addresses_table.setItem(
                    self.addresses_table.rowCount() - 1, 0, QTableWidgetItem(email)
                )
                self.addresses_table.setItem(
                    self.addresses_table.rowCount() - 1, 1, QTableWidgetItem(folder)
                )

        self.addresses_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.addresses_table.setSortingEnabled(True)
        self.addresses_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.addresses_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.addresses_table.setCursor(QCursor(Qt.PointingHandCursor))

        tracked_layout.addWidget(self.addresses_table)
        tracked_layout.setContentsMargins(0, 5, 0, 5)

        # Bottom Layout
        bottom_layout = QVBoxLayout()
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.on_delete_button_clicked)
        self.delete_button.setStyleSheet(self.delete_button_style)
        self.delete_button.setCursor(QCursor(Qt.PointingHandCursor))
        bottom_layout.addWidget(self.delete_button)

        layout.addLayout(input_selection_layout)
        layout.addLayout(message_layout)
        layout.addLayout(tracked_layout)
        layout.addLayout(bottom_layout)
        layout.addStretch()
        widget.setLayout(layout)

        return widget

    def on_delete_button_clicked(self):
        selection = self.addresses_table.selectionModel().selectedRows()
        for index in selection:
            row_number = index.row()
            email_to_delete = self.addresses_table.item(row_number, 0).text()
            del self.tracked_addresses[email_to_delete]
            self.save_addresses()
            self.addresses_table.removeRow(row_number)
            self.show_message(f"Deleted {email_to_delete}", "success")

    def read_addresses(self):
        try:
            with open("addresses.json", "r") as file:
                self.tracked_addresses = json.load(file)
        except FileNotFoundError:
            self.show_message("Error: The file 'data.json' was not found.", "error")
        except json.JSONDecodeError:
            self.show_message(
                "Error: Failed to decode JSON from the file. Check for malformed JSON syntax.",
                "error",
            )

    def save_addresses(self):
        try:
            with open("addresses.json", "w") as f:
                json.dump(self.tracked_addresses, f, indent=4)
        except FileNotFoundError:
            self.show_message(
                "Error: The file 'addresses.json' was not found.", "error"
            )
        except json.JSONDecodeError:
            self.show_message(
                "Error: Failed to decode JSON from the file. Check for malformed JSON syntax.",
                "error",
            )

    def on_add_button_clicked(self):
        email = self.email_input.text()
        folder = self.folder_input.text()

        is_valid_email = self.is_valid_email(email)
        is_valid_folder_name = self.is_valid_folder_name(folder)
        is_unique_email = self.is_unique_email(email)
        is_unique_folder_name = self.is_unique_folder_name(folder)

        if not is_valid_email or not is_valid_folder_name:
            self.show_message("Invalid email or folder name.", "error")
        if not is_unique_email or not is_unique_folder_name:
            self.show_message("Email and folder name must be unique.", "error")
        if (
            not is_valid_folder_name
            or not is_valid_email
            or not is_unique_email
            or not is_unique_folder_name
        ):
            return

        self.tracked_addresses[email] = folder

        self.save_addresses()

        self.addresses_table.insertRow(self.addresses_table.rowCount())
        self.addresses_table.setItem(
            self.addresses_table.rowCount() - 1, 0, QTableWidgetItem(email)
        )
        self.addresses_table.setItem(
            self.addresses_table.rowCount() - 1, 1, QTableWidgetItem(folder)
        )

        self.show_message(f"Added {email}", "success")

        self.email_input.clear()
        self.folder_input.clear()

    def is_valid_email(self, email):
        if email == "":
            return False
        """
        Check if email format is valid.
        Returns: True if valid, False if invalid
        """
        # Check if @ exists
        if "@" not in email:
            return False

        # Split by @ to get local and domain parts
        parts = email.split("@")

        # Check if there are exactly 2 parts (local@domain)
        if len(parts) != 2:
            return False

        local_part, domain = parts

        # Check if local part is not empty
        if len(local_part) == 0:
            return False

        # Check if domain is not empty and contains a dot
        if len(domain) == 0 or "." not in domain:
            return False

        return True

    def is_valid_folder_name(self, folder_name):
        """
        Check if folder name is valid.
        Returns: True if valid, False if invalid
        """
        # Check if empty
        if folder_name == "":
            return False

        # Check if too long (Windows limit)
        if len(folder_name) > 255:
            return False

        # Invalid characters for folder names on Windows
        invalid_chars = ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]

        for char in invalid_chars:
            if char in folder_name:
                return False

        return True

    def is_unique_email(self, email):
        return email not in self.tracked_addresses.keys()

    def is_unique_folder_name(self, folder):
        return folder not in self.tracked_addresses.values()

    def show_message(self, text, message_type=""):
        self.message_label.setStyleSheet(self.message_styles[message_type])

        self.message_label.setText(text)
        # self.message_label.setVisible(True)

        self.message_timer = QTimer()
        self.message_timer.setSingleShot(True)
        self.message_timer.timeout.connect(self.clear_message)
        self.message_timer.start(5000)

    def clear_message(self):
        self.message_label.setText("")  # Empty the label
        self.message_label.setStyleSheet("")

    def create_tab(self, label_text):
        widget = QWidget()
        layout = QVBoxLayout()
        label = QLabel(label_text)
        layout.addWidget(label)
        widget.setLayout(layout)

        return widget


def main():
    app = QApplication(sys.argv)
    window = MailSorterApp()

    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
