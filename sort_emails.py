from read_emails import read_emails
import os
import base64
import json
from datetime import datetime

desktop_path = os.path.join(os.path.join(os.environ["USERPROFILE"]), "Desktop")


def extract_email(from_string):
    """Extract email address from 'Name <email@domain.com>' format"""
    if "<" in from_string and ">" in from_string:
        start = from_string.find("<") + 1
        end = from_string.find(">")
        return from_string[start:end]
    return from_string


def load_keywords(address):
    if not os.path.isfile("keywords.json"):
        with open("keywords.json", "w") as f:
            json.dump({}, f, indent=4)

    with open("keywords.json") as f:
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


def process_mails():
    if not os.path.isfile("addresses.json"):
        with open("addresses.json", "w") as f:
            json.dump({}, f, indent=4)

    with open("addresses.json", "r") as f:
        addresses_to_track = json.load(f)

    # Create Mails folder if it doesn't exist
    mails_path = os.path.join(desktop_path, "Mails")
    if not os.path.exists(mails_path):
        os.makedirs(mails_path)

    emails = fetch_new_emails()

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

                    save_attachment_image(
                        attachment["data"],
                        os.path.join(path_with_subfolder, attachment["filename"]),
                    )
                emails_processed_count += 1

    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

    with open("stats.json", "w") as f:
        stats = {}
        stats["last_run"] = formatted_datetime
        stats["emails_processed"] = emails_processed_count
        json.dump(stats, f, indent=4)
