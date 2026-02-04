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
)
from PyQt5.QtCore import Qt


class MailSorterApp(QMainWindow):

    def __init__(self):
        super().__init__()

        # Set window title and size
        self.setWindowTitle("Mail Sorter App")
        self.setGeometry(0, 0, 800, 600)

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
        input_selection_layout = QVBoxLayout()
        title = QLabel("ADD NEW ADDRESS")
        input_selection_horizontal = QHBoxLayout()
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter email address")
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Enter folder name")
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.on_add_button_clicked)

        input_selection_horizontal.addWidget(self.email_input)
        input_selection_horizontal.addWidget(self.folder_input)
        input_selection_horizontal.addWidget(self.add_button)

        input_selection_layout.addWidget(title)
        input_selection_layout.addLayout(input_selection_horizontal)

        # Tabel Layout
        tracked_layout = QVBoxLayout()
        tracked_title = QLabel("TRACKED ADDRESSES")
        tracked_layout.addWidget(tracked_title)

        layout.addLayout(input_selection_layout)
        layout.addLayout(tracked_layout)
        layout.addStretch()
        widget.setLayout(layout)

        return widget

    def on_add_button_clicked(self):
        email = self.email_input.text()
        folder = self.folder_input.text()

        is_valid_email = self.is_valid_email(email)
        is_valid_folder_name = self.is_valid_folder_name(folder)

        if not is_valid_email:
            print("Invalid email")
        if not is_valid_folder_name:
            print("Invalid folder name")
        if not is_valid_folder_name or not is_valid_email:
            return

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
