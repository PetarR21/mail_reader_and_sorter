import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QDesktopWidget,
    QWidget,
    QVBoxLayout,
    QLabel,
    QTabWidget,
)
from PyQt5.QtCore import Qt


def create_tab(self, label_text):
    widget = QWidget()
    layout = QVBoxLayout()
    label = QLabel(label_text)
    layout.addWidget(label)
    widget.setLayout(layout)

    return widget


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

        tab = QTabWidget()

        tab.addTab(create_tab(self, "Dashboard"), "dashboard")
        tab.addTab(create_tab(self, "Addresses"), "addresses")
        tab.addTab(create_tab(self, "Prefernces"), "preferences")
        tab.addTab(create_tab(self, "Settings"), "settings")

        layout.addWidget(tab)
        central_widget.setLayout(layout)
        # Center the window
        geometry = self.frameGeometry()
        center = QDesktopWidget().availableGeometry().center()
        geometry.moveCenter(center)
        self.move(geometry.topLeft())


def main():
    app = QApplication(sys.argv)
    window = MailSorterApp()

    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
