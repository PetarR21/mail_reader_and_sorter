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
    QSizePolicy,
)
from PyQt5.QtCore import QTimer
import json


class MailSorterApp(QMainWindow):

    def __init__(self):
        super().__init__()

        # Set window title and size
        self.setWindowTitle("Mail Sorter App")
        self.setGeometry(0, 0, 800, 600)

        self.setup_styles()

        # Create widgets and layouts
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

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

        self.text_input_style = """
            padding: 8px 12px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            font-size: 14px;
            background-color: white;
        """

        self.title_style = """
            font-size: 16px;
            font-weight: bold;
            color: #212529;
            margin-bottom: 10px;
            margin-top: 10px;
        """

    def create_navigation_tabs(self):
        tab = QTabWidget()

        tab.addTab(self.create_tab("Dashboard"), "dashboard")
        tab.addTab(self.create_addresses_tab(), "addresses")
        tab.addTab(self.create_tab("Prefernces"), "preferences")
        tab.addTab(self.create_tab("Settings"), "settings")

        return tab

    def create_addresses_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Input Selection Layout
        self.read_addresses()

        input_selection_layout = QVBoxLayout()
        title = QLabel("ADD NEW ADDRESS")
        title.setStyleSheet(self.title_style)
        input_selection_horizontal = QHBoxLayout()
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter email address")
        self.email_input.setStyleSheet(self.text_input_style)
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Enter folder name")
        self.folder_input.setStyleSheet(self.text_input_style)
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.on_add_button_clicked)

        input_selection_horizontal.addWidget(self.email_input)
        input_selection_horizontal.addWidget(self.folder_input)
        input_selection_horizontal.addWidget(self.add_button)

        input_selection_layout.addWidget(title)
        input_selection_layout.addLayout(input_selection_horizontal)

        # Message layout
        message_layout = QVBoxLayout()
        self.message_label = QLabel()
        self.message_label.setVisible(False)
        message_layout.addWidget(self.message_label)

        # Table Layout
        tracked_layout = QVBoxLayout()
        tracked_title = QLabel("TRACKED ADDRESSES")
        tracked_title.setStyleSheet(self.title_style)
        tracked_layout.addWidget(tracked_title)

        self.addresses_table = QTableWidget()
        self.addresses_table.setColumnCount(2)
        self.addresses_table.setHorizontalHeaderLabels(["Email Address", "Folder Name"])

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

        tracked_layout.addWidget(self.addresses_table)

        # Bottom Layout
        bottom_layout = QVBoxLayout()
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.on_delete_button_clicked)
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
        self.message_label.setVisible(True)

        self.message_timer = QTimer()
        self.message_timer.setSingleShot(True)
        self.message_timer.timeout.connect(self.clear_message)
        self.message_timer.start(5000)

    def clear_message(self):
        self.message_label.setText("")  # Empty the label
        self.message_label.setStyleSheet("")
        self.message_label.setVisible(False)

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
