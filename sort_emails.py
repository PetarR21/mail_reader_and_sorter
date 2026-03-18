from read_emails import read_emails
import os
import base64
import json
from datetime import datetime
from app_paths import get_data_file

desktop_path = os.path.join(os.path.join(os.environ["USERPROFILE"]), "Desktop")


def _settings_file():
    return get_data_file("settings.json")


def _keywords_file():
    return get_data_file("keywords.json")


def _addresses_file():
    return get_data_file("addresses.json")


def _stats_file():
    return get_data_file("stats.json")


def is_valid_folder_name(folder_name):
    if not isinstance(folder_name, str) or not folder_name.strip():
        return False

    invalid_chars = ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]
    for char in invalid_chars:
        if char in folder_name:
            return False

    return True


def load_storage_settings():
    default_base_path = desktop_path
    default_folder_name = "Main"

    if not os.path.isfile(_settings_file()):
        return default_base_path, default_folder_name

    try:
        with open(_settings_file(), "r") as f:
            settings = json.load(f)

        if not isinstance(settings, dict):
            return default_base_path, default_folder_name

        root_base_path = settings.get("root_base_path", default_base_path)
        root_folder_name = settings.get("root_folder_name", default_folder_name)

        if not isinstance(root_base_path, str) or not root_base_path.strip():
            root_base_path = default_base_path

        if not is_valid_folder_name(root_folder_name):
            root_folder_name = default_folder_name

        return root_base_path.strip(), root_folder_name.strip()
    except (json.JSONDecodeError, OSError, ValueError):
        return default_base_path, default_folder_name


def extract_email(from_string):
    """Extract email address from 'Name <email@domain.com>' format"""
    if "<" in from_string and ">" in from_string:
        start = from_string.find("<") + 1
        end = from_string.find(">")
        return from_string[start:end]
    return from_string


def load_keywords(address):
    if not os.path.isfile(_keywords_file()):
        with open(_keywords_file(), "w") as f:
            json.dump({}, f, indent=4)

    with open(_keywords_file()) as f:
        keywords = json.load(f)

    if keywords:
        for key in keywords.keys():
            if key == address:
                return keywords[key]
    else:
        return None


def fetch_new_emails():
    emails = read_emails()
    if emails:
        return emails
    else:
        return []


def b64url_to_bytes(data: str) -> bytes:
    # Gmail uses urlsafe base64, sometimes without '=' padding
    data += "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def save_attachment_image(attachment_response: dict, output_path: str) -> None:
    # Handle both response structure and direct data
    data = (
        attachment_response.get("data")
        if isinstance(attachment_response, dict)
        else attachment_response
    )
    if data is None:
        return
    raw = b64url_to_bytes(data)
    with open(output_path, "wb") as f:
        f.write(raw)


def check_keywords(attachment_name, email_address):
    keywords = load_keywords(email_address)
    if not keywords:
        return "Default"
    for keyword in keywords:
        if keyword.lower().strip() in attachment_name.lower().strip():
            return keyword.title()
    return "Default"


def get_current_datetime():
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

    return formatted_datetime


def process_mails():
    if not os.path.isfile(_addresses_file()):
        with open(_addresses_file(), "w") as f:
            json.dump({}, f, indent=4)

    with open(_addresses_file(), "r") as f:
        addresses_to_track = json.load(f)

    root_base_path, root_folder_name = load_storage_settings()
    mails_path = os.path.join(root_base_path, root_folder_name)

    try:
        os.makedirs(mails_path, exist_ok=True)
    except OSError:
        mails_path = os.path.join(desktop_path, "Main")
        os.makedirs(mails_path, exist_ok=True)

    emails = fetch_new_emails()

    events = []
    processed_count = 0
    failed_count = 0
    emails_processed_count = 0

    for email in emails:
        email_address = extract_email(email["from"])
        if email_address in addresses_to_track:
            user_path = os.path.join(mails_path, addresses_to_track[email_address])

            if not os.path.exists(user_path):
                os.makedirs(user_path)

            if email["attachments"]:
                for attachment in email["attachments"]:
                    subfolder = check_keywords(attachment["filename"], email_address)
                    path_with_subfolder = os.path.join(user_path, subfolder)
                    if not os.path.exists(path_with_subfolder):
                        os.makedirs(path_with_subfolder)

                    event = {}
                    event["timestamp"] = get_current_datetime()
                    event["from_email"] = email_address
                    event["attachment_name"] = attachment["filename"]
                    event["folder_path"] = str(path_with_subfolder)
                    event["status"] = None
                    try:
                        save_attachment_image(
                            attachment["data"],
                            os.path.join(path_with_subfolder, attachment["filename"]),
                        )
                        processed_count += 1
                        event["status"] = "saved"
                        event["error"] = None
                    except Exception as e:
                        failed_count += 1
                        event["status"] = "failed"
                        event["error"] = str(e)
                    events.append(event)
                emails_processed_count += 1

    with open(_stats_file(), "w") as f:
        stats = {}
        stats["last_run"] = get_current_datetime()
        stats["emails_processed"] = emails_processed_count
        json.dump(stats, f, indent=4)

    return {
        "processed_count": processed_count,
        "failed_count": failed_count,
        "events": events,
        "last_run": stats["last_run"],
    }
