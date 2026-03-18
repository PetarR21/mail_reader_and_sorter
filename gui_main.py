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
    QFileDialog,
    QComboBox,
    QFrame,
    QListWidget,
    QListWidgetItem,
    QCheckBox,
    QSpinBox,
)
from PyQt5.QtCore import Qt, QTimer, QEvent, QThread, QObject, pyqtSignal
from PyQt5.QtGui import QCursor, QIcon, QPixmap
import json
from sort_emails import process_mails
import os
import shutil
import ctypes
from collections import deque
from datetime import datetime
from app_paths import (
    get_data_file,
    get_resource_file,
    set_active_profile,
    get_active_profile,
    list_profiles,
)
from email_api_setup import get_gmail_service


def SETTINGS_FILE():
    return get_data_file("settings.json")


def RUN_HISTORY_FILE():
    return get_data_file("run_history.json")


def STATS_FILE():
    return get_data_file("stats.json")


def KEYWORDS_FILE():
    return get_data_file("keywords.json")


def ADDRESSES_FILE():
    return get_data_file("addresses.json")


def TOKEN_FILE():
    return get_data_file("token.json")


def HISTORY_FILE():
    return get_data_file("history_id.txt")


APP_ICON_FILE = get_resource_file(os.path.join("logos", "mail_app_logo_2.png"))


class MailSortWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def run(self):
        try:
            result = process_mails()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class AuthWorker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def run(self):
        try:
            # This triggers OAuth if token is missing/invalid
            get_gmail_service()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class MailSorterApp(QMainWindow):
    def has_token(self):
        return os.path.isfile(TOKEN_FILE()) and os.path.getsize(TOKEN_FILE()) > 0

    def has_credentials(self):
        creds_file = get_data_file("credentials.json")
        return os.path.isfile(creds_file) and os.path.getsize(creds_file) > 0

    def show_main_ui(self):
        if not self.has_credentials():
            self.show_auth_ui()
            if hasattr(self, "auth_status_label"):
                self.auth_status_label.setText(
                    "❌ credentials.json is missing. Please select it before continuing."
                )
            return

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

    def show_auth_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("authRoot")
        central_widget.setStyleSheet(self.auth_style)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        card = QFrame()
        card.setObjectName("authCard")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(10)

        title = QLabel("Authentication Required")
        title.setStyleSheet(self.title_style)

        info = QLabel(
            "Login is required before using the app.\n"
            "Google OAuth setup must be valid in Google Cloud Console."
        )
        info.setObjectName("authSubtitle")
        info.setWordWrap(True)

        hint = QLabel(
            "Setup checklist:\n"
            "• Select your credentials.json file below\n"
            "• Gmail API must be enabled in Google Cloud Console\n"
            "• OAuth consent screen/test users must be configured"
        )
        hint.setObjectName("authHint")
        hint.setWordWrap(True)

        creds_label = QLabel("Credentials file")
        creds_label.setObjectName("authSubtitle")
        creds_layout = QHBoxLayout()
        self.auth_creds_path_label = QLineEdit()
        self.auth_creds_path_label.setReadOnly(True)
        self.auth_creds_path_label.setStyleSheet(self.input_style)
        self.auth_creds_path_label.setPlaceholderText("No credentials.json selected")
        creds_file = get_data_file("credentials.json")
        if os.path.isfile(creds_file):
            self.auth_creds_path_label.setText(creds_file)
        self.auth_browse_creds_button = QPushButton("Browse")
        self.auth_browse_creds_button.setStyleSheet(self.add_button_style)
        self.auth_browse_creds_button.clicked.connect(
            self.on_auth_browse_credentials_clicked
        )
        creds_layout.addWidget(self.auth_creds_path_label, 1)
        creds_layout.addWidget(self.auth_browse_creds_button)

        self.auth_status_label = QLabel("")
        self.auth_status_label.setObjectName("authStatus")
        self.auth_start_button = QPushButton("Start Google Login")
        self.auth_start_button.setStyleSheet(self.add_button_style)
        self.auth_start_button.setMinimumHeight(46)
        self.auth_start_button.setMaximumWidth(260)
        self.auth_start_button.clicked.connect(self.on_start_auth_clicked)

        has_creds = os.path.isfile(get_data_file("credentials.json"))
        self.auth_start_button.setEnabled(has_creds)
        if has_creds:
            self.auth_status_label.setText(
                "✅ credentials.json found. Press 'Start Google Login' to continue."
            )
        else:
            self.auth_status_label.setText(
                "Select your credentials.json file to continue."
            )

        card_layout.addWidget(title)
        card_layout.addWidget(info)
        card_layout.addWidget(hint)
        card_layout.addWidget(creds_label)
        card_layout.addLayout(creds_layout)
        card_layout.addWidget(self.auth_status_label)
        card_layout.addWidget(self.auth_start_button)
        card.setLayout(card_layout)

        layout.addWidget(card)
        layout.addStretch()

        central_widget.setLayout(layout)

    def import_credentials_file(self, source_path):
        dest = get_data_file("credentials.json")
        try:
            shutil.copy2(source_path, dest)
            return True, dest
        except Exception as e:
            return False, str(e)

    def on_auth_browse_credentials_clicked(self):
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Select credentials.json",
            "",
            "JSON Files (*.json);;All Files (*)",
        )
        if not selected:
            return

        ok, result = self.import_credentials_file(selected)
        if ok:
            self.auth_creds_path_label.setText(result)
            self.auth_start_button.setEnabled(True)
            self.auth_status_label.setText(
                "✅ credentials.json imported. Press 'Start Google Login' to continue."
            )
        else:
            self.auth_status_label.setText(f"❌ Failed to import credentials: {result}")

    def on_start_auth_clicked(self):
        if self.auth_thread is not None:
            return

        self.auth_start_button.setEnabled(False)
        self.auth_status_label.setText("Opening Google login...")

        self.auth_thread = QThread()
        self.auth_worker = AuthWorker()
        self.auth_worker.moveToThread(self.auth_thread)

        self.auth_thread.started.connect(self.auth_worker.run)
        self.auth_worker.finished.connect(self.on_auth_success)
        self.auth_worker.error.connect(self.on_auth_failed)

        self.auth_worker.finished.connect(self.auth_thread.quit)
        self.auth_worker.error.connect(self.auth_thread.quit)
        self.auth_thread.finished.connect(self.cleanup_auth_thread)

        self.auth_thread.start()

    def on_auth_success(self):
        if hasattr(self, "auth_status_label"):
            self.auth_status_label.setText("✅ Login successful. Loading app...")
        self.show_main_ui()

    def on_auth_failed(self, message):
        if hasattr(self, "auth_status_label"):
            self.auth_status_label.setText(
                "❌ Authentication failed. Check credentials.json and Google Cloud OAuth setup.\n"
                f"Details: {message}"
            )
        if hasattr(self, "auth_start_button"):
            self.auth_start_button.setEnabled(True)

    def cleanup_auth_thread(self):
        self.auth_worker = None
        self.auth_thread = None

    def __init__(self):
        self.is_sorting_running = False
        self.sort_thread = None
        self.sort_worker = None
        self.auth_thread = None
        self.auth_worker = None

        super().__init__()

        self.auto_sort_enabled = False
        self.auto_sort_interval_minutes = 10
        self.root_base_path = os.path.join(
            os.path.join(os.environ["USERPROFILE"]), "Desktop"
        )
        self.root_folder_name = "Main"
        self.auto_sort_timer = QTimer(self)
        self.auto_sort_timer.timeout.connect(self.on_auto_sort_timeout)

        # Set window title and size
        self.setWindowTitle("Mail Sorter")
        self.setGeometry(0, 0, 1100, 820)
        if os.path.isfile(APP_ICON_FILE):
            self.setWindowIcon(QIcon(APP_ICON_FILE))

        self.setup_styles()

        self.normal_table_min_height = 300
        self.normal_table_max_height = 400
        self.expanded_table_min_height = 420
        self.expanded_table_max_height = 700

        # Always start with profile selection
        self.show_profile_ui()

    def activate_profile(self, profile_name):
        """Set the active profile and proceed to auth/main."""
        set_active_profile(profile_name)
        self.setWindowTitle(f"Mail Sorter — {profile_name}")

        self.read_run_history()
        self.read_settings()
        self.apply_auto_sort_state()

        if self.has_token() and self.has_credentials():
            self.show_main_ui()
        else:
            self.show_auth_ui()

    def show_profile_ui(self):
        """Show the profile selection / creation screen."""
        self.stop_auto_sort_timer()

        central_widget = QWidget()
        central_widget.setObjectName("authRoot")
        central_widget.setStyleSheet(self.auth_style)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        card = QFrame()
        card.setObjectName("authCard")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(10)

        title = QLabel("Select Profile")
        title.setStyleSheet(self.title_style)

        subtitle = QLabel(
            "Each profile has its own credentials, addresses and settings."
        )
        subtitle.setObjectName("authSubtitle")
        subtitle.setWordWrap(True)

        # Existing profiles list
        self.profile_list = QListWidget()
        self.profile_list.setObjectName("activityList")
        self.profile_list.setMinimumHeight(180)
        self.profile_list.setMaximumHeight(320)
        self.profile_list.setSpacing(4)

        profiles = list_profiles()
        for p in profiles:
            self.profile_list.addItem(QListWidgetItem(p))

        if profiles:
            self.profile_list.setCurrentRow(0)

        self.profile_list.itemDoubleClicked.connect(self.on_profile_selected)

        select_button = QPushButton("Open Profile")
        select_button.setStyleSheet(self.add_button_style)
        select_button.setMinimumHeight(44)
        select_button.setMaximumWidth(260)
        select_button.clicked.connect(self.on_profile_selected)

        # New profile creation
        new_label = QLabel("Or create a new profile")
        new_label.setObjectName("authSubtitle")
        new_layout = QHBoxLayout()
        self.new_profile_input = QLineEdit()
        self.new_profile_input.setPlaceholderText("Profile name")
        self.new_profile_input.setStyleSheet(self.input_style)
        create_button = QPushButton("Create")
        create_button.setStyleSheet(self.add_button_style)
        create_button.clicked.connect(self.on_create_profile_clicked)
        new_layout.addWidget(self.new_profile_input, 1)
        new_layout.addWidget(create_button)

        self.profile_status_label = QLabel("")
        self.profile_status_label.setObjectName("authStatus")

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(self.profile_list)
        card_layout.addWidget(select_button)
        card_layout.addWidget(new_label)
        card_layout.addLayout(new_layout)
        card_layout.addWidget(self.profile_status_label)

        card.setLayout(card_layout)
        layout.addWidget(card)
        layout.addStretch()
        central_widget.setLayout(layout)

    def on_profile_selected(self, item=None):
        if item and isinstance(item, QListWidgetItem):
            profile_name = item.text()
        else:
            current = self.profile_list.currentItem()
            if not current:
                self.profile_status_label.setText("❌ No profile selected.")
                return
            profile_name = current.text()

        self.activate_profile(profile_name)

    def on_create_profile_clicked(self):
        name = self.new_profile_input.text().strip()
        if not name:
            self.profile_status_label.setText("❌ Profile name cannot be empty.")
            return

        invalid_chars = ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]
        for c in invalid_chars:
            if c in name:
                self.profile_status_label.setText(
                    '❌ Invalid name. Avoid: \\ / : * ? " < > |'
                )
                return

        existing = [p.lower() for p in list_profiles()]
        if name.lower() in existing:
            self.profile_status_label.setText(
                "❌ A profile with that name already exists."
            )
            return

        self.activate_profile(name)

    def save_settings(self):
        try:
            with open(SETTINGS_FILE(), "w") as f:
                settings = {}
                settings["auto_sort_enabled"] = self.auto_sort_enabled
                settings["auto_sort_interval_minutes"] = self.auto_sort_interval_minutes
                settings["root_base_path"] = self.root_base_path
                settings["root_folder_name"] = self.root_folder_name
                json.dump(settings, f)
        except OSError:
            with open(SETTINGS_FILE(), "w") as f:
                json.dump(
                    {
                        "auto_sort_enabled": False,
                        "auto_sort_interval_minutes": 10,
                        "root_base_path": os.path.join(
                            os.path.join(os.environ["USERPROFILE"]), "Desktop"
                        ),
                        "root_folder_name": "Main",
                    },
                    f,
                    indent=4,
                )

    def read_settings(self):
        if not os.path.isfile(SETTINGS_FILE()):
            with open(SETTINGS_FILE(), "w") as f:
                json.dump(
                    {
                        "auto_sort_enabled": False,
                        "auto_sort_interval_minutes": 10,
                        "root_base_path": os.path.join(
                            os.path.join(os.environ["USERPROFILE"]), "Desktop"
                        ),
                        "root_folder_name": "Main",
                    },
                    f,
                    indent=4,
                )
            return

        try:
            with open(SETTINGS_FILE(), "r") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("settings.json must contain a JSON dictionary")

                auto_sort_enabled = data.get("auto_sort_enabled", None)
                if isinstance(auto_sort_enabled, bool):
                    self.auto_sort_enabled = auto_sort_enabled

                auto_sort_interval_minutes = data.get(
                    "auto_sort_interval_minutes", None
                )

                if auto_sort_interval_minutes is not None:
                    try:
                        interval_value = int(auto_sort_interval_minutes)
                    except (TypeError, ValueError):
                        interval_value = None

                    if interval_value is not None and 1 <= interval_value <= 1440:
                        self.auto_sort_interval_minutes = interval_value

                root_base_path = data.get("root_base_path", None)
                if isinstance(root_base_path, str) and root_base_path.strip():
                    self.root_base_path = root_base_path.strip()

                root_folder_name = data.get("root_folder_name", None)
                if (
                    isinstance(root_folder_name, str)
                    and root_folder_name.strip()
                    and self.is_valid_folder_name(root_folder_name.strip())
                ):
                    self.root_folder_name = root_folder_name.strip()

        except (json.JSONDecodeError, ValueError, FileNotFoundError):
            self.auto_sort_enabled = False
            self.auto_sort_interval_minutes = 10
            self.root_base_path = os.path.join(
                os.path.join(os.environ["USERPROFILE"]), "Desktop"
            )
            self.root_folder_name = "Main"
            with open(SETTINGS_FILE(), "w") as f:
                json.dump(
                    {
                        "auto_sort_enabled": self.auto_sort_enabled,
                        "auto_sort_interval_minutes": self.auto_sort_interval_minutes,
                        "root_base_path": self.root_base_path,
                        "root_folder_name": self.root_folder_name,
                    },
                    f,
                    indent=4,
                )

    def on_auto_sort_timeout(self):
        if self.is_sorting_running:
            return
        self.on_run_sorting_clicked()

    def start_auto_sort_timer(self):
        self.auto_sort_timer.start(self.auto_sort_interval_minutes * 60 * 1000)

    def stop_auto_sort_timer(self):
        self.auto_sort_timer.stop()

    def apply_auto_sort_state(self):
        if self.auto_sort_enabled:
            self.start_auto_sort_timer()
        else:
            self.stop_auto_sort_timer()

    def read_run_history(self):
        self.ensure_run_history_file()

        try:
            with open(RUN_HISTORY_FILE(), "r") as f:
                data = json.load(f)
                self.run_history = deque(data if isinstance(data, list) else [])
        except (json.JSONDecodeError, FileNotFoundError):
            self.run_history = deque([])
            with open(RUN_HISTORY_FILE(), "w") as f:
                json.dump([], f, indent=4)

    def ensure_run_history_file(self):
        if not os.path.isfile(RUN_HISTORY_FILE()):
            with open(RUN_HISTORY_FILE(), "w") as f:
                json.dump([], f, indent=4)
            return

        try:
            with open(RUN_HISTORY_FILE(), "r") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError("run_history.json must contain a JSON list")
        except (json.JSONDecodeError, ValueError, FileNotFoundError):
            with open(RUN_HISTORY_FILE(), "w") as f:
                json.dump([], f, indent=4)

    def is_expanded_window(self):
        return self.isFullScreen() or self.isMaximized()

    def refresh_activity_list(self):
        self.activity_list.clear()

        for entry in self.run_history:
            status = entry.get("status", "")
            ts = entry.get("timestamp", "")
            sender = entry.get("from_email", "")
            filename = entry.get("attachment_name", "")
            folder = entry.get("folder_path", "")
            err = entry.get("error", "")

            if status == "saved":
                text = f'{ts} - ✅ Saved "{filename}" from {sender} -> {folder}'
            elif status == "failed":
                text = f'{ts} - ❌ Failed to save "{filename}" from {sender}: ({err})'
            else:
                text = f"{ts} - {status}"

            self.activity_list.addItem(QListWidgetItem(text))

    def append_run_history_entry(self, result):
        self.read_run_history()

        # success payload from process_mails()
        if isinstance(result, dict):
            events = result.get("events", [])
            for event in events:
                entry = {
                    "timestamp": event.get(
                        "timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ),
                    "status": event.get("status", "unknown"),
                    "from_email": event.get("from_email", ""),
                    "attachment_name": event.get("attachment_name", ""),
                    "folder_path": event.get("folder_path", ""),
                    "error": event.get("error", ""),
                }
                self.run_history.appendleft(entry)

        # error path from on_sorting_failed(message)
        # error path from on_sorting_failed(message)
        elif isinstance(result, str):
            entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "failed",
                "from_email": "",
                "attachment_name": "",
                "folder_path": "",
                "error": result,
            }
            self.run_history.appendleft(entry)

        while len(self.run_history) > 100:
            self.run_history.pop()

        with open(RUN_HISTORY_FILE(), "w") as f:
            json.dump(list(self.run_history), f, indent=4)
            ## WORKING HERE

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
                if table_name in ("keywords_table", "addresses_table"):
                    table.setMinimumHeight(min_height + 120)
                    table.setMaximumHeight(max_height + 180)
                else:
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

        self.dashboard_action_button_style = """
            QPushButton {
                background-color: #2f80ed;
                color: white;
                padding: 12px 14px;
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
            QFrame#activityCard,
            QFrame#kpiCard {
                background-color: #f8fbff;
                border: 1px solid #dbe7f6;
                border-radius: 8px;
            }
            QWidget#quickActionsCard {
                background-color: transparent;
                border: none;
            }
            QListWidget#activityList {
                background-color: white;
                border: 1px solid #dbe7f6;
                border-radius: 8px;
                padding: 6px;
                font-size: 14px;
                color: #1f2a37;
                outline: none;
            }
            QListWidget#activityList::item {
                border: 1px solid #edf3fb;
                border-radius: 6px;
                padding: 8px;
                margin: 2px 0px;
                background-color: #f8fbff;
            }
            QListWidget#activityList::item:selected {
                background-color: #dcecff;
                color: #1f2a37;
                border: 1px solid #c6d8ee;
            }
            QListWidget#activityList::item:hover {
                background-color: #eef5ff;
            }
            QLabel#dashboardSubtitle {
                color: #5f7992;
                font-size: 14px;
                font-weight: 500;
                padding-left: 4px;
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

        self.settings_style = """
            QFrame#settingsCard {
                background-color: #f8fbff;
                border: 1px solid #dbe7f6;
                border-radius: 8px;
            }
            QLabel#settingsLabel {
                color: #5f7992;
                font-size: 13px;
                font-weight: 600;
                margin-top: 4px;
            }
            QLabel#settingsStatus {
                color: #344054;
                font-size: 14px;
                font-weight: 500;
                background-color: #eef5ff;
                border: 1px solid #dbe7f6;
                border-radius: 6px;
                padding: 8px;
            }
            QCheckBox {
                color: #1f2a37;
                font-size: 14px;
                font-weight: 600;
            }
            QSpinBox {
                padding: 8px 12px;
                border: 1px solid #c6d8ee;
                border-radius: 4px;
                font-size: 15px;
                background-color: white;
                color: #1f2a37;
            }
            QSpinBox:focus {
                border: 1px solid #2f80ed;
            }
        """

        self.auth_style = """
            QWidget#authRoot {
                background-color: #f6faff;
            }
            QFrame#authCard {
                background-color: white;
                border: 1px solid #dbe7f6;
                border-radius: 12px;
            }
            QLabel#authSubtitle {
                color: #5f7992;
                font-size: 14px;
                font-weight: 500;
            }
            QLabel#authHint {
                color: #344054;
                font-size: 13px;
                background-color: #f8fbff;
                border: 1px solid #e3edf9;
                border-radius: 8px;
                padding: 10px;
            }
            QLabel#authStatus {
                color: #1f2a37;
                font-size: 14px;
                font-weight: 600;
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
        tab.addTab(self.create_settings_tab(), "Settings")

        return tab

    def create_settings_tab(self):
        widget = QWidget()
        widget.setStyleSheet(self.settings_style)
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        card = QFrame()
        card.setObjectName("settingsCard")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(10)
        title = QLabel("Automatic Sorting")
        title.setStyleSheet(self.title_style)
        self.auto_sort_checkbox = QCheckBox("Enable automatic sorting")
        self.auto_sort_interval_spinbox = QSpinBox()
        self.auto_sort_interval_spinbox.setMinimum(1)
        self.auto_sort_interval_spinbox.setMaximum(1440)
        self.auto_sort_interval_spinbox.setSingleStep(1)
        self.auto_sort_interval_spinbox.setSuffix(" min")

        self.root_base_path_input = QLineEdit()
        self.root_base_path_input.setPlaceholderText("Root save location")
        self.root_base_path_input.setStyleSheet(self.input_style)
        self.root_browse_button = QPushButton("Browse")
        self.root_browse_button.setStyleSheet(self.add_button_style)

        self.root_folder_name_input = QLineEdit()
        self.root_folder_name_input.setPlaceholderText("Root folder name")
        self.root_folder_name_input.setStyleSheet(self.input_style)

        self.auto_sort_apply_button = QPushButton("Save and Apply")
        self.auto_sort_apply_button.setStyleSheet(self.add_button_style)
        self.logout_button = QPushButton("Log out from Google")
        self.logout_button.setStyleSheet(self.delete_button_style)
        self.auto_sort_status_label = QLabel("")
        self.auto_sort_status_label.setObjectName("settingsStatus")

        # Default setting
        self.auto_sort_checkbox.setChecked(self.auto_sort_enabled)

        self.auto_sort_interval_spinbox.setValue(self.auto_sort_interval_minutes)
        self.auto_sort_interval_spinbox.setEnabled(self.auto_sort_enabled)
        self.root_base_path_input.setText(self.root_base_path)
        self.root_folder_name_input.setText(self.root_folder_name)

        # Signals
        self.auto_sort_checkbox.toggled.connect(self.on_auto_sort_toggle_changed)
        self.auto_sort_interval_spinbox.valueChanged.connect(
            self.on_auto_sort_interval_changed
        )
        self.root_browse_button.clicked.connect(self.on_browse_root_path_clicked)
        self.auto_sort_apply_button.clicked.connect(self.on_apply_auto_sort_clicked)
        self.logout_button.clicked.connect(self.on_logout_clicked)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.root_base_path_input, 1)
        path_layout.addWidget(self.root_browse_button)

        card_layout.addWidget(title)
        card_layout.addWidget(self.auto_sort_checkbox)
        card_layout.addWidget(self.auto_sort_interval_spinbox)
        root_path_label = QLabel("Root save location")
        root_path_label.setObjectName("settingsLabel")
        card_layout.addWidget(root_path_label)
        card_layout.addLayout(path_layout)
        root_folder_label = QLabel("Root folder name")
        root_folder_label.setObjectName("settingsLabel")
        card_layout.addWidget(root_folder_label)
        card_layout.addWidget(self.root_folder_name_input)
        card_layout.addWidget(self.auto_sort_apply_button)
        card_layout.addWidget(self.logout_button)
        card_layout.addWidget(self.auto_sort_status_label)

        card.setLayout(card_layout)

        # Credentials card
        creds_card = QFrame()
        creds_card.setObjectName("settingsCard")
        creds_card_layout = QVBoxLayout()
        creds_card_layout.setContentsMargins(14, 14, 14, 14)
        creds_card_layout.setSpacing(10)

        creds_title = QLabel("Google Credentials")
        creds_title.setStyleSheet(self.title_style)

        creds_path_label = QLabel("credentials.json location")
        creds_path_label.setObjectName("settingsLabel")

        creds_path_layout = QHBoxLayout()
        self.settings_creds_path_input = QLineEdit()
        self.settings_creds_path_input.setReadOnly(True)
        self.settings_creds_path_input.setStyleSheet(self.input_style)
        self.settings_creds_path_input.setPlaceholderText("No credentials.json found")
        creds_file = get_data_file("credentials.json")
        if os.path.isfile(creds_file):
            self.settings_creds_path_input.setText(creds_file)
        self.settings_browse_creds_button = QPushButton("Browse")
        self.settings_browse_creds_button.setStyleSheet(self.add_button_style)
        self.settings_browse_creds_button.clicked.connect(
            self.on_settings_browse_credentials_clicked
        )
        creds_path_layout.addWidget(self.settings_creds_path_input, 1)
        creds_path_layout.addWidget(self.settings_browse_creds_button)

        self.settings_creds_status_label = QLabel("")
        self.settings_creds_status_label.setObjectName("settingsStatus")

        creds_card_layout.addWidget(creds_title)
        creds_card_layout.addWidget(creds_path_label)
        creds_card_layout.addLayout(creds_path_layout)
        creds_card_layout.addWidget(self.settings_creds_status_label)
        creds_card.setLayout(creds_card_layout)

        # Switch profile button
        self.switch_profile_button = QPushButton("Switch Profile")
        self.switch_profile_button.setStyleSheet(self.delete_button_style)
        self.switch_profile_button.setMinimumHeight(44)
        self.switch_profile_button.clicked.connect(self.on_switch_profile_clicked)

        layout.addWidget(card)
        layout.addWidget(creds_card)
        layout.addWidget(self.switch_profile_button)
        widget.setLayout(layout)

        self.update_auto_sort_status_label()

        return widget

    def on_auto_sort_toggle_changed(self, checked):
        self.auto_sort_interval_spinbox.setEnabled(checked)
        self.update_auto_sort_status_label()

    def on_auto_sort_interval_changed(self, value):
        self.update_auto_sort_status_label()

    def on_settings_browse_credentials_clicked(self):
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Select credentials.json",
            "",
            "JSON Files (*.json);;All Files (*)",
        )
        if not selected:
            return

        ok, result = self.import_credentials_file(selected)
        if ok:
            self.settings_creds_path_input.setText(result)
            self.settings_creds_status_label.setText(
                "✅ Credentials updated. Log out and log back in to use the new credentials."
            )
        else:
            self.settings_creds_status_label.setText(
                f"❌ Failed to import credentials: {result}"
            )

    def on_browse_root_path_clicked(self):
        selected = QFileDialog.getExistingDirectory(
            self,
            "Select root save location",
            self.root_base_path_input.text().strip() or self.root_base_path,
        )
        if selected:
            self.root_base_path_input.setText(selected)
            self.update_auto_sort_status_label()

    def on_apply_auto_sort_clicked(self):
        root_base_path = self.root_base_path_input.text().strip()
        root_folder_name = self.root_folder_name_input.text().strip()

        if not root_base_path:
            root_base_path = os.path.join(
                os.path.join(os.environ["USERPROFILE"]), "Desktop"
            )

        if not root_folder_name:
            root_folder_name = "Main"

        if not self.is_valid_folder_name(root_folder_name):
            self.auto_sort_status_label.setText(
                '❌ Invalid folder name. Avoid: \\ / : * ? " < > |'
            )
            return

        self.auto_sort_enabled = self.auto_sort_checkbox.isChecked()
        self.auto_sort_interval_minutes = self.auto_sort_interval_spinbox.value()
        self.root_base_path = root_base_path
        self.root_folder_name = root_folder_name

        self.root_base_path_input.setText(self.root_base_path)
        self.root_folder_name_input.setText(self.root_folder_name)

        self.save_settings()
        self.apply_auto_sort_state()
        self.update_auto_sort_status_label()

    def on_logout_clicked(self):
        if self.is_sorting_running:
            self.auto_sort_status_label.setText(
                "❌ Cannot log out while sorting is in progress."
            )
            return

        for file_path in (TOKEN_FILE(), HISTORY_FILE()):
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except OSError:
                pass

        self.auto_sort_enabled = False
        self.apply_auto_sort_state()
        self.save_settings()

        self.show_auth_ui()
        if hasattr(self, "auth_status_label"):
            self.auth_status_label.setText(
                "Logged out successfully. Press 'Start Google Login' to continue."
            )

    def on_switch_profile_clicked(self):
        if self.is_sorting_running:
            self.auto_sort_status_label.setText(
                "❌ Cannot switch profile while sorting is in progress."
            )
            return

        self.auto_sort_enabled = False
        self.apply_auto_sort_state()

        self.show_profile_ui()

    def update_auto_sort_status_label(self):
        target_path = os.path.join(
            self.root_base_path_input.text().strip() or self.root_base_path,
            self.root_folder_name_input.text().strip() or self.root_folder_name,
        )
        if self.auto_sort_enabled:
            self.auto_sort_status_label.setText(
                f"Auto-sort is ON (every {self.auto_sort_interval_minutes} min) | Save to: {target_path}"
            )
        else:
            self.auto_sort_status_label.setText(
                f"Auto-sort is OFF | Save to: {target_path}"
            )

    def create_dashboard_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        widget.setStyleSheet(self.dashboard_style)

        # Title and subtitle
        top_card = QWidget()
        top_card.setObjectName("dashHeader")
        top_header_layout = QHBoxLayout()
        top_header_layout.setContentsMargins(14, 14, 14, 14)
        top_header_layout.setSpacing(10)

        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)
        title = QLabel("Dashboard")
        title.setStyleSheet(self.title_style)
        subtitle = QLabel("Quick overview of your mail sorting status")
        subtitle.setObjectName("dashboardSubtitle")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        top_header_layout.addLayout(title_layout, 1)

        if os.path.isfile(APP_ICON_FILE):
            logo_label = QLabel()
            logo_label.setStyleSheet("background-color: transparent;")
            pixmap = QPixmap(APP_ICON_FILE)
            if not pixmap.isNull():
                logo_label.setPixmap(
                    pixmap.scaled(88, 88, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                top_header_layout.addWidget(
                    logo_label, 0, Qt.AlignRight | Qt.AlignVCenter
                )

        top_card.setLayout(top_header_layout)

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
        self.activity_text = QLabel(
            "• No recent activity yet\n" "• Last action: --\n" "• Status: waiting"
        )
        self.activity_text.setObjectName("activityText")
        self.activity_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.activity_list = QListWidget()
        self.activity_list.setObjectName("activityList")
        self.activity_list.setFocusPolicy(Qt.NoFocus)
        self.activity_list.setSpacing(4)
        self.activity_list.setMinimumHeight(300)
        self.activity_list.itemDoubleClicked.connect(self.on_activity_item_clicked)

        activity_layout.addWidget(activity_title)
        activity_layout.addWidget(self.activity_text)
        activity_layout.addWidget(self.activity_list, 1)
        activity_card.setLayout(activity_layout)
        activity_card.setMinimumHeight(430)

        self.refresh_activity_list()

        # Quick actions (Step 5)
        quick_actions_card = QWidget()
        quick_actions_card.setObjectName("quickActionsCard")
        quick_actions_layout = QHBoxLayout()
        quick_actions_layout.setContentsMargins(14, 14, 14, 14)
        quick_actions_layout.setSpacing(10)

        self.run_sorting_button = QPushButton("Run mail sorting now")
        self.run_sorting_button.setStyleSheet(self.dashboard_action_button_style)
        self.run_sorting_button.setMinimumHeight(48)
        self.run_sorting_button.setMaximumWidth(300)
        self.run_sorting_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.run_sorting_button.clicked.connect(self.on_run_sorting_clicked)

        self.refresh_dashboard_button = QPushButton("Refresh dashboard data")
        self.refresh_dashboard_button.setStyleSheet(self.dashboard_action_button_style)
        self.refresh_dashboard_button.setMinimumHeight(48)
        self.refresh_dashboard_button.setMaximumWidth(300)
        self.refresh_dashboard_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.refresh_dashboard_button.clicked.connect(self.refresh_dashboard_metrics)

        quick_actions_layout.addWidget(self.run_sorting_button)
        quick_actions_layout.addWidget(self.refresh_dashboard_button)
        quick_actions_card.setLayout(quick_actions_layout)

        layout.addWidget(top_card)
        layout.addWidget(kpi_card)
        layout.addWidget(activity_card, 3)
        layout.addWidget(quick_actions_card)
        widget.setLayout(layout)

        return widget

    def contains_saved(self, value):
        if not isinstance(value, str):
            return False
        return "Saved".lower() in value.lower()

    def extract_path_from_string(self, text):
        if not isinstance(text, str) or not text.strip():
            return None

        if "->" in text:
            candidate = text.split("->", 1)[1].strip().strip('"').strip("'")
            return candidate or None

        drive_index = None
        for i in range(len(text) - 2):
            if text[i].isalpha() and text[i + 1 : i + 3] == ":\\":
                drive_index = i
                break

        if drive_index is None:
            return None

        allowed = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ .\\/:()"
        )
        end = drive_index
        while end < len(text) and text[end] in allowed:
            end += 1

        candidate = text[drive_index:end].strip().rstrip(".,;:)]}")
        return candidate or None

    def on_activity_item_clicked(self, item):
        text = item.text()
        if self.contains_saved(text):
            path = self.extract_path_from_string(text)
            if path:
                os.startfile(path)

    def on_run_sorting_clicked(self):
        if self.is_sorting_running:
            return

        self.is_sorting_running = True
        self.run_sorting_button.setEnabled(False)
        self.refresh_dashboard_button.setEnabled(False)
        self.activity_text.setText("⏳ Sorting in progress...")

        self.sort_thread = QThread()
        self.sort_worker = MailSortWorker()

        self.sort_worker.moveToThread(self.sort_thread)

        self.sort_thread.started.connect(self.sort_worker.run)

        self.sort_worker.finished.connect(self.on_sorting_finished)
        self.sort_worker.error.connect(self.on_sorting_failed)

        self.sort_worker.finished.connect(self.sort_thread.quit)
        self.sort_worker.error.connect(self.sort_thread.quit)

        self.sort_thread.finished.connect(self.cleanup_sorting_thread)

        self.sort_thread.start()

    def on_sorting_finished(self, result):

        self.is_sorting_running = False
        self.run_sorting_button.setEnabled(True)
        self.refresh_dashboard_button.setEnabled(True)
        self.append_run_history_entry(result)
        self.activity_text.setText(f"✅ Sorting completed successfully.")
        self.refresh_activity_list()
        self.refresh_dashboard_metrics()

    def on_sorting_failed(self, message):
        self.is_sorting_running = False
        self.run_sorting_button.setEnabled(True)
        self.refresh_dashboard_button.setEnabled(True)
        self.append_run_history_entry(message)
        self.activity_text.setText(
            "❌ Sorting failed. Check recent activity for details."
        )
        self.refresh_activity_list()

    def cleanup_sorting_thread(self):
        self.sort_worker = None
        self.sort_thread = None

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

        if os.path.isfile(STATS_FILE()):
            try:
                with open(STATS_FILE(), "r") as f:
                    stats = json.load(f)
                    if isinstance(stats, dict):
                        if "last_run" in stats:
                            last_run = stats["last_run"]
                        if "emails_processed" in stats:
                            emails_processed = stats["emails_processed"]
            except json.JSONDecodeError:
                with open(STATS_FILE(), "w") as f:
                    json.dump({}, f, indent=4)

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
        layout.addWidget(self.keywords_table, 1)
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
            with open(KEYWORDS_FILE(), "r") as f:
                self.tracked_keywords = json.load(f)
        except FileNotFoundError:
            self.show_message("Error: The file 'keywords.json' was not found.", "error")
            self.tracked_keywords = {}
            with open(KEYWORDS_FILE(), "w") as f:
                json.dump({}, f)
        except json.JSONDecodeError:
            self.show_message(
                "Error: Failed to decode JSON from the file. Check for malformed JSON syntax.",
                "error",
            )
            self.tracked_keywords = {}

    def save_keywords(self):
        with open(KEYWORDS_FILE(), "w") as f:
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

        tracked_layout.addWidget(self.addresses_table, 1)
        tracked_layout.setContentsMargins(0, 5, 0, 5)

        # Bottom Layout
        bottom_layout = QVBoxLayout()
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.on_delete_button_clicked)
        self.delete_button.setStyleSheet(self.delete_button_style)
        self.delete_button.setCursor(QCursor(Qt.PointingHandCursor))
        bottom_layout.addWidget(self.delete_button)

        layout.addWidget(top_card)
        layout.addLayout(tracked_layout, 1)
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
            with open(ADDRESSES_FILE(), "r") as file:
                self.tracked_addresses = json.load(file)
        except FileNotFoundError:
            self.show_message(
                "Error: The file 'addresses.json' was not found.", "error"
            )
            self.tracked_addresses = {}
            with open(ADDRESSES_FILE(), "w") as f:
                json.dump({}, f)
        except json.JSONDecodeError:
            self.show_message(
                "Error: Failed to decode JSON from the file. Check for malformed JSON syntax.",
                "error",
            )
            self.tracked_addresses = {}

    def save_addresses(self):
        try:
            with open(ADDRESSES_FILE(), "w") as f:
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
    if sys.platform.startswith("win"):
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "petar.mail_sorter.app"
            )
        except Exception:
            pass

    app = QApplication(sys.argv)
    if os.path.isfile(APP_ICON_FILE):
        app.setWindowIcon(QIcon(APP_ICON_FILE))

    window = MailSorterApp()

    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
