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
    QFrame,
)
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QCursor
import json


class MailSorterApp(QMainWindow):

    def __init__(self):
        super().__init__()

        # Set window title and size
        self.setWindowTitle("Mail Sorter App")
        self.setGeometry(0, 0, 900, 700)

        self.setup_styles()

        self.normal_table_min_height = 300
        self.normal_table_max_height = 400
        self.expanded_table_min_height = 420
        self.expanded_table_max_height = 700

        # Create widgets and layouts
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        self.tracked_addresses = {}
        self.tracked_keywords = {}

        self.message_label = None
        self.keywords_message_label = None

        # Read required files
        self.read_addresses()
        self.read_keywords()

        # Create navigation tabs
        layout.addWidget(self.create_navigation_tabs())
        self.update_table_heights()

        central_widget.setLayout(layout)
        # Center the window
        geometry = self.frameGeometry()
        center = QDesktopWidget().availableGeometry().center()
        geometry.moveCenter(center)
        self.move(geometry.topLeft())

    def is_expanded_window(self):
        return self.isFullScreen() or self.isMaximized()

    def update_table_heights(self):
        if self.is_expanded_window():
            min_height = self.expanded_table_min_height
            max_height = self.expanded_table_max_height
        else:
            min_height = self.normal_table_min_height
            max_height = self.normal_table_max_height

        for table_name in ("keywords_table", "addresses_table"):
            table = getattr(self, table_name, None)
            if table is not None:
                table.setMinimumHeight(min_height)
                table.setMaximumHeight(max_height)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.WindowStateChange:
            self.update_table_heights()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_table_heights()

    def setup_styles(self):
        self.message_styles = {
            "error": """
                background-color: #fdeaea;
                color: #7a2e2e;
                padding: 12px 15px;
                border: 1px solid #f4c8c8;
                border-radius: 4px;
                font-size: 15px;
                font-weight: 500;
            """,
            "success": """
                background-color: #e7f6ed;
                color: #1f5a34;
                padding: 12px 15px;
                border: 1px solid #c9e9d3;
                border-radius: 4px;
                font-size: 15px;
                font-weight: 500;
            """,
        }

        self.input_style = """
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #c6d8ee;
                border-radius: 4px;
                font-size: 15px;
                background-color: white;
                color: #1f2a37;
            }
            QLineEdit:hover {
                border: 1px solid #8fb6e8;
                background-color: #f6faff;
            }
            QLineEdit:focus {
                border: 1px solid #2f80ed;
            }
        """

        self.title_style = """
            font-size: 20px;
            font-weight: 700;
            color:#2f4858;
            margin-bottom: 10px;
            margin-top: 10px;
        """

        self.add_button_style = """
            QPushButton {
                background-color: #2f80ed;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-weight: 600;
                font-size: 15px;
                outline: none;
            }
            QPushButton:hover {
                background-color: #1f6ed4;
            }
            QPushButton:pressed {
                background-color: #195bb0;
            }
            QPushButton:focus {
                outline: none;
            }
        """
        self.delete_button_style = """
            QPushButton {
                background-color: #2f80ed;
                color: white;
                padding: 12px 20px;
                border: none;
                border-radius: 4px;
                font-weight: 600;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #1f6ed4;
            }
            QPushButton:pressed {
                background-color: #195bb0;
            }
        """

        self.combo_style = """
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #c6d8ee;
                border-radius: 4px;
                font-size: 15px;
                background-color: white;
                color: #1f2a37;
            }
            QComboBox:hover {
                border: 1px solid #8fb6e8;
            }
            QComboBox:focus {
                border: 1px solid #2f80ed;
            }
            QComboBox::drop-down {
                border: none;
                width: 28px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #dbe7f6;
                selection-background-color: #dcecff;
                selection-color: #1f2a37;
                font-size: 14px;
            }
        """

        self.pref_card_style = """
            QWidget#prefCard,
            QWidget#addrCard {
                background-color: #f8fbff;
                border: 1px solid #dbe7f6;
                border-radius: 8px;
            }
        """

        self.dashboard_style = """
            QWidget#dashHeader,
            QWidget#quickActionsCard,
            QFrame#activityCard,
            QFrame#kpiCard {
                background-color: #f8fbff;
                border: 1px solid #dbe7f6;
                border-radius: 8px;
            }
            QLabel#dashboardSubtitle {
                color: #5f7992;
                font-size: 14px;
                font-weight: 500;
            }
            QLabel#kpiTitle {
                color: #5f7992;
                font-size: 13px;
                font-weight: 600;
            }
            QLabel#kpiValue {
                color: #1f2a37;
                font-size: 24px;
                font-weight: 700;
            }
            QLabel#activityText {
                color: #344054;
                font-size: 14px;
                font-weight: 500;
            }
        """

        self.preferences_table_style = """
            QTableWidget {
                border: 1px solid #dbe7f6;
                border-radius: 8px;
                background-color: white;
                gridline-color: #edf3fb;
                outline: none;
            }
            QTableWidget::item {
                color: #1f2a37;
                font-size: 15px;
                font-weight: 500;
            }
            QTableWidget::item:focus {
                outline: none;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #dcecff;
                color: #1f2a37;
            }
            QHeaderView::section {
                background-color: #5f7992;
                color: white;
                padding: 8px;
                border: none;
                font-weight: 700;
                font-size: 17px;
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
                color: #374151;
                padding: 6px 12px;
                border: none;
                outline: none;
                font-size: 15px;
                font-weight: 600;
                min-width: 120px;
                height: 28px;
            }
            QTabBar::tab:focus {
                outline: none;
                border: none;
            }
            QTabBar::tab:selected {
                color: #2f80ed;                          
                border-bottom: 3px solid #2f80ed;        
                background-color: white;
            }
            QTabBar::tab:hover:!selected {
                color: #374151;
            }
        """

    def create_navigation_tabs(self):
        tab = QTabWidget()

        tab.setStyleSheet(self.tab_style)
        tab.setFocusPolicy(Qt.NoFocus)
        tab.tabBar().setFocusPolicy(Qt.NoFocus)
        tab.tabBar().setCursor(QCursor(Qt.ArrowCursor))

        tab.addTab(self.create_dashboard_tab(), "Dashboard")
        tab.addTab(self.create_addresses_tab(), "Addresses")
        tab.addTab(self.create_preferences_tab(), "Preferences")
        tab.addTab(self.create_tab("Settings"), "Settings")

        return tab

    def create_dashboard_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        widget.setStyleSheet(self.dashboard_style)

        # Title and subtitle
        top_card = QWidget()
        top_card.setObjectName("dashHeader")
        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(14, 14, 14, 14)
        title_layout.setSpacing(4)
        title = QLabel("Dashboard")
        title.setStyleSheet(self.title_style)
        subtitle = QLabel("Quick overview of your mail sorting status")
        subtitle.setObjectName("dashboardSubtitle")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        top_card.setLayout(title_layout)

        # KPI
        kpi_card = QWidget()
        kpi_layout = QHBoxLayout()
        kpi_layout.setContentsMargins(0, 0, 0, 0)
        kpi_layout.setSpacing(10)

        tracked_addresses_card = QFrame()
        tracked_addresses_card.setObjectName("kpiCard")
        tracked_addresses_card.setMinimumHeight(115)
        hlayout1 = QVBoxLayout()
        hlayout1.setContentsMargins(14, 12, 14, 12)
        hlayout1.setSpacing(6)
        title1 = QLabel("Tracked Addresses")
        title1.setObjectName("kpiTitle")
        self.tracked_addresses_value = QLabel("0")
        self.tracked_addresses_value.setObjectName("kpiValue")
        hlayout1.addWidget(title1)
        hlayout1.addWidget(self.tracked_addresses_value)
        hlayout1.addStretch()
        tracked_addresses_card.setLayout(hlayout1)

        tracked_keywords_card = QFrame()
        tracked_keywords_card.setObjectName("kpiCard")
        tracked_keywords_card.setMinimumHeight(115)
        hlayout2 = QVBoxLayout()
        hlayout2.setContentsMargins(14, 12, 14, 12)
        hlayout2.setSpacing(6)
        title2 = QLabel("Tracked Keywords")
        title2.setObjectName("kpiTitle")
        self.tracked_keywords_value = QLabel("0")
        self.tracked_keywords_value.setObjectName("kpiValue")
        hlayout2.addWidget(title2)
        hlayout2.addWidget(self.tracked_keywords_value)
        hlayout2.addStretch()
        tracked_keywords_card.setLayout(hlayout2)

        last_run_card = QFrame()
        last_run_card.setObjectName("kpiCard")
        last_run_card.setMinimumHeight(115)
        hlayout3 = QVBoxLayout()
        hlayout3.setContentsMargins(14, 12, 14, 12)
        hlayout3.setSpacing(6)
        title3 = QLabel("Last Run")
        title3.setObjectName("kpiTitle")
        self.last_run_value = QLabel("XX.XX.XXXX 00:00")
        self.last_run_value.setObjectName("kpiValue")
        hlayout3.addWidget(title3)
        hlayout3.addWidget(self.last_run_value)
        hlayout3.addStretch()
        last_run_card.setLayout(hlayout3)

        emails_processed_card = QFrame()
        emails_processed_card.setObjectName("kpiCard")
        emails_processed_card.setMinimumHeight(115)
        hlayout4 = QVBoxLayout()
        hlayout4.setContentsMargins(14, 12, 14, 12)
        hlayout4.setSpacing(6)
        title4 = QLabel("Emails Processed:")
        title4.setObjectName("kpiTitle")
        self.emails_processed_value = QLabel("0")
        self.emails_processed_value.setObjectName("kpiValue")
        hlayout4.addWidget(title4)
        hlayout4.addWidget(self.emails_processed_value)
        hlayout4.addStretch()
        emails_processed_card.setLayout(hlayout4)

        kpi_layout.addWidget(tracked_addresses_card, 1)
        kpi_layout.addWidget(tracked_keywords_card, 1)
        kpi_layout.addWidget(last_run_card, 1)
        kpi_layout.addWidget(emails_processed_card, 1)
        kpi_card.setLayout(kpi_layout)

        self.refresh_dashboard_metrics()

        # Activity panel (Step 4)
        activity_card = QFrame()
        activity_card.setObjectName("activityCard")
        activity_layout = QVBoxLayout()
        activity_layout.setContentsMargins(14, 14, 14, 14)
        activity_layout.setSpacing(10)

        activity_title = QLabel("Recent Activity")
        activity_title.setStyleSheet(self.title_style)
        activity_text = QLabel(
            "• No recent activity yet\n" "• Last action: --\n" "• Status: waiting"
        )
        activity_text.setObjectName("activityText")
        activity_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        activity_layout.addWidget(activity_title)
        activity_layout.addWidget(activity_text)
        activity_layout.addStretch(1)
        activity_card.setLayout(activity_layout)
        activity_card.setMinimumHeight(260)

        # Quick actions (Step 5)
        quick_actions_card = QWidget()
        quick_actions_card.setObjectName("quickActionsCard")
        quick_actions_layout = QHBoxLayout()
        quick_actions_layout.setContentsMargins(14, 14, 14, 14)
        quick_actions_layout.setSpacing(10)

        self.run_sorting_button = QPushButton("Run mail sorting now")
        self.run_sorting_button.setStyleSheet(self.add_button_style)
        self.run_sorting_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.run_sorting_button.clicked.connect(self.on_run_sorting_clicked)

        self.refresh_dashboard_button = QPushButton("Refresh dashboard data")
        self.refresh_dashboard_button.setStyleSheet(self.add_button_style)
        self.refresh_dashboard_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.refresh_dashboard_button.clicked.connect(self.refresh_dashboard_metrics)

        quick_actions_layout.addWidget(self.run_sorting_button)
        quick_actions_layout.addWidget(self.refresh_dashboard_button)
        quick_actions_card.setLayout(quick_actions_layout)

        layout.addWidget(top_card)
        layout.addWidget(kpi_card)
        layout.addWidget(activity_card, 1)
        layout.addWidget(quick_actions_card)
        layout.addStretch(1)
        widget.setLayout(layout)

        return widget

    def on_run_sorting_clicked(self):
        print("Hello")

    def refresh_dashboard_metrics(self):
        metrics = self.get_dashboard_metrics()

        self.tracked_addresses_value.setText(str(metrics[0]))
        self.tracked_keywords_value.setText(str(metrics[1]))
        self.last_run_value.setText(str(metrics[2]))
        self.emails_processed_value.setText(str(metrics[3]))

    def get_dashboard_metrics(self):
        number_of_tracked_addresses = len(self.tracked_addresses)
        number_of_tracked_keywords = 0
        for keywords in self.tracked_keywords.values():
            number_of_tracked_keywords += len(keywords)

        last_run = "--"
        emails_processed = "0"
        return [
            number_of_tracked_addresses,
            number_of_tracked_keywords,
            last_run,
            emails_processed,
        ]

    def create_preferences_tab(self):

        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        top_card = QWidget()
        top_card.setObjectName("prefCard")
        top_card.setStyleSheet(self.pref_card_style)
        top_card_layout = QVBoxLayout()
        top_card_layout.setContentsMargins(14, 14, 14, 14)
        top_card_layout.setSpacing(10)

        title = QLabel("Add new keyword")
        title.setStyleSheet(self.title_style)

        self.email_dropdown = QComboBox()
        self.email_dropdown.setStyleSheet(self.combo_style)
        self.populate_email_dropdown()
        self.email_dropdown.setCurrentIndex(-1)
        self.email_dropdown.setPlaceholderText("Select email address")
        self.email_dropdown.currentIndexChanged.connect(self.populate_keywords_table)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("Enter new keyword")
        self.keyword_input.setStyleSheet(self.input_style)
        self.keyword_input.setCursor(QCursor(Qt.IBeamCursor))
        self.add_keyword_button = QPushButton("Add")
        self.add_keyword_button.setMinimumWidth(90)
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

        top_card_layout.addWidget(title)
        top_card_layout.addWidget(self.email_dropdown)
        top_card_layout.addLayout(input_layout)
        top_card_layout.addLayout(message_layout)
        top_card.setLayout(top_card_layout)

        ## Keywords table
        self.keywords_table = QTableWidget()
        self.keywords_table.setMinimumHeight(self.normal_table_min_height)
        self.keywords_table.setMaximumHeight(self.normal_table_max_height)
        self.keywords_table.setColumnCount(1)
        self.keywords_table.setHorizontalHeaderLabels(["Tracked Keywords"])
        header = self.keywords_table.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { border: 1px solid #D3D3D3; }")
        self.keywords_table.verticalHeader().setDefaultSectionSize(40)
        self.keywords_table.verticalHeader().setVisible(False)
        self.keywords_table.setStyleSheet(self.preferences_table_style)
        self.keywords_table.setAlternatingRowColors(True)
        self.keywords_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.keywords_table.setSortingEnabled(True)
        self.keywords_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.keywords_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.keywords_table.setFocusPolicy(Qt.NoFocus)
        self.keywords_table.setCursor(QCursor(Qt.PointingHandCursor))

        # Delete keyword button
        self.delete_keyword_button = QPushButton("Delete Selected")
        self.delete_keyword_button.clicked.connect(
            self.on_delete_keyword_button_clicked
        )
        self.delete_keyword_button.setStyleSheet(self.delete_button_style)
        self.delete_keyword_button.setCursor(QCursor(Qt.PointingHandCursor))

        layout.addWidget(top_card)
        layout.addWidget(self.keywords_table)
        layout.addWidget(self.delete_keyword_button)
        layout.addStretch(stretch=1)
        widget.setLayout(layout)

        return widget

    def on_delete_keyword_button_clicked(self):
        selection = self.keywords_table.selectionModel().selectedRows()
        for index in selection:
            row_number = index.row()
            keyword_to_delete = self.keywords_table.item(row_number, 0).text()
            current_email = self.email_dropdown.currentText()
            self.tracked_keywords[current_email].remove(keyword_to_delete)
            self.save_keywords()
            self.keywords_table.removeRow(row_number)
            self.show_keywords_message(f"Deleted {keyword_to_delete}", "success")
            self.refresh_dashboard_metrics()

    def populate_keywords_table(self):
        self.keywords_table.clearContents()
        self.keywords_table.setRowCount(0)

        if self.email_dropdown.currentText() == "":
            return

        if self.email_dropdown.currentText() not in self.tracked_keywords.keys():
            return

        keywords = self.tracked_keywords[self.email_dropdown.currentText()]
        for keyword in keywords:
            self.add_keyword(keyword)

    def show_keywords_message(self, text, message_type=""):
        if self.keywords_message_label == None:
            return

        self.keywords_message_label.setStyleSheet(self.message_styles[message_type])

        self.keywords_message_label.setText(
            self.format_message_text(text, message_type)
        )

        self.keywords_message_timer = QTimer()
        self.keywords_message_timer.setSingleShot(True)
        self.keywords_message_timer.timeout.connect(self.clear_keywords_message)
        self.keywords_message_timer.start(5000)

    def clear_keywords_message(self):
        self.keywords_message_label.setText("")  # Empty the label
        self.keywords_message_label.setStyleSheet("")

    def add_keyword(self, keyword):
        self.keywords_table.insertRow(self.keywords_table.rowCount())
        item = QTableWidgetItem(keyword)
        item.setTextAlignment(Qt.AlignCenter)
        self.keywords_table.setItem(self.keywords_table.rowCount() - 1, 0, item)

    def on_add_keyword_button_clicked(self):
        new_keyword = self.keyword_input.text().lower()
        selected_email = self.email_dropdown.currentText()

        if self.email_dropdown.currentIndex() == -1:
            self.show_keywords_message("No email selected", "error")
            return
        if new_keyword == "":
            return

        if selected_email not in self.tracked_keywords.keys():
            self.tracked_keywords[selected_email] = []
            self.save_keywords()

        if new_keyword not in self.tracked_keywords[selected_email]:
            self.tracked_keywords[selected_email].append(new_keyword)
            self.show_keywords_message("Successfully added new keyword.", "success")
            self.save_keywords()
            self.keyword_input.clear()
            self.add_keyword(new_keyword)
            self.refresh_dashboard_metrics()
        else:
            self.show_keywords_message("Keyword already exists", "error")

    def populate_email_dropdown(self):
        self.email_dropdown.clear()
        self.email_dropdown.setCurrentIndex(-1)
        for email in self.tracked_addresses.keys():
            self.email_dropdown.addItem(email)

    def read_keywords(self):
        try:
            with open("keywords.json", "r") as f:
                self.tracked_keywords = json.load(f)
        except FileNotFoundError:
            self.show_message("Error: The file 'keywords.json' was not found.", "error")
            self.tracked_keywords = {}
            with open("keywords.json", "w") as f:
                json.dump({}, f)
        except json.JSONDecodeError:
            self.show_message(
                "Error: Failed to decode JSON from the file. Check for malformed JSON syntax.",
                "error",
            )
            self.tracked_keywords = {}

    def save_keywords(self):
        with open("keywords.json", "w") as f:
            json.dump(self.tracked_keywords, f)

    def create_addresses_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Input Selection Layout
        top_card = QWidget()
        top_card.setObjectName("addrCard")
        top_card.setStyleSheet(self.pref_card_style)
        top_card_layout = QVBoxLayout()
        top_card_layout.setContentsMargins(14, 14, 14, 14)
        top_card_layout.setSpacing(10)

        input_selection_layout = QVBoxLayout()
        title = QLabel("Add New Address")
        title.setStyleSheet(self.title_style)
        input_selection_horizontal = QHBoxLayout()
        input_selection_horizontal.setSpacing(8)
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
        self.add_button.setMinimumWidth(90)
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
        top_card_layout.addLayout(input_selection_layout)
        top_card_layout.addLayout(message_layout)
        top_card.setLayout(top_card_layout)

        # Table Layout
        tracked_layout = QVBoxLayout()
        tracked_title = QLabel("Tracked Addresses")
        tracked_title.setStyleSheet(self.title_style)
        tracked_layout.addWidget(tracked_title)

        self.addresses_table = QTableWidget()
        self.addresses_table.setMinimumHeight(self.normal_table_min_height)
        self.addresses_table.setMaximumHeight(self.normal_table_max_height)
        self.addresses_table.setColumnCount(2)
        self.addresses_table.setHorizontalHeaderLabels(["Email Address", "Folder Name"])
        header = self.addresses_table.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { border: 1px solid #D3D3D3; }")
        self.addresses_table.verticalHeader().setDefaultSectionSize(40)
        self.addresses_table.verticalHeader().setVisible(False)
        self.addresses_table.setStyleSheet(self.preferences_table_style)
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
        self.addresses_table.setFocusPolicy(Qt.NoFocus)
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

        layout.addWidget(top_card)
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
            self.populate_email_dropdown()
            self.refresh_dashboard_metrics()

    def read_addresses(self):
        try:
            with open("addresses.json", "r") as file:
                self.tracked_addresses = json.load(file)
        except FileNotFoundError:
            self.show_message(
                "Error: The file 'addresses.json' was not found.", "error"
            )
            self.tracked_addresses = {}
            with open("addresses.json", "w") as f:
                json.dump({}, f)
        except json.JSONDecodeError:
            self.show_message(
                "Error: Failed to decode JSON from the file. Check for malformed JSON syntax.",
                "error",
            )
            self.tracked_addresses = {}

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
        self.populate_email_dropdown()
        self.refresh_dashboard_metrics()

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
        if self.message_label is None:
            return

        self.message_label.setStyleSheet(self.message_styles[message_type])

        self.message_label.setText(self.format_message_text(text, message_type))
        # self.message_label.setVisible(True)

        self.message_timer = QTimer()
        self.message_timer.setSingleShot(True)
        self.message_timer.timeout.connect(self.clear_message)
        self.message_timer.start(5000)

    def clear_message(self):
        self.message_label.setText("")  # Empty the label
        self.message_label.setStyleSheet("")

    def format_message_text(self, text, message_type):
        icons = {
            "success": "✅",
            "error": "❌",
        }
        icon = icons.get(message_type, "")
        if icon:
            return f"{icon}  {text}"
        return text

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
