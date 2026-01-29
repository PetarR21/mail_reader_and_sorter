from read_emails import read_emails
import os
import base64
import json

desktop_path = os.path.join(os.path.join(os.environ["USERPROFILE"]), "Desktop")


def extract_email(from_string):
    """Extract email address from 'Name <email@domain.com>' format"""
    if "<" in from_string and ">" in from_string:
        start = from_string.find("<") + 1
        end = from_string.find(">")
        return from_string[start:end]
    return from_string


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
    raw = b64url_to_bytes(attachment_response["data"])
    with open(output_path, "wb") as f:
        f.write(raw)


def process_mails():
    with open("addresses.json", "r") as f:
        addresses_to_track = json.load(f)

    # Create Mails folder if it doesn't exist
    mails_path = os.path.join(desktop_path, "Mails")
    if not os.path.exists(mails_path):
        os.makedirs(mails_path)

    emails = fetch_new_emails()
    for email in emails:
        if email["attachment"]:
            email_address = extract_email(email["from"])
            if email_address in addresses_to_track:
                user_path = os.path.join(mails_path, addresses_to_track[email_address])

                if not os.path.exists(user_path):
                    os.makedirs(user_path)

                save_attachment_image(
                    email["attachment"]["data"],
                    os.path.join(user_path, email["attachment"]["filename"]),
                )
